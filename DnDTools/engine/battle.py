"""
BattleSystem – manages combat state, turn order, grid positions, terrain.
The TacticalAI (engine/ai.py) computes what NPCs should do.
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
from data.models import CreatureStats


class BattleSystem:
    def __init__(self, log_callback: Callable[[str], None], initial_entities: List[Entity] = None):
        self.grid_size = 60             # pixels per square
        self.entities: List[Entity] = initial_entities or []
        self.turn_index = 0
        self.log = log_callback
        self.round = 1
        self.ai = TacticalAI()
        self.terrain: List[TerrainObject] = []

        # Pending OA reactions: list of (reactor, mover)
        self.pending_reactions: List[tuple] = []

        # Legendary action queue: entities that may still act this round
        self.legendary_queue: List[Entity] = []

        if not self.entities:
            self._init_demo_entities()
        self._start_combat()

    # ------------------------------------------------------------------ #
    # Setup                                                                #
    # ------------------------------------------------------------------ #

    def _start_combat(self):
        for entity in self.entities:
            entity.roll_initiative()
        self.entities.sort(key=lambda e: e.initiative, reverse=True)
        self.log("=== COMBAT STARTED ===")
        self.log("Initiative order: " + " > ".join(e.name for e in self.entities))
        curr = self.get_current_entity()
        curr.reset_turn()
        self.log(f"--- Round {self.round}: {curr.name}'s turn ---")

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
        return self.entities[self.turn_index]

    def next_turn(self) -> Entity:
        # Check for legendary actions at end of this turn (for other legendary creatures)
        self._process_legendary_queue()

        # Advance turn
        self.turn_index += 1
        if self.turn_index >= len(self.entities):
            self.turn_index = 0
            self.round += 1
            # Reset legendary actions for all creatures
            for e in self.entities:
                e.reset_legendary_actions()
            self.log(f"=== ROUND {self.round} ===")

        # Skip dead entities
        attempts = 0
        while self.entities[self.turn_index].hp <= 0 and attempts < len(self.entities):
            self.turn_index = (self.turn_index + 1) % len(self.entities)
            attempts += 1

        current = self.get_current_entity()
        current.reset_turn()

        # Check hazard terrain at start of turn
        self._check_hazard_damage(current)

        # Add to legendary queue if this creature has legendary actions
        self._build_legendary_queue()

        self.log(f"--- {current.name}'s turn (Round {self.round}, Initiative {current.initiative}) ---")
        if current.conditions:
            for cond in current.conditions:
                self.log(f"  [STATUS] {cond}")
        if current.concentrating_on:
            self.log(f"  [CONCENTRATION] {current.concentrating_on.name}")
        return current

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

    def _process_legendary_queue(self):
        """Allow legendary creatures to use actions now."""
        for leg_entity in self.legendary_queue:
            if leg_entity.legendary_actions_left <= 0:
                continue
            step = self.ai.calculate_legendary_action(leg_entity, self)
            if step:
                self.log(f"[LEG] {step.description}")

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
            if math.hypot(e.grid_x - x, e.grid_y - y) < 0.9:
                return True
        return False

    def is_passable(self, x: float, y: float, exclude: Entity = None) -> bool:
        """Returns True if cell is both unoccupied by entities and traversable terrain."""
        if self.is_occupied(x, y, exclude=exclude):
            return False
        t = self.get_terrain_at(int(x), int(y))
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
        best = None
        best_dist = 0.6
        for e in self.entities:
            d = math.hypot(e.grid_x + 0.5 - x, e.grid_y + 0.5 - y)
            if d < best_dist:
                best_dist = d
                best = e
        return best

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

    # ------------------------------------------------------------------ #
    # Save / Load                                                          #
    # ------------------------------------------------------------------ #

    def save_state(self, filepath: str):
        """Serialize full combat state to JSON."""
        data = {
            "round": self.round,
            "turn_index": self.turn_index,
            "entities": [],
            "terrain": [t.to_dict() for t in self.terrain],
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
                "spell_slots": e.spell_slots,
                "legendary_resistances_left": e.legendary_resistances_left,
                "legendary_actions_left": e.legendary_actions_left,
                "exhaustion": e.exhaustion,
                "feature_uses": e.feature_uses,
                "action_used": e.action_used,
                "bonus_action_used": e.bonus_action_used,
                "reaction_used": e.reaction_used,
                "movement_left": e.movement_left,
                "concentrating_on": e.concentrating_on.name if e.concentrating_on else None,
                "death_save_successes": e.death_save_successes,
                "death_save_failures": e.death_save_failures,
                "is_stable": e.is_stable,
            }
            data["entities"].append(ent_data)
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

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
        sys_obj.turn_index = data.get("turn_index", 0)
        sys_obj.ai = TacticalAI()
        sys_obj.terrain = []
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

            conc_name = ent_data.get("concentrating_on")
            if conc_name:
                for sp in list(stats.spells_known) + list(stats.cantrips):
                    if sp.name == conc_name:
                        e.concentrating_on = sp
                        break

            sys_obj.entities.append(e)

        sys_obj.turn_index = min(sys_obj.turn_index, max(0, len(sys_obj.entities) - 1))
        sys_obj.terrain = [TerrainObject.from_dict(t) for t in data.get("terrain", [])]

        log_callback(f"=== ENCOUNTER LOADED (Round {sys_obj.round}) ===")
        return sys_obj
