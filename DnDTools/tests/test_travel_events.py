"""Phase 6b — arrival events + manual progression tests."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest

from data.map_travel import (
    advance_followers, advance_followers_events,
    set_progress_miles, set_progress_fraction, token_progress,
)
from data.map_engine import (
    WorldMap, MapLayer, MapObject, AnnotationPath,
)


def _square_wm():
    """100% wide, 100% tall, 10 mi/day, 1 mi per % → easy arithmetic."""
    wm = WorldMap(name="T", width=100, height=100, tile_size=1,
                   scale_miles_per_pct=1.0, travel_speed_miles_per_day=10.0)
    wm.layers = [MapLayer(id="L0", name="Surface")]
    wm.annotations = []
    return wm


def _add_path_and_token(wm, path_points, label="P", speed_mult=1.0,
                        start_miles=0.0):
    p = AnnotationPath(id="P1", name="Road", path_type="road",
                       points=list(path_points))
    wm.annotations.append(p)
    obj = MapObject(x=path_points[0][0], y=path_points[0][1],
                    object_type="party_token", label=label,
                    follow_path_id="P1", travel_speed_mult=speed_mult,
                    path_progress_miles=start_miles)
    wm.layers[0].objects.append(obj)
    return p, obj


class TestAdvanceEvents(unittest.TestCase):
    def test_no_days_no_events(self):
        wm = _square_wm()
        _add_path_and_token(wm, [(0, 50), (100, 50)])
        self.assertEqual(advance_followers_events(wm, 0), [])

    def test_single_token_event_fields(self):
        wm = _square_wm()
        _, obj = _add_path_and_token(wm, [(0, 50), (100, 50)], label="Caravan")
        events = advance_followers_events(wm, days=1)  # 10 miles
        self.assertEqual(len(events), 1)
        ev = events[0]
        self.assertEqual(ev["obj_id"], obj.id)
        self.assertEqual(ev["label"], "Caravan")
        self.assertEqual(ev["path_id"], "P1")
        self.assertEqual(ev["path_name"], "Road")
        self.assertAlmostEqual(ev["miles_before"], 0.0)
        self.assertAlmostEqual(ev["miles_after"], 10.0)
        self.assertAlmostEqual(ev["total_miles"], 100.0)
        self.assertAlmostEqual(ev["fraction"], 0.1)
        self.assertFalse(ev["arrived"])

    def test_arrival_flagged_on_reaching_end(self):
        wm = _square_wm()
        _add_path_and_token(wm, [(0, 50), (100, 50)], start_miles=95.0)
        events = advance_followers_events(wm, days=1)  # would move 10 mi
        self.assertEqual(len(events), 1)
        self.assertTrue(events[0]["arrived"])
        self.assertAlmostEqual(events[0]["miles_after"], 100.0)

    def test_no_second_arrival_when_already_at_end(self):
        """An already-arrived token doesn't re-trigger 'arrived' on the
        next advance — it's still at the end, not arriving this call."""
        wm = _square_wm()
        _, obj = _add_path_and_token(wm, [(0, 50), (100, 50)])
        advance_followers_events(wm, days=100)  # arrive
        events = advance_followers_events(wm, days=1)  # try again
        self.assertEqual(len(events), 1)
        self.assertFalse(events[0]["arrived"])
        self.assertAlmostEqual(events[0]["miles_before"], 100.0)

    def test_multiple_tokens_emit_one_event_each(self):
        wm = _square_wm()
        # First token
        _add_path_and_token(wm, [(0, 50), (100, 50)], label="A")
        # Second token, on a separate path
        p2 = AnnotationPath(id="P2", name="Mountain", path_type="road",
                             points=[(0, 10), (100, 10)])
        wm.annotations.append(p2)
        wm.layers[0].objects.append(
            MapObject(x=0, y=10, object_type="army_token", label="B",
                      follow_path_id="P2")
        )
        events = advance_followers_events(wm, days=1)
        labels = sorted(e["label"] for e in events)
        self.assertEqual(labels, ["A", "B"])

    def test_backward_compat_advance_followers_returns_int(self):
        wm = _square_wm()
        _add_path_and_token(wm, [(0, 50), (100, 50)])
        self.assertEqual(advance_followers(wm, 1), 1)


class TestSetProgressMiles(unittest.TestCase):
    def test_sets_position_and_progress(self):
        wm = _square_wm()
        _, obj = _add_path_and_token(wm, [(0, 50), (100, 50)])
        ok = set_progress_miles(wm, obj, 25.0)
        self.assertTrue(ok)
        self.assertAlmostEqual(obj.path_progress_miles, 25.0)
        self.assertAlmostEqual(obj.x, 25.0, places=3)
        self.assertAlmostEqual(obj.y, 50.0, places=3)

    def test_clamps_negative(self):
        wm = _square_wm()
        _, obj = _add_path_and_token(wm, [(0, 50), (100, 50)],
                                       start_miles=50.0)
        set_progress_miles(wm, obj, -100.0)
        self.assertAlmostEqual(obj.path_progress_miles, 0.0)

    def test_clamps_over_total(self):
        wm = _square_wm()
        _, obj = _add_path_and_token(wm, [(0, 50), (100, 50)])
        set_progress_miles(wm, obj, 9999.0)
        self.assertAlmostEqual(obj.path_progress_miles, 100.0)

    def test_rejects_if_no_path(self):
        wm = _square_wm()
        orphan = MapObject(x=0, y=0, object_type="party_token")
        self.assertFalse(set_progress_miles(wm, orphan, 10.0))


class TestSetProgressFraction(unittest.TestCase):
    def test_half_way(self):
        wm = _square_wm()
        _, obj = _add_path_and_token(wm, [(0, 50), (100, 50)])
        self.assertTrue(set_progress_fraction(wm, obj, 0.5))
        self.assertAlmostEqual(obj.path_progress_miles, 50.0)
        self.assertAlmostEqual(obj.x, 50.0, places=3)

    def test_clamps_out_of_range(self):
        wm = _square_wm()
        _, obj = _add_path_and_token(wm, [(0, 50), (100, 50)])
        set_progress_fraction(wm, obj, 1.7)
        self.assertAlmostEqual(obj.path_progress_miles, 100.0)
        set_progress_fraction(wm, obj, -0.2)
        self.assertAlmostEqual(obj.path_progress_miles, 0.0)


class TestTokenProgress(unittest.TestCase):
    def test_full_snapshot(self):
        wm = _square_wm()
        _, obj = _add_path_and_token(wm, [(0, 50), (100, 50)],
                                       start_miles=40.0)
        snap = token_progress(wm, obj)
        self.assertAlmostEqual(snap["miles_traveled"], 40.0)
        self.assertAlmostEqual(snap["miles_remaining"], 60.0)
        self.assertAlmostEqual(snap["total_miles"], 100.0)
        self.assertAlmostEqual(snap["fraction"], 0.4)
        self.assertFalse(snap["arrived"])
        self.assertAlmostEqual(snap["miles_per_day"], 10.0)
        self.assertAlmostEqual(snap["days_remaining"], 6.0)

    def test_arrived_flag(self):
        wm = _square_wm()
        _, obj = _add_path_and_token(wm, [(0, 50), (100, 50)],
                                       start_miles=100.0)
        snap = token_progress(wm, obj)
        self.assertTrue(snap["arrived"])
        self.assertAlmostEqual(snap["miles_remaining"], 0.0)
        self.assertAlmostEqual(snap["days_remaining"], 0.0)

    def test_empty_when_no_path(self):
        wm = _square_wm()
        orphan = MapObject(x=0, y=0, object_type="party_token")
        self.assertEqual(token_progress(wm, orphan), {})

    def test_speed_mult_honored(self):
        wm = _square_wm()
        _, obj = _add_path_and_token(wm, [(0, 50), (100, 50)],
                                       speed_mult=0.5)
        snap = token_progress(wm, obj)
        self.assertAlmostEqual(snap["miles_per_day"], 5.0)


if __name__ == "__main__":
    unittest.main()
