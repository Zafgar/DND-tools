"""Lvl 12 -mökkisession vastukset ja nimikkokohtaamiset.

Varmistaa että
  * kaikki 15 vastusta latautuvat kirjastosta oikein statein,
  * loitsijat ratkaisevat loitsunsa keskitetystä loitsukirjastosta
    nimellä (ei omia holdereita),
  * moniosaiset rider-vahingot (``1d8+3d6``) jäsentyvät,
  * AI osaa laskea vuoron jokaiselle vastukselle ilman kaatumista,
  * kahdeksan nimikkokohtaamista rakentuvat taisteluksi (terrain +
    hirviöt kirjastosta).
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

from data.library import library
from data.heroes import hero_list
from data.spells import has_spell
from engine.entities import Entity
from engine.battle import BattleSystem
from engine.ai import TacticalAI
from engine.dice import average_damage, roll_dice
from data import scenarios


FOES = [
    "Velve Dro Invisiittori", "Velve Dro Varjoterä",
    "Faerzress-Kiipeilijalisko", "Kreivitar Vila Norgrad",
    "Ravenstonen Ghoul-murskaaja", "A.E.G.I.S. Titaani",
    "Kellopeli-Eliminoija", "Shug Orgar -Sotapaallikko",
    "Emnarin Verimaagi", "Panssaroitu Sota-Bulette",
    "Vigilin Puhdistaja", "Verilahettilas",
    "Crimson Night-Stalker", "Red Dagger -Pyoveli",
    "Red Dagger -Varjokulkija",
]

LVL12_SCENARIOS = [
    "lvl12_velve_dro_patrol", "lvl12_ravenstone_veil",
    "lvl12_aegis_protocol", "lvl12_shug_orgar_strike",
    "lvl12_krusk_vs_purifier", "lvl12_krusk_vs_herald",
    "lvl12_padak_vs_stalker", "lvl12_red_dagger_ambush",
]


class TestLvl12FoesLoad(unittest.TestCase):
    def test_all_fifteen_load(self):
        for name in FOES:
            m = library.get_monster(name)
            self.assertGreater(m.hit_points, 0, name)
            self.assertGreaterEqual(m.armor_class, 14, name)

    def test_key_stat_blocks_match_pdf(self):
        cap = library.get_monster("Velve Dro Invisiittori")
        self.assertEqual((cap.armor_class, cap.hit_points), (17, 135))
        titan = library.get_monster("A.E.G.I.S. Titaani")
        self.assertEqual((titan.armor_class, titan.hit_points), (20, 210))
        vamp = library.get_monster("Kreivitar Vila Norgrad")
        self.assertEqual((vamp.armor_class, vamp.hit_points), (16, 144))
        self.assertEqual(vamp.legendary_action_count, 3)

    def test_casters_resolve_spells_from_library(self):
        vamp = library.get_monster("Kreivitar Vila Norgrad")
        known = {s.name for s in vamp.spells_known}
        for expected in ("Fireball", "Cloudkill", "Counterspell", "Blight"):
            self.assertIn(expected, known)
            self.assertTrue(has_spell(expected))
        cants = {s.name for s in vamp.cantrips}
        self.assertIn("Ray of Frost", cants)

    def test_inquisitor_resolves_spirit_guardians(self):
        inq = library.get_monster("Vigilin Puhdistaja")
        known = {s.name for s in inq.spells_known}
        self.assertIn("Spirit Guardians", known)

    def test_no_percreature_spell_holder(self):
        # Spells must come from the central library, so a resolved spell
        # object is a real library spell, not an empty placeholder.
        shaman = library.get_monster("Emnarin Verimaagi")
        haste = next(s for s in shaman.spells_known if s.name == "Haste")
        self.assertEqual(haste.level, 3)


class TestMultiTermRiderDamage(unittest.TestCase):
    def test_rider_damage_parses(self):
        # Faerzress Rapier: 1d8+5 piercing + 3d6 poison folded into dice.
        self.assertAlmostEqual(average_damage("1d8+3d6"), 15.0, places=1)
        for _ in range(20):
            r = roll_dice("1d10+4d6")
            self.assertGreaterEqual(r, 5)   # min 1 + 4
            self.assertLessEqual(r, 34)     # max 10 + 24

    def test_rider_actions_present(self):
        cap = library.get_monster("Velve Dro Invisiittori")
        rapier = next(a for a in cap.actions if a.name == "Faerzress Rapier")
        self.assertEqual(rapier.damage_dice, "1d8+3d6")
        self.assertEqual(rapier.damage_bonus, 5)


class TestLvl12AiTurns(unittest.TestCase):
    def test_ai_computes_turn_for_every_foe(self):
        heroes = hero_list[:3]
        ents = [Entity(h, 3, 3 + i * 2, is_player=True)
                for i, h in enumerate(heroes)]
        for j, name in enumerate(FOES):
            ents.append(Entity(library.get_monster(name), 12, 1 + j,
                               is_player=False))
        battle = BattleSystem(log_callback=lambda s: None,
                              initial_entities=ents)
        ai = TacticalAI()
        for e in ents:
            if e.is_player:
                continue
            plan = ai.calculate_turn(e, battle)
            self.assertIsNotNone(plan, e.name)


class TestLvl12Scenarios(unittest.TestCase):
    def test_all_eight_registered(self):
        for sid in LVL12_SCENARIOS:
            s = scenarios.get_scenario(sid)
            self.assertEqual(s.recommended_level_min, 12, sid)
            self.assertEqual(s.recommended_level_max, 12, sid)

    def test_scenarios_build_into_battle(self):
        for sid in LVL12_SCENARIOS:
            s = scenarios.get_scenario(sid)
            battle = scenarios.build_battle_from_scenario(s)
            self.assertEqual(len(battle.entities), len(s.monsters), sid)
            self.assertTrue(all(not e.is_player for e in battle.entities), sid)

    def test_duels_are_single_opponent(self):
        for sid in ("lvl12_krusk_vs_purifier", "lvl12_krusk_vs_herald",
                    "lvl12_padak_vs_stalker"):
            s = scenarios.get_scenario(sid)
            self.assertEqual(len(s.monsters), 1, sid)
            self.assertEqual(s.recommended_party_size, 1, sid)

    def test_scenario_monsters_exist_in_library(self):
        for sid in LVL12_SCENARIOS:
            s = scenarios.get_scenario(sid)
            for m in s.monsters:
                # Should not raise.
                library.get_monster(m.name)


if __name__ == "__main__":
    unittest.main()
