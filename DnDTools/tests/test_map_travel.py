"""Tests for data/map_travel.py — path-follow movement for map tokens."""
import unittest

from data.map_travel import (
    polyline_total_miles, point_at_miles, advance_followers,
)
from data.map_engine import WorldMap, MapLayer, MapObject, AnnotationPath


def _square_worldmap():
    """100x100 tile map with 1 px tiles → 100x100 px.  1 mile per %."""
    wm = WorldMap(name="T", width=100, height=100, tile_size=1,
                  scale_miles_per_pct=1.0, travel_speed_miles_per_day=10.0)
    wm.layers = [MapLayer(id="L0", name="Surface")]
    wm.annotations = []
    return wm


class TestPolylineLength(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(polyline_total_miles([], 100, 100, 1.0), 0.0)

    def test_single_point(self):
        self.assertEqual(polyline_total_miles([(0, 0)], 100, 100, 1.0), 0.0)

    def test_horizontal_run_square_map(self):
        # 0,50 -> 100,50 on 100x100 map = 100% run = 100 miles at scale 1
        pts = [(0, 50), (100, 50)]
        self.assertAlmostEqual(polyline_total_miles(pts, 100, 100, 1.0),
                                100.0, places=4)

    def test_y_rescaled_on_nonsquare_map(self):
        # On a 200x100 px map, 10% vertical = 5% horizontal-equivalent
        # => aspect = 0.5, dy_scaled = dy * 0.5
        pts = [(0, 0), (0, 10)]
        miles = polyline_total_miles(pts, 200, 100, 1.0)
        self.assertAlmostEqual(miles, 5.0, places=4)


class TestPointAtMiles(unittest.TestCase):
    def test_zero_miles_returns_first_point(self):
        pts = [(10, 10), (90, 10)]
        self.assertEqual(point_at_miles(pts, 100, 100, 1.0, 0.0), (10, 10))

    def test_clamps_to_last_point(self):
        pts = [(10, 10), (90, 10)]
        self.assertEqual(point_at_miles(pts, 100, 100, 1.0, 999.0),
                          (90, 10))

    def test_midpoint(self):
        # Run from x=0 to x=100 = 100 miles; midpoint at 50 miles
        pts = [(0, 50), (100, 50)]
        mid = point_at_miles(pts, 100, 100, 1.0, 50.0)
        self.assertAlmostEqual(mid[0], 50.0, places=4)
        self.assertAlmostEqual(mid[1], 50.0, places=4)

    def test_multi_segment(self):
        # Two legs: 0-50 (50mi), 50-100 (50mi).  At 75 miles we are
        # halfway along the second leg.
        pts = [(0, 50), (50, 50), (100, 50)]
        p = point_at_miles(pts, 100, 100, 1.0, 75.0)
        self.assertAlmostEqual(p[0], 75.0, places=4)

    def test_empty_points(self):
        self.assertEqual(point_at_miles([], 100, 100, 1.0, 5.0), (0.0, 0.0))


class TestAdvanceFollowers(unittest.TestCase):
    def _wm_with_path(self):
        wm = _square_worldmap()
        path = AnnotationPath(id="p1", name="Road",
                               points=[(0, 50), (100, 50)])
        wm.annotations.append(path)
        return wm, path

    def test_moves_token_along_path(self):
        wm, path = self._wm_with_path()
        obj = MapObject(x=0, y=50, object_type="party_token",
                         follow_path_id="p1")
        wm.layers[0].objects.append(obj)
        # 10 miles/day * 1 day = 10 miles = 10% horizontal
        moved = advance_followers(wm, days=1)
        self.assertEqual(moved, 1)
        self.assertAlmostEqual(obj.x, 10.0, places=4)
        self.assertAlmostEqual(obj.y, 50.0, places=4)
        self.assertAlmostEqual(obj.path_progress_miles, 10.0, places=4)

    def test_clamps_at_path_end(self):
        wm, _ = self._wm_with_path()
        obj = MapObject(x=0, y=50, object_type="party_token",
                         follow_path_id="p1")
        wm.layers[0].objects.append(obj)
        advance_followers(wm, days=999)
        self.assertAlmostEqual(obj.x, 100.0, places=4)
        self.assertAlmostEqual(obj.path_progress_miles, 100.0, places=4)

    def test_zero_days_noop(self):
        wm, _ = self._wm_with_path()
        obj = MapObject(x=5, y=50, object_type="party_token",
                         follow_path_id="p1")
        wm.layers[0].objects.append(obj)
        self.assertEqual(advance_followers(wm, 0), 0)
        self.assertEqual(obj.x, 5)

    def test_respects_speed_mult(self):
        wm, _ = self._wm_with_path()
        slow = MapObject(x=0, y=50, object_type="caravan",
                          follow_path_id="p1", travel_speed_mult=0.5)
        wm.layers[0].objects.append(slow)
        advance_followers(wm, days=2)   # 10 * 0.5 * 2 = 10 miles
        self.assertAlmostEqual(slow.path_progress_miles, 10.0, places=4)

    def test_ignores_tokens_without_path(self):
        wm, _ = self._wm_with_path()
        detached = MapObject(x=30, y=30, object_type="party_token")
        wm.layers[0].objects.append(detached)
        moved = advance_followers(wm, days=1)
        self.assertEqual(moved, 0)
        self.assertEqual(detached.x, 30)

    def test_unknown_path_is_skipped(self):
        wm, _ = self._wm_with_path()
        obj = MapObject(x=5, y=5, object_type="party_token",
                         follow_path_id="missing")
        wm.layers[0].objects.append(obj)
        moved = advance_followers(wm, days=1)
        self.assertEqual(moved, 0)


class TestMapObjectSerialization(unittest.TestCase):
    def test_roundtrip_movement_fields(self):
        from data.map_engine import _obj_to_dict, _obj_from_dict
        obj = MapObject(x=1, y=2, object_type="party_token",
                         follow_path_id="p1",
                         path_progress_miles=12.5,
                         travel_speed_mult=1.5)
        d = _obj_to_dict(obj)
        round_trip = _obj_from_dict(d)
        self.assertEqual(round_trip.follow_path_id, "p1")
        self.assertAlmostEqual(round_trip.path_progress_miles, 12.5, places=4)
        self.assertAlmostEqual(round_trip.travel_speed_mult, 1.5, places=4)


if __name__ == "__main__":
    unittest.main()
