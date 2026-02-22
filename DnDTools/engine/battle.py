"""
BattleSystem – manages combat state, turn order, grid positions.
The TacticalAI (engine/ai.py) computes what NPCs should do.
"""
import math
import random
from typing import List, Optional, Callable
from engine.entities import Entity
from engine.ai import TacticalAI, TurnPlan, ActionStep
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
        from engine.entities import Entity as E
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

        # Add to legendary queue if this creature has legendary actions
        self._build_legendary_queue()

        self.log(f"--- {current.name}'s turn (Round {self.round}, Initiative {current.initiative}) ---")
        if current.conditions:
            for cond in current.conditions:
                self.log(f"  [STATUS] {cond}")
        if current.concentrating_on:
            self.log(f"  [CONCENTRATION] {current.concentrating_on.name}")
        return current

    def _build_legendary_queue(self):
        """After each turn, legendary creatures can use their legendary actions."""
        self.legendary_queue = [
            e for e in self.entities
            if e.legendary_actions_left > 0 and e.hp > 0 and e != self.get_current_entity()
        ]

    def _process_legendary_queue(self):
        """Allow legendary creatures to use actions now."""
        current = self.get_current_entity()
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
        # We need a "preview" mode - compute without modifying state.
        # For simplicity: the AI modifies state directly and we return the plan for UI display.
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
                # Triggers OA
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
