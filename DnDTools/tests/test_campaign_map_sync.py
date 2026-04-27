"""Phase 10a — Campaign location ↔ map token bridge tests."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest

from data.world import World, Location
from data.map_engine import WorldMap, MapLayer, MapObject
from data.campaign_map_sync import (
    map_object_type_for_location, location_to_map_object,
    find_map_object_for_location, sync_location_to_map,
    sync_map_object_to_location, unlink_location,
    remove_map_objects_for_location, available_unplaced_locations,
    all_settlement_locations, all_settlement_objects,
)


def _wm():
    wm = WorldMap(name="T", width=100, height=100, tile_size=1)
    wm.layers = [MapLayer(id="L0", name="Surface")]
    wm.annotations = []
    return wm


def _world_with(*locs):
    w = World(name="W")
    for loc in locs:
        w.locations[loc.id] = loc
    return w


class TestTypeMapping(unittest.TestCase):
    def test_city_maps_to_city_token(self):
        loc = Location(id="x", name="Arenhold", location_type="city")
        self.assertEqual(map_object_type_for_location(loc), "city")

    def test_capital_maps_to_capital(self):
        loc = Location(id="x", name="Capital", location_type="capital")
        self.assertEqual(map_object_type_for_location(loc), "capital")

    def test_kingdom_maps_to_capital(self):
        loc = Location(id="x", name="Tarmaas", location_type="kingdom")
        self.assertEqual(map_object_type_for_location(loc), "capital")

    def test_unknown_falls_back(self):
        loc = Location(id="x", name="Y", location_type="planet")
        self.assertEqual(map_object_type_for_location(loc), "info_pin")


class TestLocationToMapObject(unittest.TestCase):
    def test_creates_object_with_link(self):
        loc = Location(id="loc1", name="Arenhold",
                        location_type="town",
                        description="Port city.",
                        notes="DM only", tags=["coast"])
        obj = location_to_map_object(loc, x=42, y=58)
        self.assertEqual(obj.linked_location_id, "loc1")
        self.assertEqual(obj.label, "Arenhold")
        self.assertEqual(obj.object_type, "town")
        self.assertEqual(obj.x, 42)
        self.assertEqual(obj.y, 58)
        self.assertIn("coast", obj.tags)


class TestSyncLocationToMap(unittest.TestCase):
    def test_inserts_when_missing(self):
        loc = Location(id="loc1", name="Vardun", location_type="fort")
        w = _world_with(loc)
        wm = _wm()
        obj = sync_location_to_map(w, wm, "loc1")
        self.assertEqual(obj.linked_location_id, "loc1")
        self.assertIn(obj, wm.layers[0].objects)
        self.assertEqual(obj.object_type, "fort")

    def test_idempotent_keeps_position(self):
        loc = Location(id="loc1", name="V", location_type="town")
        w = _world_with(loc)
        wm = _wm()
        first = sync_location_to_map(w, wm, "loc1")
        first.x = 10; first.y = 20
        # Mutate the location to verify display fields refresh
        loc.name = "V2"
        loc.notes = "updated"
        again = sync_location_to_map(w, wm, "loc1")
        self.assertIs(again, first)
        self.assertEqual(again.x, 10)   # position preserved
        self.assertEqual(again.label, "V2")  # label refreshed
        self.assertEqual(again.notes, "updated")

    def test_unknown_location_raises(self):
        with self.assertRaises(KeyError):
            sync_location_to_map(_world_with(), _wm(), "nope")


class TestSyncObjectToLocation(unittest.TestCase):
    def test_creates_location_for_unlinked_token(self):
        wm = _wm()
        obj = MapObject(x=10, y=20, object_type="village",
                         label="Bramblefoot", hover_info="Sleepy.")
        wm.layers[0].objects.append(obj)
        w = World()
        loc = sync_map_object_to_location(w, wm, obj.id)
        self.assertIsNotNone(loc)
        self.assertEqual(loc.name, "Bramblefoot")
        self.assertEqual(obj.linked_location_id, loc.id)
        self.assertIn(loc.id, w.locations)

    def test_skips_when_already_linked(self):
        existing = Location(id="loc1", name="V", location_type="town")
        w = _world_with(existing)
        wm = _wm()
        obj = MapObject(x=0, y=0, object_type="town", label="V",
                         linked_location_id="loc1")
        wm.layers[0].objects.append(obj)
        loc = sync_map_object_to_location(w, wm, obj.id)
        self.assertIs(loc, existing)
        self.assertEqual(len(w.locations), 1)


class TestUnlinkAndRemove(unittest.TestCase):
    def test_unlink_keeps_token(self):
        loc = Location(id="loc1", name="V", location_type="town")
        w = _world_with(loc)
        wm = _wm()
        sync_location_to_map(w, wm, "loc1")
        n = unlink_location(wm, "loc1")
        self.assertEqual(n, 1)
        self.assertEqual(len(wm.layers[0].objects), 1)
        self.assertEqual(wm.layers[0].objects[0].linked_location_id, "")

    def test_remove_drops_token(self):
        loc = Location(id="loc1", name="V", location_type="town")
        w = _world_with(loc)
        wm = _wm()
        sync_location_to_map(w, wm, "loc1")
        n = remove_map_objects_for_location(wm, "loc1")
        self.assertEqual(n, 1)
        self.assertEqual(wm.layers[0].objects, [])


class TestPalettes(unittest.TestCase):
    def test_unplaced_locations(self):
        a = Location(id="locA", name="A", location_type="city")
        b = Location(id="locB", name="B", location_type="town")
        w = _world_with(a, b)
        wm = _wm()
        sync_location_to_map(w, wm, "locA")
        unplaced = available_unplaced_locations(w, wm)
        self.assertEqual([loc.id for loc in unplaced], ["locB"])

    def test_settlement_location_filter(self):
        cap = Location(id="A", name="Cap", location_type="capital")
        wild = Location(id="B", name="Wild", location_type="wilderness")
        w = _world_with(cap, wild)
        kinds = {loc.id for loc in all_settlement_locations(w)}
        self.assertEqual(kinds, {"A"})

    def test_settlement_object_filter(self):
        wm = _wm()
        wm.layers[0].objects = [
            MapObject(x=0, y=0, object_type="city", label="A"),
            MapObject(x=1, y=1, object_type="info_pin", label="B"),
            MapObject(x=2, y=2, object_type="village", label="C"),
        ]
        labels = sorted(o.label for o in all_settlement_objects(wm))
        self.assertEqual(labels, ["A", "C"])


if __name__ == "__main__":
    unittest.main()
