"""Phase 13c — NPC link picker tests."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest

from data.world import World, NPC
from data.map_engine import MapObject
from states.npc_link_picker import (
    NPCLinkPicker, link_npc_to_object_callback,
)


def _world(*npcs):
    w = World()
    for n in npcs:
        w.npcs[n.id] = n
    return w


class TestPickerLifecycle(unittest.TestCase):
    def setUp(self):
        self.w = _world(
            NPC(id="n1", name="Alara", occupation="Ranger",
                  faction="Greenstone"),
            NPC(id="n2", name="Bran", occupation="Castellan",
                  faction="Vardun"),
            NPC(id="n3", name="Mira", occupation="Merchant"),
        )
        self.picked = []
        self.picker = NPCLinkPicker(
            self.w, on_pick=lambda x: self.picked.append(x),
        )

    def test_starts_closed(self):
        self.assertFalse(self.picker.is_open)

    def test_open_lists_all_npcs(self):
        self.picker.open(anchor_rect=(0, 0, 200, 30))
        self.assertEqual(len(self.picker._dropdown._results), 3)

    def test_query_filters(self):
        self.picker.open(anchor_rect=(0, 0, 200, 30))
        self.picker._dropdown.set_query("alara")
        self.assertEqual(len(self.picker._dropdown._results), 1)
        self.assertEqual(self.picker._dropdown._results[0].id, "n1")

    def test_excluded_ids_skipped(self):
        self.picker.open(anchor_rect=(0, 0, 200, 30),
                           exclude_ids={"n1"})
        ids = [r.id for r in self.picker._dropdown._results]
        self.assertNotIn("n1", ids)
        self.assertIn("n2", ids)

    def test_pick_fires_on_pick(self):
        self.picker.open(anchor_rect=(0, 0, 200, 30))
        # move_highlight from -1 (no selection) advances to 0 (n1).
        # Move again to land on index 1 → n2.
        self.picker._dropdown.move_highlight(+1)
        self.picker._dropdown.move_highlight(+1)
        self.picker._dropdown.commit_highlighted()
        self.assertEqual(self.picked, ["n2"])
        self.assertFalse(self.picker.is_open)

    def test_close_without_commit_yields_none(self):
        self.picker.open(anchor_rect=(0, 0, 200, 30))
        self.picker.close(commit=False)
        self.assertEqual(self.picked, [None])

    def test_sub_label_shows_occupation_and_faction(self):
        self.picker.open(anchor_rect=(0, 0, 200, 30))
        entry = next(e for e in self.picker._dropdown._results
                     if e.id == "n1")
        self.assertIn("Ranger", entry.sub)
        self.assertIn("Greenstone", entry.sub)


class TestLinkCallback(unittest.TestCase):
    def test_appends_to_linked_npc_ids(self):
        obj = MapObject(x=0, y=0, object_type="info_pin")
        cb = link_npc_to_object_callback(obj)
        cb("n1")
        self.assertEqual(obj.linked_npc_ids, ["n1"])

    def test_dedupe(self):
        obj = MapObject(x=0, y=0, object_type="info_pin",
                         linked_npc_ids=["n1"])
        cb = link_npc_to_object_callback(obj)
        cb("n1")  # already there
        cb("n2")
        self.assertEqual(obj.linked_npc_ids, ["n1", "n2"])

    def test_none_is_noop(self):
        obj = MapObject(x=0, y=0, object_type="info_pin",
                         linked_npc_ids=["n1"])
        cb = link_npc_to_object_callback(obj)
        cb(None)
        self.assertEqual(obj.linked_npc_ids, ["n1"])


class TestSubLabels(unittest.TestCase):
    def test_no_occupation_no_faction(self):
        w = _world(NPC(id="n1", name="X"))
        picker = NPCLinkPicker(w, on_pick=lambda x: None)
        picker.open(anchor_rect=(0, 0, 200, 30))
        entry = picker._dropdown._results[0]
        self.assertEqual(entry.sub, "")

    def test_only_occupation(self):
        w = _world(NPC(id="n1", name="X", occupation="Bard"))
        picker = NPCLinkPicker(w, on_pick=lambda x: None)
        picker.open(anchor_rect=(0, 0, 200, 30))
        entry = picker._dropdown._results[0]
        self.assertEqual(entry.sub, "Bard")


if __name__ == "__main__":
    unittest.main()
