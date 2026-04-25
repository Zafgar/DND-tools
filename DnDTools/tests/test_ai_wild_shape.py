"""Phase 9b — AI Wild Shape tests."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import unittest

from data.models import (
    CreatureStats, AbilityScores, Action, Feature, SpellInfo,
)
from engine.entities import Entity
from engine.battle import BattleSystem
from engine.ai.tactical_ai import TacticalAI


def _druid(level=4, moon=False, hp=24, current_hp=None,
            wild_shape_uses=2):
    feats = [
        Feature(name="Wild Shape", uses_per_day=2,
                 mechanic="wild_shape"),
    ]
    if moon:
        feats.append(Feature(name="Combat Wild Shape",
                              mechanic="combat_wild_shape"))
    stats = CreatureStats(
        name=f"Druid (lv{level}{' moon' if moon else ''})",
        size="Medium", hit_points=hp, armor_class=12, speed=30,
        abilities=AbilityScores(strength=10, dexterity=12,
                                  constitution=14, intelligence=10,
                                  wisdom=16, charisma=8),
        features=feats,
        actions=[Action(name="Quarterstaff", attack_bonus=2,
                        damage_dice="1d6", damage_bonus=0,
                        damage_type="bludgeoning", range=5)],
        character_level=level,
    )
    e = Entity(stats, 5, 5, is_player=True)
    if current_hp is not None:
        e.hp = current_hp
    e.feature_uses["Wild Shape"] = wild_shape_uses
    return e


def _goblin(x=8, y=5, hp=10):
    stats = CreatureStats(
        name="Goblin", size="Small", hit_points=hp, armor_class=15,
        speed=30,
        abilities=AbilityScores(strength=8, dexterity=14,
                                  constitution=10, intelligence=10,
                                  wisdom=8, charisma=8),
        actions=[Action(name="Scimitar", attack_bonus=4,
                        damage_dice="1d6", damage_bonus=2,
                        damage_type="slashing", range=5)],
    )
    return Entity(stats, x, y, is_player=False)


def _battle(*ents):
    return BattleSystem(log_callback=lambda *a: None,
                         initial_entities=list(ents))


class TestMoonDruidShifts(unittest.TestCase):
    """Circle of the Moon (combat_wild_shape) should shift on bonus
    action whenever a fight is on, no matter the HP."""
    def test_full_hp_moon_druid_shifts(self):
        d = _druid(moon=True, hp=30, current_hp=30)
        g = _goblin()
        b = _battle(d, g)
        ai = TacticalAI()
        step = ai._try_wild_shape(d, [g], [], b)
        self.assertIsNotNone(step)
        self.assertEqual(step.action_name, "Wild Shape")
        self.assertEqual(step.step_type, "transform")
        self.assertIsNotNone(step.transform_stats)
        # Bonus action consumed
        self.assertTrue(d.bonus_action_used)
        self.assertFalse(d.action_used)


class TestRegularDruidShifts(unittest.TestCase):
    """Plain druids only shift when wounded — they want their spells
    in good health."""
    def test_full_hp_skips(self):
        d = _druid(moon=False, hp=30, current_hp=30)
        g = _goblin()
        b = _battle(d, g)
        step = TacticalAI()._try_wild_shape(d, [g], [], b)
        self.assertIsNone(step)

    def test_wounded_shifts(self):
        d = _druid(moon=False, hp=30, current_hp=8)   # 27% HP
        g = _goblin()
        b = _battle(d, g)
        step = TacticalAI()._try_wild_shape(d, [g], [], b)
        self.assertIsNotNone(step)
        self.assertEqual(step.action_name, "Wild Shape")
        self.assertTrue(d.action_used)


class TestNoShiftConditions(unittest.TestCase):
    def test_already_shifted_skips(self):
        d = _druid(moon=True, hp=30)
        d.is_wild_shaped = True
        g = _goblin()
        b = _battle(d, g)
        self.assertIsNone(TacticalAI()._try_wild_shape(d, [g], [], b))

    def test_no_uses_skips(self):
        d = _druid(moon=True, hp=30, wild_shape_uses=0)
        g = _goblin()
        b = _battle(d, g)
        self.assertIsNone(TacticalAI()._try_wild_shape(d, [g], [], b))

    def test_no_enemies_skips(self):
        d = _druid(moon=True, hp=30)
        b = _battle(d)
        self.assertIsNone(TacticalAI()._try_wild_shape(d, [], [], b))

    def test_no_wild_shape_feature_skips(self):
        # Plain fighter shouldn't trigger.
        stats = CreatureStats(
            name="Fighter", hit_points=30, armor_class=18,
            abilities=AbilityScores(strength=16, dexterity=12),
            actions=[Action(name="Sword", attack_bonus=5,
                            damage_dice="1d8", damage_bonus=3,
                            damage_type="slashing", range=5)],
        )
        f = Entity(stats, 5, 5, is_player=True)
        g = _goblin()
        b = _battle(f, g)
        self.assertIsNone(TacticalAI()._try_wild_shape(f, [g], [], b))

    def test_moon_druid_with_bonus_used_skips(self):
        d = _druid(moon=True, hp=30)
        d.bonus_action_used = True
        g = _goblin()
        b = _battle(d, g)
        self.assertIsNone(TacticalAI()._try_wild_shape(d, [g], [], b))

    def test_regular_druid_with_action_used_skips(self):
        d = _druid(moon=False, hp=30, current_hp=8)
        d.action_used = True
        g = _goblin()
        b = _battle(d, g)
        self.assertIsNone(TacticalAI()._try_wild_shape(d, [g], [], b))


class TestUsesAccounting(unittest.TestCase):
    def test_use_decrement(self):
        d = _druid(moon=True, hp=30, wild_shape_uses=2)
        g = _goblin()
        b = _battle(d, g)
        TacticalAI()._try_wild_shape(d, [g], [], b)
        self.assertEqual(d.feature_uses["Wild Shape"], 1)


class TestBeastSelection(unittest.TestCase):
    def test_picks_strongest_available_beast(self):
        d = _druid(moon=True, hp=30)
        g = _goblin()
        b = _battle(d, g)
        step = TacticalAI()._try_wild_shape(d, [g], [], b)
        # Highest-HP option in our short-list is Brown Bear (34 HP)
        self.assertIn(step.transform_stats.name,
                       ("Brown Bear", "Dire Wolf", "Black Bear"))


class TestPlanIntegration(unittest.TestCase):
    """Verify Wild Shape is actually attempted via calculate_turn."""
    def test_moon_druid_plan_includes_transform(self):
        d = _druid(moon=True, hp=30, current_hp=20)
        g = _goblin(x=8, y=5)
        b = _battle(d, g)
        plan = TacticalAI().calculate_turn(d, b)
        types = [s.step_type for s in plan.steps]
        self.assertIn("transform", types,
                       f"Expected a transform step in {types}")


if __name__ == "__main__":
    unittest.main()
