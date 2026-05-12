"""Phase 23 — living-world UI wiring:

  23a: NPC/Shop coin breakdowns + bank entity + wealth aggregator.
  23b: KingdomNavigatorWidget smoke (pygame headless).
  23c: OrganisationPanelWidget smoke.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import json
import unittest

from data import kingdoms as kg
from data import organizations as orgs
from data import wealth as wlth
from data.currency import Coins
from data.world import World, NPC, Shop

try:
    import pygame  # noqa: F401
    HAS_PYGAME = True
except ImportError:  # pragma: no cover
    HAS_PYGAME = False


class _FakeCampaign:
    """Minimal stand-in matching what the widgets touch."""
    def __init__(self):
        self.kingdoms_data = None
        self.organisations_data = None


# --------------------------------------------------------------------- #
# 23a — coin breakdown on NPC/Shop
# --------------------------------------------------------------------- #
class TestNPCShopCoins(unittest.TestCase):
    def test_npc_coins_falls_back_to_gold_float(self):
        n = NPC(id="n", name="Tester", gold=15.0)
        c = wlth.npc_coins(n)
        # 15 gp → 1500 cp
        self.assertEqual(c.total_cp(), 1500)

    def test_set_npc_coins_round_trip(self):
        n = NPC(id="n", name="Tester")
        wlth.set_npc_coins(n, Coins(pp=2, gp=5))
        c = wlth.npc_coins(n)
        # 2pp = 2000 cp + 5gp = 500 cp = 2500 cp total
        self.assertEqual(c.total_cp(), 2500)
        # ``gold`` float mirror is in sync
        self.assertAlmostEqual(n.gold, 25.0)

    def test_shop_coins_falls_back_to_gold(self):
        s = Shop(id="s", name="Smithy", gold=200.0)
        c = wlth.shop_coins(s)
        self.assertEqual(c.total_cp(), 20000)

    def test_shop_bank_holdings_field(self):
        s = Shop(id="s", name="Counting House", is_bank=True,
                  bank_holdings_gp=5000.0)
        self.assertTrue(s.is_bank)
        self.assertEqual(s.bank_holdings_gp, 5000.0)

    def test_npc_serialisation_round_trip(self):
        from data.world import _serialize_npc, _deserialize_npc
        n = NPC(id="n", name="Tester", gold=0.0)
        wlth.set_npc_coins(n, Coins(pp=1, gp=2, sp=3, cp=4))
        d = _serialize_npc(n)
        s = json.dumps(d)
        n2 = _deserialize_npc(json.loads(s))
        self.assertEqual(n2.wealth, {"pp": 1, "gp": 2, "ep": 0,
                                      "sp": 3, "cp": 4})
        # Round-trip total preserved
        self.assertEqual(wlth.npc_coins(n2).total_cp(),
                          wlth.npc_coins(n).total_cp())

    def test_shop_serialisation_round_trip(self):
        from data.world import _serialize_shop, _deserialize_shop
        s = Shop(id="s", name="Bank", is_bank=True, bank_holdings_gp=900.0)
        wlth.set_shop_coins(s, Coins(pp=3))
        ser = _serialize_shop(s)
        s2 = _deserialize_shop(json.loads(json.dumps(ser)))
        self.assertTrue(s2.is_bank)
        self.assertEqual(s2.bank_holdings_gp, 900.0)
        self.assertEqual(s2.wealth.get("pp"), 3)


# --------------------------------------------------------------------- #
# 23a — city / kingdom aggregates with linked world
# --------------------------------------------------------------------- #
class TestWealthAggregation(unittest.TestCase):
    def setUp(self):
        self.camp = _FakeCampaign()
        self.world = World()
        # Two NPCs and a shop + a bank in Frand
        self.world.npcs["n1"] = NPC(id="n1", name="Beggar",
                                      location_id="loc_frand", gold=2.0)
        n2 = NPC(id="n2", name="Noble", location_id="loc_frand")
        wlth.set_npc_coins(n2, Coins(pp=5, gp=20))
        self.world.npcs["n2"] = n2
        self.world.shops["s1"] = Shop(id="s1", name="Smithy",
                                         location_id="loc_frand",
                                         gold=150.0)
        self.world.shops["s2"] = Shop(id="s2", name="Bank",
                                         location_id="loc_frand",
                                         is_bank=True,
                                         gold=300.0,
                                         bank_holdings_gp=10_000.0)
        kg.ensure_kingdoms_on_campaign(self.camp)
        self.frand = kg.find_city(self.camp, "tarmaas", "frand")
        self.frand.location_id = "loc_frand"

    def test_city_breakdown_includes_all_pools(self):
        br = wlth.city_wealth_breakdown(self.world, self.frand)
        self.assertGreater(br["npcs"], 0)
        self.assertGreater(br["shops"], 0)
        self.assertEqual(br["banks"], 10_000.0)
        self.assertEqual(br["crown"], self.frand.treasury_gp)
        self.assertAlmostEqual(
            br["total"],
            br["crown"] + br["npcs"] + br["shops"] + br["banks"])

    def test_kingdom_wealth_sums_cities(self):
        tarmaas = kg.find_kingdom(self.camp, "tarmaas")
        total = wlth.kingdom_total_wealth_gp(self.world, tarmaas)
        # Includes the Tarmaas crown + Frand breakdown
        self.assertGreater(total, tarmaas.treasury_gp)

    def test_world_total_sums_kingdoms(self):
        total = wlth.world_total_wealth_gp(self.world, self.camp)
        # Strictly greater than the sum of kingdom crowns, because the
        # NPC/shop/bank money in Frand is now in the mix.
        crowns = sum(k.treasury_gp for k in kg.SEED_KINGDOMS)
        self.assertGreater(total, crowns)

    def test_suggest_coins_for_wealth_tier(self):
        c = wlth.suggest_coins_for_wealth_tier("comfortable")
        # 100 gp → 10 pp normalised
        self.assertAlmostEqual(c.total_gp(), 100.0)
        c2 = wlth.suggest_coins_for_wealth_tier("squalid")
        self.assertAlmostEqual(c2.total_gp(), 0.5)


# --------------------------------------------------------------------- #
# 23b / 23c — widget smoke tests (require pygame)
# --------------------------------------------------------------------- #
@unittest.skipUnless(HAS_PYGAME, "pygame not installed")
class TestKingdomNavigatorWidget(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import pygame
        pygame.init()
        pygame.display.set_mode((1280, 800))

    def test_open_and_draw_without_crashing(self):
        from data.novus_somnium import build_novus_somnium
        from states.kingdom_navigator_widget import KingdomNavigatorWidget
        import pygame
        camp = build_novus_somnium()
        widget = KingdomNavigatorWidget(camp, World())
        widget.open()
        widget.draw(pygame.display.get_surface())
        # A kingdom should have been auto-selected
        self.assertTrue(widget.selected_kingdom_key)

    def test_click_kingdom_row_selects_it(self):
        from data.novus_somnium import build_novus_somnium
        from states.kingdom_navigator_widget import KingdomNavigatorWidget
        import pygame
        camp = build_novus_somnium()
        widget = KingdomNavigatorWidget(camp, World())
        widget.open()
        # Render once so _kingdom_rects is populated
        widget.draw(pygame.display.get_surface())
        # Simulate a click on the second row (Fundarla)
        if len(widget._kingdom_rects) >= 2:
            rect, k = widget._kingdom_rects[1]
            event = pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                                          {"button": 1,
                                           "pos": rect.center})
            widget.handle_event(event)
            self.assertEqual(widget.selected_kingdom_key, k.key)


@unittest.skipUnless(HAS_PYGAME, "pygame not installed")
class TestOrganisationPanelWidget(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import pygame
        pygame.init()
        pygame.display.set_mode((1280, 800))

    def test_open_and_draw_without_crashing(self):
        from data.novus_somnium import build_novus_somnium
        from states.organisation_panel_widget import OrganisationPanelWidget
        import pygame
        camp = build_novus_somnium()
        widget = OrganisationPanelWidget(camp)
        widget.open()
        widget.draw(pygame.display.get_surface())
        self.assertEqual(widget.selected_key,
                          "brotherhood_of_glorious_sun")

    def test_member_click_fires_npc_callback(self):
        from data.novus_somnium import build_novus_somnium
        from states.organisation_panel_widget import OrganisationPanelWidget
        import pygame
        # Wire one Brotherhood member to a real NPC id
        camp = build_novus_somnium()
        b = orgs.find_organisation(camp,
                                       "brotherhood_of_glorious_sun")
        if b.members:
            b.members[0].npc_id = "wired_npc"
        seen = []
        widget = OrganisationPanelWidget(
            camp,
            on_npc_click=lambda npc_id: seen.append(npc_id),
        )
        widget.open()
        widget.draw(pygame.display.get_surface())
        # Find the wired member row and click it
        for rect, m in widget._member_rects:
            if m.npc_id == "wired_npc":
                event = pygame.event.Event(
                    pygame.MOUSEBUTTONDOWN,
                    {"button": 1, "pos": rect.center})
                widget.handle_event(event)
                break
        self.assertEqual(seen, ["wired_npc"])


if __name__ == "__main__":
    unittest.main()
