"""
BattleSystem – manages combat state, turn order, grid positions, terrain.
The TacticalAI (engine/ai.py) computes what NPCs should do.
Includes BattleStatisticsTracker, DMAdvisor, and WinProbabilityCalculator.
"""
import json
import math
import os
import copy
import random
from typing import List, Optional, Callable
from engine.entities import Entity
from engine.ai import TacticalAI, TurnPlan, ActionStep
from engine.terrain import TerrainObject, get_elevation_at, check_los_blocked, calculate_fall_damage
from engine.dice import roll_dice
from engine.battle_stats import BattleStatisticsTracker
from engine.dm_advisor import DMAdvisor
from engine.win_probability import WinProbabilityCalculator
from data.models import CreatureStats


class BattleSystem:
    def __init__(self, log_callback: Callable[[str], None], initial_entities: List[Entity] = None):
        self.grid_size = 60             # pixels per square
        self.entities: List[Entity] = initial_entities or []
        self.turn_index = 0
        self.current_plane = "Material Plane"
        self.log = log_callback
        self.round = 1
        self.combat_started = False
        self.ai = TacticalAI()
        self.terrain: List[TerrainObject] = []
        self.weather = "Clear"  # Clear, Rain, Fog, Ash

        # Pending OA reactions: list of (reactor, mover)
        self.pending_reactions: List[tuple] = []

        # Legendary action queue: entities that may still act this round
        self.legendary_queue: List[Entity] = []

        # Lair activation: set True from encounter setup if combat takes place in a lair
        # Lair actions only happen when this is True (PHB/MM: lair actions are NOT available
        # outside the creature's lair)
        self.lair_enabled: bool = False

        # Battle analytics
        self.stats_tracker = BattleStatisticsTracker()
        self.dm_advisor = DMAdvisor()
        self.win_calculator = WinProbabilityCalculator()

        # Track last damage source for kill attribution
        self._last_damage_source: str = ""

        if not self.entities:
            self._init_demo_entities()

    # ------------------------------------------------------------------ #
    # Setup                                                                #
    # ------------------------------------------------------------------ #

    def start_combat(self, surprise_side: str = ""):
        """Start combat. surprise_side: 'players' if players surprise enemies,
        'enemies' if enemies surprise players, '' for no surprise."""
        self.combat_started = True

        # Register entities with stats tracker
        for entity in self.entities:
            if not entity.is_lair:
                self.stats_tracker.register_entity(entity)

        # Check for Lair Actions (only if lair is enabled from encounter setup)
        # PHB/MM: Lair actions only occur when fighting in the creature's lair
        lair_owners = []
        if self.lair_enabled:
            lair_owners = [e for e in self.entities if any(a.action_type == "lair" for a in e.stats.actions)]
        for owner in lair_owners:
            from data.models import CreatureStats
            lair_stats = CreatureStats(name="Lair Action", hit_points=1, speed=0, challenge_rating=0)
            lair_ent = Entity(lair_stats, -100, -100)
            lair_ent.initiative = 20
            lair_ent.is_lair = True
            lair_ent.lair_owner = owner
            self.entities.append(lair_ent)

        for entity in self.entities:
            if not entity.is_lair:
                entity.roll_initiative()
        self.entities.sort(key=lambda e: e.initiative, reverse=True)

        # PHB p.189: Surprise — surprised creatures can't move or act in round 1
        if surprise_side:
            for entity in self.entities:
                if entity.is_lair:
                    continue
                # Alert feat: can't be surprised
                if entity.has_feature("alert"):
                    continue
                if surprise_side == "players" and not entity.is_player:
                    entity.is_surprised = True
                    self.log(f"  [SURPRISE] {entity.name} is surprised!")
                elif surprise_side == "enemies" and entity.is_player:
                    entity.is_surprised = True
                    self.log(f"  [SURPRISE] {entity.name} is surprised!")

        self.log("=== COMBAT STARTED ===")
        self.log("Initiative order: " + " > ".join(e.name for e in self.entities))
        curr = self.get_current_entity()
        curr.reset_turn()
        self.log(f"--- Round {self.round}: {curr.name}'s turn ---")
        self._build_legendary_queue()

        # Initial win probability
        self.win_calculator.calculate(self)

    def _init_demo_entities(self):
        from data.models import AbilityScores, Action
        from data.library import library
        paladin = CreatureStats(
            name="Hero Paladin", hit_points=80, armor_class=18, speed=30,
            abilities=AbilityScores(strength=18, constitution=16, charisma=14),
            actions=[Action("Longsword", attack_bonus=7, damage_dice="1d8",
                            damage_bonus=4, damage_type="slashing")]
        )
        self.entities.append(Entity(paladin, 5, 5, is_player=True))
        bugbear = library.get_monster("Bugbear")
        self.entities.append(Entity(bugbear, 10, 5, is_player=False))

    # ------------------------------------------------------------------ #
    # Turn Management                                                      #
    # ------------------------------------------------------------------ #

    def get_current_entity(self) -> Entity:
        if not self.entities:
            raise ValueError("No entities in battle!")
        if self.turn_index >= len(self.entities):
            self.turn_index = 0
        return self.entities[self.turn_index]

    def spawn_summon(self, owner: Entity, name: str, x: float, y: float,
                     hp: int = 0, ac: int = 10, atk_bonus: int = 0,
                     damage_dice: str = "", damage_type: str = "force",
                     duration: int = 10, spell_name: str = "") -> Entity:
        """Spawn a summoned token (e.g. Spiritual Weapon) on the battlefield."""
        from data.models import CreatureStats, Action, AbilityScores

        spell_mod = owner.get_modifier(owner.stats.spellcasting_ability) if owner.stats.spellcasting_ability else 0
        actual_atk = atk_bonus or owner.stats.spell_attack_bonus or (
            owner.stats.proficiency_bonus + spell_mod)
        actual_dmg_bonus = spell_mod

        summon_stats = CreatureStats(
            name=f"{name} ({owner.name})",
            hit_points=max(hp, 1),
            armor_class=ac,
            speed=20,
            actions=[
                Action(name, description=f"Summon attack",
                       attack_bonus=actual_atk, damage_dice=damage_dice or "1d8",
                       damage_bonus=actual_dmg_bonus, damage_type=damage_type,
                       range=5)
            ],
        )
        ent = Entity(summon_stats, x, y, is_player=owner.is_player)
        ent.is_summon = True
        ent.summon_owner = owner
        ent.summon_rounds_left = duration
        ent.summon_spell_name = spell_name
        ent.hp = max(hp, 1)
        ent.max_hp = max(hp, 1)
        # Summon acts right after the owner in initiative
        ent.initiative = owner.initiative - 0.5
        if "Spiritual Weapon" in name:
            ent.acts_on_initiative = False

        self.entities.append(ent)
        # Re-sort to maintain initiative order
        current = self.get_current_entity()
        self.entities.sort(key=lambda e: e.initiative, reverse=True)
        self.turn_index = self.entities.index(current)

        self.log(f"[SUMMON] {name} appears at ({int(x)},{int(y)})!")
        return ent

    def remove_expired_summons(self) -> bool:
        """Remove summons that have expired. Returns True if current entity was removed."""
        current = self.get_current_entity() if self.entities else None
        expired = [e for e in self.entities if e.is_summon and e.summon_rounds_left <= 0]
        current_removed = False
        for e in expired:
            self.log(f"[SUMMON] {e.name} disappears.")
            if e == current:
                current_removed = True

        self.entities = [e for e in self.entities if e not in expired]
        
        if current and current in self.entities:
            self.turn_index = self.entities.index(current)
        elif self.entities:
            self.turn_index = min(self.turn_index, len(self.entities) - 1)
            
        return current_removed

    def next_turn(self, skip_saves: bool = False) -> Optional[Entity]:
        if not self.entities:
            return None

        # Safety check for turn_index
        if self.turn_index >= len(self.entities):
            self.turn_index = 0

        # --- END OF TURN LOGIC (Previous Entity) ---
        prev_ent = self.entities[self.turn_index]
        if prev_ent.hp > 0 and not skip_saves:
            self.handle_end_of_turn_saves(prev_ent)

        # Check Banishment status (returns, permanent banishment, etc.)
        self._update_banishment_status()

        # Validate grapples (break if out of range)
        self.validate_grapples()

        # Check Barbarian Rage end-of-turn
        if prev_ent.rage_active:
            if prev_ent.check_rage_end():
                self.log(f"[RAGE] {prev_ent.name}'s rage ends! (No attack/damage this turn)")

        # Clean up expired summons
        current_removed = self.remove_expired_summons()

        # Check if entities still exist
        if not self.entities:
            return None

        # If current entity was removed, the next entity shifted into its index.
        # So we decrement index so that the increment below lands on the correct next entity.
        if current_removed:
            self.turn_index -= 1

        # Advance turn — use a flag to ensure round increments exactly once per wrap
        self.turn_index += 1
        new_round = False
        if self.turn_index >= len(self.entities):
            self.turn_index = 0
            new_round = True

        # Find next valid entity (Alive OR Dying Player OR Lair)
        start_index = self.turn_index
        while True:
            ent = self.entities[self.turn_index]
            is_alive = ent.hp > 0
            # Players roll death saves, so they get a turn even if 0 HP (unless dead-dead or stable)
            is_dying_player = ent.is_player and ent.hp <= 0 and ent.death_save_failures < 3 and not ent.is_stable

            should_act = ent.acts_on_initiative
            if (is_alive or is_dying_player or ent.is_lair) and should_act:
                break

            self.turn_index = (self.turn_index + 1) % len(self.entities)
            if self.turn_index == 0:
                new_round = True

            if self.turn_index == start_index:
                break # Everyone dead/skipped

        if new_round:
            self.round += 1
            self.log(f"=== ROUND {self.round} ===")

        current = self.get_current_entity()

        # PHB p.189: Surprised creatures skip their first turn,
        # then surprise ends (they can use reactions afterwards)
        if current.is_surprised:
            current.is_surprised = False
            self.log(f"  [SURPRISE] {current.name} is surprised and loses this turn.")
            # Still reset turn economy so reaction becomes available after this point
            current.reset_turn()
            current.action_used = True
            current.bonus_action_used = True
            current.movement_left = 0
            return current

        # 5e Rule: Legendary Actions reset at start of creature's turn
        current.reset_legendary_actions()
        current.reset_turn()

        # Handle Effects Duration (decrement at start of turn)
        expired = []
        for eff, duration in list(current.active_effects.items()):
            current.active_effects[eff] -= 1
            if current.active_effects[eff] <= 0:
                expired.append(eff)
        for eff in expired:
            del current.active_effects[eff]
            self.log(f"  [EFFECT] '{eff}' expired.")
            # Auto-remove condition if it matches effect name (e.g. Guiding Bolt)
            if current.has_condition(eff):
                current.remove_condition(eff)

        # Regeneration at start of turn (Vampire, Troll, Phoenix, etc.)
        if current.hp > 0:
            self._handle_regeneration(current)

        # Champion Fighter: Survivor feature (regen if below half HP)
        if current.hp > 0 and current.has_feature("survivor"):
            if current.hp <= current.max_hp // 2:
                regen_amount = 5 + current.get_modifier("Constitution")
                old_hp = current.hp
                current.heal(regen_amount)
                actual = current.hp - old_hp
                if actual > 0:
                    self.log(f"  [SURVIVOR] {current.name} regenerates {actual} HP (below half)")

        # Concentration duration tracking: decrement rounds remaining
        if current.concentrating_on:
            self._tick_concentration_duration(current)

        # Check phase triggers (behavior change at HP thresholds)
        if current.hp > 0:
            self._check_phase_triggers(current)

        # Check hazard terrain at start of turn
        if current.hp > 0:
            self._check_hazard_damage(current)

        # Decrement Summon Duration
        if current.is_summon:
            current.summon_rounds_left -= 1
            if current.summon_rounds_left <= 0:
                self.log(f"  [SUMMON] {current.name} duration expired.")

        # Recharge Rolls (only if alive)
        if current.hp > 0:
            recharges = current.recharge_features()
            for r in recharges:
                self.log(f"  [RECHARGE] {r}")

        # Death Saves
        if current.hp <= 0 and not current.is_stable and not current.is_lair:
            res = current.roll_death_save()
            if res:
                self.log(f"  [DEATH] {res}")

        # Add to legendary queue if this creature has legendary actions
        self._build_legendary_queue()

        self.log(f"--- {current.name}'s turn (Round {self.round}, Initiative {current.initiative}) ---")
        if current.conditions:
            for cond in current.conditions:
                self.log(f"  [STATUS] {cond}")
        if current.concentrating_on:
            self.log(f"  [CONCENTRATION] {current.concentrating_on.name}")
        return current

    def _update_banishment_status(self):
        """Check all banished entities for return conditions."""
        # Iterate a copy since we might remove entities
        for ent in list(self.entities):
            if "Banished" not in ent.conditions:
                continue

            caster = ent.condition_sources.get("Banished")
            should_return = False
            permanent_banish = False

            # 1. Check Concentration: If caster lost it, target returns immediately
            if not caster or not caster.concentrating_on or caster.concentrating_on.name != "Banishment":
                should_return = True
                self.log(f"[BANISHMENT] Concentration broken/ended. {ent.name} returns.")
            
            # 2. Check Duration: If time runs out (active_effects <= 0)
            elif ent.active_effects.get("Banishment", 0) <= 0:
                # Duration expired naturally (1 minute passed)
                # Check planes
                native = ent.stats.native_plane
                current = self.current_plane
                
                if native and current and native.lower() != current.lower():
                    permanent_banish = True
                else:
                    should_return = True
                    self.log(f"[BANISHMENT] Duration expired. {ent.name} returns.")

            if permanent_banish:
                self.log(f"[BANISHMENT] {ent.name} is permanently banished to {ent.stats.native_plane}!")
                ent.remove_condition("Banished")
                self.entities.remove(ent)
                # Adjust turn index if needed
                if self.turn_index >= len(self.entities):
                    self.turn_index = 0

            elif should_return:
                ent.remove_condition("Banished")
                # Find return spot
                rx, ry = ent.banished_from if ent.banished_from else (ent.grid_x, ent.grid_y)
                if self.is_occupied(rx, ry, exclude=ent):
                    # Find nearest free space
                    # Spiral search
                    found = False
                    for r in range(1, 6): # Search up to 30ft away
                        for dx in range(-r, r+1):
                            for dy in range(-r, r+1):
                                nx, ny = rx + dx, ry + dy
                                if self.is_passable(nx, ny, exclude=ent):
                                    rx, ry = nx, ny
                                    found = True
                                    break
                            if found: break
                        if found: break
                
                ent.grid_x, ent.grid_y = rx, ry
                self.log(f"[BANISHMENT] {ent.name} reappears at ({int(rx)}, {int(ry)}).")

    def validate_grapples(self):
        """Check all active grapples and break them if invalid (out of reach)."""
        for grappler in self.entities:
            # Check targets this entity is grappling
            for target in list(grappler.grappling):
                # 1. Check if grappler incapacitated
                if grappler.is_incapacitated():
                    grappler.release_grapple(target)
                    self.log(f"[GRAPPLE] {grappler.name} incapacitated; releases {target.name}.")
                    continue
                
                # 2. Check range
                dist = self.get_distance(grappler, target)
                # Reach is usually 5ft (1 square). Large creatures might have more?
                # Standard grapple reach is 5ft unless specified.
                # We'll use max_melee_reach of grappler.
                reach = grappler.get_max_melee_reach() / 5.0
                
                if dist > reach + 0.1:
                    grappler.release_grapple(target)
                    self.log(f"[GRAPPLE] {target.name} broke free from {grappler.name} (out of reach).")

    def get_total_save_bonus(self, entity: Entity, ability: str) -> int:
        """Get save bonus including auras (e.g. Paladin)."""
        bonus = entity.get_save_bonus(ability)
        # Paladin Aura of Protection check
        for ally in self.get_allies_of(entity):
            if ally.hp > 0 and not ally.is_incapacitated():
                aura = ally.get_feature("aura_of_protection")
                if aura and self.get_distance(entity, ally) * 5 <= (aura.aura_radius or 10):
                    bonus += max(1, ally.get_modifier("Charisma"))
                    break # Bonuses don't stack
        return bonus

    def handle_end_of_turn_saves(self, entity: Entity):
        """Check if entity can shake off any conditions at end of turn."""
        from engine.rules import make_saving_throw

        # Check if Frightened source is dead -> remove Frightened
        if entity.has_condition("Frightened"):
            fear_source = entity.get_condition_source("Frightened")
            if fear_source and fear_source.hp <= 0:
                entity.remove_condition("Frightened")
                self.log(f"[STATUS] {entity.name} is no longer Frightened (source defeated)")

        # Check if grappler is incapacitated or dead -> remove Grappled
        if entity.has_condition("Grappled") and entity.grappled_by:
            grappler = entity.grappled_by
            if grappler.hp <= 0 or grappler.is_incapacitated():
                grappler.release_grapple(entity)
                self.log(f"[STATUS] {entity.name} escapes grapple ({grappler.name} incapacitated)")

        # Iterate a copy since we might modify the dict
        for cond, meta in list(entity.condition_metadata.items()):
            if cond not in entity.conditions:
                continue  # Already removed above
            ability = meta.get("save")
            dc = meta.get("dc")
            if ability and dc:
                success, total, msg = make_saving_throw(entity, ability, dc, self,
                                                        applies_condition=cond)
                if success:
                    entity.remove_condition(cond)
                    self.log(f"[SAVE] {msg} -> no longer {cond}!")
                else:
                    self.log(f"[SAVE] {msg} -> remains {cond}.")

    def _check_hazard_damage(self, entity: Entity):
        """Apply hazard terrain damage at the start of an entity's turn.
        Flying creatures above ground-level hazards are safe."""
        if entity.is_flying:
            return  # Flying above hazards
        t = self.get_terrain_at(int(entity.grid_x), int(entity.grid_y))
        if t and t.is_hazard:
            dmg = roll_dice(t.hazard_damage)
            dealt, _ = entity.take_damage(dmg, t.hazard_damage_type)
            self.log(f"  [HAZARD] {entity.name} takes {dealt} {t.hazard_damage_type} from {t.label}!")

    def _handle_regeneration(self, entity: Entity):
        """Handle start-of-turn regeneration for creatures with the Regeneration feature.
        Vampire: 20 HP, Troll: 10 HP, Phoenix: 10 HP, etc.
        Uses the 'regeneration' mechanic key and mechanic_value for HP amount."""
        regen_feat = entity.get_feature("regeneration")
        if not regen_feat:
            return
        try:
            regen_amount = int(regen_feat.mechanic_value) if regen_feat.mechanic_value else 10
        except ValueError:
            regen_amount = 10
        if entity.hp >= entity.max_hp:
            return
        old_hp = entity.hp
        entity.heal(regen_amount)
        actual = entity.hp - old_hp
        if actual > 0:
            self.log(f"  [REGEN] {entity.name} regenerates {actual} HP")

    def _check_phase_triggers(self, entity: Entity):
        """Check if any phase mechanics should trigger based on HP thresholds."""
        if entity.max_hp <= 0:
            return
        hp_pct = entity.hp / entity.max_hp
        for feat in entity.stats.features:
            if feat.phase_trigger_hp_pct > 0 and feat.name not in entity.active_phases:
                if hp_pct <= feat.phase_trigger_hp_pct:
                    entity.active_phases.add(feat.name)
                    self.log(f"  [PHASE] {entity.name}: {feat.name} triggered! {feat.phase_description}")

    # Duration constants: spell duration -> rounds (1 round = 6 sec)
    _DURATION_ROUNDS = {
        "1 round": 1, "1 minute": 10, "10 minutes": 100,
        "1 hour": 600, "8 hours": 4800, "24 hours": 14400,
    }

    def _tick_concentration_duration(self, entity: Entity):
        """Track concentration spell duration. Auto-drop when expired.
        Uses the entity's concentration_rounds_left counter."""
        spell = entity.concentrating_on
        if not spell or not spell.duration:
            return
        # Initialize counter if not set
        if not hasattr(entity, 'concentration_rounds_left') or entity.concentration_rounds_left is None:
            rounds = self._DURATION_ROUNDS.get(spell.duration, 0)
            if rounds <= 0:
                return  # Unknown or permanent duration - don't auto-expire
            entity.concentration_rounds_left = rounds
        # Decrement
        entity.concentration_rounds_left -= 1
        remaining = entity.concentration_rounds_left
        # Log warning at key thresholds
        if remaining == 1:
            self.log(f"  [CONCENTRATION] {spell.name} expires next round!")
        elif remaining <= 0:
            self.log(f"  [CONCENTRATION] {spell.name} duration expired!")
            self.remove_spell_terrain(entity.name, spell.name)
            entity.drop_concentration()
            entity.concentration_rounds_left = None

    def _build_legendary_queue(self):
        """After each turn, legendary creatures can use their legendary actions."""
        self.legendary_queue = [
            e for e in self.entities
            if e.legendary_actions_left > 0 and e.hp > 0 and e != self.get_current_entity()
        ]

    def get_pending_legendary_action(self) -> tuple[Optional[Entity], Optional[ActionStep]]:
        """Pop the next legendary action from the queue, if any."""
        while self.legendary_queue:
            leg_entity = self.legendary_queue[0]
            # Verify still valid
            if leg_entity.legendary_actions_left <= 0 or leg_entity.hp <= 0:
                self.legendary_queue.pop(0)
                continue
            
            step = self.ai.calculate_legendary_action(leg_entity, self)
            if step:
                # Don't pop yet; wait for UI to confirm/execute
                return leg_entity, step
            else:
                # No valid action found for this entity
                self.legendary_queue.pop(0)
        return None, None

    def commit_legendary_action(self, entity: Entity):
        """Call this after the UI has executed the legendary action."""
        if self.legendary_queue and self.legendary_queue[0] == entity:
            self.legendary_queue.pop(0)

    # ------------------------------------------------------------------ #
    # AI                                                                   #
    # ------------------------------------------------------------------ #

    def compute_ai_turn(self, entity: Entity) -> TurnPlan:
        """Calculate full turn plan for an NPC. Does NOT apply changes yet."""
        return self.ai.calculate_turn(entity, self)

    def check_opportunity_attacks(self, mover: Entity, old_x: float, old_y: float):
        """Check if any hostile can make an OA against mover."""
        if mover.is_disengaging:
            return []
            
        # Forced movement (e.g. Grappled/dragged, Shoved) does not provoke OAs
        # If speed is 0 (Grappled), they can't move voluntarily, so it must be forced.
        if mover.has_condition("Grappled") or mover.has_condition("Restrained") or mover.has_condition("Stunned"):
            return []
            
        oas = []
        for e in self.entities:
            if e == mover or e.hp <= 0 or e.reaction_used:
                continue
            if e.is_player == mover.is_player:
                continue  # same team
            
            # Calculate reach in squares (1 square = 5 ft)
            reach_squares = e.get_max_melee_reach() / 5.0
            
            # Calculate distance BEFORE move (using old coordinates)
            dist_old = self._calculate_distance_coords(
                e.grid_x, e.grid_y, e.size_in_squares,
                old_x, old_y, mover.size_in_squares
            )
            
            # Calculate distance AFTER move (current coordinates)
            dist_new = self.get_distance(e, mover)
            
            # Trigger OA if target was within reach AND is now outside reach
            # Add small tolerance for floating point comparisons
            if dist_old <= reach_squares + 0.01 and dist_new > reach_squares + 0.01:
                oas.append(e)
        return oas

    def check_counterspell_reaction(self, caster: Entity, spell_level: int) -> List[Entity]:
        """Check if any enemy can counterspell."""
        potential = []
        for enemy in self.get_enemies_of(caster):
            if enemy.reaction_used or enemy.is_incapacitated():
                continue
            
            # Check if has Counterspell known
            has_cs = False
            for s in enemy.stats.spells_known:
                if s.name == "Counterspell":
                    has_cs = True
                    break
            if not has_cs:
                continue

            # Check range (60ft) and slots (needs lvl 3+)
            if self.get_distance(caster, enemy) * 5 <= 60 and enemy.has_spell_slot(3):
                potential.append(enemy)
        return potential

    def check_turn_start_auras(self, entity: Entity) -> List[dict]:
        """Check if entity is in aura of others at start of turn."""
        triggers = []
        for other in self.entities:
            if other == entity or other.hp <= 0:
                continue
            # Check features
            for feat in other.stats.features:
                if feat.aura_radius > 0:
                    # Filter out passive auras (like Paladin Aura of Protection)
                    # Only trigger if it requires a save, deals damage, or applies a condition
                    if not (feat.save_ability or feat.damage_dice or feat.applies_condition):
                        continue

                    # Team safety check: Harmful auras don't affect allies
                    if other.is_player == entity.is_player:
                        continue

                    dist_ft = self.get_distance(entity, other) * 5
                    if dist_ft <= feat.aura_radius:
                        triggers.append({
                            "source": other,
                            "target": entity,
                            "feature": feat
                        })
        return triggers

    # ------------------------------------------------------------------ #
    # Grid / Geometry                                                      #
    # ------------------------------------------------------------------ #

    def _calculate_distance_coords(self, x1, y1, s1, x2, y2, s2) -> float:
        """Calculate distance between two entities given their coordinates and sizes."""
        # Distance in X (0 if ranges overlap)
        dx = max(0, x2 - (x1 + s1), x1 - (x2 + s2))
        # Distance in Y (0 if ranges overlap)
        dy = max(0, y2 - (y1 + s1), y1 - (y2 + s2))
        return math.hypot(dx, dy)

    def get_distance(self, e1: Entity, e2: Entity) -> float:
        """Calculate distance between entities in grid squares, accounting for elevation.
        Elevation difference adds to 3D distance (1 square = 5ft)."""
        s1 = e1.size_in_squares
        s2 = e2.size_in_squares

        # Distance in X (0 if ranges overlap)
        dx = max(0, e2.grid_x - (e1.grid_x + s1), e1.grid_x - (e2.grid_x + s2))

        # Distance in Y (0 if ranges overlap)
        dy = max(0, e2.grid_y - (e1.grid_y + s1), e1.grid_y - (e2.grid_y + s2))

        # Elevation difference in squares (5ft per square)
        dz = abs(e1.elevation - e2.elevation) / 5.0

        return math.sqrt(dx*dx + dy*dy + dz*dz)

    def is_adjacent(self, e1: Entity, e2: Entity) -> bool:
        return self.get_distance(e1, e2) < 0.5

    def is_occupied(self, x: float, y: float, exclude: Entity = None) -> bool:
        for e in self.entities:
            if e == exclude or e.hp <= 0:
                continue
            # Check if point (x,y) is inside e's footprint
            s = e.size_in_squares
            if e.grid_x <= x < e.grid_x + s and e.grid_y <= y < e.grid_y + s:
                return True
        return False

    def get_cover_bonus(self, attacker: Entity, target: Entity) -> int:
        """
        Calculate AC bonus from cover (0, 2, or 5).
        5e cover: Half (+2 AC), Three-quarters (+5 AC), Total (can't target).
        Also considers elevation advantage (higher ground negates some cover).
        """
        best_bonus = 0

        # Elevation advantage: attacker above target reduces cover effectiveness
        elev_diff = attacker.elevation - target.elevation

        for t in self.terrain:
            if not t.provides_cover:
                continue

            # Is terrain adjacent to target?
            dist = math.hypot(t.grid_x - target.grid_x, t.grid_y - target.grid_y)
            if dist < 1.5:
                # Is terrain between attacker and target?
                v_ta_x = attacker.grid_x - target.grid_x
                v_ta_y = attacker.grid_y - target.grid_y
                v_tt_x = t.grid_x - target.grid_x
                v_tt_y = t.grid_y - target.grid_y

                if (v_ta_x * v_tt_x + v_ta_y * v_tt_y) > 0:
                    cb = t.cover_bonus
                    # If attacker is significantly above, reduce cover
                    if elev_diff >= 10 and cb <= 2:
                        cb = 0  # High ground negates half cover
                    elif elev_diff >= 20 and cb <= 5:
                        cb = 2  # Very high ground reduces 3/4 to half
                    best_bonus = max(best_bonus, cb)

        # Check LOS blocking terrain between attacker and target
        if best_bonus == 0:
            ax, ay = int(attacker.grid_x), int(attacker.grid_y)
            tx, ty = int(target.grid_x), int(target.grid_y)
            if check_los_blocked(self.terrain, ax, ay, tx, ty):
                best_bonus = max(best_bonus, 2)  # At minimum half cover if LOS obstructed

        return best_bonus

    def has_line_of_sight(self, e1: Entity, e2: Entity) -> bool:
        """Check if e1 can see e2. Considers terrain LOS blocking, darkness, invisibility.

        5e 2014 rules:
        - Heavily obscured (darkness, heavy fog): can't see → no LOS
        - Darkvision: treats darkness as dim light (lightly obscured) within range
        - Devil's Sight / Truesight: see normally in magical darkness
        - Blindsight: see without relying on sight at all
        """
        # Blindsight always works within range (ignore visibility entirely)
        bs_range = e1.get_blindsight_range()
        if bs_range > 0:
            dist_ft = self.get_distance(e1, e2) * 5
            if dist_ft <= bs_range:
                # Blindsight ignores invisible, darkness, everything
                # Still blocked by full cover (terrain LOS blocking)
                x1, y1 = int(e1.grid_x), int(e1.grid_y)
                x2, y2 = int(e2.grid_x), int(e2.grid_y)
                if check_los_blocked(self.terrain, x1, y1, x2, y2):
                    if not (e1.is_flying and e1.elevation >= 15):
                        return False
                return True

        # Invisible target: can't see unless truesight
        if e2.has_condition("Invisible") and not e1.has_feature("truesight"):
            return False

        x1, y1 = int(e1.grid_x), int(e1.grid_y)
        x2, y2 = int(e2.grid_x), int(e2.grid_y)

        # Check terrain LOS blocking (walls, full cover)
        if check_los_blocked(self.terrain, x1, y1, x2, y2):
            if e1.is_flying and e1.elevation >= 15:
                return True  # Can see over most walls from high altitude
            return False

        # Darkness check: target in darkness terrain (heavily obscured)
        t_at_target = self.get_terrain_at(x2, y2)
        if t_at_target and t_at_target.terrain_type == "darkness":
            # Devil's Sight / Truesight see through magical darkness
            if e1.has_feature("devil_sight") or e1.has_feature("truesight"):
                return True
            # Darkvision: treats darkness as dim light within range → can see (with disadvantage)
            dv_range = e1.get_darkvision_range()
            if dv_range > 0:
                dist_ft = self.get_distance(e1, e2) * 5
                if dist_ft <= dv_range:
                    return True  # Can see but effectively lightly obscured → disadvantage applied elsewhere
            return False  # No special sight: heavily obscured = can't see

        # Heavy fog also blocks LOS (already handled via blocks_los in terrain)

        return True

    def get_target_obscurement(self, attacker: Entity, target: Entity) -> str:
        """Determine visibility obscurement level from attacker to target.

        Returns:
          "none"    - clear vision, no penalty
          "light"   - lightly obscured (dim light, light fog) → disadvantage on Perception
                      In 5e 2014 this gives disadvantage on attack rolls (effectively Blinded)
          "heavy"   - heavily obscured → can't see (handled by LOS check, shouldn't reach here)
        """
        x2, y2 = int(target.grid_x), int(target.grid_y)
        t = self.get_terrain_at(x2, y2)

        # Devil's Sight / Truesight: see normally in all darkness
        if attacker.has_feature("devil_sight") or attacker.has_feature("truesight"):
            return "none"

        # Blindsight: no visual penalties
        bs_range = attacker.get_blindsight_range()
        if bs_range > 0:
            dist_ft = self.get_distance(attacker, target) * 5
            if dist_ft <= bs_range:
                return "none"

        if t:
            # Darkness: if darkvision can reach, treated as dim light (lightly obscured)
            if t.terrain_type == "darkness":
                dv_range = attacker.get_darkvision_range()
                dist_ft = self.get_distance(attacker, target) * 5
                if dv_range > 0 and dist_ft <= dv_range:
                    return "light"  # Darkvision treats darkness as dim light
                return "heavy"  # Shouldn't get here if LOS blocks, but safety

            # Dim light: lightly obscured (disadvantage on Perception-based sight)
            if t.terrain_type == "dim_light":
                dv_range = attacker.get_darkvision_range()
                dist_ft = self.get_distance(attacker, target) * 5
                if dv_range > 0 and dist_ft <= dv_range:
                    return "none"  # Darkvision: dim light → normal light
                return "light"

            # Light fog: lightly obscured
            if t.terrain_type == "fog_light":
                return "light"

        return "none"

    def is_passable(self, x: float, y: float, exclude: Entity = None) -> bool:
        """Returns True if cell is both unoccupied by entities and traversable terrain.
        Flying entities ignore ground obstacles (walls, closed doors) but not other entities."""
        size = exclude.size_in_squares if exclude else 1
        is_flyer = exclude.is_flying if exclude else False
        for dx in range(size):
            for dy in range(size):
                check_x, check_y = x + dx, y + dy
                if self.is_occupied(check_x, check_y, exclude=exclude):
                    return False
                if not is_flyer:
                    t = self.get_terrain_at(int(check_x), int(check_y))
                    if t and not t.passable:
                        return False
        return True

    def is_passable_or_jumpable(self, x: float, y: float, entity: Entity = None) -> bool:
        """Like is_passable but also allows gaps that the entity can jump/fly across.
        Used by AI pathfinding to consider jump routes."""
        if self.is_passable(x, y, exclude=entity):
            return True
        if entity and entity.is_flying:
            # Flyer can cross anything except entity-occupied
            return not self.is_occupied(x, y, exclude=entity)
        # Check if it's a jumpable gap
        t = self.get_terrain_at(int(x), int(y))
        if t and t.is_gap and entity:
            gap_ft = t.gap_width_ft
            if entity.can_jump_gap(gap_ft, running_start=True):
                return not self.is_occupied(x, y, exclude=entity)
        return False

    def get_gap_at(self, x: int, y: int):
        """Get gap terrain at position, or None."""
        t = self.get_terrain_at(x, y)
        if t and t.is_gap:
            return t
        return None

    def get_terrain_movement_cost(self, x: float, y: float, entity: Entity = None) -> float:
        """Returns movement multiplier: 1.0 normal, 2.0 difficult, 2.0 climbing.
        Flying entities ignore difficult terrain."""
        if entity and entity.is_flying:
            return 1.0
        t = self.get_terrain_at(int(x), int(y))
        if t:
            if t.is_difficult:
                return 2.0
            if t.is_climbable and entity and entity.is_climbing:
                # Climbing without climb speed = half speed (2x cost)
                if entity.stats.climb_speed <= 0:
                    return 2.0
        return 1.0

    def get_entity_at(self, x: float, y: float) -> Optional[Entity]:
        for e in self.entities:
            s = e.size_in_squares
            if e.grid_x <= x < e.grid_x + s and e.grid_y <= y < e.grid_y + s:
                return e
        return None

    def get_enemies_of(self, entity: Entity) -> List[Entity]:
        return [e for e in self.entities if e.is_player != entity.is_player and e.hp > 0 and "Banished" not in e.conditions]

    def get_allies_of(self, entity: Entity) -> List[Entity]:
        return [e for e in self.entities if e.is_player == entity.is_player and e.hp > 0 and e != entity and "Banished" not in e.conditions]

    # ------------------------------------------------------------------ #
    # Terrain                                                              #
    # ------------------------------------------------------------------ #

    def get_terrain_at(self, gx: int, gy: int) -> Optional[TerrainObject]:
        for t in self.terrain:
            if t.occupies(gx, gy):
                return t
        return None

    def add_terrain(self, terrain: TerrainObject):
        # Remove any existing terrain at the same cell first
        self.terrain = [t for t in self.terrain if not t.occupies(terrain.grid_x, terrain.grid_y)]
        self.terrain.append(terrain)

    def remove_terrain_at(self, gx: int, gy: int):
        self.terrain = [t for t in self.terrain if not t.occupies(gx, gy)]

    def spawn_spell_terrain(self, spell, caster, center_x, center_y):
        """Create persistent terrain tiles for a spell's area of effect."""
        import math
        terrain_type = spell.creates_terrain
        if not terrain_type:
            return
        radius_sq = spell.aoe_radius / 5.0  # convert feet to grid squares
        tiles_created = 0
        for dx in range(int(-radius_sq), int(radius_sq) + 1):
            for dy in range(int(-radius_sq), int(radius_sq) + 1):
                gx = int(center_x) + dx
                gy = int(center_y) + dy
                # Shape filtering
                if spell.aoe_shape in ("sphere", "cylinder"):
                    if math.hypot(dx, dy) > radius_sq:
                        continue
                elif spell.aoe_shape == "cube":
                    if abs(dx) > radius_sq or abs(dy) > radius_sq:
                        continue
                elif spell.aoe_shape == "line":
                    # Walls: thin strip along longest axis
                    if abs(dy) > 0 and abs(dx) > 0:
                        continue
                    if abs(dx) + abs(dy) > radius_sq:
                        continue
                # Don't overwrite non-spell terrain (walls, doors, etc.)
                existing = self.get_terrain_at(gx, gy)
                if existing and not existing.is_spell_terrain:
                    continue
                t = TerrainObject(
                    terrain_type=terrain_type,
                    grid_x=gx, grid_y=gy,
                    spell_owner=caster.name,
                    spell_name=spell.name,
                    is_spell_terrain=True,
                )
                self.add_terrain(t)
                tiles_created += 1
        if tiles_created > 0:
            self.log(f"  [TERRAIN] {caster.name}'s {spell.name} creates {tiles_created} tiles of {terrain_type}.")

    def remove_spell_terrain(self, caster_name: str, spell_name: str):
        """Remove all terrain tiles created by a specific spell from a specific caster."""
        before = len(self.terrain)
        self.terrain = [t for t in self.terrain
                        if not (t.is_spell_terrain and t.spell_owner == caster_name and t.spell_name == spell_name)]
        removed = before - len(self.terrain)
        if removed > 0:
            self.log(f"  [TERRAIN] {spell_name} terrain fades ({removed} tiles removed).")

    def toggle_door_at(self, gx: int, gy: int) -> bool:
        """Toggle a door at the given position. Returns True if toggled."""
        t = self.get_terrain_at(gx, gy)
        if t and t.is_door:
            if t.toggle_door():
                state = "opens" if t.door_open else "closes"
                self.log(f"  [DOOR] Door at ({gx},{gy}) {state}.")
                return True
            else:
                self.log(f"  [DOOR] Door at ({gx},{gy}) is locked!")
                return False
        return False

    def unlock_door_at(self, gx: int, gy: int) -> bool:
        """Unlock a locked door at the given position."""
        t = self.get_terrain_at(gx, gy)
        if t and t.is_door and t.is_locked:
            t.unlock()
            self.log(f"  [DOOR] Door at ({gx},{gy}) unlocked!")
            return True
        return False

    def get_elevation_at(self, gx: int, gy: int) -> int:
        """Get ground elevation in feet at grid position."""
        return get_elevation_at(self.terrain, gx, gy)

    def apply_fall_damage(self, entity: Entity, fall_height_ft: int):
        """Apply falling damage to an entity. 1d6 per 10ft, max 20d6. Lands prone."""
        if fall_height_ft <= 0:
            return
        dmg = calculate_fall_damage(fall_height_ft)
        if dmg > 0:
            dealt, _ = entity.take_damage(dmg, "bludgeoning")
            self.log(f"  [FALL] {entity.name} falls {fall_height_ft}ft and takes {dealt} bludgeoning damage!")
            # Falling creatures land prone (PHB p.183)
            if entity.hp > 0 and not entity.has_condition("Prone"):
                entity.add_condition("Prone")
                self.log(f"  [FALL] {entity.name} lands prone.")
        entity.is_flying = False
        entity.is_climbing = False

    def move_entity_with_elevation(self, entity: Entity, new_x: float, new_y: float,
                                    is_jumping: bool = False):
        """Move entity and handle elevation changes, fall damage, climbing costs.
        is_jumping: entity is mid-jump (won't fall into gaps)."""
        old_elev = entity.elevation
        new_ground = self.get_elevation_at(int(new_x), int(new_y))

        # Check for gap/chasm at destination
        t_at_new = self.get_terrain_at(int(new_x), int(new_y))
        if t_at_new and t_at_new.is_gap and not entity.is_flying and not is_jumping:
            # Entity walks into a chasm without jumping - they fall!
            fall_dist = abs(t_at_new.elevation) + old_elev
            entity.grid_x = float(new_x)
            entity.grid_y = float(new_y)
            entity.elevation = t_at_new.elevation
            if t_at_new.is_hazard:
                # Lava/acid chasm: hazard damage on top of fall
                from engine.dice import roll_dice
                hdmg = roll_dice(t_at_new.hazard_damage)
                dealt, _ = entity.take_damage(hdmg, t_at_new.hazard_damage_type)
                self.log(f"  [HAZARD] {entity.name} falls into {t_at_new.name}! {dealt} {t_at_new.hazard_damage_type} damage!")
            self.apply_fall_damage(entity, fall_dist)
            self.log(f"  [CHASM] {entity.name} falls into {t_at_new.name}!")
            return

        if entity.is_flying:
            # Flying entity: stays at current elevation or terrain elevation, whichever is higher
            entity.elevation = max(entity.elevation, new_ground)
        elif entity.is_climbing:
            # Climbing: entity reaches the terrain's elevation
            entity.elevation = new_ground
        else:
            # Walking: if terrain is lower, check for fall
            if new_ground < old_elev:
                fall_dist = old_elev - new_ground
                t_at_new = self.get_terrain_at(int(new_x), int(new_y))
                # Stairs/ladders/bridges are safe transitions
                if t_at_new and t_at_new.terrain_type in ("stairs_up", "stairs_down", "ladder", "bridge"):
                    entity.elevation = new_ground
                elif fall_dist >= 10:
                    # Fall damage
                    entity.elevation = new_ground
                    self.apply_fall_damage(entity, fall_dist)
                else:
                    # Small drop (< 10ft), no damage
                    entity.elevation = new_ground
            else:
                # Going up: need stairs/ladder/climb, or it's same level
                if new_ground > old_elev:
                    t_at_new = self.get_terrain_at(int(new_x), int(new_y))
                    if t_at_new and t_at_new.terrain_type in ("stairs_up", "stairs_down", "ladder"):
                        entity.elevation = new_ground
                    elif t_at_new and t_at_new.is_climbable:
                        entity.elevation = new_ground
                        entity.is_climbing = True
                    else:
                        entity.elevation = new_ground
                else:
                    entity.elevation = new_ground

        entity.grid_x = float(new_x)
        entity.grid_y = float(new_y)

    # ------------------------------------------------------------------ #
    # Manual DM operations                                                 #
    # ------------------------------------------------------------------ #

    def update_initiative(self, entity: Entity, delta: int):
        current = self.get_current_entity()
        entity.initiative += delta
        self.entities.sort(key=lambda e: e.initiative, reverse=True)
        self.turn_index = self.entities.index(current)

    def check_battle_over(self) -> Optional[str]:
        players_alive = any(e.is_player and e.hp > 0 for e in self.entities)
        enemies_alive = any(not e.is_player and e.hp > 0 and not e.is_lair and not e.is_summon for e in self.entities)
        if not players_alive:
            return "enemies"
        if not enemies_alive:
            return "players"
        return None

    def finalize_battle(self, winner: str):
        """Finalize battle statistics and generate report."""
        self.stats_tracker.finalize(self.entities, self.round, winner)

    def get_win_probability(self) -> dict:
        """Get current win probability for players."""
        return self.win_calculator.calculate(self)

    def get_encounter_danger(self) -> dict:
        """Get pre-combat encounter danger assessment."""
        from engine.win_probability import assess_encounter_danger
        players = [e for e in self.entities if e.is_player]
        enemies = [e for e in self.entities if not e.is_player and not e.is_lair]
        return assess_encounter_danger(players, enemies)

    def get_dm_suggestion(self, entity: Entity):
        """Get AI suggestion for a player's turn."""
        return self.dm_advisor.get_optimal_move(entity, self)

    def rate_player_action(self, entity: Entity, action_type: str,
                           target: Entity = None, damage_dealt: int = 0,
                           spell_name: str = "", moved_distance: float = 0):
        """Rate a player's action compared to AI optimal."""
        return self.dm_advisor.rate_player_action(
            entity, self, action_type, target, damage_dealt,
            spell_name, moved_distance)

    # ------------------------------------------------------------------ #
    # Save / Load                                                          #
    # ------------------------------------------------------------------ #

    def get_state_dict(self) -> dict:
        """Serialize full combat state to a dictionary."""
        data = {
            "combat_started": self.combat_started,
            "round": self.round,
            "current_plane": self.current_plane,
            "turn_index": self.turn_index,
            "entities": [],
            "terrain": [t.to_dict() for t in self.terrain],
            "weather": self.weather,
            "lair_enabled": self.lair_enabled,
        }
        for e in self.entities:
            ent_data = {
                "name": e.name,
                "base_name": e.stats.name,
                "is_player": e.is_player,
                "grid_x": e.grid_x,
                "grid_y": e.grid_y,
                "hp": e.hp,
                "max_hp": e.max_hp,
                "temp_hp": e.temp_hp,
                "initiative": e.initiative,
                "conditions": list(e.conditions),
                "condition_metadata": copy.deepcopy(e.condition_metadata),
                "spell_slots": copy.deepcopy(e.spell_slots),
                "legendary_resistances_left": e.legendary_resistances_left,
                "legendary_actions_left": e.legendary_actions_left,
                "exhaustion": e.exhaustion,
                "feature_uses": copy.deepcopy(e.feature_uses),
                "action_used": e.action_used,
                "bonus_action_used": e.bonus_action_used,
                "reaction_used": e.reaction_used,
                "movement_left": e.movement_left,
                "concentrating_on": e.concentrating_on.name if e.concentrating_on else None,
                "death_save_successes": e.death_save_successes,
                "death_save_failures": e.death_save_failures,
                "is_stable": e.is_stable,
                "is_lair": e.is_lair,
                "lair_owner_name": e.lair_owner.name if e.lair_owner else None,
                "last_lair_action": e.last_lair_action,
                "active_effects": copy.deepcopy(e.active_effects),
                "notes": e.notes,
                "rage_active": e.rage_active,
                "rage_rounds": e.rage_rounds,
                "rages_left": e.rages_left,
                "ki_points_left": e.ki_points_left,
                "sorcery_points_left": e.sorcery_points_left,
                "lay_on_hands_left": e.lay_on_hands_left,
                "bardic_inspiration_left": e.bardic_inspiration_left,
                "is_summon": e.is_summon,
                "summon_rounds_left": e.summon_rounds_left,
                "summon_spell_name": e.summon_spell_name,
                "summon_owner_name": e.summon_owner.name if e.summon_owner else None,
                "marked_target_name": e.marked_target.name if e.marked_target else None,
                "death_save_history": e.death_save_history,
                "is_surprised": e.is_surprised,
                # Grapple state
                "grappling_names": [g.name for g in e.grappling] if e.grappling else [],
                "grappled_by_name": e.grappled_by.name if e.grappled_by else None,
                # Condition sources (Frightened, Charmed sources)
                "condition_sources": {k: v.name for k, v in e.condition_sources.items()} if e.condition_sources else {},
                # Elevation & flying
                "elevation": e.elevation,
                "is_flying": e.is_flying,
                "is_climbing": e.is_climbing,
            }
            data["entities"].append(ent_data)
        return data

    def save_state(self, filepath: str):
        """Serialize full combat state to JSON file."""
        data = self.get_state_dict()
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    def restore_state(self, data: dict):
        """Restore state from dictionary."""
        from data.library import library
        from data.heroes import hero_list as heroes
        from engine.terrain import TerrainObject
        from engine.entities import Entity

        self.round = data.get("round", 1)
        self.combat_started = data.get("combat_started", True)
        self.current_plane = data.get("current_plane", "Material Plane")
        self.turn_index = data.get("turn_index", 0)
        self.weather = data.get("weather", "Clear")
        self.terrain = [TerrainObject.from_dict(t) for t in data.get("terrain", [])]
        
        self.entities = []
        self.pending_reactions = []
        self.legendary_queue = []

        hero_map = {h.name: h for h in heroes}

        for ent_data in data["entities"]:
            base_name = ent_data.get("base_name", ent_data["name"])
            stats = None

            if ent_data["is_player"]:
                stats = copy.deepcopy(hero_map.get(base_name))
                if stats is None:
                    for h in heroes:
                        if h.name in base_name or base_name in h.name:
                            stats = copy.deepcopy(h)
                            break
            else:
                if ent_data.get("is_lair"):
                     from data.models import CreatureStats
                     stats = CreatureStats(name="Lair Action", hit_points=1, speed=0, challenge_rating=0)
                else:
                    try:
                        stats = library.get_monster(base_name)
                    except ValueError:
                        stripped = base_name.rsplit(" ", 1)[0]
                        try:
                            stats = library.get_monster(stripped)
                        except ValueError:
                            pass

            if stats is None:
                from data.models import CreatureStats
                stats = CreatureStats(name=ent_data["name"], hit_points=ent_data["max_hp"])

            stats.name = ent_data["name"]
            e = Entity(stats, ent_data["grid_x"], ent_data["grid_y"], ent_data["is_player"])
            e.hp = ent_data["hp"]
            e.max_hp = ent_data["max_hp"]
            e.temp_hp = ent_data["temp_hp"]
            e.initiative = ent_data["initiative"]
            e.conditions = set(ent_data["conditions"])
            e.condition_metadata = ent_data.get("condition_metadata", {})
            e.spell_slots = ent_data["spell_slots"]
            e.legendary_resistances_left = ent_data["legendary_resistances_left"]
            e.legendary_actions_left = ent_data["legendary_actions_left"]
            e.exhaustion = ent_data["exhaustion"]
            e.feature_uses = ent_data["feature_uses"]
            e.action_used = ent_data["action_used"]
            e.bonus_action_used = ent_data["bonus_action_used"]
            e.reaction_used = ent_data["reaction_used"]
            e.movement_left = ent_data["movement_left"]
            e.death_save_successes = ent_data["death_save_successes"]
            e.death_save_failures = ent_data["death_save_failures"]
            e.is_stable = ent_data["is_stable"]
            e.is_lair = ent_data.get("is_lair", False)
            e.last_lair_action = ent_data.get("last_lair_action", "")
            e.active_effects = ent_data.get("active_effects", {})
            e.notes = ent_data.get("notes", "")
            e.is_surprised = ent_data.get("is_surprised", False)
            e.rage_active = ent_data.get("rage_active", False)
            e.rage_rounds = ent_data.get("rage_rounds", 0)
            e.rages_left = ent_data.get("rages_left", e.stats.rage_count)
            e.ki_points_left = ent_data.get("ki_points_left", e.stats.ki_points)
            e.sorcery_points_left = ent_data.get("sorcery_points_left", e.stats.sorcery_points)
            e.lay_on_hands_left = ent_data.get("lay_on_hands_left", e.stats.lay_on_hands_pool)
            e.bardic_inspiration_left = ent_data.get("bardic_inspiration_left", e.stats.bardic_inspiration_count)
            e.is_summon = ent_data.get("is_summon", False)
            e.summon_rounds_left = ent_data.get("summon_rounds_left", 0)
            e.summon_spell_name = ent_data.get("summon_spell_name", "")
            e.death_save_history = ent_data.get("death_save_history", [])
            e.elevation = ent_data.get("elevation", 0)
            e.is_flying = ent_data.get("is_flying", False)
            e.is_climbing = ent_data.get("is_climbing", False)

            conc_name = ent_data.get("concentrating_on")
            if conc_name:
                for sp in list(stats.spells_known) + list(stats.cantrips):
                    if sp.name == conc_name:
                        e.concentrating_on = sp
                        break

            self.entities.append(e)

        # Link lair owners
        for i, ent_data in enumerate(data["entities"]):
            owner_name = ent_data.get("lair_owner_name")
            if owner_name:
                owner = next((x for x in self.entities if x.name == owner_name), None)
                self.entities[i].lair_owner = owner

        # Link summon owners and marked targets
        for i, ent_data in enumerate(data["entities"]):
            summon_owner_name = ent_data.get("summon_owner_name")
            if summon_owner_name:
                owner = next((x for x in self.entities if x.name == summon_owner_name), None)
                self.entities[i].summon_owner = owner
            marked_name = ent_data.get("marked_target_name")
            if marked_name:
                marked = next((x for x in self.entities if x.name == marked_name), None)
                self.entities[i].marked_target = marked

        # Link grapple relationships
        for i, ent_data in enumerate(data["entities"]):
            grappled_by_name = ent_data.get("grappled_by_name")
            if grappled_by_name:
                grappler = next((x for x in self.entities if x.name == grappled_by_name), None)
                if grappler:
                    self.entities[i].grappled_by = grappler
            for gname in ent_data.get("grappling_names", []):
                target = next((x for x in self.entities if x.name == gname), None)
                if target:
                    self.entities[i].grappling.append(target)
            # Link condition sources (Frightened/Charmed)
            for cond, source_name in ent_data.get("condition_sources", {}).items():
                source = next((x for x in self.entities if x.name == source_name), None)
                if source:
                    self.entities[i].condition_sources[cond] = source

    @classmethod
    def from_save(cls, filepath: str, log_callback: Callable[[str], None]) -> "BattleSystem":
        """Reconstruct a BattleSystem from a saved JSON file."""
        from data.library import library
        from data.heroes import hero_list as heroes

        with open(filepath) as f:
            data = json.load(f)

        # Build instance without calling __init__ (which rolls initiative etc.)
        sys_obj = object.__new__(cls)
        sys_obj.grid_size = 60
        sys_obj.entities = []
        sys_obj.log = log_callback
        sys_obj.round = data.get("round", 1)
        sys_obj.combat_started = data.get("combat_started", True)
        sys_obj.current_plane = data.get("current_plane", "Material Plane")
        sys_obj.turn_index = data.get("turn_index", 0)
        sys_obj.ai = TacticalAI()
        sys_obj.terrain = []
        sys_obj.weather = data.get("weather", "Clear")
        sys_obj.pending_reactions = []
        sys_obj.legendary_queue = []
        sys_obj.lair_enabled = data.get("lair_enabled", False)

        hero_map = {h.name: h for h in heroes}

        for ent_data in data["entities"]:
            base_name = ent_data.get("base_name", ent_data["name"])
            stats = None

            if ent_data["is_player"]:
                stats = copy.deepcopy(hero_map.get(base_name))
                if stats is None:
                    # Try substring match (handles renamed heroes)
                    for h in heroes:
                        if h.name in base_name or base_name in h.name:
                            stats = copy.deepcopy(h)
                            break
            else:
                if ent_data.get("is_lair"):
                    from data.models import CreatureStats as CS
                    stats = CS(name="Lair Action", hit_points=1, speed=0, challenge_rating=0)
                else:
                    try:
                        stats = library.get_monster(base_name)
                    except ValueError:
                        # Strip number suffix (e.g. "Goblin 2" → "Goblin")
                        stripped = base_name.rsplit(" ", 1)[0]
                        try:
                            stats = library.get_monster(stripped)
                        except ValueError:
                            pass

            if stats is None:
                log_callback(f"[LOAD] Could not find stats for '{base_name}', skipping.")
                continue

            stats.name = ent_data["name"]  # restore display name (may have number suffix)
            e = Entity(stats, ent_data["grid_x"], ent_data["grid_y"], ent_data["is_player"])
            e.hp = ent_data["hp"]
            e.max_hp = ent_data["max_hp"]
            e.temp_hp = ent_data["temp_hp"]
            e.initiative = ent_data["initiative"]
            e.conditions = set(ent_data["conditions"])
            e.condition_metadata = ent_data.get("condition_metadata", {})
            e.spell_slots = ent_data["spell_slots"]
            e.legendary_resistances_left = ent_data["legendary_resistances_left"]
            e.legendary_actions_left = ent_data["legendary_actions_left"]
            e.exhaustion = ent_data["exhaustion"]
            e.feature_uses = ent_data["feature_uses"]
            e.action_used = ent_data["action_used"]
            e.bonus_action_used = ent_data["bonus_action_used"]
            e.reaction_used = ent_data["reaction_used"]
            e.movement_left = ent_data["movement_left"]
            e.death_save_successes = ent_data["death_save_successes"]
            e.death_save_failures = ent_data["death_save_failures"]
            e.is_stable = ent_data["is_stable"]
            e.is_lair = ent_data.get("is_lair", False)
            e.last_lair_action = ent_data.get("last_lair_action", "")
            e.active_effects = ent_data.get("active_effects", {})
            e.notes = ent_data.get("notes", "")
            e.is_surprised = ent_data.get("is_surprised", False)
            e.rage_active = ent_data.get("rage_active", False)
            e.rage_rounds = ent_data.get("rage_rounds", 0)
            e.rages_left = ent_data.get("rages_left", e.stats.rage_count)
            e.ki_points_left = ent_data.get("ki_points_left", e.stats.ki_points)
            e.sorcery_points_left = ent_data.get("sorcery_points_left", e.stats.sorcery_points)
            e.lay_on_hands_left = ent_data.get("lay_on_hands_left", e.stats.lay_on_hands_pool)
            e.bardic_inspiration_left = ent_data.get("bardic_inspiration_left", e.stats.bardic_inspiration_count)
            e.is_summon = ent_data.get("is_summon", False)
            e.summon_rounds_left = ent_data.get("summon_rounds_left", 0)
            e.summon_spell_name = ent_data.get("summon_spell_name", "")
            e.death_save_history = ent_data.get("death_save_history", [])
            e.elevation = ent_data.get("elevation", 0)
            e.is_flying = ent_data.get("is_flying", False)
            e.is_climbing = ent_data.get("is_climbing", False)

            conc_name = ent_data.get("concentrating_on")
            if conc_name:
                for sp in list(stats.spells_known) + list(stats.cantrips):
                    if sp.name == conc_name:
                        e.concentrating_on = sp
                        break

            sys_obj.entities.append(e)

        # Build name→entity lookup for linking (safe even if entities were skipped)
        entity_by_name = {e.name: e for e in sys_obj.entities}

        # Link lair owners, summon owners, marked targets, grapple, and condition sources
        for ent_data in data["entities"]:
            ent = entity_by_name.get(ent_data["name"])
            if ent is None:
                continue

            owner_name = ent_data.get("lair_owner_name")
            if owner_name:
                ent.lair_owner = entity_by_name.get(owner_name)

            summon_owner_name = ent_data.get("summon_owner_name")
            if summon_owner_name:
                ent.summon_owner = entity_by_name.get(summon_owner_name)

            marked_name = ent_data.get("marked_target_name")
            if marked_name:
                ent.marked_target = entity_by_name.get(marked_name)

            grappled_by_name = ent_data.get("grappled_by_name")
            if grappled_by_name:
                grappler = entity_by_name.get(grappled_by_name)
                if grappler:
                    ent.grappled_by = grappler

            for gname in ent_data.get("grappling_names", []):
                target = entity_by_name.get(gname)
                if target:
                    ent.grappling.append(target)

            for cond, source_name in ent_data.get("condition_sources", {}).items():
                source = entity_by_name.get(source_name)
                if source:
                    ent.condition_sources[cond] = source

        sys_obj.turn_index = min(sys_obj.turn_index, max(0, len(sys_obj.entities) - 1))
        sys_obj.terrain = [TerrainObject.from_dict(t) for t in data.get("terrain", [])]

        # Initialize analytics
        sys_obj.stats_tracker = BattleStatisticsTracker()
        sys_obj.dm_advisor = DMAdvisor()
        sys_obj.win_calculator = WinProbabilityCalculator()
        sys_obj._last_damage_source = ""

        log_callback(f"=== ENCOUNTER LOADED (Round {sys_obj.round}) ===")
        return sys_obj
