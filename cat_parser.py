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


def _parse_stats(raw: bytes, strings: list[tuple[int, str]]) -> tuple[CatStats, str]:
    """Find the 92-byte stat block and stat_type from string fields."""
    stats = CatStats()
    stat_type = "none"

    # Find stat_type string (it's right after the stat block)
    for idx, (off, s) in enumerate(strings):
        if s in STAT_TYPES:
            stat_type = s
            stat_block_start = off - _STAT_BLOCK_SIZE
            if stat_block_start >= 0:
                block = raw[stat_block_start:off]
                stats.base = [struct.unpack_from('<i', block, _STAT_BASE_OFFSET + j*4)[0]
                              for j in range(_STAT_COUNT)]
                stats.bonus = [struct.unpack_from('<i', block, _STAT_BONUS_OFFSET + j*4)[0]
                               for j in range(_STAT_COUNT)]
                stats.extra = [struct.unpack_from('<i', block, _STAT_EXTRA_OFFSET + j*4)[0]
                               for j in range(_STAT_COUNT)]
            break

    return stats, stat_type


def _parse_mutations(raw: bytes, all_strings: list[tuple[int, str]]) -> dict[str, int]:
    """Parse 368-byte equipment block between breed and voice strings to find mutations.

    Returns dict of part_name -> frame_number for mutated parts (frame >= 300).
    """
    # Find voice string offset (it's right after equipment block)
    voice_off = None
    breed_end = None
    for idx, (off, s) in enumerate(all_strings):
        if re.match(r'^(male|female|spidercat)\d', s):
            voice_off = off
            # Breed is the string(s) before voice; equipment block sits between
            # breed end and voice start
            if idx > 0:
                prev_off, prev_s = all_strings[idx - 1]
                breed_end = prev_off + 8 + len(prev_s)
            break

    if voice_off is None or breed_end is None:
        return {}

    equip_block_start = breed_end
    equip_block_end = voice_off
    block_size = equip_block_end - equip_block_start

    if block_size != _EQUIP_BLOCK_SIZE:
        return {}

    block = raw[equip_block_start:equip_block_end]
    mutations = {}
    for offset, part_name in _EQUIP_BLOCK_PART_OFFSETS:
        if offset + 4 <= len(block):
            frame = struct.unpack_from('<I', block, offset)[0]
            if _MUTATION_FRAME_THRESHOLD <= frame <= 10000:
                mutations[part_name] = frame

    return mutations


def parse_cat_blob(cat_id: int, blob: bytes) -> CatData:
    """Parse a cat binary blob from the save database."""
    cat = CatData(id=cat_id)

    if len(blob) < 20:
        return cat

    raw = _decompress_blob(blob)

    # Extract name
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
    name_byte_end = _NAME_START + (name_len * 2 if 'name_len' in dir() else 0)
    all_strings = _scan_ascii_strings(raw, name_byte_end)
    cat.raw_strings = [s for _, s in all_strings]

    # Parse stats
    cat.stats, stat_type_str = _parse_stats(raw, all_strings)
    cat.stat_focus = STAT_FOCUS_RU.get(stat_type_str, stat_type_str)

    # Parse mutations from equipment block
    cat.mutations = _parse_mutations(raw, all_strings)

    # Check for injuries (negative extra stats)
    has_negative_extra = any(e < 0 for e in cat.stats.extra)

    # Classify strings using end-relative indexing
    n = len(all_strings)
    if n >= 2:
        # Class is always last string
        class_str = all_strings[-1][1]
        if class_str in CLASS_RU:
            cat.cat_class = class_str

        # Voice is at a known position from end
        # Find voice string (matches pattern like male5, female33, spidercat1)
        for idx, (off, s) in enumerate(all_strings):
            if re.match(r'^(male|female|spidercat)\d', s):
                cat.voice = s
                for prefix, gender in VOICE_GENDER.items():
                    if s.startswith(prefix):
                        cat.gender = gender
                        break
                break

        # Basic attack is at end-14 (for 18 strings) or generally the string after DefaultMove
        for idx, (off, s) in enumerate(all_strings):
            if s == "DefaultMove" and idx + 1 < n:
                attack_str = all_strings[idx + 1][1]
                cat.basic_attack = attack_str
                # Determine class from basic attack if not already set
                for attack_prefix, cls in ATTACK_TO_CLASS.items():
                    if attack_str.startswith(attack_prefix.replace("_", "")):
                        if cat.cat_class == "Colorless" and cls != "Colorless":
                            cat.cat_class = cls
                        break
                break

        # String layout from end:
        # -1: class
        # -2, -3, -4: items (can be "None")
        # -5, -6, -7: passives (can be "None")
        # -8, -9, -10: passive ability duplicates
        # -11, -12, -13: active abilities
        # -14: basic attack
        # -15: DefaultMove
        # -16: stat_type
        # -17: voice
        # -18+: breed

        # Active abilities: between DefaultMove+basic_attack and the passive dup section
        # Find DefaultMove index
        dm_idx = None
        for idx, (off, s) in enumerate(all_strings):
            if s == "DefaultMove":
                dm_idx = idx
                break

        if dm_idx is not None and n >= 18:
            # Active abilities: dm_idx+2 to dm_idx+2+ability_count
            # The number of ability slots varies. Basic pattern:
            # After basic_attack, abilities go until we hit the passive dup section

            # Items: from end-2 backwards, up to 3 slots (before class)
            items_start = max(n - 4, 0)
            items_end = n - 1  # exclusive (class is at n-1)
            for idx in range(items_start, items_end):
                s = all_strings[idx][1]
                if s != "None":
                    cat.items.append(s)

            # Passives: 3 slots before items
            passives_start = max(n - 7, 0)
            passives_end = items_start
            for idx in range(passives_start, passives_end):
                s = all_strings[idx][1]
                if s != "None":
                    cat.passives.append(s)

            # Active abilities: from basic_attack+1 up to passive dup area
            # Standard 18-string cat: 3 ability slots (dm+2..dm+4)
            # Extra strings = more abilities or items
            # The passive dup section starts at n-10 for standard cats
            extra = n - 18  # how many extra string slots beyond standard
            abilities_start = dm_idx + 2
            abilities_end = max(n - 10 - extra, abilities_start)
            # Safer: count abilities as everything between basic_attack
            # and the first repeated/dup section
            # The dup section starts at n - 10
            abilities_end = n - 10
            seen_abilities = set()
            for idx in range(abilities_start, max(abilities_end, abilities_start)):
                s = all_strings[idx][1]
                if s != "None" and s not in seen_abilities:
                    cat.abilities.append(s)
                    seen_abilities.add(s)

    # Determine status
    # Check death: look for pre-meta flags
    if has_negative_extra:
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
