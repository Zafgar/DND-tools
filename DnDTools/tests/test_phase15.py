"""Phase 15 — party gold/inventory + portrait loader + search helpers
+ widget logic tests.

Pygame-dependent widget rendering is skipped when pygame isn't
available; the data math underneath each widget is exercised via
the underlying Phase 14 helpers, plus a few wiring smoke tests.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import json
import tempfile
import unittest

from data.campaign import Campaign, PartyMember, save_campaign, load_campaign
from data.npc_actor_sync import search_party_members
from data.portrait_loader import (
    PROJECT_ROOT, PORTRAITS_DIR,
    resolve_portrait_path, has_portrait, import_portrait_file,
    load_portrait, clear_cache,
)


# --------------------------------------------------------------------- #
# 15a — Party gold + inventory persistence
# --------------------------------------------------------------------- #
class TestPartyGoldAndInventory(unittest.TestCase):
    def test_default_zero(self):
        c = Campaign()
        self.assertEqual(c.party_gold, 0.0)
        self.assertEqual(c.party_inventory, [])

    def test_pc_gold_default_zero(self):
        m = PartyMember()
        self.assertEqual(m.gold, 0.0)

    def test_persistence_roundtrip(self):
        c = Campaign(name="X", party_gold=125.5,
                       party_inventory=["potion", "rope"])
        c.party.append(PartyMember(hero_data={"name": "Alara"},
                                      gold=15.0))
        with tempfile.NamedTemporaryFile(suffix=".json",
                                            delete=False) as tf:
            path = tf.name
        try:
            save_campaign(c, path)
            c2 = load_campaign(path)
            self.assertEqual(c2.party_gold, 125.5)
            self.assertEqual(c2.party_inventory, ["potion", "rope"])
            self.assertEqual(c2.party[0].gold, 15.0)
        finally:
            os.unlink(path)

    def test_legacy_save_defaults(self):
        """An old campaign JSON without party_gold/party_inventory
        loads cleanly with sensible defaults."""
        legacy = {
            "name": "Old", "description": "x",
            "created": "", "last_modified": "",
            "party": [], "time_of_day": "day",
            "current_area": "", "session_number": 1,
            "encounters": [], "areas": [], "notes": [],
            "world_data": {}, "kingdoms_data": [],
            "primary_world_map_id": "", "active_map_id": "",
            "settings": {},
        }
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w",
                                            delete=False) as tf:
            json.dump(legacy, tf)
            path = tf.name
        try:
            c = load_campaign(path)
            self.assertEqual(c.party_gold, 0.0)
            self.assertEqual(c.party_inventory, [])
        finally:
            os.unlink(path)


# --------------------------------------------------------------------- #
# 15b — Hero search (used by HeroLinkPicker)
# --------------------------------------------------------------------- #
class TestSearchPartyMembers(unittest.TestCase):
    def setUp(self):
        self.c = Campaign()
        self.c.party = [
            PartyMember(hero_data={"name": "Alara",
                                     "character_class": "Ranger"}),
            PartyMember(hero_data={"name": "Bran",
                                     "character_class": "Cleric"}),
            PartyMember(hero_data={"name": "Mira",
                                     "character_class": "Wizard"}),
        ]

    def test_empty_query(self):
        self.assertEqual(len(search_party_members(self.c, "")), 3)

    def test_name_filter(self):
        m = search_party_members(self.c, "alara")
        self.assertEqual(len(m), 1)
        self.assertEqual(m[0].hero_data["name"], "Alara")

    def test_alphabetical_order(self):
        names = [m.hero_data["name"]
                  for m in search_party_members(self.c, "")]
        self.assertEqual(names, sorted(names, key=str.lower))


# --------------------------------------------------------------------- #
# 15c — TownViewWidget tab logic via TownSummary
# --------------------------------------------------------------------- #
class TestTownViewLogic(unittest.TestCase):
    """Sanity that the data the widget reads is shaped correctly."""
    def test_summary_with_shops_and_services(self):
        from data.world import World, Location, NPC, Shop, Service
        from data.town_economy import town_summary
        w = World()
        w.locations["loc1"] = Location(id="loc1", name="X",
                                          location_type="town")
        w.npcs["n1"] = NPC(id="n1", name="A", location_id="loc1")
        w.shops["s1"] = Shop(id="s1", name="Y",
                                location_id="loc1")
        w.services["v1"] = Service(id="v1", name="Z",
                                       location_id="loc1")
        s = town_summary(w, "loc1")
        self.assertEqual(s.location.name, "X")
        self.assertEqual(len(s.npcs), 1)
        self.assertEqual(len(s.shops), 1)
        self.assertEqual(len(s.services), 1)


# --------------------------------------------------------------------- #
# 15d — Shop panel buy/sell logic via Phase 14b helpers
# --------------------------------------------------------------------- #
class TestShopPanelLogic(unittest.TestCase):
    def test_buy_decrements_party_gold_via_helper(self):
        from data.world import Shop, ShopItem
        from data.town_economy import buy_from_shop
        c = Campaign(party_gold=100.0)
        shop = Shop(id="s", name="Forge", gold=0)
        shop.inventory = [ShopItem(item_name="Mace",
                                      base_price_gp=10, quantity=5)]
        result = buy_from_shop(shop, "Mace", quantity=2,
                                  party_gold=c.party_gold)
        self.assertTrue(result.success)
        c.party_gold -= result.price_gp
        self.assertEqual(c.party_gold, 80.0)
        self.assertEqual(shop.gold, 20.0)
        self.assertEqual(shop.inventory[0].quantity, 3)

    def test_sell_credits_party_gold(self):
        from data.world import Shop
        from data.town_economy import sell_to_shop
        c = Campaign(party_gold=10.0)
        shop = Shop(id="s", name="X", gold=200.0, buy_markup=0.5)
        result = sell_to_shop(shop, "Helm", quantity=1,
                                 base_price_gp=20)
        self.assertTrue(result.success)
        c.party_gold += result.price_gp
        self.assertEqual(c.party_gold, 20.0)


# --------------------------------------------------------------------- #
# 15e — Relationship matrix logic
# --------------------------------------------------------------------- #
class TestRelationshipMatrixLogic(unittest.TestCase):
    def test_plus_minus_navigates_attitudes(self):
        from data.world import NPC
        from data.town_economy import (
            adjust_attitude, get_relationship,
        )
        npc = NPC(id="n1", name="X")
        adjust_attitude(npc, "Alara", +1)
        self.assertEqual(get_relationship(npc, "Alara").attitude,
                          "friendly")
        adjust_attitude(npc, "Alara", -2)
        self.assertEqual(get_relationship(npc, "Alara").attitude,
                          "unfriendly")


# --------------------------------------------------------------------- #
# 15f — Portrait loader
# --------------------------------------------------------------------- #
class TestPortraitLoader(unittest.TestCase):
    def setUp(self):
        clear_cache()

    def test_resolve_empty(self):
        self.assertEqual(resolve_portrait_path(""), "")

    def test_resolve_absolute(self):
        self.assertEqual(resolve_portrait_path("/tmp/x.jpg"),
                          "/tmp/x.jpg")

    def test_resolve_relative_uses_project_root(self):
        result = resolve_portrait_path("saves/portraits/x.jpg")
        self.assertTrue(result.startswith(PROJECT_ROOT))
        self.assertTrue(result.endswith("x.jpg"))

    def test_has_portrait_missing(self):
        self.assertFalse(has_portrait("/nonexistent/missing.jpg"))

    def test_has_portrait_existing(self):
        with tempfile.NamedTemporaryFile(suffix=".jpg",
                                            delete=False) as tf:
            tf.write(b"x")
            path = tf.name
        try:
            self.assertTrue(has_portrait(path))
        finally:
            os.unlink(path)

    def test_import_portrait_copies(self):
        with tempfile.NamedTemporaryFile(suffix=".png",
                                            delete=False) as tf:
            tf.write(b"\x89PNG\r\n\x1a\n")
            src = tf.name
        try:
            rel = import_portrait_file(src, name_hint="Mira")
            self.assertTrue(rel)
            self.assertTrue(rel.endswith(".png"))
            self.assertIn("Mira", rel)
            full = os.path.join(PROJECT_ROOT, rel)
            self.assertTrue(os.path.isfile(full))
            os.unlink(full)
        finally:
            os.unlink(src)

    def test_load_portrait_missing_returns_none(self):
        self.assertIsNone(load_portrait("/no/such/file.jpg"))


if __name__ == "__main__":
    unittest.main()
