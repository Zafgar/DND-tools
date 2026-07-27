"""AI:n vaihtoehdot pelinjohtajalle.

Pelinjohtaja pyysi näkemään kaikki vaihtoehdot, joita AI harkitsee
kunkin hahmon vuorolla — paras ylimpänä, vähemmän optimaaliset alla,
lyhyt perustelu kullekin. Silloin DM voi valita tarkoituksella
huonomman linjan, esimerkiksi koska joku pelaaja teki jotain, minkä
takia hirviön pitäisi kohdistaa isku juuri häneen.

Tekninen ydin: taktinen AI *rakensi jo* jokaisen vaihtoehdon ja pisteytti
ne — ja heitti sitten kaikki paitsi voittajan pois. Nyt ne säilytetään.

Vaikein osa on resurssikirjanpito. Jokainen ``_try_*``-apuri kuluttaa
loitsupaikan heti kun se rakentaa ehdokkaan, mutta vain yhtä käytetään,
joten häviäjille pitää palauttaa paikat ja voittajalta veloittaa. Kun DM
vaihtaa vaihtoehtoa, saman kirjanpidon pitää pitää: nämä testit
vaihtavat edestakaisin ja tarkistavat, ettei yksikään paikka vuoda
suuntaan tai toiseen.
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
from data.maps import load_map_terrain
from engine.ai.models import TurnOption, TurnPlan
from engine.entities import Entity
from states.battle_state import BattleState


class _FM:
    def __init__(self):
        self.screen = pygame.display.get_surface()
        self.running = True
        self.states = {}

    def change_state(self, *a, **k):
        pass


def _hero(name, x, y):
    h = {h.name: h for h in hero_list}[name]
    return Entity(copy.deepcopy(h), float(x), float(y), is_player=True)


def _mon(name, x, y, player=False):
    return Entity(copy.deepcopy(library.get_monster(name)),
                  float(x), float(y), is_player=player)


def _caster_scene(seed=4):
    """A wizard with several genuinely different plays available."""
    random.seed(seed)
    pc = _hero("Archmage Wizard", 5, 5)
    bs = BattleState(_FM(), entities=[
        pc, _hero("Magnus Dragonius", 6, 7),
        _mon("Ogre", 9, 5), _mon("Ogre", 9, 7), _mon("Goblin", 11, 6)])
    bs.battle.start_combat()
    guard = 0
    while bs.battle.get_current_entity() is not pc and guard < 30:
        bs.battle.next_turn()
        guard += 1
    bs._do_ai_turn()
    return bs, pc


# ===================================================================== #
# 1. THE OPTIONS EXIST AND ARE RANKED
# ===================================================================== #
class TestOptionsAreProduced(unittest.TestCase):

    def test_a_caster_turn_offers_several_ranked_options(self):
        bs, pc = _caster_scene()
        opts = bs.pending_plan.options
        self.assertGreaterEqual(len(opts), 3,
                                "an archmage should have more than two plays")
        scores = [o.score for o in opts]
        self.assertEqual(scores, sorted(scores, reverse=True),
                         "options must be ranked best first")
        self.assertEqual([o.rank for o in opts],
                         list(range(1, len(opts) + 1)))

    def test_exactly_one_option_is_flagged_as_the_ais_own_pick(self):
        bs, pc = _caster_scene()
        best = [o for o in bs.pending_plan.options if o.is_best]
        self.assertEqual(len(best), 1)
        self.assertEqual(best[0].rank, 1)

    def test_the_ais_pick_is_what_the_plan_actually_does(self):
        bs, pc = _caster_scene()
        plan = bs.pending_plan
        start, end = plan.action_slice
        self.assertEqual(plan.steps[start:end], plan.options[0].steps)
        self.assertEqual(plan.chosen_rank, 1)

    def test_every_option_can_be_shown_to_a_human(self):
        bs, pc = _caster_scene()
        for o in bs.pending_plan.options:
            with self.subTest(rank=o.rank):
                self.assertTrue(o.label.strip(), "no label to put on a button")
                self.assertTrue(o.reason.strip(), "no reason for the DM")
                self.assertLess(len(o.reason), 160, "reason is an essay")
                self.assertTrue(o.steps, "an option with nothing in it")

    def test_the_reasons_are_specific_not_boilerplate(self):
        bs, pc = _caster_scene()
        reasons = [o.reason for o in bs.pending_plan.options]
        self.assertEqual(len(set(reasons)), len(reasons),
                         "two options gave the DM the same explanation")

    def test_monsters_get_options_too(self):
        random.seed(11)
        dragon = _mon("Adult Red Dragon", 10, 10)
        bs = BattleState(_FM(), entities=[
            _hero("Magnus Dragonius", 8, 10), _hero("Beatrice", 8, 12),
            dragon])
        bs.battle.start_combat()
        guard = 0
        while bs.battle.get_current_entity() is not dragon and guard < 30:
            bs.battle.next_turn()
            guard += 1
        bs._do_ai_turn()
        self.assertTrue(bs.pending_plan)
        self.assertTrue(bs.pending_plan.options)

    def test_a_plan_with_no_action_phase_simply_has_no_options(self):
        plan = TurnPlan()
        self.assertEqual(plan.options, [])
        self.assertEqual(plan.chosen_rank, 0)

    def test_a_dragon_still_breathes_when_it_should(self):
        """The breath weapon used to claim the action before scoring ever
        ran, which is why a dragon's turn showed no alternatives. Moving
        it into the candidate list must not change what dragons do."""
        from engine.battle import BattleSystem
        for seed in range(6):
            with self.subTest(seed=seed):
                random.seed(seed)
                d = _mon("Adult Red Dragon", 10, 10)
                pcs = [_hero("Magnus Dragonius", 6, 9),
                       _hero("Beatrice", 6, 10), _hero("Carlo", 6, 11)]
                b = BattleSystem(log_callback=lambda s: None,
                                 initial_entities=pcs + [d])
                b.start_combat()
                plan = b.ai.calculate_turn(d, b)
                self.assertTrue(plan.options)
                self.assertIn("Breath", plan.options[0].label)
                self.assertGreater(len(plan.options), 1,
                                   "no alternatives offered to the DM")

    def test_the_recharge_is_only_spent_when_the_breath_is_taken(self):
        """Proposing a breath weapon must not burn its recharge — the
        DM might well pick the bite instead."""
        from engine.battle import BattleSystem
        random.seed(2)
        d = _mon("Adult Red Dragon", 10, 10)
        pcs = [_hero("Magnus Dragonius", 6, 9), _hero("Beatrice", 6, 10)]
        b = BattleSystem(log_callback=lambda s: None,
                         initial_entities=pcs + [d])
        b.start_combat()
        step = b.ai._try_aoe_action(d, pcs, [], b, consume=False)
        self.assertIsNotNone(step)
        self.assertTrue(d.can_use_feature(step.action.name),
                        "merely proposing the breath spent its recharge")
        b.ai.commit_option(d, "aoe_action", [step], slots_before={})
        self.assertFalse(d.can_use_feature(step.action.name),
                         "taking the breath did not spend its recharge")

    def test_an_emergency_action_still_tells_the_dm_what_happened(self):
        """Lay on Hands and friends bypass the scoring entirely. The
        panel must not go blank on exactly the turns that matter."""
        from engine.battle import BattleSystem
        random.seed(1)
        pal = _hero("Holy Paladin", 5, 5)
        dying = _hero("Magnus Dragonius", 6, 5)
        dying.hp = 0
        foe = _mon("Ogre", 12, 5)
        b = BattleSystem(log_callback=lambda s: None,
                         initial_entities=[pal, dying, foe])
        b.start_combat()
        plan = b.ai.calculate_turn(pal, b)
        if plan.options:
            self.assertTrue(plan.options[0].label.strip())
            self.assertTrue(plan.options[0].reason.strip())


# ===================================================================== #
# 2. THE DM CAN TAKE A WORSE LINE ON PURPOSE
# ===================================================================== #
class TestChoosingAnOption(unittest.TestCase):

    def test_choosing_a_lower_ranked_option_swaps_the_action(self):
        bs, pc = _caster_scene()
        plan = bs.pending_plan
        wanted = plan.options[2]
        self.assertTrue(bs.choose_plan_option(3))
        start, end = plan.action_slice
        self.assertEqual(plan.steps[start:end], wanted.steps)
        self.assertEqual(plan.chosen_rank, 3)

    def test_the_movement_around_the_action_is_left_alone(self):
        bs, pc = _caster_scene()
        plan = bs.pending_plan
        start, _end = plan.action_slice
        before = list(plan.steps[:start])
        bs.choose_plan_option(len(plan.options))
        self.assertEqual(plan.steps[:start], before,
                         "swapping the action disturbed the movement")

    def test_switching_back_and_forth_never_leaks_a_spell_slot(self):
        """Every _try_ helper spends its slot while merely proposing."""
        bs, pc = _caster_scene()
        plan = bs.pending_plan
        baseline = dict(plan.slots_before)
        seen = {}
        for rank in (1, 3, 2, 1, 3, 2, 1):
            bs.choose_plan_option(rank)
            spent = {lvl: baseline.get(lvl, 0) - pc.spell_slots.get(lvl, 0)
                     for lvl in baseline}
            spent = {k: v for k, v in spent.items() if v}
            if rank in seen:
                self.assertEqual(
                    spent, seen[rank],
                    f"option {rank} cost differently the second time")
            seen[rank] = spent
            for lvl, n in spent.items():
                self.assertGreaterEqual(
                    n, 0, f"switching REFUNDED more {lvl} than it spent")
                self.assertLessEqual(
                    n, 1, f"switching charged {lvl} twice over")

    def test_an_option_costs_exactly_what_its_own_steps_declare(self):
        bs, pc = _caster_scene()
        plan = bs.pending_plan
        baseline = dict(plan.slots_before)
        from engine.entities import Entity as _E
        for opt in plan.options:
            with self.subTest(rank=opt.rank):
                bs.choose_plan_option(opt.rank)
                declared = [s.slot_used for s in opt.steps if s.slot_used]
                for lvl_name in baseline:
                    spent = baseline[lvl_name] - pc.spell_slots.get(lvl_name, 0)
                    self.assertGreaterEqual(spent, 0)
                self.assertEqual(sum(1 for _ in declared),
                                 sum(baseline[k] - pc.spell_slots.get(k, 0)
                                     for k in baseline),
                                 "slots charged do not match the steps")

    def test_the_action_is_still_marked_as_used(self):
        bs, pc = _caster_scene()
        bs.choose_plan_option(2)
        self.assertTrue(pc.action_used)

    def test_the_choice_is_written_to_the_log_for_the_table(self):
        bs, pc = _caster_scene()
        before = len(bs.logs)
        bs.choose_plan_option(2)
        self.assertGreater(len(bs.logs), before)
        self.assertTrue(any("[DM]" in line for line in bs.logs[before:]))

    def test_a_swapped_option_runs_through_the_normal_confirm_flow(self):
        """The whole point: nothing downstream treats it specially."""
        bs, pc = _caster_scene()
        bs.choose_plan_option(2)
        guard = 0
        while bs.pending_plan and guard < 40:
            guard += 1
            bs._confirm_step()
        self.assertIsNone(bs.pending_plan, "the plan never finished")

    def test_outcomes_are_recalculated_for_the_new_action(self):
        bs, pc = _caster_scene()
        plan = bs.pending_plan
        bs.pending_step_idx = plan.action_slice[0]
        bs._prepare_step_outcomes()
        bs.choose_plan_option(3)
        step = plan.steps[plan.action_slice[0]]
        targets = step.targets or ([step.target] if step.target else [])
        for t in targets:
            self.assertIn(t, bs.current_step_outcomes,
                          "the new action has no pre-rolled outcome")


# ===================================================================== #
# 3. GUARD RAILS
# ===================================================================== #
class TestGuardRails(unittest.TestCase):

    def test_a_rank_outside_the_list_is_refused(self):
        bs, pc = _caster_scene()
        n = len(bs.pending_plan.options)
        for bad in (0, -1, n + 1, 999):
            with self.subTest(rank=bad):
                self.assertFalse(bs.can_choose_plan_option(bad))
                self.assertFalse(bs.choose_plan_option(bad))

    def test_you_cannot_change_an_action_that_already_happened(self):
        bs, pc = _caster_scene()
        plan = bs.pending_plan
        start, _end = plan.action_slice
        self.assertTrue(bs.can_choose_plan_option(2))
        bs.pending_step_idx = start + 1        # the DM confirmed it
        self.assertFalse(bs.can_choose_plan_option(2))
        self.assertFalse(bs.choose_plan_option(2))
        self.assertEqual(plan.chosen_rank, 1, "the plan changed anyway")

    def test_choosing_without_a_pending_plan_is_harmless(self):
        bs, pc = _caster_scene()
        bs.pending_plan = None
        self.assertFalse(bs.can_choose_plan_option(1))
        self.assertFalse(bs.choose_plan_option(1))


# ===================================================================== #
# 4. THE PANEL
# ===================================================================== #
class TestTheOptionsPanel(unittest.TestCase):

    def test_it_is_hidden_until_the_dm_asks_for_it(self):
        bs, pc = _caster_scene()
        self.assertFalse(bs.show_plan_options)
        bs._toggle_plan_options()
        self.assertTrue(bs.show_plan_options)
        bs._toggle_plan_options()
        self.assertFalse(bs.show_plan_options)

    def test_the_dialog_draws_with_the_panel_open_and_shut(self):
        screen = pygame.display.get_surface()
        for opened in (False, True):
            with self.subTest(panel_open=opened):
                bs, pc = _caster_scene()
                bs.battle.terrain = load_map_terrain("castle_courtyard")
                bs.show_plan_options = opened
                screen.fill((0, 0, 0))
                bs.draw(screen)

    def test_the_panel_registers_a_click_zone_for_every_option(self):
        screen = pygame.display.get_surface()
        bs, pc = _caster_scene()
        bs.show_plan_options = True
        screen.fill((0, 0, 0))
        bs.draw(screen)
        self.assertIsNotNone(bs.plan_options_rect,
                             "the panel published no rect for the "
                             "event handler, so clicks fall through "
                             "to the battle map")
        self.assertGreaterEqual(len(bs.ui_click_zones),
                                len(bs.pending_plan.options))

    def test_clicking_a_row_selects_that_option(self):
        screen = pygame.display.get_surface()
        bs, pc = _caster_scene()
        bs.show_plan_options = True
        screen.fill((0, 0, 0))
        bs.draw(screen)
        # The zones the panel added are the trailing ones
        zones = [z for z in bs.ui_click_zones
                 if bs.plan_options_rect.contains(z[0])]
        self.assertTrue(zones)
        zones[-1][1]()          # click the lowest-ranked visible option
        self.assertGreater(bs.pending_plan.chosen_rank, 1)

    def test_no_click_zones_once_the_action_is_locked_in(self):
        screen = pygame.display.get_surface()
        bs, pc = _caster_scene()
        bs.show_plan_options = True
        bs.pending_step_idx = bs.pending_plan.action_slice[0] + 1
        screen.fill((0, 0, 0))
        bs.draw(screen)
        if getattr(bs, "plan_options_rect", None) is not None:
            zones = [z for z in bs.ui_click_zones
                     if bs.plan_options_rect.contains(z[0])]
            self.assertEqual(zones, [],
                             "a locked action still offered clickable "
                             "alternatives")


# ===================================================================== #
# 5. THE MODEL
# ===================================================================== #
class TestTurnOption(unittest.TestCase):

    def test_it_has_sane_defaults(self):
        o = TurnOption(kind="multiattack")
        self.assertEqual(o.score, 0.0)
        self.assertEqual(o.steps, [])
        self.assertFalse(o.is_best)

    def test_two_options_do_not_share_a_step_list(self):
        a, b = TurnOption(kind="x"), TurnOption(kind="y")
        a.steps.append("s")
        self.assertEqual(b.steps, [])

    def test_the_labels_fall_back_to_a_readable_kind(self):
        from engine.ai import TacticalAI
        from engine.ai.models import ActionStep
        blank = [ActionStep(step_type="wait")]
        self.assertEqual(TacticalAI._option_label("dodge", blank), "Väistä")
        self.assertEqual(TacticalAI._option_label("some_new_thing", blank),
                         "Some New Thing")

    def test_a_named_ability_wins_over_the_generic_label(self):
        from engine.ai import TacticalAI
        from engine.ai.models import ActionStep
        named = [ActionStep(step_type="spell", action_name="Fireball")]
        self.assertEqual(TacticalAI._option_label("aoe_spell", named),
                         "Fireball")


if __name__ == "__main__":
    unittest.main()
