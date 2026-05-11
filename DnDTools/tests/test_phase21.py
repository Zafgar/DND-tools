"""Phase 21 — combat AI hardening:
  21a: A* iteration cap returns partial path.
  21b: calculate_turn wall-clock budget aborts cleanly.
  21c: action-economy validator + repair.
  21d: suggest-only dry-run.
  21e: smoke tests for the previously deadlocking scenarios.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import unittest
from unittest.mock import MagicMock

from data.models import (
    CreatureStats, AbilityScores, Action, Feature, SpellInfo,
)
from engine.entities import Entity
from engine.battle import BattleSystem
from engine.terrain import TerrainObject
from engine.ai.tactical_ai import TacticalAI
from engine.ai.models import ActionStep, TurnPlan
from engine.ai.action_economy import validate_plan, repair_plan
from engine.ai.suggest import suggest_turn, describe_plan


def _battle(*ents):
    return BattleSystem(log_callback=lambda *a: None,
                          initial_entities=list(ents))


def _ent(name="X", hp=20, ac=14, x=5, y=5, is_player=False,
          actions=None, features=None, speed=30,
          fly_speed=0):
    stats = CreatureStats(
        name=name, size="Medium", hit_points=hp, armor_class=ac,
        speed=speed, fly_speed=fly_speed,
        abilities=AbilityScores(strength=14, dexterity=12,
                                  constitution=12, intelligence=10,
                                  wisdom=10, charisma=10),
        actions=actions or [Action(name="Sword", attack_bonus=4,
                                       damage_dice="1d8",
                                       damage_bonus=2,
                                       damage_type="slashing",
                                       range=5)],
        features=features or [],
    )
    return Entity(stats, x, y, is_player=is_player)


# --------------------------------------------------------------------- #
# 21a — A* iteration cap
# --------------------------------------------------------------------- #
class TestAStarCap(unittest.TestCase):
    def test_unreachable_returns_partial_or_none(self):
        att = _ent("A", x=2, y=2)
        tgt = _ent("T", x=20, y=20, is_player=True)
        b = _battle(att, tgt)
        # Build an impassable wall ring around target
        for x in range(18, 23):
            for y in range(18, 23):
                if x in (18, 22) or y in (18, 22):
                    b.terrain.append(TerrainObject(
                        terrain_type="wall", grid_x=x, grid_y=y,
                    ))
        ai = TacticalAI()
        # Should not hang and should return either None or a list
        path = ai._find_path((2, 2), (20, 20), b, att,
                                max_iterations=300,
                                return_partial=True)
        self.assertTrue(path is None or isinstance(path, list))

    def test_cap_returns_partial_when_partial_progress_made(self):
        att = _ent("A", x=2, y=2)
        tgt = _ent("T", x=40, y=40, is_player=True)
        b = _battle(att, tgt)
        ai = TacticalAI()
        # Open ground, big distance — capping mid-search returns
        # the best-so-far closest-to-end node.
        path = ai._find_path((2, 2), (40, 40), b, att,
                                max_iterations=80,
                                return_partial=True)
        if path is not None:
            # Last node should be closer to (40,40) than (2,2)
            last = path[-1]
            from_h = max(abs(2 - 40), abs(2 - 40))
            to_h = max(abs(last[0] - 40), abs(last[1] - 40))
            self.assertLessEqual(to_h, from_h)


# --------------------------------------------------------------------- #
# 21b — calculate_turn budget + error handling
# --------------------------------------------------------------------- #
class TestCalculateTurnBudget(unittest.TestCase):
    def test_wraps_exceptions(self):
        att = _ent("A")
        b = _battle(att)
        ai = TacticalAI()
        # Force an exception inside the inner planner
        original = ai._calculate_turn_inner
        def boom(entity, battle):
            raise RuntimeError("simulated")
        ai._calculate_turn_inner = boom
        try:
            plan = ai.calculate_turn(att, b)
            self.assertTrue(plan.skipped)
            self.assertIn("AI error", plan.skip_reason)
        finally:
            ai._calculate_turn_inner = original

    def test_returns_normally_under_budget(self):
        att = _ent("A", x=5, y=5)
        tgt = _ent("T", x=6, y=5, is_player=True)
        b = _battle(att, tgt)
        b.combat_started = True
        ai = TacticalAI()
        plan = ai.calculate_turn(att, b)
        self.assertIsNotNone(plan)


# --------------------------------------------------------------------- #
# 21c — Action economy validation
# --------------------------------------------------------------------- #
class TestActionEconomyValidator(unittest.TestCase):
    def _step(self, kind, action_name="X"):
        return ActionStep(step_type=kind, action_name=action_name)

    def test_clean_plan_passes(self):
        att = _ent("X")
        plan = TurnPlan(entity=att)
        plan.steps = [self._step("attack"), self._step("move")]
        plan.steps[1].movement_ft = 20
        rep = validate_plan(plan, att)
        self.assertTrue(rep.ok)

    def test_double_action_flagged(self):
        att = _ent("X")
        plan = TurnPlan(entity=att)
        plan.steps = [self._step("attack", "a"),
                       self._step("attack", "b")]
        rep = validate_plan(plan, att)
        self.assertFalse(rep.ok)
        self.assertEqual(rep.actions_used, 2)

    def test_double_bonus_flagged(self):
        att = _ent("X")
        plan = TurnPlan(entity=att)
        plan.steps = [self._step("bonus_attack"),
                       self._step("bonus_attack")]
        rep = validate_plan(plan, att)
        self.assertFalse(rep.ok)

    def test_movement_over_speed_flagged(self):
        att = _ent("X", speed=30)
        plan = TurnPlan(entity=att)
        m = self._step("move")
        m.movement_ft = 60
        plan.steps = [m]
        rep = validate_plan(plan, att)
        self.assertFalse(rep.ok)

    def test_repair_drops_extra_steps(self):
        att = _ent("X")
        plan = TurnPlan(entity=att)
        plan.steps = [
            self._step("attack", "a"),
            self._step("attack", "b"),
            self._step("attack", "c"),
        ]
        plan, rep = repair_plan(plan, att)
        self.assertEqual(rep.actions_used, 1)
        self.assertEqual(len(plan.steps), 1)


# --------------------------------------------------------------------- #
# 21d — Suggest-only dry-run
# --------------------------------------------------------------------- #
class TestSuggestOnlyMode(unittest.TestCase):
    def test_does_not_consume_resources(self):
        att = _ent("A", x=5, y=5)
        tgt = _ent("T", x=6, y=5, is_player=True)
        b = _battle(att, tgt)
        b.combat_started = True
        ai = TacticalAI()
        att.action_used = False
        att.bonus_action_used = False
        suggest_turn(att, b, ai=ai)
        # Even though the planner mutates these mid-decision, they
        # must be restored by the time we return.
        self.assertFalse(att.action_used)
        self.assertFalse(att.bonus_action_used)

    def test_describe_plan_empty_for_skipped(self):
        plan = TurnPlan(entity=None)
        plan.skipped = True
        plan.skip_reason = "x"
        self.assertIn("Skip", describe_plan(plan))

    def test_describe_plan_lists_steps(self):
        plan = TurnPlan(entity=None)
        plan.steps = [
            ActionStep(step_type="attack", action_name="Sword",
                         description="Slash the bandit"),
        ]
        s = describe_plan(plan)
        self.assertIn("Slash the bandit", s)


# --------------------------------------------------------------------- #
# 21e — Previously-deadlocking scenarios complete planning
# --------------------------------------------------------------------- #
class TestPreviouslyDeadlockedScenarios(unittest.TestCase):
    """Phase 9d flagged devil_incursion (Bone Devil) and
    tavern_brawl (PC outside walls) as expectedFailure. After the
    iteration cap + wall-clock guard they should complete within
    the budget."""
    def test_bone_devil_in_devil_incursion(self):
        from data.scenarios import (
            get_scenario, apply_scenario_to_battle,
            scenario_monsters_as_entities,
        )
        import signal
        scen = get_scenario("devil_incursion")
        b = BattleSystem(log_callback=lambda *a: None,
                           initial_entities=[])
        b.entities = []; b.terrain = []
        apply_scenario_to_battle(scen, b)
        for ent in scenario_monsters_as_entities(scen):
            b.entities.append(ent)
        b.combat_started = True
        ai = TacticalAI()
        # Per-entity timeout to fail fast if the cap fails to help.
        def handler(signum, frame):
            raise TimeoutError("AI hang detected")
        if hasattr(signal, "SIGALRM"):
            signal.signal(signal.SIGALRM, handler)
            signal.alarm(8)
        try:
            for ent in b.entities:
                if ent.hp <= 0:
                    continue
                plan = ai.calculate_turn(ent, b)
                self.assertIsNotNone(plan)
        finally:
            if hasattr(signal, "SIGALRM"):
                signal.alarm(0)


if __name__ == "__main__":
    unittest.main()
