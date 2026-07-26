"""Summonit, kumppanit ja Wild Shape.

Kattaa:
  * Wild Shape -vahingon carry-over (myös tarkka tappoisku, joka ennen
    laskettiin kahdesti), palautuksen ja statsien palautumisen.
  * Summonin elinkaaren: kutsu, aloitejärjestys, AI, vanheneminen.
  * Concentration-summonit katoavat kun keskittyminen katkeaa.
  * AI osaa kutsua olento-loitsuja (ei enää vain Spiritual Weaponia)
    kuluttamatta loitsupaikkaa turhaan.
  * DM:n manuaalinen kumppanin kutsu ja vapautus.
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

from data.heroes import hero_list
from data.library import library
from data.spells import get_spell
from engine.entities import Entity
from engine.battle import BattleSystem
from engine.ai import TacticalAI
from states.battle_state import BattleState


def _hero(name):
    return {h.name: h for h in hero_list}[name]


def _ent(name, x=3, y=3, player=True):
    return Entity(copy.deepcopy(_hero(name)), x, y, is_player=player)


class _FM:
    def __init__(self):
        self.screen = pygame.display.get_surface()
        self.running = True
        self.states = {}

    def change_state(self, *a, **k):
        pass


class TestWildShape(unittest.TestCase):
    def setUp(self):
        self.orig_hp = _hero("ULV").hit_points

    def _shaped(self):
        e = _ent("ULV")
        e.transform_into(library.get_monster("Brown Bear"))
        return e

    def test_partial_damage_stays_in_beast_form(self):
        e = self._shaped()
        beast_max = e.max_hp
        e.take_damage(5, "slashing")
        self.assertTrue(e.is_wild_shaped)
        self.assertEqual(e.hp, beast_max - 5)

    def test_excess_damage_carries_to_druid(self):
        e = self._shaped()
        e.take_damage(e.hp + 10, "slashing")
        self.assertFalse(e.is_wild_shaped)
        self.assertEqual(e.hp, self.orig_hp - 10)

    def test_exact_kill_does_not_double_count(self):
        """Regression: damage exactly equal to the beast's HP used to be
        subtracted from the druid's restored HP as well."""
        e = self._shaped()
        beast_hp = e.hp
        e.take_damage(beast_hp, "slashing")
        self.assertFalse(e.is_wild_shaped)
        self.assertEqual(e.hp, self.orig_hp)

    def test_massive_damage_carries_through(self):
        e = self._shaped()
        beast_hp = e.hp
        e.take_damage(beast_hp + 200, "slashing")
        self.assertFalse(e.is_wild_shaped)
        self.assertLessEqual(e.hp, 0)

    def test_revert_restores_stats(self):
        e = _ent("ULV")
        ac, str_, n_act = (e.stats.armor_class,
                           e.stats.abilities.strength, len(e.stats.actions))
        n_spells = len(e.stats.spells_known)
        e.transform_into(library.get_monster("Brown Bear"))
        self.assertEqual(len(e.stats.spells_known), 0)  # no casting in form
        e.revert_form()
        self.assertEqual(e.stats.armor_class, ac)
        self.assertEqual(e.stats.abilities.strength, str_)
        self.assertEqual(len(e.stats.actions), n_act)
        self.assertEqual(len(e.stats.spells_known), n_spells)
        self.assertFalse(e.is_wild_shaped)


class TestSummonLifecycle(unittest.TestCase):
    def _battle(self):
        cleric = _ent("War Cleric")
        foe = Entity(library.get_monster("Ravenstonen Ghoul-murskaaja"),
                     9, 3, player=False) if False else Entity(
            library.get_monster("Ravenstonen Ghoul-murskaaja"), 9, 3,
            is_player=False)
        b = BattleSystem(log_callback=lambda s: None,
                         initial_entities=[cleric, foe])
        b.start_combat()
        return b, cleric, foe

    def test_spawn_sets_owner_side_and_initiative(self):
        b, cleric, _foe = self._battle()
        s = b.spawn_summon(cleric, "Spiritual Weapon", 5, 3, hp=0, ac=99,
                           damage_dice="1d8", duration=10,
                           spell_name="Spiritual Weapon")
        self.assertTrue(s.is_summon)
        self.assertIs(s.summon_owner, cleric)
        self.assertEqual(s.is_player, cleric.is_player)
        self.assertAlmostEqual(s.initiative, cleric.initiative - 0.5)
        self.assertIn(s, b.entities)

    def test_ai_drives_summon(self):
        b, cleric, _foe = self._battle()
        s = b.spawn_summon(cleric, "Spiritual Weapon", 5, 3, hp=0, ac=99,
                           damage_dice="1d8", duration=10,
                           spell_name="Spiritual Weapon")
        plan = TacticalAI().calculate_turn(s, b)
        self.assertFalse(plan.skipped)
        self.assertTrue(any(st.step_type == "attack" for st in plan.steps))

    def test_summon_expires(self):
        b, cleric, _foe = self._battle()
        s = b.spawn_summon(cleric, "Spiritual Weapon", 5, 3, hp=0, ac=99,
                           damage_dice="1d8", duration=10)
        s.summon_rounds_left = 0
        b.remove_expired_summons()
        self.assertNotIn(s, b.entities)

    def test_enemy_summon_not_counted_for_battle_over(self):
        b, _cleric, foe = self._battle()
        b.spawn_summon(foe, "Shadow", 9, 4, hp=20, ac=12, damage_dice="1d6",
                       duration=5)
        foe.hp = 0
        self.assertEqual(b.check_battle_over(), "players")


class TestConcentrationSummon(unittest.TestCase):
    def _setup(self):
        caster = _ent("Venris Galanodel")
        foe = Entity(library.get_monster("Ravenstonen Ghoul-murskaaja"), 9, 3,
                     is_player=False)
        b = BattleSystem(log_callback=lambda s: None,
                         initial_entities=[caster, foe])
        b.start_combat()
        caster.start_concentration(get_spell("Summon Construct"))
        s = b.spawn_summon(caster, "Construct Spirit", 8, 3, hp=40, ac=13,
                           damage_dice="1d8+4", duration=10,
                           spell_name="Summon Construct")
        return b, caster, s

    def test_dropping_concentration_removes_summon(self):
        b, caster, s = self._setup()
        caster.drop_concentration()
        b.remove_expired_summons()
        self.assertNotIn(s, b.entities)

    def test_damage_breaking_concentration_removes_summon(self):
        b, caster, s = self._setup()
        caster.take_damage(60, "fire")      # DC 30 → certain break
        b.remove_expired_summons()
        self.assertIsNone(caster.concentrating_on)
        self.assertNotIn(s, b.entities)

    def test_non_concentration_summon_survives(self):
        cleric = _ent("War Cleric")
        b = BattleSystem(log_callback=lambda s: None,
                         initial_entities=[cleric])
        b.start_combat()
        sw = b.spawn_summon(cleric, "Spiritual Weapon", 5, 3, hp=0, ac=99,
                            damage_dice="1d8", duration=10,
                            spell_name="Spiritual Weapon")
        cleric.drop_concentration()
        b.remove_expired_summons()
        self.assertIn(sw, b.entities)


class TestAiSummonsCreatures(unittest.TestCase):
    def _battle(self, hero, n_foes=1, foe="A.E.G.I.S. Titaani"):
        e = _ent(hero)
        foes = [Entity(library.get_monster(foe), 12, 3 + i, is_player=False)
                for i in range(n_foes)]
        b = BattleSystem(log_callback=lambda s: None,
                         initial_entities=[e] + foes)
        b.start_combat()
        return b, e, foes

    def test_party_casters_have_summon_spells(self):
        for name in ("Beatrice", "Venris Galanodel"):
            spells = [s for s in _hero(name).spells_known
                      if getattr(s, "summon_name", "")]
            self.assertTrue(spells, f"{name} has no summon spell")

    def test_ai_casts_summon_against_single_boss(self):
        b, e, foes = self._battle("Venris Galanodel")
        ai = TacticalAI()
        got = None
        for _ in range(3):
            e.reset_turn()
            plan = ai.calculate_turn(e, b)
            for st in plan.steps:
                if st.step_type == "summon":
                    got = st
            if got:
                break
        self.assertIsNotNone(got, "AI never cast a creature summon")
        self.assertTrue(got.summon_hp > 0)
        self.assertEqual(e.concentrating_on.name, "Summon Construct")
        self.assertEqual(e.spell_slots.get("4th"), 2)   # 3 -> 2, one spent

    def test_summon_helper_consumes_nothing_by_itself(self):
        """The summon candidate must be free to evaluate — it only costs
        a slot if the AI actually picks it."""
        b, e, foes = self._battle("Venris Galanodel")
        before = dict(e.spell_slots)
        e.reset_turn()
        step = TacticalAI()._try_summon_creature_spell(e, foes, b)
        self.assertIsNotNone(step)
        self.assertEqual(e.spell_slots, before)
        self.assertFalse(e.action_used)

    def test_losing_candidates_do_not_leak_slots(self):
        """Regression: every _try_* helper consumed a slot while building
        its candidate, so unchosen options (e.g. Disintegrate) burned
        slots. Only the chosen step's slot may be spent."""
        b, e, foes = self._battle("Venris Galanodel", n_foes=4,
                                  foe="Ravenstonen Ghoul-murskaaja")
        before = dict(e.spell_slots)
        e.reset_turn()
        plan = TacticalAI().calculate_turn(e, b)
        spent = {lvl: before[lvl] - now
                 for lvl, now in e.spell_slots.items() if before[lvl] != now}
        expected = {}
        for st in plan.steps:
            lvl = getattr(st, "slot_used", 0) or 0
            if lvl > 0:
                key = e._LEVEL_KEYS[lvl]
                expected[key] = expected.get(key, 0) + 1
        self.assertEqual(spent, expected,
                         f"slot accounting mismatch: spent={spent} "
                         f"expected={expected}")

    def test_only_one_summon_per_caster(self):
        b, e, foes = self._battle("Venris Galanodel")
        b.spawn_summon(e, "Construct Spirit", 8, 3, hp=40, ac=13,
                       damage_dice="1d8+4", duration=10)
        e.reset_turn()
        self.assertIsNone(
            TacticalAI()._try_summon_creature_spell(e, foes, b))

    def test_concentration_blocks_new_summon(self):
        b, e, foes = self._battle("Venris Galanodel")
        e.start_concentration(get_spell("Haste"))
        e.reset_turn()
        self.assertIsNone(
            TacticalAI()._try_summon_creature_spell(e, foes, b))


class TestDmCompanion(unittest.TestCase):
    def _bs(self):
        bea = _ent("Beatrice")
        foe = Entity(library.get_monster("Ravenstonen Ghoul-murskaaja"), 10, 3,
                     is_player=False)
        bs = BattleState(_FM(), entities=[bea, foe])
        bs.battle.start_combat()
        return bs, bea

    def test_companion_bound_to_owner(self):
        bs, bea = self._bs()
        bs._begin_summon_companion(bea)
        self.assertIs(bs._summon_owner_pending, bea)
        self.assertTrue(bs.add_entity_open)
        bs._add_entity_to_battle(library.get_monster("Shadow"),
                                 is_player=bs.add_entity_is_player)
        comp = [e for e in bs.battle.entities if e.is_summon]
        self.assertEqual(len(comp), 1)
        c = comp[0]
        self.assertIs(c.summon_owner, bea)
        self.assertEqual(c.is_player, bea.is_player)
        self.assertAlmostEqual(c.initiative, bea.initiative - 0.5)
        self.assertIn("Beatrice", c.name)
        self.assertIsNone(bs._summon_owner_pending)

    def test_ai_drives_dm_companion(self):
        bs, bea = self._bs()
        bs._begin_summon_companion(bea)
        bs._add_entity_to_battle(library.get_monster("Shadow"), is_player=True)
        c = next(e for e in bs.battle.entities if e.is_summon)
        plan = TacticalAI().calculate_turn(c, bs.battle)
        self.assertFalse(plan.skipped)

    def test_dismiss_companions(self):
        bs, bea = self._bs()
        bs._begin_summon_companion(bea)
        bs._add_entity_to_battle(library.get_monster("Shadow"), is_player=True)
        c = next(e for e in bs.battle.entities if e.is_summon)
        bs._dismiss_companions(bea)
        self.assertNotIn(c, bs.battle.entities)

    def test_normal_add_is_not_a_companion(self):
        bs, _bea = self._bs()
        bs._add_entity_to_battle(library.get_monster("Shadow"), is_player=False)
        added = bs.battle.entities[-1]
        self.assertFalse(added.is_summon)


if __name__ == "__main__":
    unittest.main()
