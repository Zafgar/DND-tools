import copy
from data.models import CreatureStats

# Tuodaan monsterit eri moduuleista
from data.monsters.cr_1 import monsters as cr1_list

class MonsterLibrary:
    def __init__(self):
        self._monsters = {}
        
        # Ladataan kaikki listat kirjastoon
        self._load_list(cr1_list)

    def _load_list(self, monster_list):
        for m in monster_list:
            self._monsters[m.name.lower()] = m

    def get_monster(self, name: str) -> CreatureStats:
        """Hakee monsterin nimen perusteella ja palauttaa siitä uuden kopion."""
        key = name.lower()
        if key in self._monsters:
            return copy.deepcopy(self._monsters[key])
        raise ValueError(f"Monster '{name}' not found in library.")

    def get_all_monsters(self) -> list[CreatureStats]:
        """Palauttaa listan kaikista monstereista järjestettynä CR:n mukaan."""
        return sorted(self._monsters.values(), key=lambda m: m.challenge_rating)

# Globaali instanssi
library = MonsterLibrary()