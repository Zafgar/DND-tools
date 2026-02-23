import random
import copy
import math
from settings import COLORS
from data.models import CreatureStats, SpellInfo, Item
from data.conditions import INCAPACITATING_CONDITIONS, SPEED_ZERO_CONDITIONS


class Entity:
    def __init__(self, stats: CreatureStats, x: float, y: float, is_player: bool = False):
        self.stats = stats
        self.name = stats.name
        self.grid_x = float(x)
        self.grid_y = float(y)
        self.is_player = is_player
        self.is_lair = False
        self.lair_owner = None  # Reference to the entity that owns this lair action

        # Dynamic HP
        self.hp = stats.hit_points
        self.max_hp = stats.hit_points
        self.temp_hp = 0

        # Duration tracking & Notes
        self.active_effects = {}  # "Effect Name": rounds_remaining (int)
        self.notes = ""           # DM notes for this entity

        # Visuals
        self.color = COLORS["player"] if is_player else COLORS["enemy"]

        # Initiative
        self.initiative = 0

        # Conditions: set of strings
        self.conditions: set = set()
        self.condition_metadata: dict = {}  # "Condition": {"dc": 15, "save": "Wisdom"}

        # Resources
        self.spell_slots: dict = copy.deepcopy(stats.spell_slots)
        self.legendary_resistances_left: int = stats.legendary_resistance_count
        self.legendary_actions_left: int = stats.legendary_action_count
        self.items: list = copy.deepcopy(stats.items)
        self.exhaustion: int = 0

        # Feature uses (resets on long/short rest)
        self.feature_uses: dict = {}
        for feat in stats.features:
            if feat.uses_per_day > 0:
                self.feature_uses[feat.name] = feat.uses_per_day
            elif feat.recharge:
                # Recharge abilities usually start charged (1 use)
                self.feature_uses[feat.name] = 1

        # Turn economy
        self.action_used: bool = False
        self.bonus_action_used: bool = False
        self.reaction_used: bool = False
        self.movement_left: float = float(stats.speed)

        # Concentration
        self.concentrating_on: SpellInfo | None = None

        # Death saves (players only)
        self.death_save_successes: int = 0
        self.death_save_failures: int = 0
        self.is_stable: bool = False

    @property
    def size_in_squares(self) -> int:
        s = self.stats.size.lower()
        if "large" in s: return 2
        if "huge" in s: return 3
        if "gargantuan" in s: return 4
        return 1

    # ------------------------------------------------------------------ #
    # HP / Damage                                                          #
    # ------------------------------------------------------------------ #

    def take_damage(self, amount: int, damage_type: str = "") -> tuple[int, bool]:
        """
        Apply damage. Returns (damage_dealt, broke_concentration).
        Respects temp HP, resistances, immunities, vulnerabilities.
        """
        dtype_lower = damage_type.lower()
        if dtype_lower in [x.lower() for x in self.stats.damage_immunities]:
            return 0, False
        if dtype_lower in [x.lower() for x in self.stats.damage_resistances]:
            amount = amount // 2
        if dtype_lower in [x.lower() for x in self.stats.damage_vulnerabilities]:
            amount = amount * 2

        # Temp HP absorbs first
        if self.temp_hp > 0:
            absorbed = min(self.temp_hp, amount)
            self.temp_hp -= absorbed
            amount -= absorbed

        self.hp -= amount
        self.hp = max(self.hp, 0 if not self.is_player else -self.max_hp)

        # Concentration check on damage
        broke_conc = False
        if self.concentrating_on and amount > 0:
            dc = max(10, amount // 2)
            con_bonus = self.get_save_bonus("Constitution")
            roll = random.randint(1, 20) + con_bonus
            if roll < dc:
                self.drop_concentration()
                broke_conc = True

        return amount, broke_conc

    def heal(self, amount: int):
        self.hp = min(self.max_hp, self.hp + amount)

    def add_temp_hp(self, amount: int):
        """Temp HP doesn't stack; take the higher value."""
        self.temp_hp = max(self.temp_hp, amount)

    # ------------------------------------------------------------------ #
    # Concentration                                                        #
    # ------------------------------------------------------------------ #

    def start_concentration(self, spell: SpellInfo) -> SpellInfo | None:
        dropped = self.concentrating_on
        self.concentrating_on = spell
        return dropped

    def drop_concentration(self):
        dropped = self.concentrating_on
        self.concentrating_on = None
        return dropped

    # ------------------------------------------------------------------ #
    # Conditions                                                           #
    # ------------------------------------------------------------------ #

    def add_condition(self, condition: str, save_ability: str = None, save_dc: int = 0):
        immune = [x.lower() for x in self.stats.condition_immunities]
        if condition.lower() not in immune:
            self.conditions.add(condition)
            if save_ability and save_dc > 0:
                self.condition_metadata[condition] = {"save": save_ability, "dc": save_dc}
            if condition in INCAPACITATING_CONDITIONS and self.concentrating_on:
                self.drop_concentration()

    def remove_condition(self, condition: str):
        self.conditions.discard(condition)
        self.condition_metadata.pop(condition, None)

    def has_condition(self, condition: str) -> bool:
        return condition in self.conditions

    def is_incapacitated(self) -> bool:
        return bool(self.conditions & INCAPACITATING_CONDITIONS)

    def can_move(self) -> bool:
        return bool(not (self.conditions & SPEED_ZERO_CONDITIONS))

    # ------------------------------------------------------------------ #
    # Movement                                                             #
    # ------------------------------------------------------------------ #

    def get_speed(self) -> float:
        if self.conditions & SPEED_ZERO_CONDITIONS:
            return 0.0
        speed = float(self.stats.speed)
        if self.has_condition("Prone"):
            speed = speed / 2.0
        # Exhaustion 2+: half speed
        if self.exhaustion >= 2:
            speed = speed / 2.0
        return speed

    # ------------------------------------------------------------------ #
    # Modifiers                                                            #
    # ------------------------------------------------------------------ #

    def get_modifier(self, ability: str) -> int:
        return self.stats.abilities.get_mod(ability)

    def get_save_bonus(self, ability: str) -> int:
        return self.stats.saving_throws.get(ability, self.get_modifier(ability))

    def get_skill_bonus(self, skill: str) -> int:
        return self.stats.skills.get(skill, 0)

    # ------------------------------------------------------------------ #
    # Attack advantage/disadvantage                                        #
    # ------------------------------------------------------------------ #

    def has_attack_advantage(self, target: "Entity" = None, is_ranged: bool = False) -> bool:
        if self.has_condition("Invisible"):
            return True
        if target:
            if target.has_condition("Paralyzed") or target.has_condition("Unconscious"):
                return True
            if target.has_condition("Stunned") or target.has_condition("Restrained"):
                return True
            if target.has_condition("Blinded"):
                return True
            if target.has_condition("Prone") and not is_ranged:
                return True
        return False

    def has_attack_disadvantage(self, target: "Entity" = None, is_ranged: bool = False) -> bool:
        if self.has_condition("Blinded"):
            return True
        if self.has_condition("Poisoned"):
            return True
        if self.has_condition("Frightened"):
            return True
        if self.has_condition("Restrained"):
            return True
        if is_ranged and target:
            dist = math.hypot(self.grid_x - target.grid_x, self.grid_y - target.grid_y) * 5
            if dist <= 5:
                return True  # Ranged attack while in melee
        if target and target.has_condition("Invisible"):
            return True
        if self.has_condition("Prone") and is_ranged:
            return True
        # Exhaustion 3+
        if self.exhaustion >= 3:
            return True
        return False

    # ------------------------------------------------------------------ #
    # Spell slots                                                          #
    # ------------------------------------------------------------------ #

    _LEVEL_KEYS = {1:"1st",2:"2nd",3:"3rd",4:"4th",5:"5th",6:"6th",7:"7th",8:"8th",9:"9th"}

    def has_spell_slot(self, min_level: int = 1) -> bool:
        for lvl in range(min_level, 10):
            key = self._LEVEL_KEYS.get(lvl, f"{lvl}th")
            if self.spell_slots.get(key, 0) > 0:
                return True
        return False

    def get_highest_slot(self) -> int:
        """Returns the highest available spell slot level (0 if none)."""
        for lvl in range(9, 0, -1):
            key = self._LEVEL_KEYS.get(lvl, f"{lvl}th")
            if self.spell_slots.get(key, 0) > 0:
                return lvl
        return 0

    def use_spell_slot(self, level: int) -> bool:
        for lvl in range(level, 10):
            key = self._LEVEL_KEYS.get(lvl, f"{lvl}th")
            if self.spell_slots.get(key, 0) > 0:
                self.spell_slots[key] -= 1
                return True
        return False

    def get_slot_for_level(self, level: int) -> int:
        """Returns the lowest slot >= level that is available."""
        for lvl in range(level, 10):
            key = self._LEVEL_KEYS.get(lvl, f"{lvl}th")
            if self.spell_slots.get(key, 0) > 0:
                return lvl
        return 0

    # ------------------------------------------------------------------ #
    # Initiative                                                           #
    # ------------------------------------------------------------------ #

    def roll_initiative(self) -> int:
        dex_mod = self.get_modifier("dexterity")
        self.initiative = random.randint(1, 20) + dex_mod
        return self.initiative

    # ------------------------------------------------------------------ #
    # Turn management                                                      #
    # ------------------------------------------------------------------ #

    def reset_turn(self):
        self.action_used = False
        self.bonus_action_used = False
        self.reaction_used = False
        self.movement_left = self.get_speed()

    def reset_legendary_actions(self):
        self.legendary_actions_left = self.stats.legendary_action_count

    # ------------------------------------------------------------------ #
    # Rests                                                                #
    # ------------------------------------------------------------------ #

    def long_rest(self):
        self.hp = self.max_hp
        self.temp_hp = 0
        self.spell_slots = copy.deepcopy(self.stats.spell_slots)
        self.conditions.clear()
        self.condition_metadata.clear()
        self.concentrating_on = None
        self.death_save_successes = 0
        self.death_save_failures = 0
        self.is_stable = False
        self.exhaustion = max(0, self.exhaustion - 1)
        self.legendary_resistances_left = self.stats.legendary_resistance_count
        for feat in self.stats.features:
            if feat.uses_per_day > 0:
                self.feature_uses[feat.name] = feat.uses_per_day

    def short_rest(self):
        pass  # Classes handle their own short rest abilities

    def recharge_features(self) -> list[str]:
        """Rolls for recharge abilities (e.g. Dragon Breath). Returns logs."""
        logs = []
        for feat in self.stats.features:
            if not feat.recharge:
                continue
            
            # Check if used
            current = self.feature_uses.get(feat.name, 0)
            max_uses = feat.uses_per_day if feat.uses_per_day > 0 else 1
            
            if current < max_uses:
                # Parse recharge string "5-6" or "6"
                req_str = feat.recharge.replace("-", " ")
                req = [int(s) for s in req_str.split() if s.isdigit()]
                if not req: continue
                
                roll = random.randint(1, 6)
                success = False
                # "Recharge 5-6" means 5 or 6. "Recharge 6" means 6.
                if len(req) == 1:
                    if roll >= req[0]: success = True
                elif len(req) >= 2:
                    if req[0] <= roll <= req[1]: success = True
                
                if success:
                    self.feature_uses[feat.name] = max_uses
                    logs.append(f"{feat.name} recharged! (Rolled {roll})")
        return logs

    def roll_death_save(self) -> str:
        """Rolls a death saving throw. Returns status string."""
        if self.hp > 0 or self.is_stable or self.death_save_failures >= 3 or self.death_save_successes >= 3:
            return ""
        
        roll = random.randint(1, 20)
        msg = f"Death Save: {roll}"
        
        if roll == 1:
            self.death_save_failures += 2
            msg += " (CRITICAL FAIL! +2 failures)"
        elif roll == 20:
            self.hp = 1
            self.death_save_failures = 0
            self.death_save_successes = 0
            msg += " (CRITICAL SUCCESS! Regain 1 HP)"
        elif roll >= 10:
            self.death_save_successes += 1
            msg += " (Success)"
        else:
            self.death_save_failures += 1
            msg += " (Failure)"
            
        if self.death_save_successes >= 3:
            self.is_stable = True
            self.death_save_successes = 0
            self.death_save_failures = 0
            msg += " -> STABILIZED!"
        elif self.death_save_failures >= 3:
            msg += " -> DIED!"
            
        return msg
