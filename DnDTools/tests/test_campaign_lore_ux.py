"""Kampanjanäkymän lore-UX: paikan faktapaneeli, alialueet, kuvat,
NPC-suhteet ja ristiinnavigointi paikkojen ja NPC:iden välillä.
"""
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
from data import npc_directory as npc_dir
from states.campaign_manager import CampaignManagerState


class _FM:
    def __init__(self):
        self.screen = pygame.display.get_surface()
        self.running = True

    def change_state(self, *a, **k):
        pass


def _cm():
    return CampaignManagerState(_FM(), build_novus_somnium())


class TestLocationFactEditing(unittest.TestCase):
    def test_locfact_fields_apply(self):
        cm = _cm()
        loc = next(iter(cm.world.locations.values()))
        cm.selected_location_id = loc.id
        for field, value in (("government", "Teknokraattinen neuvosto"),
                             ("known_for", "Höyryteollisuus"),
                             ("religion", "Mortem-kultti"),
                             ("defenses", "Muurit ja vartiot")):
            cm.input_active = f"locfact_{field}"
            cm.input_text = value
            cm._apply_input()
            self.assertEqual(getattr(loc, field), value, field)

    def test_population_parses_spaces(self):
        cm = _cm()
        loc = next(iter(cm.world.locations.values()))
        cm.selected_location_id = loc.id
        cm.input_active = "locfact_population"
        cm.input_text = "500 000"
        cm._apply_input()
        self.assertEqual(loc.population, 500000)

    def test_population_garbage_ignored(self):
        cm = _cm()
        loc = next(iter(cm.world.locations.values()))
        before = loc.population
        cm.selected_location_id = loc.id
        cm.input_active = "locfact_population"
        cm.input_text = "paljon"
        cm._apply_input()
        self.assertEqual(loc.population, before)


class TestNpcFieldEditing(unittest.TestCase):
    def test_title_and_faction_apply(self):
        cm = _cm()
        npc = next(iter(cm.world.npcs.values()))
        cm.selected_npc_id = npc.id
        cm.input_active = "npc_title"
        cm.input_text = "Arkkimaagi"
        cm._apply_input()
        cm.input_active = "npc_faction"
        cm.input_text = "Talo Baenrahel"
        cm._apply_input()
        self.assertEqual(npc.title, "Arkkimaagi")
        self.assertEqual(npc.faction, "Talo Baenrahel")


class TestLoreDataNavigable(unittest.TestCase):
    """The Novus Somnium world exposes the navigation data the new UI
    renders: parent chains, children, NPCs-at-location and NPC links."""

    def test_city_has_children_and_npcs(self):
        cm = _cm()
        from data.world import get_npcs_at_location, get_location_path
        cities = [l for l in cm.world.locations.values()
                  if l.location_type == "city" and l.children_ids]
        self.assertTrue(cities)
        city = cities[0]
        path = get_location_path(cm.world, city.id)
        self.assertGreaterEqual(len(path), 1)
        # children resolve to real locations
        for cid in city.children_ids:
            self.assertIn(cid, cm.world.locations)

    def test_npc_links_resolve_targets(self):
        cm = _cm()
        linked = [n for n in cm.world.npcs.values()
                  if npc_dir.npc_links_of(cm.world, n.id)]
        self.assertTrue(linked)
        links = npc_dir.npc_links_of(cm.world, linked[0].id)
        for link in links:
            self.assertIn(link["target_id"], cm.world.npcs)
            self.assertTrue(link["target_name"])


class TestWorldTabDrawSmoke(unittest.TestCase):
    def test_location_detail_draws(self):
        cm = _cm()
        cm.active_tab = 4
        cm.world_view = "locations"
        cities = [l for l in cm.world.locations.values()
                  if l.location_type == "city" and l.children_ids]
        cm.selected_location_id = (cities[0] if cities else
                                   next(iter(cm.world.locations.values()))).id
        cm.draw(pygame.display.get_surface())   # must not raise

    def test_location_detail_with_image(self):
        cm = _cm()
        cm.active_tab = 4
        cm.world_view = "locations"
        loc = next(iter(cm.world.locations.values()))
        # Generate a small image and attach it to the location.
        img_path = os.path.join(
            os.environ.get("TMPDIR", "/tmp"), "loc_test_img.png")
        surf = pygame.Surface((64, 48))
        surf.fill((90, 120, 60))
        pygame.image.save(surf, img_path)
        loc.map_image_path = img_path
        cm.selected_location_id = loc.id
        cm.draw(pygame.display.get_surface())
        # Cached scaled surface stored
        self.assertIn(img_path, cm._loc_img_cache)
        self.assertTrue(cm._loc_img_cache[img_path])

    def test_npc_detail_with_links_draws(self):
        cm = _cm()
        cm.active_tab = 4
        cm.world_view = "npcs"
        linked = [n for n in cm.world.npcs.values()
                  if npc_dir.npc_links_of(cm.world, n.id)]
        cm.selected_npc_id = (linked[0] if linked else
                              next(iter(cm.world.npcs.values()))).id
        cm.draw(pygame.display.get_surface())

    def test_locfact_edit_modal_draws(self):
        cm = _cm()
        cm.active_tab = 4
        cm.world_view = "locations"
        cm.selected_location_id = next(iter(cm.world.locations.values())).id
        cm.input_active = "locfact_known_for"
        cm.input_text = "Testi"
        cm.modal = ("edit_field", "locfact_known_for")
        cm.draw(pygame.display.get_surface())


if __name__ == "__main__":
    unittest.main()
