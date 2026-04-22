"""Phase 5b/5c — Battle Environment modal logic tests.

We don't exercise the modal's pygame drawing; instead we verify the
action handlers (_nudge_alpha, _nudge_cells, _set_ceiling,
_clear_bg) mutate the BattleSystem correctly and clamp values to the
right bounds.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import unittest
import tempfile

from data.models import CreatureStats, AbilityScores, Action
from engine.entities import Entity
from engine.battle import BattleSystem


def _make_battle(entities=None):
    return BattleSystem(log_callback=lambda *a: None,
                         initial_entities=entities or [])


def _make_entity(name="Drake", fly_speed=60, x=5.0, y=5.0):
    stats = CreatureStats(
        name=name, size="Medium", hit_points=50, armor_class=15,
        speed=30, fly_speed=fly_speed,
        abilities=AbilityScores(strength=12, dexterity=14),
        actions=[Action(name="Bite", attack_bonus=5, damage_dice="1d8",
                        damage_bonus=3, damage_type="piercing", range=5)],
    )
    return Entity(stats, x, y, is_player=False)


class _StubModal:
    """Reproduces the handler methods of BattleEnvironmentModal without
    requiring pygame. Keeping it minimal — only the tested behaviour."""
    def __init__(self, battle):
        self.battle = battle
        self.log = lambda *a: None
        self.is_open = False

    # Mirror the production handlers
    def _nudge_alpha(self, delta):
        new_a = max(0, min(255, int(self.battle.background_alpha) + delta))
        self.battle.background_alpha = new_a

    def _nudge_cells(self, dw=0, dh=0):
        self.battle.background_world_cells_w = max(
            1, self.battle.background_world_cells_w + dw
        )
        self.battle.background_world_cells_h = max(
            1, self.battle.background_world_cells_h + dh
        )

    def _clear_bg(self):
        if not self.battle.background_image_path:
            return
        self.battle.set_background_image("")

    def _set_ceiling(self, ft):
        self.battle.ceiling_ft = max(0, int(ft))
        if ft > 0:
            for ent in self.battle.entities:
                self.battle.clamp_fly_altitude(ent)


class TestAlphaNudging(unittest.TestCase):
    def test_increase(self):
        b = _make_battle()
        m = _StubModal(b)
        b.background_alpha = 100
        m._nudge_alpha(+25)
        self.assertEqual(b.background_alpha, 125)

    def test_decrease(self):
        b = _make_battle()
        m = _StubModal(b)
        b.background_alpha = 100
        m._nudge_alpha(-25)
        self.assertEqual(b.background_alpha, 75)

    def test_clamp_upper(self):
        b = _make_battle()
        m = _StubModal(b)
        b.background_alpha = 250
        m._nudge_alpha(+25)
        self.assertEqual(b.background_alpha, 255)

    def test_clamp_lower(self):
        b = _make_battle()
        m = _StubModal(b)
        b.background_alpha = 10
        m._nudge_alpha(-25)
        self.assertEqual(b.background_alpha, 0)


class TestCellsNudging(unittest.TestCase):
    def test_width(self):
        b = _make_battle()
        m = _StubModal(b)
        m._nudge_cells(dw=+5)
        self.assertEqual(b.background_world_cells_w, 45)

    def test_height(self):
        b = _make_battle()
        m = _StubModal(b)
        m._nudge_cells(dh=-5)
        self.assertEqual(b.background_world_cells_h, 35)

    def test_min_1(self):
        b = _make_battle()
        m = _StubModal(b)
        b.background_world_cells_w = 3
        m._nudge_cells(dw=-10)
        self.assertEqual(b.background_world_cells_w, 1)


class TestClearBackground(unittest.TestCase):
    def test_clear_set(self):
        b = _make_battle()
        m = _StubModal(b)
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tf:
            tf.write(b"x"); path = tf.name
        try:
            b.set_background_image(path)
            self.assertEqual(b.background_image_path, path)
            m._clear_bg()
            self.assertEqual(b.background_image_path, "")
        finally:
            os.unlink(path)

    def test_clear_noop_when_empty(self):
        b = _make_battle()
        m = _StubModal(b)
        self.assertEqual(b.background_image_path, "")
        m._clear_bg()  # should not crash
        self.assertEqual(b.background_image_path, "")


class TestSetCeiling(unittest.TestCase):
    def test_set_ceiling(self):
        b = _make_battle()
        m = _StubModal(b)
        m._set_ceiling(15)
        self.assertEqual(b.ceiling_ft, 15)

    def test_set_open_sky(self):
        b = _make_battle()
        m = _StubModal(b)
        b.ceiling_ft = 20
        m._set_ceiling(0)
        self.assertEqual(b.ceiling_ft, 0)

    def test_set_ceiling_clamps_flyers(self):
        drake = _make_entity(fly_speed=60)
        drake.is_flying = True
        drake.elevation = 50
        b = _make_battle([drake])
        m = _StubModal(b)
        m._set_ceiling(15)
        self.assertLessEqual(drake.elevation, 10)

    def test_set_ceiling_open_does_not_clamp(self):
        drake = _make_entity(fly_speed=60)
        drake.is_flying = True
        drake.elevation = 100
        b = _make_battle([drake])
        m = _StubModal(b)
        m._set_ceiling(0)
        self.assertEqual(drake.elevation, 100)

    def test_set_ceiling_negative_rejected(self):
        b = _make_battle()
        m = _StubModal(b)
        m._set_ceiling(-5)
        self.assertEqual(b.ceiling_ft, 0)


if __name__ == "__main__":
    unittest.main()
