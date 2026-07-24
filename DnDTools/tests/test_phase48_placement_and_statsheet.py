"""Phase 48 — side selection when placing entities, and NPC stat-sheet
access from navigation.

Covers:
  * The battle ADD-entity flow places a creature on the side chosen by
    the toggle (add_entity_is_player), regardless of whether the entry
    is a hero or a monster — so any creature can join either side.
  * battle_renderer imports library / hero_list (the ADD modal used to
    crash with NameError when opened).
  * campaign_manager._get_npc_stats resolves a monster stat block via
    the correct library API and the right CreatureStats fields, so the
    Monster Lore sheet opens from an NPC.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import unittest

import pygame
pygame.init()
pygame.display.set_mode((320, 240))

from data.models import CreatureStats, AbilityScores, Action
from engine.entities import Entity
from data.library import library


def _mk(name, x, y, is_player):
    stats = CreatureStats(
        name=name, hit_points=40, armor_class=15, speed=30,
        abilities=AbilityScores(strength=14, dexterity=14, constitution=14),
        actions=[Action("Sword", "Melee", 5, "1d8", 3, "slashing")])
    return Entity(stats, x, y, is_player=is_player)


class _FakeManager:
    def __init__(self, screen):
        self.screen = screen
        self.running = True

    def change_state(self, *a, **k):
        pass


class TestSideSelectionOnPlacement(unittest.TestCase):
    def setUp(self):
        from states.battle_state import BattleState
        self.screen = pygame.display.get_surface()
        self.bs = BattleState(_FakeManager(self.screen),
                              entities=[_mk("Hero", 2, 2, True),
                                        _mk("Goblin", 8, 8, False)])

    def test_monster_can_be_added_as_ally(self):
        self.bs.add_entity_is_player = True
        m = library.get_monster("Baenrahel Aether Vanguard")
        self.bs._add_entity_to_battle(m, is_player=self.bs.add_entity_is_player)
        added = self.bs.battle.entities[-1]
        self.assertEqual(added.name, "Baenrahel Aether Vanguard")
        self.assertTrue(added.is_player, "toggle=ally must place monster on "
                                          "the player side")

    def test_hero_can_be_added_as_enemy(self):
        from data.heroes import hero_list
        self.bs.add_entity_is_player = False
        hero = hero_list[0]
        self.bs._add_entity_to_battle(hero, is_player=self.bs.add_entity_is_player)
        added = self.bs.battle.entities[-1]
        self.assertFalse(added.is_player, "toggle=enemy must place hero on "
                                           "the enemy side")

    def test_add_entity_modal_renders_without_nameerror(self):
        # Regression: battle_renderer must import library + hero_list.
        self.bs.add_entity_open = True
        self.bs.add_entity_is_player = True
        try:
            self.bs.draw(self.screen)
        except NameError as e:
            self.fail(f"ADD-entity modal crashed: {e}")


class TestNpcStatSheetResolves(unittest.TestCase):
    def test_get_npc_stats_resolves_monster(self):
        from states.campaign_manager import CampaignManagerState
        from data.novus_somnium import build_novus_somnium
        mgr = _FakeManager(pygame.display.get_surface())
        cm = CampaignManagerState(mgr, build_novus_somnium())
        elarae = cm.world.npcs["npc_elarae"]
        stats = cm._get_npc_stats(elarae)
        self.assertIsNotNone(stats)
        self.assertEqual(stats.name, "Elarae Baenrahel")
        self.assertEqual(stats.challenge_rating, 14.0)
        self.assertGreater(stats.hit_points, 0)

    def test_detail_modal_exposes_stats_button(self):
        from states.npc_detail_modal import NpcDetailModal
        from data.novus_somnium import build_novus_somnium
        from states.campaign_manager import CampaignManagerState
        mgr = _FakeManager(pygame.display.get_surface())
        cm = CampaignManagerState(mgr, build_novus_somnium())
        opened = {}
        modal = NpcDetailModal(
            cm.world, cm.campaign, cm.world.npcs["npc_dravin"],
            on_open_stats=lambda npc: opened.setdefault("npc", npc))
        self.assertTrue(hasattr(modal, "btn_stats"))
        modal._open_stats()
        self.assertEqual(opened["npc"].id, "npc_dravin")


if __name__ == "__main__":
    unittest.main()
