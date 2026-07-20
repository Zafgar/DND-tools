"""Phase 53 — AI (NPC) movement provokes opportunity attacks.

Previously only player token-drag movement ran check_opportunity_attacks;
an enemy walking out of a PC's reach was never punished. The AI move
step now hands off to the same reaction flow (pause -> resolve -> resume).
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import unittest

import pygame
pygame.init()
pygame.display.set_mode((320, 240))

from data.models import CreatureStats, AbilityScores, Action
from engine.entities import Entity
from engine.ai import TurnPlan, ActionStep
from states.battle_state import BattleState


class _FM:
    def __init__(self):
        self.screen = pygame.display.get_surface()
        self.running = True

    def change_state(self, *a, **k):
        pass


def _mk(name, x, y, is_player, hp=40, ac=5):
    # Very low AC so the OA reliably hits in the test.
    s = CreatureStats(name=name, hit_points=hp, armor_class=ac, speed=30,
                      abilities=AbilityScores(strength=16, dexterity=12),
                      actions=[Action("Sword", "Melee", 8, "1d8", 3,
                                      "slashing", range=5)])
    return Entity(s, x, y, is_player=is_player)


def _move_step(mover, old_x, old_y):
    st = ActionStep("move")
    st.attacker = mover
    st.old_x, st.old_y = old_x, old_y
    st.new_x, st.new_y = mover.grid_x, mover.grid_y
    st.movement_ft = 30
    st.description = f"{mover.name} moves"
    return st


class TestAiMovementProvokesOA(unittest.TestCase):
    def _setup(self, mover_final=(9.0, 5.0)):
        watcher = _mk("Hero", 5, 5, True)           # PC watcher
        mover = _mk("Goblin", 6, 5, False)          # NPC, adjacent to Hero
        bs = BattleState(_FM(), entities=[watcher, mover])
        # Simulate planning already moving the NPC to its destination.
        old_x, old_y = mover.grid_x, mover.grid_y
        mover.grid_x, mover.grid_y = mover_final
        plan = TurnPlan()
        plan.entity = mover
        plan.steps = [_move_step(mover, old_x, old_y)]
        bs.pending_plan = plan
        bs.pending_step_idx = 0
        bs._prepare_step_outcomes()
        return bs, watcher, mover

    def test_move_out_of_reach_triggers_oa(self):
        bs, watcher, mover = self._setup(mover_final=(10.0, 5.0))
        bs._confirm_step()
        self.assertEqual(bs.reaction_type, "oa")
        self.assertIn(watcher, bs.reaction_pending)
        # Mover reverted to origin while the OA is pending.
        self.assertEqual((mover.grid_x, mover.grid_y), (6.0, 5.0))

    def test_oa_deals_damage_and_resumes_turn(self):
        bs, watcher, mover = self._setup(mover_final=(10.0, 5.0))
        bs._confirm_step()
        hp0 = mover.hp
        bs._resolve_reaction(True)          # PC takes the opportunity attack
        self.assertTrue(watcher.reaction_used)
        self.assertLess(mover.hp, hp0, "the OA should deal damage")
        # Move committed to destination and the AI plan advanced/ended.
        self.assertEqual((mover.grid_x, mover.grid_y), (10.0, 5.0))
        self.assertIsNone(bs.pending_plan)

    def test_declined_oa_uses_no_reaction_but_still_moves(self):
        bs, watcher, mover = self._setup(mover_final=(10.0, 5.0))
        bs._confirm_step()
        bs._resolve_reaction(False)         # PC declines
        self.assertFalse(watcher.reaction_used)
        self.assertEqual((mover.grid_x, mover.grid_y), (10.0, 5.0))
        self.assertIsNone(bs.pending_plan)

    def test_staying_in_reach_provokes_nothing(self):
        # Move but remain adjacent (within reach) -> no OA.
        bs, watcher, mover = self._setup(mover_final=(5.0, 6.0))
        bs._confirm_step()
        self.assertNotEqual(bs.reaction_type, "oa")
        self.assertEqual(bs.reaction_pending, [])
        self.assertIsNone(bs.pending_plan)   # plan completed normally


if __name__ == "__main__":
    unittest.main()
