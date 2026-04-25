"""Phase 7a — settlement waypoint detection tests."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest

from data.map_travel import (
    advance_followers_events, nearby_settlements,
    clear_waypoints, DEFAULT_WAYPOINT_TOLERANCE_PCT,
)
from data.map_engine import (
    WorldMap, MapLayer, MapObject, AnnotationPath,
)


def _wm():
    wm = WorldMap(name="T", width=100, height=100, tile_size=1,
                   scale_miles_per_pct=1.0, travel_speed_miles_per_day=10.0)
    wm.layers = [MapLayer(id="L0", name="Surface")]
    wm.annotations = []
    return wm


def _settle(wm, name, x, y, kind="town"):
    obj = MapObject(x=x, y=y, object_type=kind, label=name)
    wm.layers[0].objects.append(obj)
    return obj


def _path_token(wm, points, label="Caravan", start_miles=0.0):
    p = AnnotationPath(id="P1", name="Trade Road", path_type="road",
                       points=list(points))
    wm.annotations.append(p)
    obj = MapObject(x=points[0][0], y=points[0][1],
                    object_type="caravan", label=label,
                    follow_path_id="P1",
                    path_progress_miles=start_miles)
    wm.layers[0].objects.append(obj)
    return p, obj


class TestNearbySettlements(unittest.TestCase):
    def test_detects_within_tolerance(self):
        wm = _wm()
        _settle(wm, "Arenhold", 50, 50, "town")
        hits = nearby_settlements(wm, 50.5, 50.5, tolerance_pct=1.5)
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].label, "Arenhold")

    def test_skips_outside_tolerance(self):
        wm = _wm()
        _settle(wm, "Faraway", 90, 90)
        self.assertEqual(nearby_settlements(wm, 10, 10, 1.0), [])

    def test_ignores_non_settlements(self):
        wm = _wm()
        # Treasure pin at the spot, no settlement
        wm.layers[0].objects.append(
            MapObject(x=50, y=50, object_type="treasure", label="X")
        )
        self.assertEqual(nearby_settlements(wm, 50, 50, 1.0), [])

    def test_sorted_nearest_first(self):
        wm = _wm()
        a = _settle(wm, "A", 50, 50)
        b = _settle(wm, "B", 50, 50.4)
        c = _settle(wm, "C", 50, 50.2)
        hits = nearby_settlements(wm, 50, 50, tolerance_pct=1.0)
        self.assertEqual([h.label for h in hits], ["A", "C", "B"])

    def test_supports_all_settlement_kinds(self):
        wm = _wm()
        for k in ("capital", "city", "town", "village", "fort"):
            _settle(wm, k.title(), 50, 50, kind=k)
        hits = nearby_settlements(wm, 50, 50, tolerance_pct=1.0)
        self.assertEqual(len(hits), 5)


class TestEventWaypoints(unittest.TestCase):
    def test_passing_through_settlement(self):
        wm = _wm()
        _settle(wm, "Midway", 50, 50)  # midpoint of horizontal path
        _, obj = _path_token(wm, [(0, 50), (100, 50)])
        # 1 day = 10 mi → still at x=10, far from midway
        events = advance_followers_events(wm, days=1)
        self.assertEqual(events[0]["waypoints_passed"], [])
        # 5 more days → x≈60, past Midway
        events = advance_followers_events(wm, days=5)
        wps = events[0]["waypoints_passed"]
        self.assertEqual(len(wps), 1)
        self.assertEqual(wps[0]["label"], "Midway")

    def test_waypoint_only_emitted_once(self):
        wm = _wm()
        _settle(wm, "Midway", 50, 50)
        _, obj = _path_token(wm, [(0, 50), (100, 50)])
        # Fast-forward past Midway
        advance_followers_events(wm, days=6)   # x→60, Midway crossed
        events = advance_followers_events(wm, days=1)  # x→70
        self.assertEqual(events[0]["waypoints_passed"], [])

    def test_multiple_waypoints_in_one_step(self):
        wm = _wm()
        _settle(wm, "First",  20, 50)
        _settle(wm, "Second", 40, 50)
        _settle(wm, "Third",  60, 50)
        _, obj = _path_token(wm, [(0, 50), (100, 50)])
        events = advance_followers_events(wm, days=7)  # x→70 past all 3
        labels = sorted(w["label"] for w in events[0]["waypoints_passed"])
        self.assertEqual(labels, ["First", "Second", "Third"])

    def test_clear_waypoints_lets_them_re_emit(self):
        wm = _wm()
        _settle(wm, "Midway", 50, 50)
        _, obj = _path_token(wm, [(0, 50), (100, 50)])
        advance_followers_events(wm, days=7)  # crosses Midway
        clear_waypoints(obj)
        # Force the token back to before Midway and re-advance
        obj.x, obj.y, obj.path_progress_miles = 0, 50, 0
        events = advance_followers_events(wm, days=7)
        labels = [w["label"] for w in events[0]["waypoints_passed"]]
        self.assertIn("Midway", labels)

    def test_arrival_destination_also_emits_waypoint(self):
        """A path ending AT a settlement still flags it as passed."""
        wm = _wm()
        _settle(wm, "Endpoint", 100, 50)
        _, obj = _path_token(wm, [(0, 50), (100, 50)])
        events = advance_followers_events(wm, days=20)  # arrive
        self.assertTrue(events[0]["arrived"])
        labels = [w["label"] for w in events[0]["waypoints_passed"]]
        self.assertIn("Endpoint", labels)


class TestVisitedSerialization(unittest.TestCase):
    def test_visited_roundtrips(self):
        from data.map_engine import _obj_to_dict, _obj_from_dict
        obj = MapObject(x=0, y=0, object_type="caravan",
                         visited_waypoint_ids=["obj_a", "obj_b"])
        d = _obj_to_dict(obj)
        self.assertEqual(d["visited_waypoint_ids"], ["obj_a", "obj_b"])
        obj2 = _obj_from_dict(d)
        self.assertEqual(obj2.visited_waypoint_ids, ["obj_a", "obj_b"])

    def test_legacy_object_default_empty(self):
        from data.map_engine import _obj_from_dict
        obj = _obj_from_dict({"id": "x", "x": 0, "y": 0,
                               "object_type": "caravan"})
        self.assertEqual(obj.visited_waypoint_ids, [])


if __name__ == "__main__":
    unittest.main()
