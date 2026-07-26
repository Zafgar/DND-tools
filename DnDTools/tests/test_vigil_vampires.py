"""Pinwudin Vigil-temppelin vampyyriongelma.

Kattaa statblockit, niiden kytkennän maailmaan (NPC:t, suhteet,
Lore-Codex) ja sen että AI osaa pelata jokaisen niistä.
"""
import sys
import os
import copy
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import unittest

import pygame
pygame.init()
pygame.display.set_mode((1920, 1080))

from data.library import library
from data.spells import has_spell
from data.heroes import hero_list
from data.novus_somnium import build_novus_somnium
from data import lore_codex as codex
from states.campaign_manager import CampaignManagerState
from engine.entities import Entity
from engine.battle import BattleSystem
from engine.ai import TacticalAI
from states.battle_state import BattleState


class _FM:
    def __init__(self):
        self.screen = pygame.display.get_surface()
        self.running = True
        self.states = {}

    def change_state(self, *a, **k):
        pass


# CR-portaikko, jonka pelinjohtaja voi ajaa läpi
ROSTER = [
    ("Verikuoron akolyytti", 4.0),
    ("Medicus Sanguinis", 5.0),
    ("Custos Nocturnus", 6.0),
    ("Sanguis Custos", 8.0),
    ("Confessor Ianus", 10.0),
    ("Magister Sanguinis Vhaltor", 11.0),
    ("Praefectus Sanguinis Ostorius", 13.0),
    ("Sanctum Abominatio", 16.0),
]


class TestRosterLoads(unittest.TestCase):
    def test_every_block_loads_at_the_intended_cr(self):
        for name, cr in ROSTER:
            m = library.get_monster(name)
            self.assertEqual(m.challenge_rating, cr, name)
            self.assertGreater(m.hit_points, 0, name)
            self.assertTrue(m.actions, name)

    def test_cr_ladder_is_monotonic(self):
        crs = [library.get_monster(n).challenge_rating for n, _ in ROSTER]
        self.assertEqual(crs, sorted(crs))

    def test_the_two_bosses_are_the_toughest(self):
        """HP ei nouse tiukasti CR:n mukana — Sanguis Custos on etulinjan
        tankki ja Confessor Ianus loitsija — mutta johtaja ja
        pyhäinjäännös ovat selvästi kestävimmät."""
        hp = {n: library.get_monster(n).hit_points for n, _ in ROSTER}
        toughest = sorted(hp, key=lambda n: -hp[n])[:2]
        self.assertEqual(set(toughest),
                         {"Praefectus Sanguinis Ostorius",
                          "Sanctum Abominatio"})
        mooks = ("Verikuoron akolyytti", "Medicus Sanguinis",
                 "Custos Nocturnus")
        for n in mooks:
            self.assertLess(hp[n], hp["Praefectus Sanguinis Ostorius"], n)

    def test_all_referenced_spells_exist(self):
        for name, _cr in ROSTER:
            m = library.get_monster(name)
            for s in list(m.spells_known) + list(m.cantrips):
                self.assertTrue(has_spell(s.name), f"{name} -> {s.name}")

    def test_everyone_has_dm_facing_text(self):
        for name, _cr in ROSTER:
            m = library.get_monster(name)
            self.assertTrue(m.lore, name)
            self.assertTrue(m.tactics, name)
            self.assertTrue(m.loot_table, name)
            self.assertIn("Pinwud", m.habitat, name)


class TestVampireRules(unittest.TestCase):
    """Vampyyrin heikkoudet ja regeneraatio ovat pelinjohtajan tärkeimmät
    työkalut, joten ne on oltava jokaisella lehdellä."""

    VAMPIRES = [n for n, _ in ROSTER if n != "Sanctum Abominatio"]

    def test_every_vampire_lists_its_weaknesses(self):
        for name in self.VAMPIRES:
            feats = {f.name: f for f in library.get_monster(name).features}
            self.assertIn("Vampyyrin heikkoudet", feats, name)
            d = feats["Vampyyrin heikkoudet"].description
            for bit in ("Auringonvalo", "juoksevaa vettä", "vaarna",
                        "regeneraation"):
                self.assertIn(bit, d, f"{name}: {bit}")

    def test_every_vampire_regenerates(self):
        for name in self.VAMPIRES:
            regen = next((f for f in library.get_monster(name).features
                          if f.mechanic == "regeneration"), None)
            self.assertIsNotNone(regen, name)
            self.assertGreater(int(regen.mechanic_value), 0, name)

    def test_all_are_undead_and_resist_necrotic(self):
        for name, _cr in ROSTER:
            m = library.get_monster(name)
            self.assertEqual(m.creature_type, "Undead", name)
            self.assertIn("necrotic", m.damage_resistances, name)

    def test_only_true_vampires_have_misty_escape(self):
        """Spawnit kuolevat kentällä; todelliset vampyyrit pakenevat
        arkkuunsa — pelinjohtajan on tiedettävä kumpi on kumpi."""
        with_escape = {n for n, _ in ROSTER
                       if any(f.name == "Misty Escape"
                              for f in library.get_monster(n).features)}
        self.assertEqual(with_escape,
                         {"Confessor Ianus", "Magister Sanguinis Vhaltor",
                          "Praefectus Sanguinis Ostorius"})

    def test_corrupted_divinity_lost_radiant_magic(self):
        """Turmeltunut pappi ei osaa enää loitsia valoa — se on vihje."""
        for name in ("Verikuoron akolyytti", "Medicus Sanguinis",
                     "Sanguis Custos", "Confessor Ianus",
                     "Praefectus Sanguinis Ostorius"):
            m = library.get_monster(name)
            feats = {f.name: f for f in m.features}
            self.assertIn("Turmeltunut jumaluus", feats, name)
            self.assertIn("Sacred Flame",
                          feats["Turmeltunut jumaluus"].description, name)
            known = {s.name for s in list(m.spells_known) + list(m.cantrips)}
            for radiant in ("Sacred Flame", "Guiding Bolt", "Sunbeam",
                            "Sunburst", "Word of Radiance", "Moonbeam"):
                self.assertNotIn(radiant, known, f"{name} still has {radiant}")

    def test_sanctum_abominatio_is_not_a_vampire(self):
        """Pelaajien vampyyrisuunnitelma ei tehoa pyhäinjäännökseen."""
        m = library.get_monster("Sanctum Abominatio")
        feats = {f.name: f for f in m.features}
        self.assertNotIn("Vampyyrin heikkoudet", feats)
        self.assertIn("Auringonvalo ei pure", feats)
        self.assertIn("Pyhitetty runko", feats)
        self.assertIn("Requiem", feats["Pyhitetty runko"].description)
        self.assertEqual(m.size, "Huge")


class TestSignatureAbilities(unittest.TestCase):
    def test_choir_scales_when_they_sing_together(self):
        m = library.get_monster("Verikuoron akolyytti")
        song = next(a for a in m.actions if a.name == "Kuolinvirsi")
        self.assertEqual(song.condition_dc, 12)
        self.assertIn("DC on 15", song.description)
        self.assertEqual(song.applies_condition, "Frightened")
        self.assertTrue(any(f.mechanic == "pack_tactics" for f in m.features))

    def test_medicus_heals_only_the_undead(self):
        m = library.get_monster("Medicus Sanguinis")
        feats = {f.name: f for f in m.features}
        d = feats["Turmeltunut jumaluus"].description
        self.assertIn("VAIN epäkuolleita", d)
        self.assertIn("vampyyrina", d)
        known = {s.name for s in m.spells_known}
        self.assertIn("Cure Wounds", known)
        self.assertIn("Revivify", known)

    def test_night_watch_uses_the_vigils_own_gear(self):
        m = library.get_monster("Custos Nocturnus")
        names = {a.name for a in m.actions}
        self.assertIn("Requiem-terä", names)
        self.assertIn("Pyhä varsijousi", names)
        self.assertIn("Vaarnaheitto", names)
        bow = next(a for a in m.actions if a.name == "Pyhä varsijousi")
        self.assertEqual(bow.applies_condition, "Restrained")
        sneak = next(f for f in m.features
                     if f.mechanic == "sneak_attack")
        self.assertEqual(sneak.mechanic_value, "3d6")

    def test_purificator_smite_blocks_healing(self):
        m = library.get_monster("Sanguis Custos")
        smite = next(a for a in m.actions if a.name == "Turmeltunut smite")
        self.assertEqual(smite.damage_type, "necrotic")
        self.assertIn("ei voi saada healingia", smite.description)
        self.assertTrue(any(f.name == "Turmeltunut smite" and f.recharge
                            for f in m.features))

    def test_confessor_passes_for_living(self):
        m = library.get_monster("Confessor Ianus")
        feats = {f.name: f for f in m.features}
        mask = feats["Elävän naamio"]
        self.assertIn("DC 25", mask.description)
        self.assertIn("Detect Evil and Good", mask.description)
        seal = next(a for a in m.actions if a.name == "Ripin sinetti")
        self.assertEqual(seal.applies_condition, "Charmed")
        self.assertEqual(seal.condition_dc, 17)
        self.assertEqual(m.legendary_action_count, 2)

    def test_librarian_reads_from_confiscated_artefacts(self):
        m = library.get_monster("Magister Sanguinis Vhaltor")
        feats = {f.name: f for f in m.features}
        self.assertEqual(feats["Epäpuhdas kirjasto"].uses_per_day, 3)
        burst = next(a for a in m.actions
                     if a.name == "Epäpuhtaan kirjaston avaus")
        self.assertIn("max HP laskee", burst.description)
        self.assertTrue(any(i.item_type == "wand" for i in m.items))

    def test_ostorius_is_the_master(self):
        m = library.get_monster("Praefectus Sanguinis Ostorius")
        feats = {f.name: f for f in m.features}
        self.assertEqual(feats["Isäntä"].aura_radius, 60)
        self.assertIn("pakenevat", feats["Isäntä"].description)
        grave = next(a for a in m.actions if a.name == "Hauta avautuu")
        self.assertIn("TUPLAVAHINGON", grave.description)
        self.assertIn("alttarin alle",
                      feats["Misty Escape"].description.lower())
        self.assertEqual(m.legendary_action_count, 3)
        self.assertEqual(m.legendary_resistance_count, 3)
        self.assertGreaterEqual(
            len([f for f in m.features if f.feature_type == "lair"]), 3)

    def test_ostorius_carries_the_dimerius_letter(self):
        """Kampanjan käännekohta on tavara, ei kohtaus."""
        m = library.get_monster("Praefectus Sanguinis Ostorius")
        letter = next(i for i in m.items if "sinettikirje" in i.name.lower())
        self.assertEqual(letter.rarity, "legendary")
        self.assertIn("sinettikirje", m.loot_table.lower())


class TestAiPlaysThemAll(unittest.TestCase):
    def test_ai_plans_a_turn_for_every_block(self):
        pc = Entity(copy.deepcopy(
            {h.name: h for h in hero_list}["Padak Onslaught"]), 3, 3,
            is_player=True)
        foes = [Entity(library.get_monster(n), 11, 1 + i, is_player=False)
                for i, (n, _cr) in enumerate(ROSTER)]
        b = BattleSystem(log_callback=lambda s: None,
                         initial_entities=[pc] + foes)
        b.start_combat()
        ai = TacticalAI()
        for e in foes:
            e.reset_turn()
            plan = ai.calculate_turn(e, b)
            self.assertIsNotNone(plan, e.name)

    def test_the_infestation_runs_as_an_auto_battle(self):
        random.seed(13)
        heroes = {h.name: h for h in hero_list}
        pcs = [Entity(copy.deepcopy(heroes[n]), 3 + (i % 3), 3 + i,
                      is_player=True)
               for i, n in enumerate(["Magnus Dragonius", "Balthazar",
                                      "Venris Galanodel",
                                      "Padak Onslaught", "Marduk"])]
        foes = [Entity(library.get_monster(n), 13, 3 + i * 2,
                       is_player=False)
                for i, n in enumerate(["Praefectus Sanguinis Ostorius",
                                       "Sanguis Custos", "Custos Nocturnus",
                                       "Medicus Sanguinis",
                                       "Verikuoron akolyytti"])]
        bs = BattleState(_FM(), entities=pcs + foes)
        bs._set_ai_mode("full_auto")
        for _ in range(4000):
            bs._process_auto_battle()
            if not bs.auto_battle:
                break
            if (not [e for e in bs.battle.entities
                     if e.is_player and e.hp > 0]
                    or not [e for e in bs.battle.entities
                            if not e.is_player and e.hp > 0]):
                break
        else:
            self.fail("auto-battle ei päättynyt")


class TestWiredIntoTheCampaign(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cm = CampaignManagerState(_FM(), build_novus_somnium())

    EXPECTED = {
        "npc_ostorius": "monster:Praefectus Sanguinis Ostorius",
        "npc_ianus": "monster:Confessor Ianus",
        "npc_vhaltor": "monster:Magister Sanguinis Vhaltor",
        "npc_livia": "monster:Medicus Sanguinis",
        "npc_bracca": "monster:Custos Nocturnus",
        "npc_neva": "monster:Verikuoron akolyytti",
        "npc_sanctum_abominatio": "monster:Sanctum Abominatio",
    }

    def test_all_have_npc_sheets_at_the_temple(self):
        for nid, src in self.EXPECTED.items():
            npc = self.cm.world.npcs.get(nid)
            self.assertIsNotNone(npc, nid)
            self.assertEqual(npc.stat_source, src, nid)
            self.assertEqual(npc.location_id, "loc_pinwud", nid)
            self.assertIsNotNone(self.cm._get_npc_stats(npc), nid)

    def test_they_still_hold_vigil_offices(self):
        """Peittely on koko juju: he esiintyvät yhä virassaan."""
        for nid in ("npc_ostorius", "npc_ianus", "npc_vhaltor",
                    "npc_livia", "npc_bracca", "npc_neva"):
            npc = self.cm.world.npcs[nid]
            self.assertEqual(npc.faction, "Death's Vigil", nid)
            self.assertIn("secret", npc.tags, nid)

    def test_no_npc_left_without_stats(self):
        broken = [(n.name, n.stat_source)
                  for n in self.cm.world.npcs.values()
                  if n.stat_source and self.cm._get_npc_stats(n) is None]
        self.assertEqual(broken, [])

    def test_dimerius_owns_ostorius_who_owns_the_rest(self):
        from data import npc_directory as nd
        links = {l["target_id"] for l
                 in nd.npc_links_of(self.cm.world, "npc_dimerius")}
        self.assertIn("npc_ostorius", links)
        own = {l["target_id"] for l
               in nd.npc_links_of(self.cm.world, "npc_ostorius")}
        for nid in ("npc_ianus", "npc_vhaltor", "npc_livia",
                    "npc_bracca", "npc_neva"):
            self.assertIn(nid, own, nid)
        # ja hän on Vigilin johdon vihollinen, vaikka he eivät tiedä
        self.assertIn("npc_gaius_marad", own)
        self.assertIn("npc_aurelia_valtar", own)

    def test_codex_article_exists_and_is_searchable(self):
        e = codex.get_entry("pinwud_vampyyriongelma")
        self.assertIsNotNone(e)
        self.assertTrue(e.spoiler)
        self.assertEqual(e.category, "uhat")
        for q in ("vampyyri", "pinwud", "ostorius", "verikuoro",
                  "sanctum abominatio", "sinettikirje"):
            keys = [h.key for h in codex.search(q)[:3]]
            self.assertIn("pinwud_vampyyriongelma", keys, f"{q!r} -> {keys}")

    def test_codex_article_lists_the_whole_cast_and_the_fix(self):
        e = codex.get_entry("pinwud_vampyyriongelma")
        for bit in ("VERIKUORO", "YÖVARTIO", "LÄÄKÄRI", "KIRJASTO",
                    "RIPPI-ISÄ", "ESIMIES", "PYHÄINJÄÄNNÖS",
                    "MITEN SE RATKAISTAAN", "ALTTARIN ALLE"):
            self.assertIn(bit, e.body, bit)
        for nid in self.EXPECTED:
            self.assertIn(nid, e.npc_ids, nid)
        self.assertIn("loc_pinwud", e.location_ids)

    def test_codex_cross_links_resolve(self):
        e = codex.get_entry("pinwud_vampyyriongelma")
        for k in e.see_also:
            self.assertIsNotNone(codex.get_entry(k), k)
        for nid in e.npc_ids:
            self.assertIn(nid, self.cm.world.npcs, nid)
        for lid in e.location_ids:
            self.assertIn(lid, self.cm.world.locations, lid)

    def test_stat_sheets_render(self):
        screen = pygame.display.get_surface()
        for nid in self.EXPECTED:
            self.cm._open_monster_lore(self.cm.world.npcs[nid])
            screen.fill((0, 0, 0))
            self.cm._monster_lore_modal.draw(screen)


if __name__ == "__main__":
    unittest.main()
