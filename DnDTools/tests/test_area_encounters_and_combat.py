"""Valmiit tasokohtaamiset alueille, partyn vienti taisteluun,
suomenkieliset hover-selitteet ja klikkaa-heitä-noppatiput."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import unittest

import pygame
pygame.init()
pygame.display.set_mode((1920, 1080))

from data.novus_somnium import (build_novus_somnium, seed_area_encounters,
                                LVL12_ENCOUNTERS)
from data.library import library
from states.campaign_manager import CampaignManagerState


class _FM:
    def __init__(self):
        self.screen = pygame.display.get_surface()
        self.running = True
        self.states = {}
        self.last = None

    def change_state(self, *a, **k):
        self.last = a


class TestAreaEncounters(unittest.TestCase):
    def setUp(self):
        self.camp = build_novus_somnium()

    def test_eight_lvl12_encounters_seeded(self):
        names = {e.name for e in self.camp.encounters}
        for spec in LVL12_ENCOUNTERS:
            self.assertIn(spec["name"], names, spec["name"])

    def test_encounters_have_real_monster_slots(self):
        by = {e.name: e for e in self.camp.encounters}
        for spec in LVL12_ENCOUNTERS:
            enc = by[spec["name"]]
            self.assertTrue(enc.slots, spec["name"])
            for slot in enc.slots:
                # every slot resolves to a real library monster
                library.get_monster(slot.creature_name)
                self.assertEqual(slot.side, "enemy")

    def test_seed_is_idempotent(self):
        self.assertEqual(seed_area_encounters(self.camp), 0)

    def test_old_save_gets_encounters(self):
        camp = build_novus_somnium()
        # simulate a save from before the expansion
        camp.encounters = [e for e in camp.encounters
                           if e.name not in {s["name"] for s in LVL12_ENCOUNTERS}]
        n_before = len(camp.encounters)
        cm = CampaignManagerState(_FM(), camp)
        self.assertEqual(len(cm.campaign.encounters),
                         n_before + len(LVL12_ENCOUNTERS))


class TestLaunchEncounterUsesActiveGroup(unittest.TestCase):
    def test_only_active_group_deployed(self):
        cm = CampaignManagerState(_FM(), build_novus_somnium())
        cm._set_active_group("pg_pinwud")   # just Marduk
        # find the Red Dagger encounter and launch it
        idx = next(i for i, e in enumerate(cm.campaign.encounters)
                   if "Red Dagger" in e.name)
        cm.selected_encounter_idx = idx
        cm._launch_encounter()
        bs = cm.manager.states.get("BATTLE")
        self.assertIsNotNone(bs)
        players = [e.name for e in bs.battle.entities if e.is_player]
        self.assertEqual(players, ["Marduk"])
        # enemies from the encounter present
        enemies = [e.name for e in bs.battle.entities if not e.is_player]
        self.assertTrue(any("Red Dagger" in n for n in enemies))


class TestPartyToCombat(unittest.TestCase):
    def test_launch_group_pcs_and_companions(self):
        cm = CampaignManagerState(_FM(), build_novus_somnium())
        cm._launch_party_to_combat("pg_ravenstone")   # Padak + Sam NPC
        bs = cm.manager.states.get("BATTLE")
        self.assertIsNotNone(bs)
        players = [e.name for e in bs.battle.entities if e.is_player]
        self.assertIn("Padak Onslaught", players)

    def test_launch_aterterra_full_four(self):
        cm = CampaignManagerState(_FM(), build_novus_somnium())
        cm._launch_party_to_combat("pg_aterterra")
        bs = cm.manager.states.get("BATTLE")
        players = {e.name for e in bs.battle.entities if e.is_player}
        for n in ("Beatrice", "Balthazar", "Kairon", "Magnus Dragonius"):
            self.assertIn(n, players)


class TestFinnishHoverInLoreModal(unittest.TestCase):
    def test_hover_targets_have_finnish_text(self):
        from states.monster_lore_modal import MonsterLoreModal
        stats = library.get_monster("Kreivitar Vila Norgrad")
        m = MonsterLoreModal(stats, on_close=lambda: None)
        m.open()
        m.draw(pygame.display.get_surface())
        self.assertTrue(m._hover_targets)
        # each target carries a non-empty Finnish string
        for _rect, fi in m._hover_targets:
            self.assertTrue(fi)


class TestClickToRoll(unittest.TestCase):
    def test_roll_goes_to_dice_tray(self):
        cm = CampaignManagerState(_FM(), build_novus_somnium())
        cm._roll_d20("Kairon", "CHA-heitto", 5)
        self.assertEqual(cm._dice_tray.expr, "1d20+5")
        self.assertTrue(cm._dice_tray.is_open)
        self.assertIn("Kairon", cm._dice_tray.label)

    def test_negative_and_zero_modifier(self):
        cm = CampaignManagerState(_FM(), build_novus_somnium())
        cm._roll_d20("X", "STR", -1)
        self.assertEqual(cm._dice_tray.expr, "1d20-1")
        cm._roll_d20("X", "INT", 0)
        self.assertEqual(cm._dice_tray.expr, "1d20")

    def test_member_detail_with_rolls_draws(self):
        cm = CampaignManagerState(_FM(), build_novus_somnium())
        cm.active_tab = 0
        cm.selected_member_idx = 0
        cm.draw(pygame.display.get_surface())  # must not raise


if __name__ == "__main__":
    unittest.main()
