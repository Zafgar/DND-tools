"""Phase 12d — post-import auto-link tests."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest

from data.world import World, NPC, Location
from data.map_engine import WorldMap, MapLayer, MapObject
from data.actors import ActorRegistry
from data.text_import import import_text
from data.import_link import link_all, LinkReport


SAMPLE = """\
## Locations
- Arenhold (town): Port-city.
- Vardun Keep (fort): Castle on the road.

## NPCs
- Lady Mira Vardun (Castellan, Vardun Keep): Stern.
- Harbourmaster Jolan Ves (Harbourmaster, Arenhold): Tracks ships.
"""


def _wm():
    wm = WorldMap(name="T", width=100, height=100, tile_size=1)
    wm.layers = [MapLayer(id="L0", name="Surface")]
    wm.annotations = []
    return wm


class TestLinkAll(unittest.TestCase):
    def test_imports_then_links(self):
        w = World()
        import_text(w, SAMPLE)
        wm = _wm()
        reg = ActorRegistry()
        rep = link_all(w, wm, reg)
        # 2 NPCs → 2 actors
        self.assertEqual(rep.actors_created, 2)
        self.assertEqual(reg.list_by_kind("npc")[0].kind, "npc")
        # 2 settlements → 2 tokens placed
        self.assertEqual(rep.locations_placed, 2)
        self.assertEqual(len(wm.layers[0].objects), 2)
        for obj in wm.layers[0].objects:
            self.assertTrue(obj.linked_location_id)

    def test_token_label_matches_actor_name_link(self):
        w = World()
        reg = ActorRegistry()
        actor = reg.create("Mira Vardun", kind="npc")
        wm = _wm()
        wm.layers[0].objects.append(
            MapObject(id="T1", x=10, y=10, label="Mira Vardun",
                       object_type="info_pin")
        )
        rep = link_all(w, wm, reg)
        self.assertEqual(rep.tokens_linked_to_actor, 1)
        self.assertEqual(wm.layers[0].objects[0].actor_id, actor.id)

    def test_idempotent_re_link(self):
        w = World()
        import_text(w, SAMPLE)
        reg = ActorRegistry()
        wm = _wm()
        link_all(w, wm, reg)
        rep2 = link_all(w, wm, reg)
        # Already-linked NPCs: actors_synced > 0, actors_created == 0
        self.assertEqual(rep2.actors_created, 0)
        self.assertEqual(rep2.actors_synced, 2)
        # Already-placed locations: nothing more to add
        self.assertEqual(rep2.locations_placed, 0)

    def test_skips_world_map_when_none(self):
        w = World()
        import_text(w, SAMPLE)
        reg = ActorRegistry()
        rep = link_all(w, world_map=None, registry=reg)
        # Actors still created, no token placement
        self.assertEqual(rep.actors_created, 2)
        self.assertEqual(rep.locations_placed, 0)

    def test_skips_actors_when_no_registry(self):
        w = World()
        import_text(w, SAMPLE)
        wm = _wm()
        rep = link_all(w, world_map=wm, registry=None)
        self.assertEqual(rep.actors_created, 0)
        self.assertEqual(rep.locations_placed, 2)

    def test_settlement_filter_excludes_wilderness(self):
        w = World()
        import_text(w, "## Locations\n"
                       "- Arenhold (town): X.\n"
                       "- Silverbough (wilderness): Trees.\n")
        wm = _wm()
        rep = link_all(w, wm, ActorRegistry())
        # Only 'Arenhold' is a settlement → 1 token placed
        self.assertEqual(rep.locations_placed, 1)


class TestLinkReportSummary(unittest.TestCase):
    def test_no_changes(self):
        rep = LinkReport()
        self.assertEqual(rep.summary(), "no links")

    def test_describes_changes(self):
        rep = LinkReport(actors_created=2, locations_placed=3)
        s = rep.summary()
        self.assertIn("actors", s)
        self.assertIn("tokens", s)


if __name__ == "__main__":
    unittest.main()
