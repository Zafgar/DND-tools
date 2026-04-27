"""Phase 11c — drag-onto-map palette widget lifecycle tests.

Pure-logic tests against the LocationPaletteWidget API. The widget is
pygame-dependent so the rendering path skips when pygame isn't
available; the search/state/click-routing logic is exercised
directly.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import unittest

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

from data.world import World, Location
from data.map_engine import WorldMap, MapLayer


def _stub_state(world, world_map):
    """Minimal stand-in for MapEditorState — only the attributes the
    widget reads."""
    class S:
        pass
    s = S()
    s.world = world
    s.world_map = world_map
    s.screen_w = 1600
    s.screen_h = 900
    s._set_status = lambda msg: setattr(s, "_last_status", msg)
    return s


def _world_with_locs(*locs):
    w = World()
    for loc in locs:
        w.locations[loc.id] = loc
    return w


def _wm():
    wm = WorldMap(name="T", width=100, height=100, tile_size=1)
    wm.layers = [MapLayer(id="L0", name="Surface")]
    wm.annotations = []
    return wm


@unittest.skipUnless(PYGAME_AVAILABLE, "pygame not available")
class TestWidgetLifecycle(unittest.TestCase):
    def setUp(self):
        from states.location_palette_widget import LocationPaletteWidget
        self.WidgetCls = LocationPaletteWidget

    def test_starts_closed(self):
        w = self.WidgetCls(_stub_state(World(), _wm()))
        self.assertFalse(w.is_open)

    def test_open_close(self):
        w = self.WidgetCls(_stub_state(World(), _wm()))
        w.open()
        self.assertTrue(w.is_open)
        self.assertFalse(w.search_active)
        self.assertEqual(w.scroll, 0)
        w.close()
        self.assertFalse(w.is_open)

    def test_close_callback_runs(self):
        called = []
        w = self.WidgetCls(
            _stub_state(World(), _wm()),
            on_close=lambda: called.append(True),
        )
        w.open()
        w.close()
        self.assertEqual(called, [True])

    def test_drop_at_canvas_center_inserts_token(self):
        loc = Location(id="loc1", name="Arenhold",
                        location_type="town")
        world = _world_with_locs(loc)
        wm = _wm()
        state = _stub_state(world, wm)
        w = self.WidgetCls(state)
        from data.location_palette import (
            location_palette_entries,
        )
        rows = location_palette_entries(world, wm)
        self.assertEqual(len(rows), 1)
        w._drop_at_canvas_center(rows[0])
        # MapObject created
        self.assertEqual(len(wm.layers[0].objects), 1)
        obj = wm.layers[0].objects[0]
        self.assertEqual(obj.linked_location_id, "loc1")
        self.assertEqual(obj.x, 50.0)
        self.assertEqual(obj.y, 50.0)
        self.assertIn("Arenhold", state._last_status)


if __name__ == "__main__":
    unittest.main()
