"""Death's Vigil — statblockit, NPC:t, suhteet ja keskeneräisten
hahmojen täydentäminen.

Kattaa:
  * 7 uutta statblockia (Senatorum, Puhdistajat, Parantajat) + Commoner.
  * Gaius Maradin lähdedatan täsmäävyys (HP/AC/kykyarvot/savet).
  * Aurelian "tuplasmite" -paketti ja Thalgrumin legendaarinen taso.
  * Aurelia + Thalgrum NPC:inä, statlinkit ja johtokolmikon suhteet.
  * JOKAINEN kampanjan NPC ratkeaa statlehteen (ei enää keskeneräisiä),
    mukaan lukien uusi ``hero:``-linkki ja rikkinäinen monster:Commoner.
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

from data.library import library
from data.spells import has_spell
from data.novus_somnium import build_novus_somnium
from states.campaign_manager import CampaignManagerState
from engine.entities import Entity
from engine.battle import BattleSystem
from engine.ai import TacticalAI


class _FM:
    def __init__(self):
        self.screen = pygame.display.get_surface()
        self.running = True
        self.states = {}

    def change_state(self, *a, **k):
        pass


VIGIL = ["Gaius Marad", "Aurelia Valtar", "Thalgrum",
         "Praefectus Purificatorum", "Purificator", "Archimedicus",
         "Medicus Animae"]


class TestVigilStatBlocks(unittest.TestCase):
    def test_all_blocks_load(self):
        for name in VIGIL + ["Commoner"]:
            m = library.get_monster(name)
            self.assertGreater(m.hit_points, 0, name)
            self.assertGreaterEqual(m.armor_class, 10, name)

    def test_gaius_matches_source_data(self):
        g = library.get_monster("Gaius Marad")
        self.assertEqual((g.armor_class, g.hit_points), (20, 140))
        self.assertEqual(g.speed, 30)
        a = g.abilities
        self.assertEqual(
            (a.strength, a.dexterity, a.constitution,
             a.intelligence, a.wisdom, a.charisma),
            (12, 12, 18, 14, 20, 16))
        self.assertEqual(g.saving_throws.get("Wisdom"), 10)
        self.assertEqual(g.saving_throws.get("Charisma"), 8)
        feats = {f.name for f in g.features}
        for want in ("Channel Divinity: Path to the Grave",
                     "Eyes of the Grave", "Sentinel at Death's Door",
                     "Keeper of Souls"):
            self.assertIn(want, feats)

    def test_aurelia_double_smite_kit(self):
        a = library.get_monster("Aurelia Valtar")
        feats = {f.name: f for f in a.features}
        # The "double smite" needs Action Surge + Divine Smite + 2 attacks
        self.assertIn("Action Surge", feats)
        self.assertIn("Divine Smite", feats)
        self.assertEqual(feats["Action Surge"].mechanic, "action_surge")
        self.assertEqual(feats["Divine Smite"].mechanic, "divine_smite")
        multi = next(x for x in a.actions if x.is_multiattack)
        self.assertEqual(multi.multiattack_count, 2)
        # Ground-shaking wrath from the lore
        self.assertTrue(any(x.name == "Earthshaking Wrath" for x in a.actions))
        self.assertGreaterEqual(a.challenge_rating, 15.0)

    def test_thalgrum_is_the_biggest_threat(self):
        t = library.get_monster("Thalgrum")
        gaius = library.get_monster("Gaius Marad")
        aurelia = library.get_monster("Aurelia Valtar")
        # Padak's read: "a whole different level of threat"
        self.assertGreater(t.challenge_rating, gaius.challenge_rating)
        self.assertGreater(t.challenge_rating, aurelia.challenge_rating)
        self.assertEqual(t.legendary_action_count, 3)
        self.assertEqual(t.legendary_resistance_count, 3)
        self.assertGreaterEqual(t.spell_save_dc, 20)

    def test_all_referenced_spells_exist(self):
        for name in VIGIL:
            m = library.get_monster(name)
            for sp in list(m.spells_known) + list(m.cantrips):
                self.assertTrue(has_spell(sp.name),
                                f"{name} references missing spell {sp.name}")

    def test_ai_runs_every_vigil_block(self):
        foes = [Entity(library.get_monster(n), 12, 2 + i * 2, is_player=False)
                for i, n in enumerate(VIGIL)]
        pc = Entity(library.get_monster("Purificator"), 3, 3, is_player=True)
        b = BattleSystem(log_callback=lambda s: None,
                         initial_entities=[pc] + foes)
        b.start_combat()
        ai = TacticalAI()
        for e in foes:
            e.reset_turn()
            self.assertIsNotNone(ai.calculate_turn(e, b), e.name)


class TestVigilNpcs(unittest.TestCase):
    def setUp(self):
        self.cm = CampaignManagerState(_FM(), build_novus_somnium())

    def test_leaders_exist_with_stats(self):
        for nid, stat in (("npc_gaius_marad", "monster:Gaius Marad"),
                          ("npc_aurelia_valtar", "monster:Aurelia Valtar"),
                          ("npc_thalgrum", "monster:Thalgrum")):
            npc = self.cm.world.npcs.get(nid)
            self.assertIsNotNone(npc, nid)
            self.assertEqual(npc.stat_source, stat)
            self.assertIsNotNone(self.cm._get_npc_stats(npc))
            self.assertEqual(npc.faction, "Death's Vigil")
            self.assertEqual(npc.location_id, "loc_pinwud")

    def test_senatorum_relationships(self):
        from data import npc_directory as nd
        links = {(l["target_id"], l["kind"])
                 for l in nd.npc_links_of(self.cm.world, "npc_aurelia_valtar")}
        self.assertIn(("npc_marduk", "mentor"), links)      # trained Marduk
        self.assertIn(("npc_thalgrum", "rival"), links)     # sword vs book
        tl = {(l["target_id"], l["kind"])
              for l in nd.npc_links_of(self.cm.world, "npc_thalgrum")}
        self.assertIn(("npc_marduk", "other"), tl)          # research subject

    def test_organisation_lists_senatorum(self):
        from data import organizations as orgs
        org = orgs.find_organisation(self.cm.campaign, "deaths_vigil")
        self.assertIsNotNone(org)
        ids = {m.npc_id for m in org.members}
        for nid in ("npc_gaius_marad", "npc_aurelia_valtar", "npc_thalgrum",
                    "npc_marduk"):
            self.assertIn(nid, ids)


class TestNoIncompleteCharacters(unittest.TestCase):
    """"tee hahmot jotka ovat kesken täysin valmiiksi" — every NPC in the
    campaign must resolve to a usable stat sheet."""

    def setUp(self):
        self.cm = CampaignManagerState(_FM(), build_novus_somnium())

    def test_every_npc_has_a_stat_source(self):
        missing = [n.name for n in self.cm.world.npcs.values()
                   if not n.stat_source]
        self.assertEqual(missing, [], f"NPCs without stats: {missing}")

    def test_every_stat_source_resolves(self):
        broken = [(n.name, n.stat_source) for n in self.cm.world.npcs.values()
                  if n.stat_source and self.cm._get_npc_stats(n) is None]
        self.assertEqual(broken, [], f"broken stat links: {broken}")

    def test_hero_link_returns_player_sheet(self):
        npc = self.cm.world.npcs["npc_beatrice"]
        self.assertTrue(npc.stat_source.startswith("hero:"))
        stats = self.cm._get_npc_stats(npc)
        self.assertEqual(stats.name, "Beatrice")
        self.assertEqual(stats.hit_points, 89)
        # a real hero sheet carries spells
        self.assertTrue(stats.spells_known)

    def test_hero_link_handles_quoted_name(self):
        npc = self.cm.world.npcs["npc_darius"]
        stats = self.cm._get_npc_stats(npc)
        self.assertIsNotNone(stats)
        self.assertIn("Darius", stats.name)

    def test_commoner_block_exists(self):
        """6 NPCs pointed at monster:Commoner, which was missing."""
        c = library.get_monster("Commoner")
        self.assertEqual(c.challenge_rating, 0.0)
        self.assertTrue(c.actions)

    def test_hero_link_unknown_name_is_none(self):
        npc = self.cm.world.npcs["npc_beatrice"]
        npc.stat_source = "hero:Nobody At All"
        self.assertIsNone(self.cm._get_npc_stats(npc))


if __name__ == "__main__":
    unittest.main()
