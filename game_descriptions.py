"""Load game descriptions from CSV files for abilities, passives, and items.

CSV format: KEY,en,ru
Supports language selection via `lang` parameter (default: 'ru').
"""

import csv
import os
import re

_GAME_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "game_data")


def _clean_desc(text: str) -> str:
    """Clean game description markup."""
    text = re.sub(r'\[img:(\w+)\]', lambda m: m.group(1).upper(), text)
    text = re.sub(r'\[s:[.\d]+\](.*?)\[/s\]', r'\1', text)
    text = text.replace('&nbsp;', ' ')
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _load_csv_descriptions(csv_path: str) -> dict[str, dict[str, tuple[str, str]]]:
    """Load all NAME/DESC pairs from a CSV, keyed by lowercase internal name.

    Returns: {lowercase_key: {'en': (name, desc), 'ru': (name, desc)}}
    """
    entries = {}  # lowercase_key -> {lang: {NAME: ..., DESC: ...}}

    if not os.path.exists(csv_path):
        return {}

    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = row.get('KEY', '')
            if not key or key.startswith('//'):
                continue

            m = re.match(r'[A-Z]+_(.+?)(\d*)_(NAME|DESC)$', key)
            if not m:
                continue

            raw_name = m.group(1).lower().replace('_', '')
            level = m.group(2) or ''
            field_type = m.group(3)
            full_key = raw_name + level

            if full_key not in entries:
                entries[full_key] = {}

            for lang in ('en', 'ru'):
                val = row.get(lang, '')
                if val:
                    if lang not in entries[full_key]:
                        entries[full_key][lang] = {}
                    entries[full_key][lang][field_type] = val

    result = {}
    for lc_key, lang_data in entries.items():
        result[lc_key] = {}
        for lang, fields in lang_data.items():
            name = fields.get('NAME', '')
            desc = _clean_desc(fields.get('DESC', ''))
            if name or desc:
                result[lc_key][lang] = (name, desc)
    return result


def _load_mutation_descriptions(csv_path: str) -> dict[str, dict[str, str]]:
    """Load mutation descriptions keyed by 'PART_FRAME'.

    Returns: {part_frame: {'en': desc, 'ru': desc}}
    """
    result = {}
    if not os.path.exists(csv_path):
        return result

    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = row.get('KEY', '')
            if not key or key.startswith('//'):
                continue
            m = re.match(r'MUTATION_(\w+?)_(\d+)_DESC$', key)
            if m:
                part = m.group(1).lower()
                frame = m.group(2)
                pk = f"{part}_{frame}"
                result[pk] = {}
                for lang in ('en', 'ru'):
                    val = row.get(lang, '')
                    if val:
                        result[pk][lang] = _clean_desc(val)

    return result


class GameDescriptions:
    """Lazy-loaded game description database with multi-language support."""

    def __init__(self):
        self._abilities = None
        self._passives = None
        self._items = None
        self._mutations = None

    def _ensure_loaded(self):
        if self._abilities is not None:
            return
        self._abilities = _load_csv_descriptions(
            os.path.join(_GAME_DATA_DIR, "abilities.csv"))
        self._passives = _load_csv_descriptions(
            os.path.join(_GAME_DATA_DIR, "passives.csv"))
        self._items = _load_csv_descriptions(
            os.path.join(_GAME_DATA_DIR, "items.csv"))
        self._mutations = _load_mutation_descriptions(
            os.path.join(_GAME_DATA_DIR, "mutations.csv"))

    def _lookup(self, db: dict, internal_name: str, lang: str = 'ru') -> tuple[str, str] | None:
        """Lookup by internal CamelCase name -> (name, desc) in given language."""
        lc = internal_name.lower()
        entry = db.get(lc)
        if not entry:
            return None
        # Try requested lang, fallback to en, then ru
        return entry.get(lang) or entry.get('en') or entry.get('ru')

    def get_ability(self, name: str, lang: str = 'ru') -> tuple[str, str] | None:
        self._ensure_loaded()
        return self._lookup(self._abilities, name, lang) or self._lookup(self._passives, name, lang)

    def get_passive(self, name: str, lang: str = 'ru') -> tuple[str, str] | None:
        self._ensure_loaded()
        return self._lookup(self._passives, name, lang) or self._lookup(self._abilities, name, lang)

    def get_item(self, name: str, lang: str = 'ru') -> tuple[str, str] | None:
        self._ensure_loaded()
        return self._lookup(self._items, name, lang) or self._lookup(self._passives, name, lang)

    def get_mutation(self, part: str, frame: int, lang: str = 'ru') -> str | None:
        self._ensure_loaded()
        part_map = {
            'leftear': 'ears', 'rightear': 'ears',
            'lefteye': 'eyes', 'righteye': 'eyes',
            'lefteyebrow': 'eyebrows', 'righteyebrow': 'eyebrows',
            'leg1': 'legs', 'leg2': 'legs',
            'arm1': 'arms', 'arm2': 'arms',
        }
        csv_part = part_map.get(part, part)
        entry = self._mutations.get(f"{csv_part}_{frame}")
        if not entry:
            return None
        return entry.get(lang) or entry.get('en') or entry.get('ru')


# Singleton
game_desc = GameDescriptions()
