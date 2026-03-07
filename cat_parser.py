"""Parser for Mewgenics save files (.sav SQLite databases).

Reverse-engineered from MewgenicsSaveEditor v3.0.1 (decompiled).

Cat blobs are LZ4-compressed. After decompression:
  - Header: magic(19) at byte 0, name_len(u32) at byte 12, name(UTF-16LE) at byte 20
  - Pre-meta block: 24 bytes = 6×u32 [0, 0, gender_a, gender_b, flags, 0]
  - ASCII strings: [u32 strlen][u32 pad=0][ascii bytes]
  - Equipment block: 368 bytes between breed and voice (mutation frames)
  - Stat block: 92 bytes between voice and stat_type
    [f64 seed][7×i32 base][7×i32 bonus][7×i32 extra]
  - Death marker: 14-byte gap between stat_type and DefaultMove
    [f32 ~2.0][u32 dead_flag][6×00]
  - Trailing data after class string:
    [12 bytes inbreeding][i32 birth_day][24 bytes parents][growth+flags]

String field layout (end-relative):
  strings[-1]      = class
  strings[-15:-1]  = 14 abilities (first = DefaultMove)
  strings[-16]     = stat_type
  strings[-17]     = voice
  strings[0]       = breed
"""

import sqlite3
import struct
import os
import re
from dataclasses import dataclass, field

import lz4.block


# === Constants from MewgenicsSaveEditor v3.0.1 ===

_CAT_MAGIC = 19
_NAME_LEN_OFFSET = 12
_NAME_START = 20
_MAX_NAME_LENGTH = 5000

# Pre-meta block
_PRE_META_SIZE = 24  # 6 × u32
_PRE_META_U32_COUNT = 6
_GENDER_INDEX_A = 2
_GENDER_INDEX_B = 3
_FLAGS_INDEX = 4
_GENDER_MALE = 1
_GENDER_FEMALE = 2
_GENDER_ANY = 3

# Flag masks (at pre_meta[4])
_RETIRED_FLAG = 0x02
_DEAD_FLAG = 0x10
_GAMEPLAY_FLAG = 0x10000
_DONATED_FLAG = 0x80000
_NPC_AWAY_MASK = 0xFF800  # bits 11-19

# Stat block layout (92 bytes total)
_STAT_BLOCK_SIZE = 92
_STAT_COUNT = 7
_STAT_SEED_SIZE = 8      # f64
_STAT_BASE_OFFSET = 8    # after seed
_STAT_BONUS_OFFSET = 36  # 8 + 7*4
_STAT_EXTRA_OFFSET = 64  # 8 + 7*4 + 7*4

STAT_NAMES = ('str', 'dex', 'con', 'int', 'spd', 'cha', 'lck')
STAT_LABELS = ('STR', 'DEX', 'CON', 'INT', 'SPD', 'CHA', 'LCK')
STAT_LABELS_RU = ('СИЛ', 'ЛОВ', 'ВЫН', 'ИНТ', 'СКР', 'ХАР', 'УДЧ')

# Equipment block: 368 bytes between breed and voice strings
_EQUIP_BLOCK_SIZE = 368
_EQUIP_BLOCK_PART_OFFSETS = (
    (68, 'texture'), (80, 'body'), (100, 'head'), (120, 'tail'),
    (140, 'leg1'), (160, 'leg2'), (180, 'arm1'), (200, 'arm2'),
    (220, 'lefteye'), (240, 'righteye'), (260, 'lefteyebrow'),
    (280, 'righteyebrow'),
)
_MUTATION_FRAME_THRESHOLD = 300
_BIRTH_DEFECT_FRAME_THRESHOLD = 700

# Death marker layout (14-byte gap between stat_type and DefaultMove)
_DEATH_MARKER_OFFSET = 4  # offset within the gap to the u32 dead flag

# Trailing data (after class string)
_TRAIL_INBREEDING_SIZE = 12   # +0..+11
_TRAIL_BIRTHDAY_OFFSET = 12   # +12..+15 (i32)
_TRAIL_PARENTS_OFFSET = 16    # +16..+39 (6 u32s = parent keys)
_TRAIL_PARENTS_SIZE = 24
_BIRTH_DAY_EPOCH_OFFSET = 4

# Part name -> Russian display
PART_NAME_RU = {
    'texture': 'Текстура', 'body': 'Тело', 'head': 'Голова', 'tail': 'Хвост',
    'leg1': 'Нога 1', 'leg2': 'Нога 2', 'arm1': 'Рука 1', 'arm2': 'Рука 2',
    'lefteye': 'Левый глаз', 'righteye': 'Правый глаз',
    'lefteyebrow': 'Левая бровь', 'righteyebrow': 'Правая бровь',
}

# Known stat types
STAT_TYPES = {'none', 'str', 'dex', 'con', 'int', 'spd', 'cha', 'lck',
              'poisoned', 'burned', 'bleeding'}

# Basic attack -> class mapping
ATTACK_TO_CLASS = {
    "BasicMelee_Fighter": "Fighter",
    "BasicMelee": "Colorless",
    "BasicTankMelee": "Tank",
    "BasicRanged_Hunter": "Hunter",
    "BasicMagicShortRanged": "Mage",
    "BasicMedicMelee": "Medic",
    "BasicMedClee": "Medic",
    "BasicNecroRanged": "Necromancer",
    "BasicDruidAbility": "Druid",
    "BasicShortLobbed": "Colorless",
    "BasicShortRanged": "Colorless",
    "BasicStraightShot_Thief": "Thief",
    "TinkererCraft": "Tinkerer",
}

CLASS_RU = {
    "Fighter": "Боец", "Tank": "Танк", "Hunter": "Охотник", "Mage": "Маг",
    "Medic": "Медик", "Necromancer": "Некромант", "Druid": "Друид",
    "Thief": "Вор", "Tinkerer": "Механик", "Colorless": "Бесцветный",
    "Monk": "Монах", "Jester": "Шут", "Psychic": "Психик", "Butcher": "Мясник",
}

VOICE_GENDER = {"male": "кот", "female": "кошка", "spidercat": "кот-паук"}

STAT_FOCUS_RU = {
    "str": "Сила", "spd": "Скорость", "lck": "Удача", "int": "Интеллект",
    "dex": "Ловкость", "cha": "Харизма", "con": "Выносливость", "none": "Нет",
    "burned": "Обожжённый", "poisoned": "Отравленный", "bleeding": "Кровотечение",
}

BIRTH_DEFECT_PASSIVES = frozenset({
    'Dwarfism', 'Tourettes', 'Dyslexia', 'WobblyCat', 'SavantSyndrome',
    'PrimordialDwarf', 'OCD', 'Autism', 'Anemia', 'Depression', 'Bipolar',
    'Narcolepsy', 'ADHD', 'Diabetes', 'SpinaBifida', 'Schizophrenia',
    'GlassBones', 'Albinism', 'Tachysensia', 'WilliamsSyndrome', 'DownsSyndrome',
})


@dataclass
class CatStats:
    base: list = field(default_factory=lambda: [0]*7)
    bonus: list = field(default_factory=lambda: [0]*7)
    extra: list = field(default_factory=lambda: [0]*7)
    seed: float = 0.0

    @property
    def effective(self) -> list:
        return [b + bn + e for b, bn, e in zip(self.base, self.bonus, self.extra)]


@dataclass
class CatData:
    id: int = 0
    name: str = ""
    voice: str = ""
    gender: str = ""
    gender_code: int = 0  # 1=male, 2=female, 3=any
    stat_focus: str = ""
    cat_class: str = "Colorless"
    basic_attack: str = ""
    abilities: list = field(default_factory=list)
    passives: list = field(default_factory=list)
    items: list = field(default_factory=list)
    mutations: dict = field(default_factory=dict)
    all_frames: dict = field(default_factory=dict)  # all body part frames
    stats: CatStats = field(default_factory=CatStats)
    status: str = "OK"  # OK, Injured, Dead
    is_dead: bool = False
    is_retired: bool = False
    is_donated: bool = False
    birth_day: int | None = None
    age_days: int | None = None
    pre_meta_flags: int = 0
    parent_keys: list = field(default_factory=list)
    inbreeding_level: int = 0
    breed: str = ""
    raw_strings: list = field(default_factory=list)


# === Core parsing functions ===

def _decompress_blob(blob: bytes) -> bytes:
    """Decompress LZ4-compressed cat blob. First 4 bytes = uncompressed size."""
    uncomp_size = struct.unpack_from('<I', blob, 0)[0]
    try:
        return lz4.block.decompress(blob[4:], uncompressed_size=uncomp_size)
    except Exception:
        return blob


def _scan_ascii_strings(data: bytes, start: int) -> list[tuple[int, str]]:
    """Scan for ASCII strings encoded as [u32 len][u32 pad=0][ascii bytes]."""
    strings = []
    i = start
    while i < len(data) - 8:
        slen = struct.unpack_from('<I', data, i)[0]
        pad = struct.unpack_from('<I', data, i + 4)[0]
        if 1 <= slen <= 60 and pad == 0 and i + 8 + slen <= len(data):
            try:
                s = data[i+8:i+8+slen].decode('ascii')
                if all(32 <= ord(c) < 127 for c in s):
                    strings.append((i, s))
                    i += 8 + slen
                    continue
            except (UnicodeDecodeError, ValueError):
                pass
        i += 1
    return strings


def _parse_pre_meta(data: bytes, name_end: int, first_string_offset: int) -> tuple[list, int, str]:
    """Parse the pre-meta block between name end and first ASCII string.

    Two layouts:
    - Full (breed="None"): 24-byte block between name_end and first string
      Layout: [0, 0, gender_a, gender_b, flags, 0]
    - Compact (breed is a real type): first string starts right at name_end,
      16-byte block between 1st and 2nd string
      Layout: [gender_a, gender_b, flags, 0] (padded to 6 for compat)

    Returns (u32_values[6], block_offset, format_kind).
    """
    gap = first_string_offset - name_end

    if gap >= _PRE_META_SIZE:
        # Full format: 24-byte block
        vals = []
        for i in range(_PRE_META_U32_COUNT):
            v = struct.unpack_from('<I', data, name_end + i * 4)[0]
            vals.append(v)
        return vals, name_end, 'standard'

    # Compact format: block is between 1st and 2nd string
    return [0] * _PRE_META_U32_COUNT, name_end, 'compact'


def _parse_pre_meta_compact(data: bytes, strings: list[tuple[int, str]]) -> tuple[list, int, str]:
    """Parse pre-meta for compact format (between 1st and 2nd ASCII string)."""
    if len(strings) < 2:
        return [0] * _PRE_META_U32_COUNT, 0, 'unknown'

    first_off, first_val = strings[0]
    first_end = first_off + 8 + len(first_val)
    second_off = strings[1][0]
    gap = second_off - first_end

    if gap >= 16:
        vals = [0, 0]  # pad to match 6-u32 canonical form
        for i in range(4):
            if first_end + i * 4 + 4 <= len(data):
                v = struct.unpack_from('<I', data, first_end + i * 4)[0]
                vals.append(v) if i >= 2 else None  # skip first 2 for padding
                if i < 2:
                    vals[i] = 0  # keep canonical padding
        # Actually read 4 u32s and prepend [0,0]
        compact_vals = []
        for i in range(min(4, gap // 4)):
            compact_vals.append(struct.unpack_from('<I', data, first_end + i * 4)[0])
        while len(compact_vals) < 4:
            compact_vals.append(0)
        return [0, 0] + compact_vals, first_end, 'compact'

    return [0] * _PRE_META_U32_COUNT, 0, 'unknown'


def _find_stat_block(data: bytes, strings: list[tuple[int, str]]) -> tuple[CatStats | None, int | None, int | None]:
    """Find the 92-byte stat block between consecutive string fields.

    Scans all consecutive field pairs for the unique 92-byte gap.
    Returns (stat_data, voice_field_index, stat_type_field_index).
    """
    for i in range(len(strings) - 1):
        off_a = strings[i][0]
        val_a = strings[i][1]
        a_end = off_a + 8 + len(val_a)
        off_b = strings[i + 1][0]
        gap_size = off_b - a_end

        if gap_size == _STAT_BLOCK_SIZE:
            block = data[a_end:off_b]
            seed = struct.unpack_from('<d', block, 0)[0]
            base = [struct.unpack_from('<i', block, _STAT_BASE_OFFSET + j*4)[0] for j in range(_STAT_COUNT)]
            bonus = [struct.unpack_from('<i', block, _STAT_BONUS_OFFSET + j*4)[0] for j in range(_STAT_COUNT)]
            extra = [struct.unpack_from('<i', block, _STAT_EXTRA_OFFSET + j*4)[0] for j in range(_STAT_COUNT)]

            all_vals = base + bonus + extra
            if any(abs(v) > 1000 for v in all_vals):
                continue

            stats = CatStats(base=base, bonus=bonus, extra=extra, seed=seed)
            return stats, i, i + 1

    return None, None, None


def _parse_equipment_block(data: bytes, strings: list[tuple[int, str]]) -> tuple[dict, dict, int | None]:
    """Parse mutation data from the 368-byte equipment block between breed and voice.

    Returns (mutations, all_frames, block_offset).
    Mutations only includes frames >= 300.
    All_frames includes every body part frame.
    """
    # Find breed (first string) and voice (identified by content)
    breed_idx = None
    voice_idx = None

    for idx, (off, s) in enumerate(strings):
        if voice_idx is None and re.match(r'^(male|female|spidercat)\d', s):
            voice_idx = idx
            break

    if voice_idx is None or voice_idx < 1:
        return {}, {}, None

    # Breed is strings[0], equipment block is between breed end and voice start
    breed_off, breed_val = strings[0]
    breed_end = breed_off + 8 + len(breed_val)
    voice_off = strings[voice_idx][0]
    block_size = voice_off - breed_end

    # Try to find the block — may be between breed and voice directly,
    # or there might be extra strings (compact breed variants)
    candidates = [(breed_end, voice_off)]

    # Also try from strings[1] end if breed is at index 0
    for back in range(1, min(4, voice_idx)):
        prev_off, prev_val = strings[voice_idx - back]
        prev_end = prev_off + 8 + len(prev_val)
        candidates.append((prev_end, voice_off))

    mutations = {}
    all_frames = {}
    for start, end in candidates:
        bs = end - start
        if _EQUIP_BLOCK_SIZE - 8 <= bs <= _EQUIP_BLOCK_SIZE + 8:
            block = data[start:end]
            for offset, part_name in _EQUIP_BLOCK_PART_OFFSETS:
                if offset + 4 <= len(block):
                    frame = struct.unpack_from('<I', block, offset)[0]
                    all_frames[part_name] = frame
                    if frame >= _MUTATION_FRAME_THRESHOLD:
                        mutations[part_name] = frame
            return mutations, all_frames, start

    return {}, {}, None


def _parse_death_marker(data: bytes, strings: list[tuple[int, str]], stat_type_idx: int | None) -> bool:
    """Check the death marker in the gap between stat_type and next string.

    The gap is 14 bytes: [f32 ~2.0][u32 dead_flag][6×00].
    """
    if stat_type_idx is None or stat_type_idx + 1 >= len(strings):
        return False

    st_off, st_val = strings[stat_type_idx]
    st_end = st_off + 8 + len(st_val)
    death_off = st_end + _DEATH_MARKER_OFFSET

    if death_off + 4 <= len(data):
        dead_val = struct.unpack_from('<I', data, death_off)[0]
        return dead_val == 1

    return False


def _parse_trailing_data(data: bytes, strings: list[tuple[int, str]]) -> dict:
    """Parse trailing data after the class string (last string).

    Layout (relative to class string end):
      +0..+11:  inbreeding level + padding
      +12..+15: birth_day (i32)
      +16..+39: parent/ancestor key references (6 u32s)
      +40+:     growth stage + flags
    """
    result = {'birth_day': None, 'parent_keys': [], 'inbreeding': 0}

    if not strings:
        return result

    # Class is last string
    class_off, class_val = strings[-1]
    class_end = class_off + 8 + len(class_val)

    # Adventure counter is first u32 after class
    # Then trailing data

    # Inbreeding level (first u32 of trailing area)
    if class_end + 4 <= len(data):
        result['inbreeding'] = struct.unpack_from('<I', data, class_end)[0]

    # Birth day at +12
    birthday_off = class_end + _TRAIL_BIRTHDAY_OFFSET
    if birthday_off + 4 <= len(data):
        raw_val = struct.unpack_from('<i', data, birthday_off)[0]
        if -100000 < raw_val < 100000:  # sanity check
            result['birth_day'] = raw_val

    # Parent keys at +16 (6 u32s)
    parents_off = class_end + _TRAIL_PARENTS_OFFSET
    if parents_off + _TRAIL_PARENTS_SIZE <= len(data):
        parent_keys = []
        for i in range(6):
            pk = struct.unpack_from('<I', data, parents_off + i * 4)[0]
            if pk > 0:
                parent_keys.append(pk)
        result['parent_keys'] = parent_keys

    return result


def _classify_strings_saveeditor(cat: CatData, all_strings: list[tuple[int, str]],
                                  voice_idx: int | None, stat_type_idx: int | None):
    """Classify strings using the SaveEditor's end-relative indexing.

    Layout from the SaveEditor docstring:
      strings[0]      = breed
      strings[-17]    = voice
      strings[-16]    = stat_type
      strings[-15:-1] = 14 abilities (first = DefaultMove, second = basic_attack)
      strings[-1]     = class

    However, ability count can vary (14 or 15), and there may be extra
    strings before voice. So we use the stat block position as anchor.
    """
    n = len(all_strings)

    if n < 3:
        return

    # Class is always last string
    class_str = all_strings[-1][1]
    if class_str in CLASS_RU:
        cat.cat_class = class_str

    # Voice
    if voice_idx is not None:
        cat.voice = all_strings[voice_idx][1]
        for prefix, gender in VOICE_GENDER.items():
            if cat.voice.startswith(prefix):
                cat.gender = gender
                break

    # Breed is first string
    if n >= 1:
        cat.breed = all_strings[0][1]

    # Use end-relative indexing if we have enough strings
    # strings[-1] = class
    # strings[-15:-1] = abilities (14 slots)
    # strings[-16] = stat_type
    # strings[-17] = voice

    # But first try to use the stat_type_idx as anchor (more reliable)
    if stat_type_idx is not None:
        # stat_type is at stat_type_idx
        st_str = all_strings[stat_type_idx][1]
        if st_str in STAT_TYPES:
            cat.stat_focus = STAT_FOCUS_RU.get(st_str, st_str)

        # Abilities start right after stat_type (+gap) = stat_type_idx + 1
        # But there's a 14-byte gap with death marker, then DefaultMove
        # In terms of string indices: everything from stat_type_idx+1 to n-2 is abilities
        # Last one (n-1) is class
        ability_strings = []
        for idx in range(stat_type_idx + 1, n - 1):
            s = all_strings[idx][1]
            ability_strings.append(s)

        _parse_ability_slots(cat, ability_strings)
        return

    # Fallback: end-relative
    if n >= 16:
        # stat_type at -16
        st_str = all_strings[-16][1]
        if st_str in STAT_TYPES:
            cat.stat_focus = STAT_FOCUS_RU.get(st_str, st_str)

        ability_strings = [all_strings[i][1] for i in range(n - 15, n - 1)]
        _parse_ability_slots(cat, ability_strings)


def _parse_ability_slots(cat: CatData, ability_strings: list[str]):
    """Parse the 14 ability slots into DefaultMove, basic_attack, abilities, passives, items.

    Slot layout (14 slots):
      [0]  DefaultMove
      [1]  basic_attack
      [2]  ability1
      [3]  ability2
      [4]  ability3
      [5]  passive_dup1
      [6]  passive_dup2
      [7]  passive_dup3
      [8]  passive1
      [9]  passive2
      [10] passive3
      [11] item1
      [12] item2
      [13] item3

    But count can vary. If we have exactly 14: use fixed slots.
    If more or less, use heuristics.
    """
    n = len(ability_strings)

    if n == 0:
        return

    # DefaultMove is always first
    if n >= 2:
        cat.basic_attack = ability_strings[1]
        for attack_prefix, cls in ATTACK_TO_CLASS.items():
            if ability_strings[1].startswith(attack_prefix.replace("_", "")):
                if cat.cat_class == "Colorless" and cls != "Colorless":
                    cat.cat_class = cls
                break

    if n >= 14:
        # Standard layout: 14 slots
        # Abilities: slots 2-4
        for s in ability_strings[2:5]:
            if s != "None":
                cat.abilities.append(s)

        # Passives: slots 8-10 (skip dups at 5-7)
        for s in ability_strings[8:11]:
            if s != "None":
                cat.passives.append(s)

        # Items: slots 11-13
        for s in ability_strings[11:14]:
            if s != "None":
                cat.items.append(s)
    elif n >= 10:
        # Variable layout — use end-relative
        # items: last 3
        for s in ability_strings[-3:]:
            if s != "None" and s not in CLASS_RU:
                cat.items.append(s)
        # passives: 3 before items
        for s in ability_strings[-6:-3]:
            if s != "None":
                cat.passives.append(s)
        # abilities: from slot 2 to passives_dup start
        abilities_end = max(n - 9, 2)
        for s in ability_strings[2:abilities_end]:
            if s != "None":
                cat.abilities.append(s)


def parse_cat_blob(cat_id: int, blob: bytes) -> CatData:
    """Parse a cat binary blob from the save database."""
    cat = CatData(id=cat_id)

    if len(blob) < 20:
        return cat

    raw = _decompress_blob(blob)

    # Extract name
    name_len = 0
    if len(raw) >= _NAME_START:
        name_len = struct.unpack_from('<I', raw, _NAME_LEN_OFFSET)[0]
        name_end = _NAME_START + name_len * 2
        if name_end <= len(raw) and 0 < name_len < 50:
            try:
                cat.name = raw[_NAME_START:name_end].decode('utf-16-le')
            except UnicodeDecodeError:
                cat.name = ""

    if not cat.name.strip():
        cat.name = f"Cat #{cat_id}"

    name_byte_end = _NAME_START + name_len * 2

    # Scan all ASCII strings
    all_strings = _scan_ascii_strings(raw, name_byte_end)
    cat.raw_strings = [s for _, s in all_strings]

    if not all_strings:
        return cat

    # === Pre-meta block (gender, flags) ===
    first_string_off = all_strings[0][0]
    gap_to_first = first_string_off - name_byte_end

    if gap_to_first >= _PRE_META_SIZE:
        # Full format
        pre_meta, _, fmt = _parse_pre_meta(raw, name_byte_end, first_string_off)
    else:
        # Compact format
        pre_meta, _, fmt = _parse_pre_meta_compact(raw, all_strings)

    if len(pre_meta) >= 5:
        cat.gender_code = pre_meta[_GENDER_INDEX_A]
        cat.pre_meta_flags = pre_meta[_FLAGS_INDEX]

        # Gender from pre-meta
        if cat.gender_code == _GENDER_MALE:
            cat.gender = "кот"
        elif cat.gender_code == _GENDER_FEMALE:
            cat.gender = "кошка"
        elif cat.gender_code == _GENDER_ANY:
            cat.gender = "любой"

        # Flags
        cat.is_retired = bool(cat.pre_meta_flags & _RETIRED_FLAG)
        cat.is_donated = bool(cat.pre_meta_flags & _DONATED_FLAG)

    # === Equipment block (mutations + appearance frames) ===
    cat.mutations, cat.all_frames, _ = _parse_equipment_block(raw, all_strings)

    # === Stat block (92 bytes between voice and stat_type) ===
    stat_data, voice_idx, stat_type_idx = _find_stat_block(raw, all_strings)
    if stat_data:
        cat.stats = stat_data

    # stat_focus from stat_type string
    if stat_type_idx is not None:
        st_str = all_strings[stat_type_idx][1]
        if st_str in STAT_TYPES:
            cat.stat_focus = STAT_FOCUS_RU.get(st_str, st_str)

    # Voice from voice_idx
    if voice_idx is None:
        # Fallback: find voice by content
        for idx, (off, s) in enumerate(all_strings):
            if re.match(r'^(male|female|spidercat)\d', s):
                voice_idx = idx
                break

    if voice_idx is not None and not cat.voice:
        cat.voice = all_strings[voice_idx][1]
        if not cat.gender:
            for prefix, gender in VOICE_GENDER.items():
                if cat.voice.startswith(prefix):
                    cat.gender = gender
                    break

    # === Death marker ===
    death_byte_dead = _parse_death_marker(raw, all_strings, stat_type_idx)
    flag_dead = bool(cat.pre_meta_flags & _DEAD_FLAG)
    cat.is_dead = death_byte_dead or flag_dead

    # === Classify strings (abilities, passives, items, class) ===
    _classify_strings_saveeditor(cat, all_strings, voice_idx, stat_type_idx)

    # === Trailing data (birth day, parents, inbreeding) ===
    trailing = _parse_trailing_data(raw, all_strings)
    cat.birth_day = trailing.get('birth_day')
    cat.parent_keys = trailing.get('parent_keys', [])
    cat.inbreeding_level = trailing.get('inbreeding', 0)

    # === Status determination (SaveEditor rules) ===
    if cat.is_dead:
        cat.status = "Dead"
    elif not cat.is_donated and any(e < 0 for e in cat.stats.extra):
        cat.status = "Injured"
    else:
        cat.status = "OK"

    return cat


def load_all_cats(save_path: str, current_day: int | None = None) -> list[CatData]:
    """Load all cats from a save file (read-only)."""
    conn = sqlite3.connect(f"file:{save_path}?mode=ro", uri=True)
    cats = []

    # Read current_day from properties for age calculation
    if current_day is None:
        try:
            row = conn.execute("SELECT data FROM properties WHERE key='current_day'").fetchone()
            if row:
                current_day = int(row[0])
        except Exception:
            pass

    try:
        for row in conn.execute("SELECT key, data FROM cats ORDER BY key"):
            cat = parse_cat_blob(row[0], row[1])

            # Calculate age if we have current_day and birth_day
            if current_day is not None and cat.birth_day is not None:
                cat.age_days = max(1, current_day - cat.birth_day)

            cats.append(cat)
    finally:
        conn.close()
    return cats


def get_save_info(save_path: str) -> dict:
    """Get basic save file info (read-only)."""
    conn = sqlite3.connect(f"file:{save_path}?mode=ro", uri=True)
    info = {}
    try:
        for row in conn.execute("SELECT key, data FROM properties"):
            key = row[0]
            if key in ("current_day", "house_gold", "house_food", "save_file_percent",
                       "on_adventure", "house_night", "adventure_coins", "adventure_food",
                       "blank_collars", "house_storage_upgrades"):
                info[key] = row[1]
        info["total_cats"] = conn.execute("SELECT count(*) FROM cats").fetchone()[0]
    finally:
        conn.close()
    return info
