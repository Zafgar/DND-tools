"""Phase 12b — rectangle select + bulk-edit tests."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest

from data.map_engine import (
    WorldMap, MapLayer, MapObject, AnnotationPath,
)
from data.map_bulk_ops import (
    objects_in_rect, select_in_rect,
    bulk_move, bulk_set_object_type, bulk_add_tags,
    bulk_remove_tags, bulk_set_visibility, bulk_delete,
    selection_summary,
)
from data.path_waypoints import make_path_between


def _wm():
    wm = WorldMap(name="T", width=100, height=100, tile_size=1)
    wm.layers = [MapLayer(id="L0", name="Surface")]
    wm.annotations = []
    return wm


def _settle(wm, oid, x, y, kind="info_pin"):
    obj = MapObject(id=oid, x=x, y=y, object_type=kind, label=oid)
    wm.layers[0].objects.append(obj)
    return obj


class TestSelectInRect(unittest.TestCase):
    def test_inside(self):
        wm = _wm()
        _settle(wm, "A", 10, 10)
        _settle(wm, "B", 50, 50)
        _settle(wm, "C", 90, 90)
        ids = select_in_rect(wm, 0, 0, 60, 60)
        self.assertEqual(ids, {"A", "B"})

    def test_corners_inclusive(self):
        wm = _wm()
        a = _settle(wm, "A", 20, 20)
        ids = select_in_rect(wm, 20, 20, 30, 30)
        self.assertIn("A", ids)

    def test_reverse_corners_ok(self):
        wm = _wm()
        _settle(wm, "A", 50, 50)
        # Drag from bottom-right to top-left
        ids = select_in_rect(wm, 80, 80, 10, 10)
        self.assertEqual(ids, {"A"})

    def test_layer_filter(self):
        wm = _wm()
        wm.layers.append(MapLayer(id="L1", name="Other"))
        _settle(wm, "A", 10, 10)  # on L0
        wm.layers[1].objects.append(
            MapObject(id="B", x=10, y=10,
                       object_type="info_pin", label="B")
        )
        # Only L0
        ids = select_in_rect(wm, 0, 0, 50, 50, layer_idx=0)
        self.assertEqual(ids, {"A"})


class TestBulkMove(unittest.TestCase):
    def test_translates_selected(self):
        wm = _wm()
        _settle(wm, "A", 10, 10)
        _settle(wm, "B", 20, 20)
        _settle(wm, "C", 90, 90)
        bulk_move(wm, {"A", "B"}, dx_pct=5, dy_pct=-3)
        objs = {o.id: (o.x, o.y) for o in wm.layers[0].objects}
        self.assertEqual(objs["A"], (15, 7))
        self.assertEqual(objs["B"], (25, 17))
        self.assertEqual(objs["C"], (90, 90))

    def test_clamps_to_world_bounds(self):
        wm = _wm()
        _settle(wm, "A", 99, 99)
        bulk_move(wm, {"A"}, dx_pct=20, dy_pct=20)
        a = wm.layers[0].objects[0]
        self.assertEqual(a.x, 100)
        self.assertEqual(a.y, 100)

    def test_path_reroutes_after_bulk_move(self):
        wm = _wm()
        a = _settle(wm, "A", 0, 50, kind="city")
        b = _settle(wm, "B", 50, 50, kind="city")
        c = _settle(wm, "C", 100, 50, kind="city")
        path = make_path_between(wm, "A", "B", "C")
        # Move B
        bulk_move(wm, {"B"}, dx_pct=0, dy_pct=-30)
        self.assertEqual(path.points[1], (50, 20))


class TestBulkSetObjectType(unittest.TestCase):
    def test_retypes(self):
        wm = _wm()
        _settle(wm, "A", 10, 10, kind="info_pin")
        _settle(wm, "B", 20, 20, kind="info_pin")
        n = bulk_set_object_type(wm, {"A", "B"}, "city")
        self.assertEqual(n, 2)
        for obj in wm.layers[0].objects:
            self.assertEqual(obj.object_type, "city")

    def test_unknown_type_rejected(self):
        wm = _wm()
        _settle(wm, "A", 10, 10)
        n = bulk_set_object_type(wm, {"A"}, "starbase")
        self.assertEqual(n, 0)
        self.assertEqual(wm.layers[0].objects[0].object_type, "info_pin")


class TestBulkTags(unittest.TestCase):
    def test_add_tags_dedupes(self):
        wm = _wm()
        a = _settle(wm, "A", 10, 10)
        a.tags = ["existing"]
        bulk_add_tags(wm, {"A"}, ["existing", "new"])
        self.assertEqual(a.tags, ["existing", "new"])

    def test_remove_tags(self):
        wm = _wm()
        a = _settle(wm, "A", 10, 10)
        a.tags = ["alpha", "beta", "gamma"]
        bulk_remove_tags(wm, {"A"}, ["beta", "missing"])
        self.assertEqual(a.tags, ["alpha", "gamma"])

    def test_empty_lists_noop(self):
        wm = _wm()
        a = _settle(wm, "A", 10, 10)
        a.tags = ["x"]
        self.assertEqual(bulk_add_tags(wm, {"A"}, []), 0)
        self.assertEqual(bulk_remove_tags(wm, {"A"}, []), 0)
        self.assertEqual(a.tags, ["x"])


class TestBulkVisibility(unittest.TestCase):
    def test_set_dm_only(self):
        wm = _wm()
        _settle(wm, "A", 10, 10)
        _settle(wm, "B", 20, 20)
        bulk_set_visibility(wm, {"A", "B"}, dm_only=True)
        for obj in wm.layers[0].objects:
            self.assertTrue(obj.dm_only)

    def test_set_invisible(self):
        wm = _wm()
        a = _settle(wm, "A", 10, 10)
        bulk_set_visibility(wm, {"A"}, visible=False)
        self.assertFalse(a.visible)

    def test_no_args_is_noop(self):
        wm = _wm()
        a = _settle(wm, "A", 10, 10)
        a.visible = True
        a.dm_only = False
        n = bulk_set_visibility(wm, {"A"})
        self.assertEqual(n, 0)
        self.assertTrue(a.visible)
        self.assertFalse(a.dm_only)


class TestBulkDelete(unittest.TestCase):
    def test_removes_selected(self):
        wm = _wm()
        _settle(wm, "A", 10, 10)
        _settle(wm, "B", 20, 20)
        _settle(wm, "C", 30, 30)
        n = bulk_delete(wm, {"A", "C"})
        self.assertEqual(n, 2)
        ids = {obj.id for obj in wm.layers[0].objects}
        self.assertEqual(ids, {"B"})

    def test_drops_path_when_endpoint_deleted(self):
        wm = _wm()
        _settle(wm, "A", 0, 50, kind="city")
        _settle(wm, "B", 100, 50, kind="city")
        path = make_path_between(wm, "A", "B")
        bulk_delete(wm, {"B"})
        # Path lost endpoint and should have been removed
        self.assertNotIn(path, wm.annotations)

    def test_empty_selection_noop(self):
        wm = _wm()
        _settle(wm, "A", 10, 10)
        n = bulk_delete(wm, set())
        self.assertEqual(n, 0)
        self.assertEqual(len(wm.layers[0].objects), 1)


class TestSummary(unittest.TestCase):
    def test_groups_by_type(self):
        wm = _wm()
        _settle(wm, "A", 10, 10, kind="city")
        _settle(wm, "B", 20, 20, kind="city")
        _settle(wm, "C", 30, 30, kind="info_pin")
        s = selection_summary(wm, {"A", "B", "C"})
        self.assertEqual(s.count, 3)
        self.assertEqual(s.by_type, {"city": 2, "info_pin": 1})

    def test_common_tags_intersection(self):
        wm = _wm()
        a = _settle(wm, "A", 10, 10)
        b = _settle(wm, "B", 20, 20)
        c = _settle(wm, "C", 30, 30)
        a.tags = ["coast", "trade"]
        b.tags = ["coast", "trade", "noble"]
        c.tags = ["coast"]
        s = selection_summary(wm, {"A", "B", "C"})
        self.assertEqual(s.common_tags, ["coast"])

    def test_empty_selection(self):
        wm = _wm()
        s = selection_summary(wm, set())
        self.assertEqual(s.count, 0)
        self.assertEqual(s.by_type, {})
        self.assertEqual(s.common_tags, [])


if __name__ == "__main__":
    unittest.main()
