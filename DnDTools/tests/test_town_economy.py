"""Phase 14a-d — town economy + relationships + summary tests."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest

from data.world import (
    World, Location, NPC, NPCRelationship,
    Shop, ShopItem, Service, Quest,
)
from data.town_economy import (
    buy_from_shop, sell_to_shop, restock_item,
    ATTITUDES, attitude_score, attitude_from_score,
    get_relationship, set_attitude, adjust_attitude,
    list_relationships_to_hero, list_relationships_of_npc,
    town_summary, TownSummary, TransactionResult,
)


def _shop(**kw):
    s = Shop(id=kw.pop("id", "s1"), name=kw.pop("name", "Test Shop"))
    for k, v in kw.items():
        setattr(s, k, v)
    return s


# --------------------------------------------------------------------- #
# Buy / sell
# --------------------------------------------------------------------- #
class TestBuyFromShop(unittest.TestCase):
    def test_basic_buy(self):
        s = _shop(gold=0)
        s.inventory = [ShopItem(item_name="Potion",
                                  base_price_gp=10.0,
                                  quantity=5)]
        r = buy_from_shop(s, "Potion", quantity=2, party_gold=100)
        self.assertTrue(r.success)
        self.assertEqual(r.quantity, 2)
        self.assertEqual(r.price_gp, 20.0)
        self.assertEqual(s.inventory[0].quantity, 3)
        self.assertEqual(s.gold, 20.0)

    def test_unlimited_stock(self):
        s = _shop()
        s.inventory = [ShopItem(item_name="Bread",
                                  base_price_gp=1.0, quantity=-1)]
        r = buy_from_shop(s, "Bread", quantity=10, party_gold=100)
        self.assertTrue(r.success)
        self.assertEqual(s.inventory[0].quantity, -1)

    def test_unknown_item(self):
        s = _shop()
        r = buy_from_shop(s, "Plasma", party_gold=1000)
        self.assertFalse(r.success)
        self.assertIn("not in stock", r.reason)

    def test_insufficient_stock(self):
        s = _shop()
        s.inventory = [ShopItem(item_name="X", base_price_gp=5,
                                  quantity=2)]
        r = buy_from_shop(s, "X", quantity=5, party_gold=1000)
        self.assertFalse(r.success)
        self.assertIn("insufficient", r.reason)

    def test_party_too_poor(self):
        s = _shop()
        s.inventory = [ShopItem(item_name="X", base_price_gp=50,
                                  quantity=1)]
        r = buy_from_shop(s, "X", party_gold=10)
        self.assertFalse(r.success)
        self.assertIn("afford", r.reason)
        self.assertEqual(s.inventory[0].quantity, 1)  # untouched

    def test_quantity_must_be_positive(self):
        s = _shop()
        r = buy_from_shop(s, "X", quantity=0)
        self.assertFalse(r.success)

    def test_sell_markup_applies(self):
        s = _shop(sell_markup=1.5)
        s.inventory = [ShopItem(item_name="X", base_price_gp=10,
                                  quantity=5)]
        r = buy_from_shop(s, "X", quantity=2, party_gold=100)
        self.assertEqual(r.price_gp, 30.0)


class TestSellToShop(unittest.TestCase):
    def test_basic_sell_creates_row(self):
        s = _shop(gold=200, buy_markup=0.5)
        r = sell_to_shop(s, "Helm", quantity=1, base_price_gp=20)
        self.assertTrue(r.success)
        self.assertEqual(r.price_gp, 10.0)
        self.assertEqual(s.gold, 190.0)
        self.assertEqual(len(s.inventory), 1)
        self.assertEqual(s.inventory[0].quantity, 1)

    def test_sell_to_existing_row(self):
        s = _shop(gold=100)
        s.inventory = [ShopItem(item_name="X", base_price_gp=2,
                                  quantity=3)]
        sell_to_shop(s, "X", quantity=2, base_price_gp=2)
        self.assertEqual(s.inventory[0].quantity, 5)

    def test_shop_too_poor(self):
        s = _shop(gold=5, buy_markup=1.0)
        r = sell_to_shop(s, "Big", quantity=1, base_price_gp=100)
        self.assertFalse(r.success)
        self.assertIn("afford", r.reason)
        self.assertEqual(s.gold, 5)


class TestRestock(unittest.TestCase):
    def test_creates_row(self):
        s = _shop()
        restock_item(s, "Rope", quantity=4, base_price_gp=2)
        self.assertEqual(len(s.inventory), 1)
        self.assertEqual(s.inventory[0].quantity, 4)

    def test_appends_to_existing_row(self):
        s = _shop()
        s.inventory = [ShopItem(item_name="X", quantity=1,
                                  base_price_gp=1)]
        restock_item(s, "X", quantity=10)
        self.assertEqual(s.inventory[0].quantity, 11)


# --------------------------------------------------------------------- #
# Relationships
# --------------------------------------------------------------------- #
class TestAttitudeMath(unittest.TestCase):
    def test_score_known(self):
        for name, score in (("hostile", -2), ("unfriendly", -1),
                              ("neutral", 0), ("friendly", 1),
                              ("allied", 2)):
            self.assertEqual(attitude_score(name), score)

    def test_score_unknown_neutral(self):
        self.assertEqual(attitude_score("weird"), 0)

    def test_from_score_clamps(self):
        self.assertEqual(attitude_from_score(99), "allied")
        self.assertEqual(attitude_from_score(-99), "hostile")
        self.assertEqual(attitude_from_score(0), "neutral")


class TestRelationshipUpsert(unittest.TestCase):
    def test_set_creates_row(self):
        npc = NPC(id="n", name="X")
        npc.relationships = []
        rel = set_attitude(npc, "Alara", "friendly", "good ally")
        self.assertEqual(rel.attitude, "friendly")
        self.assertEqual(rel.notes, "good ally")
        self.assertEqual(len(npc.relationships), 1)

    def test_set_updates_existing(self):
        npc = NPC(id="n", name="X")
        npc.relationships = [
            NPCRelationship(hero_name="Alara", attitude="hostile"),
        ]
        set_attitude(npc, "alara", "friendly")
        self.assertEqual(len(npc.relationships), 1)
        self.assertEqual(npc.relationships[0].attitude, "friendly")

    def test_unknown_attitude_falls_back(self):
        npc = NPC(id="n", name="X")
        rel = set_attitude(npc, "Alara", "spicy")
        self.assertEqual(rel.attitude, "neutral")

    def test_get_relationship_case_insensitive(self):
        npc = NPC(id="n", name="X")
        set_attitude(npc, "Alara", "allied")
        self.assertIsNotNone(get_relationship(npc, "ALARA"))
        self.assertIsNotNone(get_relationship(npc, "  alara  "))


class TestAdjustAttitude(unittest.TestCase):
    def test_increment(self):
        npc = NPC(id="n", name="X")
        rel = adjust_attitude(npc, "Alara", +1)
        self.assertEqual(rel.attitude, "friendly")
        rel2 = adjust_attitude(npc, "Alara", +1)
        self.assertEqual(rel2.attitude, "allied")
        rel3 = adjust_attitude(npc, "Alara", +1)
        self.assertEqual(rel3.attitude, "allied")  # clamped

    def test_decrement(self):
        npc = NPC(id="n", name="X")
        rel = adjust_attitude(npc, "Alara", -1)
        self.assertEqual(rel.attitude, "unfriendly")

    def test_appends_note(self):
        npc = NPC(id="n", name="X")
        adjust_attitude(npc, "Alara", -1, append_note="stole gold")
        adjust_attitude(npc, "Alara", -1, append_note="punched in fight")
        rel = get_relationship(npc, "Alara")
        self.assertIn("stole gold", rel.notes)
        self.assertIn("punched in fight", rel.notes)


class TestRelationshipList(unittest.TestCase):
    def test_list_to_hero(self):
        w = World()
        n1 = NPC(id="n1", name="Mira")
        n2 = NPC(id="n2", name="Bran")
        n3 = NPC(id="n3", name="Loner")
        w.npcs = {"n1": n1, "n2": n2, "n3": n3}
        set_attitude(n1, "Alara", "friendly")
        set_attitude(n2, "Alara", "hostile")
        # n3 has no relationship → excluded
        rows = list_relationships_to_hero(w, "Alara")
        names = [npc.name for npc, _r in rows]
        self.assertEqual(set(names), {"Mira", "Bran"})

    def test_list_of_npc(self):
        npc = NPC(id="n", name="X")
        set_attitude(npc, "Alara", "allied")
        set_attitude(npc, "Bran", "hostile")
        rels = list_relationships_of_npc(npc)
        self.assertEqual(len(rels), 2)


# --------------------------------------------------------------------- #
# Town summary
# --------------------------------------------------------------------- #
class TestTownSummary(unittest.TestCase):
    def setUp(self):
        self.w = World()
        self.w.locations["arenhold"] = Location(
            id="arenhold", name="Arenhold",
            location_type="town",
            children_ids=["docks"],
        )
        self.w.locations["docks"] = Location(
            id="docks", name="Docks", location_type="region",
            parent_id="arenhold",
        )
        self.w.npcs["jolan"] = NPC(id="jolan", name="Jolan",
                                    location_id="arenhold")
        self.w.npcs["away"] = NPC(id="away", name="Away",
                                   location_id="elsewhere")
        self.w.shops["s1"] = Shop(id="s1", name="Trading Post",
                                    location_id="arenhold")
        self.w.services["sv1"] = Service(id="sv1",
                                            name="Innkeeper room",
                                            location_id="arenhold")
        self.w.quests["q1"] = Quest(id="q1", name="Goblin Hunt",
                                      location_ids=["arenhold"])

    def test_unknown_location_returns_none(self):
        self.assertIsNone(town_summary(self.w, "nope"))

    def test_summary_aggregates(self):
        s = town_summary(self.w, "arenhold")
        self.assertIsNotNone(s)
        self.assertEqual(s.location.name, "Arenhold")
        self.assertEqual([n.name for n in s.npcs], ["Jolan"])
        self.assertEqual([sh.name for sh in s.shops], ["Trading Post"])
        self.assertEqual([sv.name for sv in s.services],
                          ["Innkeeper room"])
        self.assertEqual([cl.name for cl in s.child_locations],
                          ["Docks"])
        self.assertEqual(s.quest_count, 1)

    def test_excludes_other_locations(self):
        s = town_summary(self.w, "arenhold")
        names = [n.name for n in s.npcs]
        self.assertNotIn("Away", names)


# --------------------------------------------------------------------- #
# Serialization roundtrip
# --------------------------------------------------------------------- #
class TestShopServiceRoundtrip(unittest.TestCase):
    def test_world_roundtrip_keeps_shops(self):
        from data.world import save_world, load_world
        import tempfile
        w = World()
        w.shops["s1"] = Shop(
            id="s1", name="Forge", shop_type="smithy",
            location_id="loc1", owner_npc_id="npc1",
            inventory=[ShopItem(item_name="Mace",
                                  base_price_gp=10, quantity=3)],
            gold=50, sell_markup=1.2, buy_markup=0.4,
            tags=["weapons"],
        )
        w.services["sv1"] = Service(
            id="sv1", name="Healing Potion Brew",
            service_type="healing", location_id="loc1",
            price_gp=25, npc_id="npc1",
        )
        with tempfile.NamedTemporaryFile(suffix=".json",
                                            delete=False, mode="w") as tf:
            path = tf.name
        try:
            save_world(w, path)
            w2 = load_world(path)
            self.assertEqual(w2.shops["s1"].name, "Forge")
            self.assertEqual(w2.shops["s1"].inventory[0].item_name,
                              "Mace")
            self.assertEqual(w2.shops["s1"].sell_markup, 1.2)
            self.assertEqual(w2.services["sv1"].price_gp, 25.0)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
