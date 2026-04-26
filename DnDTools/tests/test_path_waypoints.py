"""Phase 10b — path waypoint chaining tests."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest

from data.map_engine import (
    WorldMap, MapLayer, MapObject, AnnotationPath,
)
from data.path_waypoints import (
    rebuild_points_from_waypoints, add_waypoint, remove_waypoint,
    insert_waypoint_between, on_object_moved, on_object_deleted,
    waypoint_objects, make_path_between,
)


def _wm():
    wm = WorldMap(name="T", width=100, height=100, tile_size=1)
    wm.layers = [MapLayer(id="L0", name="Surface")]
    wm.annotations = []
    return wm


def _settle(wm, oid, x, y, name=""):
    obj = MapObject(id=oid, x=x, y=y, object_type="city",
                    label=name or oid)
    wm.layers[0].objects.append(obj)
    return obj


class TestMakePath(unittest.TestCase):
    def test_two_settlements(self):
        wm = _wm()
        a = _settle(wm, "A", 10, 50)
        c = _settle(wm, "C", 90, 50)
        path = make_path_between(wm, "A", "C", name="Trade Road")
        self.assertIsNotNone(path)
        self.assertEqual(path.waypoint_object_ids, ["A", "C"])
        self.assertEqual(path.points, [(10, 50), (90, 50)])
        self.assertIn(path, wm.annotations)

    def test_one_endpoint_returns_none(self):
        wm = _wm()
        _settle(wm, "A", 10, 50)
        self.assertIsNone(make_path_between(wm, "A"))

    def test_unknown_id_skipped(self):
        wm = _wm()
        _settle(wm, "A", 10, 50)
        _settle(wm, "B", 50, 50)
        path = make_path_between(wm, "A", "ghost", "B")
        self.assertEqual(path.waypoint_object_ids, ["A", "B"])


class TestAddWaypoint(unittest.TestCase):
    def test_append(self):
        wm = _wm()
        _settle(wm, "A", 10, 50); _settle(wm, "B", 50, 50)
        path = make_path_between(wm, "A", "B")
        _settle(wm, "C", 90, 50)
        self.assertTrue(add_waypoint(wm, path, "C"))
        self.assertEqual(path.waypoint_object_ids, ["A", "B", "C"])
        self.assertEqual(path.points[-1], (90, 50))

    def test_insert_at_position(self):
        wm = _wm()
        _settle(wm, "A", 10, 50); _settle(wm, "B", 90, 50)
        path = make_path_between(wm, "A", "B")
        _settle(wm, "M", 50, 50)
        add_waypoint(wm, path, "M", position=1)
        self.assertEqual(path.waypoint_object_ids, ["A", "M", "B"])

    def test_duplicate_rejected(self):
        wm = _wm()
        _settle(wm, "A", 10, 50); _settle(wm, "B", 50, 50)
        path = make_path_between(wm, "A", "B")
        self.assertFalse(add_waypoint(wm, path, "A"))


class TestInsertBetween(unittest.TestCase):
    def test_picks_smallest_detour(self):
        """A → C path; insert M closer to mid → goes between A and C."""
        wm = _wm()
        _settle(wm, "A", 0, 50)
        _settle(wm, "C", 100, 50)
        path = make_path_between(wm, "A", "C")
        _settle(wm, "M", 50, 55)
        self.assertTrue(insert_waypoint_between(wm, path, "M"))
        self.assertEqual(path.waypoint_object_ids, ["A", "M", "C"])

    def test_insert_picks_correct_segment(self):
        """A → C → E; insert D between C and E (closer)."""
        wm = _wm()
        _settle(wm, "A", 0, 50)
        _settle(wm, "C", 50, 50)
        _settle(wm, "E", 100, 50)
        path = make_path_between(wm, "A", "C", "E")
        _settle(wm, "D", 75, 50)
        insert_waypoint_between(wm, path, "D")
        self.assertEqual(path.waypoint_object_ids, ["A", "C", "D", "E"])


class TestRemoveWaypoint(unittest.TestCase):
    def test_drops_middle(self):
        wm = _wm()
        for oid, x in (("A", 0), ("B", 50), ("C", 100)):
            _settle(wm, oid, x, 50)
        path = make_path_between(wm, "A", "B", "C")
        self.assertTrue(remove_waypoint(wm, path, "B"))
        self.assertEqual(path.waypoint_object_ids, ["A", "C"])
        self.assertEqual(path.points, [(0, 50), (100, 50)])


class TestObjectMoved(unittest.TestCase):
    def test_moving_a_waypoint_reroutes(self):
        wm = _wm()
        a = _settle(wm, "A", 0, 50)
        b = _settle(wm, "B", 50, 50)
        c = _settle(wm, "C", 100, 50)
        path = make_path_between(wm, "A", "B", "C")
        # User drags B
        b.x = 50; b.y = 10
        n = on_object_moved(wm, "B")
        self.assertEqual(n, 1)
        self.assertEqual(path.points, [(0, 50), (50, 10), (100, 50)])

    def test_moving_unrelated_object_doesnt_touch_path(self):
        wm = _wm()
        a = _settle(wm, "A", 0, 50); _settle(wm, "B", 50, 50)
        path = make_path_between(wm, "A", "B")
        unrelated = _settle(wm, "X", 80, 80)
        unrelated.x = 0; unrelated.y = 0
        n = on_object_moved(wm, "X")
        self.assertEqual(n, 0)


class TestObjectDeleted(unittest.TestCase):
    def test_endpoint_deleted_drops_path(self):
        wm = _wm()
        _settle(wm, "A", 0, 50)
        _settle(wm, "B", 100, 50)
        path = make_path_between(wm, "A", "B")
        rep = on_object_deleted(wm, "B")
        self.assertEqual(rep["removed"], 1)
        self.assertIn(path.id, rep["removed_path_ids"])
        self.assertEqual(wm.annotations, [])

    def test_middle_waypoint_deleted_keeps_path(self):
        wm = _wm()
        for oid, x in (("A", 0), ("M", 50), ("Z", 100)):
            _settle(wm, oid, x, 50)
        path = make_path_between(wm, "A", "M", "Z")
        rep = on_object_deleted(wm, "M")
        self.assertEqual(rep["removed"], 0)
        self.assertEqual(rep["rebuilt"], 1)
        self.assertEqual(path.waypoint_object_ids, ["A", "Z"])
        self.assertEqual(path.points, [(0, 50), (100, 50)])

    def test_unrelated_delete_noop(self):
        wm = _wm()
        _settle(wm, "A", 0, 50); _settle(wm, "B", 100, 50)
        make_path_between(wm, "A", "B")
        rep = on_object_deleted(wm, "ghost")
        self.assertEqual(rep["rebuilt"], 0)
        self.assertEqual(rep["removed"], 0)


class TestSerialization(unittest.TestCase):
    def test_waypoints_and_opacity_roundtrip(self):
        from data.map_engine import _path_to_dict, _path_from_dict
        wm = _wm()
        _settle(wm, "A", 0, 50); _settle(wm, "B", 100, 50)
        p = make_path_between(wm, "A", "B")
        p.opacity = 0.6
        d = _path_to_dict(p)
        self.assertEqual(d["waypoint_object_ids"], ["A", "B"])
        self.assertAlmostEqual(d["opacity"], 0.6)
        p2 = _path_from_dict(d)
        self.assertEqual(p2.waypoint_object_ids, ["A", "B"])
        self.assertAlmostEqual(p2.opacity, 0.6)

    def test_legacy_path_default_opacity(self):
        from data.map_engine import _path_from_dict
        p = _path_from_dict({"id": "P", "name": "x",
                              "points": [[0, 0], [10, 10]]})
        self.assertAlmostEqual(p.opacity, 0.85)
        self.assertEqual(p.waypoint_object_ids, [])


if __name__ == "__main__":
    unittest.main()
