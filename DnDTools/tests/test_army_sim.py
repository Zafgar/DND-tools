"""Tests for the abstract army_sim module."""
import random
import unittest
from dataclasses import dataclass, field
from typing import List

from data.army_sim import (
    Army, UnitStack, SimulationResult, MonteCarloResult,
    hit_chance, _parse_damage_dice, unit_from_stats,
    army_from_map_object, simulate, monte_carlo,
)


@dataclass
class FakeAction:
    damage_dice: str = ""
    damage_bonus: int = 0
    attack_bonus: int = 0


@dataclass
class FakeStats:
    name: str = "Goblin"
    hit_points: int = 7
    armor_class: int = 13
    speed: int = 30
    challenge_rating: float = 0.25
    actions: List[FakeAction] = field(default_factory=list)


@dataclass
class FakeMapObj:
    unit_type: str = ""
    unit_count: int = 0
    faction: str = ""


class FakeLibrary:
    def __init__(self, stats):
        self._stats = stats

    def get_monster(self, name):
        if name == self._stats.name:
            return self._stats
        raise KeyError(name)


# ----------------------------------------------------------------------
class TestUnitStack(unittest.TestCase):
    def test_total_hp_and_dpr(self):
        s = UnitStack(count=5, hp_each=8, dpr_each=3.0)
        self.assertEqual(s.total_hp, 40)
        self.assertEqual(s.total_dpr, 15.0)

    def test_apply_casualties_kills_whole_models(self):
        s = UnitStack(count=5, hp_each=8)
        killed = s.apply_casualties(20)  # 20/8 = 2 killed, 4 remainder ignored
        self.assertEqual(killed, 2)
        self.assertEqual(s.count, 3)

    def test_apply_casualties_cannot_go_below_zero(self):
        s = UnitStack(count=2, hp_each=5)
        killed = s.apply_casualties(999)
        self.assertEqual(killed, 2)
        self.assertEqual(s.count, 0)

    def test_apply_casualties_zero_damage(self):
        s = UnitStack(count=3, hp_each=8)
        self.assertEqual(s.apply_casualties(0), 0)
        self.assertEqual(s.apply_casualties(-5), 0)
        self.assertEqual(s.count, 3)


class TestArmy(unittest.TestCase):
    def test_totals_sum_across_stacks(self):
        a = Army(stacks=[
            UnitStack(count=3, hp_each=10, dpr_each=2.0, ac=12),
            UnitStack(count=2, hp_each=5, dpr_each=4.0, ac=16),
        ])
        self.assertEqual(a.total_hp, 40)
        self.assertEqual(a.total_dpr, 14.0)
        self.assertEqual(a.total_count, 5)
        # Weighted AC = (12*3 + 16*2) / 5 = 13.6
        self.assertAlmostEqual(a.mean_ac, 13.6, places=4)

    def test_is_broken_when_no_models(self):
        a = Army(stacks=[UnitStack(count=0)])
        self.assertTrue(a.is_broken())

    def test_mean_ac_default_when_empty(self):
        a = Army(stacks=[])
        self.assertEqual(a.mean_ac, 12.0)


class TestHitChance(unittest.TestCase):
    def test_clamps_upper(self):
        # Huge to-hit vs tiny AC: should clamp to 0.95
        self.assertEqual(hit_chance(to_hit=30, target_ac=10), 0.95)

    def test_clamps_lower(self):
        # Tiny to-hit vs huge AC: should clamp to 0.05
        self.assertEqual(hit_chance(to_hit=-10, target_ac=25), 0.05)

    def test_mid_range(self):
        # +5 vs AC 15: need 10, chance = 11/20 = 0.55
        self.assertAlmostEqual(hit_chance(5, 15), 0.55, places=4)


class TestParseDamageDice(unittest.TestCase):
    def test_basic_dice(self):
        # 1d8 = 4.5
        self.assertAlmostEqual(_parse_damage_dice("1d8"), 4.5, places=4)

    def test_dice_plus_bonus(self):
        # 2d6 = 7, +3 = 10
        self.assertAlmostEqual(_parse_damage_dice("2d6+3"), 10.0, places=4)

    def test_empty_expression(self):
        self.assertEqual(_parse_damage_dice(""), 0.0)
        self.assertEqual(_parse_damage_dice(None or ""), 0.0)


class TestUnitFromStats(unittest.TestCase):
    def test_pulls_action_damage(self):
        stats = FakeStats(actions=[FakeAction(
            damage_dice="1d6", damage_bonus=2, attack_bonus=4
        )])
        stack = unit_from_stats(stats, count=10)
        self.assertEqual(stack.count, 10)
        self.assertEqual(stack.hp_each, 7)
        self.assertEqual(stack.ac, 13)
        self.assertAlmostEqual(stack.dpr_each, 5.5, places=4)  # 3.5 + 2
        self.assertEqual(stack.to_hit, 4)

    def test_falls_back_to_cr_dpr(self):
        stats = FakeStats(challenge_rating=2, actions=[])
        stack = unit_from_stats(stats, count=1)
        # dpr ≈ 2 + 2*4 = 10
        self.assertGreaterEqual(stack.dpr_each, 1.0)

    def test_count_floor_one(self):
        stack = unit_from_stats(FakeStats(), count=0)
        self.assertEqual(stack.count, 1)


class TestArmyFromMapObject(unittest.TestCase):
    def test_returns_none_for_blank_unit(self):
        obj = FakeMapObj(unit_type="", unit_count=5)
        self.assertIsNone(army_from_map_object(obj, library=FakeLibrary(FakeStats())))

    def test_returns_none_for_zero_count(self):
        obj = FakeMapObj(unit_type="Goblin", unit_count=0)
        self.assertIsNone(army_from_map_object(obj, library=FakeLibrary(FakeStats())))

    def test_builds_army_with_faction_name(self):
        obj = FakeMapObj(unit_type="Goblin", unit_count=40, faction="Oblitus")
        army = army_from_map_object(obj, library=FakeLibrary(FakeStats()))
        self.assertIsNotNone(army)
        self.assertEqual(army.name, "Oblitus")
        self.assertEqual(len(army.stacks), 1)
        self.assertEqual(army.stacks[0].count, 40)

    def test_count_override(self):
        obj = FakeMapObj(unit_type="Goblin", unit_count=40)
        army = army_from_map_object(obj, count_override=5,
                                     library=FakeLibrary(FakeStats()))
        self.assertEqual(army.stacks[0].count, 5)

    def test_unresolved_monster_returns_none(self):
        obj = FakeMapObj(unit_type="Unknown", unit_count=10)
        self.assertIsNone(army_from_map_object(obj, library=FakeLibrary(FakeStats())))


class TestSimulate(unittest.TestCase):
    def _army(self, name, count, hp=8, dpr=3.0, ac=12, to_hit=3):
        return Army(name=name, stacks=[
            UnitStack(name=name, count=count, hp_each=hp,
                      ac=ac, to_hit=to_hit, dpr_each=dpr)
        ])

    def test_stronger_army_wins(self):
        strong = self._army("A", count=40, dpr=6.0)
        weak = self._army("B", count=8, dpr=1.0)
        res = simulate(strong, weak, max_rounds=60,
                       rng=random.Random(1))
        self.assertEqual(res.winner, "a")
        self.assertTrue(weak.is_broken())
        self.assertGreater(res.casualties_b, 0)

    def test_matched_armies_produce_result(self):
        a = self._army("A", count=20)
        b = self._army("B", count=20)
        res = simulate(a, b, max_rounds=60, rng=random.Random(0))
        self.assertIn(res.winner, ("a", "b", "draw"))
        self.assertGreaterEqual(res.rounds, 1)

    def test_casualties_are_non_negative(self):
        a = self._army("A", count=5)
        b = self._army("B", count=5)
        res = simulate(a, b, rng=random.Random(0))
        self.assertGreaterEqual(res.casualties_a, 0)
        self.assertGreaterEqual(res.casualties_b, 0)


class TestMonteCarlo(unittest.TestCase):
    def test_trials_count(self):
        a = Army(stacks=[UnitStack(count=10, hp_each=8, dpr_each=4.0)])
        b = Army(stacks=[UnitStack(count=10, hp_each=8, dpr_each=4.0)])
        res = monte_carlo(a, b, trials=7, rng=random.Random(42))
        self.assertEqual(res.trials, 7)
        self.assertEqual(res.a_wins + res.b_wins + res.draws, 7)

    def test_does_not_mutate_inputs(self):
        a = Army(stacks=[UnitStack(count=10, hp_each=8, dpr_each=4.0)])
        b = Army(stacks=[UnitStack(count=10, hp_each=8, dpr_each=4.0)])
        start_a, start_b = a.total_count, b.total_count
        monte_carlo(a, b, trials=3, rng=random.Random(0))
        # inputs should be deep-copied per trial; originals intact
        self.assertEqual(a.total_count, start_a)
        self.assertEqual(b.total_count, start_b)

    def test_win_rate_properties(self):
        res = MonteCarloResult(trials=10, a_wins=7, b_wins=2, draws=1,
                                mean_rounds=3.0, mean_cas_a=1.0, mean_cas_b=5.0)
        self.assertAlmostEqual(res.win_rate_a, 0.7)
        self.assertAlmostEqual(res.win_rate_b, 0.2)

    def test_overwhelming_side_wins_most(self):
        strong = Army(stacks=[UnitStack(count=50, hp_each=10, dpr_each=8.0,
                                          ac=16, to_hit=6)])
        weak = Army(stacks=[UnitStack(count=5, hp_each=6, dpr_each=1.0,
                                        ac=10, to_hit=1)])
        res = monte_carlo(strong, weak, trials=20, rng=random.Random(7))
        self.assertGreater(res.a_wins, res.b_wins)


if __name__ == "__main__":
    unittest.main()
