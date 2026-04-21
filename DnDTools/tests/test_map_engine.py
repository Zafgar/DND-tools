"""Tests for the Map Engine data model."""
import json
import os
import tempfile
import unittest

from data.map_engine import (
    TERRAIN_BRUSHES, MAP_OBJECT_TYPES, MAP_TYPES, LAYER_TYPES,
    SETTLEMENT_TYPES, DRILLDOWN_TYPES, TOKEN_TYPES,
    MapLayer, MapObject, WorldMap, AnnotationPath,
    serialize_world_map, deserialize_world_map,
    save_world_map, load_world_map, list_world_maps,
    load_all_world_maps, delete_world_map,
)


class TestPalettes(unittest.TestCase):
    def test_terrain_brush_structure(self):
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

    def test_category_constants_reference_real_types(self):
        for key in SETTLEMENT_TYPES + DRILLDOWN_TYPES + TOKEN_TYPES:
            self.assertIn(key, MAP_OBJECT_TYPES, key)


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
        self.assertEqual(len(layer.tiles), 9)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                self.assertEqual(layer.get_tile(5 + dx, 5 + dy), "grass")

    def test_flood_fill_respects_bounds_and_source(self):
        layer = MapLayer()
        for x in range(4):
            for y in range(4):
                layer.set_tile(x, y, "grass")
        layer.set_tile(2, 2, "forest")
        changed = layer.flood_fill(0, 0, "ocean", width=4, height=4)
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

    def test_drilldown_and_token_flags(self):
        city = MapObject(object_type="city")
        self.assertTrue(city.is_drilldown)
        self.assertFalse(city.is_token)

        party = MapObject(object_type="party_token")
        self.assertTrue(party.is_token)
        # Party token without a linked_map_id should not pretend to drill-down
        self.assertFalse(party.is_drilldown)

        pin_with_link = MapObject(object_type="info_pin", linked_map_id="map_123")
        self.assertTrue(pin_with_link.is_drilldown)

    def test_extended_fields_defaults(self):
        obj = MapObject(object_type="trap", trap_save="DC 15 DEX",
                        trap_damage="2d10 piercing", lockpick_dc=18,
                        detect_dc=15, hidden=True, dm_only=True)
        self.assertEqual(obj.lockpick_dc, 18)
        self.assertTrue(obj.hidden)
        self.assertTrue(obj.dm_only)


class TestAnnotationPath(unittest.TestCase):
    def test_length_pct_and_default_id(self):
        p = AnnotationPath(points=[(0.0, 0.0), (3.0, 4.0)])
        self.assertTrue(p.id.startswith("path_"))
        self.assertAlmostEqual(p.length_pct(), 5.0, places=5)

    def test_empty_path_has_zero_length(self):
        self.assertEqual(AnnotationPath().length_pct(), 0.0)


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
        self.assertTrue(wm.remove_layer(1))
        self.assertEqual(len(wm.layers), 1)
        self.assertFalse(wm.remove_layer(0))  # cannot remove last one

    def test_find_and_remove_object(self):
        wm = WorldMap()
        wm.active_layer.objects.append(MapObject(x=1, y=2, label="A"))
        obj = wm.active_layer.objects[0]
        self.assertIs(wm.find_object(obj.id), obj)
        self.assertTrue(wm.remove_object(obj.id))
        self.assertIsNone(wm.find_object(obj.id))

    def test_scale_conversions(self):
        wm = WorldMap(scale_miles_per_pct=2.0, travel_speed_miles_per_day=20.0)
        # 5% straight-line == 10 miles
        miles = wm.pct_to_miles(3.0, 4.0)
        self.assertAlmostEqual(miles, 10.0)
        self.assertAlmostEqual(wm.miles_to_travel_days(20.0), 1.0)


class TestSerialization(unittest.TestCase):
    def _sample_map(self) -> WorldMap:
        wm = WorldMap(name="Sample", width=10, height=8, tile_size=20,
                      background_image="saves/map_backgrounds/world.jpg",
                      scale_miles_per_pct=1.25, owner_kingdom="Tarmaas")
        wm.active_layer.paint_brush(4, 4, "forest", radius=1)
        wm.active_layer.objects.append(
            MapObject(x=25.0, y=33.0, object_type="city", label="Frand",
                      linked_map_id="map_frand", hover_info="Capital of Tarmaas",
                      linked_npc_ids=["npc_1", "npc_2"])
        )
        wm.active_layer.objects.append(
            MapObject(x=60.0, y=40.0, object_type="trap",
                      trap_save="DC 15 DEX", trap_damage="2d10 piercing",
                      hidden=True, dm_only=True)
        )
        wm.annotations.append(AnnotationPath(
            name="King's Road",
            points=[(10.0, 10.0), (25.0, 20.0), (40.0, 35.0)],
            path_type="road",
        ))
        wm.add_layer("Underdark", "underground", -1)
        wm.active_layer.set_tile(1, 1, "cave_entrance")
        wm.active_layer_idx = 0
        return wm

    def test_round_trip_dict(self):
        wm = self._sample_map()
        data = serialize_world_map(wm)
        for trans in ("camera_x", "camera_y", "zoom"):
            self.assertNotIn(trans, data)
        wm2 = deserialize_world_map(data)
        self.assertEqual(wm2.name, wm.name)
        self.assertEqual(wm2.owner_kingdom, "Tarmaas")
        self.assertEqual(wm2.scale_miles_per_pct, 1.25)
        self.assertEqual(len(wm2.layers), len(wm.layers))
        self.assertEqual(wm2.layers[0].tiles, wm.layers[0].tiles)
        self.assertEqual(wm2.layers[1].tiles, wm.layers[1].tiles)
        # Objects survive with extended fields
        city = wm2.layers[0].objects[0]
        self.assertEqual(city.label, "Frand")
        self.assertEqual(city.linked_map_id, "map_frand")
        self.assertEqual(city.linked_npc_ids, ["npc_1", "npc_2"])
        self.assertEqual(city.hover_info, "Capital of Tarmaas")
        trap = wm2.layers[0].objects[1]
        self.assertEqual(trap.trap_save, "DC 15 DEX")
        self.assertTrue(trap.hidden)
        self.assertTrue(trap.dm_only)
        # Annotations survive
        self.assertEqual(len(wm2.annotations), 1)
        self.assertAlmostEqual(
            wm2.annotations[0].length_pct(), wm.annotations[0].length_pct()
        )
        # Tuple vs list
        self.assertIsInstance(wm2.grid_color, tuple)
        self.assertIsInstance(wm2.layers[0].objects[0].color, tuple)

    def test_save_and_load_file(self):
        wm = self._sample_map()
        with tempfile.TemporaryDirectory() as td:
            path = save_world_map(wm, directory=td)
            self.assertTrue(os.path.isfile(path))
            with open(path) as f:
                raw = json.load(f)
            self.assertEqual(raw["name"], "Sample")
            loaded = load_world_map(path)
            self.assertEqual(loaded.id, wm.id)
            self.assertEqual(loaded.layers[0].get_tile(4, 4), "forest")
            self.assertEqual(list_world_maps(td), [f"{wm.id}.json"])

    def test_load_all_and_delete(self):
        with tempfile.TemporaryDirectory() as td:
            a = WorldMap(name="A")
            b = WorldMap(name="B")
            save_world_map(a, directory=td)
            save_world_map(b, directory=td)
            all_maps = load_all_world_maps(td)
            self.assertEqual(set(all_maps.keys()), {a.id, b.id})
            self.assertTrue(delete_world_map(a.id, directory=td))
            self.assertFalse(delete_world_map(a.id, directory=td))
            remaining = load_all_world_maps(td)
            self.assertEqual(set(remaining.keys()), {b.id})


if __name__ == "__main__":
    unittest.main()
