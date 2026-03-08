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
        self.team = ""  # Team name for multi-team combat (e.g. "Blue", "Red", "Green", "Gold")

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
        self.condition_sources: dict = {}   # "Condition": Entity reference (source of Frightened/Charmed)

        # Grapple tracking (PHB p.195)
        self.grappling: list = []           # List of Entity references this entity is currently grappling
        self.grappled_by: "Entity | None" = None  # Entity that is grappling us (None if not grappled)

        # Resources
        self.spell_slots: dict = copy.deepcopy(stats.spell_slots)
        self.legendary_resistances_left: int = stats.legendary_resistance_count
        self.legendary_actions_left: int = stats.legendary_action_count
        self.items: list = copy.deepcopy(stats.items)
        self.exhaustion: int = 0
        # Hit Dice pool (PHB p.186): number of hit dice = character level
        import re as _re
        _hd_match = _re.search(r"(\d+)d(\d+)", stats.hit_dice)
        self.hit_dice_remaining: int = int(_hd_match.group(1)) if _hd_match else max(stats.character_level, 1)

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
        self.is_surprised: bool = False  # PHB p.189: Surprised creatures can't move/act in round 1

        # Concentration
        self.concentrating_on: SpellInfo | None = None
        self.concentration_rounds_left: int | None = None  # Auto-tracked by BattleSystem

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

        # Lucky feat uses (3/long rest)
        self.lucky_uses_left: int = 3 if any(f.mechanic == "lucky" for f in stats.features) else 0
        # Savage Attacker tracking
        self.savage_attacker_used: bool = False

        # Class resource tracking
        self.rage_active: bool = False
        self.rage_rounds: int = 0         # Rounds since rage started (max 10 = 1 min)
        self.rage_damage_taken: bool = False  # Did we take damage this round?
        self.attacked_this_turn: bool = False # Did we make an attack roll this turn?
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

        # Banishment tracking
        self.banished_from: tuple[float, float] | None = None

        # Elevation & Flying
        self.elevation: int = 0           # Current elevation in feet
        self.is_flying: bool = False      # Currently airborne
        self.is_climbing: bool = False    # Currently climbing (half speed)

        # Wild Shape / Polymorph tracking
        self.is_wild_shaped: bool = False
        self.wild_shape_name: str = ""
        self.original_form: dict | None = None

        # Initialize channel divinity uses from features
        for feat in stats.features:
            if feat.mechanic == "channel_divinity" and feat.uses_per_day > 0:
                self.channel_divinity_left = feat.uses_per_day

    @property
    def can_fly(self) -> bool:
        """Entity has a fly speed (innate or from spells)."""
        if self.stats.fly_speed > 0:
            return True
        if "Fly" in self.active_effects:
            return True
        return False

    @property
    def effective_fly_speed(self) -> int:
        """Fly speed in feet (0 if can't fly)."""
        if "Fly" in self.active_effects:
            return max(self.stats.fly_speed, 60)
        return self.stats.fly_speed

    def start_flying(self) -> bool:
        """Begin flying. Returns False if entity can't fly."""
        if not self.can_fly:
            return False
        self.is_flying = True
        self.is_climbing = False
        return True

    def land(self, ground_elevation: int = 0):
        """Land at ground level."""
        self.is_flying = False
        self.elevation = ground_elevation

    def start_climbing(self) -> bool:
        """Begin climbing (half speed movement)."""
        if self.stats.climb_speed > 0:
            self.is_climbing = True
            return True
        # No climb speed: Athletics check needed (handled elsewhere), use half speed
        self.is_climbing = True
        return True

    def stop_climbing(self):
        self.is_climbing = False

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
        # Defensive Duelist: reaction adds proficiency to AC (tracked as effect)
        if "Defensive Duelist" in self.active_effects:
            ac += self.stats.proficiency_bonus
        return ac

    def get_max_melee_reach(self) -> int:
        """Get the maximum melee reach of this entity in feet."""
        max_reach = 5
        for action in self.stats.actions:
            if action.reach:
                max_reach = max(max_reach, action.reach)
        return max_reach

    def transform_into(self, beast_stats: CreatureStats):
        """Transform into another creature (Wild Shape/Polymorph)."""
        # Save original state
        self.original_form = {
            "hp": self.hp,
            "max_hp": self.max_hp,
            "ac": self.stats.armor_class,
            "speed": self.stats.speed,
            "str": self.stats.abilities.strength,
            "dex": self.stats.abilities.dexterity,
            "con": self.stats.abilities.constitution,
            "actions": self.stats.actions,
            "features": self.stats.features,
            "size": self.stats.size,
            "skills": self.stats.skills,
            "saving_throws": self.stats.saving_throws,
            "spells_known": self.stats.spells_known,
            "cantrips": self.stats.cantrips,
        }
        
        # Apply beast stats
        self.hp = beast_stats.hit_points
        self.max_hp = beast_stats.hit_points
        self.temp_hp = 0 
        
        # Physical stats change
        self.stats.abilities.strength = beast_stats.abilities.strength
        self.stats.abilities.dexterity = beast_stats.abilities.dexterity
        self.stats.abilities.constitution = beast_stats.abilities.constitution
        self.stats.armor_class = beast_stats.armor_class
        self.stats.speed = beast_stats.speed
        self.stats.size = beast_stats.size
        
        # Actions & Features
        self.stats.actions = beast_stats.actions
        # Merge features (keep mental/class features, add beast traits like Pack Tactics)
        self.stats.features = self.original_form["features"] + beast_stats.features
        
        # Merge Skills & Saves (Use higher bonus)
        new_skills = self.stats.skills.copy()
        for sk, bonus in beast_stats.skills.items():
            if sk not in new_skills or bonus > new_skills[sk]:
                new_skills[sk] = bonus
        self.stats.skills = new_skills
        
        new_saves = self.stats.saving_throws.copy()
        for sv, bonus in beast_stats.saving_throws.items():
            if sv not in new_saves or bonus > new_saves[sv]:
                new_saves[sv] = bonus
        self.stats.saving_throws = new_saves

        # Disable spells unless Beast Spells feature
        if not self.has_feature("beast_spells"):
            self.stats.spells_known = []
            self.stats.cantrips = []

        self.is_wild_shaped = True
        self.wild_shape_name = beast_stats.name

    def revert_form(self):
        """Revert to original form."""
        if not self.original_form: return
        
        orig = self.original_form
        self.hp = orig["hp"]
        self.max_hp = orig["max_hp"]
        self.stats.armor_class = orig["ac"]
        self.stats.speed = orig["speed"]
        self.stats.abilities.strength = orig["str"]
        self.stats.abilities.dexterity = orig["dex"]
        self.stats.abilities.constitution = orig["con"]
        self.stats.actions = orig["actions"]
        self.stats.features = orig["features"]
        self.stats.size = orig["size"]
        self.stats.skills = orig["skills"]
        self.stats.saving_throws = orig["saving_throws"]
        self.stats.spells_known = orig["spells_known"]
        self.stats.cantrips = orig["cantrips"]
        
        self.original_form = None
        self.is_wild_shaped = False
        self.wild_shape_name = ""

    def record_attack(self):
        """Record that this entity made an attack roll this turn (hit or miss)."""
        self.attacked_this_turn = True

    # ------------------------------------------------------------------ #
    # HP / Damage                                                          #
    # ------------------------------------------------------------------ #

    def take_damage(self, amount: int, damage_type: str = "", is_magical: bool = False) -> tuple[int, bool]:
        """
        Apply damage. Returns (damage_dealt, broke_concentration).
        Respects temp HP, resistances, immunities, vulnerabilities, rage.
        """
        dtype_lower = damage_type.lower()
        if dtype_lower in [x.lower() for x in self.stats.damage_immunities]:
            return 0, False

        # Check resistances (Rage + Native)
        is_resistant = False
        if self.rage_active:
            if self.has_feature("totem_bear") and dtype_lower != "psychic":
                is_resistant = True
            elif dtype_lower in ("bludgeoning", "piercing", "slashing"):
                is_resistant = True
        
        if not is_resistant:
            for r in self.stats.damage_resistances:
                r_lower = r.lower()
                if dtype_lower in r_lower:
                    # Check for non-magical condition
                    if "non-magic" in r_lower or "non-silvered" in r_lower:
                        if not is_magical:
                            is_resistant = True
                    else:
                        is_resistant = True

        if is_resistant:
            amount = amount // 2

        # Heavy Armor Master: reduce nonmagical B/P/S by 3 while in heavy armor
        if self.has_feature("heavy_armor_master") and not is_magical:
            if dtype_lower in ("bludgeoning", "piercing", "slashing"):
                amount = max(0, amount - 3)

        if dtype_lower in [x.lower() for x in self.stats.damage_vulnerabilities]:
            amount = amount * 2

        # Reset stability if taking damage
        if amount > 0:
            self.is_stable = False

        # Temp HP absorbs first
        if self.temp_hp > 0:
            absorbed = min(self.temp_hp, amount)
            self.temp_hp -= absorbed
            amount -= absorbed

        # Wild Shape Damage Carry-over
        if self.is_wild_shaped and amount > 0:
            if self.hp - amount <= 0:
                excess = amount - self.hp
                self.hp = 0
                self.revert_form()
                # Apply excess damage to original form
                if excess > 0:
                    return self.take_damage(excess, damage_type, is_magical)

        self.hp -= amount

        # Relentless Endurance (Half-Orc): Drop to 1 HP instead of 0
        if self.hp <= 0 and self.hp > -self.max_hp:
            if self.has_feature("relentless_endurance") and self.can_use_feature("Relentless Endurance"):
                self.hp = 1
                self.use_feature("Relentless Endurance")

        self.hp = max(self.hp, 0 if not self.is_player else -self.max_hp)

        # Track rage damage taken
        if self.rage_active:
            self.rage_damage_taken = True

        # Concentration check on damage
        broke_conc = False
        if self.concentrating_on and amount > 0:
            dc = max(10, amount // 2)
            con_bonus = self.get_save_bonus("Constitution")
            roll = random.randint(1, 20) + con_bonus
            # War Caster: advantage on concentration saves
            if self.has_feature("war_caster"):
                roll2 = random.randint(1, 20) + con_bonus
                roll = max(roll, roll2)
            if roll < dc:
                self.drop_concentration()
                broke_conc = True

        # Unconscious at 0 HP for players
        if self.hp <= 0 and self.is_player and not self.has_condition("Unconscious"):
            if self.hp <= -self.max_hp:
                # PHB p.197: Massive Damage Instant Death
                # Remaining damage equals or exceeds max HP → instant death
                self.death_save_failures = 3
                self.add_condition("Unconscious")
                self.is_stable = False
                self.death_save_history = ["MASSIVE"]
                if self.concentrating_on:
                    self.drop_concentration()
                    broke_conc = True
                if self.rage_active:
                    self.end_rage()
                if hasattr(self, '_log_func') and self._log_func:
                    self._log_func(f"  [MASSIVE DAMAGE] {self.name} is killed instantly!")
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

        # Release grapples if defeated (NPC at 0 HP or player unconscious)
        if self.hp <= 0 and self.grappling:
            self._release_all_grapples()

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
        self.attacked_this_turn = False
        self.rages_left -= 1
        # Rage grants advantage on STR checks/saves (tracked via condition-like flag)
        return True

    def end_rage(self):
        """Deactivate rage."""
        self.rage_active = False
        self.rage_rounds = 0
        self.rage_damage_taken = False
        self.attacked_this_turn = False

    def check_rage_end(self) -> bool:
        """Check if rage should end at end of turn. Returns True if rage ended."""
        if not self.rage_active:
            return False
        self.rage_rounds += 1
        # Rage ends if: 10 rounds (1 minute), or didn't attack/take damage
        if self.rage_rounds >= 10:
            self.end_rage()
            return True
        if not self.attacked_this_turn and not self.rage_damage_taken:
            self.end_rage()
            return True
        # Reset per-round tracking
        self.rage_damage_taken = False
        self.attacked_this_turn = False
        return False

    # ------------------------------------------------------------------ #
    # Concentration                                                        #
    # ------------------------------------------------------------------ #

    def start_concentration(self, spell: SpellInfo) -> SpellInfo | None:
        dropped = self.concentrating_on
        self.concentrating_on = spell
        self.concentration_rounds_left = None  # Reset; BattleSystem will initialize
        # If dropping a mark spell, clear marked target
        if dropped and dropped.name in ("Hunter's Mark", "Hex"):
            self.marked_target = None
        return dropped

    def drop_concentration(self):
        dropped = self.concentrating_on
        self.concentrating_on = None
        self.concentration_rounds_left = None
        if dropped and dropped.name in ("Hunter's Mark", "Hex"):
            self.marked_target = None
        return dropped

    # ------------------------------------------------------------------ #
    # Conditions                                                           #
    # ------------------------------------------------------------------ #

    def add_condition(self, condition: str, save_ability: str = None, save_dc: int = 0,
                      source: "Entity | None" = None):
        from data.conditions import INCAPACITATING_CONDITIONS
        immune = [x.lower() for x in self.stats.condition_immunities]
        if condition.lower() not in immune:
            self.conditions.add(condition)
            if save_ability and save_dc > 0:
                self.condition_metadata[condition] = {"save": save_ability, "dc": save_dc}
            if source:
                self.condition_sources[condition] = source
            if condition in INCAPACITATING_CONDITIONS:
                if self.concentrating_on:
                    self.drop_concentration()
                # PHB: Incapacitated grappler releases grapple
                self._release_all_grapples()

    def remove_condition(self, condition: str):
        self.conditions.discard(condition)
        self.condition_metadata.pop(condition, None)
        self.condition_sources.pop(condition, None)
        # If Grappled is removed, clean up grapple references
        if condition == "Grappled" and self.grappled_by:
            grappler = self.grappled_by
            if self in grappler.grappling:
                grappler.grappling.remove(self)
            self.grappled_by = None

    def has_condition(self, condition: str) -> bool:
        return condition in self.conditions

    def get_condition_source(self, condition: str) -> "Entity | None":
        """Get the source entity for a source-dependent condition (Frightened, Charmed)."""
        return self.condition_sources.get(condition, None)

    def is_incapacitated(self) -> bool:
        from data.conditions import INCAPACITATING_CONDITIONS
        return bool(self.conditions & INCAPACITATING_CONDITIONS)

    def can_move(self) -> bool:
        from data.conditions import SPEED_ZERO_CONDITIONS
        return bool(not (self.conditions & SPEED_ZERO_CONDITIONS))

    # ------------------------------------------------------------------ #
    # Grapple Management (PHB p.195)                                       #
    # ------------------------------------------------------------------ #

    def start_grapple(self, target: "Entity"):
        """Apply grapple: this entity grapples target."""
        if target not in self.grappling:
            self.grappling.append(target)
        target.grappled_by = self
        target.add_condition("Grappled")

    def release_grapple(self, target: "Entity"):
        """Release a specific grappled creature."""
        if target in self.grappling:
            self.grappling.remove(target)
        if target.grappled_by == self:
            target.grappled_by = None
            target.remove_condition("Grappled")

    def _release_all_grapples(self):
        """Release all creatures this entity is grappling (e.g. when incapacitated)."""
        for target in list(self.grappling):
            if target.grappled_by == self:
                target.grappled_by = None
                target.remove_condition("Grappled")
        self.grappling.clear()

    def can_stand_from_prone(self) -> tuple[bool, str]:
        """
        PHB p.190-191: Standing costs half movement speed.
        Cannot stand if speed is 0 (Grappled, Restrained, etc.).
        """
        from engine.rules import can_stand_from_prone
        return can_stand_from_prone(self)

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
        # Exhaustion 5: speed 0
        if self.exhaustion >= 5:
            return 0.0
        # Grapple drag: half speed while dragging a creature
        # (unless grappled creature is 2+ sizes smaller)
        if self.grappling:
            from engine.rules import get_grapple_drag_speed_multiplier
            worst_mult = 1.0
            for grappled in self.grappling:
                mult = get_grapple_drag_speed_multiplier(self, grappled)
                worst_mult = min(worst_mult, mult)
            speed *= worst_mult
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
        # Resistance: +1d4 to one save (consumable)
        if "Resistance" in self.active_effects:
            base += random.randint(1, 4)
            self.active_effects.pop("Resistance")
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
        bonus = self.stats.skills.get(skill, 0)
        # Guidance: +1d4 to ability checks
        if "Guidance" in self.active_effects:
            bonus += random.randint(1, 4)
        return bonus

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
        # Invisible attacker has advantage (unless target has Alert)
        if self.has_condition("Invisible"):
            if target and target.has_feature("alert"):
                pass  # Alert: unseen attackers don't gain advantage
            else:
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
            if target.has_condition("Guiding Bolt"):
                return True
        return False

    def has_attack_disadvantage(self, target: "Entity" = None, is_ranged: bool = False,
                                is_threatened: bool = False, distance_ft: float = 0,
                                normal_range: int = 0, long_range: int = 0) -> bool:
        if self.has_condition("Blinded"):
            return True
        if self.has_condition("Poisoned"):
            return True
        if self.has_condition("Frightened"):
            return True
        if self.has_condition("Restrained"):
            return True
        if self.has_condition("Prone"):
            return True
        if is_ranged and target:
            if target.has_condition("Prone"):
                return True
            if is_threatened and not self.has_feature("crossbow_expert"):
                return True
            # PHB p.195: Long range disadvantage
            if normal_range > 0 and long_range > 0 and distance_ft > normal_range:
                return True
        if target and target.has_condition("Invisible"):
            return True
        if target and target.is_dodging and not target.is_incapacitated():
            return True
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

        # Alert feat: +5 to initiative
        if self.has_feature("alert"):
            self.initiative += 5

        # Guidance check (Ability Check)
        if "Guidance" in self.active_effects:
            bonus = random.randint(1, 4)
            self.initiative += bonus
            self.active_effects.pop("Guidance")

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
        self.savage_attacker_used = False
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
        # PHB p.186: Regain up to half total Hit Dice (min 1) on long rest
        import re as _re
        _hd_match = _re.search(r"(\d+)d(\d+)", self.stats.hit_dice)
        max_dice = int(_hd_match.group(1)) if _hd_match else max(self.stats.character_level, 1)
        regain = max(max_dice // 2, 1)
        self.hit_dice_remaining = min(self.hit_dice_remaining + regain, max_dice)
        self.spell_slots = copy.deepcopy(self.stats.spell_slots)
        self._release_all_grapples()
        if self.grappled_by:
            self.grappled_by.release_grapple(self)
        self.conditions.clear()
        self.condition_metadata.clear()
        self.condition_sources.clear()
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
        # Lucky feat
        if self.has_feature("lucky"):
            self.lucky_uses_left = 3
        # Channel divinity
        for feat in self.stats.features:
            if feat.mechanic == "channel_divinity" and feat.uses_per_day > 0:
                self.channel_divinity_left = feat.uses_per_day

    def short_rest(self, hit_dice_to_spend: int = 0) -> str:
        """Short rest: restore Ki, short-rest features, and optionally spend Hit Dice.
        Returns summary string."""
        msgs = []
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

        # PHB p.186: Spend Hit Dice to heal
        if hit_dice_to_spend > 0 and self.hp < self.max_hp:
            # Parse hit dice from stats (e.g. "10d8+30" → die size 8, max dice = 10)
            import re as _re
            hd_match = _re.search(r"(\d+)d(\d+)", self.stats.hit_dice)
            if hd_match:
                max_dice = int(hd_match.group(1))
                die_size = int(hd_match.group(2))
            else:
                # Fallback: level d8
                max_dice = max(self.stats.character_level, 1)
                die_size = 8
            # Track available hit dice
            if not hasattr(self, "hit_dice_remaining"):
                self.hit_dice_remaining = max_dice
            dice_to_use = min(hit_dice_to_spend, self.hit_dice_remaining)
            con_mod = self.stats.abilities.get_mod("constitution")
            total_healed = 0
            for _ in range(dice_to_use):
                roll = random.randint(1, die_size) + con_mod
                roll = max(roll, 1)  # minimum 1 HP
                total_healed += roll
                self.hit_dice_remaining -= 1
            old_hp = self.hp
            self.hp = min(self.hp + total_healed, self.max_hp)
            actual = self.hp - old_hp
            if actual > 0:
                msgs.append(f"{self.name} spends {dice_to_use} Hit Dice, heals {actual} HP.")
        return " ".join(msgs)

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
