"""Load game descriptions from CSV files for abilities, passives, and items."""

import csv
import os
import re

_GAME_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "game_data")


def _clean_desc(text: str) -> str:
    """Clean game description markup for prompt use."""
    # Remove [img:xxx] tags -> replace with stat name
    text = re.sub(r'\[img:(\w+)\]', lambda m: m.group(1).upper(), text)
    # Remove [s:.7]...[/s] (fine print)
    text = re.sub(r'\[s:[.\d]+\](.*?)\[/s\]', r'\1', text)
    # Remove &nbsp;
    text = text.replace('&nbsp;', ' ')
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _load_csv_descriptions(csv_path: str) -> dict[str, tuple[str, str]]:
    """Load all NAME/DESC pairs from a CSV, keyed by lowercase internal name.

    Handles various prefixes: ABILITY_, ABLITY_, PASSIVE_, DISORDER_,
    ITEM_, ARMOR_, WEAPON_, CONSUMABLE_, etc.
    """
    entries = {}  # lowercase_key -> {NAME: ..., DESC: ...}

    if not os.path.exists(csv_path):
        return {}

    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        for row in csv.reader(f):
            if len(row) < 2 or row[0].startswith('//') or 'KEY' in row[0]:
                continue
            key, ru = row[0], row[1]
            if not ru:
                continue

            # Match any PREFIX_INTERNALNAME[digits]_NAME/DESC
            m = re.match(r'[A-Z]+_(.+?)(\d*)_(NAME|DESC)$', key)
            if m:
                raw_name = m.group(1).lower().replace('_', '')
                level = m.group(2) or ''
                field_type = m.group(3)
                # Only keep base level (no suffix) or level 2
                full_key = raw_name + level
                if full_key not in entries:
                    entries[full_key] = {}
                entries[full_key][field_type] = ru

    result = {}
    for lc_key, fields in entries.items():
        name = fields.get('NAME', '')
        desc = _clean_desc(fields.get('DESC', ''))
        if name or desc:
            result[lc_key] = (name, desc)
    return result


def _load_mutation_descriptions(csv_path: str) -> dict[str, str]:
    """Load mutation descriptions keyed by 'PART_FRAME' e.g. 'body_301'."""
    result = {}
    if not os.path.exists(csv_path):
        return result

    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        for row in csv.reader(f):
            if len(row) < 2 or row[0].startswith('//') or 'KEY' in row[0]:
                continue
            key, ru = row[0], row[1]
            if not ru:
                continue
            # MUTATION_BODY_301_DESC -> body_301
            m = re.match(r'MUTATION_(\w+?)_(\d+)_DESC$', key)
            if m:
                part = m.group(1).lower()
                frame = m.group(2)
                result[f"{part}_{frame}"] = _clean_desc(ru)

    return result


class GameDescriptions:
    """Lazy-loaded game description database."""

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

    def _lookup(self, db: dict, internal_name: str) -> tuple[str, str] | None:
        """Lookup by internal CamelCase name -> (ru_name, ru_desc)."""
        lc = internal_name.lower()
        return db.get(lc)

    def get_ability(self, name: str) -> tuple[str, str] | None:
        self._ensure_loaded()
        # Try abilities first, then passives (some overlap)
        return self._lookup(self._abilities, name) or self._lookup(self._passives, name)

    def get_passive(self, name: str) -> tuple[str, str] | None:
        self._ensure_loaded()
        return self._lookup(self._passives, name) or self._lookup(self._abilities, name)

    def get_item(self, name: str) -> tuple[str, str] | None:
        self._ensure_loaded()
        return self._lookup(self._items, name) or self._lookup(self._passives, name)

    def describe_ability_for_prompt(self, name: str) -> str:
        """Get a concise English-style visual description for an ability."""
        info = self.get_ability(name)
        if info:
            ru_name, ru_desc = info
            return f"{name} ({ru_name}): {ru_desc}"
        return name

    def describe_passive_for_prompt(self, name: str) -> str:
        info = self.get_passive(name)
        if info:
            ru_name, ru_desc = info
            return f"{name} ({ru_name}): {ru_desc}"
        return name

    def describe_item_for_prompt(self, name: str) -> str:
        info = self.get_item(name)
        if info:
            ru_name, ru_desc = info
            return f"{name} ({ru_name}): {ru_desc}"
        return name

    def get_mutation(self, part: str, frame: int) -> str | None:
        """Get mutation description by part name and frame number.

        Part names in CSV use singular mapped forms:
        - leftear/rightear -> ears
        - lefteye/righteye -> eyes
        - lefteyebrow/righteyebrow -> eyebrows
        - leg1/leg2 -> legs
        - arm1/arm2 -> arms
        """
        self._ensure_loaded()
        # Map parser part names to CSV part names
        part_map = {
            'leftear': 'ears', 'rightear': 'ears',
            'lefteye': 'eyes', 'righteye': 'eyes',
            'lefteyebrow': 'eyebrows', 'righteyebrow': 'eyebrows',
            'leg1': 'legs', 'leg2': 'legs',
            'arm1': 'arms', 'arm2': 'arms',
        }
        csv_part = part_map.get(part, part)
        return self._mutations.get(f"{csv_part}_{frame}")


# Singleton
game_desc = GameDescriptions()
