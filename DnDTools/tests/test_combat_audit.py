"""Combat audit — testit työkalulle joka etsii viat muualta.

Pelinjohtaja pyysi työkalun, joka pelaa valtavan määrän hahmoja,
loitsuja ja luokkia oikeissa taisteluissa, kirjaa kaiken ylös ja kertoo
lokitiedostossa onko jossain vikaa.

Auditoija itse on koodia siinä missä muukin, ja **väärä löydös on
pahempi kuin ei löydöstä ollenkaan**: jos loki huutaa asioista jotka
ovat kunnossa, kukaan ei lue sitä. Siksi nämä testit rakentavat
tilanteita joissa tiedetään mikä on rikki ja mikä ei, ja vaativat että
auditoija erottaa ne toisistaan.

Kaksi väärää löydöstä jäi kiinni jo rakennusvaiheessa:

  * näköyhteystarkistus käytti ``has_line_of_sight``-metodia, joka
    palauttaa Falsen myös näkymättömälle kohteelle — cloaker joka puri
    näkymätöntä rogueta täysin tyhjällä kartalla raportoitiin
    "ampumisena seinän läpi",
  * ja moottorin sisäinen Lethargic-tila (Hasten jälkivaikutus) sekä
    sisällön "Turned" ja "Max HP Reduced" raportoitiin virheinä, vaikka
    kyse on puuttuvasta taulukkomerkinnästä eikä rikkinäisestä
    säännöstä.
"""
import sys
import os
import copy
import json
import random
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import unittest

import pygame
pygame.init()
pygame.display.set_mode((1920, 1080))

from data.conditions import CONDITIONS
from data.heroes import hero_list
from data.library import library
from engine.battle import BattleSystem
from engine.entities import Entity
from engine.terrain import TerrainObject
from engine.combat_audit import (
    AuditReport, AuditRunner, Finding, Scenario, _Watcher,
    build_scenarios, format_report, report_to_dict, write_report,
    DEPTHS, ERROR, WARNING, INFO,
)


def _hero(name="Magnus Dragonius"):
    return copy.deepcopy({h.name: h for h in hero_list}[name])


def _mon(name, x, y, player=False):
    return Entity(copy.deepcopy(library.get_monster(name)),
                  float(x), float(y), is_player=player)


def _battle(*ents, terrain=None):
    b = BattleSystem(log_callback=lambda s: None,
                     initial_entities=list(ents))
    b.terrain = list(terrain or [])
    return b


def _fresh_watcher():
    rep = AuditReport()
    return rep, _Watcher(rep)


def _titles(rep):
    return {f.title for f in rep.findings.values()}


# ===================================================================== #
# 1. THE WATCHER CATCHES WHAT IT SHOULD
# ===================================================================== #
class TestWatcherCatchesFaults(unittest.TestCase):

    def test_two_creatures_in_one_square(self):
        rep, w = _fresh_watcher()
        a = _mon("Goblin", 5, 5)
        b = _mon("Goblin", 5, 5)
        w.check_state(_battle(a, b), "t")
        self.assertIn("Two creatures in one square", _titles(rep))

    def test_a_large_creature_half_inside_a_small_one(self):
        rep, w = _fresh_watcher()
        ogre = _mon("Ogre", 5, 5)          # 2x2
        gob = _mon("Goblin", 6, 6)
        w.check_state(_battle(ogre, gob), "t")
        self.assertIn("Two creatures in one square", _titles(rep))

    def test_a_creature_standing_in_a_wall(self):
        rep, w = _fresh_watcher()
        gob = _mon("Goblin", 5, 5)
        w.check_state(_battle(gob, terrain=[TerrainObject("wall", 5, 5)]), "t")
        self.assertIn("Creature inside impassable terrain", _titles(rep))

    def test_hit_points_above_maximum(self):
        rep, w = _fresh_watcher()
        gob = _mon("Goblin", 5, 5)
        gob.hp = gob.max_hp + 5
        w.check_state(_battle(gob), "t")
        self.assertIn("Hit points above maximum", _titles(rep))

    def test_negative_spell_slots(self):
        rep, w = _fresh_watcher()
        arch = _mon("Archmage", 5, 5)
        b = _battle(arch)
        w.baseline(b)
        arch.spell_slots["3rd"] = -1
        w.check_state(b, "t")
        self.assertIn("Negative spell slots", _titles(rep))

    def test_more_spell_slots_than_it_started_with(self):
        rep, w = _fresh_watcher()
        arch = _mon("Archmage", 5, 5)
        b = _battle(arch)
        w.baseline(b)
        lvl = next(iter(arch.spell_slots))
        arch.spell_slots[lvl] += 3
        w.check_state(b, "t")
        self.assertIn("More spell slots than it started with", _titles(rep))

    def test_impossible_legendary_action_counts(self):
        rep, w = _fresh_watcher()
        d = _mon("Adult Red Dragon", 5, 5)
        b = _battle(d)
        w.baseline(b)
        d.legendary_actions_left = d.stats.legendary_action_count + 2
        w.check_state(b, "t")
        self.assertIn("More legendary actions than the maximum", _titles(rep))
        rep2, w2 = _fresh_watcher()
        d.legendary_actions_left = -1
        w2.check_state(b, "t")
        self.assertIn("Negative legendary actions", _titles(rep2))

    def test_negative_movement(self):
        rep, w = _fresh_watcher()
        gob = _mon("Goblin", 5, 5)
        gob.movement_left = -10
        w.check_state(_battle(gob), "t")
        self.assertIn("Negative movement remaining", _titles(rep))

    def test_death_saves_past_three(self):
        rep, w = _fresh_watcher()
        gob = _mon("Goblin", 5, 5)
        gob.death_save_failures = 7
        w.check_state(_battle(gob), "t")
        self.assertIn("Death saves past three", _titles(rep))

    def test_a_condition_missing_from_the_table(self):
        rep, w = _fresh_watcher()
        gob = _mon("Goblin", 5, 5)
        gob.conditions.add("Bewildered")
        w.check_state(_battle(gob), "t")
        found = [f for f in rep.findings.values()
                 if "condition missing from the table" in f.title]
        self.assertTrue(found)
        self.assertEqual(found[0].severity, WARNING,
                         "an unlisted condition is a gap, not a broken rule")

    def test_a_downed_creature_taking_an_action(self):
        from engine.ai.models import ActionStep
        rep, w = _fresh_watcher()
        gob = _mon("Goblin", 5, 5)
        gob.hp = -1
        step = ActionStep(step_type="attack", attacker=gob,
                          action_name="Scimitar")
        w.check_step(_battle(gob), step, "t")
        self.assertIn("A downed creature acted", _titles(rep))

    def test_an_attack_from_beyond_its_reach(self):
        from engine.ai.models import ActionStep
        rep, w = _fresh_watcher()
        gob = _mon("Goblin", 5, 5)
        pc = Entity(_hero(), 15, 5, is_player=True)
        melee = next(a for a in gob.stats.actions
                     if a.range <= 5 and not a.is_multiattack)
        step = ActionStep(step_type="attack", attacker=gob, target=pc,
                          targets=[pc], action=melee,
                          action_name=melee.name)
        w.check_step(_battle(gob, pc), step, "t")
        self.assertIn("Attack made beyond its reach", _titles(rep))

    def test_an_attack_through_a_wall(self):
        from engine.ai.models import ActionStep
        rep, w = _fresh_watcher()
        gob = _mon("Goblin", 4, 5)
        pc = Entity(_hero(), 8, 5, is_player=True)
        walls = [TerrainObject("wall", 6, y) for y in range(0, 12)]
        ranged = next((a for a in gob.stats.actions if a.range > 10), None)
        if ranged is None:
            self.skipTest("no ranged attack on this stat block")
        step = ActionStep(step_type="attack", attacker=gob, target=pc,
                          targets=[pc], action=ranged,
                          action_name=ranged.name)
        w.check_step(_battle(gob, pc, terrain=walls), step, "t")
        self.assertIn("Attack made through solid terrain", _titles(rep))

    def test_moving_further_than_the_speed_allows(self):
        from engine.ai.models import ActionStep
        rep, w = _fresh_watcher()
        gob = _mon("Goblin", 5, 5)
        step = ActionStep(step_type="move", attacker=gob, movement_ft=500)
        w.check_step(_battle(gob), step, "t")
        self.assertIn("Moved further than its speed allows", _titles(rep))

    def test_a_save_with_no_dc(self):
        from engine.ai.models import ActionStep
        rep, w = _fresh_watcher()
        gob = _mon("Goblin", 5, 5)
        step = ActionStep(step_type="attack", attacker=gob,
                          action_name="Something",
                          save_ability="Strength", save_dc=0)
        w.check_step(_battle(gob), step, "t")
        self.assertIn("Saving throw with no DC", _titles(rep))


# ===================================================================== #
# 2. AND STAYS QUIET ABOUT WHAT IS FINE
#    A noisy auditor is a useless one.
# ===================================================================== #
class TestWatcherDoesNotCryWolf(unittest.TestCase):

    def test_a_clean_board_reports_nothing(self):
        rep, w = _fresh_watcher()
        a = _mon("Goblin", 2, 2)
        b = _mon("Goblin", 9, 9)
        bat = _battle(a, b)
        w.baseline(bat)
        w.check_state(bat, "t")
        self.assertEqual(rep.findings, {})

    def test_a_flyer_above_a_wall_is_not_standing_in_it(self):
        rep, w = _fresh_watcher()
        d = _mon("Adult Red Dragon", 5, 5)
        d.is_flying = True
        d.elevation = 40
        w.check_state(_battle(d, terrain=[TerrainObject("wall", 5, 5)]), "t")
        self.assertEqual(rep.findings, {})

    def test_attacking_an_invisible_target_is_legal(self):
        """Tämä oli auditoijan oma väärä löydös: has_line_of_sight on
        False myös näkymättömälle, ja näkymättömän lyöminen on sallittua
        (haitalla). Cloaker tyhjällä kartalla raportoitiin ampumisena
        seinän läpi."""
        from engine.ai.models import ActionStep
        rep, w = _fresh_watcher()
        atk = _mon("Cloaker", 5, 5)
        pc = Entity(_hero(), 6, 5, is_player=True)
        pc.add_condition("Invisible")
        melee = next(a for a in atk.stats.actions
                     if not a.is_multiattack and a.damage_dice)
        step = ActionStep(step_type="attack", attacker=atk, target=pc,
                          targets=[pc], action=melee, action_name=melee.name)
        b = _battle(atk, pc)                       # no terrain at all
        self.assertFalse(b.has_line_of_sight(atk, pc))
        w.check_step(b, step, "t")
        self.assertNotIn("Attack made through solid terrain", _titles(rep))

    def test_an_area_attack_may_catch_things_round_a_corner(self):
        from engine.ai.models import ActionStep
        rep, w = _fresh_watcher()
        d = _mon("Adult Red Dragon", 2, 5)
        pc = Entity(_hero(), 9, 5, is_player=True)
        breath = next(a for a in d.stats.actions if a.aoe_radius > 0)
        step = ActionStep(step_type="attack", attacker=d, target=pc,
                          targets=[pc], action=breath,
                          action_name=breath.name, aoe_center=(5, 5))
        walls = [TerrainObject("wall", 6, y) for y in range(0, 12)]
        w.check_step(_battle(d, pc, terrain=walls), step, "t")
        self.assertNotIn("Attack made through solid terrain", _titles(rep))

    def test_a_reach_weapon_may_strike_from_its_reach(self):
        from engine.ai.models import ActionStep
        rep, w = _fresh_watcher()
        d = _mon("Adult Red Dragon", 2, 5)
        pc = Entity(_hero(), 6, 5, is_player=True)
        bite = next(a for a in d.stats.actions
                    if a.reach >= 10 and not a.is_multiattack)
        step = ActionStep(step_type="attack", attacker=d, target=pc,
                          targets=[pc], action=bite, action_name=bite.name)
        w.check_step(_battle(d, pc), step, "t")
        self.assertNotIn("Attack made beyond its reach", _titles(rep))

    def test_an_opportunity_attack_is_not_judged_after_the_fact(self):
        """Vapaaisku tehdään sillä hetkellä kun kohde lähtee — jälkikäteen
        mitattuna se on aina liian kaukana."""
        from engine.ai.models import ActionStep
        rep, w = _fresh_watcher()
        gob = _mon("Goblin", 5, 5)
        pc = Entity(_hero(), 15, 5, is_player=True)
        melee = next(a for a in gob.stats.actions
                     if a.range <= 5 and not a.is_multiattack)
        step = ActionStep(step_type="reaction", attacker=gob, target=pc,
                          targets=[pc], action=melee, action_name=melee.name)
        w.check_step(_battle(gob, pc), step, "t")
        self.assertNotIn("Attack made beyond its reach", _titles(rep))

    def test_a_known_condition_is_counted_not_reported(self):
        rep, w = _fresh_watcher()
        gob = _mon("Goblin", 5, 5)
        cond = sorted(CONDITIONS)[0]
        gob.conditions.add(cond)
        w.check_state(_battle(gob), "t")
        self.assertEqual(rep.findings, {})
        self.assertEqual(rep.conditions_seen[cond], 1)

    def test_the_watcher_never_changes_the_battle(self):
        rep, w = _fresh_watcher()
        a = _mon("Ogre", 3, 3)
        b = _mon("Goblin", 9, 9)
        bat = _battle(a, b)
        w.baseline(bat)
        before = [(e.name, e.hp, e.grid_x, e.grid_y, dict(e.spell_slots),
                   set(e.conditions)) for e in bat.entities]
        for _ in range(3):
            w.check_state(bat, "t")
        after = [(e.name, e.hp, e.grid_x, e.grid_y, dict(e.spell_slots),
                  set(e.conditions)) for e in bat.entities]
        self.assertEqual(before, after, "the auditor mutated the battle")


# ===================================================================== #
# 3. SCENARIOS
# ===================================================================== #
class TestScenarioMatrix(unittest.TestCase):

    def test_every_depth_builds_a_matrix(self):
        for depth in DEPTHS:
            with self.subTest(depth=depth):
                sc = build_scenarios(depth)
                self.assertGreater(len(sc), 20)
                self.assertEqual(len({s.suite for s in sc}),
                                 5, "a whole suite went missing")

    def test_deeper_settings_do_more_work(self):
        q = len(build_scenarios("quick"))
        s = len(build_scenarios("standard"))
        d = len(build_scenarios("deep"))
        self.assertLess(q, s)
        self.assertLess(s, d)

    def test_the_matrix_is_the_same_every_time(self):
        a = [(s.suite, s.label, s.seed) for s in build_scenarios("quick")]
        b = [(s.suite, s.label, s.seed) for s in build_scenarios("quick")]
        self.assertEqual(a, b, "scenario order is not reproducible")

    def test_the_deep_run_fields_every_monster_in_the_library(self):
        sc = build_scenarios("deep")
        fielded = set()
        for s in sc:
            fielded.update(s.enemies)
        every = {m.name for m in library.get_all_monsters()}
        missing = every - fielded
        self.assertEqual(missing, set(),
                         f"{len(missing)} stat blocks never get a fight")

    def test_every_class_in_the_roster_gets_played(self):
        sc = build_scenarios("deep")
        played = set()
        for s in sc:
            played.update(s.players)
        self.assertEqual(set(h.name for h in hero_list) - played, set())

    def test_the_named_players_and_maps_all_exist(self):
        from data.maps import PREMADE_MAPS
        names = {h.name for h in hero_list}
        for s in build_scenarios("standard"):
            for p in s.players:
                self.assertIn(p, names, f"{s.label}: unknown hero {p}")
            if s.map_key:
                self.assertIn(s.map_key, PREMADE_MAPS, s.map_key)
            for e in s.enemies:
                library.get_monster(e)      # raises if unknown


# ===================================================================== #
# 4. THE RUNNER
# ===================================================================== #
class TestRunner(unittest.TestCase):

    def _tiny(self):
        return [Scenario(suite="t", label="tiny", seed=1, map_key="",
                         players=["Magnus Dragonius"],
                         enemies=["Goblin", "Goblin"])]

    def test_it_plays_a_battle_and_counts_it(self):
        r = AuditRunner("quick", scenarios=self._tiny())
        rep = r.run_all()
        self.assertEqual(rep.battles, 1)
        self.assertGreater(rep.steps, 0)
        self.assertGreater(rep.rounds, 0)

    def test_it_records_what_actually_happened(self):
        r = AuditRunner("quick", scenarios=self._tiny())
        rep = r.run_all()
        self.assertTrue(rep.step_types, "no steps observed at all")
        self.assertTrue(rep.actions_used, "no actions observed")
        self.assertTrue(rep.classes_played)
        self.assertTrue(rep.monsters_played)

    def test_it_runs_in_slices_and_reports_progress(self):
        sc = self._tiny() * 6
        r = AuditRunner("quick", scenarios=sc)
        self.assertEqual(r.progress, 0.0)
        slices = 0
        while not r.run_slice(0.001) and slices < 200:
            slices += 1
        self.assertTrue(r.done)
        self.assertEqual(r.progress, 1.0)
        self.assertEqual(r.report.battles, len(sc))

    def test_a_broken_scenario_is_reported_not_raised(self):
        bad = [Scenario(suite="t", label="nonsense", seed=1, map_key="",
                        players=["No Such Hero"],
                        enemies=["No Such Monster"])]
        rep = AuditRunner("quick", scenarios=bad).run_all()
        self.assertEqual(rep.battles, 1)      # it tried

    def test_a_fight_that_never_ends_is_reported(self):
        r = AuditRunner("quick", scenarios=self._tiny())
        r.MAX_STEPS_PER_BATTLE = 1            # guarantee the cap is hit
        rep = r.run_all()
        self.assertIn("Fight hit the step cap", _titles(rep))

    def test_the_elapsed_time_is_recorded(self):
        rep = AuditRunner("quick", scenarios=self._tiny()).run_all()
        self.assertGreater(rep.elapsed_s, 0.0)

    def test_a_real_quick_slice_finds_and_covers_things(self):
        """Yksi oikea siivu koko matriisista: kattavuuslaskurien pitää
        täyttyä ja ajon pysyä pystyssä."""
        sc = build_scenarios("quick")[:14]
        rep = AuditRunner("quick", scenarios=sc).run_all()
        self.assertEqual(rep.battles, len(sc))
        self.assertGreater(len(rep.actions_used), 3)
        self.assertGreater(sum(rep.step_types.values()), 50)


# ===================================================================== #
# 5. THE REPORT AND THE LOG FILE
# ===================================================================== #
class TestReporting(unittest.TestCase):

    def _report(self):
        rep = AuditReport(depth="quick", started="now")
        rep.battles, rep.steps, rep.rounds = 3, 40, 9
        rep.elapsed_s = 1.5
        rep.note(ERROR, "rules", "Something impossible", "battle 1: proof")
        rep.note(ERROR, "rules", "Something impossible", "battle 2: proof")
        rep.note(WARNING, "coverage", "Something unused", "spell X")
        rep.spells_cast["Fireball"] = 4
        rep.classes_played["Wizard"] = 1
        rep.conditions_seen["Prone"] = 2
        return rep

    def test_findings_are_deduplicated_and_counted(self):
        rep = self._report()
        f = rep.findings[("rules", "Something impossible")]
        self.assertEqual(f.count, 2)
        self.assertEqual(len(f.examples), 2)

    def test_evidence_is_capped_so_one_fault_cannot_flood_the_log(self):
        f = Finding(severity=ERROR, category="x", title="y")
        for i in range(500):
            f.add(f"occurrence {i}")
        self.assertEqual(f.count, 500)
        self.assertLessEqual(len(f.examples), 4)

    def test_errors_sort_above_warnings(self):
        rep = self._report()
        order = [f.severity for f in rep.sorted_findings()]
        self.assertEqual(order, sorted(order,
                                       key=lambda s: {"error": 0,
                                                      "warning": 1,
                                                      "info": 2}[s]))

    def test_the_log_says_what_happened_and_what_was_covered(self):
        text = format_report(self._report())
        for expected in ("COMBAT AUDIT", "FINDINGS", "COVERAGE",
                         "Something impossible", "Fireball", "battles"):
            self.assertIn(expected, text)

    def test_a_clean_run_says_so_in_plain_words(self):
        rep = AuditReport(depth="quick", started="now")
        rep.battles = 5
        text = format_report(rep)
        self.assertIn("no rule or state violations found", text)

    def test_the_json_twin_is_machine_readable(self):
        d = report_to_dict(self._report())
        json.dumps(d)                      # must not raise
        self.assertEqual(len(d["findings"]), 2)
        self.assertIn("coverage", d)
        self.assertEqual(d["coverage"]["spells_cast"]["Fireball"], 4)

    def test_writing_produces_both_files(self):
        rep = self._report()
        with tempfile.TemporaryDirectory() as tmp:
            path = write_report(rep, tmp)
            self.assertTrue(os.path.exists(path))
            self.assertTrue(path.endswith(".log"))
            twin = path[:-4] + ".json"
            self.assertTrue(os.path.exists(twin))
            with open(path, encoding="utf-8") as fh:
                self.assertIn("Something impossible", fh.read())
            with open(twin, encoding="utf-8") as fh:
                self.assertEqual(json.load(fh)["battles"], 3)


# ===================================================================== #
# 6. THE SCREEN
# ===================================================================== #
class TestAuditScreen(unittest.TestCase):

    def _state(self):
        from states.combat_audit_state import CombatAuditState

        class _FM:
            def __init__(self):
                self.screen = pygame.display.get_surface()
                self.states = {}
                self.opened = []

            def change_state(self, name, **k):
                self.opened.append(name)

        return CombatAuditState(_FM())

    def test_it_opens_and_draws_before_anything_has_run(self):
        st = self._state()
        screen = pygame.display.get_surface()
        screen.fill((0, 0, 0))
        st.draw(screen)
        self.assertFalse(st.running)
        self.assertIsNone(st.report)

    def test_it_shows_how_much_work_each_depth_is(self):
        st = self._state()
        for depth in DEPTHS:
            self.assertGreater(st.counts[depth], 0)

    def test_a_run_progresses_frame_by_frame_and_finishes(self):
        st = self._state()
        st.runner = AuditRunner("quick", scenarios=[
            Scenario(suite="t", label="tiny", seed=1, map_key="",
                     players=["Magnus Dragonius"], enemies=["Goblin"])] * 3)
        screen = pygame.display.get_surface()
        frames = 0
        while st.running and frames < 500:
            st.update()
            screen.fill((0, 0, 0))
            st.draw(screen)        # the progress bar must draw mid-run
            frames += 1
        self.assertFalse(st.running)
        self.assertIsNotNone(st.report)
        self.assertEqual(st.report.battles, 3)

    def test_the_finished_report_draws(self):
        st = self._state()
        st.runner = AuditRunner("quick", scenarios=[
            Scenario(suite="t", label="tiny", seed=1, map_key="",
                     players=["Magnus Dragonius"], enemies=["Goblin"])])
        while st.running:
            st.update()
        screen = pygame.display.get_surface()
        screen.fill((0, 0, 0))
        st.draw(screen)
        self.assertTrue(st.log_path, "no log file was written")
        self.assertTrue(os.path.exists(st.log_path))

    def test_stopping_early_keeps_what_was_found(self):
        st = self._state()
        st.runner = AuditRunner("quick", scenarios=[
            Scenario(suite="t", label="tiny", seed=1, map_key="",
                     players=["Magnus Dragonius"], enemies=["Goblin"])] * 40)
        st.update()
        self.assertTrue(st.running)
        played = st.runner.index
        st._stop()
        self.assertFalse(st.running)
        self.assertIsNotNone(st.report)
        self.assertEqual(st.report.battles, played)

    def test_escape_leaves_the_screen(self):
        st = self._state()
        st.handle_events([pygame.event.Event(pygame.KEYDOWN,
                                             key=pygame.K_ESCAPE)])
        self.assertIn("MENU", st.manager.opened)

    def test_the_depth_can_be_changed_before_a_run_but_not_during(self):
        st = self._state()
        st._set_depth("deep")
        self.assertEqual(st.depth, "deep")
        st.runner = AuditRunner("quick", scenarios=[
            Scenario(suite="t", label="tiny", seed=1, map_key="",
                     players=["Magnus Dragonius"], enemies=["Goblin"])] * 40)
        st._set_depth("quick")
        self.assertEqual(st.depth, "deep", "depth changed mid-run")

    def test_it_is_reachable_from_the_main_menu(self):
        import inspect
        from states import menu_state
        src = inspect.getsource(menu_state.MenuState.__init__)
        self.assertIn("COMBAT_AUDIT", src)
        with open(os.path.join(os.path.dirname(__file__), "..",
                               "main.py"), encoding="utf-8") as fh:
            main_src = fh.read()
        self.assertIn("COMBAT_AUDIT", main_src)
        self.assertIn("CombatAuditState", main_src)


# ===================================================================== #
# 7. THE ENGINE SPEED-UP THE AUDIT FORCED
# ===================================================================== #
class TestTerrainIndex(unittest.TestCase):
    """get_terrain_at scanned the whole terrain list. On the city map
    that is two thousand comparisons for every passability test, and
    pathfinding does thousands of those per turn."""

    def test_it_finds_the_same_tiles_a_scan_would(self):
        from data.maps import load_map_terrain
        terr = load_map_terrain("grand_city")
        b = _battle(terrain=terr)
        by_scan = {}
        for t in terr:
            by_scan.setdefault((t.grid_x, t.grid_y), t)
        for (x, y), t in list(by_scan.items())[::37]:
            self.assertIs(b.get_terrain_at(x, y), t, f"({x},{y})")

    def test_empty_squares_are_still_empty(self):
        b = _battle(terrain=[TerrainObject("wall", 5, 5)])
        self.assertIsNone(b.get_terrain_at(9, 9))
        self.assertIsNotNone(b.get_terrain_at(5, 5))

    def test_it_notices_when_the_terrain_changes(self):
        b = _battle(terrain=[TerrainObject("wall", 5, 5)])
        self.assertIsNotNone(b.get_terrain_at(5, 5))
        b.terrain = [TerrainObject("wall", 7, 7)]
        self.assertIsNone(b.get_terrain_at(5, 5))
        self.assertIsNotNone(b.get_terrain_at(7, 7))
        b.terrain.append(TerrainObject("wall", 8, 8))
        self.assertIsNotNone(b.get_terrain_at(8, 8))
        b.remove_terrain_at(8, 8)
        self.assertIsNone(b.get_terrain_at(8, 8))

    def test_opening_a_door_does_not_stale_the_index(self):
        door = TerrainObject("door", 5, 5)
        b = _battle(terrain=[door])
        self.assertFalse(b.get_terrain_at(5, 5).passable)
        door.door_open = True
        self.assertTrue(b.get_terrain_at(5, 5).passable)

    def test_it_is_much_faster_than_scanning_the_big_map(self):
        import time
        from data.maps import load_map_terrain
        terr = load_map_terrain("grand_city")
        b = _battle(terrain=terr)
        b.get_terrain_at(0, 0)                 # build the index
        t0 = time.perf_counter()
        for i in range(4000):
            b.get_terrain_at(i % 60, (i // 60) % 44)
        indexed = time.perf_counter() - t0
        t0 = time.perf_counter()
        for i in range(4000):
            x, y = i % 60, (i // 60) % 44
            next((t for t in terr if t.occupies(x, y)), None)
        scanned = time.perf_counter() - t0
        self.assertLess(indexed * 10, scanned,
                        f"index {indexed:.3f}s vs scan {scanned:.3f}s")


if __name__ == "__main__":
    unittest.main()
