"""Tests for the Phase 1 Map Engine data model."""
import json
import os
import tempfile
import unittest

from data.map_engine import (
    TERRAIN_BRUSHES, MAP_OBJECT_TYPES, MAP_TYPES, LAYER_TYPES,
    MapLayer, MapObject, WorldMap,
    serialize_world_map, deserialize_world_map,
    save_world_map, load_world_map, list_world_maps,
)


class TestPalettes(unittest.TestCase):
    def test_terrain_brush_structure(self):
        # Every brush has the three documented fields + valid category
        valid_cats = {"land", "water", "road", "hazard", "special"}
        for key, spec in TERRAIN_BRUSHES.items():
            self.assertIn("color", spec, key)
            self.assertIn("icon", spec, key)
            self.assertIn("category", spec, key)
            self.assertEqual(len(spec["color"]), 3, key)
            self.assertIn(spec["category"], valid_cats, key)

    def test_object_palette(self):
        for key, spec in MAP_OBJECT_TYPES.items():
            self.assertIn("icon", spec, key)
            self.assertIn("size", spec, key)
            self.assertIn("color", spec, key)
            self.assertGreater(spec["size"], 0.0, key)


class TestMapLayerPainting(unittest.TestCase):
    def test_set_and_get_tile(self):
        layer = MapLayer()
        layer.set_tile(3, 4, "forest")
        self.assertEqual(layer.get_tile(3, 4), "forest")
        self.assertEqual(layer.get_tile(5, 5), "")

    def test_empty_string_erases(self):
        layer = MapLayer()
        layer.set_tile(1, 1, "grass")
        layer.set_tile(1, 1, "")
        self.assertEqual(layer.get_tile(1, 1), "")

    def test_paint_brush_radius(self):
        layer = MapLayer()
        layer.paint_brush(5, 5, "grass", radius=1)
        # 3x3 square: 9 tiles
        self.assertEqual(len(layer.tiles), 9)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                self.assertEqual(layer.get_tile(5 + dx, 5 + dy), "grass")

    def test_flood_fill_respects_bounds_and_source(self):
        layer = MapLayer()
        # Fill a 4x4 patch with grass first
        for x in range(4):
            for y in range(4):
                layer.set_tile(x, y, "grass")
        # Block one tile with forest
        layer.set_tile(2, 2, "forest")
        changed = layer.flood_fill(0, 0, "ocean", width=4, height=4)
        # Every grass tile except (2,2) becomes ocean → 15 tiles
        self.assertEqual(changed, 15)
        self.assertEqual(layer.get_tile(2, 2), "forest")
        self.assertEqual(layer.get_tile(0, 0), "ocean")

    def test_flood_fill_no_op_if_target_matches(self):
        layer = MapLayer()
        layer.set_tile(0, 0, "ocean")
        self.assertEqual(layer.flood_fill(0, 0, "ocean", 4, 4), 0)


class TestMapObject(unittest.TestCase):
    def test_object_type_applies_palette_defaults(self):
        obj = MapObject(x=10, y=20, object_type="capital")
        self.assertEqual(obj.icon, MAP_OBJECT_TYPES["capital"]["icon"])
        self.assertEqual(obj.color, MAP_OBJECT_TYPES["capital"]["color"])
        self.assertEqual(obj.size, MAP_OBJECT_TYPES["capital"]["size"])

    def test_auto_id(self):
        obj = MapObject(object_type="info_pin")
        self.assertTrue(obj.id.startswith("obj_"))


class TestWorldMap(unittest.TestCase):
    def test_default_layer_created(self):
        wm = WorldMap(name="X")
        self.assertEqual(len(wm.layers), 1)
        self.assertEqual(wm.active_layer.name, "Surface")

    def test_add_and_remove_layer(self):
        wm = WorldMap()
        wm.add_layer("Underdark", "underground", -1)
        self.assertEqual(len(wm.layers), 2)
        self.assertEqual(wm.active_layer_idx, 1)
        # removing last layer is a no-op
        self.assertTrue(wm.remove_layer(1))
        self.assertEqual(len(wm.layers), 1)
        self.assertFalse(wm.remove_layer(0))  # cannot remove the last one


class TestSerialization(unittest.TestCase):
    def _sample_map(self) -> WorldMap:
        wm = WorldMap(name="Sample", width=10, height=8, tile_size=20)
        wm.active_layer.paint_brush(4, 4, "forest", radius=1)
        wm.active_layer.objects.append(
            MapObject(x=25.0, y=33.0, object_type="city", label="Sharn")
        )
        wm.add_layer("Underdark", "underground", -1)
        wm.active_layer.set_tile(1, 1, "cave_entrance")
        wm.active_layer_idx = 0
        return wm

    def test_round_trip_dict(self):
        wm = self._sample_map()
        data = serialize_world_map(wm)
        # Camera state must not be persisted.
        for trans in ("camera_x", "camera_y", "zoom"):
            self.assertNotIn(trans, data)
        wm2 = deserialize_world_map(data)
        self.assertEqual(wm2.name, wm.name)
        self.assertEqual(len(wm2.layers), len(wm.layers))
        self.assertEqual(wm2.layers[0].tiles, wm.layers[0].tiles)
        self.assertEqual(wm2.layers[1].tiles, wm.layers[1].tiles)
        self.assertEqual(wm2.layers[0].objects[0].label, "Sharn")
        # Tuples get restored from lists
        self.assertIsInstance(wm2.grid_color, tuple)
        self.assertIsInstance(wm2.layers[0].objects[0].color, tuple)

    def test_save_and_load_file(self):
        wm = self._sample_map()
        with tempfile.TemporaryDirectory() as td:
            path = save_world_map(wm, directory=td)
            self.assertTrue(os.path.isfile(path))
            # File is valid JSON
            with open(path) as f:
                raw = json.load(f)
            self.assertEqual(raw["name"], "Sample")
            loaded = load_world_map(path)
            self.assertEqual(loaded.id, wm.id)
            self.assertEqual(loaded.layers[0].get_tile(4, 4), "forest")
            self.assertEqual(list_world_maps(td), [f"{wm.id}.json"])


if __name__ == "__main__":
    unittest.main()
