"""Phase 20 — UI wiring smoke tests.

We can't drive the full pygame UI in unit tests, but we exercise the
command methods + state setup that the buttons call into.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import unittest

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

from data.campaign import Campaign
from data.campaign_calendar import (
    advance_time_of_day, advance_days, format_date,
)


# --------------------------------------------------------------------- #
# 20e — Calendar advance command behaviour
# --------------------------------------------------------------------- #
class TestCalendarAdvanceCommands(unittest.TestCase):
    """Stand-ins for _cmd_advance_tod / _cmd_advance_day /
    _cmd_advance_week — replicates the production logic without
    instantiating the pygame manager."""

    def test_advance_tod_rolls_day_at_night(self):
        c = Campaign(time_of_day="night", in_game_day=5)
        info = advance_time_of_day(c)
        self.assertEqual(info["time_of_day"], "dawn")
        self.assertEqual(c.in_game_day, 6)

    def test_advance_day_increments(self):
        c = Campaign(in_game_day=3)
        advance_days(c, 1)
        self.assertEqual(c.in_game_day, 4)

    def test_advance_week_overflows_month(self):
        c = Campaign(in_game_day=28, in_game_month=1)
        advance_days(c, 7)
        # 28 + 7 = 35 → month 2, day 5
        self.assertEqual(c.in_game_month, 2)
        self.assertEqual(c.in_game_day, 5)

    def test_format_date_includes_month_and_year(self):
        c = Campaign(in_game_day=15, in_game_month=4,
                       in_game_year=1492, time_of_day="dusk")
        s = format_date(c)
        self.assertIn("15th", s)
        self.assertIn("Tarsakh", s)
        self.assertIn("1492", s)
        self.assertIn("dusk", s)


# --------------------------------------------------------------------- #
# 20b — Loot panel hook smoke test (data only)
# --------------------------------------------------------------------- #
class TestLootHookSmoke(unittest.TestCase):
    """Verify that calling the production loot helpers with a battle's
    entity list yields a sensible LootBundle ready for the panel."""
    def test_filters_alive_and_player(self):
        from data.loot import loot_from_defeated_entities
        class _S:
            items = ["potion"]
            loot_gold = 5.0
        class _E:
            def __init__(self, name, hp, is_player=False,
                          is_summon=False, is_lair=False):
                self.name = name; self.hp = hp
                self.is_player = is_player
                self.is_summon = is_summon
                self.is_lair = is_lair
                self.stats = _S()
        ents = [
            _E("DeadOrc", 0),
            _E("AliveOrc", 8),  # filtered (still alive)
            _E("HeroAlara", 0, is_player=True),  # filtered
        ]
        bundle = loot_from_defeated_entities(ents)
        self.assertEqual(bundle.source_names, ["DeadOrc"])
        self.assertEqual(bundle.gold, 5.0)


# --------------------------------------------------------------------- #
# 20c — Quick NPC creation flow smoke test
# --------------------------------------------------------------------- #
class TestQuickNPCFlow(unittest.TestCase):
    def test_quick_create_returns_npc_and_actor(self):
        from data.world import World
        from data.actors import ActorRegistry
        from data.npc_quick_create import quick_create_npc
        w = World()
        reg = ActorRegistry()
        rep = quick_create_npc(w, name="Mira", registry=reg)
        self.assertTrue(rep.npc_id)
        self.assertTrue(rep.actor_id)
        self.assertEqual(w.npcs[rep.npc_id].name, "Mira")


# --------------------------------------------------------------------- #
# 20d — Multi-pick toggle is the whole quest list semantics
# --------------------------------------------------------------------- #
class TestMultiPickToggle(unittest.TestCase):
    def test_add_remove(self):
        from states.multi_pick_helpers import toggle_in_list
        lst: list = []
        self.assertTrue(toggle_in_list("a", lst))
        self.assertEqual(lst, ["a"])
        self.assertFalse(toggle_in_list("a", lst))  # remove
        self.assertEqual(lst, [])


# --------------------------------------------------------------------- #
# 20a — Dashboard widget lifecycle (skipped without pygame)
# --------------------------------------------------------------------- #
@unittest.skipUnless(PYGAME_AVAILABLE, "pygame not available")
class TestDashboardWidgetLifecycle(unittest.TestCase):
    def setUp(self):
        if not pygame.display.get_init():
            pygame.display.init()
        if pygame.display.get_surface() is None:
            pygame.display.set_mode((1, 1))

    def test_open_close(self):
        from states.campaign_dashboard_widget import (
            CampaignDashboardWidget,
        )
        from data.world import World
        w = CampaignDashboardWidget(Campaign(), World())
        self.assertFalse(w.is_open)
        w.open()
        self.assertTrue(w.is_open)
        w.close()
        self.assertFalse(w.is_open)

    def test_expand_toggle(self):
        from states.campaign_dashboard_widget import (
            CampaignDashboardWidget,
        )
        from data.world import World
        w = CampaignDashboardWidget(Campaign(), World())
        w.open()
        self.assertFalse(w.expanded)
        w._toggle_expand()
        self.assertTrue(w.expanded)


if __name__ == "__main__":
    unittest.main()
