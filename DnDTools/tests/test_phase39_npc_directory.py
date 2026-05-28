"""Phase 39 — NPC directory: search, links, inventory, copy-to-md.

Audits:

  * search_npcs scores by name > occupation > faction; respects
    location/faction/organisation/tag filters.
  * locate_npc returns by id then exact name then case-insensitive
    name.
  * add_npc_link auto-flips asymmetric kinds (mentor↔protege,
    patron↔subordinate) and stays symmetric for symmetric kinds
    (rival↔rival, family↔family).
  * remove_npc_link clears both ends by default.
  * inventory_detailed add / remove via npc_directory helpers.
  * search_npcs_with_item finds both legacy ``inventory_items`` and
    structured ``inventory_detailed`` carry-items.
  * npc_to_markdown renders identity, faction, organisations,
    links and inventory in a stable form.
  * NPC serialisation round-trips npc_links + inventory_detailed.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import json
import unittest

from data.world import (
    World, NPC, Location,
    _serialize_npc, _deserialize_npc,
)
from data import npc_directory as nd


def _world_with_npcs():
    w = World()
    w.locations["loc_frand"] = Location(
        id="loc_frand", name="Frand", location_type="city")
    w.npcs["n_cal"] = NPC(
        id="n_cal", name="Radiant Calistro",
        race="Human", occupation="Noble patron",
        title="Radiant", alignment="Lawful Evil",
        faction="Brotherhood of Glorious Sun",
        notes="Charming patron of the arts.",
        location_id="loc_frand",
        tags=["brotherhood", "noble"],
    )
    w.npcs["n_vela"] = NPC(
        id="n_vela", name="Lightbringer Vela",
        race="Half-Elf", occupation="Missionary",
        title="Lightbringer",
        faction="Brotherhood of Glorious Sun",
        notes="Recruits orphans.",
        location_id="loc_frand",
        tags=["brotherhood", "priest"],
    )
    w.npcs["n_jolan"] = NPC(
        id="n_jolan", name="Harbourmaster Jolan",
        race="Human", occupation="Harbourmaster",
        faction="Crown",
        location_id="loc_frand",
        tags=["crown", "official"],
    )
    w.npcs["n_garek"] = NPC(
        id="n_garek", name="Garek Hammerfall",
        race="Dwarf", occupation="Blacksmith",
        faction="",
        location_id="loc_frand",
    )
    w.npcs["n_arys"] = NPC(
        id="n_arys", name="Captain Arys Tarn",
        race="Human", occupation="Merchant captain",
        faction="House Tarn",
        location_id="",
    )
    return w


class TestSearchNpcs(unittest.TestCase):
    def setUp(self):
        self.w = _world_with_npcs()

    def test_exact_name_match_scores_highest(self):
        hits = nd.search_npcs(self.w, "Garek Hammerfall")
        self.assertEqual(hits[0].npc.id, "n_garek")
        self.assertGreater(hits[0].score, 10)

    def test_substring_in_faction_finds_brotherhood_npcs(self):
        hits = nd.search_npcs(self.w, "brotherhood")
        names = {h.npc.id for h in hits}
        self.assertIn("n_cal", names)
        self.assertIn("n_vela", names)
        self.assertNotIn("n_jolan", names)

    def test_location_filter(self):
        hits = nd.search_npcs(self.w, "",
                                location_id="loc_frand")
        ids = {h.npc.id for h in hits}
        self.assertEqual(ids, {"n_cal", "n_vela", "n_jolan",
                                 "n_garek"})

    def test_faction_filter(self):
        hits = nd.search_npcs(self.w, "",
                                faction="Crown")
        ids = {h.npc.id for h in hits}
        self.assertEqual(ids, {"n_jolan"})

    def test_tag_filter(self):
        hits = nd.search_npcs(self.w, "",
                                tags=["priest"])
        ids = {h.npc.id for h in hits}
        self.assertEqual(ids, {"n_vela"})

    def test_alive_only_excludes_dead(self):
        self.w.npcs["n_cal"].alive = False
        hits = nd.search_npcs(self.w, "Calistro")
        ids = {h.npc.id for h in hits}
        self.assertNotIn("n_cal", ids)


class TestLocateNpc(unittest.TestCase):
    def setUp(self):
        self.w = _world_with_npcs()

    def test_locate_by_id(self):
        self.assertEqual(
            nd.locate_npc(self.w, "n_cal").id, "n_cal")

    def test_locate_by_exact_name(self):
        self.assertEqual(
            nd.locate_npc(self.w, "Radiant Calistro").id, "n_cal")

    def test_locate_case_insensitive(self):
        self.assertEqual(
            nd.locate_npc(self.w, "radiant calistro").id, "n_cal")

    def test_locate_missing_returns_none(self):
        self.assertIsNone(nd.locate_npc(self.w, "nobody"))


class TestNpcLinks(unittest.TestCase):
    def setUp(self):
        self.w = _world_with_npcs()

    def test_patron_subordinate_auto_flip(self):
        ok = nd.add_npc_link(self.w, "n_cal", "n_vela",
                                kind="patron",
                                notes="Funds the orphanage")
        self.assertTrue(ok)
        out_from_cal = nd.npc_links_of(self.w, "n_cal")
        self.assertEqual(len(out_from_cal), 1)
        self.assertEqual(out_from_cal[0]["kind"], "patron")
        out_from_vela = nd.npc_links_of(self.w, "n_vela")
        self.assertEqual(len(out_from_vela), 1)
        self.assertEqual(out_from_vela[0]["kind"], "subordinate",
                          "patron should auto-flip to subordinate")

    def test_rival_is_symmetric(self):
        nd.add_npc_link(self.w, "n_cal", "n_jolan", kind="rival",
                          notes="Dock politics")
        out_from_cal = nd.npc_links_of(self.w, "n_cal")
        out_from_jolan = nd.npc_links_of(self.w, "n_jolan")
        self.assertEqual(out_from_cal[0]["kind"], "rival")
        self.assertEqual(out_from_jolan[0]["kind"], "rival",
                          "rival should be symmetric")

    def test_mentor_protege_auto_flip(self):
        nd.add_npc_link(self.w, "n_garek", "n_arys",
                          kind="mentor", notes="Trained smithing")
        out_g = nd.npc_links_of(self.w, "n_garek")
        out_a = nd.npc_links_of(self.w, "n_arys")
        self.assertEqual(out_g[0]["kind"], "mentor")
        self.assertEqual(out_a[0]["kind"], "protege")

    def test_remove_link_clears_both_ends(self):
        nd.add_npc_link(self.w, "n_cal", "n_vela", kind="patron")
        self.assertTrue(nd.remove_npc_link(self.w, "n_cal", "n_vela"))
        self.assertEqual(nd.npc_links_of(self.w, "n_cal"), [])
        self.assertEqual(nd.npc_links_of(self.w, "n_vela"), [])

    def test_npcs_linking_to_finds_incoming(self):
        nd.add_npc_link(self.w, "n_cal", "n_vela", kind="patron")
        incoming = nd.npcs_linking_to(self.w, "n_vela")
        self.assertEqual(len(incoming), 1)
        self.assertEqual(incoming[0]["source_id"], "n_cal")

    def test_self_link_refused(self):
        self.assertFalse(
            nd.add_npc_link(self.w, "n_cal", "n_cal", kind="other"))

    def test_unknown_target_refused(self):
        self.assertFalse(
            nd.add_npc_link(self.w, "n_cal", "nobody", kind="rival"))

    def test_invalid_kind_normalised_to_other(self):
        nd.add_npc_link(self.w, "n_cal", "n_vela", kind="space_alien")
        link = nd.npc_links_of(self.w, "n_cal")[0]
        self.assertEqual(link["kind"], "other")


class TestInventoryDetailed(unittest.TestCase):
    def setUp(self):
        self.w = _world_with_npcs()
        self.npc = self.w.npcs["n_cal"]

    def test_add_letter(self):
        entry = nd.add_inventory_item(
            self.npc, "Sealed letter", kind="letter",
            description="Signed V.")
        self.assertEqual(entry["kind"], "letter")
        self.assertEqual(len(self.npc.inventory_detailed), 1)

    def test_remove_item(self):
        nd.add_inventory_item(self.npc, "Key", kind="key")
        self.assertTrue(
            nd.remove_inventory_item(self.npc, "Key"))
        self.assertEqual(self.npc.inventory_detailed, [])

    def test_find_inventory_item(self):
        nd.add_inventory_item(self.npc, "Letter A", kind="letter")
        nd.add_inventory_item(self.npc, "Letter B", kind="letter")
        found = nd.find_inventory_item(self.npc, "Letter B")
        self.assertIsNotNone(found)
        self.assertEqual(found["kind"], "letter")

    def test_search_with_item_covers_legacy_string_list(self):
        self.w.npcs["n_jolan"].inventory_items = [
            "Customs Manifest"]
        hits = nd.search_npcs_with_item(self.w, "customs")
        self.assertEqual([h.id for h in hits], ["n_jolan"])

    def test_search_with_item_covers_structured_list(self):
        nd.add_inventory_item(
            self.w.npcs["n_vela"], "Encoded Letter",
            kind="letter")
        hits = nd.search_npcs_with_item(self.w, "encoded")
        self.assertEqual([h.id for h in hits], ["n_vela"])


class TestNpcMarkdownExport(unittest.TestCase):
    def setUp(self):
        self.w = _world_with_npcs()

    def test_markdown_contains_identity_and_links(self):
        nd.add_npc_link(self.w, "n_cal", "n_vela", kind="patron",
                          notes="Funds orphanage")
        nd.add_inventory_item(
            self.w.npcs["n_cal"], "Sealed Letter",
            kind="letter", description="To Vela")
        md = nd.npc_to_markdown(self.w, self.w.npcs["n_cal"])
        self.assertIn("# Radiant Calistro", md)
        self.assertIn("Brotherhood of Glorious Sun", md)
        # Location resolved by id → name
        self.assertIn("Frand", md)
        self.assertIn("Links", md)
        self.assertIn("Vela", md)
        self.assertIn("Inventory", md)
        self.assertIn("Sealed Letter", md)


class TestSerialisationRoundTrip(unittest.TestCase):
    def test_npc_with_links_and_detailed_inventory(self):
        w = _world_with_npcs()
        nd.add_npc_link(w, "n_cal", "n_vela", kind="patron",
                          notes="Funds her work")
        nd.add_inventory_item(
            w.npcs["n_cal"], "Sealed Letter",
            kind="letter", description="To Vela")
        d = _serialize_npc(w.npcs["n_cal"])
        s = json.dumps(d)
        rt = _deserialize_npc(json.loads(s))
        self.assertEqual(len(rt.npc_links), 1)
        self.assertEqual(rt.npc_links[0]["kind"], "patron")
        self.assertEqual(len(rt.inventory_detailed), 1)
        self.assertEqual(rt.inventory_detailed[0]["kind"], "letter")


# --------------------------------------------------------------------- #
# Pygame-skipped UI smoke tests
# --------------------------------------------------------------------- #
try:
    import pygame  # noqa: F401
    HAS_PYGAME = True
except ImportError:
    HAS_PYGAME = False


@unittest.skipUnless(HAS_PYGAME, "pygame not installed")
class TestNpcSearchModal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import pygame
        pygame.init()
        pygame.display.set_mode((1600, 900))

    def test_open_and_draw(self):
        from states.npc_search_modal import NpcSearchModal
        import pygame
        w = _world_with_npcs()
        m = NpcSearchModal(w, campaign=None)
        m.open()
        m.draw(pygame.display.get_surface())
        # Typing reduces hits
        m.query = "brotherhood"
        self.assertGreater(len(m._hits()), 0)


@unittest.skipUnless(HAS_PYGAME, "pygame not installed")
class TestNpcDetailModal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import pygame
        pygame.init()
        pygame.display.set_mode((1600, 900))

    def test_open_and_draw_with_links(self):
        from states.npc_detail_modal import NpcDetailModal
        import pygame
        w = _world_with_npcs()
        nd.add_npc_link(w, "n_cal", "n_vela", kind="patron")
        nd.add_inventory_item(
            w.npcs["n_cal"], "Sealed Letter", kind="letter")
        m = NpcDetailModal(w, campaign=None, npc=w.npcs["n_cal"])
        m.open()
        m.draw(pygame.display.get_surface())

    def test_add_letter_button_appends_item(self):
        from states.npc_detail_modal import NpcDetailModal
        w = _world_with_npcs()
        m = NpcDetailModal(w, campaign=None, npc=w.npcs["n_cal"])
        m.open()
        m._add_inv("letter")
        self.assertEqual(
            len(w.npcs["n_cal"].inventory_detailed), 1)


if __name__ == "__main__":
    unittest.main()
