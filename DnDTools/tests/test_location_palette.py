"""Phase 11c — campaign-locations drag-onto-map palette tests."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest

from data.world import World, Location
from data.map_engine import WorldMap, MapLayer, MapObject
from data.campaign_map_sync import sync_location_to_map
from data.location_palette import (
    PaletteEntry, location_palette_entries,
    place_location_on_map, palette_search, unplaced_count,
)


def _wm():
    wm = WorldMap(name="T", width=100, height=100, tile_size=1)
    wm.layers = [MapLayer(id="L0", name="Surface")]
    wm.annotations = []
    return wm


def _world_with_locs(*locs):
    w = World()
    for loc in locs:
        w.locations[loc.id] = loc
    return w


class TestPaletteEntries(unittest.TestCase):
    def test_lists_settlements_alphabetically(self):
        w = _world_with_locs(
            Location(id="a", name="Zorvath", location_type="city"),
            Location(id="b", name="Arenhold", location_type="town"),
            Location(id="c", name="Vardun Keep", location_type="fort"),
        )
        entries = location_palette_entries(w, _wm())
        names = [e.name for e in entries]
        self.assertEqual(names, ["Arenhold", "Vardun Keep", "Zorvath"])

    def test_filters_to_settlements_only(self):
        w = _world_with_locs(
            Location(id="a", name="A City", location_type="city"),
            Location(id="b", name="A Wilderness", location_type="wilderness"),
            Location(id="c", name="A Region", location_type="region"),
        )
        entries = location_palette_entries(w, _wm())
        self.assertEqual([e.location_id for e in entries], ["a"])

    def test_settlements_only_false_lists_everything(self):
        w = _world_with_locs(
            Location(id="a", name="A Region", location_type="region"),
            Location(id="b", name="B City",   location_type="city"),
        )
        entries = location_palette_entries(w, _wm(),
                                              settlements_only=False)
        self.assertEqual({e.location_id for e in entries}, {"a", "b"})

    def test_marks_placed_entries(self):
        w = _world_with_locs(
            Location(id="a", name="Already on map", location_type="city"),
            Location(id="b", name="Not on map yet", location_type="town"),
        )
        wm = _wm()
        sync_location_to_map(w, wm, "a")
        entries = location_palette_entries(w, wm)
        a_entry = next(e for e in entries if e.location_id == "a")
        b_entry = next(e for e in entries if e.location_id == "b")
        self.assertTrue(a_entry.has_token)
        self.assertFalse(b_entry.has_token)


class TestPlaceLocation(unittest.TestCase):
    def test_drops_at_exact_position(self):
        w = _world_with_locs(
            Location(id="a", name="Arenhold", location_type="town"),
        )
        wm = _wm()
        obj = place_location_on_map(w, wm, "a", 42.0, 58.0)
        self.assertIsNotNone(obj)
        self.assertEqual(obj.x, 42.0)
        self.assertEqual(obj.y, 58.0)
        self.assertEqual(obj.linked_location_id, "a")

    def test_subsequent_drop_moves_existing_token(self):
        w = _world_with_locs(
            Location(id="a", name="A", location_type="town"),
        )
        wm = _wm()
        place_location_on_map(w, wm, "a", 10, 10)
        # Second drop on the same location → moves it
        obj = place_location_on_map(w, wm, "a", 80, 80)
        self.assertEqual(obj.x, 80)
        self.assertEqual(obj.y, 80)
        # Only one token total
        tokens = [o for o in wm.layers[0].objects
                  if o.linked_location_id == "a"]
        self.assertEqual(len(tokens), 1)

    def test_unknown_location_returns_none(self):
        wm = _wm()
        self.assertIsNone(place_location_on_map(World(), wm, "ghost",
                                                   0, 0))


class TestSearch(unittest.TestCase):
    def setUp(self):
        self.w = _world_with_locs(
            Location(id="a", name="Arenhold", location_type="town",
                      description="Port-city on Greysea."),
            Location(id="b", name="Vardun Keep", location_type="fort"),
            Location(id="c", name="Silver City", location_type="city"),
        )
        self.wm = _wm()

    def test_empty_returns_all(self):
        self.assertEqual(len(palette_search(self.w, self.wm, "")), 3)

    def test_name_match(self):
        rows = palette_search(self.w, self.wm, "vardun")
        self.assertEqual([r.location_id for r in rows], ["b"])

    def test_type_match(self):
        rows = palette_search(self.w, self.wm, "fort")
        self.assertEqual([r.location_id for r in rows], ["b"])

    def test_description_match(self):
        rows = palette_search(self.w, self.wm, "greysea")
        self.assertEqual([r.location_id for r in rows], ["a"])


class TestCount(unittest.TestCase):
    def test_unplaced_count_decreases_after_placement(self):
        w = _world_with_locs(
            Location(id="a", name="A", location_type="town"),
            Location(id="b", name="B", location_type="town"),
        )
        wm = _wm()
        self.assertEqual(unplaced_count(w, wm), 2)
        place_location_on_map(w, wm, "a", 50, 50)
        self.assertEqual(unplaced_count(w, wm), 1)


if __name__ == "__main__":
    unittest.main()
