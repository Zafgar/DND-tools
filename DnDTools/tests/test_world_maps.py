"""Pelinjohtajan omat kartat pelin sisällä.

Cunae-yleiskartta ja valtakuntien tarkat kartat (Smardu, Tarmaas,
Oblitus, Fundarla) ovat rekisteröityjä karttoja, joilla on paikkamerkit
kytkettynä oikeisiin ``loc_*``-tunnuksiin. Maailmankarttanäkymästä voi
vaihtaa arkkia, ja merkit seuraavat mukana.

Kattaa myös regressiot: karttamerkit, tokenit, kaupat ja palvelut eivät
enää katoa tallennuksessa.
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

from data import world_maps as wm
from data.world import World, MapPin, add_pin
from data.novus_somnium import build_novus_somnium
from states.campaign_manager import CampaignManagerState


class _FM:
    def __init__(self):
        self.screen = pygame.display.get_surface()
        self.running = True
        self.states = {}

    def change_state(self, *a, **k):
        pass


class TestRegistry(unittest.TestCase):
    def test_all_five_maps_are_registered(self):
        keys = {m.key for m in wm.all_maps()}
        self.assertEqual(keys, {"cunae", "smardu", "tarmaas", "oblitus",
                                "fundarla"})

    def test_every_map_file_ships_with_the_repo(self):
        for m in wm.all_maps():
            self.assertTrue(m.exists(), f"{m.filename} missing on disk")

    def test_every_map_loads_as_an_image(self):
        for m in wm.all_maps():
            surf = pygame.image.load(m.abs_path())
            w, h = surf.get_size()
            self.assertGreater(w, 1000, m.key)
            self.assertGreater(h, 700, m.key)

    def test_regional_maps_name_their_kingdom(self):
        expected = {
            "smardu": "loc_smardu", "tarmaas": "loc_tarmaas",
            "oblitus": "loc_oblitus", "fundarla": "loc_fundarla",
        }
        for key, loc_id in expected.items():
            self.assertEqual(wm.get_map(key).location_id, loc_id)
        # the overview map belongs to no single kingdom
        self.assertEqual(wm.get_map("cunae").location_id, "")

    def test_lookup_helpers(self):
        self.assertIsNone(wm.get_map("no-such-map"))
        self.assertEqual(wm.map_for_location("loc_tarmaas").key, "tarmaas")
        self.assertIsNone(wm.map_for_location("loc_frand"))
        self.assertEqual(wm.key_for_path("data/maps/world/oblitus.jpg"),
                         "oblitus")
        self.assertEqual(wm.key_for_path("data\\maps\\world\\smardu.jpg"),
                         "smardu")
        self.assertEqual(wm.key_for_path("saves/whatever.png"), "")
        self.assertEqual(wm.key_for_path(""), "")

    def test_cunae_carries_the_scale_note(self):
        self.assertIn("mailia", wm.get_map("cunae").scale_note)

    def test_fundarla_is_flagged_as_unfinished(self):
        """Pelinjohtaja sanoi sen olevan eniten kesken — se pitää lukea
        kuvauksesta eikä yllättää pöydässä."""
        self.assertIn("KESKEN", wm.get_map("fundarla").description)


class TestPinSpecs(unittest.TestCase):
    def test_every_map_has_pins(self):
        for m in wm.all_maps():
            self.assertTrue(wm.pins_for(m.key), m.key)

    def test_pin_coordinates_are_percentages_inside_the_sheet(self):
        for m in wm.all_maps():
            for spec in wm.pins_for(m.key):
                self.assertGreaterEqual(spec["map_x"], 0.0, spec["name"])
                self.assertLessEqual(spec["map_x"], 100.0, spec["name"])
                self.assertGreaterEqual(spec["map_y"], 0.0, spec["name"])
                self.assertLessEqual(spec["map_y"], 100.0, spec["name"])

    def test_pin_names_are_unique_per_map(self):
        for m in wm.all_maps():
            names = [s["name"] for s in wm.pins_for(m.key)]
            self.assertEqual(len(names), len(set(names)), m.key)

    def test_pin_ids_are_stable_and_map_scoped(self):
        a = wm.pin_id("cunae", "Old Vaisil")
        self.assertEqual(a, wm.pin_id("cunae", "Old Vaisil"))
        self.assertNotEqual(a, wm.pin_id("tarmaas", "Old Vaisil"))

    def test_pin_types_are_known(self):
        from data.world import MAP_PIN_TYPES
        for m in wm.all_maps():
            for spec in wm.pins_for(m.key):
                self.assertIn(spec["pin_type"], MAP_PIN_TYPES, spec["name"])

    def test_the_campaign_hotspots_are_pinned(self):
        """Ne paikat joissa ryhmä oikeasti on."""
        cunae = {s["location_id"] for s in wm.pins_for("cunae")}
        for loc_id in ("loc_tarmaas", "loc_oblitus", "loc_fundarla",
                       "loc_aterterra", "loc_ravenstone",
                       "loc_fort_whitestone", "loc_zlalens", "loc_aesica"):
            self.assertIn(loc_id, cunae, loc_id)
        tarmaas = {s["location_id"] for s in wm.pins_for("tarmaas")}
        self.assertIn("loc_pinwud", tarmaas)     # Vigilin temppeli
        self.assertIn("loc_ravenstone", tarmaas)  # Dimeriuksen kaupunki


class TestApplyToWorld(unittest.TestCase):
    def setUp(self):
        self.cm = CampaignManagerState(_FM(), build_novus_somnium())
        self.world = self.cm.world

    def test_cunae_becomes_the_world_background(self):
        self.assertEqual(self.world.map_image_path,
                         wm.get_map("cunae").path)

    def test_each_kingdom_carries_its_own_map(self):
        for key in ("smardu", "tarmaas", "oblitus", "fundarla"):
            m = wm.get_map(key)
            self.assertEqual(self.world.locations[m.location_id].map_image_path,
                             m.path, key)

    def test_pins_were_created_for_every_map(self):
        by_key = {}
        for p in self.world.map_pins:
            by_key.setdefault(p.map_key, []).append(p)
        for m in wm.all_maps():
            self.assertEqual(len(by_key.get(m.key, [])),
                             len(wm.pins_for(m.key)), m.key)

    def test_no_pin_points_at_a_location_that_does_not_exist(self):
        dead = [(p.name, p.location_id) for p in self.world.map_pins
                if p.location_id and p.location_id not in self.world.locations]
        self.assertEqual(dead, [])

    def test_most_pins_link_somewhere(self):
        linked = [p for p in self.world.map_pins if p.location_id]
        self.assertGreaterEqual(len(linked), 30)

    def test_applying_twice_adds_nothing(self):
        before = len(self.world.map_pins)
        result = wm.apply_world_maps(self.world)
        self.assertEqual(result["added_pins"], 0)
        self.assertEqual(len(self.world.map_pins), before)

    def test_it_never_moves_a_pin_the_dm_already_placed(self):
        pin = self.world.map_pins[0]
        pin.map_x, pin.map_y, pin.name = 3.0, 4.0, "DM moved this"
        wm.apply_world_maps(self.world)
        again = next(p for p in self.world.map_pins if p.id == pin.id)
        self.assertEqual((again.map_x, again.map_y, again.name),
                         (3.0, 4.0, "DM moved this"))

    def test_it_never_overwrites_a_dm_chosen_background(self):
        world = World(name="test")
        world.map_image_path = "saves/map_backgrounds/mine.png"
        wm.apply_world_maps(world)
        self.assertEqual(world.map_image_path,
                         "saves/map_backgrounds/mine.png")

    def test_a_bare_world_gets_pins_but_no_dead_links(self):
        world = World(name="empty")
        result = wm.apply_world_maps(world)
        self.assertGreater(result["added_pins"], 0)
        self.assertEqual(result["missing_files"], [])
        self.assertTrue(all(not p.location_id for p in world.map_pins),
                        "linked a location that does not exist here")


class TestPersistence(unittest.TestCase):
    """Regressio: pins, tokens, shops ja services katosivat joka
    tallennuksessa — kumpikaan sarjallistuspolku ei kirjoittanut niitä."""

    def test_pins_survive_a_save_load_round_trip(self):
        cm = CampaignManagerState(_FM(), build_novus_somnium())
        before = len(cm.world.map_pins)
        self.assertGreater(before, 0)
        cm.campaign.world_data = cm._serialize_world()
        again = CampaignManagerState(_FM(), cm.campaign)
        self.assertEqual(len(again.world.map_pins), before)

    def test_map_key_survives_the_round_trip(self):
        cm = CampaignManagerState(_FM(), build_novus_somnium())
        cm.campaign.world_data = cm._serialize_world()
        again = CampaignManagerState(_FM(), cm.campaign)
        keys = {p.map_key for p in again.world.map_pins}
        self.assertEqual(keys, {"cunae", "smardu", "tarmaas", "oblitus",
                                "fundarla"})

    def test_a_hand_placed_pin_survives(self):
        cm = CampaignManagerState(_FM(), build_novus_somnium())
        pin = add_pin(cm.world, "Ambush here", "danger", 42.0, 17.0)
        pin.notes = "Kolme sutta ja metsästäjä."
        cm.campaign.world_data = cm._serialize_world()
        again = CampaignManagerState(_FM(), cm.campaign)
        found = next(p for p in again.world.map_pins if p.id == pin.id)
        self.assertEqual(found.name, "Ambush here")
        self.assertEqual(found.notes, "Kolme sutta ja metsästäjä.")
        self.assertEqual((found.map_x, found.map_y), (42.0, 17.0))

    def test_tokens_survive(self):
        from data.world import add_token
        cm = CampaignManagerState(_FM(), build_novus_somnium())
        tok = add_token(cm.world, "Party", "party", 30.0, 60.0)
        cm.campaign.world_data = cm._serialize_world()
        again = CampaignManagerState(_FM(), cm.campaign)
        found = next(t for t in again.world.map_tokens if t.id == tok.id)
        self.assertEqual((found.map_x, found.map_y), (30.0, 60.0))

    def test_shops_and_services_survive(self):
        cm = CampaignManagerState(_FM(), build_novus_somnium())
        shops_before = len(cm.world.shops)
        self.assertGreater(shops_before, 0)
        cm.campaign.world_data = cm._serialize_world()
        again = CampaignManagerState(_FM(), cm.campaign)
        self.assertEqual(len(again.world.shops), shops_before)

    def test_an_old_save_without_maps_is_upgraded(self):
        camp = build_novus_somnium()
        wd = camp.world_data
        wd.pop("map_pins", None)
        wd["map_image_path"] = ""
        for lid in ("loc_smardu", "loc_tarmaas", "loc_oblitus",
                    "loc_fundarla"):
            wd["locations"][lid].pop("map_image_path", None)
        cm = CampaignManagerState(_FM(), camp)
        self.assertEqual(cm.world.map_image_path, wm.get_map("cunae").path)
        self.assertGreater(len(cm.world.map_pins), 100)
        self.assertEqual(cm.world.locations["loc_tarmaas"].map_image_path,
                         wm.get_map("tarmaas").path)

    def test_upgrading_an_old_save_twice_does_not_duplicate(self):
        camp = build_novus_somnium()
        camp.world_data.pop("map_pins", None)
        first = CampaignManagerState(_FM(), camp)
        n = len(first.world.map_pins)
        first.campaign.world_data = first._serialize_world()
        second = CampaignManagerState(_FM(), first.campaign)
        self.assertEqual(len(second.world.map_pins), n)


class TestMapSwitcher(unittest.TestCase):
    def setUp(self):
        self.cm = CampaignManagerState(_FM(), build_novus_somnium())
        self.cm.active_tab = 4
        self.cm.world_map_mode = True
        self.screen = pygame.display.get_surface()

    def _frame(self):
        self.screen.fill((0, 0, 0))
        self.cm.draw(self.screen)

    def test_the_open_map_is_identified(self):
        self.assertEqual(self.cm.active_map_key(), "cunae")

    def test_switching_changes_the_background_and_resets_the_camera(self):
        self.cm.map_zoom = 3.0
        self.cm.map_offset_x = 500
        self.assertTrue(self.cm._switch_world_map("oblitus"))
        self.assertEqual(self.cm.active_map_key(), "oblitus")
        self.assertEqual(self.cm.world.map_image_path,
                         wm.get_map("oblitus").path)
        self.assertEqual(self.cm.map_zoom, 1.0)
        self.assertEqual(self.cm.map_offset_x, 0)

    def test_switching_to_the_same_map_is_a_no_op(self):
        self.assertFalse(self.cm._switch_world_map("cunae"))

    def test_unknown_map_is_refused(self):
        self.assertFalse(self.cm._switch_world_map("atlantis"))
        self.assertEqual(self.cm.active_map_key(), "cunae")

    def test_pins_follow_the_open_map(self):
        for key in ("cunae", "smardu", "tarmaas", "oblitus", "fundarla"):
            self.cm._switch_world_map(key)
            shown = self.cm._visible_map_pins()
            self.assertTrue(shown, key)
            self.assertTrue(all(p.map_key == key for p in shown), key)
            self.assertEqual(len(shown), len(wm.pins_for(key)), key)

    def test_a_hand_placed_pin_shows_on_every_sheet(self):
        """Pelinjohtajan omat merkinnät eivät saa kadota arkkia
        vaihtaessa."""
        loose = add_pin(self.cm.world, "My note", "note", 50.0, 50.0)
        loose.map_key = ""
        for key in ("cunae", "tarmaas", "fundarla"):
            self.cm._switch_world_map(key)
            self.assertIn(loose, self.cm._visible_map_pins(), key)

    def test_hidden_pins_are_not_drawn(self):
        pin = next(p for p in self.cm.world.map_pins if p.map_key == "cunae")
        pin.visible = False
        self.assertNotIn(pin, self.cm._visible_map_pins())

    def test_the_switcher_renders_a_chip_per_map(self):
        self._frame()
        keys = [k for _r, k in self.cm._map_switch_rects]
        self.assertEqual(set(keys), {m.key for m in wm.all_maps()})

    def test_clicking_a_chip_switches_the_map(self):
        self._frame()
        rect, key = next((r, k) for r, k in self.cm._map_switch_rects
                         if k == "fundarla")
        self.assertTrue(self.cm._handle_map_switcher_click(rect.center))
        self.assertEqual(self.cm.active_map_key(), "fundarla")

    def test_clicking_away_from_the_chips_does_nothing(self):
        self._frame()
        self.assertFalse(self.cm._handle_map_switcher_click((5, 900)))
        self.assertEqual(self.cm.active_map_key(), "cunae")

    def test_a_frame_renders_for_every_map(self):
        for m in wm.all_maps():
            self.cm._switch_world_map(m.key)
            self._frame()

    def test_a_new_hand_placed_pin_is_stamped_with_the_open_map(self):
        self.cm._switch_world_map("oblitus")
        self.cm._map_pin_mode = True
        grid = self.cm._get_map_grid_area()
        self.cm._handle_map_click(grid.center, grid)
        placed = next(p for p in self.cm.world.map_pins
                      if p.id == self.cm.selected_pin_id)
        self.assertEqual(placed.map_key, "oblitus")


if __name__ == "__main__":
    unittest.main()
