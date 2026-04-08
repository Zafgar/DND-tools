"""Tests for engine/terrain.py – Terrain objects and LOS calculations."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest
from engine.terrain import (
    TerrainObject, TERRAIN_TYPES,
    get_elevation_at, check_los_blocked, calculate_fall_damage,
)


class TestTerrainTypes(unittest.TestCase):
    def test_wall_is_impassable(self):
        self.assertFalse(TERRAIN_TYPES["wall"]["passable"])

    def test_difficult_terrain_is_passable(self):
        self.assertTrue(TERRAIN_TYPES["difficult"]["passable"])

    def test_wall_blocks_los(self):
        self.assertTrue(TERRAIN_TYPES["wall"].get("blocks_los", False))

    def test_door_is_a_door(self):
        self.assertTrue(TERRAIN_TYPES["door"].get("door", False))

    def test_chasm_is_gap(self):
        self.assertTrue(TERRAIN_TYPES["chasm"].get("is_gap", False))

    def test_all_terrain_types_have_color(self):
        for name, data in TERRAIN_TYPES.items():
            self.assertIn("color", data, f"{name} missing color")

    def test_all_terrain_types_have_passable(self):
        for name, data in TERRAIN_TYPES.items():
            self.assertIn("passable", data, f"{name} missing passable flag")


class TestTerrainObject(unittest.TestCase):
    def test_create_wall(self):
        t = TerrainObject(terrain_type="wall", grid_x=5, grid_y=3)
        self.assertEqual(t.terrain_type, "wall")
        self.assertEqual(t.grid_x, 5)
        self.assertEqual(t.grid_y, 3)
        self.assertFalse(t.passable)
        self.assertTrue(t.blocks_los)

    def test_create_difficult_terrain(self):
        t = TerrainObject(terrain_type="difficult", grid_x=2, grid_y=2)
        self.assertTrue(t.passable)
        self.assertTrue(t.is_difficult)

    def test_occupies(self):
        t = TerrainObject(terrain_type="wall", grid_x=5, grid_y=5)
        self.assertTrue(t.occupies(5, 5))
        self.assertFalse(t.occupies(6, 5))
        self.assertFalse(t.occupies(5, 6))

    def test_door_toggle(self):
        t = TerrainObject(terrain_type="door", grid_x=3, grid_y=3)
        self.assertTrue(t.is_door)
        self.assertFalse(t.door_open)
        result = t.toggle_door()
        self.assertTrue(result)
        self.assertTrue(t.door_open)
        self.assertTrue(t.passable)  # Open door should be passable

    def test_locked_door_cannot_toggle(self):
        t = TerrainObject(terrain_type="door_locked", grid_x=3, grid_y=3)
        self.assertTrue(t.is_door)
        self.assertTrue(t.is_locked)
        result = t.toggle_door()
        self.assertFalse(result)  # Can't open locked door

    def test_unlock_then_toggle(self):
        t = TerrainObject(terrain_type="door_locked", grid_x=3, grid_y=3)
        t.unlock()
        self.assertFalse(t.is_locked)
        result = t.toggle_door()
        self.assertTrue(result)

    def test_serialization(self):
        t = TerrainObject(terrain_type="wall", grid_x=5, grid_y=3)
        data = t.to_dict()
        self.assertEqual(data["terrain_type"], "wall")
        self.assertEqual(data["grid_x"], 5)
        restored = TerrainObject.from_dict(data)
        self.assertEqual(restored.terrain_type, "wall")
        self.assertEqual(restored.grid_x, 5)
        self.assertEqual(restored.grid_y, 3)

    def test_cover_bonus(self):
        t = TerrainObject(terrain_type="cover", grid_x=5, grid_y=5)
        self.assertTrue(t.provides_cover)
        self.assertGreater(t.cover_bonus, 0)


class TestElevation(unittest.TestCase):
    def test_no_terrain_elevation_zero(self):
        elev = get_elevation_at([], 5, 5)
        self.assertEqual(elev, 0)

    def test_platform_elevation(self):
        t = TerrainObject(terrain_type="platform_10", grid_x=5, grid_y=5)
        elev = get_elevation_at([t], 5, 5)
        self.assertEqual(elev, 10)


class TestLOSBlocked(unittest.TestCase):
    def test_no_obstacles(self):
        result = check_los_blocked([], 0, 0, 10, 10)
        self.assertFalse(result)

    def test_wall_blocks(self):
        wall = TerrainObject(terrain_type="wall", grid_x=5, grid_y=5)
        result = check_los_blocked([wall], 0, 5, 10, 5)
        self.assertTrue(result)


class TestFallDamage(unittest.TestCase):
    def test_zero_height(self):
        dmg = calculate_fall_damage(0)
        self.assertEqual(dmg, 0)

    def test_ten_feet(self):
        import random
        random.seed(42)
        dmg = calculate_fall_damage(10)
        self.assertGreaterEqual(dmg, 1)
        self.assertLessEqual(dmg, 6)

    def test_twenty_feet(self):
        import random
        random.seed(42)
        dmg = calculate_fall_damage(20)
        self.assertGreaterEqual(dmg, 2)
        self.assertLessEqual(dmg, 12)

    def test_max_capped(self):
        """Fall damage maxes at 20d6 (120) per PHB rules."""
        import random
        random.seed(42)
        dmg = calculate_fall_damage(500)
        self.assertLessEqual(dmg, 120)


if __name__ == "__main__":
    unittest.main()
