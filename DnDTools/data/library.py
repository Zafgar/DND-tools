import copy
from data.models import CreatureStats
from data.monsters.cr_018 import monsters as cr018_list
from data.monsters.cr_025 import monsters as cr025_list
from data.monsters.cr_05  import monsters as cr05_list
from data.monsters.cr_1   import monsters as cr1_list
from data.monsters.cr_2   import monsters as cr2_list
from data.monsters.cr_3   import monsters as cr3_list
from data.monsters.cr_4   import monsters as cr4_list
from data.monsters.cr_5   import monsters as cr5_list
from data.monsters.cr_67  import monsters as cr67_list
from data.monsters.cr_8   import monsters as cr8_list
from data.monsters.cr_910 import monsters as cr910_list
from data.monsters.cr_1112 import monsters as cr1112_list
from data.monsters.cr_13  import monsters as cr13_list
from data.monsters.cr_1416 import monsters as cr1416_list
from data.monsters.cr_17plus import monsters as cr17_list


class MonsterLibrary:
    def __init__(self):
        self._monsters: dict[str, CreatureStats] = {}
        for lst in [cr018_list, cr025_list, cr05_list, cr1_list,
                    cr2_list, cr3_list, cr4_list, cr5_list, cr67_list,
                    cr8_list, cr910_list, cr1112_list, cr13_list, cr1416_list, cr17_list]:
            self._load_list(lst)

    def _load_list(self, monster_list):
        for m in monster_list:
            self._monsters[m.name.lower()] = m

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


library = MonsterLibrary()
