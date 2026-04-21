"""Phase 4b — JPG/PNG battle-map background tests.

Covers:
  * BattleSystem.set_background_image accepts/rejects paths, clears on empty.
  * Serialization roundtrip includes background fields.
  * Alpha / cell-span / offset settings are clamped/coerced.
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
from engine.battle_serialization import get_state_dict, restore_state


def _make_entity(name="Test", x=5.0, y=5.0, is_player=True):
    stats = CreatureStats(
        name=name, size="Medium", hit_points=50, armor_class=15, speed=30,
        abilities=AbilityScores(strength=10, dexterity=10),
        actions=[Action(name="Sword", attack_bonus=5, damage_dice="1d8",
                        damage_bonus=3, damage_type="slashing", range=5)],
    )
    return Entity(stats, x, y, is_player=is_player)


def _make_battle(entities=None):
    log = []
    b = BattleSystem(log_callback=log.append, initial_entities=entities or [])
    return b, log


class TestBackgroundConfig(unittest.TestCase):
    def test_default_values(self):
        b, _ = _make_battle()
        self.assertEqual(b.background_image_path, "")
        self.assertEqual(b.background_alpha, 200)
        self.assertEqual(b.background_world_cells_w, 40)
        self.assertEqual(b.background_world_cells_h, 40)
        self.assertEqual(b.background_offset_x, 0)
        self.assertEqual(b.background_offset_y, 0)

    def test_clear_background(self):
        b, _ = _make_battle()
        b.background_image_path = "fake.jpg"
        ok = b.set_background_image("")
        self.assertTrue(ok)
        self.assertEqual(b.background_image_path, "")

    def test_missing_file_rejected(self):
        b, _ = _make_battle()
        ok = b.set_background_image("/nonexistent/definitely_missing_123.jpg")
        self.assertFalse(ok)
        self.assertEqual(b.background_image_path, "")

    def test_accept_real_file(self):
        b, _ = _make_battle()
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tf:
            tf.write(b"\xff\xd8\xff\xd9")  # minimal JPEG bytes (valid SOI/EOI)
            path = tf.name
        try:
            ok = b.set_background_image(path, alpha=128, cells_w=50, cells_h=30,
                                         offset_x=5, offset_y=-3)
            self.assertTrue(ok)
            self.assertEqual(b.background_image_path, path)
            self.assertEqual(b.background_alpha, 128)
            self.assertEqual(b.background_world_cells_w, 50)
            self.assertEqual(b.background_world_cells_h, 30)
            self.assertEqual(b.background_offset_x, 5)
            self.assertEqual(b.background_offset_y, -3)
        finally:
            os.unlink(path)

    def test_alpha_clamped(self):
        b, _ = _make_battle()
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tf:
            tf.write(b"x")
            path = tf.name
        try:
            b.set_background_image(path, alpha=500)
            self.assertEqual(b.background_alpha, 255)
            b.set_background_image(path, alpha=-20)
            self.assertEqual(b.background_alpha, 0)
        finally:
            os.unlink(path)

    def test_cells_min_1(self):
        b, _ = _make_battle()
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tf:
            tf.write(b"x")
            path = tf.name
        try:
            b.set_background_image(path, cells_w=0, cells_h=-3)
            self.assertEqual(b.background_world_cells_w, 1)
            self.assertEqual(b.background_world_cells_h, 1)
        finally:
            os.unlink(path)


class TestBackgroundSerialization(unittest.TestCase):
    def test_roundtrip_empty_background(self):
        hero = _make_entity("Hero", is_player=True)
        b, _ = _make_battle([hero])
        data = get_state_dict(b)
        self.assertIn("background_image_path", data)
        self.assertEqual(data["background_image_path"], "")

        b2, _ = _make_battle([_make_entity("Hero", is_player=True)])
        restore_state(b2, data)
        self.assertEqual(b2.background_image_path, "")

    def test_roundtrip_with_background(self):
        hero = _make_entity("Hero", is_player=True)
        b, _ = _make_battle([hero])
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tf:
            tf.write(b"x")
            path = tf.name
        try:
            b.set_background_image(path, alpha=180, cells_w=25, cells_h=20,
                                    offset_x=10, offset_y=20)
            data = get_state_dict(b)

            b2, _ = _make_battle([_make_entity("Hero", is_player=True)])
            restore_state(b2, data)
            self.assertEqual(b2.background_image_path, path)
            self.assertEqual(b2.background_alpha, 180)
            self.assertEqual(b2.background_world_cells_w, 25)
            self.assertEqual(b2.background_world_cells_h, 20)
            self.assertEqual(b2.background_offset_x, 10)
            self.assertEqual(b2.background_offset_y, 20)
        finally:
            os.unlink(path)

    def test_restore_missing_fields_defaults(self):
        """Old save files without background fields should load cleanly."""
        hero = _make_entity("Hero", is_player=True)
        b, _ = _make_battle([hero])
        data = get_state_dict(b)
        # Simulate an older save without the new keys
        for k in list(data.keys()):
            if k.startswith("background_"):
                del data[k]

        b2, _ = _make_battle([_make_entity("Hero", is_player=True)])
        restore_state(b2, data)
        self.assertEqual(b2.background_image_path, "")
        self.assertEqual(b2.background_alpha, 200)
        self.assertEqual(b2.background_world_cells_w, 40)


if __name__ == "__main__":
    unittest.main()
