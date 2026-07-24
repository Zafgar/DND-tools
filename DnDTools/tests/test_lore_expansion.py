"""Cunae-loren laajennus: puuttuvat kaupungit + kolme ulottuvuutta,
sekä additiivinen merge vanhoihin tallennuksiin."""
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


NEW_CITIES = [
    "Honpa", "Stein Festing (Kivikaupunki)", "Nunamair",
    "Sshamath Ul (Tulen Kaupunki)", "Ghaurath Tol (Tuhkan Torni)",
    "Ilnauth Zen (Jään Kuiskaus)", "Zekk'Und", "Tharkozh-Varr",
    "Xullrae (Hämärän Vedet)", "Quellan'Dra", "Ivory Hollow",
]
REALMS = {
    "Celeste (High Heavens)": ["Aurea Porta", "Arx Mnemosyne",
                               "Gossamer Grove"],
    "Infernal Disc (9 Hells)": ["Brassharbor", "Veilmire", "Hingehold",
                                "Chainledger"],
    "Regnum Fatarum (Feywild)": ["Pale Diadem", "Bonehaven", "Spindlehaven"],
}


class TestLoreCitiesPresent(unittest.TestCase):
    def setUp(self):
        self.cm = CampaignManagerState(_FM(), build_novus_somnium())
        self.by_name = {l.name: l for l in self.cm.world.locations.values()}

    def test_all_new_cities_added(self):
        for city in NEW_CITIES:
            self.assertIn(city, self.by_name, city)

    def test_realms_are_top_level_with_children(self):
        for realm, cities in REALMS.items():
            self.assertIn(realm, self.by_name, realm)
            loc = self.by_name[realm]
            self.assertEqual(loc.parent_id, "", f"{realm} should be top-level")
            self.assertEqual(len(loc.children_ids), len(cities), realm)
            for city in cities:
                self.assertIn(city, self.by_name, city)
                self.assertEqual(self.by_name[city].parent_id, loc.id, city)

    def test_underdark_cities_under_aterterra(self):
        aterterra = next(l for l in self.cm.world.locations.values()
                         if l.name == "Aterterra")
        for city in ("Sshamath Ul (Tulen Kaupunki)", "Xullrae (Hämärän Vedet)",
                     "Quellan'Dra"):
            self.assertEqual(self.by_name[city].parent_id, aterterra.id, city)

    def test_new_cities_have_descriptions(self):
        for city in NEW_CITIES:
            self.assertTrue(self.by_name[city].description.strip(), city)


class TestOldSaveMerge(unittest.TestCase):
    def test_missing_cities_merged_on_load(self):
        camp = build_novus_somnium()
        # Simulate a save made before the expansion by dropping the new ids.
        drop = ["loc_honpa", "loc_stein_festing", "loc_nunamair",
                "loc_celeste", "loc_aurea_porta", "loc_infernal_disc",
                "loc_regnum_fatarum", "loc_pale_diadem", "loc_xullrae"]
        for i in drop:
            camp.world_data["locations"].pop(i, None)
        before = len(camp.world_data["locations"])
        cm = CampaignManagerState(_FM(), camp)
        after = len(cm.world.locations)
        self.assertEqual(after - before, len(drop))
        names = {l.name for l in cm.world.locations.values()}
        self.assertIn("Honpa", names)
        self.assertIn("Celeste (High Heavens)", names)
        # Merge is persisted back into world_data.
        self.assertIn("loc_honpa", cm.campaign.world_data["locations"])

    def test_non_canon_campaign_not_touched(self):
        from data.campaign import Campaign
        camp = Campaign(name="My Homebrew", created="x")
        cm = CampaignManagerState(_FM(), camp)
        # No canon merge for a non-Novus campaign — should stay tiny/empty.
        self.assertNotIn("loc_honpa",
                         {l.id for l in cm.world.locations.values()})

    def test_refresh_lore_idempotent(self):
        from data import novus_somnium_lore as lore
        camp = build_novus_somnium()
        cm = CampaignManagerState(_FM(), camp)
        # Running refresh again adds nothing (everything already present).
        added = lore.refresh_lore(cm.campaign, cm.world)
        self.assertEqual(added, 0)


if __name__ == "__main__":
    unittest.main()
