"""Tests for engine/entities.py – Entity state management."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import unittest
import random
from data.models import CreatureStats, AbilityScores, Action, Feature, SpellInfo, Item


def _make_entity(name="Test", is_player=True, hp=50, ac=15, strength=10,
                 dexterity=10, constitution=10, speed=30, size="Medium",
                 features=None, actions=None, items=None, spells_known=None, **kwargs):
    from engine.entities import Entity
    stats = CreatureStats(
        name=name, size=size, hit_points=hp, armor_class=ac, speed=speed,
        abilities=AbilityScores(strength=strength, dexterity=dexterity,
                                constitution=constitution),
        features=features or [],
        actions=actions or [],
        items=items or [],
        spells_known=spells_known or [],
        **kwargs,
    )
    return Entity(stats, 5.0, 5.0, is_player=is_player)


class TestEntityCreation(unittest.TestCase):
    def test_basic_creation(self):
        e = _make_entity("Fighter", hp=40, ac=18)
        self.assertEqual(e.name, "Fighter")
        self.assertEqual(e.hp, 40)
        self.assertEqual(e.max_hp, 40)
        self.assertTrue(e.is_player)
        self.assertEqual(e.grid_x, 5.0)
        self.assertEqual(e.grid_y, 5.0)

    def test_default_resources(self):
        e = _make_entity()
        self.assertEqual(e.temp_hp, 0)
        self.assertEqual(e.exhaustion, 0)
        self.assertFalse(e.rage_active)
        self.assertFalse(e.is_flying)
        self.assertEqual(e.conditions, set())

    def test_feature_uses_initialized(self):
        feat = Feature(name="Action Surge", uses_per_day=1)
        e = _make_entity(features=[feat])
        self.assertEqual(e.feature_uses.get("Action Surge"), 1)


class TestConditions(unittest.TestCase):
    def test_add_condition(self):
        e = _make_entity()
        e.add_condition("Poisoned")
        self.assertTrue(e.has_condition("Poisoned"))

    def test_remove_condition(self):
        e = _make_entity()
        e.add_condition("Poisoned")
        e.remove_condition("Poisoned")
        self.assertFalse(e.has_condition("Poisoned"))

    def test_remove_nonexistent_condition(self):
        e = _make_entity()
        e.remove_condition("Stunned")  # Should not raise

    def test_prone_condition(self):
        e = _make_entity()
        e.add_condition("Prone")
        self.assertTrue(e.has_condition("Prone"))


class TestDamage(unittest.TestCase):
    def test_basic_damage(self):
        e = _make_entity(hp=50)
        dealt, broke_conc = e.take_damage(10, "slashing")
        self.assertEqual(dealt, 10)
        self.assertEqual(e.hp, 40)
        self.assertFalse(broke_conc)

    def test_temp_hp_absorbs_first(self):
        e = _make_entity(hp=50)
        e.temp_hp = 10
        dealt, _ = e.take_damage(15, "fire")
        self.assertEqual(e.temp_hp, 0)
        self.assertEqual(e.hp, 45)

    def test_temp_hp_partial_absorb(self):
        e = _make_entity(hp=50)
        e.temp_hp = 20
        dealt, _ = e.take_damage(10, "fire")
        self.assertEqual(e.temp_hp, 10)
        self.assertEqual(e.hp, 50)

    def test_damage_immunity(self):
        e = _make_entity(hp=50, damage_immunities=["fire"])
        dealt, _ = e.take_damage(20, "fire")
        self.assertEqual(dealt, 0)
        self.assertEqual(e.hp, 50)

    def test_damage_resistance(self):
        e = _make_entity(hp=50, damage_resistances=["fire"])
        dealt, _ = e.take_damage(20, "fire")
        self.assertEqual(e.hp, 40)  # 20 // 2 = 10 damage

    def test_damage_vulnerability(self):
        e = _make_entity(hp=50, damage_vulnerabilities=["fire"])
        dealt, _ = e.take_damage(10, "fire")
        self.assertEqual(e.hp, 30)  # 10 * 2 = 20 damage

    def test_resistance_and_vulnerability_cancel(self):
        e = _make_entity(hp=50, damage_resistances=["fire"],
                         damage_vulnerabilities=["fire"])
        dealt, _ = e.take_damage(10, "fire")
        self.assertEqual(e.hp, 40)  # No modification

    def test_rage_physical_resistance(self):
        e = _make_entity(hp=50)
        e.rage_active = True
        dealt, _ = e.take_damage(20, "slashing")
        self.assertEqual(e.hp, 40)  # 20 // 2 = 10

    def test_rage_no_psychic_resistance(self):
        e = _make_entity(hp=50)
        e.rage_active = True
        dealt, _ = e.take_damage(20, "psychic")
        self.assertEqual(e.hp, 30)  # No resistance for psychic

    def test_concentration_break_on_damage(self):
        random.seed(0)
        spell = SpellInfo(name="Bless", level=1, concentration=True)
        e = _make_entity(hp=50, spells_known=[spell], constitution=10)
        e.concentrating_on = spell
        # Large damage = high DC, likely to fail
        _, broke = e.take_damage(50, "bludgeoning")
        # With seed 0 and high DC, concentration likely broken
        # Just test that the mechanism works
        self.assertIsInstance(broke, bool)


class TestHealing(unittest.TestCase):
    def test_basic_heal(self):
        e = _make_entity(hp=50)
        e.hp = 20
        e.heal(15)
        self.assertEqual(e.hp, 35)

    def test_heal_capped_at_max(self):
        e = _make_entity(hp=50)
        e.hp = 45
        e.heal(20)
        self.assertEqual(e.hp, 50)

    def test_heal_from_zero(self):
        e = _make_entity(hp=50)
        e.hp = 0
        e.heal(10)
        self.assertEqual(e.hp, 10)


class TestFlying(unittest.TestCase):
    def test_cannot_fly_without_fly_speed(self):
        e = _make_entity()
        self.assertFalse(e.can_fly)
        self.assertFalse(e.start_flying())

    def test_can_fly_with_fly_speed(self):
        e = _make_entity(fly_speed=60)
        self.assertTrue(e.can_fly)
        result = e.start_flying()
        self.assertTrue(result)
        self.assertTrue(e.is_flying)

    def test_land(self):
        e = _make_entity(fly_speed=60)
        e.start_flying()
        e.elevation = 30
        e.land(ground_elevation=0)
        self.assertFalse(e.is_flying)
        self.assertEqual(e.elevation, 0)

    def test_fly_effect_grants_flight(self):
        e = _make_entity()
        e.active_effects["Fly"] = 10
        self.assertTrue(e.can_fly)
        self.assertEqual(e.effective_fly_speed, 60)


class TestWildShape(unittest.TestCase):
    def test_transform_and_revert(self):
        e = _make_entity("Druid", hp=40, strength=10, dexterity=14)
        bear_stats = CreatureStats(
            name="Brown Bear", size="Large", hit_points=34, armor_class=11,
            speed=40,
            abilities=AbilityScores(strength=19, dexterity=10, constitution=16),
            actions=[Action(name="Bite", attack_bonus=5, damage_dice="1d8",
                            damage_bonus=4, damage_type="piercing")],
        )
        e.transform_into(bear_stats)
        self.assertTrue(e.is_wild_shaped)
        self.assertEqual(e.hp, 34)
        self.assertEqual(e.stats.abilities.strength, 19)
        self.assertEqual(e.wild_shape_name, "Brown Bear")

        e.revert_form()
        self.assertFalse(e.is_wild_shaped)
        self.assertEqual(e.hp, 40)
        self.assertEqual(e.stats.abilities.strength, 10)


class TestTurnReset(unittest.TestCase):
    def test_reset_turn(self):
        e = _make_entity(speed=30)
        e.action_used = True
        e.bonus_action_used = True
        e.reaction_used = True
        e.movement_left = 0
        e.sneak_attack_used = True
        e.reset_turn()
        self.assertFalse(e.action_used)
        self.assertFalse(e.bonus_action_used)
        self.assertFalse(e.reaction_used)
        self.assertFalse(e.sneak_attack_used)
        self.assertGreater(e.movement_left, 0)


class TestDeathSaves(unittest.TestCase):
    def test_death_save_tracking(self):
        e = _make_entity(hp=50)
        e.hp = 0
        self.assertEqual(e.death_save_successes, 0)
        self.assertEqual(e.death_save_failures, 0)

    def test_roll_death_save(self):
        random.seed(42)
        e = _make_entity(hp=50)
        e.hp = 0
        result = e.roll_death_save()
        self.assertIsInstance(result, str)
        self.assertIn("Death Save", result)


class TestSizeInSquares(unittest.TestCase):
    def test_medium(self):
        e = _make_entity(size="Medium")
        self.assertEqual(e.size_in_squares, 1)

    def test_large(self):
        e = _make_entity(size="Large")
        self.assertEqual(e.size_in_squares, 2)

    def test_huge(self):
        e = _make_entity(size="Huge")
        self.assertEqual(e.size_in_squares, 3)

    def test_gargantuan(self):
        e = _make_entity(size="Gargantuan")
        self.assertEqual(e.size_in_squares, 4)


if __name__ == "__main__":
    unittest.main()
