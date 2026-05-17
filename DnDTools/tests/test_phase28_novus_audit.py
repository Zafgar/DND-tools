"""Phase 28 — Novus Somnium integrity audit.

Locks the contract that the starter campaign is internally consistent:

  * ``world_data`` is populated and rehydrates cleanly.
  * Every kingdom city with a ``location_id`` resolves to a real
    Location in the World.
  * The Frand starter NPCs are present and physically at Frand.
  * The starter shop and bank exist and are linked to Frand.
  * Brotherhood members whose ``npc_name`` matches a starter NPC
    name have their ``npc_id`` wired.
  * Quest reverse lookups for the starter quests return a hit.
  * Wealth aggregator returns >0 for Frand once the cross-links are
    in place.

These are the invariants the audit revealed weren't enforced. If we
break any of them the test suite stops the regression at source.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import unittest

from data.novus_somnium import build_novus_somnium
from data import kingdoms as kg
from data import organizations as orgs
from data import wealth as wlth
from data import quest_log as ql
from data.world import (
    World, _deserialize_location, _deserialize_npc, _deserialize_quest,
    _deserialize_shop, _deserialize_service,
)


def _rehydrate(camp) -> World:
    """Mirror the campaign-manager's _load_world_from_campaign path."""
    wd = camp.world_data or {}
    return World(
        name=wd.get("name", camp.name),
        description=wd.get("description", ""),
        locations={k: _deserialize_location(v)
                    for k, v in wd.get("locations", {}).items()},
        npcs={k: _deserialize_npc(v) for k, v in wd.get("npcs", {}).items()},
        quests={k: _deserialize_quest(v)
                  for k, v in wd.get("quests", {}).items()},
        shops={k: _deserialize_shop(v)
                 for k, v in wd.get("shops", {}).items()},
        services={k: _deserialize_service(v)
                    for k, v in wd.get("services", {}).items()},
        next_id=wd.get("next_id", 1),
    )


class TestNovusSomniumWorldIsPopulated(unittest.TestCase):
    def setUp(self):
        self.camp = build_novus_somnium()
        self.world = _rehydrate(self.camp)

    def test_world_data_is_non_empty(self):
        self.assertTrue(self.camp.world_data,
                          "Novus Somnium should ship with a populated World")

    def test_one_country_location_per_kingdom(self):
        names = {loc.name for loc in self.world.locations.values()
                  if loc.location_type == "country"}
        for required in ("Tarmaas", "Fundarla", "Smardu",
                          "Aterterra", "Oblitus"):
            self.assertIn(required, names)

    def test_frand_is_a_city_under_tarmaas(self):
        frand = self.world.locations.get("loc_frand")
        self.assertIsNotNone(frand, "Frand location missing")
        self.assertEqual(frand.location_type, "city")
        self.assertEqual(frand.parent_id, "loc_tarmaas")
        self.assertGreater(frand.population, 0)

    def test_starter_npcs_present_in_frand(self):
        frand = self.world.locations["loc_frand"]
        npc_ids = set(frand.npc_ids)
        for required in ("npc_calistro", "npc_vela", "npc_smith",
                          "npc_jolan", "npc_arys"):
            self.assertIn(required, npc_ids,
                            f"{required} should be at Frand")
            self.assertIn(required, self.world.npcs)

    def test_starter_npcs_carry_coins(self):
        for nid in ("npc_calistro", "npc_smith", "npc_jolan"):
            npc = self.world.npcs[nid]
            self.assertGreater(wlth.npc_coins(npc).total_cp(), 0,
                                f"{nid} should have wealth seeded")

    def test_starter_shop_and_bank_at_frand(self):
        shop = self.world.shops.get("shop_anvil_star")
        self.assertIsNotNone(shop)
        self.assertEqual(shop.location_id, "loc_frand")
        self.assertGreater(len(shop.inventory), 0,
                            "Anvil & Star should ship pre-stocked")
        bank = self.world.shops.get("shop_counting_house")
        self.assertIsNotNone(bank)
        self.assertTrue(bank.is_bank)
        self.assertGreater(bank.bank_holdings_gp, 0)

    def test_starter_quests_exist_and_pinned(self):
        for qid in ("quest_anvil_blade",
                     "quest_brotherhood_recruits"):
            q = self.world.quests.get(qid)
            self.assertIsNotNone(q)
            self.assertEqual(q.map_pin_location_id, "loc_frand")

    def test_anvil_quest_has_smith_giver(self):
        q = self.world.quests["quest_anvil_blade"]
        self.assertEqual(q.giver_npc_id, "npc_smith")
        self.assertIn("shop_anvil_star", q.shop_ids)


class TestKingdomToWorldCrossLinks(unittest.TestCase):
    def setUp(self):
        self.camp = build_novus_somnium()
        self.world = _rehydrate(self.camp)

    def test_frand_city_has_location_id(self):
        frand_city = kg.find_city(self.camp, "tarmaas", "frand")
        self.assertEqual(frand_city.location_id, "loc_frand")

    def test_kingdom_wealth_aggregates_real_data(self):
        tarmaas = kg.find_kingdom(self.camp, "tarmaas")
        frand_city = next(c for c in tarmaas.cities
                           if c.key == "frand")
        breakdown = wlth.city_wealth_breakdown(self.world, frand_city)
        # Crown + NPC pile + shop pile + bank deposits all > 0 now
        self.assertGreater(breakdown["crown"], 0)
        self.assertGreater(breakdown["npcs"], 0)
        self.assertGreater(breakdown["shops"], 0)
        self.assertGreater(breakdown["banks"], 0)


class TestBrotherhoodIsLinkedToFrand(unittest.TestCase):
    def setUp(self):
        self.camp = build_novus_somnium()

    def test_calistro_member_linked_to_npc(self):
        b = orgs.find_organisation(self.camp,
                                       "brotherhood_of_glorious_sun")
        cal = next(m for m in b.members
                    if m.npc_name == "Radiant Calistro")
        self.assertEqual(cal.npc_id, "npc_calistro")

    def test_vela_member_linked_to_npc(self):
        b = orgs.find_organisation(self.camp,
                                       "brotherhood_of_glorious_sun")
        vela = next(m for m in b.members
                     if m.npc_name == "Lightbringer Vela")
        self.assertEqual(vela.npc_id, "npc_vela")

    def test_organisation_lookup_for_calistro(self):
        hits = orgs.organisations_for_npc(self.camp, "npc_calistro")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].key, "brotherhood_of_glorious_sun")


class TestQuestReverseLookups(unittest.TestCase):
    def setUp(self):
        self.camp = build_novus_somnium()
        self.world = _rehydrate(self.camp)

    def test_quests_pinned_at_frand_active_only(self):
        hits = ql.quests_pinned_at(self.world, "loc_frand")
        # The Anvil quest is active; the Brotherhood quest is
        # not_started so it doesn't render on the map.
        ids = {q.id for q in hits}
        self.assertIn("quest_anvil_blade", ids)
        self.assertNotIn("quest_brotherhood_recruits", ids,
                           "not_started quests should not show on map")

    def test_quests_for_smith(self):
        hits = ql.quests_for_npc(self.world, "npc_smith")
        self.assertIn("quest_anvil_blade", {q.id for q in hits})

    def test_quests_for_jolan(self):
        hits = ql.quests_for_npc(self.world, "npc_jolan")
        self.assertIn("quest_brotherhood_recruits",
                       {q.id for q in hits})

    def test_quests_for_shop_anvil(self):
        hits = ql.quests_for_shop(self.world, "shop_anvil_star")
        self.assertEqual({q.id for q in hits}, {"quest_anvil_blade"})


class TestRoundTripIsStable(unittest.TestCase):
    """Phase 28 — save/load preserves every cross-link we just wired."""
    def test_round_trip_preserves_world_and_links(self):
        import json
        from data.campaign import save_campaign, load_campaign
        import tempfile, os
        camp = build_novus_somnium()
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "novus.json")
            save_campaign(camp, path)
            loaded = load_campaign(path)
        # World data preserved
        self.assertTrue(loaded.world_data)
        self.assertEqual(len(loaded.world_data["locations"]),
                          len(camp.world_data["locations"]))
        self.assertEqual(len(loaded.world_data["npcs"]),
                          len(camp.world_data["npcs"]))
        # Kingdom city's location_id survives
        loaded_kingdoms = loaded.kingdoms_data
        tarmaas = next(k for k in loaded_kingdoms
                        if k["key"] == "tarmaas")
        frand = next(c for c in tarmaas["cities"]
                       if c["key"] == "frand")
        self.assertEqual(frand["location_id"], "loc_frand")
        # Brotherhood members keep their npc_id wiring
        b = next(o for o in loaded.organisations_data
                  if o["key"] == "brotherhood_of_glorious_sun")
        cal = next(m for m in b["members"]
                    if m["npc_name"] == "Radiant Calistro")
        self.assertEqual(cal["npc_id"], "npc_calistro")


if __name__ == "__main__":
    unittest.main()
