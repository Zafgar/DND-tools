"""Phase 7b — travel pace, forced march, and rest mechanics."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest
import random

from data.travel_pace import (
    PACE, NORMAL_TRAVEL_HOURS, LONG_REST_HOURS, ELF_TRANCE_HOURS,
    SHORT_REST_HOURS, EXHAUSTION_EFFECTS,
    PartyMemberPace,
    miles_in_hours, miles_per_day,
    forced_march_dc, forced_march_outcome, simulate_forced_march,
    long_rest_relief, apply_long_rest, short_rest_grants_benefit,
    simulate_travel_day, exhaustion_description,
)


class TestPace(unittest.TestCase):
    def test_normal_pace_3mph(self):
        self.assertEqual(miles_in_hours("normal", 8), 24)
        self.assertEqual(miles_per_day("normal"), 24)

    def test_slow_pace(self):
        self.assertEqual(miles_in_hours("slow", 8), 16)
        self.assertEqual(miles_per_day("slow"), 18)

    def test_fast_pace(self):
        self.assertEqual(miles_in_hours("fast", 8), 32)
        self.assertEqual(miles_per_day("fast"), 30)

    def test_unknown_pace_raises(self):
        with self.assertRaises(ValueError):
            miles_in_hours("hyperspeed", 1)

    def test_zero_hours(self):
        self.assertEqual(miles_in_hours("normal", 0), 0)


class TestForcedMarchDC(unittest.TestCase):
    def test_no_extra_is_dc10(self):
        self.assertEqual(forced_march_dc(0), 10)
        self.assertEqual(forced_march_dc(-3), 10)

    def test_one_extra_is_dc11(self):
        self.assertEqual(forced_march_dc(1), 11)

    def test_four_extra_is_dc14(self):
        self.assertEqual(forced_march_dc(4), 14)


class TestForcedMarchOutcome(unittest.TestCase):
    def test_pass_at_dc(self):
        out = forced_march_outcome(2, con_save_total=12)
        self.assertEqual(out["dc"], 12)
        self.assertTrue(out["succeeded"])
        self.assertEqual(out["exhaustion_gained"], 0)

    def test_fail_below_dc(self):
        out = forced_march_outcome(2, con_save_total=11)
        self.assertFalse(out["succeeded"])
        self.assertEqual(out["exhaustion_gained"], 1)


class TestSimulateForcedMarch(unittest.TestCase):
    def test_high_modifier_always_passes(self):
        rng = random.Random(0)
        for _ in range(40):
            out = simulate_forced_march(2, con_modifier=20, rng=rng)
            self.assertTrue(out["succeeded"])

    def test_low_modifier_often_fails(self):
        rng = random.Random(1)
        fails = sum(1 for _ in range(200)
                    if not simulate_forced_march(8, con_modifier=-5, rng=rng)["succeeded"])
        self.assertGreater(fails, 100)

    def test_advantage_helps(self):
        rng_a = random.Random(42)
        rng_b = random.Random(42)
        n_pass_no_adv = sum(
            1 for _ in range(200)
            if simulate_forced_march(4, con_modifier=0, rng=rng_a)["succeeded"]
        )
        rng_b = random.Random(42)
        n_pass_adv = sum(
            1 for _ in range(200)
            if simulate_forced_march(4, con_modifier=0, advantage=True,
                                       rng=rng_b)["succeeded"]
        )
        self.assertGreater(n_pass_adv, n_pass_no_adv)

    def test_advantage_and_disadvantage_cancel(self):
        # No exception, behaves like a flat roll
        rng = random.Random(7)
        for _ in range(20):
            simulate_forced_march(2, 0, advantage=True, disadvantage=True,
                                    rng=rng)


class TestLongRest(unittest.TestCase):
    def test_full_rest_clears_one_level(self):
        pc = PartyMemberPace("A", exhaustion=3)
        self.assertEqual(apply_long_rest(pc, hours_slept=8), 1)
        self.assertEqual(pc.exhaustion, 2)

    def test_short_rest_no_relief(self):
        pc = PartyMemberPace("A", exhaustion=3)
        self.assertEqual(apply_long_rest(pc, hours_slept=4), 0)
        self.assertEqual(pc.exhaustion, 3)

    def test_no_exhaustion_means_no_relief(self):
        pc = PartyMemberPace("A", exhaustion=0)
        self.assertEqual(apply_long_rest(pc, 8), 0)

    def test_elf_trance_4h_counts(self):
        pc = PartyMemberPace("Elara", exhaustion=2, is_elf_trance=True)
        self.assertEqual(apply_long_rest(pc, hours_slept=4), 1)

    def test_human_4h_does_not_count(self):
        pc = PartyMemberPace("Bran", exhaustion=2, is_elf_trance=False)
        self.assertEqual(apply_long_rest(pc, hours_slept=4), 0)

    def test_short_rest_threshold(self):
        self.assertFalse(short_rest_grants_benefit(0.5))
        self.assertTrue(short_rest_grants_benefit(1.0))
        self.assertTrue(short_rest_grants_benefit(2.0))


class TestSimulateTravelDay(unittest.TestCase):
    def test_normal_8h_no_saves(self):
        party = [PartyMemberPace("A"), PartyMemberPace("B")]
        rep = simulate_travel_day(party, hours_walked=8)
        self.assertEqual(rep["extra_hours"], 0)
        self.assertIsNone(rep["dc"])
        self.assertEqual(rep["miles_travelled"], 24)
        self.assertEqual(party[0].exhaustion, 0)

    def test_extra_hours_accrue_exhaustion(self):
        party = [PartyMemberPace("A", con_modifier=-5)]
        rng = random.Random(11)
        rep = simulate_travel_day(party, hours_walked=12, rng=rng)
        self.assertEqual(rep["extra_hours"], 4)
        self.assertEqual(rep["dc"], 14)
        # Most likely the -5 character failed at DC 14
        self.assertGreaterEqual(party[0].exhaustion, 0)

    def test_pace_affects_distance(self):
        party = [PartyMemberPace("A")]
        slow = simulate_travel_day(party, pace="slow", hours_walked=8)
        fast = simulate_travel_day(party, pace="fast", hours_walked=8)
        self.assertEqual(slow["miles_travelled"], 16)
        self.assertEqual(fast["miles_travelled"], 32)

    def test_exhaustion_caps_at_6_and_logs_death(self):
        party = [PartyMemberPace("A", con_modifier=-20, exhaustion=5)]
        rng = random.Random(0)
        rep = simulate_travel_day(party, hours_walked=12, rng=rng)
        # Massive negative mod + extra hours → certain failure
        self.assertEqual(party[0].exhaustion, 6)
        self.assertIn("A", rep["deaths"])

    def test_unknown_pace_falls_back_to_normal(self):
        party = [PartyMemberPace("A")]
        rep = simulate_travel_day(party, pace="hyperspeed", hours_walked=8)
        self.assertEqual(rep["pace"], "normal")


class TestExhaustionDescription(unittest.TestCase):
    def test_levels_0_to_6(self):
        self.assertEqual(exhaustion_description(0), "None")
        self.assertEqual(exhaustion_description(6), "Death")
        for lvl in range(7):
            self.assertEqual(
                exhaustion_description(lvl), EXHAUSTION_EFFECTS[lvl]
            )

    def test_clamps_out_of_range(self):
        self.assertEqual(exhaustion_description(-1), "None")
        self.assertEqual(exhaustion_description(99), "Death")


if __name__ == "__main__":
    unittest.main()
