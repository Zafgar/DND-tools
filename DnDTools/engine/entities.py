from settings import COLORS
from data.models import CreatureStats
import random
import copy

class Entity:
    def __init__(self, stats: CreatureStats, x, y, is_player=False):
        self.stats = stats
        self.name = stats.name
        self.grid_x = x
        self.grid_y = y
        self.is_player = is_player
        
        # Dynaamiset arvot (jotka muuttuvat taistelun aikana)
        self.hp = stats.hit_points
        self.max_hp = stats.hit_points
        self.color = COLORS["player"] if is_player else COLORS["enemy"]
        self.initiative = 0
        self.conditions = set()
        
        # Resurssit ja vuoron tila
        self.spell_slots = copy.deepcopy(stats.spell_slots)
        self.action_used = False
        self.bonus_action_used = False
        self.movement_left = stats.speed

    def get_modifier(self, ability: str) -> int:
        return self.stats.abilities.get_mod(ability)

    def roll_initiative(self):
        dex_mod = self.get_modifier("dexterity")
        self.initiative = random.randint(1, 20) + dex_mod
        return self.initiative

    def add_condition(self, condition: str):
        """Lisää statuksen, jos olento ei ole immuuni sille."""
        if condition.lower() not in [x.lower() for x in self.stats.condition_immunities]:
            self.conditions.add(condition)

    def remove_condition(self, condition: str):
        self.conditions.discard(condition)

    def has_condition(self, condition: str) -> bool:
        return condition in self.conditions

    def reset_turn(self):
        """Kutsutaan vuoron alussa."""
        self.action_used = False
        self.bonus_action_used = False
        self.movement_left = self.stats.speed

    def long_rest(self):
        """Palauttaa HP:t ja spell slotit."""
        self.hp = self.max_hp
        self.spell_slots = copy.deepcopy(self.stats.spell_slots)
        self.conditions.clear()