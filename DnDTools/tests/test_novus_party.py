"""Novus Somnium -kampanjan pelaajahahmot (taso 11).

Varmistaa että viisi pelaajahahmoa (Magnus, Balthazar, Venris, Padak,
Krusk) latautuvat hero_listiin, että loitsijat ratkaisevat loitsunsa
keskitetystä loitsukirjastosta nimellä ja että AI osaa laskea vuoron
jokaiselle ilman kaatumista.
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

from data.heroes import hero_list
from data.library import library
from data.spells import has_spell
from engine.entities import Entity
from engine.battle import BattleSystem
from engine.ai import TacticalAI


PARTY = {
    "Magnus Dragonius": ("Ranger", 11),
    "Balthazar": ("Warlock", 11),
    "Venris Galanodel": ("Wizard", 11),
    "Padak Onslaught": ("Fighter", 11),
    "Krusk": ("Barbarian", 11),
    "Beatrice": ("Warlock", 11),
    "Carlo": ("Barbarian", 11),
}


def _by_name():
    return {h.name: h for h in hero_list}


class TestNovusPartyLoads(unittest.TestCase):
    def test_all_five_in_hero_list(self):
        heroes = _by_name()
        for name, (cls, lvl) in PARTY.items():
            self.assertIn(name, heroes, name)
            h = heroes[name]
            self.assertEqual(h.character_class, cls, name)
            self.assertEqual(h.character_level, lvl, name)
            self.assertGreater(h.hit_points, 0, name)

    def test_key_stats_from_sheets(self):
        h = _by_name()
        self.assertEqual((h["Krusk"].armor_class, h["Krusk"].hit_points),
                         (15, 115))
        self.assertEqual(h["Magnus Dragonius"].armor_class, 17)
        self.assertEqual(h["Balthazar"].spell_save_dc, 16)
        self.assertEqual(h["Venris Galanodel"].abilities.intelligence, 18)

    def test_items_auto_assigned(self):
        h = _by_name()
        for name in PARTY:
            self.assertTrue(h[name].items, name)


class TestNovusPartySpells(unittest.TestCase):
    def test_casters_resolve_from_library(self):
        h = _by_name()
        venris = {s.name for s in h["Venris Galanodel"].spells_known}
        for sp in ("Fireball", "Counterspell", "Haste", "Wall of Force"):
            self.assertIn(sp, venris)
            self.assertTrue(has_spell(sp))
        balth = {s.name for s in h["Balthazar"].cantrips}
        self.assertIn("Eldritch Blast", balth)
        magnus = {s.name for s in h["Magnus Dragonius"].spells_known}
        self.assertIn("Hunter's Mark", magnus)

    def test_martials_have_no_spells(self):
        h = _by_name()
        self.assertEqual(len(h["Krusk"].spells_known), 0)
        self.assertEqual(len(h["Padak Onslaught"].spells_known), 0)
        self.assertEqual(len(h["Carlo"].spells_known), 0)

    def test_beatrice_is_hexblade(self):
        b = _by_name()["Beatrice"]
        self.assertEqual((b.armor_class, b.hit_points), (17, 89))
        known = {s.name for s in b.spells_known}
        self.assertIn("Shadow of Moil", known)
        self.assertIn("Hex", known)
        self.assertIn("Eldritch Blast", {s.name for s in b.cantrips})
        # Hexblade's Curse + pact-weapon extra attack are modelled.
        feats = {f.name for f in b.features}
        self.assertIn("Hexblade's Curse", feats)
        glaive = next(a for a in b.actions if a.name == "Pact Glaive")
        self.assertEqual(glaive.reach, 10)

    def test_carlo_is_berserker(self):
        c = _by_name()["Carlo"]
        self.assertEqual((c.armor_class, c.hit_points), (16, 115))
        self.assertEqual(c.rage_count, 4)
        feats = {f.name for f in c.features}
        self.assertIn("Frenzy", feats)
        self.assertIn("Intimidating Presence", feats)


class TestNovusPartyCombat(unittest.TestCase):
    def test_ai_computes_turn_for_each(self):
        heroes = _by_name()
        pcs = [Entity(heroes[n], 3, 3 + i, is_player=True)
               for i, n in enumerate(PARTY)]
        foes = [Entity(library.get_monster("Ravenstonen Ghoul-murskaaja"),
                       12, 3 + i, is_player=False) for i in range(3)]
        battle = BattleSystem(log_callback=lambda s: None,
                              initial_entities=pcs + foes)
        ai = TacticalAI()
        for e in pcs:
            self.assertIsNotNone(ai.calculate_turn(e, battle), e.name)

    def test_extra_attack_multiattack(self):
        h = _by_name()
        padak = next(a for a in h["Padak Onslaught"].actions
                     if a.is_multiattack)
        self.assertEqual(padak.multiattack_count, 3)
        krusk = next(a for a in h["Krusk"].actions if a.is_multiattack)
        self.assertEqual(krusk.multiattack_count, 2)


if __name__ == "__main__":
    unittest.main()
