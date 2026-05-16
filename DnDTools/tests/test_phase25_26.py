"""Phase 25 — shop presets + 5e price book:

  25a: scroll prices, magic-item bands, spellcasting services.
  25b: shop_preset_library merges items into a Shop.

Phase 26 — quest tracking:

  26a: Quest extra link fields + log + serialisation round-trip.
  26b: quest_log helpers (pay/receive/kill/deliver/complete + lookups).
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import json
import unittest

from data.price_book import (
    scroll_centre_price, scroll_price_for_spell,
    magic_item_centre_price, service_price,
    bundle_total_gp, list_phb_bundles,
)
from data.shop_preset_library import (
    list_presets_for, preset_items, apply_preset_to_shop,
    temple_service_presets,
)
from data.world import (
    World, Shop, NPC, Quest, QuestObjective, QuestLogEntry,
    _serialize_quest, _deserialize_quest,
)
from data import quest_log as ql


# --------------------------------------------------------------------- #
# 25a — price book
# --------------------------------------------------------------------- #
class TestPriceBook(unittest.TestCase):
    def test_scroll_centre_increases_with_level(self):
        cantrip = scroll_centre_price(0)
        third = scroll_centre_price(3)
        ninth = scroll_centre_price(9)
        self.assertLess(cantrip, third)
        self.assertLess(third, ninth)

    def test_scroll_price_for_known_spell(self):
        # Fireball is 3rd level → 500–750 → centre 625
        self.assertEqual(scroll_price_for_spell("Fireball"), 625)

    def test_scroll_price_for_unknown_spell(self):
        # Unknown → falls back to 50
        self.assertEqual(scroll_price_for_spell("Made Up Spell"), 50)

    def test_magic_item_band(self):
        self.assertEqual(magic_item_centre_price("common"), 75)
        self.assertEqual(magic_item_centre_price("uncommon"), 300)
        self.assertGreater(magic_item_centre_price("legendary"),
                            magic_item_centre_price("very rare"))

    def test_spellcasting_services(self):
        self.assertEqual(service_price("Lesser Restoration"), 40)
        self.assertEqual(service_price("Raise Dead"), 1250)

    def test_phb_bundle_total_positive(self):
        for key in list_phb_bundles():
            total = bundle_total_gp(key)
            self.assertGreater(total, 0,
                                f"{key} should have a non-zero bundle price")


# --------------------------------------------------------------------- #
# 25b — shop preset library
# --------------------------------------------------------------------- #
class TestShopPresets(unittest.TestCase):
    def test_blacksmith_basic_present(self):
        keys = list_presets_for("blacksmith")
        self.assertIn("basic", keys)

    def test_preset_items_blacksmith_has_weapons(self):
        rows = preset_items("blacksmith", "basic")
        self.assertGreater(len(rows), 0)
        names = {r[0] for r in rows}
        self.assertIn("Dagger", names)
        self.assertIn("Longsword", names)

    def test_library_tier3_includes_high_level_scrolls(self):
        rows = preset_items("library", "library_tier3")
        # Should reach at least 7th-level scrolls
        prices = [r[2] for r in rows]
        self.assertGreater(max(prices), 5000)

    def test_apply_preset_to_empty_shop(self):
        shop = Shop(id="s", name="Smithy", shop_type="blacksmith")
        added = apply_preset_to_shop(shop, "basic")
        self.assertGreater(added, 0)
        names = {it.item_name for it in shop.inventory}
        self.assertIn("Dagger", names)

    def test_apply_preset_merges_quantities(self):
        shop = Shop(id="s", name="Smithy", shop_type="blacksmith")
        apply_preset_to_shop(shop, "basic")
        before = {it.item_name: it.quantity for it in shop.inventory}
        apply_preset_to_shop(shop, "basic")  # re-apply
        for it in shop.inventory:
            # Quantity should at least have stacked, not duplicated rows
            self.assertGreaterEqual(it.quantity, before.get(it.item_name, 0))

    def test_apply_preset_replace_wipes_first(self):
        shop = Shop(id="s", name="Smithy", shop_type="blacksmith")
        apply_preset_to_shop(shop, "basic")
        apply_preset_to_shop(shop, "stocked", replace=True)
        # After replace, "stocked"-only items appear
        names = {it.item_name for it in shop.inventory}
        self.assertIn("Greatsword", names)

    def test_temple_services_returns_rows(self):
        rows = temple_service_presets()
        self.assertGreater(len(rows), 0)
        names = {r[0] for r in rows}
        self.assertIn("Lesser Restoration", names)


# --------------------------------------------------------------------- #
# 26a — Quest model extensions + serialisation
# --------------------------------------------------------------------- #
class TestQuestModelExtensions(unittest.TestCase):
    def test_new_fields_have_defaults(self):
        q = Quest(id="q1", name="Test")
        self.assertEqual(q.shop_ids, [])
        self.assertEqual(q.monster_names, [])
        self.assertEqual(q.map_pin_location_id, "")
        self.assertEqual(q.log, [])

    def test_quest_round_trips_extra_fields(self):
        q = Quest(id="q1", name="Bandit Hunt")
        q.shop_ids = ["s1"]
        q.monster_names = ["Bandit", "Bandit Captain"]
        q.map_pin_location_id = "loc_outpost"
        q.log.append(QuestLogEntry(
            timestamp="S3 D5", kind="kill",
            description="Killed bandit captain",
            monster_name="Bandit Captain"))
        d = _serialize_quest(q)
        s = json.dumps(d)
        q2 = _deserialize_quest(json.loads(s))
        self.assertEqual(q2.shop_ids, ["s1"])
        self.assertEqual(q2.monster_names, ["Bandit", "Bandit Captain"])
        self.assertEqual(q2.map_pin_location_id, "loc_outpost")
        self.assertEqual(len(q2.log), 1)
        self.assertEqual(q2.log[0].kind, "kill")


# --------------------------------------------------------------------- #
# 26b — quest_log helpers
# --------------------------------------------------------------------- #
class _Stub:
    def __init__(self):
        self.party_gold = 50.0
        self.session_number = 3
        self.in_game_day = 5


class TestQuestLogHelpers(unittest.TestCase):
    def setUp(self):
        self.q = Quest(id="q1", name="Forge Sword")
        self.camp = _Stub()

    def test_log_event_appends_with_timestamp(self):
        ql.log_event(self.q, kind="note", description="Met NPC",
                      campaign=self.camp)
        self.assertEqual(len(self.q.log), 1)
        self.assertEqual(self.q.log[0].timestamp, "S3 D5")

    def test_pay_npc_decrements_party_gold(self):
        ql.pay_npc(self.q, "npc_smith", 30.0,
                    description="Paid blacksmith",
                    campaign=self.camp)
        self.assertEqual(self.q.log[0].gold_delta, -30.0)
        self.assertAlmostEqual(self.camp.party_gold, 20.0)

    def test_receive_from_npc_increments(self):
        ql.receive_from_npc(self.q, "npc_lord", 100.0, campaign=self.camp)
        self.assertEqual(self.q.log[0].gold_delta, +100.0)
        self.assertAlmostEqual(self.camp.party_gold, 150.0)

    def test_kill_monster_logs_kill_kind(self):
        ql.kill_monster(self.q, "Bandit Captain", campaign=self.camp)
        self.assertEqual(self.q.log[0].kind, "kill")
        self.assertEqual(self.q.log[0].monster_name, "Bandit Captain")

    def test_complete_quest_sets_status(self):
        ql.complete_quest(self.q, campaign=self.camp)
        self.assertEqual(self.q.status, "completed")
        self.assertEqual(self.q.completed_date, "S3 D5")

    def test_quests_for_npc_finds_by_giver_id(self):
        w = World()
        q = Quest(id="qx", name="Test", giver_npc_id="npc_jarl")
        w.quests["qx"] = q
        hits = ql.quests_for_npc(w, "npc_jarl")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].id, "qx")

    def test_quests_for_shop(self):
        w = World()
        q = Quest(id="qx", name="Test", shop_ids=["s1"])
        w.quests["qx"] = q
        hits = ql.quests_for_shop(w, "s1")
        self.assertEqual(len(hits), 1)

    def test_quests_for_location_via_map_pin(self):
        w = World()
        q = Quest(id="qx", name="Test",
                   map_pin_location_id="loc_outpost")
        w.quests["qx"] = q
        hits = ql.quests_for_location(w, "loc_outpost")
        self.assertEqual(len(hits), 1)

    def test_quests_for_monster_case_insensitive(self):
        w = World()
        q = Quest(id="qx", name="Test",
                   monster_names=["Bandit Captain"])
        w.quests["qx"] = q
        hits = ql.quests_for_monster(w, "bandit captain")
        self.assertEqual(len(hits), 1)

    def test_gold_movements_split(self):
        ql.pay_npc(self.q, "n", 30, campaign=self.camp)
        ql.receive_from_npc(self.q, "n", 80, campaign=self.camp)
        mv = ql.gold_movements(self.q)
        self.assertEqual(mv["paid"], 30)
        self.assertEqual(mv["received"], 80)
        self.assertEqual(mv["net"], 50)

    def test_reward_summary_and_progress(self):
        q = Quest(id="q", name="Test", reward_xp=200, reward_gold=50,
                    reward_items=["Sword"])
        q.objectives = [
            QuestObjective(description="Find map", completed=True),
            QuestObjective(description="Return"),
        ]
        s = ql.reward_summary(q)
        self.assertIn("200 XP", s)
        self.assertIn("50 gp", s)
        self.assertIn("Sword", s)
        self.assertEqual(ql.objective_progress(q), "1/2")


if __name__ == "__main__":
    unittest.main()
