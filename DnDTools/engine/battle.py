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
from engine.terrain import TerrainObject
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

    def start_combat(self):
        self.combat_started = True

        # Register entities with stats tracker
        for entity in self.entities:
            if not entity.is_lair:
                self.stats_tracker.register_entity(entity)

        # Check for Lair Actions
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

        self.entities.append(ent)
        # Re-sort to maintain initiative order
        current = self.get_current_entity()
        self.entities.sort(key=lambda e: e.initiative, reverse=True)
        self.turn_index = self.entities.index(current)

        self.log(f"[SUMMON] {name} appears at ({int(x)},{int(y)})!")
        return ent

    def remove_expired_summons(self):
        """Remove summons that have expired."""
        current = self.get_current_entity() if self.entities else None
        expired = [e for e in self.entities if e.is_summon and e.summon_rounds_left <= 0]
        for e in expired:
            self.log(f"[SUMMON] {e.name} disappears.")
        self.entities = [e for e in self.entities if e not in expired]
        if current and current in self.entities:
            self.turn_index = self.entities.index(current)
        elif self.entities:
            self.turn_index = min(self.turn_index, len(self.entities) - 1)

    def next_turn(self) -> Optional[Entity]:
        if not self.entities:
            return None

        # --- END OF TURN LOGIC (Previous Entity) ---
        prev_ent = self.entities[self.turn_index]
        if prev_ent.hp > 0:
            self._handle_end_of_turn_saves(prev_ent)

        # Check Barbarian Rage end-of-turn
        if prev_ent.rage_active:
            if prev_ent.check_rage_end():
                self.log(f"[RAGE] {prev_ent.name}'s rage ends! (No attack/damage this turn)")

        # Clean up expired summons
        self.remove_expired_summons()

        # Advance turn
        self.turn_index += 1
        if self.turn_index >= len(self.entities):
            self.turn_index = 0
            self.round += 1
            self.log(f"=== ROUND {self.round} ===")

        # Find next valid entity (Alive OR Dying Player OR Lair)
        start_index = self.turn_index
        while True:
            ent = self.entities[self.turn_index]
            is_alive = ent.hp > 0
            # Players roll death saves, so they get a turn even if 0 HP (unless dead-dead or stable)
            is_dying_player = ent.is_player and ent.hp <= 0 and ent.death_save_failures < 3 and not ent.is_stable
            
            if is_alive or is_dying_player or ent.is_lair:
                break
            
            self.turn_index = (self.turn_index + 1) % len(self.entities)
            if self.turn_index == 0:
                self.round += 1
                self.log(f"=== ROUND {self.round} ===")
            
            if self.turn_index == start_index:
                break # Everyone dead/skipped

        current = self.get_current_entity()
        
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

        # Check hazard terrain at start of turn
        if current.hp > 0:
            self._check_hazard_damage(current)

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

    def _handle_end_of_turn_saves(self, entity: Entity):
        """Check if entity can shake off any conditions at end of turn."""
        # Iterate a copy since we might modify the dict
        for cond, meta in list(entity.condition_metadata.items()):
            ability = meta.get("save")
            dc = meta.get("dc")
            if ability and dc:
                bonus = entity.get_save_bonus(ability)
                roll = random.randint(1, 20)
                total = roll + bonus
                if total >= dc:
                    entity.remove_condition(cond)
                    self.log(f"[SAVE] {entity.name} rolled {total} (DC {dc} {ability}) and is no longer {cond}!")
                else:
                    self.log(f"[SAVE] {entity.name} rolled {total} (DC {dc} {ability}) and remains {cond}.")

    def _check_hazard_damage(self, entity: Entity):
        """Apply hazard terrain damage at the start of an entity's turn."""
        t = self.get_terrain_at(int(entity.grid_x), int(entity.grid_y))
        if t and t.is_hazard:
            dmg = roll_dice(t.hazard_damage)
            dealt, _ = entity.take_damage(dmg, t.hazard_damage_type)
            self.log(f"  [HAZARD] {entity.name} takes {dealt} {t.hazard_damage_type} from {t.label}!")

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
        oas = []
        for e in self.entities:
            if e == mover or e.hp <= 0 or e.reaction_used:
                continue
            if e.is_player == mover.is_player:
                continue  # same team
            was_adjacent = math.hypot(old_x - e.grid_x, old_y - e.grid_y) < 1.5
            now_adjacent = self.is_adjacent(e, mover)
            if was_adjacent and not now_adjacent:
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

    def get_distance(self, e1: Entity, e2: Entity) -> float:
        return math.hypot(e1.grid_x - e2.grid_x, e1.grid_y - e2.grid_y)

    def is_adjacent(self, e1: Entity, e2: Entity) -> bool:
        return self.get_distance(e1, e2) < 1.5

    def is_occupied(self, x: float, y: float, exclude: Entity = None) -> bool:
        for e in self.entities:
            if e == exclude or e.hp <= 0:
                continue
            # Check if point (x,y) is inside e's footprint
            s = e.size_in_squares
            if e.grid_x <= x < e.grid_x + s and e.grid_y <= y < e.grid_y + s:
                return True
        return False

    def is_passable(self, x: float, y: float, exclude: Entity = None) -> bool:
        """Returns True if cell is both unoccupied by entities and traversable terrain."""
        # Check full footprint if entity is known
        size = exclude.size_in_squares if exclude else 1
        for dx in range(size):
            for dy in range(size):
                check_x, check_y = x + dx, y + dy
                if self.is_occupied(check_x, check_y, exclude=exclude):
                    return False
                t = self.get_terrain_at(int(check_x), int(check_y))
                if t and not t.passable:
                    return False
        return True

    def get_terrain_movement_cost(self, x: float, y: float) -> float:
        """Returns movement multiplier: 1.0 normal, 2.0 difficult."""
        t = self.get_terrain_at(int(x), int(y))
        if t and t.is_difficult:
            return 2.0
        return 1.0

    def get_entity_at(self, x: float, y: float) -> Optional[Entity]:
        for e in self.entities:
            s = e.size_in_squares
            if e.grid_x <= x < e.grid_x + s and e.grid_y <= y < e.grid_y + s:
                return e
        return None

    def get_enemies_of(self, entity: Entity) -> List[Entity]:
        return [e for e in self.entities if e.is_player != entity.is_player and e.hp > 0]

    def get_allies_of(self, entity: Entity) -> List[Entity]:
        return [e for e in self.entities if e.is_player == entity.is_player and e.hp > 0 and e != entity]

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
        enemies_alive = any(not e.is_player and e.hp > 0 for e in self.entities)
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
            "turn_index": self.turn_index,
            "entities": [],
            "terrain": [t.to_dict() for t in self.terrain],
            "weather": self.weather,
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
            e.active_effects = ent_data.get("active_effects", {})
            e.notes = ent_data.get("notes", "")
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
        sys_obj.turn_index = data.get("turn_index", 0)
        sys_obj.ai = TacticalAI()
        sys_obj.terrain = []
        sys_obj.weather = data.get("weather", "Clear")
        sys_obj.pending_reactions = []
        sys_obj.legendary_queue = []

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
            e.active_effects = ent_data.get("active_effects", {})
            e.notes = ent_data.get("notes", "")
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

            conc_name = ent_data.get("concentrating_on")
            if conc_name:
                for sp in list(stats.spells_known) + list(stats.cantrips):
                    if sp.name == conc_name:
                        e.concentrating_on = sp
                        break

            sys_obj.entities.append(e)

        # Link lair owners
        for i, ent_data in enumerate(data["entities"]):
            owner_name = ent_data.get("lair_owner_name")
            if owner_name:
                owner = next((x for x in sys_obj.entities if x.name == owner_name), None)
                sys_obj.entities[i].lair_owner = owner

        # Link summon owners and marked targets
        for i, ent_data in enumerate(data["entities"]):
            summon_owner_name = ent_data.get("summon_owner_name")
            if summon_owner_name:
                owner = next((x for x in sys_obj.entities if x.name == summon_owner_name), None)
                sys_obj.entities[i].summon_owner = owner
            marked_name = ent_data.get("marked_target_name")
            if marked_name:
                marked = next((x for x in sys_obj.entities if x.name == marked_name), None)
                sys_obj.entities[i].marked_target = marked

        sys_obj.turn_index = min(sys_obj.turn_index, max(0, len(sys_obj.entities) - 1))
        sys_obj.terrain = [TerrainObject.from_dict(t) for t in data.get("terrain", [])]

        log_callback(f"=== ENCOUNTER LOADED (Round {sys_obj.round}) ===")
        return sys_obj
