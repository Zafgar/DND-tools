"""Phase 45 — DM dice tray.

Pure-logic tests for the breakdown roller + history. Pygame-skipped
smoke for the widget.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import random
import unittest

from data.dice_tray import (
    DiceTray, DiceRoll, parse_expression, roll_expression,
)


class TestParse(unittest.TestCase):
    def test_simple_ndm(self):
        groups, flat = parse_expression("2d6")
        self.assertEqual(groups, [(2, 6, 1)])
        self.assertEqual(flat, 0)

    def test_ndm_with_modifier(self):
        groups, flat = parse_expression("4d8+3")
        self.assertEqual(groups, [(4, 8, 1)])
        self.assertEqual(flat, 3)

    def test_negative_modifier(self):
        groups, flat = parse_expression("1d20-2")
        self.assertEqual(groups, [(1, 20, 1)])
        self.assertEqual(flat, -2)

    def test_bare_d_means_one(self):
        groups, flat = parse_expression("d20")
        self.assertEqual(groups, [(1, 20, 1)])

    def test_mixed_terms(self):
        groups, flat = parse_expression("3d6+1d4+2")
        self.assertIn((3, 6, 1), groups)
        self.assertIn((1, 4, 1), groups)
        self.assertEqual(flat, 2)

    def test_junk_returns_empty(self):
        self.assertEqual(parse_expression("hello"), ([], 0))

    def test_empty_returns_empty(self):
        self.assertEqual(parse_expression(""), ([], 0))


class TestRoll(unittest.TestCase):
    def setUp(self):
        self.rng = random.Random(1)

    def test_total_within_bounds(self):
        r = roll_expression("2d6+3", rng=self.rng)
        self.assertGreaterEqual(r.total, 2 + 3)
        self.assertLessEqual(r.total, 12 + 3)

    def test_breakdown_shows_individual_dice(self):
        r = roll_expression("3d6", rng=self.rng)
        self.assertEqual(len(r.groups[0].rolls), 3)
        self.assertIn("3d6[", r.breakdown())

    def test_advantage_keeps_higher(self):
        # Force a seed where the two d20 differ
        rng = random.Random(7)
        r = roll_expression("d20", mode="advantage", rng=rng)
        self.assertIsNotNone(r.adv_pair)
        kept, disc = r.adv_pair
        self.assertGreaterEqual(kept, disc)
        self.assertEqual(r.total, kept)  # no modifier

    def test_disadvantage_keeps_lower(self):
        rng = random.Random(7)
        r = roll_expression("d20", mode="disadvantage", rng=rng)
        kept, disc = r.adv_pair
        self.assertLessEqual(kept, disc)

    def test_advantage_only_applies_to_lone_d20(self):
        # 2d6 with advantage mode should ignore the mode
        r = roll_expression("2d6", mode="advantage", rng=self.rng)
        self.assertIsNone(r.adv_pair)

    def test_negative_group(self):
        rng = random.Random(3)
        r = roll_expression("1d8-1d4", rng=rng)
        # Second group is subtractive
        self.assertEqual(r.groups[1].sign, -1)
        expected = r.groups[0].subtotal + r.groups[1].subtotal
        self.assertEqual(r.total, expected)


class TestTrayHistory(unittest.TestCase):
    def test_roll_adds_to_history_front(self):
        tray = DiceTray(rng=random.Random(1))
        tray.roll("d20", label="first")
        tray.roll("d6", label="second")
        self.assertEqual(tray.history[0].label, "second")
        self.assertEqual(tray.history[1].label, "first")

    def test_history_capped(self):
        tray = DiceTray(rng=random.Random(1))
        for _ in range(40):
            tray.roll("d6")
        self.assertEqual(len(tray.history), DiceTray.MAX_HISTORY)

    def test_roll_preset_parses_mode(self):
        tray = DiceTray(rng=random.Random(7))
        r = tray.roll_preset("d20:advantage", label="Stealth")
        self.assertEqual(r.mode, "advantage")
        self.assertIsNotNone(r.adv_pair)
        self.assertEqual(r.label, "Stealth")

    def test_reroll_repeats_last_expression(self):
        tray = DiceTray(rng=random.Random(5))
        tray.roll("2d6+1", label="dmg")
        r2 = tray.reroll_last()
        self.assertEqual(r2.expression, "2d6+1")
        self.assertEqual(r2.label, "dmg")

    def test_reroll_empty_returns_none(self):
        tray = DiceTray()
        self.assertIsNone(tray.reroll_last())

    def test_clear(self):
        tray = DiceTray(rng=random.Random(1))
        tray.roll("d20")
        tray.clear()
        self.assertEqual(tray.history, [])


# --------------------------------------------------------------------- #
try:
    import pygame  # noqa: F401
    HAS_PYGAME = True
except ImportError:
    HAS_PYGAME = False


@unittest.skipUnless(HAS_PYGAME, "pygame not installed")
class TestDiceTrayWidget(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import pygame
        pygame.init()
        pygame.display.set_mode((1600, 900))

    def test_open_roll_draw(self):
        from states.dice_tray_widget import DiceTrayWidget
        import pygame
        w = DiceTrayWidget()
        w.open()
        w.expr = "2d6+3"
        w._roll_expr()
        self.assertEqual(len(w.tray.history), 1)
        w.draw(pygame.display.get_surface())

    def test_toggle(self):
        from states.dice_tray_widget import DiceTrayWidget
        w = DiceTrayWidget()
        self.assertFalse(w.is_open)
        w.toggle()
        self.assertTrue(w.is_open)


if __name__ == "__main__":
    unittest.main()
