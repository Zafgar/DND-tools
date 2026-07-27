"""Kun pelinjohtaja tekee asiat itse: klikkaukset osuvat, heitot näkyvät,
monihyökkäys kertoo millä aseella ja säännöt pitävät myös käsipelissä.

Kaikki tässä löytyi pöydästä, ei koodia lukemalla: klikkaus painoi ihan
muuta kuin mihin osoitti, reckless attack ei mennyt läpi, osumaheitosta
ei näkynyt noppaa eikä AC:tä, ja täysi simulaatio seisoi paikallaan
sanomatta miksi.
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
from data.spells import get_spell
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


def _hero(match):
    return next(h for h in hero_list if match in h.name)


def _fight(a="Barbarian", b="Fighter"):
    p = Entity(copy.deepcopy(_hero(a)), 3.0, 3.0, is_player=True)
    e = Entity(copy.deepcopy(_hero(b)), 4.0, 3.0, is_player=False)
    bs = BattleState(_FM(), entities=[p, e])
    return bs, p, e


# ===================================================================== #
# 1. CLICKS LAND WHERE THE CURSOR IS
# ===================================================================== #
class TestClickZones(unittest.TestCase):
    """Klikattavat alueet rekisteröidään piirron aikana. Lista siivottiin
    ennen sen paneelin toimesta joka sattui piirtymään ensin — ja se
    paneeli oli ehdollinen."""

    def _drawn(self, bs, frames=4):
        screen = pygame.display.get_surface()
        counts = []
        for _ in range(frames):
            bs.draw(screen)
            counts.append(len(bs.ui_click_zones))
        return counts

    def test_zones_do_not_pile_up_frame_after_frame(self):
        bs, p, e = _fight()
        bs._do_start_combat()
        counts = self._drawn(bs, frames=6)
        self.assertEqual(len(set(counts)), 1,
                         f"klikkausalueet kasvavat ruutu ruudulta: {counts}")

    def test_zones_survive_in_deployment_too(self):
        bs, p, e = _fight()
        counts = self._drawn(bs, frames=5)
        self.assertEqual(len(set(counts)), 1, counts)
        self.assertGreater(counts[0], 0)

    def test_the_stat_panel_stays_clickable_under_the_ai_dialog(self):
        # This is the one that bit: opening an AI suggestion wiped every
        # zone the right-hand sheet had just registered, so Reckless
        # Attack, the condition toggles and the action list all went
        # dead while the dialog was up.
        bs, p, e = _fight()
        bs._do_start_combat()
        screen = pygame.display.get_surface()
        bs.draw(screen)
        alone = len(bs.ui_click_zones)
        bs.selected_entity = bs.battle.get_current_entity()
        bs._do_ai_turn()
        bs.draw(screen)
        self.assertGreaterEqual(
            len(bs.ui_click_zones), alone,
            "AI-dialogi tyhjensi oikean paneelin klikkausalueet")

    def test_a_modal_drawn_last_does_not_wipe_the_rest(self):
        bs, p, e = _fight()
        bs._do_start_combat()
        screen = pygame.display.get_surface()
        bs.draw(screen)
        alone = len(bs.ui_click_zones)
        bs.save_modal_open = True
        bs.pending_saves = []
        bs.draw(screen)
        self.assertGreaterEqual(len(bs.ui_click_zones), alone)

    def test_the_dialog_publishes_the_rect_the_events_use(self):
        bs, p, e = _fight()
        bs._do_start_combat()
        bs.selected_entity = bs.battle.get_current_entity()
        bs._do_ai_turn()
        bs.draw(pygame.display.get_surface())
        if bs.pending_plan:
            self.assertIsNotNone(bs.ai_dialog_rect)
            self.assertTrue(bs.ai_dialog_rect.collidepoint(
                bs.ai_dialog_rect.center))


# ===================================================================== #
# 2. A MANUAL ACTION IS ACTUALLY ROLLED
# ===================================================================== #
class TestManualAttacks(unittest.TestCase):

    def _swing(self, bs, attacker, target, action):
        bs._start_action_targeting(attacker, action)
        sx, sy = bs._grid_to_screen(target.grid_x, target.grid_y)
        bs._execute_manual_action((sx + 5, sy + 5))
        return bs.pending_plan

    def test_multiattack_becomes_one_step_per_weapon(self):
        random.seed(4)
        bs, p, e = _fight()
        bs._do_start_combat()
        multi = next(a for a in p.stats.actions if a.is_multiattack)
        plan = self._swing(bs, p, e, multi)
        self.assertIsNotNone(plan)
        self.assertGreaterEqual(len(plan.steps), 2,
                                "monihyökkäys jäi yhdeksi askeleeksi")
        for st in plan.steps:
            self.assertIsNotNone(st.action)
            self.assertFalse(st.action.is_multiattack)
            self.assertIn(st.action.name, [a.name for a in p.stats.actions])

    def test_the_step_names_the_weapon(self):
        random.seed(5)
        bs, p, e = _fight()
        bs._do_start_combat()
        multi = next(a for a in p.stats.actions if a.is_multiattack)
        plan = self._swing(bs, p, e, multi)
        line = BattleRendererMixin._step_one_liner(plan.steps[0])
        self.assertIn(plan.steps[0].action.name, line)
        self.assertIn(e.name, line)

    def test_a_manual_swing_rolls_a_real_attack(self):
        random.seed(6)
        bs, p, e = _fight()
        bs._do_start_combat()
        weapon = next(a for a in p.stats.actions
                      if not a.is_multiattack and a.damage_dice)
        plan = self._swing(bs, p, e, weapon)
        st = plan.steps[0]
        self.assertGreater(st.attack_roll, 0, "hyökkäysheittoa ei heitetty")
        self.assertTrue(1 <= st.nat_roll <= 20)
        self.assertTrue(st.attack_roll_str)
        self.assertGreater(st.damage, 0)
        # And the roll decides the outcome instead of defaulting to MISS.
        expected = "hit" if st.is_hit else "miss"
        self.assertEqual(bs.current_step_outcomes[e], expected)

    def test_the_description_carries_the_die_the_bonus_and_the_ac(self):
        random.seed(9)
        bs, p, e = _fight()
        bs._do_start_combat()
        weapon = next(a for a in p.stats.actions
                      if not a.is_multiattack and a.damage_dice)
        plan = self._swing(bs, p, e, weapon)
        d = plan.steps[0].description
        self.assertIn("d20", d)
        self.assertIn(f"AC {e.stats.armor_class}", d)
        self.assertIn("=", d)

    def test_a_manual_attack_never_silently_misses_by_default(self):
        # Every manual action used to arrive with is_hit False, which
        # the outcome table reads as a miss. Thirteen rounds of that and
        # nobody has taken a point of damage.
        random.seed(11)
        hits = 0
        for i in range(20):
            bs, p, e = _fight()
            bs._do_start_combat()
            e.stats.armor_class = 5          # cannot plausibly miss
            weapon = next(a for a in p.stats.actions
                          if not a.is_multiattack and a.damage_dice)
            plan = self._swing(bs, p, e, weapon)
            st = plan.steps[0]
            if st.is_hit:
                hits += 1
            else:
                # A natural 1 always misses; nothing else may.
                self.assertEqual(st.nat_roll, 1,
                                 f"AC 5 vastaan ohi ilman ykköstä: {st.description}")
        self.assertGreaterEqual(hits, 16, "AC 5 vastaan pitäisi osua lähes aina")


# ===================================================================== #
# 3. RECKLESS ATTACK AND FRIENDS
# ===================================================================== #
class TestFeatureToggles(unittest.TestCase):

    def test_reckless_attack_toggles_instead_of_just_logging(self):
        bs, p, e = _fight()
        feat = next(f for f in p.stats.features
                    if "reckless" in f.name.lower())
        self.assertFalse(p.reckless_attack_active)
        bs._use_feature_manual(p, feat)
        self.assertTrue(p.reckless_attack_active)
        bs._use_feature_manual(p, feat)
        self.assertFalse(p.reckless_attack_active)

    def test_reckless_actually_reaches_the_attack_roll(self):
        random.seed(12)
        bs, p, e = _fight()
        bs._do_start_combat()
        # Prone and the like hand out disadvantage that cancels the
        # advantage; start from a clean fighter so the test is about
        # Reckless and nothing else.
        p.conditions.clear()
        e.conditions.clear()
        feat = next(f for f in p.stats.features
                    if "reckless" in f.name.lower())
        bs._use_feature_manual(p, feat)
        weapon = next(a for a in p.stats.actions
                      if not a.is_multiattack and a.damage_dice
                      and a.range <= 5)
        bs._start_action_targeting(p, weapon)
        sx, sy = bs._grid_to_screen(e.grid_x, e.grid_y)
        bs._execute_manual_action((sx + 5, sy + 5))
        st = bs.pending_plan.steps[0]
        self.assertIn("Adv", st.attack_roll_str,
                      "reckless ei tuottanut etua heittoon")

    def test_the_dialog_names_what_is_riding_on_the_swing(self):
        random.seed(13)
        bs, p, e = _fight()
        bs._do_start_combat()
        p.conditions.clear()
        e.conditions.clear()
        feat = next(f for f in p.stats.features
                    if "reckless" in f.name.lower())
        bs._use_feature_manual(p, feat)
        weapon = next(a for a in p.stats.actions
                      if not a.is_multiattack and a.damage_dice
                      and a.range <= 5)
        bs._start_action_targeting(p, weapon)
        sx, sy = bs._grid_to_screen(e.grid_x, e.grid_y)
        bs._execute_manual_action((sx + 5, sy + 5))
        note = BattleRendererMixin._attack_modifier_note(
            bs.pending_plan.steps[0])
        self.assertIn("Reckless", note)


# ===================================================================== #
# 4. CONDITIONS BIND THE DM PANEL TOO
# ===================================================================== #
class TestConditionsBlockManualPlay(unittest.TestCase):

    def test_hold_person_stops_a_manual_misty_step(self):
        bs, p, e = _fight("Wizard", "Fighter")
        bs._do_start_combat()
        p.add_condition("Paralyzed", source=e)
        misty = next((s for s in p.stats.spells_known
                      if s.name == "Misty Step"), None)
        if misty is None:
            self.skipTest("this hero has no Misty Step")
        bs._start_spell_targeting(p, misty)
        self.assertIsNone(bs.spell_targeting,
                          "halvaantunut hahmo pääsi loitsimaan")

    def test_a_paralyzed_creature_cannot_swing_by_hand_either(self):
        bs, p, e = _fight()
        bs._do_start_combat()
        p.add_condition("Paralyzed", source=e)
        weapon = next(a for a in p.stats.actions if not a.is_multiattack)
        bs._start_action_targeting(p, weapon)
        self.assertIsNone(bs.action_targeting)

    def test_the_block_says_who_is_holding_them(self):
        bs, p, e = _fight()
        bs._do_start_combat()
        p.add_condition("Paralyzed", source=e)
        weapon = next(a for a in p.stats.actions if not a.is_multiattack)
        bs._start_action_targeting(p, weapon)
        self.assertTrue(any(e.name in str(m) and "Paralyzed" in str(m)
                            for m in bs.logs[-3:]),
                        f"lokista ei näy kuka pitää: {bs.logs[-3:]}")

    def test_a_healthy_creature_is_not_blocked(self):
        bs, p, e = _fight()
        bs._do_start_combat()
        weapon = next(a for a in p.stats.actions if not a.is_multiattack)
        bs._start_action_targeting(p, weapon)
        self.assertIsNotNone(bs.action_targeting)

    def test_the_ai_already_skips_a_held_creature(self):
        bs, p, e = _fight("Wizard", "Fighter")
        bs._do_start_combat()
        p.add_condition("Paralyzed", source=e)
        plan = bs.battle.compute_ai_turn(p)
        self.assertTrue(plan.skipped)
        self.assertIn("Paralyzed", plan.skip_reason)


# ===================================================================== #
# 5. CONCENTRATION NAMES ITS VICTIM
# ===================================================================== #
class TestConcentrationTargets(unittest.TestCase):

    def test_the_caster_knows_who_it_is_holding(self):
        bs, p, e = _fight("Wizard", "Fighter")
        hold = get_spell("Hold Person")
        p.start_concentration(hold)
        p.register_concentration_effect(e, "condition", "Paralyzed")
        self.assertEqual(p.concentration_target_names(), [e.name])

    def test_no_links_means_no_names_rather_than_a_crash(self):
        bs, p, e = _fight("Wizard", "Fighter")
        self.assertEqual(p.concentration_target_names(), [])

    def test_the_victim_records_who_did_it(self):
        bs, p, e = _fight()
        p.add_condition("Paralyzed", source=e)
        self.assertIs(p.condition_sources.get("Paralyzed"), e)

    def test_it_renders(self):
        bs, p, e = _fight("Wizard", "Fighter")
        bs._do_start_combat()
        p.start_concentration(get_spell("Hold Person"))
        p.register_concentration_effect(e, "condition", "Paralyzed")
        e.add_condition("Paralyzed", source=p)
        bs.selected_entity = p
        bs.condition_reminder = e
        bs.draw(pygame.display.get_surface())     # must not raise


# ===================================================================== #
# 6. A SIM WITH NOBODY TO FIGHT SAYS SO
# ===================================================================== #
class TestOneSidedRoster(unittest.TestCase):

    def _party_only(self):
        ents = [Entity(copy.deepcopy(h), 3.0 + i * 2, 3.0, is_player=True)
                for i, h in enumerate(hero_list[:4])]
        return BattleState(_FM(), entities=ents)

    def test_the_sim_stops_and_explains_itself(self):
        bs = self._party_only()
        bs._set_ai_mode("full_auto")
        bs._do_start_combat()
        for _ in range(40):
            bs._process_auto_battle()
            if not bs.auto_battle:
                break
        self.assertFalse(bs.auto_battle)
        self.assertTrue(
            any("ei ole vihollisia" in str(m) for m in bs.logs),
            f"simulaatio pysähtyi selittämättä: {bs.logs[-3:]}")

    def test_it_does_not_masquerade_as_a_stalemate(self):
        bs = self._party_only()
        bs._set_ai_mode("full_auto")
        bs._do_start_combat()
        for _ in range(40):
            bs._process_auto_battle()
            if not bs.auto_battle:
                break
        self.assertFalse(any("Umpikuja" in str(m) for m in bs.logs),
                         "tyhjä kenttä raportoitiin umpikujana")

    def test_a_two_sided_fight_still_runs(self):
        random.seed(3)
        bs, p, e = _fight()
        bs._set_ai_mode("full_auto")
        bs._do_start_combat()
        for _ in range(600):
            bs._process_auto_battle()
            if not bs.auto_battle or bs.battle.check_battle_over():
                break
        self.assertTrue(bs.battle.check_battle_over())


if __name__ == "__main__":
    unittest.main()
