"""Sijaintipohjaiset party-presetit + neljä uutta pelaajahahmoa.

Varmistaa että
  * Darius, ULV, Marduk ja Kairon latautuvat heroihin,
  * presetit ratkaisevat vain kirjastossa olevat hahmot ja ohittavat
    vielä lisäämättömät nimet (Beatrice, Carlo, Blitz),
  * ``preset_as_entities`` ei duplikoi jo roosterissa olevia pelaajia,
  * modaalin voi luoda ja piirtää ilman kaatumista.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import unittest

import pygame
pygame.init()
pygame.display.set_mode((1280, 720))

from data.heroes import hero_list
from data import party_presets as pp


NEW_PCS = {
    "Darius \"Slick\" Morin": ("Rogue", 10),
    "ULV": ("Druid", 11),
    "Marduk": ("Fighter", 11),
    "Kairon": ("Bard", 11),
}


class TestNewPlayerCharacters(unittest.TestCase):
    def test_four_new_pcs_present(self):
        heroes = {h.name: h for h in hero_list}
        for name, (cls, lvl) in NEW_PCS.items():
            self.assertIn(name, heroes, name)
            self.assertEqual(heroes[name].character_class, cls, name)
            self.assertEqual(heroes[name].character_level, lvl, name)

    def test_caster_spells_resolve(self):
        heroes = {h.name: h for h in hero_list}
        kairon = {s.name for s in heroes["Kairon"].spells_known}
        self.assertIn("Hypnotic Pattern", kairon)
        self.assertIn("Counterspell", kairon)
        ulv = {s.name for s in heroes["ULV"].spells_known}
        self.assertIn("Call Lightning", ulv)
        marduk = {s.name for s in heroes["Marduk"].spells_known}
        self.assertIn("Guiding Bolt", marduk)

    def test_rogue_has_sneak_attack(self):
        heroes = {h.name: h for h in hero_list}
        darius = heroes["Darius \"Slick\" Morin"]
        sneak = next(f for f in darius.features
                     if f.mechanic == "sneak_attack")
        self.assertEqual(sneak.mechanic_value, "5d6")


class TestPartyPresets(unittest.TestCase):
    def test_all_presets_resolvable(self):
        for p in pp.list_presets():
            found, missing = pp.resolve_members(p)
            self.assertIsInstance(found, list)
            # Every found entry is a real hero object.
            for h in found:
                self.assertTrue(hasattr(h, "character_class"))

    def test_solo_location_presets(self):
        rav, _ = pp.resolve_members(pp.get_preset("ravenstone"))
        self.assertEqual([h.name for h in rav], ["Padak Onslaught"])
        aes, _ = pp.resolve_members(pp.get_preset("aesica"))
        self.assertEqual([h.name for h in aes], ["Krusk"])

    def test_future_members_skipped_not_error(self):
        found, missing = pp.resolve_members(pp.get_preset("aterterra"))
        names = [h.name for h in found]
        self.assertIn("Magnus Dragonius", names)
        self.assertIn("Kairon", names)
        self.assertIn("Beatrice", missing)  # not yet added

    def test_entities_are_players(self):
        ents = pp.preset_as_entities(pp.get_preset("full"))
        self.assertTrue(ents)
        self.assertTrue(all(e.is_player for e in ents))

    def test_no_duplicate_when_stacking(self):
        roster = list(pp.preset_as_entities(pp.get_preset("aterterra")))
        roster.extend(pp.preset_as_entities(pp.get_preset("full"), roster))
        names = [e.name for e in roster]
        self.assertEqual(len(names), len(set(names)))


class TestPartyPickerModal(unittest.TestCase):
    def test_modal_draw(self):
        from states.party_picker_modal import PartyPickerModal
        m = PartyPickerModal(on_load=lambda p: None)
        m.open()
        m.selected = pp.list_presets()[1]
        m.draw(pygame.display.get_surface())  # should not raise

    def test_confirm_calls_on_load(self):
        from states.party_picker_modal import PartyPickerModal
        picked = []
        m = PartyPickerModal(on_load=lambda p: picked.append(p))
        m.open()
        m.selected = pp.get_preset("ravenstone")
        m._confirm_load()
        self.assertEqual(picked[0].id, "ravenstone")
        self.assertFalse(m.is_open)


if __name__ == "__main__":
    unittest.main()
