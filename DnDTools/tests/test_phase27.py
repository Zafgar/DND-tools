"""Phase 27 — quest pins, shop commissions, quick quests, org operations.

  27a: quest_log.quests_pinned_at + map_pin_colour_for_quest.
  27b: ShopCommission + helper API (commission_party, mark_ready,
       deliver, cancel, active_commissions).
  27c: QuickCreateQuestModal data wiring.
  27d: OrganisationOperation + add_operation + reverse lookups +
       seed data on Brotherhood + serialisation.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import json
import unittest

from data.world import (
    World, Shop, Quest, ShopCommission,
    _serialize_shop, _deserialize_shop,
)
from data import quest_log as ql
from data import organizations as orgs

try:
    import pygame  # noqa: F401
    HAS_PYGAME = True
except ImportError:  # pragma: no cover
    HAS_PYGAME = False


class _Stub:
    def __init__(self):
        self.party_gold = 100.0
        self.session_number = 3
        self.in_game_day = 5


class _FakeCampaign:
    def __init__(self):
        self.kingdoms_data = None
        self.organisations_data = None


# --------------------------------------------------------------------- #
# 27a — quest pin helpers
# --------------------------------------------------------------------- #
class TestQuestPins(unittest.TestCase):
    def test_pinned_at_filters_by_status(self):
        w = World()
        q_active = Quest(id="qa", name="Bandit",
                          map_pin_location_id="loc_outpost",
                          status="active")
        q_done = Quest(id="qd", name="Done",
                        map_pin_location_id="loc_outpost",
                        status="completed")
        w.quests["qa"] = q_active
        w.quests["qd"] = q_done
        hits = ql.quests_pinned_at(w, "loc_outpost")
        self.assertEqual({q.id for q in hits}, {"qa"})

    def test_pinned_at_returns_empty_for_unknown(self):
        self.assertEqual(ql.quests_pinned_at(World(), "nope"), [])

    def test_pin_colour_changes_with_priority(self):
        urgent = Quest(id="u", name="U", priority="urgent")
        normal = Quest(id="n", name="N", priority="normal")
        low = Quest(id="l", name="L", priority="low")
        self.assertNotEqual(
            ql.map_pin_colour_for_quest(urgent),
            ql.map_pin_colour_for_quest(normal))
        self.assertNotEqual(
            ql.map_pin_colour_for_quest(low),
            ql.map_pin_colour_for_quest(normal))


# --------------------------------------------------------------------- #
# 27b — shop commissions
# --------------------------------------------------------------------- #
class TestShopCommissions(unittest.TestCase):
    def setUp(self):
        self.shop = Shop(id="s", name="Smithy", shop_type="blacksmith",
                          owner_npc_id="npc_smith")
        self.quest = Quest(id="q", name="Forge Sword")
        self.camp = _Stub()

    def test_commission_party_logs_deposit_and_links_shop(self):
        c = ql.commission_party(
            self.shop, "+1 Longsword", price_gp=200,
            deposit_gp=100, due_in_days=5,
            description="Smith promised in 5 days.",
            linked_quest=self.quest, campaign=self.camp,
        )
        self.assertIsInstance(c, ShopCommission)
        self.assertEqual(c.status, "in_progress")
        self.assertEqual(c.deposit_paid_gp, 100)
        self.assertIn(self.shop.id, self.quest.shop_ids)
        # The deposit hit the party purse and a transaction line was logged
        self.assertAlmostEqual(self.camp.party_gold, 0.0)
        self.assertEqual(self.quest.log[-1].kind, "transaction")
        self.assertEqual(self.quest.log[-1].gold_delta, -100.0)

    def test_mark_ready_and_deliver(self):
        c = ql.commission_party(self.shop, "Mace", price_gp=20,
                                  linked_quest=self.quest,
                                  campaign=self.camp)
        ok = ql.mark_commission_ready(self.shop, c.id,
                                         linked_quest=self.quest,
                                         campaign=self.camp)
        self.assertTrue(ok)
        self.assertEqual(c.status, "ready")
        ok = ql.deliver_commission(self.shop, c.id,
                                      linked_quest=self.quest,
                                      campaign=self.camp)
        self.assertTrue(ok)
        self.assertEqual(c.status, "delivered")
        # Remainder (20 gp) was paid out
        self.assertAlmostEqual(c.deposit_paid_gp, 20.0)

    def test_cancel(self):
        c = ql.commission_party(self.shop, "Dagger", price_gp=2,
                                  campaign=self.camp)
        self.assertTrue(ql.cancel_commission(self.shop, c.id))
        self.assertEqual(c.status, "cancelled")

    def test_active_commissions_excludes_delivered_and_cancelled(self):
        a = ql.commission_party(self.shop, "A", price_gp=5,
                                  campaign=self.camp)
        b = ql.commission_party(self.shop, "B", price_gp=5,
                                  campaign=self.camp)
        ql.deliver_commission(self.shop, a.id, campaign=self.camp)
        active = ql.active_commissions(self.shop)
        self.assertEqual([c.id for c in active], [b.id])

    def test_commission_round_trips(self):
        ql.commission_party(self.shop, "Helm", price_gp=10,
                              deposit_gp=2, due_in_days=3,
                              campaign=self.camp)
        d = _serialize_shop(self.shop)
        s = json.dumps(d)
        s2 = _deserialize_shop(json.loads(s))
        self.assertEqual(len(s2.commissions), 1)
        c2 = s2.commissions[0]
        self.assertEqual(c2.item_name, "Helm")
        self.assertEqual(c2.price_gp, 10.0)
        self.assertEqual(c2.deposit_paid_gp, 2.0)
        self.assertEqual(c2.due_in_days, 3)


# --------------------------------------------------------------------- #
# 27c — quick quest modal data wiring
# --------------------------------------------------------------------- #
@unittest.skipUnless(HAS_PYGAME, "pygame not installed")
class TestQuickCreateQuestModal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import pygame
        pygame.init()
        pygame.display.set_mode((1280, 800))

    def test_create_inserts_quest_into_world(self):
        from states.quick_create_quest_modal import QuickCreateQuestModal
        from data.world import Location, NPC
        w = World()
        w.locations["loc_a"] = Location(id="loc_a", name="A")
        w.npcs["npc_a"] = NPC(id="npc_a", name="Jarl")
        seen = []
        m = QuickCreateQuestModal(w,
                                     default_giver_npc_id="npc_a",
                                     default_location_id="loc_a",
                                     on_created=lambda qid: seen.append(qid))
        m.open()
        m.name = "Bandit hunt"
        m.monster = "Bandit Captain"
        m.xp_str = "200"
        m.gold_str = "50"
        m._create()
        self.assertEqual(len(seen), 1)
        qid = seen[0]
        q = w.quests[qid]
        self.assertEqual(q.name, "Bandit hunt")
        self.assertEqual(q.giver_npc_id, "npc_a")
        self.assertIn("npc_a", q.npc_ids)
        self.assertEqual(q.map_pin_location_id, "loc_a")
        self.assertEqual(q.monster_names, ["Bandit Captain"])
        self.assertEqual(q.reward_xp, 200)
        self.assertEqual(q.reward_gold, 50.0)

    def test_empty_name_does_not_create(self):
        from states.quick_create_quest_modal import QuickCreateQuestModal
        w = World()
        m = QuickCreateQuestModal(w)
        m.open()
        m._create()
        self.assertEqual(len(w.quests), 0)
        self.assertIn("nimi", m._status.lower())


# --------------------------------------------------------------------- #
# 27d — organisation operations
# --------------------------------------------------------------------- #
class TestOrganisationOperations(unittest.TestCase):
    def test_seed_brotherhood_has_three_operations(self):
        camp = _FakeCampaign()
        b = orgs.ensure_organisations_on_campaign(camp)[0]
        self.assertGreaterEqual(len(b.operations), 3)
        kinds = {op.kind for op in b.operations}
        self.assertIn("ritual", kinds)
        self.assertIn("recruit", kinds)

    def test_add_operation(self):
        camp = _FakeCampaign()
        orgs.ensure_organisations_on_campaign(camp)
        op = orgs.add_operation(camp, "brotherhood_of_glorious_sun",
                                  name="Test heist",
                                  kind="raid",
                                  target_city_key="frand",
                                  target_kingdom_key="tarmaas",
                                  severity=7,  # clamped to 5
                                  status="active")
        self.assertIsNotNone(op)
        self.assertEqual(op.severity, 5)
        self.assertEqual(op.status, "active")
        # Reverse lookups
        in_city = orgs.operations_in_city(camp, "frand")
        in_kingdom = orgs.operations_in_kingdom(camp, "tarmaas")
        self.assertTrue(any(o.name == "Test heist" for o in in_city))
        self.assertTrue(any(o.name == "Test heist" for o in in_kingdom))

    def test_organisation_round_trips_operations(self):
        camp = _FakeCampaign()
        orgs.ensure_organisations_on_campaign(camp)
        orgs.sync_organisations_to_campaign(camp)
        s = json.dumps(camp.organisations_data)
        c2 = _FakeCampaign()
        c2.organisations_data = json.loads(s)
        r2 = orgs.ensure_organisations_on_campaign(c2)
        b2 = r2[0]
        self.assertGreaterEqual(len(b2.operations), 3)
        op = b2.operations[0]
        self.assertEqual(op.kind, "recruit")
        self.assertEqual(op.target_city_key, "frand")


if __name__ == "__main__":
    unittest.main()
