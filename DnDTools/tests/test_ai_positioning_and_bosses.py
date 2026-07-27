"""Kuka haluaa lähelle ja kuka kauas — ja toimivatko pomot oikeasti.

Jousimies käveli suoraan velhon syliin. Syy oli se, että kykyarvoista
pääteltiin taistelutyyli: Scoutin jousi ja lyhytmiekka ovat molemmat
DEX, joten "henkinen vs fyysinen" ei koskaan valinnut kaukotaistelua ja
150 jalan jousella varustettu olento luokiteltiin lähitaistelijaksi.

Beholder puolestaan oli olento joka puree: sen kymmenen sädettä olivat
yksi toiminto ilman vahinkoa, pelastusta tai tilaa.
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
from engine.entities import Entity
from engine.battle import BattleSystem
from engine.ai.tactical_ai import TacticalAI
from engine.special_actions import resolve_special_actions
from states.battle_state import BattleState


class _FM:
    def __init__(self):
        self.screen = pygame.display.get_surface()
        self.running = True
        self.states = {}

    def change_state(self, *a, **k):
        pass


def _mon(name, x=0, y=0, player=False):
    return Entity(copy.deepcopy(library.get_monster(name)), float(x),
                  float(y), is_player=player)


def _battle(*ents):
    b = BattleSystem(lambda m: None, list(ents))
    b.terrain = []
    return b


# ===================================================================== #
# 1. WHO WANTS TO BE CLOSE
# ===================================================================== #
class TestCombatPreference(unittest.TestCase):

    def _pref(self, name):
        return TacticalAI()._get_combat_preference(_mon(name))

    def test_an_archer_is_a_ranged_combatant(self):
        # A Scout carries a shortsword AND a 150 ft longbow. Comparing
        # DEX against WIS called it a melee fighter.
        self.assertEqual(self._pref("Scout"), "ranged")

    def test_a_caster_whose_damage_is_all_area_spells_is_ranged(self):
        # An Archmage's only weapon is a dagger; everything that hurts
        # is Fireball and friends. Excluding area spells from the
        # comparison made it want dagger range.
        self.assertEqual(self._pref("Archmage"), "ranged")

    def test_a_dragon_still_wants_to_close(self):
        # Its breath is the biggest number on the sheet but it recharges;
        # counting it would turn every dragon into an artillery piece.
        self.assertEqual(self._pref("Adult Red Dragon"), "melee")

    def test_a_pure_brawler_is_melee(self):
        self.assertEqual(self._pref("Ogre"), "melee")

    def test_a_creature_with_no_melee_at_all_is_ranged(self):
        e = _mon("Ogre")
        for a in e.stats.actions:
            a.range = 60
        self.assertEqual(TacticalAI()._get_combat_preference(e), "ranged")

    def test_a_creature_with_no_ranged_option_is_melee(self):
        e = _mon("Scout")
        e.stats.actions = [a for a in e.stats.actions if a.range <= 5]
        e.stats.spells_known = []
        self.assertEqual(TacticalAI()._get_combat_preference(e), "melee")

    def test_the_sustained_figure_ignores_breath_but_counts_spells(self):
        ai = TacticalAI()
        dragon = _mon("Adult Red Dragon")
        self.assertEqual(ai._best_sustained(dragon, ranged=True), 0.0,
                         "henkäysase laskettiin kestäväksi kaukohyökkäykseksi")
        mage = _mon("Archmage")
        self.assertGreater(ai._best_sustained(mage, ranged=True), 0.0,
                           "aluetaikoja ei laskettu lainkaan")


# ===================================================================== #
# 2. AN ARCHER KEEPS ITS DISTANCE
# ===================================================================== #
class TestRangedPositioning(unittest.TestCase):

    def test_an_archer_does_not_walk_into_contact(self):
        random.seed(3)
        for start in (8, 10, 12, 14):
            sc = _mon("Scout", start, 5)
            pc = Entity(copy.deepcopy(hero_list[0]), 5.0, 5.0,
                        is_player=True)
            b = _battle(sc, pc)
            b.start_combat()
            before = b.get_distance(sc, pc)
            step = b.ai._decide_movement(sc, [pc], [], b)
            if step is None:
                continue
            sc.grid_x, sc.grid_y = step.new_x, step.new_y
            after = b.get_distance(sc, pc)
            self.assertGreater(
                after, 1.0,
                f"jousimies siirtyi kosketusetäisyydelle lähtien {start}")
            self.assertGreaterEqual(
                after, before - 0.1,
                f"jousimies lähestyi turhaan lähtien {start}")

    def test_a_line_of_sight_step_keeps_its_distance(self):
        """Näköyhteyttä hakiessa valittiin kohdetta LÄHIN ruutu, mikä on
        jousimiehelle huonoin tarjolla oleva."""
        from engine.terrain import TerrainObject
        random.seed(5)
        sc = _mon("Scout", 12, 5)
        pc = Entity(copy.deepcopy(hero_list[0]), 5.0, 5.0, is_player=True)
        b = _battle(sc, pc)
        b.terrain = [TerrainObject("wall", 8, y) for y in range(3, 8)]
        b.start_combat()
        before = b.get_distance(sc, pc)
        step = b.ai._move_to_get_los(sc, pc, b)
        if step is None:
            self.skipTest("no line of sight square within reach")
        sc.grid_x, sc.grid_y = step.new_x, step.new_y
        self.assertGreater(b.get_distance(sc, pc), 1.0,
                           "näköyhteyttä haettiin kohteen syliin asti")

    def test_cover_is_not_worth_walking_into_a_sword(self):
        random.seed(9)
        sc = _mon("Scout", 12, 5)
        brute = _mon("Ogre", 9, 5, player=True)
        b = _battle(sc, brute)
        b.start_combat()
        step = b.ai._seek_cover_position(sc, brute, [brute], b)
        if step is None:
            return
        sc.grid_x, sc.grid_y = step.new_x, step.new_y
        self.assertGreater(b.get_distance(sc, brute), 1.0,
                           "suojaa haettiin lähitaistelijan ulottuvilta")

    def test_a_ranged_creature_still_attacks_almost_every_turn(self):
        """Etäisyyden pitäminen ei saa maksaa hyökkäystä."""
        random.seed(11)
        turns = attacks = 0
        for start in range(6, 18, 2):
            sc = _mon("Scout", start, 5)
            pc = Entity(copy.deepcopy(hero_list[0]), 4.0, 5.0,
                        is_player=True)
            b = _battle(sc, pc)
            b.start_combat()
            plan = b.ai.calculate_turn(sc, b)
            turns += 1
            if any(s.step_type in ("attack", "bonus_attack", "spell")
                   and (s.target or s.targets) for s in plan.steps):
                attacks += 1
        self.assertGreaterEqual(attacks, turns - 1,
                                f"vain {attacks}/{turns} vuorolla hyökättiin")


# ===================================================================== #
# 2b. THE BOARD HAS EDGES
# ===================================================================== #
class TestTheBattlefieldIsFinite(unittest.TestCase):
    """Kun jousimiehet lakkasivat ryntäämästä, tilalle tuli päinvastainen
    vika: peräännytään ikuisesti. Yksi ranger pakeni x = -429:ään, kahdeksan
    ruutua kierroksessa kuudenkymmenen kierroksen ajan, pois ruudulta."""

    def test_bounds_cover_where_everyone_actually_is(self):
        a = _mon("Scout", 5, 5)
        bb = _mon("Ogre", 30, 22, player=True)
        b = _battle(a, bb)
        for e in (a, bb):
            self.assertTrue(b.in_ai_bounds(e.grid_x, e.grid_y), e.name)

    def test_far_off_the_board_is_refused(self):
        a = _mon("Scout", 5, 5)
        bb = _mon("Ogre", 12, 5, player=True)
        b = _battle(a, bb)
        self.assertFalse(b.in_ai_bounds(-500, 70))
        self.assertFalse(b.in_ai_bounds(70, 900))

    def test_the_ai_will_not_step_outside(self):
        a = _mon("Scout", 5, 5)
        bb = _mon("Ogre", 12, 5, player=True)
        b = _battle(a, bb)
        x0, y0, x1, y1 = b.ai_bounds()
        self.assertFalse(b.ai._enter_cell_allowed(b, a, x0 - 5, 5))
        self.assertFalse(b.ai._enter_cell_allowed(b, a, 5, y1 + 5))

    def test_a_retreat_stops_at_the_edge(self):
        random.seed(17)
        runner = _mon("Scout", 6, 6)
        chaser = _mon("Ogre", 7, 6, player=True)
        b = _battle(runner, chaser)
        b.start_combat()
        x0, y0, x1, y1 = b.ai_bounds()
        for _ in range(40):
            runner.movement_left = runner.get_speed()
            step = b.ai._move_away(runner, chaser, b)
            if step is None:
                break
            runner.grid_x, runner.grid_y = step.new_x, step.new_y
            self.assertTrue(
                b.in_ai_bounds(runner.grid_x, runner.grid_y),
                f"pakeni kentän ulkopuolelle: "
                f"{(runner.grid_x, runner.grid_y)} vs {(x0, y0, x1, y1)}")

    def test_bounds_are_generous_enough_to_manoeuvre(self):
        # Room to kite, just not to leave the county.
        a = _mon("Scout", 10, 10)
        bb = _mon("Ogre", 12, 10, player=True)
        b = _battle(a, bb)
        x0, y0, x1, y1 = b.ai_bounds()
        self.assertGreaterEqual(x1 - x0, 60)
        self.assertGreaterEqual(y1 - y0, 60)


# ===================================================================== #
# 3. THE BEHOLDER
# ===================================================================== #
class TestTheBeholder(unittest.TestCase):

    RAYS = ["Charm Ray", "Paralyzing Ray", "Fear Ray", "Slowing Ray",
            "Enervation Ray", "Telekinetic Ray", "Sleep Ray",
            "Petrification Ray", "Disintegration Ray", "Death Ray"]

    def setUp(self):
        self.b = library.get_monster("Beholder")

    def test_all_ten_rays_exist(self):
        names = [a.name for a in self.b.actions]
        missing = [r for r in self.RAYS if r not in names]
        self.assertEqual(missing, [], "puuttuvat säteet")

    def test_every_ray_actually_does_something(self):
        for a in self.b.actions:
            if not a.name.endswith("Ray"):
                continue
            self.assertTrue(
                a.damage_dice or a.applies_condition,
                f"{a.name} ei tee vahinkoa eikä aiheuta tilaa")
            self.assertTrue(a.condition_dc, f"{a.name}: ei pelastus-DC:tä")
            self.assertTrue(a.condition_save, f"{a.name}: ei pelastusta")

    def test_the_rays_carry_the_monster_manual_numbers(self):
        by = {a.name: a for a in self.b.actions}
        self.assertEqual(by["Death Ray"].damage_dice, "10d10")
        self.assertEqual(by["Disintegration Ray"].damage_dice, "10d8")
        self.assertEqual(by["Enervation Ray"].damage_dice, "8d8")
        for r in self.RAYS:
            self.assertEqual(by[r].condition_dc, 16, r)
            self.assertEqual(by[r].range, 120, r)

    def test_eye_rays_fires_three_of_them(self):
        eye = next(a for a in self.b.actions if a.name == "Eye Rays")
        self.assertTrue(eye.is_multiattack)
        self.assertEqual(eye.multiattack_count, 3)
        self.assertEqual(len(eye.multiattack_targets), 3)
        names = [a.name for a in self.b.actions]
        for sub in eye.multiattack_targets:
            self.assertIn(sub, names)

    def test_it_has_a_legendary_action_it_can_spend(self):
        res = resolve_special_actions(self.b, "legendary")
        self.assertTrue(res, "3 legendaarista toimintoa eikä mitään mihin "
                             "käyttää ne")
        self.assertTrue(any(getattr(sa, "action", None) is not None
                            and sa.action.damage_dice for sa in res))

    def test_the_antimagic_cone_is_recorded(self):
        f = next((x for x in self.b.features
                  if x.name == "Antimagic Cone"), None)
        self.assertIsNotNone(f)
        self.assertEqual(f.aura_radius, 150)

    def test_it_fights_with_its_eyes_not_its_teeth(self):
        random.seed(2)
        used = []
        party = [Entity(copy.deepcopy(h), 3.0, 3.0 + i * 2, True)
                 for i, h in enumerate(hero_list[:4])]
        boss = Entity(copy.deepcopy(self.b), 14.0, 5.0, False)
        bs = BattleState(_FM(), entities=party + [boss])
        bs._set_ai_mode("full_auto")
        bs._do_start_combat()
        for _ in range(600):
            bs.last_executed_step = None
            bs._process_auto_battle()
            st = bs.last_executed_step
            if st is not None and st.attacker is boss and st.action_name:
                used.append(st.action_name)
            if not bs.auto_battle or bs.battle.check_battle_over():
                break
        self.assertTrue(used, "beholder ei tehnyt yhtään toimintoa")
        rays = [u for u in used if "Ray" in u]
        self.assertTrue(rays, f"beholder käytti vain: {set(used)}")


# ===================================================================== #
# 3b. A MULTIATTACK MAKES AS MANY ATTACKS AS IT SAYS
# ===================================================================== #
class TestMultiattackCount(unittest.TestCase):
    """"2 x Greatsword" is written with ONE name and a count of two. The
    count was only consulted when the name list was empty, so a Knight
    swung once instead of twice and a Gladiator once instead of three
    times."""

    def _attacks(self, name):
        random.seed(5)
        st = library.get_monster(name)
        multi = next(a for a in st.actions if a.is_multiattack)
        foe = Entity(copy.deepcopy(hero_list[0]), 5.0, 5.0, is_player=True)
        m = Entity(copy.deepcopy(st), 6.0, 5.0, is_player=False)
        b = _battle(m, foe)
        b.start_combat()
        steps = b.ai._execute_multiattack(m, multi, [foe], [], b)
        return len(steps), multi.multiattack_count

    def test_a_knight_swings_twice(self):
        got, want = self._attacks("Knight")
        self.assertEqual(got, want)

    def test_a_gladiator_attacks_three_times(self):
        got, want = self._attacks("Gladiator")
        self.assertEqual(got, want)

    def test_a_named_list_is_still_honoured(self):
        got, want = self._attacks("Vampire")
        self.assertEqual(got, want)

    def test_no_stat_block_under_delivers(self):
        short = []
        for st in library.get_all_monsters():
            for a in st.actions or ():
                if not a.is_multiattack:
                    continue
                names = list(a.multiattack_targets or [])
                count = a.multiattack_count or 0
                if not names or not count:
                    continue
                m = Entity(copy.deepcopy(st), 6.0, 5.0, is_player=False)
                foe = Entity(copy.deepcopy(hero_list[0]), 5.0, 5.0,
                             is_player=True)
                b = _battle(m, foe)
                b.start_combat()
                steps = b.ai._execute_multiattack(m, a, [foe], [], b)
                if steps and len(steps) < count:
                    short.append(f"{st.name}: {len(steps)} of {count}")
        self.assertEqual(short, [],
                         "nämä tekevät vähemmän hyökkäyksiä kuin lupaavat")


# ===================================================================== #
# 4. EVERY LEGENDARY CREATURE HAS SOMETHING TO SPEND ITS ACTIONS ON
# ===================================================================== #
class TestLegendaryRoster(unittest.TestCase):

    def test_every_legendary_creature_resolves_at_least_one_action(self):
        broken = []
        for st in library.get_all_monsters():
            if not st.legendary_action_count:
                continue
            if not resolve_special_actions(st, "legendary"):
                broken.append(st.name)
        self.assertEqual(broken, [],
                         "legendaarisia toimintoja luvattu, mutta mitään "
                         "ei ratkea")

    def test_a_declared_legendary_resistance_can_actually_be_spent(self):
        """Kuluminen lukee stats.legendary_resistance_count — erillinen
        piirre on vain listausta varten, joten testataan mekaniikka."""
        from engine.rules import can_use_legendary_resistance, \
            use_legendary_resistance
        broken = []
        for st in library.get_all_monsters():
            if not st.legendary_resistance_count:
                continue
            e = Entity(copy.deepcopy(st), 0.0, 0.0, is_player=False)
            if e.legendary_resistances_left != st.legendary_resistance_count:
                broken.append(f"{st.name}: alkumäärä väärin")
                continue
            if not can_use_legendary_resistance(e):
                broken.append(f"{st.name}: ei voi käyttää")
                continue
            use_legendary_resistance(e)
            if e.legendary_resistances_left != \
                    st.legendary_resistance_count - 1:
                broken.append(f"{st.name}: kulutus ei vähentänyt")
        self.assertEqual(broken, [])

    def test_the_death_tyrant_rays_work_too(self):
        dt = library.get_monster("Death Tyrant")
        eye = next(a for a in dt.actions if a.name == "Eye Rays")
        self.assertTrue(eye.is_multiattack)
        for sub in eye.multiattack_targets:
            act = next(a for a in dt.actions if a.name == sub)
            self.assertTrue(act.damage_dice or act.applies_condition, sub)


if __name__ == "__main__":
    unittest.main()
