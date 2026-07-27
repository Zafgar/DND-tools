"""DM-työkalun taistelunäkymän UX: AI-tilat, ehdotusten hallinta,
turn orderin muokkaus, tilojen kestot, concentration-muistutus,
DM-vapaa siirto ja loitsupaikkojen pikapalautus.
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

import engine.entities as entities_mod
from data.models import CreatureStats, AbilityScores, Action
from data.spells import get_spell
from engine.entities import Entity
from engine.battle import BattleSystem
from states.battle_state import BattleState


class _FM:
    def __init__(self):
        self.screen = pygame.display.get_surface()
        self.running = True
        self.states = {}

    def change_state(self, *a, **k):
        pass


def _mk(name, x, y, is_player, dex=10, hp=40):
    s = CreatureStats(name=name, hit_points=hp, armor_class=14, speed=30,
                      abilities=AbilityScores(strength=14, dexterity=dex,
                                              constitution=12),
                      actions=[Action("Sword", "Melee", 5, "1d8", 2,
                                      "slashing")])
    return Entity(s, x, y, is_player=is_player)


def _bs(entities):
    return BattleState(_FM(), entities=entities)


class TestAiModeDial(unittest.TestCase):
    def test_default_mode_is_suggest(self):
        bs = _bs([_mk("Hero", 3, 3, True), _mk("Orc", 10, 3, False)])
        self.assertEqual(bs.ai_mode, "suggest")
        self.assertFalse(bs.auto_battle)

    def test_mode_cycle_sets_auto_flags(self):
        bs = _bs([_mk("Hero", 3, 3, True), _mk("Orc", 10, 3, False)])
        bs._set_ai_mode("npc_auto")
        # Choosing a mode no longer rolls initiative behind the
        # DM\'s back — deployment stays inert until START COMBAT.
        if not bs.battle.combat_started:
            bs._do_start_combat()
        self.assertTrue(bs.auto_battle)
        self.assertEqual(bs.auto_battle_mode, "npc")
        self.assertTrue(bs.battle.combat_started)  # auto-started
        bs._set_ai_mode("full_auto")
        # Choosing a mode no longer rolls initiative behind the
        # DM\'s back — deployment stays inert until START COMBAT.
        if not bs.battle.combat_started:
            bs._do_start_combat()
        self.assertTrue(bs.auto_battle)
        self.assertEqual(bs.auto_battle_mode, "full")
        bs._set_ai_mode("manual")
        self.assertFalse(bs.auto_battle)

    def test_suggest_mode_queues_plan_on_npc_turn_at_start(self):
        # NPC wins initiative (huge dex) -> plan queued right at START.
        hero = _mk("Hero", 3, 3, True, dex=1)
        orc = _mk("Orc", 5, 3, False, dex=20)
        bs = _bs([hero, orc])
        bs._do_start_combat()
        curr = bs.battle.get_current_entity()
        if not curr.is_player:
            self.assertIsNotNone(bs.pending_plan)
            self.assertIs(bs.pending_plan.entity, curr)

    def test_reroll_produces_fresh_plan(self):
        hero = _mk("Hero", 3, 3, True, dex=1)
        orc = _mk("Orc", 5, 3, False, dex=20)
        bs = _bs([hero, orc])
        bs._do_start_combat()
        if bs.pending_plan is None:
            self.skipTest("player won initiative despite dex weighting")
        bs._reroll_ai_plan()
        self.assertIsNotNone(bs.pending_plan)


class TestNpcAutoPausesForPlayers(unittest.TestCase):
    def test_player_reaction_not_auto_resolved(self):
        hero = _mk("Hero", 3, 3, True)
        orc = _mk("Orc", 4, 3, False)
        bs = _bs([hero, orc])
        bs._set_ai_mode("npc_auto")
        # Choosing a mode no longer rolls initiative behind the
        # DM\'s back — deployment stays inert until START COMBAT.
        if not bs.battle.combat_started:
            bs._do_start_combat()
        bs.reaction_pending = [hero]
        bs.reaction_type = "oa"
        bs.pending_move = (orc, 8.0, 3.0)
        bs._process_auto_battle()
        # Player decides at the table: the reaction must still be pending.
        self.assertEqual(bs.reaction_pending, [hero])

    def test_npc_reaction_is_auto_resolved(self):
        hero = _mk("Hero", 3, 3, True)
        orc = _mk("Orc", 4, 3, False)
        bs = _bs([hero, orc])
        bs._set_ai_mode("npc_auto")
        # Choosing a mode no longer rolls initiative behind the
        # DM\'s back — deployment stays inert until START COMBAT.
        if not bs.battle.combat_started:
            bs._do_start_combat()
        bs.reaction_pending = [orc]
        bs.reaction_type = "oa"
        bs.pending_move = (hero, 8.0, 3.0)
        bs._process_auto_battle()
        self.assertEqual(bs.reaction_pending, [])


class TestConditionDurations(unittest.TestCase):
    def test_timed_condition_expires(self):
        e = _mk("Guard", 0, 0, False)
        b = BattleSystem(log_callback=lambda s: None, initial_entities=[e])
        e.add_condition("Blinded", duration_rounds=2)
        self.assertEqual(e.condition_durations["Blinded"], 2)
        b.handle_end_of_turn_saves(e)
        self.assertTrue(e.has_condition("Blinded"))
        b.handle_end_of_turn_saves(e)
        self.assertFalse(e.has_condition("Blinded"))
        self.assertNotIn("Blinded", e.condition_durations)

    def test_untimed_condition_untouched(self):
        e = _mk("Guard", 0, 0, False)
        b = BattleSystem(log_callback=lambda s: None, initial_entities=[e])
        e.add_condition("Prone")
        b.handle_end_of_turn_saves(e)
        self.assertTrue(e.has_condition("Prone"))

    def test_remove_condition_clears_duration(self):
        e = _mk("Guard", 0, 0, False)
        e.add_condition("Poisoned", duration_rounds=5)
        e.remove_condition("Poisoned")
        self.assertNotIn("Poisoned", e.condition_durations)


class TestTurnOrderEdit(unittest.TestCase):
    def test_move_later_swaps_neighbours(self):
        a = _mk("A", 0, 0, True)
        b_ = _mk("B", 1, 0, False)
        c = _mk("C", 2, 0, False)
        b = BattleSystem(log_callback=lambda s: None,
                         initial_entities=[a, b_, c])
        b.start_combat()
        order0 = list(b.entities)
        first = order0[0]
        b.move_in_initiative(first, +1)
        self.assertIs(b.entities[1], first)
        # Current-turn pointer still valid
        b.get_current_entity()

    def test_move_earlier_from_last(self):
        a = _mk("A", 0, 0, True)
        b_ = _mk("B", 1, 0, False)
        b = BattleSystem(log_callback=lambda s: None, initial_entities=[a, b_])
        b.start_combat()
        last = b.entities[-1]
        b.move_in_initiative(last, -1)
        self.assertIs(b.entities[0], last)


class TestConcentrationPrompt(unittest.TestCase):
    def _caster_battle(self):
        hero = _mk("Mage", 3, 3, True)
        orc = _mk("Orc", 10, 3, False)
        bs = _bs([hero, orc])
        bs.battle.start_combat()
        hero.start_concentration(get_spell("Bless"))
        return bs, hero

    def test_player_damage_defers_check(self):
        bs, hero = self._caster_battle()
        dealt, broke = hero.take_damage(22, "fire")
        self.assertFalse(broke)
        self.assertTrue(hero.concentrating_on)      # not auto-rolled
        self.assertEqual(len(bs.pending_conc_checks), 1)
        self.assertEqual(bs.pending_conc_checks[0]["dc"], 11)

    def test_resolve_break_drops_concentration(self):
        bs, hero = self._caster_battle()
        hero.take_damage(22, "fire")
        bs._resolve_conc_check(False)
        self.assertIsNone(hero.concentrating_on)
        self.assertEqual(bs.pending_conc_checks, [])

    def test_resolve_keep_retains_concentration(self):
        bs, hero = self._caster_battle()
        hero.take_damage(22, "fire")
        bs._resolve_conc_check(True)
        self.assertIsNotNone(hero.concentrating_on)

    def test_roll_resolves_the_check(self):
        bs, hero = self._caster_battle()
        hero.take_damage(22, "fire")
        bs._roll_conc_check()
        self.assertEqual(bs.pending_conc_checks, [])

    def test_full_auto_rolls_engine_side(self):
        bs, hero = self._caster_battle()
        bs._set_ai_mode("full_auto")
        # Choosing a mode no longer rolls initiative behind the
        # DM\'s back — deployment stays inert until START COMBAT.
        if not bs.battle.combat_started:
            bs._do_start_combat()
        hero.take_damage(60, "fire")   # DC 30 -> guaranteed break
        self.assertIsNone(hero.concentrating_on)
        self.assertEqual(bs.pending_conc_checks, [])

    def test_next_turn_blocked_until_resolved(self):
        bs, hero = self._caster_battle()
        hero.take_damage(22, "fire")
        curr = bs.battle.get_current_entity()
        bs._do_next_turn()
        self.assertIs(bs.battle.get_current_entity(), curr)  # did not advance

    def test_npc_damage_never_defers(self):
        bs, hero = self._caster_battle()
        orc = bs.battle.entities[-1] if not bs.battle.entities[-1].is_player \
            else bs.battle.entities[0]
        orc.start_concentration(get_spell("Bless"))
        orc.take_damage(60, "fire")
        self.assertEqual(bs.pending_conc_checks, [])


class TestDmFreeMove(unittest.TestCase):
    def test_dm_move_skips_movement_and_oa(self):
        hero = _mk("Hero", 3, 3, True)
        orc = _mk("Orc", 4, 3, False)     # adjacent: normal move provokes
        bs = _bs([hero, orc])
        bs.battle.start_combat()
        move_before = hero.movement_left
        ok = bs._dm_move_entity(hero, 10.0, 3.0)
        self.assertTrue(ok)
        self.assertEqual((hero.grid_x, hero.grid_y), (10.0, 3.0))
        self.assertEqual(hero.movement_left, move_before)   # no cost
        self.assertEqual(bs.reaction_pending, [])           # no OA
        self.assertFalse(orc.reaction_used)

    def test_dm_move_recomputes_pending_plan(self):
        hero = _mk("Hero", 3, 3, True, dex=1)
        orc = _mk("Orc", 5, 3, False, dex=20)
        bs = _bs([hero, orc])
        bs._do_start_combat()
        if bs.pending_plan is None:
            self.skipTest("player won initiative despite dex weighting")
        bs._dm_move_entity(hero, 14.0, 9.0)
        # A fresh plan exists and was computed for the acting NPC.
        self.assertIsNotNone(bs.pending_plan)

    def test_dm_move_rejects_occupied_square(self):
        hero = _mk("Hero", 3, 3, True)
        orc = _mk("Orc", 4, 3, False)
        bs = _bs([hero, orc])
        bs.battle.start_combat()
        self.assertFalse(bs._dm_move_entity(hero, 4.0, 3.0))
        self.assertEqual((hero.grid_x, hero.grid_y), (3.0, 3.0))


class TestSlotRestoreAndReactions(unittest.TestCase):
    def _caster(self):
        s = CreatureStats(
            name="Wiz", hit_points=30, armor_class=12, speed=30,
            abilities=AbilityScores(intelligence=18),
            spellcasting_ability="Intelligence", spell_save_dc=15,
            spell_attack_bonus=7,
            spell_slots={"1st": 3, "2nd": 2, "3rd": 1},
            spell_names=["Shield", "Counterspell"])
        return Entity(s, 2, 2, is_player=True)

    def test_restore_all_slots(self):
        wiz = self._caster()
        bs = _bs([wiz, _mk("Orc", 8, 3, False)])
        wiz.spell_slots["1st"] = 0
        wiz.spell_slots["3rd"] = 0
        bs._restore_all_slots(wiz)
        self.assertEqual(wiz.spell_slots["1st"], 3)
        self.assertEqual(wiz.spell_slots["3rd"], 1)

    def test_reaction_options_lists_spells(self):
        wiz = self._caster()
        bs = _bs([wiz, _mk("Orc", 8, 3, False)])
        opts = " ".join(bs._list_reaction_options(wiz))
        self.assertIn("Shield", opts)
        self.assertIn("Counterspell", opts)
        self.assertIn("Opportunity Attack", opts)

    def test_used_reaction_reported(self):
        wiz = self._caster()
        bs = _bs([wiz, _mk("Orc", 8, 3, False)])
        wiz.reaction_used = True
        opts = bs._list_reaction_options(wiz)
        self.assertEqual(len(opts), 1)
        self.assertIn("käytetty", opts[0])


class TestRendererSmoke(unittest.TestCase):
    """The new panels/modals must draw without crashing."""

    def test_draw_all_new_overlays(self):
        hero = _mk("Hero", 3, 3, True, dex=1)
        orc = _mk("Orc", 5, 3, False, dex=20)
        bs = _bs([hero, orc])
        bs._do_start_combat()
        screen = pygame.display.get_surface()
        bs.draw(screen)                       # AI dialog (suggest mode)
        # Reaction modal with options list
        bs.reaction_pending = [hero]
        bs.reaction_type = "oa"
        bs.pending_move = (orc, 8.0, 3.0)
        bs.draw(screen)
        bs.reaction_pending = []
        # Concentration modal
        hero.start_concentration(get_spell("Bless"))
        hero.take_damage(15, "fire")
        self.assertTrue(bs.pending_conc_checks)
        bs.draw(screen)
        bs._resolve_conc_check(True)
        # Finnish turn-start reminder with duration + effect rows
        hero.add_condition("Poisoned", save_ability="Constitution",
                           save_dc=13, duration_rounds=3)
        hero.active_effects["Bless"] = 4
        bs.condition_reminder = hero
        bs.draw(screen)


if __name__ == "__main__":
    unittest.main()
