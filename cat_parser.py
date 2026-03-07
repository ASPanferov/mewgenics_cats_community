"""Parser for Mewgenics save files (.sav SQLite databases).

Cat blobs are LZ4-compressed. After decompression:
  - Header: [u32 unknown][u64 uid][u32 name_len_chars]
  - Name: UTF-16LE, name_len_chars * 2 bytes
  - Pre-meta block: gender/flags
  - ASCII strings: [u32 strlen][u32 pad=0][ascii bytes]
  - 92-byte stat block between voice and stat_type strings:
    [f64 seed][7×i32 base][7×i32 bonus][7×i32 extra]
  - String fields (end-relative):
    -1=class, -2..-4=items, -5..-7=passives, -8..-10=passive_dups,
    -11..-13=abilities, -14=basic_attack, -15=default_move,
    -16=stat_type, -17=voice, -18+=breed
"""

import sqlite3
import struct
import os
import re
from dataclasses import dataclass, field

import lz4.block


# Name field offsets in decompressed blob
_NAME_LEN_OFFSET = 12   # u32 name length in UTF-16 chars
_NAME_START = 20         # UTF-16LE name bytes start here

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
    (280, 'righteyebrow'), (300, 'leftear'), (320, 'rightear'),
    (340, 'mouth'),
)
_MUTATION_FRAME_THRESHOLD = 300
_BIRTH_DEFECT_FRAME_THRESHOLD = 700

# Part name -> Russian display
PART_NAME_RU = {
    'texture': 'Текстура', 'body': 'Тело', 'head': 'Голова', 'tail': 'Хвост',
    'leg1': 'Нога 1', 'leg2': 'Нога 2', 'arm1': 'Рука 1', 'arm2': 'Рука 2',
    'lefteye': 'Левый глаз', 'righteye': 'Правый глаз',
    'lefteyebrow': 'Левая бровь', 'righteyebrow': 'Правая бровь',
    'leftear': 'Левое ухо', 'rightear': 'Правое ухо', 'mouth': 'Рот',
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

# Class name -> Russian
CLASS_RU = {
    "Fighter": "Боец",
    "Tank": "Танк",
    "Hunter": "Охотник",
    "Mage": "Маг",
    "Medic": "Медик",
    "Necromancer": "Некромант",
    "Druid": "Друид",
    "Thief": "Вор",
    "Tinkerer": "Механик",
    "Colorless": "Бесцветный",
    "Monk": "Монах",
    "Jester": "Шут",
    "Psychic": "Психик",
    "Butcher": "Мясник",
}

# Voice prefix -> gender display
VOICE_GENDER = {
    "male": "кот",
    "female": "кошка",
    "spidercat": "кот-паук",
}

# Stat focus labels
STAT_FOCUS_RU = {
    "str": "Сила",
    "spd": "Скорость",
    "lck": "Удача",
    "int": "Интеллект",
    "dex": "Ловкость",
    "cha": "Харизма",
    "con": "Выносливость",
    "none": "Нет",
    "burned": "Обожжённый",
    "poisoned": "Отравленный",
    "bleeding": "Кровотечение",
}


@dataclass
class CatStats:
    base: list = field(default_factory=lambda: [0]*7)
    bonus: list = field(default_factory=lambda: [0]*7)
    extra: list = field(default_factory=lambda: [0]*7)

    @property
    def effective(self) -> list:
        return [b + bn + e for b, bn, e in zip(self.base, self.bonus, self.extra)]


@dataclass
class CatData:
    id: int = 0
    name: str = ""
    voice: str = ""
    gender: str = ""
    stat_focus: str = ""
    cat_class: str = "Colorless"
    basic_attack: str = ""
    abilities: list = field(default_factory=list)
    passives: list = field(default_factory=list)
    items: list = field(default_factory=list)
    mutations: dict = field(default_factory=dict)  # part_name -> frame_number
    stats: CatStats = field(default_factory=CatStats)
    status: str = "OK"  # OK, Injured, Dead
    raw_strings: list = field(default_factory=list)


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


def _find_voice_idx(strings: list[tuple[int, str]]) -> int | None:
    """Find index of voice string (male5, female33, spidercat1 etc)."""
    for idx, (off, s) in enumerate(strings):
        if re.match(r'^(male|female|spidercat)\d', s):
            return idx
    return None


def _find_dm_idx(strings: list[tuple[int, str]]) -> int | None:
    """Find index of DefaultMove string."""
    for idx, (off, s) in enumerate(strings):
        if s == "DefaultMove":
            return idx
    return None


def _parse_stats_anchored(raw: bytes, strings: list[tuple[int, str]], voice_idx: int) -> tuple[CatStats, str]:
    """Find the 92-byte stat block using voice string as anchor.

    Layout: voice_string -> 92-byte stat block -> stat_type_string
    The stat_type is the string right AFTER voice.
    """
    stats = CatStats()
    stat_type = "none"

    if voice_idx is None or voice_idx + 1 >= len(strings):
        return stats, stat_type

    # stat_type is the next string after voice
    st_off, st_str = strings[voice_idx + 1]
    if st_str in STAT_TYPES:
        stat_type = st_str
    else:
        # Fallback: sometimes there's an extra string between voice and stat_type
        # Try the one after
        if voice_idx + 2 < len(strings):
            st_off2, st_str2 = strings[voice_idx + 2]
            if st_str2 in STAT_TYPES:
                stat_type = st_str2
                st_off = st_off2

    # Stat block is the 92 bytes immediately before stat_type string
    stat_block_start = st_off - _STAT_BLOCK_SIZE
    if stat_block_start >= 0:
        block = raw[stat_block_start:st_off]
        if len(block) == _STAT_BLOCK_SIZE:
            stats.base = [struct.unpack_from('<i', block, _STAT_BASE_OFFSET + j*4)[0]
                          for j in range(_STAT_COUNT)]
            stats.bonus = [struct.unpack_from('<i', block, _STAT_BONUS_OFFSET + j*4)[0]
                           for j in range(_STAT_COUNT)]
            stats.extra = [struct.unpack_from('<i', block, _STAT_EXTRA_OFFSET + j*4)[0]
                           for j in range(_STAT_COUNT)]

            # Sanity check: if values look like garbage, reset
            all_vals = stats.base + stats.bonus + stats.extra
            if any(abs(v) > 1000 for v in all_vals):
                stats = CatStats()

    return stats, stat_type


def _parse_mutations(raw: bytes, all_strings: list[tuple[int, str]], voice_idx: int) -> dict[str, int]:
    """Parse equipment block between breed and voice strings to find mutations.

    Returns dict of part_name -> frame_number for mutated parts (frame >= 300).
    """
    if voice_idx is None or voice_idx < 1:
        return {}

    voice_off = all_strings[voice_idx][0]

    # Breed is the string before voice. There might be 1 or 2 breed strings.
    # Equipment block sits between last breed string end and voice start.
    # Try with immediate predecessor first.
    for back in range(1, min(4, voice_idx + 1)):
        prev_off, prev_s = all_strings[voice_idx - back]
        breed_end = prev_off + 8 + len(prev_s)
        block_size = voice_off - breed_end

        if _EQUIP_BLOCK_SIZE - 8 <= block_size <= _EQUIP_BLOCK_SIZE + 8:
            # Close enough to expected size
            block = raw[breed_end:voice_off]
            mutations = {}
            for offset, part_name in _EQUIP_BLOCK_PART_OFFSETS:
                if offset + 4 <= len(block):
                    frame = struct.unpack_from('<I', block, offset)[0]
                    if _MUTATION_FRAME_THRESHOLD <= frame <= 10000:
                        mutations[part_name] = frame
            return mutations

    return {}


def _classify_strings(cat: CatData, all_strings: list[tuple[int, str]],
                       voice_idx: int | None, dm_idx: int | None):
    """Classify strings into abilities, passives, items using anchor positions.

    Anchors: voice_idx, dm_idx (DefaultMove), and class at end.

    Layout from DefaultMove forward:
      dm_idx:   DefaultMove
      dm_idx+1: basic_attack
      dm_idx+2..dm_idx+N: abilities (3 slots)
      next 3: passive dups (copies of passives)
      next 3: passives
      next 3: items
      last:   class

    Layout from end:
      -1:      class
      -2..-4:  items
      -5..-7:  passives
      -8..-10: passive dups
      -11+:    abilities (up to basic_attack)
    """
    n = len(all_strings)

    # Class is always last string
    if n >= 1:
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

    # Basic attack (right after DefaultMove)
    if dm_idx is not None and dm_idx + 1 < n:
        attack_str = all_strings[dm_idx + 1][1]
        cat.basic_attack = attack_str
        for attack_prefix, cls in ATTACK_TO_CLASS.items():
            if attack_str.startswith(attack_prefix.replace("_", "")):
                if cat.cat_class == "Colorless" and cls != "Colorless":
                    cat.cat_class = cls
                break

    # Parse from the END — most reliable since class is always last
    # -1: class
    # -2, -3, -4: items
    # -5, -6, -7: passives
    # -8, -9, -10: passive dups
    # -11+: abilities until basic_attack

    if n < 10:
        # Not enough strings to parse
        return

    # Items: 3 slots from end (n-4, n-3, n-2), before class (n-1)
    for idx in range(max(n - 4, 0), n - 1):
        s = all_strings[idx][1]
        if s != "None" and s not in CLASS_RU and s not in STAT_TYPES:
            cat.items.append(s)

    # Passives: 3 slots before items (n-7, n-6, n-5)
    for idx in range(max(n - 7, 0), max(n - 4, 0)):
        s = all_strings[idx][1]
        if s != "None" and s not in CLASS_RU:
            cat.passives.append(s)

    # Abilities: from basic_attack+1 to passive_dups start (n-10)
    # Passive dups are at n-10, n-9, n-8
    abilities_end = max(n - 10, 0)

    if dm_idx is not None and dm_idx + 2 <= abilities_end:
        abilities_start = dm_idx + 2
    else:
        # Fallback: abilities are right after basic_attack
        # basic_attack is at n-14 for standard 18-string cats
        # But we can also guess: anything between dm+2 and n-10
        abilities_start = abilities_end  # no abilities

    seen = set()
    for idx in range(abilities_start, abilities_end):
        s = all_strings[idx][1]
        if s != "None" and s not in seen:
            cat.abilities.append(s)
            seen.add(s)


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
        cat.name = f"Кот #{cat_id}"

    # Scan all ASCII strings
    name_byte_end = _NAME_START + name_len * 2
    all_strings = _scan_ascii_strings(raw, name_byte_end)
    cat.raw_strings = [s for _, s in all_strings]

    # Find anchor strings
    voice_idx = _find_voice_idx(all_strings)
    dm_idx = _find_dm_idx(all_strings)

    # Parse stats using voice anchor
    cat.stats, stat_type_str = _parse_stats_anchored(raw, all_strings, voice_idx)
    cat.stat_focus = STAT_FOCUS_RU.get(stat_type_str, stat_type_str)

    # Parse mutations from equipment block
    cat.mutations = _parse_mutations(raw, all_strings, voice_idx)

    # Classify strings into abilities, passives, items, class
    _classify_strings(cat, all_strings, voice_idx, dm_idx)

    # Determine status from injuries (negative extra stats)
    if any(e < 0 for e in cat.stats.extra):
        cat.status = "Injured"

    return cat


def load_all_cats(save_path: str) -> list[CatData]:
    """Load all cats from a save file (read-only)."""
    conn = sqlite3.connect(f"file:{save_path}?mode=ro", uri=True)
    cats = []
    try:
        for row in conn.execute("SELECT key, data FROM cats ORDER BY key"):
            cat = parse_cat_blob(row[0], row[1])
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
                       "on_adventure", "house_night"):
                info[key] = row[1]
        info["total_cats"] = conn.execute("SELECT count(*) FROM cats").fetchone()[0]
    finally:
        conn.close()
    return info
