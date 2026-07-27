"""Taistelunäkymän siivous: kolme selkeää tilaa, reset, paluu
kampanjaan, käsin muokattava initiative ja encounterin tallennus jo
ennen kuin noppia on heitetty.

Nämä ovat pelinjohtajan työkaluja, eivät sääntömoottoria: suurin osa
ajasta menee AI-avustetussa tilassa jossa DM hyväksyy ehdotuksia, joten
juuri sen polun pitää olla ehjä.
"""
import sys
import os
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import unittest

import pygame
pygame.init()
pygame.display.set_mode((1920, 1080))

from data.models import CreatureStats, AbilityScores, Action
from data.heroes import hero_list
from data.library import library
from engine.entities import Entity
from engine.battle import BattleSystem
from states.battle_state import BattleState


class _FM:
    def __init__(self):
        self.screen = pygame.display.get_surface()
        self.running = True
        self.states = {"CAMPAIGN": object(), "MENU": object()}
        self.changed_to = None

    def change_state(self, name, *a, **k):
        self.changed_to = name


def _mk(name, x, y, is_player, dex=10, hp=40):
    s = CreatureStats(name=name, hit_points=hp, armor_class=13, speed=30,
                      abilities=AbilityScores(strength=14, dexterity=dex,
                                              constitution=12),
                      actions=[Action("Sword", "Melee", 5, "1d8", 2,
                                      "slashing")])
    return Entity(s, x, y, is_player=is_player)


def _bs(manager=None, **kw):
    return BattleState(manager or _FM(),
                       entities=[_mk("Hero", 3, 3, True),
                                 _mk("Orc", 9, 3, False)], **kw)


# ===================================================================== #
# 1. THREE MODES, AND NOTHING RUNS BEFORE INITIATIVE
# ===================================================================== #
class TestTheThreeModes(unittest.TestCase):

    def test_every_mode_leaves_deployment_inert(self):
        for mode in ("manual", "suggest", "npc_auto", "full_auto"):
            bs = _bs()
            bs._set_ai_mode(mode)
            bs.update()
            self.assertFalse(bs.battle.combat_started,
                             f"{mode} started combat on its own")
            self.assertFalse(bs.auto_battle,
                             f"{mode} armed the simulation before initiative")
            self.assertIsNone(bs.pending_plan,
                              f"{mode} planned a turn during deployment")

    def test_tokens_move_freely_before_initiative(self):
        # Deployment: dragging a token is placement, not a 30 ft walk.
        bs = _bs()
        hero = bs.battle.entities[0]
        hero.grid_x, hero.grid_y = 12.0, 8.0
        self.assertEqual((hero.grid_x, hero.grid_y), (12.0, 8.0))
        self.assertFalse(bs.battle.combat_started)

    def test_full_sim_runs_itself_once_started(self):
        bs = _bs()
        bs._set_ai_mode("full_auto")
        bs._do_start_combat()
        self.assertTrue(bs.auto_battle)
        self.assertEqual(bs.auto_battle_mode, "full")
        for _ in range(400):
            bs._process_auto_battle()
            if not bs.auto_battle:
                break
            if bs.battle.check_battle_over():
                break
        self.assertTrue(bs.battle.check_battle_over(),
                        "täysi simulaatio ei vienyt taistelua loppuun")

    def test_a_full_sim_survives_a_run_of_bad_luck(self):
        """Kolme kierrosta ohi meneviä iskuja ei ole umpikuja.

        Auto-battle pysähtyi ennen aikojaan aina kun molemmat huitoivat
        ohi kolmella kierroksella — sitä sattuu jatkuvasti, ja simulaatio
        jäi kesken vaikka taistelu oli täysin käynnissä.
        """
        for trial in range(12):
            bs = _bs()
            bs._set_ai_mode("full_auto")
            bs._do_start_combat()
            for _ in range(600):
                bs._process_auto_battle()
                if not bs.auto_battle or bs.battle.check_battle_over():
                    break
            self.assertTrue(
                bs.battle.check_battle_over(),
                f"ajo {trial} pysähtyi kesken: "
                + "; ".join(str(m) for m in bs.logs[-3:]))

    def test_manual_mode_never_arms_the_simulation(self):
        bs = _bs()
        bs._set_ai_mode("manual")
        bs._do_start_combat()
        self.assertFalse(bs.auto_battle)

    def test_assisted_mode_suggests_but_does_not_move(self):
        # NPC wins initiative, so a plan is waiting at once — and the
        # token is still where the DM put it until a step is approved.
        hero = _mk("Hero", 3, 3, True, dex=1)
        orc = _mk("Orc", 9, 3, False, dex=20)
        bs = BattleState(_FM(), entities=[hero, orc])
        bs._set_ai_mode("suggest")
        before = (orc.grid_x, orc.grid_y)
        bs._do_start_combat()
        if bs.battle.get_current_entity() is orc:
            self.assertIsNotNone(bs.pending_plan)
            self.assertEqual((orc.grid_x, orc.grid_y), before,
                             "AI siirsi tokenin ennen hyväksyntää")


# ===================================================================== #
# 2. RESET TO THE MOMENT INITIATIVE WAS ROLLED
# ===================================================================== #
class TestResetToCombatStart(unittest.TestCase):

    def test_start_captures_a_reset_point(self):
        bs = _bs()
        self.assertIsNone(bs.combat_start_snapshot)
        bs._do_start_combat()
        self.assertIsNotNone(bs.combat_start_snapshot)

    def test_reset_restores_hp_positions_and_round(self):
        bs = _bs()
        bs._do_start_combat()
        hero, orc = bs.battle.entities[0], bs.battle.entities[1]
        start = {e.name: (e.hp, e.grid_x, e.grid_y)
                 for e in bs.battle.entities}
        # Wreck the fight thoroughly.
        for e in bs.battle.entities:
            e.take_damage(11, "slashing")
            e.grid_x += 4
        bs.battle.round = 7
        bs._reset_to_combat_start()
        for e in bs.battle.entities:
            hp, x, y = start[e.name]
            self.assertEqual(e.hp, hp, f"{e.name} hp not restored")
            self.assertEqual((e.grid_x, e.grid_y), (x, y),
                             f"{e.name} position not restored")
        self.assertEqual(bs.battle.round, 1)
        self.assertTrue(bs.battle.combat_started)

    def test_reset_clears_a_pending_suggestion(self):
        hero = _mk("Hero", 3, 3, True, dex=1)
        orc = _mk("Orc", 9, 3, False, dex=20)
        bs = BattleState(_FM(), entities=[hero, orc])
        bs._set_ai_mode("suggest")
        bs._do_start_combat()
        bs._reset_to_combat_start()
        self.assertIsNone(bs.pending_plan)
        self.assertEqual(bs.reaction_pending, [])

    def test_reset_before_combat_is_harmless(self):
        bs = _bs()
        bs._reset_to_combat_start()          # no snapshot yet
        self.assertFalse(bs.battle.combat_started)


# ===================================================================== #
# 3. BACK TO THE CAMPAIGN THE ENCOUNTER CAME FROM
# ===================================================================== #
class TestReturnToCampaign(unittest.TestCase):

    def test_it_returns_where_it_was_launched_from(self):
        fm = _FM()
        bs = _bs(fm, return_state="CAMPAIGN")
        bs._return_to_campaign()
        self.assertEqual(fm.changed_to, "CAMPAIGN")

    def test_unknown_origin_falls_back_to_the_menu(self):
        fm = _FM()
        bs = _bs(fm, return_state="NOWHERE")
        bs._return_to_campaign()
        self.assertEqual(fm.changed_to, "MENU")

    def test_no_origin_falls_back_to_the_menu(self):
        fm = _FM()
        bs = _bs(fm)
        bs._return_to_campaign()
        self.assertEqual(fm.changed_to, "MENU")


# ===================================================================== #
# 4. INITIATIVE BY HAND
# ===================================================================== #
class TestManualInitiative(unittest.TestCase):

    def test_the_editor_lists_every_combatant(self):
        bs = _bs()
        geo = bs._init_modal_rects()
        names = [r["entity"].name for r in geo["rows"]]
        self.assertEqual(sorted(names), ["Hero", "Orc"])

    def test_bumping_reorders_and_locks(self):
        bs = _bs()
        hero = next(e for e in bs.battle.entities if e.name == "Hero")
        orc = next(e for e in bs.battle.entities if e.name == "Orc")
        bs._bump_initiative(hero, 20)
        self.assertTrue(hero.initiative_locked)
        self.assertIs(bs.battle.entities[0], hero)
        bs._bump_initiative(orc, 40)
        self.assertIs(bs.battle.entities[0], orc)

    def test_start_combat_does_not_roll_over_a_hand_set_order(self):
        bs = _bs()
        hero = next(e for e in bs.battle.entities if e.name == "Hero")
        orc = next(e for e in bs.battle.entities if e.name == "Orc")
        bs._bump_initiative(hero, 18 - hero.initiative)
        bs._bump_initiative(orc, 3 - orc.initiative)
        bs._do_start_combat()
        self.assertEqual(hero.initiative, 18)
        self.assertEqual(orc.initiative, 3)
        self.assertIs(bs.battle.get_current_entity(), hero)

    def test_rolling_one_creature_leaves_the_other_alone(self):
        bs = _bs()
        hero = next(e for e in bs.battle.entities if e.name == "Hero")
        orc = next(e for e in bs.battle.entities if e.name == "Orc")
        bs._bump_initiative(orc, 9)
        before = orc.initiative
        bs._roll_initiative_for(hero)
        self.assertEqual(orc.initiative, before)
        self.assertTrue(hero.initiative_locked)

    def test_roll_all_locks_everyone(self):
        bs = _bs()
        bs._roll_all_initiative()
        for e in bs.battle.entities:
            self.assertTrue(e.initiative_locked, e.name)
        inits = [e.initiative for e in bs.battle.entities]
        self.assertEqual(inits, sorted(inits, reverse=True))

    def test_clicking_the_buttons_works(self):
        bs = _bs()
        bs._open_init_modal()
        self.assertTrue(bs.init_modal_open)
        geo = bs._init_modal_rects()
        row = geo["rows"][0]
        ent = row["entity"]
        before = ent.initiative
        bs._handle_init_modal_click(row["plus"].center)
        self.assertEqual(ent.initiative, before + 1)
        bs._handle_init_modal_click(row["minus"].center)
        self.assertEqual(ent.initiative, before)
        bs._handle_init_modal_click(geo["close"].center)
        self.assertFalse(bs.init_modal_open)

    def test_clicking_outside_closes_it(self):
        bs = _bs()
        bs._open_init_modal()
        bs._handle_init_modal_click((2, 2))
        self.assertFalse(bs.init_modal_open)

    def test_the_editor_renders(self):
        bs = _bs()
        bs._open_init_modal()
        screen = pygame.display.get_surface()
        bs.draw(screen)          # must not raise
        bs._do_start_combat()
        bs.draw(screen)


# ===================================================================== #
# 5. SAVING AN ENCOUNTER, INCLUDING BEFORE THE DICE
# ===================================================================== #
class TestEncounterSave(unittest.TestCase):

    def _real_pair(self):
        hero = Entity(hero_list[0], 2.0, 2.0, True)
        orc = Entity(library.get_monster("Orc"), 8.0, 5.0, False)
        return hero, orc

    def test_a_prepared_encounter_round_trips_before_initiative(self):
        hero, orc = self._real_pair()
        b = BattleSystem(lambda m: None, [hero, orc])
        b.update_initiative(hero, 17 - hero.initiative)
        b.update_initiative(orc, 4 - orc.initiative)
        path = os.path.join(tempfile.mkdtemp(), "prepared.json")
        b.save_state(path)

        loaded = BattleSystem.from_save(path, lambda m: None)
        self.assertFalse(loaded.combat_started,
                         "tallennettu encounter ei saa herätä valmiiksi "
                         "aloitettuna")
        by_name = {e.name: e for e in loaded.entities}
        self.assertEqual(sorted(by_name), sorted(e.name for e in b.entities))
        self.assertEqual(by_name[hero.name].initiative, 17)
        self.assertEqual(by_name[orc.name].initiative, 4)
        self.assertEqual((by_name[orc.name].grid_x, by_name[orc.name].grid_y),
                         (8.0, 5.0))

    def test_the_hand_set_order_survives_the_load_and_the_start(self):
        hero, orc = self._real_pair()
        b = BattleSystem(lambda m: None, [hero, orc])
        b.update_initiative(hero, 17 - hero.initiative)
        b.update_initiative(orc, 4 - orc.initiative)
        path = os.path.join(tempfile.mkdtemp(), "prepared2.json")
        b.save_state(path)

        loaded = BattleSystem.from_save(path, lambda m: None)
        for e in loaded.entities:
            self.assertTrue(e.initiative_locked, e.name)
        loaded.start_combat()
        self.assertEqual([e.initiative for e in loaded.entities], [17, 4])
        self.assertTrue(loaded.combat_started)

    def test_a_fight_in_progress_still_round_trips(self):
        hero, orc = self._real_pair()
        b = BattleSystem(lambda m: None, [hero, orc])
        b.start_combat()
        b.round = 3
        orc.take_damage(5, "slashing")
        path = os.path.join(tempfile.mkdtemp(), "midfight.json")
        b.save_state(path)
        loaded = BattleSystem.from_save(path, lambda m: None)
        self.assertTrue(loaded.combat_started)
        self.assertEqual(loaded.round, 3)
        self.assertEqual(
            next(e for e in loaded.entities if e.name == orc.name).hp,
            orc.hp)


# ===================================================================== #
# 6. THE CONTROL ROW ITSELF
# ===================================================================== #
class TestTheControlRow(unittest.TestCase):

    def test_the_front_row_has_no_overlapping_buttons(self):
        bs = _bs()
        row = [bs.btn_mode_manual, bs.btn_mode_assist, bs.btn_mode_sim,
               bs.btn_reset, bs.btn_save, bs.btn_back, bs.btn_tools,
               bs.btn_init]
        for i, a in enumerate(row):
            for b in row[i + 1:]:
                self.assertFalse(a.rect.colliderect(b.rect),
                                 f"{a.text} overlaps {b.text}")

    def test_the_front_row_stays_inside_the_map_area(self):
        from states.battle_constants import GRID_W
        bs = _bs()
        for b in (bs.btn_mode_manual, bs.btn_mode_assist, bs.btn_mode_sim,
                  bs.btn_reset, bs.btn_save, bs.btn_back, bs.btn_tools,
                  bs.btn_init):
            self.assertLessEqual(b.rect.right, GRID_W, b.text)

    def test_the_chosen_mode_is_the_lit_one(self):
        bs = _bs()
        from settings import COLORS
        for mode, btn in (("manual", bs.btn_mode_manual),
                          ("suggest", bs.btn_mode_assist),
                          ("full_auto", bs.btn_mode_sim)):
            bs._set_ai_mode(mode)
            bs._refresh_mode_buttons()
            self.assertEqual(btn.color, COLORS["success"], mode)
            for other in (bs.btn_mode_manual, bs.btn_mode_assist,
                          bs.btn_mode_sim):
                if other is not btn:
                    self.assertEqual(other.color, COLORS["panel"],
                                     f"{mode}: {other.text} also lit")

    def test_the_tray_hides_the_rest(self):
        bs = _bs()
        self.assertFalse(bs.tool_tray_open)
        bs._toggle_tool_tray()
        self.assertTrue(bs.tool_tray_open)
        bs._toggle_tool_tray()
        self.assertFalse(bs.tool_tray_open)


if __name__ == "__main__":
    unittest.main()
