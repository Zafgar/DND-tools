"""Novus Somnium -alaryhmät (party groups): seedaus, jäsenten siirto
ryhmien välillä, ryhmän sijainti, save/load-kierto ja korjattu
_serialize_world-nimitörmäys (save ei enää kaadu)."""
import sys
import os
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import unittest

import pygame
pygame.init()
pygame.display.set_mode((1920, 1080))

from data.novus_somnium import build_novus_somnium, seed_party_groups
from data.campaign import save_campaign, load_campaign
from states.campaign_manager import CampaignManagerState


class _FM:
    def __init__(self):
        self.screen = pygame.display.get_surface()
        self.running = True

    def change_state(self, *a, **k):
        pass


class TestPartyGroupSeed(unittest.TestCase):
    def setUp(self):
        self.camp = build_novus_somnium()

    def test_four_groups_created(self):
        ids = [g.id for g in self.camp.party_groups]
        self.assertEqual(ids, ["pg_aterterra", "pg_maclebar",
                               "pg_ravenstone", "pg_pinwud"])

    def test_groups_have_locations(self):
        loc = {g.id: g.location_id for g in self.camp.party_groups}
        self.assertEqual(loc["pg_aterterra"], "loc_zertath_lanke")
        self.assertEqual(loc["pg_maclebar"], "loc_fort_whitestone")
        self.assertEqual(loc["pg_ravenstone"], "loc_ravenstone")
        self.assertEqual(loc["pg_pinwud"], "loc_pinwud")

    def test_members_assigned_to_groups(self):
        by = {}
        for m in self.camp.party:
            by.setdefault(m.group_id, []).append(m.hero_data.get("name"))
        for name in ("Beatrice", "Balthazar", "Kairon", "Magnus Dragonius"):
            self.assertIn(name, by["pg_aterterra"], name)
        self.assertEqual(sorted(by["pg_maclebar"]),
                         ["Carlo", "Venris Galanodel"])
        self.assertEqual(by["pg_ravenstone"], ["Padak Onslaught"])
        self.assertEqual(by["pg_pinwud"], ["Marduk"])

    def test_npc_companions_attached(self):
        comp = {g.id: g.companion_npc_ids for g in self.camp.party_groups}
        self.assertIn("npc_blitz", comp["pg_maclebar"])
        self.assertIn("npc_sam_undercave", comp["pg_ravenstone"])

    def test_seed_is_idempotent(self):
        self.assertEqual(seed_party_groups(self.camp), 0)

    def test_active_group_defaults_to_first(self):
        self.assertEqual(self.camp.active_group_id, "pg_aterterra")


class TestPartyGroupSaveLoad(unittest.TestCase):
    def test_round_trip_preserves_groups(self):
        camp = build_novus_somnium()
        tmp = tempfile.mktemp(suffix=".json")
        save_campaign(camp, tmp)
        loaded = load_campaign(tmp)
        self.assertEqual(len(loaded.party_groups), 4)
        self.assertEqual(loaded.active_group_id, "pg_aterterra")
        groups = {g.id: g for g in loaded.party_groups}
        self.assertIn("npc_blitz", groups["pg_maclebar"].companion_npc_ids)
        # members keep their group tag
        by = {m.hero_data.get("name"): m.group_id for m in loaded.party}
        self.assertEqual(by["Marduk"], "pg_pinwud")


class TestSaveNoLongerCrashes(unittest.TestCase):
    """Regression: two _serialize_world defs collided and _save_campaign
    crashed with 'missing 1 required positional argument: world'."""

    def test_save_campaign_from_manager(self):
        cm = CampaignManagerState(_FM(), build_novus_somnium())
        cm._save_campaign()   # must not raise
        self.assertIn("Saved", cm._status_msg)

    def test_serialize_world_no_args(self):
        cm = CampaignManagerState(_FM(), build_novus_somnium())
        wd = cm._serialize_world()   # single canonical signature
        self.assertIn("locations", wd)
        self.assertGreater(len(wd["locations"]), 0)


class TestPartyGroupUI(unittest.TestCase):
    def _cm(self):
        return CampaignManagerState(_FM(), build_novus_somnium())

    def test_filter_by_active_group(self):
        cm = self._cm()
        cm._set_active_group("pg_ravenstone")
        names = [cm.campaign.party[i].hero_data.get("name")
                 for i in cm._visible_party_indices()]
        self.assertEqual(names, ["Padak Onslaught"])

    def test_all_group_shows_everyone(self):
        cm = self._cm()
        cm._set_active_group("")   # "Kaikki"
        self.assertEqual(len(cm._visible_party_indices()), len(cm.campaign.party))

    def test_cycle_member_between_groups(self):
        cm = self._cm()
        # Marduk is alone in pg_pinwud; cycle him forward.
        idx = next(i for i, m in enumerate(cm.campaign.party)
                   if m.hero_data.get("name") == "Marduk")
        before = cm.campaign.party[idx].group_id
        cm._cycle_member_group(idx)
        self.assertNotEqual(cm.campaign.party[idx].group_id, before)
        # cycling full circle returns to start
        for _ in range(len(cm._party_groups()) - 1):
            cm._cycle_member_group(idx)
        self.assertEqual(cm.campaign.party[idx].group_id, before)

    def test_group_location_picker_sets_location(self):
        cm = self._cm()
        cm._open_group_location_picker("pg_pinwud")
        self.assertTrue(cm._npc_location_picker_open)
        self.assertEqual(cm._group_loc_picker_gid, "pg_pinwud")

    def test_party_tab_draws_with_groups(self):
        cm = self._cm()
        cm.active_tab = 0
        cm.draw(pygame.display.get_surface())  # must not raise
        cm._set_active_group("pg_maclebar")
        cm.draw(pygame.display.get_surface())

    def test_add_group(self):
        cm = self._cm()
        n = len(cm._party_groups())
        cm._add_party_group()
        self.assertEqual(len(cm._party_groups()), n + 1)


class TestOldSaveGetsGroups(unittest.TestCase):
    def test_group_seed_merged_on_load(self):
        camp = build_novus_somnium()
        # Simulate a pre-groups save.
        camp.party_groups = []
        camp.active_group_id = ""
        for m in camp.party:
            m.group_id = ""
        cm = CampaignManagerState(_FM(), camp)
        self.assertEqual(len(cm.campaign.party_groups), 4)
        # members re-tagged
        by = {m.hero_data.get("name"): m.group_id for m in cm.campaign.party}
        self.assertEqual(by.get("Magnus Dragonius"), "pg_aterterra")


if __name__ == "__main__":
    unittest.main()
