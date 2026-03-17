"""
Hero Import/Export – JSON-based system for importing and exporting player characters.
Uses the generic serialization system for all dataclass models.
"""
import json
import os
from typing import List
from data.models import CreatureStats
from data.serialization import serialize, deserialize


def export_hero(hero: CreatureStats) -> dict:
    """Export a CreatureStats hero to a JSON-serializable dictionary."""
    return serialize(hero)


def import_hero(data: dict) -> CreatureStats:
    """Import a hero from a dictionary (parsed JSON).
    Backward-compatible: missing fields get their defaults automatically."""
    return deserialize(CreatureStats, data)


# ------------------------------------------------------------------ #
# File I/O                                                             #
# ------------------------------------------------------------------ #

def export_hero_to_file(hero: CreatureStats, filepath: str):
    """Export hero to a JSON file."""
    data = export_hero(hero)
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)


def import_hero_from_file(filepath: str) -> CreatureStats:
    """Import a hero from a JSON file."""
    with open(filepath) as f:
        data = json.load(f)
    return import_hero(data)


def import_heroes_from_file(filepath: str) -> List[CreatureStats]:
    """Import multiple heroes from a JSON file (supports both single and array)."""
    with open(filepath) as f:
        data = json.load(f)
    if isinstance(data, list):
        return [import_hero(h) for h in data]
    return [import_hero(data)]


def export_heroes_to_file(heroes: List[CreatureStats], filepath: str):
    """Export multiple heroes to a JSON file."""
    data = [export_hero(h) for h in heroes]
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)
