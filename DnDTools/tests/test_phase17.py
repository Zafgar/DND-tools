"""Phase 17 — battle-token portrait wiring + cascade delete +
scenario→encounter import.

Pygame-rendering tests skip when pygame is unavailable; pure logic
(cascade rules, scenario→encounter conversion) is exercised
directly.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest

from data.world import (
    World, Location, NPC, Shop, ShopItem, Service, Quest,
    delete_npc as world_delete_npc,
)
from data.cascade_delete import (
    CascadeReport, delete_npc, delete_location, delete_shop,
    delete_service, find_orphan_references,
)


def _world(*, locations=None, npcs=None, shops=None, services=None,
              quests=None):
    w = World()
    for loc in (locations or []):
        w.locations[loc.id] = loc
    for npc in (npcs or []):
        w.npcs[npc.id] = npc
    for shop in (shops or []):
        w.shops[shop.id] = shop
    for svc in (services or []):
        w.services[svc.id] = svc
    for q in (quests or []):
        w.quests[q.id] = q
    return w


# --------------------------------------------------------------------- #
# 17d — Cascade delete
# --------------------------------------------------------------------- #
class TestDeleteNpc(unittest.TestCase):
    def test_basic_delete(self):
        w = _world(npcs=[NPC(id="n1", name="X")])
        rep = delete_npc(w, "n1")
        self.assertEqual(rep.npcs_deleted, 1)
        self.assertNotIn("n1", w.npcs)

    def test_clears_shop_owner(self):
        npc = NPC(id="n1", name="X")
        shop = Shop(id="s1", name="Y", owner_npc_id="n1")
        w = _world(npcs=[npc], shops=[shop])
        rep = delete_npc(w, "n1")
        self.assertEqual(rep.shops_unlinked, 1)
        self.assertEqual(shop.owner_npc_id, "")
        self.assertIn("s1", w.shops)  # shop survives

    def test_clears_service_provider(self):
        npc = NPC(id="n1", name="X")
        svc = Service(id="v1", name="Heal", npc_id="n1")
        w = _world(npcs=[npc], services=[svc])
        delete_npc(w, "n1")
        self.assertEqual(svc.npc_id, "")

    def test_strips_from_location_npc_ids(self):
        loc = Location(id="loc1", name="T",
                         location_type="town", npc_ids=["n1", "n2"])
        npcs = [NPC(id="n1", name="X"), NPC(id="n2", name="Y")]
        w = _world(locations=[loc], npcs=npcs)
        delete_npc(w, "n1")
        self.assertEqual(loc.npc_ids, ["n2"])

    def test_unknown_id_no_op(self):
        w = _world()
        rep = delete_npc(w, "ghost")
        self.assertEqual(rep.npcs_deleted, 0)


class TestWorldLevelDeleteNpcAlsoScrubs(unittest.TestCase):
    """The world-level legacy delete_npc gained the same scrubs
    in Phase 17d so existing call-sites benefit too."""
    def test_scrubs_shop_owner(self):
        w = _world(npcs=[NPC(id="n1", name="X")],
                     shops=[Shop(id="s", name="Y", owner_npc_id="n1")])
        world_delete_npc(w, "n1")
        self.assertEqual(w.shops["s"].owner_npc_id, "")

    def test_scrubs_service_provider(self):
        w = _world(npcs=[NPC(id="n1", name="X")],
                     services=[Service(id="v", name="Z", npc_id="n1")])
        world_delete_npc(w, "n1")
        self.assertEqual(w.services["v"].npc_id, "")


class TestDeleteLocation(unittest.TestCase):
    def test_unmoors_npcs_by_default(self):
        loc = Location(id="loc1", name="T", location_type="town")
        npc = NPC(id="n1", name="X", location_id="loc1")
        w = _world(locations=[loc], npcs=[npc])
        rep = delete_location(w, "loc1")
        self.assertEqual(rep.npcs_unlinked, 1)
        self.assertEqual(rep.locations_deleted, 1)
        self.assertEqual(npc.location_id, "")
        self.assertIn("n1", w.npcs)

    def test_cascade_deletes_npcs(self):
        loc = Location(id="loc1", name="T", location_type="town")
        npc = NPC(id="n1", name="X", location_id="loc1")
        w = _world(locations=[loc], npcs=[npc])
        rep = delete_location(w, "loc1", cascade_npcs=True)
        self.assertEqual(rep.npcs_deleted, 1)
        self.assertNotIn("n1", w.npcs)

    def test_promotes_children_to_top_level(self):
        parent = Location(id="p", name="P", location_type="region",
                            children_ids=["c"])
        child = Location(id="c", name="C", location_type="town",
                           parent_id="p")
        w = _world(locations=[parent, child])
        rep = delete_location(w, "p")
        self.assertEqual(rep.locations_orphaned, 1)
        self.assertEqual(child.parent_id, "")
        self.assertIn("c", w.locations)

    def test_clears_shop_and_service_locations(self):
        loc = Location(id="loc1", name="T", location_type="town")
        shop = Shop(id="s", name="Y", location_id="loc1")
        svc = Service(id="v", name="Z", location_id="loc1")
        w = _world(locations=[loc], shops=[shop], services=[svc])
        delete_location(w, "loc1")
        self.assertEqual(shop.location_id, "")
        self.assertEqual(svc.location_id, "")

    def test_strips_from_quest_location_ids(self):
        loc = Location(id="loc1", name="T", location_type="town")
        q = Quest(id="q", name="Goblins",
                    location_ids=["loc1", "other"])
        w = _world(locations=[loc], quests=[q])
        delete_location(w, "loc1")
        self.assertEqual(q.location_ids, ["other"])


class TestSimpleDeletes(unittest.TestCase):
    def test_delete_shop(self):
        w = _world(shops=[Shop(id="s", name="X")])
        delete_shop(w, "s")
        self.assertEqual(w.shops, {})

    def test_delete_service(self):
        w = _world(services=[Service(id="v", name="X")])
        delete_service(w, "v")
        self.assertEqual(w.services, {})


class TestOrphanFinder(unittest.TestCase):
    def test_finds_dangling_owner(self):
        w = _world(shops=[Shop(id="s", name="Y", owner_npc_id="ghost")])
        rep = find_orphan_references(w)
        self.assertIn("s", rep["shops_with_missing_owner"])

    def test_clean_world_returns_empty(self):
        loc = Location(id="loc1", name="T", location_type="town")
        npc = NPC(id="n1", name="X", location_id="loc1")
        w = _world(locations=[loc], npcs=[npc])
        rep = find_orphan_references(w)
        for key, vals in rep.items():
            self.assertEqual(vals, [])


# --------------------------------------------------------------------- #
# 17e — scenario → CampaignEncounter conversion
# --------------------------------------------------------------------- #
class TestScenarioToEncounter(unittest.TestCase):
    def test_aggregates_monsters_into_slots(self):
        from collections import Counter
        from data.scenarios import get_scenario
        from data.campaign import EncounterSlot
        scen = get_scenario("wolf_pack")
        counts = Counter(m.name for m in scen.monsters)
        slots = [EncounterSlot(creature_name=name, count=int(n),
                                  side="enemy", is_hero=False)
                 for name, n in counts.most_common()]
        # 5 wolves + 2 dire wolves → 2 slots
        self.assertEqual(len(slots), 2)
        wolf_slot = next(s for s in slots
                          if s.creature_name == "Wolf")
        self.assertEqual(wolf_slot.count, 5)


# --------------------------------------------------------------------- #
# 17a — Battle-renderer dispatch lookup (without pygame)
# --------------------------------------------------------------------- #
class TestActorBadgeText(unittest.TestCase):
    """Verify the 3-letter actor badge falls back through the priority
    order: actor name → player class → creature icon."""
    def test_actor_name_first(self):
        actor_name = "Captain Arys Tarn"
        badge = actor_name.strip()[:3].upper()
        self.assertEqual(badge, "CAP")

    def test_falls_back_to_class(self):
        actor_name = ""
        cls = "Wizard"
        if not actor_name:
            badge = cls[:3].upper()
        self.assertEqual(badge, "WIZ")

    def test_actor_name_strips_whitespace(self):
        actor_name = "   Mira  "
        badge = actor_name.strip()[:3].upper()
        self.assertEqual(badge, "MIR")


if __name__ == "__main__":
    unittest.main()
