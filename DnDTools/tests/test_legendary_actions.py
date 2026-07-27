"""Legendaariset toiminnot ja lair-toiminnot.

Statblock voi julistaa legendaarisen tai lair-toiminnon kahdella
tavalla: ``Action``-rivinä tai ``Feature``-rivinä. Koko Novus Somnium
-kokoelma käyttää jälkimmäistä — siellä ovat kustannus, recharge,
pelastusheiton DC ja teksti — mutta molemmat käyttäjät osasivat lukea
vain Action-rivejä. 23 legendaarista olentoa ei käyttänyt yhtään
legendaarista toimintoa ja viiden bossin lair-toiminnot eivät koskaan
lauenneet.
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
from data.heroes import hero_list
from data.models import CreatureStats, AbilityScores, Action, Feature
from engine.entities import Entity
from engine.battle import BattleSystem
from engine.ai import TacticalAI
from engine.rules import should_use_lair_action
from engine.special_actions import (
    resolve_special_actions, has_lair_actions, SpecialAction,
)
from states.battle_state import BattleState


class _FM:
    def __init__(self):
        self.screen = pygame.display.get_surface()
        self.running = True
        self.states = {}

    def change_state(self, *a, **k):
        pass


def _hero(name="Magnus Dragonius"):
    return copy.deepcopy({h.name: h for h in hero_list}[name])


LEGENDARY = [m.name for m in library.get_all_monsters()
             if m.legendary_action_count > 0
             or any(f.feature_type == "legendary" for f in m.features)]

LAIR_OWNERS = [m.name for m in library.get_all_monsters()
               if has_lair_actions(m)]


def _arena(monster_name, lair=False, gap=1):
    """The monster with three heroes right next to it."""
    e = Entity(library.get_monster(monster_name), 10, 5, is_player=False)
    pcs = [Entity(_hero(), 10 - gap, 4 + i, is_player=True)
           for i in range(3)]
    b = BattleSystem(log_callback=lambda s: None,
                     initial_entities=pcs + [e])
    b.lair_enabled = lair
    b.start_combat()
    return b, e, pcs


class TestResolver(unittest.TestCase):
    def test_an_action_declared_ability_resolves(self):
        stats = CreatureStats(
            name="Old School", hit_points=100,
            actions=[Action("Tail Attack", "", 8, "2d8", 4, "bludgeoning",
                            action_type="legendary")],
            features=[Feature("Tail Attack", "", feature_type="legendary")],
            legendary_action_count=3)
        found = resolve_special_actions(stats, "legendary")
        self.assertEqual(len(found), 1)
        self.assertIsNotNone(found[0].action)
        self.assertEqual(found[0].name, "Tail Attack")

    def test_a_feature_only_ability_resolves_from_its_own_numbers(self):
        stats = CreatureStats(
            name="Modern", hit_points=100,
            features=[Feature("Crystal Bolt", "A bolt of force.",
                              feature_type="legendary", legendary_cost=2,
                              damage_dice="6d8", damage_type="lightning",
                              save_dc=23, save_ability="Dexterity")],
            legendary_action_count=3)
        found = resolve_special_actions(stats, "legendary")
        self.assertEqual(len(found), 1)
        act = found[0].action
        self.assertIsNotNone(act)
        self.assertEqual(act.damage_dice, "6d8")
        self.assertEqual(act.condition_dc, 23)
        self.assertEqual(act.condition_save, "Dexterity")
        self.assertEqual(found[0].cost, 2)

    def test_an_attack_flavoured_feature_borrows_the_best_weapon(self):
        stats = CreatureStats(
            name="Basher", hit_points=100,
            actions=[Action("Club", "", 5, "1d6", 2, "bludgeoning"),
                     Action("Greatsword", "", 9, "2d6", 5, "slashing")],
            features=[Feature("Legendaarinen: Isku",
                              "Tekee yhden aseiskun.",
                              feature_type="legendary")],
            legendary_action_count=3)
        found = resolve_special_actions(stats, "legendary")
        self.assertEqual(found[0].intent, "attack")
        self.assertEqual(found[0].action.damage_dice, "2d6")   # the bigger one
        self.assertEqual(found[0].action.name, "Legendaarinen: Isku")

    def test_a_movement_feature_is_recognised_as_a_move(self):
        stats = CreatureStats(
            name="Runner", hit_points=100,
            features=[Feature("Legendaarinen: Liike",
                              "Liikkuu koko nopeutensa provosoimatta.",
                              feature_type="legendary")],
            legendary_action_count=3)
        found = resolve_special_actions(stats, "legendary")
        self.assertEqual(found[0].intent, "move")
        self.assertIsNone(found[0].action)

    def test_a_spell_feature_is_recognised(self):
        stats = CreatureStats(
            name="Caster", hit_points=100,
            features=[Feature("Legendaarinen: Loitsu",
                              "Loitsii yhden cantripin.",
                              feature_type="legendary")],
            legendary_action_count=3)
        self.assertEqual(resolve_special_actions(stats, "legendary")[0].intent,
                         "spell")

    def test_lair_and_legendary_do_not_bleed_into_each_other(self):
        stats = CreatureStats(
            name="Both", hit_points=100,
            features=[Feature("Leg", "", feature_type="legendary"),
                      Feature("Lair thing", "", feature_type="lair")],
            legendary_action_count=3)
        leg = resolve_special_actions(stats, "legendary")
        lair = resolve_special_actions(stats, "lair")
        self.assertEqual([s.name for s in leg], ["Leg"])
        self.assertEqual([s.name for s in lair], ["Lair thing"])

    def test_a_stat_block_with_nothing_resolves_to_nothing(self):
        stats = CreatureStats(name="Plain", hit_points=10)
        self.assertEqual(resolve_special_actions(stats, "legendary"), [])
        self.assertFalse(has_lair_actions(stats))

    def test_duplicates_are_not_returned_twice(self):
        stats = CreatureStats(
            name="Dup", hit_points=100,
            actions=[Action("Bite", "", 8, "2d6", 4, "piercing",
                            action_type="legendary")],
            features=[Feature("Bite", "", feature_type="legendary")],
            legendary_action_count=3)
        self.assertEqual(len(resolve_special_actions(stats, "legendary")), 1)


class TestEveryLegendaryCreatureUsesThem(unittest.TestCase):
    def test_none_are_inert(self):
        """23 olentoa ei käyttänyt yhtään legendaarista toimintoa."""
        inert = []
        for name in LEGENDARY:
            random.seed(6)
            b, e, _pcs = _arena(name)
            e.reset_legendary_actions()
            step = TacticalAI().calculate_legendary_action(e, b)
            if step is None:
                inert.append(name)
        self.assertEqual(inert, [])

    def test_the_campaign_bosses_use_theirs(self):
        for name in ("Keisari Tarquvas Redfei", "Cazna Icharyd",
                     "Praefectus Sanguinis Ostorius",
                     "Lordi Dimerius Blackfeet", "Sanctum Abominatio",
                     "Confessor Ianus", "Thalgrum", "Xalars"):
            random.seed(6)
            b, e, _pcs = _arena(name)
            e.reset_legendary_actions()
            step = TacticalAI().calculate_legendary_action(e, b)
            self.assertIsNotNone(step, name)
            self.assertEqual(step.step_type, "legendary", name)
            self.assertTrue(step.action_name, name)

    def test_actions_are_spent_and_run_out(self):
        random.seed(6)
        b, e, _pcs = _arena("Keisari Tarquvas Redfei")
        e.reset_legendary_actions()
        budget = e.legendary_actions_left
        self.assertGreater(budget, 0)
        ai = TacticalAI()
        spent = 0
        while ai.calculate_legendary_action(e, b) is not None:
            spent += 1
            self.assertLess(spent, 12, "never ran out of legendary actions")
        self.assertGreater(spent, 0)
        self.assertLessEqual(e.legendary_actions_left, 0)

    def test_a_two_point_ability_costs_two(self):
        stats = CreatureStats(
            name="Pricey", hit_points=100, armor_class=15,
            abilities=AbilityScores(strength=18),
            features=[Feature("Big Blast", "A blast.",
                              feature_type="legendary", legendary_cost=2,
                              damage_dice="6d8", damage_type="fire",
                              save_dc=17, save_ability="Dexterity")],
            legendary_action_count=3)
        e = Entity(stats, 10, 5, is_player=False)
        pcs = [Entity(_hero(), 9, 4 + i, is_player=True) for i in range(2)]
        b = BattleSystem(log_callback=lambda s: None,
                         initial_entities=pcs + [e])
        b.start_combat()
        e.reset_legendary_actions()
        before = e.legendary_actions_left
        step = TacticalAI().calculate_legendary_action(e, b)
        self.assertIsNotNone(step)
        self.assertEqual(before - e.legendary_actions_left, 2)

    def test_an_incapacitated_creature_uses_none(self):
        random.seed(6)
        b, e, _pcs = _arena("Cazna Icharyd")
        e.reset_legendary_actions()
        e.add_condition("Stunned")
        self.assertIsNone(TacticalAI().calculate_legendary_action(e, b))

    def test_a_dead_creature_uses_none(self):
        random.seed(6)
        b, e, _pcs = _arena("Cazna Icharyd")
        e.reset_legendary_actions()
        e.hp = 0
        self.assertIsNone(TacticalAI().calculate_legendary_action(e, b))

    def test_they_are_not_used_through_a_wall(self):
        from engine.terrain import TerrainObject
        random.seed(6)
        b, e, _pcs = _arena("Lordi Dimerius Blackfeet", gap=4)
        b.terrain = [TerrainObject("wall", 8, y) for y in range(-20, 30)]
        e.reset_legendary_actions()
        step = TacticalAI().calculate_legendary_action(e, b)
        if step is not None:
            for t in list(step.targets or []) + ([step.target]
                                                 if step.target else []):
                self.assertTrue(b.has_line_of_sight(e, t), step.description)

    def test_the_queue_refills_at_the_start_of_its_turn(self):
        random.seed(6)
        b, e, _pcs = _arena("Cazna Icharyd")
        e.reset_legendary_actions()
        full = e.legendary_actions_left
        e.legendary_actions_left = 0
        e.reset_legendary_actions()
        self.assertEqual(e.legendary_actions_left, full)


class TestMonsterManualCorrections(unittest.TestCase):
    """Kolmella olennolla oli legendaarisia toimintoja joita ei MM:ssä
    ole, ja kolmelta puuttuivat omansa kokonaan."""

    def test_creatures_without_mm_legendary_actions_declare_none(self):
        for name in ("Storm Giant", "Death Knight", "Pit Fiend"):
            m = library.get_monster(name)
            self.assertEqual(m.legendary_action_count, 0, name)

    def test_the_iconic_monsters_have_theirs(self):
        expected = {
            "Ancient Red Dragon": {"Detect", "Tail Attack", "Wing Attack"},
            "Beholder": {"Eye Ray"},
            "Death Tyrant": {"Eye Ray"},
        }
        for name, wanted in expected.items():
            m = library.get_monster(name)
            got = {f.name for f in m.features
                   if f.feature_type == "legendary"}
            self.assertTrue(wanted <= got, f"{name}: {got}")

    def test_the_ancient_dragons_wing_attack_costs_two(self):
        m = library.get_monster("Ancient Red Dragon")
        wing = next(f for f in m.features
                    if f.name == "Wing Attack"
                    and f.feature_type == "legendary")
        self.assertEqual(wing.legendary_cost, 2)

    def test_no_creature_reserves_legendary_actions_it_cannot_use(self):
        """legendary_action_count > 0 ilman yhtään kykyä varaa vuoroja
        joita ei voi koskaan käyttää."""
        empty = []
        for m in library.get_all_monsters():
            if m.legendary_action_count <= 0:
                continue
            if not resolve_special_actions(m, "legendary"):
                empty.append(m.name)
        self.assertEqual(empty, [])


class TestLairActions(unittest.TestCase):
    def test_feature_declared_lair_owners_are_detected(self):
        for name in ("Praefectus Sanguinis Ostorius", "Cazna Icharyd",
                     "Keisari Tarquvas Redfei", "Sanctum Abominatio",
                     "Lordi Dimerius Blackfeet"):
            m = library.get_monster(name)
            self.assertTrue(has_lair_actions(m), name)
            self.assertTrue(should_use_lair_action(
                Entity(m, 0, 0, is_player=False)), name)

    def test_a_lair_entity_joins_initiative(self):
        for name in ("Cazna Icharyd", "Adult Red Dragon"):
            b, _e, _pcs = _arena(name, lair=True)
            lair = [x for x in b.entities if x.is_lair]
            self.assertEqual(len(lair), 1, name)
            self.assertEqual(lair[0].initiative, 20, name)

    def test_no_lair_entity_outside_the_lair(self):
        b, _e, _pcs = _arena("Cazna Icharyd", lair=False)
        self.assertEqual([x for x in b.entities if x.is_lair], [])

    def test_every_lair_owner_actually_acts(self):
        inert = []
        for name in LAIR_OWNERS:
            random.seed(8)
            b, _e, _pcs = _arena(name, lair=True)
            lair = [x for x in b.entities if x.is_lair]
            if not lair:
                inert.append((name, "no lair entity"))
                continue
            plan = TacticalAI().calculate_turn(lair[0], b)
            if plan.skipped or not plan.steps:
                inert.append((name, plan.skip_reason or "no steps"))
        self.assertEqual(inert, [])

    def test_the_same_lair_action_is_not_repeated(self):
        """MM: samaa lair-toimintoa ei saa käyttää kahtena peräkkäisenä
        kierroksena."""
        random.seed(8)
        b, _e, _pcs = _arena("Keisari Tarquvas Redfei", lair=True)
        lair = next(x for x in b.entities if x.is_lair)
        ai = TacticalAI()
        first = ai.calculate_turn(lair, b)
        self.assertTrue(first.steps)
        name = first.steps[0].action_name
        self.assertEqual(lair.last_lair_action, name)
        second = ai.calculate_turn(lair, b)
        if second.steps:
            self.assertNotEqual(second.steps[0].action_name, name)

    def test_a_dead_owner_silences_the_lair(self):
        b, e, _pcs = _arena("Cazna Icharyd", lair=True)
        lair = next(x for x in b.entities if x.is_lair)
        e.hp = 0
        plan = TacticalAI().calculate_turn(lair, b)
        self.assertTrue(plan.skipped)


class TestLegendaryInAFullFight(unittest.TestCase):
    def test_the_lair_does_not_deadlock_the_turn_order(self):
        """Regressio: lair-vuoro ei koskaan kuluttanut toimintoaan, joten
        auto-battle jäi pyörimään initiative 20:ssa eikä kukaan muu
        toiminut."""
        random.seed(21)
        pcs = [Entity(_hero(), 3, 3 + i, is_player=True) for i in range(3)]
        boss = Entity(library.get_monster("Praefectus Sanguinis Ostorius"),
                      9, 5, is_player=False)
        bs = BattleState(_FM(), entities=pcs + [boss])
        bs.battle.lair_enabled = True
        bs._set_ai_mode("full_auto")
        # Choosing a mode no longer rolls initiative behind the
        # DM\'s back — deployment stays inert until START COMBAT.
        if not bs.battle.combat_started:
            bs.battle.start_combat()
        for _ in range(300):
            bs._process_auto_battle()
        acted = {e.name for e in bs.battle.entities
                 if e.hp < e.max_hp or e.hp <= 0}
        self.assertTrue(acted, "only the lair ever acted")

    def test_a_boss_fight_runs_and_the_boss_acts_out_of_turn(self):
        random.seed(21)
        heroes = ["Magnus Dragonius", "Balthazar", "Venris Galanodel",
                  "Padak Onslaught"]
        pcs = [Entity(_hero(n), 3 + (i % 2), 3 + i, is_player=True)
               for i, n in enumerate(heroes)]
        boss = Entity(library.get_monster("Praefectus Sanguinis Ostorius"),
                      9, 5, is_player=False)
        bs = BattleState(_FM(), entities=pcs + [boss])
        bs.battle.lair_enabled = True
        bs._set_ai_mode("full_auto")
        # Choosing a mode no longer rolls initiative behind the
        # DM\'s back — deployment stays inert until START COMBAT.
        if not bs.battle.combat_started:
            bs.battle.start_combat()
        for _ in range(1500):
            bs._process_auto_battle()
            if not bs.auto_battle:
                break
            if (not [e for e in bs.battle.entities
                     if e.is_player and e.hp > 0]
                    or not [e for e in bs.battle.entities
                            if not e.is_player and e.hp > 0]):
                break
        log = "\n".join(bs.logs)
        self.assertIn("LEGENDARY", log)

    def test_the_lair_speaks_during_a_fight(self):
        random.seed(33)
        pcs = [Entity(_hero(), 3, 3 + i, is_player=True) for i in range(3)]
        boss = Entity(library.get_monster("Keisari Tarquvas Redfei"),
                      9, 5, is_player=False)
        bs = BattleState(_FM(), entities=pcs + [boss])
        bs.battle.lair_enabled = True
        bs.battle.start_combat()
        bs._set_ai_mode("full_auto")
        # Choosing a mode no longer rolls initiative behind the
        # DM\'s back — deployment stays inert until START COMBAT.
        if not bs.battle.combat_started:
            bs.battle.start_combat()
        for _ in range(4000):
            bs._process_auto_battle()
            if not bs.auto_battle:
                break
            if (not [e for e in bs.battle.entities
                     if e.is_player and e.hp > 0]
                    or not [e for e in bs.battle.entities
                            if not e.is_player and e.hp > 0]):
                break
        self.assertIn("LAIR", "\n".join(bs.logs))


if __name__ == "__main__":
    unittest.main()
