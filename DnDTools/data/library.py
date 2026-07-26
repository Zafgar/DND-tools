"""
Monster Library – loads monsters from JSON files (preferred) or Python modules (fallback).
JSON files are in data/monsters/json/ and can be edited without code changes.
"""
import os
import json
import copy
from data.models import CreatureStats
from data.serialization import deserialize


def _rebind_spells(stats):
    """Bind a stat block's spells to the central library (single source of
    truth). Tolerant of any import/lookup failure."""
    try:
        from data.spells import rebind_to_library
        rebind_to_library(stats)
    except Exception:
        pass


class MonsterLibrary:
    def __init__(self):
        self._monsters: dict[str, CreatureStats] = {}
        self._load_json_monsters()
        # Phase 37 — always load Python modules so additions made
        # there (new bosses, lore enrichments) merge with JSON. JSON
        # entries win on key clash; Python supplies the gaps.
        self._load_python_monsters()

    def _load_json_monsters(self):
        """Load monsters from JSON files in data/monsters/json/."""
        json_dir = os.path.join(os.path.dirname(__file__), "monsters", "json")
        if not os.path.isdir(json_dir):
            return
        for filename in sorted(os.listdir(json_dir)):
            if not filename.endswith(".json"):
                continue
            filepath = os.path.join(json_dir, filename)
            try:
                with open(filepath, encoding="utf-8") as f:
                    data_list = json.load(f)
                for data in data_list:
                    monster = deserialize(CreatureStats, data)
                    _rebind_spells(monster)
                    self._monsters[monster.name.lower()] = monster
            except Exception as ex:
                print(f"Warning: Failed to load {filename}: {ex}")

    def _load_python_monsters(self):
        """Fallback: load from Python modules (legacy format)."""
        try:
            from data.monsters.cr_018 import monsters as cr018_list
            from data.monsters.cr_025 import monsters as cr025_list
            from data.monsters.cr_05 import monsters as cr05_list
            from data.monsters.cr_1 import monsters as cr1_list
            from data.monsters.cr_2 import monsters as cr2_list
            from data.monsters.cr_3 import monsters as cr3_list
            from data.monsters.cr_4 import monsters as cr4_list
            from data.monsters.cr_5 import monsters as cr5_list
            from data.monsters.cr_67 import monsters as cr67_list
            from data.monsters.cr_8 import monsters as cr8_list
            from data.monsters.cr_910 import monsters as cr910_list
            from data.monsters.cr_1112 import monsters as cr1112_list
            from data.monsters.cr_13 import monsters as cr13_list
            from data.monsters.cr_1416 import monsters as cr1416_list
            from data.monsters.cr_17plus import monsters as cr17_list
            # Campaign-specific bosses & soldiers (Novus Somnium).
            from data.monsters.baenrahel import monsters as baenrahel_list
            from data.monsters.whitestone import monsters as whitestone_list
            from data.monsters.zertath import monsters as zertath_list
            from data.monsters.lvl12_foes import monsters as lvl12_list
            from data.monsters.deaths_vigil import monsters as vigil_list
            from data.monsters.ravenstone import monsters as ravenstone_list
            from data.monsters.legends import monsters as legends_list

            for lst in [cr018_list, cr025_list, cr05_list, cr1_list,
                        cr2_list, cr3_list, cr4_list, cr5_list, cr67_list,
                        cr8_list, cr910_list, cr1112_list, cr13_list, cr1416_list, cr17_list,
                        baenrahel_list, whitestone_list, zertath_list,
                        lvl12_list, vigil_list, ravenstone_list,
                        legends_list]:
                for m in lst:
                    # Don't overwrite a JSON-loaded entry; Python is
                    # a fallback / supplement for the JSON catalogue.
                    if m.name.lower() not in self._monsters:
                        _rebind_spells(m)
                        self._monsters[m.name.lower()] = m
        except ImportError as ex:
            print(f"Warning: Failed to load Python monster modules: {ex}")

    def get_monster(self, name: str) -> CreatureStats:
        key = name.lower()
        if key in self._monsters:
            return copy.deepcopy(self._monsters[key])
        raise ValueError(f"Monster '{name}' not found in library.")

    def get_all_monsters(self) -> list:
        return sorted(self._monsters.values(), key=lambda m: m.challenge_rating)

    def get_monsters_by_cr(self, cr: float) -> list:
        return [copy.deepcopy(m) for m in self._monsters.values() if m.challenge_rating == cr]

    def get_cr_list(self) -> list:
        return sorted(set(m.challenge_rating for m in self._monsters.values()))

    def reload(self):
        """Reload all monsters (useful after editing JSON files)."""
        self._monsters.clear()
        self._load_json_monsters()
        if not self._monsters:
            self._load_python_monsters()


library = MonsterLibrary()
