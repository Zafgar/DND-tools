"""Ravenstone — Dimeriuksen hovi, kryptan vartijat ja kaupungin hahmot.

Kattaa:
  * Dimerius CR 20 -buffauksen ja lähdedatan mukaiset kyvyt.
  * Golberan ja Xalarsin lore-kyvyt (Myrkkypallo/Leap, Warp Axe/ENRAGE).
  * Vampyyrihovin ja kaupungin hahmojen omat statblockit — NPC:t eivät
    enää käytä geneerisiä "Vampire"/"Assassin"-pohjia.
  * Regressio: summonin AI merkitsee toimintonsa käytetyksi, joten
    auto-battle ei anna sille ääretöntä määrää vuoroja.
"""
import sys
import os
import copy

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import unittest

import pygame
pygame.init()
pygame.display.set_mode((1280, 720))

from data.library import library
from data.spells import has_spell
from data.heroes import hero_list
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


RAVENSTONE = [
    "Lordi Dimerius Blackfeet", "Golbera", "Xalars",
    "Paroni Jugorai Millwind", "Polsen", "Beatrice Rask (vampyyri)",
    "Vilan Norgrad", "Herold Reggefoi", "Davos Wolfbane", "Aksel Wolfbane",
    "Lidian Stramroot", "Greg Silverhand", "Gaur Rakek", "Jivin Lukom",
    "Fior Rask", "Zemok Retana",
]


class TestRavenstoneBlocks(unittest.TestCase):
    def test_all_blocks_load(self):
        for name in RAVENSTONE:
            m = library.get_monster(name)
            self.assertGreater(m.hit_points, 0, name)

    def test_all_referenced_spells_exist(self):
        for name in RAVENSTONE:
            m = library.get_monster(name)
            for sp in list(m.spells_known) + list(m.cantrips):
                self.assertTrue(has_spell(sp.name),
                                f"{name} -> missing spell {sp.name}")

    def test_ai_runs_every_block(self):
        pc = Entity(copy.deepcopy(
            {h.name: h for h in hero_list}["Padak Onslaught"]), 3, 3,
            is_player=True)
        foes = [Entity(library.get_monster(n), 12, 1 + i, is_player=False)
                for i, n in enumerate(RAVENSTONE)]
        b = BattleSystem(log_callback=lambda s: None,
                         initial_entities=[pc] + foes)
        b.start_combat()
        ai = TacticalAI()
        for e in foes:
            e.reset_turn()
            self.assertIsNotNone(ai.calculate_turn(e, b), e.name)


class TestDimerius(unittest.TestCase):
    def setUp(self):
        self.d = library.get_monster("Lordi Dimerius Blackfeet")

    def test_buffed_to_cr20(self):
        """Source says CR 18; the DM asked for CR 20."""
        self.assertEqual(self.d.challenge_rating, 20.0)
        self.assertGreater(self.d.hit_points, 225)   # buffed past source HP
        self.assertEqual(self.d.legendary_action_count, 3)
        self.assertEqual(self.d.legendary_resistance_count, 3)

    def test_source_stats_kept(self):
        self.assertEqual(self.d.armor_class, 20)
        self.assertEqual(self.d.speed, 40)
        a = self.d.abilities
        self.assertEqual(
            (a.strength, a.dexterity, a.constitution,
             a.intelligence, a.wisdom, a.charisma),
            (20, 18, 22, 16, 18, 22))

    def test_immunities_and_resistances(self):
        self.assertIn("poison", self.d.damage_immunities)
        for cond in ("Charmed", "Frightened", "Poisoned", "Exhaustion"):
            self.assertIn(cond, self.d.condition_immunities)
        self.assertTrue(any("necrotic" in r for r in self.d.damage_resistances))

    def test_signature_abilities(self):
        feats = {f.name: f for f in self.d.features}
        self.assertIn("Regeneration", feats)
        self.assertEqual(feats["Regeneration"].mechanic_value, "20")
        self.assertIn("Misty Escape", feats)
        self.assertIn("Shapechanger", feats)
        self.assertIn("Spider Climb", feats)
        self.assertIn("Life Drain", feats)
        # buffed extras
        self.assertIn("Crimson Command", feats)
        names = {a.name for a in self.d.actions}
        self.assertIn("Life Drain Bite", names)
        self.assertIn("Exsanguinate", names)

    def test_has_lair_actions(self):
        lair = [f for f in self.d.features if f.feature_type == "lair"]
        self.assertGreaterEqual(len(lair), 2)

    def test_stronger_than_the_crypt_guards(self):
        for guard in ("Golbera", "Xalars"):
            self.assertGreater(self.d.challenge_rating,
                               library.get_monster(guard).challenge_rating)


class TestCryptGuards(unittest.TestCase):
    def test_golbera_source_numbers(self):
        g = library.get_monster("Golbera")
        self.assertEqual(g.hit_points, 250)      # source: 250 HP
        pb = next(a for a in g.actions if a.name == "Myrkkypallo")
        self.assertEqual(pb.range, 50)           # 50 ft range
        self.assertEqual(pb.aoe_radius, 15)      # 15 ft burst
        self.assertEqual(pb.damage_dice, "6d8")  # 6d8 poison
        self.assertEqual(pb.condition_dc, 14)    # DC 14
        leap = next(f for f in g.features if f.name == "Leap")
        self.assertEqual(leap.feature_type, "reaction")
        self.assertEqual(leap.save_dc, 12)       # DC 12 Dex
        self.assertEqual(leap.applies_condition, "Prone")

    def test_xalars_abilities(self):
        x = library.get_monster("Xalars")
        self.assertEqual(x.legendary_action_count, 2)   # "2 pistettä"
        feats = {f.name: f for f in x.features}
        self.assertIn("Reaction: Warp Axe", feats)
        self.assertEqual(feats["Reaction: Warp Axe"].feature_type, "reaction")
        enr = next(a for a in x.actions if a.name == "ENRAGE")
        self.assertEqual(enr.damage_dice, "3d12")       # 3d12 automatic fire
        self.assertEqual(enr.damage_type, "fire")
        self.assertIn("fire", x.damage_immunities)


class TestRavenstoneNpcsWired(unittest.TestCase):
    def setUp(self):
        self.cm = CampaignManagerState(_FM(), build_novus_somnium())

    def test_npcs_use_their_own_blocks(self):
        expected = {
            "npc_dimerius": "monster:Lordi Dimerius Blackfeet",
            "npc_jugorai": "monster:Paroni Jugorai Millwind",
            "npc_polsen": "monster:Polsen",
            "npc_vilan": "monster:Vilan Norgrad",
            "npc_herold": "monster:Herold Reggefoi",
            "npc_davos": "monster:Davos Wolfbane",
            "npc_aksel": "monster:Aksel Wolfbane",
            "npc_greg": "monster:Greg Silverhand",
            "npc_gaur": "monster:Gaur Rakek",
            "npc_jivin": "monster:Jivin Lukom",
        }
        for nid, src in expected.items():
            npc = self.cm.world.npcs[nid]
            self.assertEqual(npc.stat_source, src, nid)
            self.assertIsNotNone(self.cm._get_npc_stats(npc), nid)

    def test_new_npcs_added(self):
        for nid in ("npc_golbera", "npc_xalars", "npc_beatrice_vampyyri",
                    "npc_lidian"):
            npc = self.cm.world.npcs.get(nid)
            self.assertIsNotNone(npc, nid)
            self.assertIsNotNone(self.cm._get_npc_stats(npc), nid)

    def test_vampire_beatrice_is_distinct_from_pc(self):
        npc = self.cm.world.npcs["npc_beatrice_vampyyri"]
        self.assertNotEqual(npc.name, "Beatrice")
        self.assertIn("vampyyri", npc.name.lower())
        # the PC Beatrice still mirrors the hero sheet
        pc = self.cm.world.npcs["npc_beatrice"]
        self.assertTrue(pc.stat_source.startswith("hero:"))

    def test_crypt_guards_serve_dimerius(self):
        from data import npc_directory as nd
        links = {(l["target_id"], l["kind"])
                 for l in nd.npc_links_of(self.cm.world, "npc_dimerius")}
        self.assertIn(("npc_golbera", "subordinate"), links)
        self.assertIn(("npc_xalars", "subordinate"), links)

    def test_wolfbane_brothers_linked(self):
        from data import npc_directory as nd
        links = {(l["target_id"], l["kind"])
                 for l in nd.npc_links_of(self.cm.world, "npc_aksel")}
        self.assertIn(("npc_davos", "family"), links)

    def test_no_npc_left_without_stats(self):
        missing = [n.name for n in self.cm.world.npcs.values()
                   if not n.stat_source]
        broken = [(n.name, n.stat_source) for n in self.cm.world.npcs.values()
                  if n.stat_source and self.cm._get_npc_stats(n) is None]
        self.assertEqual(missing, [])
        self.assertEqual(broken, [])


class TestSummonTurnLoopFixed(unittest.TestCase):
    """Regression: _handle_summon_turn never set action_used, so the
    auto-battle loop re-planned the same summon forever — one Construct
    Spirit could solo a boss while nobody else acted."""

    def _summon(self):
        caster = Entity(copy.deepcopy(
            {h.name: h for h in hero_list}["Venris Galanodel"]), 3, 3,
            is_player=True)
        foe = Entity(library.get_monster("Golbera"), 10, 3, is_player=False)
        b = BattleSystem(log_callback=lambda s: None,
                         initial_entities=[caster, foe])
        b.start_combat()
        s = b.spawn_summon(caster, "Construct Spirit", 8, 3, hp=40, ac=13,
                           damage_dice="1d8+4", duration=10,
                           spell_name="Summon Construct")
        s.reset_turn()
        return b, s

    def test_summon_marks_action_used(self):
        b, s = self._summon()
        plan = TacticalAI().calculate_turn(s, b)
        self.assertTrue(plan.steps)
        self.assertTrue(s.action_used,
                        "summon must spend its action or it loops forever")

    def test_familiar_marks_action_used(self):
        caster = Entity(copy.deepcopy(
            {h.name: h for h in hero_list}["Venris Galanodel"]), 3, 3,
            is_player=True)
        foe = Entity(library.get_monster("Golbera"), 10, 3, is_player=False)
        b = BattleSystem(log_callback=lambda s: None,
                         initial_entities=[caster, foe])
        b.start_combat()
        fam = b.spawn_summon(caster, "Familiar", 4, 3, hp=1, ac=11,
                             duration=10, spell_name="Find Familiar")
        fam.reset_turn()
        TacticalAI().calculate_turn(fam, b)
        self.assertTrue(fam.action_used)

    def test_turn_order_includes_summon_once_per_round(self):
        b, s = self._summon()
        seen = []
        for _ in range(9):
            seen.append(b.get_current_entity().name)
            b.next_turn()
        # 3 combatants -> each name appears exactly 3 times in 9 turns
        self.assertEqual(seen.count(s.name), 3)


if __name__ == "__main__":
    unittest.main()
