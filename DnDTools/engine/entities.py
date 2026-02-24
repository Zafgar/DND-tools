import random
import copy
import math
from settings import COLORS
from data.models import CreatureStats, SpellInfo, Item


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
        self.acts_on_initiative: bool = True  # If False, skipped in turn order (e.g. Spiritual Weapon)

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
        
        # Combat States
        self.is_dodging: bool = False
        self.is_disengaging: bool = False

        # Concentration
        self.concentrating_on: SpellInfo | None = None

        # Death saves (players only)
        self.death_save_successes: int = 0
        self.death_save_failures: int = 0
        self.is_stable: bool = False
        self.death_save_history: list = []  # List of "S", "F", "S!", "F!" for display

        # Summon tracking
        self.is_summon: bool = False
        self.summon_owner: "Entity | None" = None
        self.summon_rounds_left: int = 0
        self.summon_spell_name: str = ""  # Which spell created this summon

        # Class resource tracking
        self.rage_active: bool = False
        self.rage_rounds: int = 0         # Rounds since rage started (max 10 = 1 min)
        self.rage_damage_taken: bool = False  # Did we take damage this round?
        self.rage_damage_dealt: bool = False  # Did we deal damage or attack this round?
        self.rages_left: int = stats.rage_count
        self.ki_points_left: int = stats.ki_points
        self.sorcery_points_left: int = stats.sorcery_points
        self.lay_on_hands_left: int = stats.lay_on_hands_pool
        self.bardic_inspiration_left: int = stats.bardic_inspiration_count
        self.channel_divinity_left: int = 0  # Set by class features

        # Hunter's Mark / Hex target tracking
        self.marked_target: "Entity | None" = None

        # Sneak Attack used this turn
        self.sneak_attack_used: bool = False

        # Initialize channel divinity uses from features
        for feat in stats.features:
            if feat.mechanic == "channel_divinity" and feat.uses_per_day > 0:
                self.channel_divinity_left = feat.uses_per_day

    @property
    def size_in_squares(self) -> int:
        s = self.stats.size.lower()
        if "large" in s: return 2
        if "huge" in s: return 3
        if "gargantuan" in s: return 4
        return 1

    @property
    def armor_class(self) -> int:
        """Calculate dynamic AC including active effects."""
        ac = self.stats.armor_class
        if "Haste" in self.active_effects:
            ac += 2
        if "Shield" in self.active_effects:
            ac += 5
        if "Shield of Faith" in self.active_effects:
            ac += 2
        return ac

    # ------------------------------------------------------------------ #
    # HP / Damage                                                          #
    # ------------------------------------------------------------------ #

    def take_damage(self, amount: int, damage_type: str = "") -> tuple[int, bool]:
        """
        Apply damage. Returns (damage_dealt, broke_concentration).
        Respects temp HP, resistances, immunities, vulnerabilities, rage.
        """
        dtype_lower = damage_type.lower()
        if dtype_lower in [x.lower() for x in self.stats.damage_immunities]:
            return 0, False

        # Rage resistance: half damage from bludgeoning, piercing, slashing
        if self.rage_active and dtype_lower in ("bludgeoning", "piercing", "slashing"):
            amount = amount // 2
        elif dtype_lower in [x.lower() for x in self.stats.damage_resistances]:
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

        # Track rage damage taken
        if self.rage_active and amount > 0:
            self.rage_damage_taken = True

        # Concentration check on damage
        broke_conc = False
        if self.concentrating_on and amount > 0:
            dc = max(10, amount // 2)
            con_bonus = self.get_save_bonus("Constitution")
            roll = random.randint(1, 20) + con_bonus
            if roll < dc:
                self.drop_concentration()
                broke_conc = True

        # Unconscious at 0 HP for players
        if self.hp <= 0 and self.is_player and not self.has_condition("Unconscious"):
            if self.hp <= -self.max_hp:
                pass  # Instant death, handled elsewhere
            else:
                self.add_condition("Unconscious")
                self.death_save_successes = 0
                self.death_save_failures = 0
                self.is_stable = False
                self.death_save_history = []
                # Drop concentration
                if self.concentrating_on:
                    self.drop_concentration()
                    broke_conc = True
                # End rage
                if self.rage_active:
                    self.end_rage()

        return amount, broke_conc

    def heal(self, amount: int):
        was_down = self.hp <= 0
        self.hp = min(self.max_hp, self.hp + amount)
        # Regaining HP removes Unconscious (from death saves)
        if was_down and self.hp > 0:
            self.remove_condition("Unconscious")
            self.death_save_successes = 0
            self.death_save_failures = 0
            self.is_stable = False
            self.death_save_history = []

    def add_temp_hp(self, amount: int):
        """Temp HP doesn't stack; take the higher value."""
        self.temp_hp = max(self.temp_hp, amount)

    # ------------------------------------------------------------------ #
    # Rage                                                                 #
    # ------------------------------------------------------------------ #

    def start_rage(self) -> bool:
        """Activate Barbarian rage. Returns True if successful."""
        if self.rage_active or self.rages_left <= 0:
            return False
        self.rage_active = True
        self.rage_rounds = 0
        self.rage_damage_taken = False
        self.rage_damage_dealt = False
        self.rages_left -= 1
        # Rage grants advantage on STR checks/saves (tracked via condition-like flag)
        return True

    def end_rage(self):
        """Deactivate rage."""
        self.rage_active = False
        self.rage_rounds = 0
        self.rage_damage_taken = False
        self.rage_damage_dealt = False

    def check_rage_end(self) -> bool:
        """Check if rage should end at end of turn. Returns True if rage ended."""
        if not self.rage_active:
            return False
        self.rage_rounds += 1
        # Rage ends if: 10 rounds (1 minute), or didn't attack/take damage
        if self.rage_rounds >= 10:
            self.end_rage()
            return True
        if not self.rage_damage_dealt and not self.rage_damage_taken:
            self.end_rage()
            return True
        # Reset per-round tracking
        self.rage_damage_taken = False
        self.rage_damage_dealt = False
        return False

    # ------------------------------------------------------------------ #
    # Concentration                                                        #
    # ------------------------------------------------------------------ #

    def start_concentration(self, spell: SpellInfo) -> SpellInfo | None:
        dropped = self.concentrating_on
        self.concentrating_on = spell
        # If dropping a mark spell, clear marked target
        if dropped and dropped.name in ("Hunter's Mark", "Hex"):
            self.marked_target = None
        return dropped

    def drop_concentration(self):
        dropped = self.concentrating_on
        self.concentrating_on = None
        if dropped and dropped.name in ("Hunter's Mark", "Hex"):
            self.marked_target = None
        return dropped

    # ------------------------------------------------------------------ #
    # Conditions                                                           #
    # ------------------------------------------------------------------ #

    def add_condition(self, condition: str, save_ability: str = None, save_dc: int = 0):
        from data.conditions import INCAPACITATING_CONDITIONS
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
        from data.conditions import INCAPACITATING_CONDITIONS
        return bool(self.conditions & INCAPACITATING_CONDITIONS)

    def can_move(self) -> bool:
        from data.conditions import SPEED_ZERO_CONDITIONS
        return bool(not (self.conditions & SPEED_ZERO_CONDITIONS))

    # ------------------------------------------------------------------ #
    # Movement                                                             #
    # ------------------------------------------------------------------ #

    def get_speed(self) -> float:
        from data.conditions import SPEED_ZERO_CONDITIONS
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
        if not ability: return 0
        return self.stats.abilities.get_mod(ability)

    def get_save_bonus(self, ability: str) -> int:
        base = self.stats.saving_throws.get(ability, self.get_modifier(ability))
        # Bless: +1d4 to saves
        if "Bless" in self.active_effects:
            base += random.randint(1, 4)
        if "Bane" in self.active_effects:
            base -= random.randint(1, 4)
        return base

    def get_attack_bonus_effects(self) -> int:
        """Get dynamic bonus to attack rolls from spells/effects."""
        bonus = 0
        if "Bless" in self.active_effects:
            bonus += random.randint(1, 4)
        if "Bane" in self.active_effects:
            bonus -= random.randint(1, 4)
        return bonus

    def get_skill_bonus(self, skill: str) -> int:
        return self.stats.skills.get(skill, 0)

    # ------------------------------------------------------------------ #
    # Class feature helpers                                                #
    # ------------------------------------------------------------------ #

    def has_feature(self, mechanic: str) -> bool:
        """Check if entity has a feature with the given mechanic key."""
        return any(f.mechanic == mechanic for f in self.stats.features)

    def get_feature(self, mechanic: str):
        """Get a feature by mechanic key."""
        for f in self.stats.features:
            if f.mechanic == mechanic:
                return f
        return None

    def get_feature_by_name(self, name: str):
        """Get a feature by name."""
        for f in self.stats.features:
            if f.name == name:
                return f
        return None

    def can_use_feature(self, name: str) -> bool:
        """Check if a limited-use feature has uses remaining."""
        feat = self.get_feature_by_name(name)
        if not feat:
            return False
        if feat.uses_per_day == -1 and not feat.recharge:
            return True  # Unlimited
        return self.feature_uses.get(name, 0) > 0

    def use_feature(self, name: str) -> bool:
        """Consume one use of a limited-use feature. Returns True if successful."""
        if name not in self.feature_uses:
            return False
        if self.feature_uses[name] <= 0:
            return False
        self.feature_uses[name] -= 1
        return True

    def get_rage_damage_bonus(self) -> int:
        """Get the extra damage from Barbarian rage based on level."""
        if not self.rage_active:
            return 0
        feat = self.get_feature("rage_damage")
        if feat and feat.mechanic_value:
            try:
                return int(feat.mechanic_value)
            except ValueError:
                pass
        level = self.stats.character_level
        if level >= 16:
            return 4
        if level >= 9:
            return 3
        return 2

    def get_sneak_attack_dice(self) -> str:
        """Get sneak attack dice string based on rogue level."""
        feat = self.get_feature("sneak_attack")
        if feat and feat.mechanic_value:
            return feat.mechanic_value
        return ""

    # ------------------------------------------------------------------ #
    # Attack advantage/disadvantage                                        #
    # ------------------------------------------------------------------ #

    def has_attack_advantage(self, target: "Entity" = None, is_ranged: bool = False, dist: float = 0) -> bool:
        if self.has_condition("Invisible"):
            return True
        # Reckless Attack (Barbarian) - melee STR attacks
        if self.rage_active and self.has_feature("reckless_attack") and not is_ranged:
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
            # Ranged attacks against Prone targets have Disadvantage
            if target.has_condition("Prone"):
                return True
            dist = math.hypot(self.grid_x - target.grid_x, self.grid_y - target.grid_y) * 5
            if dist <= 5:
                return True  # Ranged attack while in melee
        if target and target.has_condition("Invisible"):
            return True
        if target and target.is_dodging and not target.is_incapacitated():
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
        # Feral Instinct: advantage on initiative
        if self.has_feature("feral_instinct"):
            r1 = random.randint(1, 20) + dex_mod
            r2 = random.randint(1, 20) + dex_mod
            self.initiative = max(r1, r2)
        else:
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
        self.sneak_attack_used = False
        self.is_dodging = False
        self.is_disengaging = False

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
        self.death_save_history = []
        self.exhaustion = max(0, self.exhaustion - 1)
        self.legendary_resistances_left = self.stats.legendary_resistance_count
        for feat in self.stats.features:
            if feat.uses_per_day > 0:
                self.feature_uses[feat.name] = feat.uses_per_day
        # Restore class resources
        self.rages_left = self.stats.rage_count
        self.ki_points_left = self.stats.ki_points
        self.sorcery_points_left = self.stats.sorcery_points
        self.lay_on_hands_left = self.stats.lay_on_hands_pool
        self.bardic_inspiration_left = self.stats.bardic_inspiration_count
        self.rage_active = False
        self.marked_target = None
        self.sneak_attack_used = False
        # Channel divinity
        for feat in self.stats.features:
            if feat.mechanic == "channel_divinity" and feat.uses_per_day > 0:
                self.channel_divinity_left = feat.uses_per_day

    def short_rest(self):
        # Short rest restores: Ki, Channel Divinity, some features
        self.ki_points_left = self.stats.ki_points
        # Restore short-rest features
        for feat in self.stats.features:
            if feat.short_rest_recharge and feat.uses_per_day > 0:
                self.feature_uses[feat.name] = feat.uses_per_day
        # Fighter: Action Surge, Second Wind
        for feat in self.stats.features:
            if feat.mechanic in ("action_surge", "second_wind") and feat.uses_per_day > 0:
                self.feature_uses[feat.name] = feat.uses_per_day

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
        msg = f"Death Save: d20={roll}"

        if roll == 1:
            self.death_save_failures += 2
            self.death_save_history.append("F!")
            self.death_save_history.append("F!")
            msg += " (CRITICAL FAIL! +2 failures)"
        elif roll == 20:
            self.hp = 1
            self.death_save_failures = 0
            self.death_save_successes = 0
            self.death_save_history.append("S!")
            self.remove_condition("Unconscious")
            msg += " (CRITICAL SUCCESS! Regain 1 HP, conscious!)"
        elif roll >= 10:
            self.death_save_successes += 1
            self.death_save_history.append("S")
            msg += f" (Success) [{self.death_save_successes}/3 S, {self.death_save_failures}/3 F]"
        else:
            self.death_save_failures += 1
            self.death_save_history.append("F")
            msg += f" (Failure) [{self.death_save_successes}/3 S, {self.death_save_failures}/3 F]"

        if self.death_save_successes >= 3:
            self.is_stable = True
            msg += " -> STABILIZED!"
        elif self.death_save_failures >= 3:
            msg += " -> DIED!"

        return msg
