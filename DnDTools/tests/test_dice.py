"""Tests for engine/dice.py – D&D dice rolling and calculation."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest
import random
from engine.dice import roll_dice, roll_dice_critical, roll_d20, roll_attack, scale_cantrip_dice, average_damage


class TestRollDice(unittest.TestCase):
    def test_basic_roll(self):
        random.seed(42)
        result = roll_dice("1d6")
        self.assertGreaterEqual(result, 1)
        self.assertLessEqual(result, 6)

    def test_multiple_dice(self):
        random.seed(42)
        result = roll_dice("3d6")
        self.assertGreaterEqual(result, 3)
        self.assertLessEqual(result, 18)

    def test_modifier_positive(self):
        random.seed(42)
        result = roll_dice("1d6+3")
        self.assertGreaterEqual(result, 4)

    def test_modifier_negative(self):
        # Minimum is 0 due to max(0, total)
        result = roll_dice("1d4-10")
        self.assertEqual(result, 0)

    def test_flat_number(self):
        self.assertEqual(roll_dice("5"), 5)

    def test_empty_string(self):
        self.assertEqual(roll_dice(""), 0)

    def test_invalid_string(self):
        self.assertEqual(roll_dice("abc"), 0)

    def test_statistical_distribution(self):
        """1d6 average should be ~3.5 over many rolls."""
        random.seed(0)
        total = sum(roll_dice("1d6") for _ in range(10000))
        avg = total / 10000
        self.assertAlmostEqual(avg, 3.5, delta=0.2)


class TestRollDiceCritical(unittest.TestCase):
    def test_critical_doubles_dice(self):
        """Critical should roll double the number of dice."""
        random.seed(42)
        # Normal 2d6 range: 2-12
        # Critical 2d6 range: 4-24 (rolls 4d6)
        results = [roll_dice_critical("2d6") for _ in range(100)]
        self.assertTrue(any(r > 12 for r in results))

    def test_critical_with_modifier(self):
        random.seed(42)
        result = roll_dice_critical("1d8+5")
        self.assertGreaterEqual(result, 7)  # min: 2+5

    def test_critical_flat_number(self):
        self.assertEqual(roll_dice_critical("10"), 10)


class TestRollD20(unittest.TestCase):
    def test_normal_roll(self):
        random.seed(42)
        result, desc = roll_d20()
        self.assertGreaterEqual(result, 1)
        self.assertLessEqual(result, 20)

    def test_advantage(self):
        random.seed(42)
        result, desc = roll_d20(advantage=True)
        self.assertIn("Adv", desc)

    def test_disadvantage(self):
        random.seed(42)
        result, desc = roll_d20(disadvantage=True)
        self.assertIn("Dis", desc)

    def test_advantage_and_disadvantage_cancel(self):
        random.seed(42)
        result, desc = roll_d20(advantage=True, disadvantage=True)
        # Should be a straight roll
        self.assertNotIn("Adv", desc)
        self.assertNotIn("Dis", desc)

    def test_advantage_takes_higher(self):
        random.seed(0)
        results = [roll_d20(advantage=True)[0] for _ in range(10000)]
        avg = sum(results) / len(results)
        # Average with advantage should be ~13.8 (higher than 10.5 normal)
        self.assertGreater(avg, 12.0)

    def test_disadvantage_takes_lower(self):
        random.seed(0)
        results = [roll_d20(disadvantage=True)[0] for _ in range(10000)]
        avg = sum(results) / len(results)
        # Average with disadvantage should be ~7.2 (lower than 10.5 normal)
        self.assertLess(avg, 9.0)


class TestRollAttack(unittest.TestCase):
    def test_attack_roll(self):
        random.seed(42)
        total, nat, is_crit, is_fumble, roll_str = roll_attack(5)
        self.assertEqual(total, nat + 5)

    def test_critical_hit(self):
        # Force a nat 20
        random.seed(0)
        found_crit = False
        for _ in range(1000):
            _, nat, is_crit, _, _ = roll_attack(0)
            if nat == 20:
                self.assertTrue(is_crit)
                found_crit = True
                break
        self.assertTrue(found_crit, "Should find at least one crit in 1000 rolls")

    def test_fumble(self):
        random.seed(0)
        found_fumble = False
        for _ in range(1000):
            _, nat, _, is_fumble, _ = roll_attack(0)
            if nat == 1:
                self.assertTrue(is_fumble)
                found_fumble = True
                break
        self.assertTrue(found_fumble, "Should find at least one fumble in 1000 rolls")


class TestScaleCantrip(unittest.TestCase):
    def test_level_1(self):
        self.assertEqual(scale_cantrip_dice("1d10", 1), "1d10")

    def test_level_5(self):
        self.assertEqual(scale_cantrip_dice("1d10", 5), "2d10")

    def test_level_11(self):
        self.assertEqual(scale_cantrip_dice("1d10", 11), "3d10")

    def test_level_17(self):
        self.assertEqual(scale_cantrip_dice("1d10", 17), "4d10")

    def test_with_modifier(self):
        self.assertEqual(scale_cantrip_dice("1d8+3", 5), "2d8+3")

    def test_multi_dice_not_scaled(self):
        # 2d6 base dice shouldn't be scaled (not standard cantrip)
        self.assertEqual(scale_cantrip_dice("2d6", 5), "2d6")

    def test_empty(self):
        self.assertEqual(scale_cantrip_dice("", 5), "")


class TestAverageDamage(unittest.TestCase):
    def test_1d6(self):
        self.assertAlmostEqual(average_damage("1d6"), 3.5)

    def test_2d6(self):
        self.assertAlmostEqual(average_damage("2d6"), 7.0)

    def test_1d8_plus_3(self):
        self.assertAlmostEqual(average_damage("1d8+3"), 7.5)

    def test_flat_number(self):
        self.assertAlmostEqual(average_damage("5"), 5.0)

    def test_empty(self):
        self.assertAlmostEqual(average_damage(""), 0.0)

    def test_8d6(self):
        # Fireball: 8d6 = 28 average
        self.assertAlmostEqual(average_damage("8d6"), 28.0)


if __name__ == "__main__":
    unittest.main()
