"""World-välilehden navigointi (Paikat-nappi + aktiivisen näkymän
korostus) ja NPC:n koko statlehti (kyvyt, loitsut, tavarat)."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import unittest

import pygame
pygame.init()
pygame.display.set_mode((1920, 1080))

from data.novus_somnium import build_novus_somnium
from states.campaign_manager import CampaignManagerState


class _FM:
    def __init__(self):
        self.screen = pygame.display.get_surface()
        self.running = True

    def change_state(self, *a, **k):
        pass


def _cm():
    return CampaignManagerState(_FM(), build_novus_somnium())


class TestLocationsNavigation(unittest.TestCase):
    def test_locations_button_exists(self):
        cm = _cm()
        self.assertTrue(hasattr(cm, "btn_world_locations_view"))

    def test_show_locations_from_any_view(self):
        cm = _cm()
        for start in ("npcs", "shops", "quests"):
            cm.world_view = start
            cm.world_map_mode = True
            cm.template_view = "inn_templates"
            cm.services_view = "services"
            cm._show_locations_view()
            self.assertEqual(cm.world_view, "locations")
            self.assertFalse(cm.world_map_mode)
            self.assertEqual(cm.template_view, "")
            self.assertEqual(cm.services_view, "")

    def test_active_view_predicates(self):
        cm = _cm()
        toggles = dict((b, pred) for b, pred in cm._world_view_toggle_buttons)
        # Locations active by default
        cm.world_view = "locations"
        cm.world_map_mode = False
        cm.template_view = ""
        cm.services_view = ""
        loc_pred = toggles[cm.btn_world_locations_view]
        self.assertTrue(loc_pred())
        # Switch to NPCs -> locations predicate false, npcs true
        cm.world_view = "npcs"
        self.assertFalse(loc_pred())
        self.assertTrue(toggles[cm.btn_world_npcs_view]())

    def test_world_tab_draws_in_each_view(self):
        cm = _cm()
        cm.active_tab = 4
        scr = pygame.display.get_surface()
        for view in ("locations", "npcs", "shops", "quests"):
            cm.world_view = view
            cm.draw(scr)   # must not raise


class TestBigStatSheet(unittest.TestCase):
    def _caster_npc(self, cm):
        # Elarae Baenrahel is a linked archmage NPC with spells.
        return cm.world.npcs.get("npc_elarae") or next(
            iter(cm.world.npcs.values()))

    def test_open_full_sheet(self):
        cm = _cm()
        npc = self._caster_npc(cm)
        cm._open_monster_lore(npc)
        self.assertTrue(cm._monster_lore_open)
        self.assertIsNotNone(cm._monster_lore_modal)

    def test_sheet_shows_spells(self):
        cm = _cm()
        npc = cm.world.npcs.get("npc_elarae")
        if npc is None:
            self.skipTest("Elarae NPC not present")
        cm._open_monster_lore(npc)
        stats = cm._monster_lore_modal.stats
        self.assertGreater(len(stats.spells_known), 0)
        # The spells section draws without raising.
        cm._monster_lore_modal.draw(pygame.display.get_surface())

    def test_modal_has_spell_and_inventory_sections(self):
        from states.monster_lore_modal import MonsterLoreModal
        self.assertTrue(hasattr(MonsterLoreModal, "_draw_spells"))
        self.assertTrue(hasattr(MonsterLoreModal, "_draw_inventory"))

    def test_npc_detail_draws_sheet_button(self):
        cm = _cm()
        cm.active_tab = 4
        cm.world_view = "npcs"
        cm.selected_npc_id = self._caster_npc(cm).id
        cm.draw(pygame.display.get_surface())  # renders the sheet button


if __name__ == "__main__":
    unittest.main()
