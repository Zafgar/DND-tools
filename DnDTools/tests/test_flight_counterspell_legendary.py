"""Lentäminen, counterspell ja legendaariset toiminnot.

Pelinjohtaja kysyi kolme asiaa: toimiiko lentäminen ja ymmärtääkö AI
sen, osataanko counterspell käyttää järkevästi, ja käytetäänkö
legendaarisia toimintoja siinä kohtaa missä niistä on hyötyä eikä vain
spammata heti kun niitä on.

Kaikki kolme olivat rikki eri tavoilla, ja jokainen näistä testeistä
vastaa yhtä oikeaa vikaa:

  1. get_speed() ei koskaan katsonut fly_speed-arvoa. Virvatuli (kävely
     0, lento 50) ei voinut liikkua ruutuakaan, ja jättiläiskotka lensi
     10 jalkaa kierroksessa 80:n sijaan.
  2. Korkeus vain nousi — jokainen haara käytti max():ia eikä mikään
     laskeutunut. Ilmaan noussut lähitaistelija ei enää koskaan
     ylettänyt maassa olevaan viholliseen.
  3. Counterspell ei tarkistanut näköyhteyttä: se lensi kiviseinän läpi
     ja sokea velho torjui loitsun jota ei voinut nähdä.
  4. Legendaarinen toiminto valittiin aina parhaan pisteen mukaan, oli
     se kuinka arvoton tahansa, joten muinainen lohikäärme poltti kaikki
     kolme pistettä joka kierros ensimmäisestä alkaen.
  5. aura_radius-pohjainen Wing Attack sai kantaman 30 jalkaa, joten
     lohikäärme "siipi-iski" kolmen ruudun päähän kuin tulipallolla.
  6. "Tail Attack" ei löytänyt "Tail"-hyökkäystä, joten se rakennettiin
     paljaista nopista ja sai 60 jalan kantaman.
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
from engine.ai import TacticalAI
from engine.special_actions import resolve_special_actions
from engine.terrain import TerrainObject


def _mon(name, x, y, player=False):
    return Entity(copy.deepcopy(library.get_monster(name)),
                  float(x), float(y), is_player=player)


def _hero(name, x, y):
    h = {h.name: h for h in hero_list}
    return Entity(copy.deepcopy(h[name]), float(x), float(y), is_player=True)


def _battle(*ents, terrain=None):
    b = BattleSystem(log_callback=lambda s: None,
                     initial_entities=list(ents))
    b.start_combat()
    if terrain:
        b.terrain = list(terrain)
    return b


# ===================================================================== #
# 1. FLY SPEED
# ===================================================================== #
class TestFlySpeed(unittest.TestCase):

    def test_a_flyer_moves_at_its_fly_speed(self):
        for name in ("Adult Red Dragon", "Giant Eagle", "Harpy"):
            with self.subTest(monster=name):
                s = library.get_monster(name)
                e = Entity(copy.deepcopy(s), 0, 0)
                self.assertEqual(e.get_speed(), float(s.speed))
                e.start_flying()
                self.assertEqual(e.get_speed(), float(s.fly_speed))

    def test_a_creature_with_no_walk_speed_can_still_move(self):
        """Virvatuli: kävely 0, lento 50. Liikkumisbudjetti oli nolla."""
        w = _mon("Will-o'-Wisp", 0, 0)
        self.assertEqual(w.get_speed(), 0.0)
        w.start_flying()
        self.assertEqual(w.get_speed(), 50.0)

    def test_taking_off_mid_turn_tops_the_budget_up(self):
        e = _mon("Giant Eagle", 0, 0)
        e.reset_turn()
        self.assertEqual(e.movement_left, 10.0)   # walk speed
        e.start_flying()
        self.assertEqual(e.movement_left, 80.0)   # fly speed

    def test_landing_caps_what_is_left_at_the_walk_speed(self):
        e = _mon("Giant Eagle", 0, 0)
        e.reset_turn()
        e.start_flying()
        e.movement_left = 60.0
        e.land(0)
        self.assertEqual(e.movement_left, 10.0)
        self.assertFalse(e.is_flying)

    def test_the_ai_puts_a_walk_zero_flyer_in_the_air_and_it_closes(self):
        random.seed(2)
        w = _mon("Will-o'-Wisp", 20, 6)
        pc = _hero("Magnus Dragonius", 3, 6)
        b = _battle(w, pc)
        start_dist = b.get_distance(w, pc)
        for _ in range(3):
            w.reset_turn()
            b.ai.calculate_turn(w, b)
        self.assertTrue(w.is_flying)
        self.assertLess(b.get_distance(w, pc), start_dist)


# ===================================================================== #
# 2. COMING BACK DOWN
# ===================================================================== #
class TestDescending(unittest.TestCase):

    def _airborne(self, name, elevation=20, pc_x=None):
        """Flyer hovering directly over a ground target it cannot reach.

        The PC is placed against the flyer's footprint on purpose: a
        creature only drops once it is already above its target, so a
        distant PC is a different test (see the oscillation one below).
        """
        ai = TacticalAI()
        e = _mon(name, 6, 6)
        if pc_x is None:
            pc_x = 6 + e.size_in_squares       # right against its footprint
        pc = _hero("Magnus Dragonius", pc_x, 6)
        b = _battle(e, pc)
        e.start_flying()
        e.elevation = elevation
        e.movement_left = e.get_speed()
        return ai, e, pc, b

    def test_a_short_reach_flyer_drops_to_reach_a_ground_target(self):
        for name in ("Giant Eagle", "Harpy", "Giant Bat"):
            with self.subTest(monster=name):
                ai, e, pc, b = self._airborne(name)
                dropped = ai._consider_descending(e, [pc], b)
                self.assertGreater(dropped, 0)
                self.assertEqual(e.elevation, 0)
                self.assertFalse(e.is_flying)

    def test_a_long_reach_flyer_stays_up_when_it_can_already_bite(self):
        """Lohikäärmeen 10 jalan purenta yltää maahan 10 jalan
        korkeudelta — turha laskeutua."""
        ai = TacticalAI()
        d = _mon("Adult Red Dragon", 6, 6)
        pc = _hero("Magnus Dragonius", 9, 6)
        b = _battle(d, pc)
        d.start_flying()
        d.elevation = 10
        d.movement_left = d.get_speed()
        self.assertEqual(ai._consider_descending(d, [pc], b), 0.0)
        self.assertEqual(d.elevation, 10)

    def test_it_does_not_land_the_moment_it_takes_off(self):
        """Regressio, joka pysäytti kokonaisia taisteluita: laskeutuminen
        kumosi nousun samalla vuorolla, joten kuilun yli lentämään
        lähtenyt olento laskeutui heti takaisin eikä päässyt koskaan
        perille."""
        ai = TacticalAI()
        e = _mon("Giant Eagle", 6, 6)
        far = _hero("Magnus Dragonius", 24, 6)
        b = _battle(e, far)
        e.start_flying()
        e.elevation = 20
        e.movement_left = e.get_speed()
        self.assertEqual(ai._consider_descending(e, [far], b), 0.0)
        self.assertTrue(e.is_flying)
        self.assertEqual(e.elevation, 20)

    def test_it_stays_up_while_an_enemy_is_also_airborne(self):
        ai, e, pc, b = self._airborne("Giant Eagle")
        flyer = _mon("Giant Bat", 14, 6, player=True)
        flyer.start_flying()
        flyer.elevation = 30
        b.entities.append(flyer)
        self.assertEqual(ai._consider_descending(e, [pc, flyer], b), 0.0)

    def test_a_ranged_flyer_keeps_its_height(self):
        ai = TacticalAI()
        arch = _mon("Archmage", 6, 6)
        pc = _hero("Magnus Dragonius", 7, 6)
        b = _battle(arch, pc)
        arch.start_flying()
        arch.elevation = 20
        arch.movement_left = arch.get_speed()
        self.assertEqual(ai._consider_descending(arch, [pc], b), 0.0)

    def test_it_does_not_descend_into_the_lava_it_fled(self):
        ai, e, pc, b = self._airborne("Giant Eagle")
        b.terrain = [TerrainObject("lava", int(e.grid_x), int(e.grid_y))]
        self.assertEqual(ai._consider_descending(e, [pc], b), 0.0)
        self.assertEqual(e.elevation, 20)

    def test_descending_costs_movement(self):
        ai, e, pc, b = self._airborne("Harpy", elevation=20)
        before = e.movement_left
        dropped = ai._consider_descending(e, [pc], b)
        self.assertEqual(dropped, 20.0)
        self.assertLess(e.movement_left, before)


# ===================================================================== #
# 3. COUNTERSPELL
# ===================================================================== #
class TestCounterspell(unittest.TestCase):

    def _pair(self):
        a = _mon("Archmage", 5, 5)
        b_ = _mon("Archmage", 12, 5, player=True)
        return a, b_, _battle(a, b_)

    def test_it_fires_in_the_open(self):
        a, foe, b = self._pair()
        self.assertIn(a, b.check_counterspell_reaction(foe, 3))

    def test_it_does_not_come_through_a_stone_wall(self):
        a, foe, b = self._pair()
        b.terrain = [TerrainObject("wall", 8, y) for y in range(0, 12)]
        self.assertFalse(b.has_line_of_sight(a, foe))
        self.assertEqual(b.check_counterspell_reaction(foe, 3), [])

    def test_a_blinded_mage_cannot_counterspell(self):
        a, foe, b = self._pair()
        a.add_condition("Blinded")
        self.assertEqual(b.check_counterspell_reaction(foe, 3), [])

    def test_range_is_still_sixty_feet(self):
        a, foe, b = self._pair()
        foe.grid_x = 30.0
        self.assertEqual(b.check_counterspell_reaction(foe, 3), [])

    def test_it_needs_a_third_level_slot(self):
        a, foe, b = self._pair()
        a.spell_slots = {}
        self.assertEqual(b.check_counterspell_reaction(foe, 3), [])

    def test_the_decision_spends_slots_on_things_worth_countering(self):
        from data.spells import get_spell
        a, foe, b = self._pair()
        ai = b.ai
        self.assertTrue(ai.should_counterspell(
            a, foe, get_spell("Fireball"), 3, b))

    def test_it_never_counters_an_ally(self):
        from data.spells import get_spell
        a = _mon("Archmage", 5, 5)
        friend = _mon("Archmage", 8, 5)
        b = _battle(a, friend)
        self.assertFalse(b.ai.should_counterspell(
            a, friend, get_spell("Fireball"), 3, b))


# ===================================================================== #
# 4. LEGENDARY ACTIONS — JUDGEMENT, NOT SPAM
# ===================================================================== #
class TestLegendaryJudgement(unittest.TestCase):

    def test_wing_attack_is_centred_on_the_dragon_not_aimed_like_a_fireball(self):
        """aura_radius tarkoittaa 'kaikki X jalan sisällä MINUSTA'."""
        d = library.get_monster("Ancient Red Dragon")
        wing = next(sa for sa in resolve_special_actions(d, "legendary")
                    if sa.name == "Wing Attack")
        self.assertEqual(wing.action.range, 0)
        self.assertEqual(wing.action.aoe_radius, 15)

    def test_tail_attack_borrows_the_real_tail_and_its_reach(self):
        d = library.get_monster("Ancient Red Dragon")
        tail = next(sa for sa in resolve_special_actions(d, "legendary")
                    if sa.name == "Tail Attack")
        real = next(a for a in d.actions if a.name == "Tail")
        self.assertEqual(tail.action.reach, real.reach)
        self.assertLessEqual(tail.action.range, 10)

    def test_the_two_point_wing_attack_is_not_spent_on_one_target(self):
        """Tämä on se mitä arvokynnys oikeasti lupaa: kallis kyky vaatii
        väkijoukon. Halpa 1 pisteen toiminto saa lähteä vapaasti."""
        random.seed(4)
        d = _mon("Ancient Red Dragon", 10, 6)
        pc = _hero("Magnus Dragonius", 9, 7)
        b = _battle(d, pc)
        d.legendary_actions_left = 3
        b.ai._own_turn_is_next = lambda e, bb: False
        for _ in range(3):
            step = b.ai.calculate_legendary_action(d, b)
            if step is None:
                break
            self.assertNotEqual(
                step.action_name, "Wing Attack",
                "a 2-point wing buffet went off on a single target")

    def test_a_cheap_effect_is_still_available_when_nothing_is_in_reach(self):
        """Regressio: kynnys hiljensi olennot joiden koko legendaarinen
        arsenaali on yksi halpa efekti."""
        random.seed(4)
        d = _mon("Ancient Red Dragon", 60, 6)
        pcs = [_hero("Magnus Dragonius", 3, 5), _hero("Beatrice", 3, 8)]
        b = _battle(d, *pcs)
        d.legendary_actions_left = 3
        b.ai._own_turn_is_next = lambda e, bb: False
        step = b.ai.calculate_legendary_action(d, b)
        self.assertIsNotNone(step)
        self.assertEqual(d.legendary_actions_left, 2,
                         "a 1-point ability should cost exactly one point")

    def test_but_it_spends_them_rather_than_waste_them(self):
        """Pisteet palautuvat sen omalla vuorolla, joten säästäminen sen
        yli on pelkkää hukkaa."""
        random.seed(4)
        d = _mon("Ancient Red Dragon", 60, 6)
        pcs = [_hero("Magnus Dragonius", 3, 5), _hero("Beatrice", 3, 8)]
        b = _battle(d, *pcs)
        d.legendary_actions_left = 3
        b.ai._own_turn_is_next = lambda e, bb: True
        self.assertIsNotNone(b.ai.calculate_legendary_action(d, b))
        self.assertLess(d.legendary_actions_left, 3)

    def test_the_value_bar_rises_faster_than_the_cost(self):
        bar = TacticalAI._LEGENDARY_VALUE_BAR
        self.assertGreater(bar[2], bar[1] * 2)
        self.assertGreater(bar[3], bar[1] * 3)

    def test_it_still_attacks_when_the_party_is_on_top_of_it(self):
        random.seed(11)
        d = _mon("Ancient Red Dragon", 10, 6)
        pcs = [_hero("Magnus Dragonius", 8, 6), _hero("Beatrice", 9, 7),
               _hero("Carlo", 8, 8)]
        b = _battle(d, *pcs)
        d.legendary_actions_left = 3
        b.ai._own_turn_is_next = lambda e, bb: False
        step = b.ai.calculate_legendary_action(d, b)
        self.assertIsNotNone(step, "dragon banked its points in melee")
        self.assertEqual(step.step_type, "legendary")

    def test_it_never_spends_more_points_than_it_has(self):
        random.seed(7)
        d = _mon("Ancient Red Dragon", 10, 6)
        pcs = [_hero("Magnus Dragonius", 8, 6), _hero("Beatrice", 9, 7)]
        b = _battle(d, *pcs)
        for start in (1, 2, 3):
            d.legendary_actions_left = start
            spent = 0
            while True:
                s = b.ai.calculate_legendary_action(d, b)
                if s is None:
                    break
                spent += 1
                if spent > 5:
                    self.fail("legendary actions never ran out")
            self.assertGreaterEqual(d.legendary_actions_left, 0)

    def test_the_initiative_helpers_agree_with_the_turn_order(self):
        d = _mon("Ancient Red Dragon", 10, 6)
        pcs = [_hero("Magnus Dragonius", 3, 5), _hero("Beatrice", 3, 8)]
        b = _battle(d, *pcs)
        ai = b.ai
        current = b.get_current_entity()
        upcoming = ai._turn_order_after(b, current)
        self.assertEqual(len(upcoming), 2)
        self.assertNotIn(current, upcoming)
        self.assertTrue(ai._acts_next(upcoming[0], b))
        self.assertFalse(ai._acts_next(upcoming[1], b))

    def test_every_legendary_creature_still_finds_something_to_do(self):
        """Regressio: arvokynnys ei saa hiljentää niitä kokonaan."""
        random.seed(3)
        checked = 0
        for stats in library.get_all_monsters():
            if stats.legendary_action_count <= 0:
                continue
            if not resolve_special_actions(stats, "legendary"):
                continue
            checked += 1
            d = Entity(copy.deepcopy(stats), 10, 6)
            pcs = [_hero("Magnus Dragonius", 8, 6),
                   _hero("Beatrice", 9, 8)]
            b = _battle(d, *pcs)
            d.legendary_actions_left = stats.legendary_action_count
            b.ai._own_turn_is_next = lambda e, bb: True
            step = b.ai.calculate_legendary_action(d, b)
            self.assertIsNotNone(
                step, f"{stats.name} has legendary actions but never uses "
                      f"one even when they are about to be lost")
        self.assertGreater(checked, 10)


if __name__ == "__main__":
    unittest.main()
