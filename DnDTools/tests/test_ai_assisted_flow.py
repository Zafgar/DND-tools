"""AI-avustettu tila päästä päähän — se mitä pelinjohtaja tekee 90 %
ajasta.

Sopimus on yksinkertainen ja se testataan kokonaan: AI ehdottaa, DM
hyväksyy JOKA askeleen erikseen, mikään ei liiku eikä osu ennen
hyväksyntää, ja jokaisesta heitosta näkyy noppa, modifierit ja mitä
vastaan heitettiin. Sama koskee hero-hahmoja silloin kun pelaaja on
poissa ja DM joutuu pelaamaan hänen vuoronsa.
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

from data.heroes import hero_list
from data.library import library
from engine.entities import Entity
from states.battle_state import BattleState
from states.battle_renderer import BattleRendererMixin


class _FM:
    def __init__(self):
        self.screen = pygame.display.get_surface()
        self.running = True
        self.states = {}

    def change_state(self, *a, **k):
        pass


def _duel(seed=1, hero_dex_wins=False):
    random.seed(seed)
    p = Entity(copy.deepcopy(hero_list[0]), 3.0, 3.0, is_player=True)
    e = Entity(copy.deepcopy(library.get_monster("Ogre")), 11.0, 3.0,
               is_player=False)
    bs = BattleState(_FM(), entities=[p, e])
    bs._set_ai_mode("suggest")
    return bs, p, e


# ===================================================================== #
# 1. NOTHING HAPPENS WITHOUT A PRESS
# ===================================================================== #
class TestNothingMovesUnapproved(unittest.TestCase):

    def test_a_suggestion_does_not_move_the_token(self):
        for seed in range(8):
            bs, p, e = _duel(seed)
            bs._do_start_combat()
            curr = bs.battle.get_current_entity()
            where = {x.name: (x.grid_x, x.grid_y) for x in bs.battle.entities}
            if bs.pending_plan is None:
                bs._do_ai_turn()
            self.assertIsNotNone(bs.pending_plan, f"seed {seed}: no plan")
            now = {x.name: (x.grid_x, x.grid_y) for x in bs.battle.entities}
            self.assertEqual(where, now,
                             f"seed {seed}: suunnittelu siirsi tokeneita")

    def test_a_suggestion_does_not_deal_damage(self):
        for seed in range(8):
            bs, p, e = _duel(seed)
            bs._do_start_combat()
            hp = {x.name: x.hp for x in bs.battle.entities}
            if bs.pending_plan is None:
                bs._do_ai_turn()
            self.assertEqual({x.name: x.hp for x in bs.battle.entities}, hp,
                             f"seed {seed}: suunnittelu teki vahinkoa")

    def test_drawing_the_dialog_changes_nothing(self):
        bs, p, e = _duel(3)
        bs._do_start_combat()
        if bs.pending_plan is None:
            bs._do_ai_turn()
        before = ({x.name: (x.hp, x.grid_x, x.grid_y)
                   for x in bs.battle.entities}, bs.pending_step_idx)
        for _ in range(5):
            bs.draw(pygame.display.get_surface())
        after = ({x.name: (x.hp, x.grid_x, x.grid_y)
                  for x in bs.battle.entities}, bs.pending_step_idx)
        self.assertEqual(before, after)


# ===================================================================== #
# 2. ONE PRESS, ONE STEP
# ===================================================================== #
class TestStepByStep(unittest.TestCase):

    def _plan(self, seed=4):
        bs, p, e = _duel(seed)
        bs._do_start_combat()
        if bs.pending_plan is None:
            bs._do_ai_turn()
        return bs, p, e

    def test_confirm_advances_exactly_one_step(self):
        bs, p, e = self._plan()
        total = len(bs.pending_plan.steps)
        if total < 2:
            self.skipTest("this turn is a single step")
        for i in range(total):
            self.assertEqual(bs.pending_step_idx, i)
            bs._confirm_step()
            if bs.pending_plan is None:
                self.assertEqual(i, total - 1,
                                 "suunnitelma loppui kesken")
                break

    def test_a_move_lands_only_when_its_step_is_confirmed(self):
        for seed in range(10):
            bs, p, e = self._plan(seed)
            plan = bs.pending_plan
            move_at = next((i for i, s in enumerate(plan.steps)
                            if s.step_type == "move"), None)
            if move_at is None:
                continue
            mover = plan.steps[move_at].attacker
            start = (mover.grid_x, mover.grid_y)
            dest = (plan.steps[move_at].new_x, plan.steps[move_at].new_y)
            if start == dest:
                continue
            for i in range(move_at):
                bs._confirm_step()
            self.assertEqual((mover.grid_x, mover.grid_y), start,
                             "token liikkui ennen oman askeleensa hyväksyntää")
            bs._confirm_step()
            landed = (mover.grid_x, mover.grid_y)
            # Either it arrived, or a reaction paused it — never halfway
            # and never before the press.
            self.assertTrue(landed == dest or bs.reaction_pending,
                            f"siirto ei toteutunut hyväksynnästä: "
                            f"{landed} != {dest}")
            return
        self.skipTest("no move step turned up in ten tries")

    def test_skipping_a_step_does_not_resolve_it(self):
        bs, p, e = self._plan(6)
        hp = {x.name: x.hp for x in bs.battle.entities}
        n = len(bs.pending_plan.steps)
        for _ in range(n):
            if bs.pending_plan is None:
                break
            bs._skip_step()
        self.assertEqual({x.name: x.hp for x in bs.battle.entities}, hp,
                         "ohitetut askeleet tekivät silti vahinkoa")

    def test_cancelling_drops_the_whole_plan(self):
        bs, p, e = self._plan(7)
        bs._cancel_ai_plan()
        self.assertIsNone(bs.pending_plan)


# ===================================================================== #
# 3. THE DICE ARE ON SCREEN
# ===================================================================== #
class TestTheRollsAreVisible(unittest.TestCase):

    def test_every_attack_step_carries_its_roll(self):
        seen = 0
        for seed in range(14):
            bs, p, e = _duel(seed)
            bs._do_start_combat()
            if bs.pending_plan is None:
                bs._do_ai_turn()
            for st in bs.pending_plan.steps:
                if st.step_type not in ("attack", "bonus_attack",
                                        "legendary"):
                    continue
                if st.action is None or st.save_dc:
                    continue
                seen += 1
                self.assertTrue(st.attack_roll_str,
                                f"{st.description}: ei noppamerkintää")
                self.assertTrue(1 <= st.nat_roll <= 20,
                                f"{st.description}: nat={st.nat_roll}")
                self.assertGreater(st.attack_roll, 0)
        self.assertGreater(seen, 0, "yhtään hyökkäysaskelta ei syntynyt")

    def test_the_outcome_matches_the_roll(self):
        for seed in range(12):
            bs, p, e = _duel(seed)
            bs._do_start_combat()
            if bs.pending_plan is None:
                bs._do_ai_turn()
            step = bs.pending_plan.steps[bs.pending_step_idx]
            targets = step.targets or ([step.target] if step.target else [])
            for t in targets:
                if step.save_dc or step.action is None:
                    continue
                got = bs.current_step_outcomes.get(t)
                want = "hit" if step.is_hit else "miss"
                self.assertEqual(got, want,
                                 f"{step.description}: tulos {got}")

    def test_the_dialog_renders_the_whole_turn(self):
        bs, p, e = _duel(5)
        bs._do_start_combat()
        if bs.pending_plan is None:
            bs._do_ai_turn()
        plan = bs.pending_plan
        for st in plan.steps:
            line = BattleRendererMixin._step_one_liner(st)
            self.assertTrue(line, f"askel ilman yhteenvetoa: {st.step_type}")
        bs.draw(pygame.display.get_surface())    # must not raise
        self.assertIsNotNone(bs.ai_dialog_rect)


# ===================================================================== #
# 4. RUNNING AN ABSENT PLAYER'S HERO
# ===================================================================== #
class TestPlayingAnAbsentPlayersHero(unittest.TestCase):

    def _hero_turn(self, seed=1):
        """A board where a HERO is the one to act."""
        random.seed(seed)
        p = Entity(copy.deepcopy(hero_list[0]), 3.0, 3.0, is_player=True)
        e = Entity(copy.deepcopy(library.get_monster("Ogre")), 11.0, 3.0,
                   is_player=False)
        bs = BattleState(_FM(), entities=[p, e])
        bs._set_ai_mode("suggest")
        bs._bump_initiative(p, 30 - p.initiative)
        bs._bump_initiative(e, 2 - e.initiative)
        bs._do_start_combat()
        return bs, p, e

    def test_the_hero_is_the_one_up(self):
        bs, p, e = self._hero_turn()
        self.assertIs(bs.battle.get_current_entity(), p)

    def test_no_plan_is_forced_on_a_present_player(self):
        # Suggest mode plans NPC turns by itself. A hero's turn belongs
        # to the player unless the DM asks for help.
        bs, p, e = self._hero_turn()
        self.assertIsNone(bs.pending_plan,
                          "AI otti pelaajan vuoron ilman pyyntöä")

    def test_asking_for_help_plans_the_heros_turn(self):
        bs, p, e = self._hero_turn()
        bs._do_ai_turn()
        self.assertIsNotNone(bs.pending_plan)
        self.assertIs(bs.pending_plan.entity, p)
        self.assertTrue(bs.pending_plan.steps)

    def test_the_heros_plan_still_needs_approval_per_step(self):
        bs, p, e = self._hero_turn()
        where = (p.grid_x, p.grid_y)
        hp_before = e.hp
        bs._do_ai_turn()
        self.assertEqual((p.grid_x, p.grid_y), where,
                         "hero-ehdotus siirsi tokenin heti")
        self.assertEqual(e.hp, hp_before,
                         "hero-ehdotus teki vahinkoa heti")

    def test_the_heros_plan_shows_its_dice_too(self):
        bs, p, e = self._hero_turn()
        bs._do_ai_turn()
        rolled = [s for s in bs.pending_plan.steps
                  if s.step_type in ("attack", "bonus_attack")
                  and s.action is not None and not s.save_dc]
        for st in rolled:
            self.assertTrue(st.attack_roll_str, st.description)

    def test_the_heros_plan_offers_alternatives(self):
        bs, p, e = self._hero_turn()
        bs._do_ai_turn()
        opts = getattr(bs.pending_plan, "options", None) or []
        self.assertGreaterEqual(
            len(opts), 1,
            "hero-ehdotukselle ei tarjottu yhtään vaihtoehtoa")

    def test_the_button_says_what_it_does_on_a_hero_turn(self):
        bs, p, e = self._hero_turn()
        bs.draw(pygame.display.get_surface())
        self.assertIn("hero", bs.btn_ai.text.lower())

    def test_looking_at_a_character_does_not_spend_their_turn(self):
        """Statlehden AI-ehdotusrivi ajoi oikean suunnittelijan joka
        ruudulla, ja suunnittelu kuluttaa toiminnon, bonustoiminnon,
        loitsupaikat, raivon ja liikkeen. Hahmon katsominen söi siis
        hänen vuoronsa."""
        bs, p, e = self._hero_turn()
        bs.selected_entity = p
        before = (p.action_used, p.bonus_action_used, p.reaction_used,
                  p.movement_left, p.reckless_attack_active,
                  p.rage_active, p.rages_left, dict(p.spell_slots),
                  (p.grid_x, p.grid_y), p.hp, p.temp_hp)
        for _ in range(30):
            bs.draw(pygame.display.get_surface())
        after = (p.action_used, p.bonus_action_used, p.reaction_used,
                 p.movement_left, p.reckless_attack_active,
                 p.rage_active, p.rages_left, dict(p.spell_slots),
                 (p.grid_x, p.grid_y), p.hp, p.temp_hp)
        self.assertEqual(before, after,
                         "pelkkä piirtäminen kulutti hahmon resursseja")

    def test_the_dm_advisor_is_advisory_only(self):
        bs, p, e = self._hero_turn()
        before = (p.action_used, p.bonus_action_used, p.movement_left,
                  dict(p.spell_slots), p.rages_left)
        bs.battle.get_dm_suggestion(p)
        after = (p.action_used, p.bonus_action_used, p.movement_left,
                 dict(p.spell_slots), p.rages_left)
        self.assertEqual(before, after,
                         "neuvonantajan kysyminen kulutti vuoron")

    def test_preview_and_the_real_plan_differ_in_exactly_one_way(self):
        # The preview must give the same advice; it just must not pay
        # for it.
        bs, p, e = self._hero_turn()
        bs.battle.preview_ai_turn(p)
        self.assertFalse(p.action_used)
        bs._do_ai_turn()
        self.assertIsNotNone(bs.pending_plan)


# ===================================================================== #
# 5. SIDES
# ===================================================================== #
class TestSides(unittest.TestCase):

    def test_the_add_picker_offers_a_side_toggle(self):
        bs, p, e = _duel()
        bs.add_entity_open = True
        before = bs.add_entity_is_player
        bs.draw(pygame.display.get_surface())
        hits = [cb for r, cb in bs.ui_click_zones
                if r.width == 120 and r.height == 28]
        self.assertEqual(len(hits), 1, "puolenvalinta ei ole klikattavissa")
        hits[0]()
        self.assertNotEqual(bs.add_entity_is_player, before)

    def test_a_creature_added_as_an_ally_joins_the_party(self):
        bs, p, e = _duel()
        bs.add_entity_is_player = True
        n = len(bs.battle.entities)
        bs._add_entity_to_battle(library.get_monster("Ogre"), is_player=True)
        self.assertEqual(len(bs.battle.entities), n + 1)
        self.assertTrue(bs.battle.entities[-1].is_player)

    def test_a_creature_added_as_an_enemy_joins_the_other_side(self):
        bs, p, e = _duel()
        bs._add_entity_to_battle(hero_list[2], is_player=False)
        self.assertFalse(bs.battle.entities[-1].is_player)

    def test_a_side_can_be_flipped_after_placement(self):
        bs, p, e = _duel()
        bs._do_start_combat()
        self.assertFalse(e.is_player)
        bs._switch_side(e)
        self.assertTrue(e.is_player)
        self.assertIn(e, bs.battle.get_allies_of(p))
        bs._switch_side(e)
        self.assertFalse(e.is_player)
        self.assertIn(e, bs.battle.get_enemies_of(p))

    def test_flipping_a_side_drops_a_plan_built_for_the_old_one(self):
        bs, p, e = _duel()
        bs._do_start_combat()
        if bs.pending_plan is None:
            bs._do_ai_turn()
        target = bs.pending_plan.entity
        bs._switch_side(target)
        self.assertIsNone(bs.pending_plan)


if __name__ == "__main__":
    unittest.main()
