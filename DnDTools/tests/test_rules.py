"""Tests for engine/rules.py – D&D 5e 2014 rules engine."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import unittest
import random
from data.models import CreatureStats, AbilityScores, Action, Feature
from engine.entities import Entity
from engine.rules import (
    get_size_rank, size_difference, can_grapple, can_shove,
    resolve_grapple, resolve_shove, get_grapple_drag_speed_multiplier,
)


def _make_entity(name="Test", size="Medium", strength=10, dexterity=10,
                 hp=20, ac=10, **kwargs):
    stats = CreatureStats(
        name=name, size=size, hit_points=hp, armor_class=ac,
        abilities=AbilityScores(strength=strength, dexterity=dexterity),
        **kwargs,
    )
    return Entity(stats, 5, 5, is_player=True)


class TestSizeRank(unittest.TestCase):
    def test_known_sizes(self):
        self.assertEqual(get_size_rank("Tiny"), 0)
        self.assertEqual(get_size_rank("Small"), 1)
        self.assertEqual(get_size_rank("Medium"), 2)
        self.assertEqual(get_size_rank("Large"), 3)
        self.assertEqual(get_size_rank("Huge"), 4)
        self.assertEqual(get_size_rank("Gargantuan"), 5)

    def test_case_insensitive(self):
        self.assertEqual(get_size_rank("medium"), 2)
        self.assertEqual(get_size_rank("LARGE"), 3)

    def test_unknown_defaults_to_medium(self):
        self.assertEqual(get_size_rank("Unknown"), 2)


class TestSizeDifference(unittest.TestCase):
    def test_same_size(self):
        a = _make_entity("A", size="Medium")
        b = _make_entity("B", size="Medium")
        self.assertEqual(size_difference(a, b), 0)

    def test_larger(self):
        a = _make_entity("A", size="Large")
        b = _make_entity("B", size="Medium")
        self.assertEqual(size_difference(a, b), 1)

    def test_smaller(self):
        a = _make_entity("A", size="Small")
        b = _make_entity("B", size="Large")
        self.assertEqual(size_difference(a, b), -2)


class TestGrapple(unittest.TestCase):
    def test_can_grapple_same_size(self):
        a = _make_entity("Fighter", strength=16)
        b = _make_entity("Goblin", strength=8)
        allowed, reason = can_grapple(a, b)
        self.assertTrue(allowed)

    def test_cannot_grapple_too_large(self):
        a = _make_entity("Fighter", size="Medium")
        b = _make_entity("Dragon", size="Gargantuan")
        allowed, reason = can_grapple(a, b)
        self.assertFalse(allowed)
        self.assertIn("too large", reason)

    def test_can_grapple_one_size_larger(self):
        a = _make_entity("Fighter", size="Medium")
        b = _make_entity("Ogre", size="Large")
        allowed, reason = can_grapple(a, b)
        self.assertTrue(allowed)

    def test_incapacitated_cannot_grapple(self):
        a = _make_entity("Fighter")
        a.add_condition("Incapacitated")
        b = _make_entity("Goblin")
        allowed, reason = can_grapple(a, b)
        self.assertFalse(allowed)

    def test_grapple_resolves(self):
        random.seed(42)
        a = _make_entity("Fighter", strength=20, skills={"Athletics": 8})
        b = _make_entity("Goblin", strength=8)
        success, msg = resolve_grapple(a, b)
        self.assertIsInstance(success, bool)
        self.assertIn("grapple", msg.lower())


class TestShove(unittest.TestCase):
    def test_can_shove_same_size(self):
        a = _make_entity("Fighter")
        b = _make_entity("Goblin")
        allowed, reason = can_shove(a, b)
        self.assertTrue(allowed)

    def test_cannot_shove_too_large(self):
        a = _make_entity("Fighter", size="Medium")
        b = _make_entity("Dragon", size="Gargantuan")
        allowed, reason = can_shove(a, b)
        self.assertFalse(allowed)

    def test_shove_resolves(self):
        random.seed(42)
        a = _make_entity("Fighter", strength=18, skills={"Athletics": 7})
        b = _make_entity("Goblin", strength=8)
        success, msg = resolve_shove(a, b, prone=True)
        self.assertIsInstance(success, bool)


class TestGrappleDragSpeed(unittest.TestCase):
    def test_same_size_halved(self):
        a = _make_entity("Fighter", size="Medium")
        b = _make_entity("Goblin", size="Medium")
        self.assertEqual(get_grapple_drag_speed_multiplier(a, b), 0.5)

    def test_two_sizes_smaller_no_penalty(self):
        a = _make_entity("Giant", size="Huge")
        b = _make_entity("Goblin", size="Small")
        self.assertEqual(get_grapple_drag_speed_multiplier(a, b), 1.0)


if __name__ == "__main__":
    unittest.main()
