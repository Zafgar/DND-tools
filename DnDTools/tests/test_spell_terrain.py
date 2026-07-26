"""Kentälle jäävät loitsuefektit.

Loitsu joka luo maastoa kantoi aiemmin kentälle vain värin ja
vahinkonopat: pelastusheitto, ehto ja ajoitus katosivat matkalla. Web ei
sitonut ketään, Cloudkill ei antanut CON-savea, Spike Growth pureskeli
paikallaan seisojaa ja kolme loitsua ei luonut mitään koska niiden
maastotyyppiä ei ollut olemassa.

Tämä testi kattaa sekä säännöt että sen, että AI ymmärtää ne.
"""
import sys
import os
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import unittest

import pygame
pygame.init()
pygame.display.set_mode((1920, 1080))

import data.spells as spells_mod
from data.spells import get_spell
from data.library import library
from engine.entities import Entity
from engine.battle import BattleSystem
from engine.ai import TacticalAI
from engine.terrain import TERRAIN_TYPES, TerrainObject


TERRAIN_SPELLS = sorted(n for n, sp in spells_mod._spells.items()
                        if sp.creates_terrain)


def _mage(x=2, y=5, player=False):
    return Entity(library.get_monster("Archmage"), x, y, is_player=player)


def _ogre(x=6, y=5, player=True):
    return Entity(library.get_monster("Ogre"), x, y, is_player=player)


def _battle(*entities):
    b = BattleSystem(log_callback=lambda s: None,
                     initial_entities=list(entities))
    b.start_combat()
    return b


class TestEveryTerrainSpellLands(unittest.TestCase):
    def test_every_terrain_type_referenced_actually_exists(self):
        """Kolme loitsua osoitti maastotyyppiin jota ei ollut, joten ne
        eivät luoneet kentälle mitään."""
        missing = [(n, sp.creates_terrain)
                   for n, sp in spells_mod._spells.items()
                   if sp.creates_terrain
                   and sp.creates_terrain not in TERRAIN_TYPES]
        self.assertEqual(missing, [])

    def test_the_three_previously_broken_spells_now_build_something(self):
        for name in ("Evard's Black Tentacles", "Wall of Force",
                     "Forcecage"):
            c, o = _mage(), _ogre()
            b = _battle(c, o)
            b.spawn_spell_terrain(get_spell(name), c, 6, 5)
            self.assertGreater(len(b.terrain), 0, name)

    def test_every_terrain_spell_creates_tiles(self):
        for name in TERRAIN_SPELLS:
            c, o = _mage(), _ogre()
            b = _battle(c, o)
            b.spawn_spell_terrain(get_spell(name), c, 6, 5)
            self.assertGreater(len(b.terrain), 0, name)

    def test_force_walls_are_impassable(self):
        for name in ("Wall of Force", "Forcecage"):
            c, o = _mage(), _ogre()
            b = _battle(c, o)
            b.spawn_spell_terrain(get_spell(name), c, 6, 5)
            self.assertFalse(b.get_terrain_at(6, 5).passable, name)

    def test_wall_of_force_does_not_block_sight(self):
        """5e: näkymätön este, mutta näkyvyys säilyy."""
        c, o = _mage(), _ogre()
        b = _battle(c, o)
        b.spawn_spell_terrain(get_spell("Wall of Force"), c, 6, 5)
        self.assertFalse(b.get_terrain_at(6, 5).blocks_los)


class TestRulesCarryOntoTheTiles(unittest.TestCase):
    def _spawn(self, name, cx=6, cy=5):
        c, o = _mage(), _ogre(cx, cy)
        b = _battle(c, o)
        b.spawn_spell_terrain(get_spell(name), c, cx, cy)
        return b, c, o, b.get_terrain_at(cx, cy)

    def test_save_dc_comes_from_the_caster(self):
        _b, c, _o, t = self._spawn("Cloudkill")
        self.assertEqual(t.save_dc, c.stats.spell_save_dc)
        self.assertEqual(t.save_ability, "Constitution")

    def test_condition_is_carried(self):
        for name, cond, ability in (("Web", "Restrained", "Dexterity"),
                                    ("Entangle", "Restrained", "Strength"),
                                    ("Sleet Storm", "Prone", "Dexterity"),
                                    ("Stinking Cloud", "Poisoned",
                                     "Constitution")):
            _b, _c, _o, t = self._spawn(name)
            self.assertEqual(t.applies_condition, cond, name)
            self.assertEqual(t.save_ability, ability, name)

    def test_trigger_timing_matches_the_spell(self):
        cases = {
            "Cloudkill": "turn_start",
            "Stinking Cloud": "turn_start",
            "Spirit Guardians": "turn_start",
            "Spike Growth": "per_5ft",
            "Wall of Thorns": "per_5ft",
            "Wall of Fire": "per_5ft",
            "Web": "enter",
            "Entangle": "enter",
            "Evard's Black Tentacles": "enter",
        }
        for name, trigger in cases.items():
            _b, _c, _o, t = self._spawn(name)
            self.assertEqual(t.trigger, trigger, name)

    def test_spirit_guardians_spares_its_own_caster(self):
        _b, c, _o, t = self._spawn("Spirit Guardians")
        self.assertIn(c.name, t.exempt)

    def test_rules_survive_serialisation(self):
        _b, _c, _o, t = self._spawn("Web")
        again = TerrainObject.from_dict(t.to_dict())
        self.assertEqual(again.save_dc, t.save_dc)
        self.assertEqual(again.save_ability, t.save_ability)
        self.assertEqual(again.applies_condition, t.applies_condition)
        self.assertEqual(again.trigger, t.trigger)


class TestTerrainActuallyBites(unittest.TestCase):
    def test_cloudkill_allows_a_constitution_save(self):
        """Vahinko meni ennen läpi täysimääräisenä ilman heittoa."""
        random.seed(3)
        c, o = _mage(), _ogre(6, 5)
        b = _battle(c, o)
        b.spawn_spell_terrain(get_spell("Cloudkill"), c, 6, 5)
        t = b.get_terrain_at(6, 5)
        self.assertGreater(t.save_dc, 0)
        hp = o.hp
        b._check_hazard_damage(o)
        self.assertLess(o.hp, hp)

    def test_a_successful_save_halves_the_damage(self):
        """Yksittäinen 5d8 heitto vaihtelee liikaa, joten verrataan
        keskiarvoja kymmenestä heitosta."""
        random.seed(11)
        c, o = _mage(), _ogre(6, 5)
        b = _battle(c, o)
        b.spawn_spell_terrain(get_spell("Cloudkill"), c, 6, 5)
        t = b.get_terrain_at(6, 5)

        def _mean(dc):
            t.save_dc = dc
            total = 0
            for _ in range(10):
                o.hp = o.max_hp
                b.apply_terrain_effect(o, t)
                total += o.max_hp - o.hp
            return total / 10.0

        saved = _mean(1)      # cannot fail
        failed = _mean(99)    # cannot succeed
        self.assertLess(saved, failed)
        self.assertAlmostEqual(saved, failed / 2.0, delta=failed * 0.25)

    def test_web_restrains_on_entry(self):
        random.seed(5)
        c, o = _mage(), _ogre(6, 5)
        b = _battle(c, o)
        b.spawn_spell_terrain(get_spell("Web"), c, 6, 5)
        t = b.get_terrain_at(6, 5)
        t.save_dc = 99
        b.apply_movement_terrain(o, 6, 5, entering=True)
        self.assertTrue(o.has_condition("Restrained"))

    def test_a_creature_immune_to_the_condition_shrugs_it_off(self):
        c, o = _mage(), _ogre(6, 5)
        o.stats.condition_immunities = ["Restrained"]
        b = _battle(c, o)
        b.spawn_spell_terrain(get_spell("Web"), c, 6, 5)
        t = b.get_terrain_at(6, 5)
        t.save_dc = 99
        b.apply_movement_terrain(o, 6, 5, entering=True)
        self.assertFalse(o.has_condition("Restrained"))

    def test_spike_growth_bites_per_step_not_per_turn(self):
        random.seed(7)
        c, o = _mage(), _ogre(12, 5)
        b = _battle(c, o)
        b.spawn_spell_terrain(get_spell("Spike Growth"), c, 7, 5)
        hp = o.hp
        for x in (10, 9, 8, 7, 6):
            o.grid_x = x
            b.apply_movement_terrain(o, x, 5, entering=True)
        walked = hp - o.hp
        self.assertGreater(walked, 0)
        # …and standing still costs nothing
        still = o.hp
        b._check_hazard_damage(o)
        self.assertEqual(o.hp, still)

    def test_a_cloud_does_bite_every_turn_you_stand_in_it(self):
        random.seed(9)
        c, o = _mage(), _ogre(6, 5)
        b = _battle(c, o)
        b.spawn_spell_terrain(get_spell("Cloudkill"), c, 6, 5)
        hp = o.hp
        b._check_hazard_damage(o)
        self.assertLess(o.hp, hp)

    def test_spirit_guardians_never_hurts_its_caster(self):
        c, o = _mage(2, 5), _ogre(2, 5)
        b = _battle(c, o)
        b.spawn_spell_terrain(get_spell("Spirit Guardians"), c, 2, 5)
        hp = c.hp
        b._check_hazard_damage(c)
        self.assertEqual(c.hp, hp)

    def test_a_flying_creature_clears_ground_hazards(self):
        c, o = _mage(), _ogre(6, 5)
        o.is_flying = True
        b = _battle(c, o)
        b.spawn_spell_terrain(get_spell("Spike Growth"), c, 6, 5)
        hp = o.hp
        b._check_hazard_damage(o)
        b.apply_movement_terrain(o, 6, 5, entering=True)
        self.assertEqual(o.hp, hp)

    def test_every_terrain_spell_does_something_measurable(self):
        """Yksikään maastoloitsu ei saa olla pelkkä väri kentällä."""
        inert = []
        for name in TERRAIN_SPELLS:
            random.seed(4)
            c, o = _mage(), _ogre(6, 5)
            b = _battle(c, o)
            b.spawn_spell_terrain(get_spell(name), c, 6, 5)
            t = b.get_terrain_at(6, 5)
            hp = o.hp
            t.save_dc = 99                 # force the failure case
            b.apply_terrain_effect(o, t)
            b.apply_movement_terrain(o, 6, 5, entering=True)
            did_something = (
                o.hp < hp or bool(o.conditions) or not t.passable
                or t.blocks_los or t.is_difficult
                or t.terrain_type in ("silence", "wall_wind"))
            if not did_something:
                inert.append(name)
            o.conditions.clear()
        self.assertEqual(inert, [])


class TestSilence(unittest.TestCase):
    def test_standing_in_silence_gags_a_caster(self):
        c, o = _mage(5, 5), _ogre(9, 5)
        b = _battle(c, o)
        b.spawn_spell_terrain(get_spell("Silence"), o, 5, 5)
        self.assertTrue(b.is_silenced(c))
        self.assertFalse(b.can_cast_here(c))

    def test_outside_the_zone_casting_is_fine(self):
        c, o = _mage(5, 5), _ogre(9, 5)
        b = _battle(c, o)
        b.spawn_spell_terrain(get_spell("Silence"), o, 20, 20)
        self.assertFalse(b.is_silenced(c))
        self.assertTrue(b.can_cast_here(c))

    def test_a_spell_with_no_verbal_component_still_works(self):
        c, o = _mage(5, 5), _ogre(9, 5)
        b = _battle(c, o)
        b.spawn_spell_terrain(get_spell("Silence"), o, 5, 5)

        class _Somatic:
            components = "S,M"
        self.assertTrue(b.can_cast_here(c, _Somatic()))

    def test_a_silenced_ai_caster_casts_nothing(self):
        random.seed(7)
        c, o = _mage(5, 5), _ogre(9, 5)
        b = _battle(c, o)
        b.spawn_spell_terrain(get_spell("Silence"), o, 5, 5)
        c.reset_turn()
        c.stats.speed = 0
        c.movement_left = 0
        plan = TacticalAI().calculate_turn(c, b)
        self.assertFalse(any(s.spell for s in plan.steps),
                         "cast a spell while silenced")

    def test_a_mobile_caster_walks_out_of_the_zone(self):
        random.seed(7)
        c = _mage(5, 5)
        o = _ogre(14, 5)
        b = _battle(c, o)
        b.spawn_spell_terrain(get_spell("Silence"), c, 5, 5)
        c.reset_turn()
        TacticalAI().calculate_turn(c, b)
        self.assertFalse(b.is_silenced(c))


class TestWindWall(unittest.TestCase):
    def test_it_stops_arrows_but_not_spells(self):
        a, d = _ogre(2, 5, player=False), _ogre(10, 5, player=True)
        b = _battle(a, d)
        ai = TacticalAI()
        self.assertFalse(b.wind_wall_between(a, d))
        b.spawn_spell_terrain(get_spell("Wind Wall"), a, 6, 5)
        self.assertTrue(b.wind_wall_between(a, d))
        self.assertFalse(ai._can_ranged_attack(a, d, b, 120, is_weapon=True))
        self.assertTrue(ai._can_ranged_attack(a, d, b, 120))

    def test_it_does_not_block_sight(self):
        a, d = _ogre(2, 5, player=False), _ogre(10, 5, player=True)
        b = _battle(a, d)
        b.spawn_spell_terrain(get_spell("Wind Wall"), a, 6, 5)
        self.assertTrue(b.has_line_of_sight(a, d))

    def test_a_wall_off_to_the_side_does_not_count(self):
        a, d = _ogre(2, 5, player=False), _ogre(10, 5, player=True)
        b = _battle(a, d)
        b.spawn_spell_terrain(get_spell("Wind Wall"), a, 6, 25)
        self.assertFalse(b.wind_wall_between(a, d))


class TestAiUnderstandsTerrain(unittest.TestCase):
    def test_terrain_spell_spends_exactly_one_slot(self):
        """Regressio: pisteytyssilmukka kulutti slotin joka ehdokkaalle."""
        import copy
        from data.models import CreatureStats, AbilityScores
        stats = CreatureStats(
            name="Terrain Mage", hit_points=80, armor_class=15, speed=30,
            abilities=AbilityScores(intelligence=18, dexterity=14,
                                    constitution=14),
            spellcasting_ability="Intelligence", spell_save_dc=15,
            spell_attack_bonus=7,
            spell_slots={"1st": 4, "2nd": 3, "3rd": 3},
            spell_names=["Darkness", "Fog Cloud", "Silence"])
        e = Entity(copy.deepcopy(stats), 2, 5, is_player=False)
        foes = [Entity(library.get_monster("Archmage"), 8, 5 + i,
                       is_player=True) for i in range(2)]
        b = _battle(e, *foes)
        before = dict(e.spell_slots)
        e.reset_turn()
        result = TacticalAI()._try_terrain_spell(e, foes, [], b)
        self.assertIsNotNone(result)
        spent = sum(before[k] - e.spell_slots[k] for k in before)
        self.assertEqual(spent, 1)
        self.assertIsNotNone(e.concentrating_on)

    def test_a_hazard_zone_is_crossable_not_a_wall(self):
        """Spike Growth on vaikeaa maastoa, ei muuri — muuten ryhmä
        lukitsee AI:n ulos taistelusta yhdellä 2. tason loitsulla."""
        ai = TacticalAI()
        c, o = _mage(), _ogre(12, 5)
        b = _battle(c, o)
        b.spawn_spell_terrain(get_spell("Spike Growth"), c, 7, 5)
        self.assertTrue(ai._is_safe_passable(b, 7, 5, o))

    def test_a_permanent_hazard_is_still_refused(self):
        ai = TacticalAI()
        c, o = _mage(), _ogre(12, 5)
        b = _battle(c, o)
        b.add_terrain(TerrainObject("lava", 7, 5))
        self.assertFalse(ai._is_safe_passable(b, 7, 5, o))

    def test_a_zone_that_would_kill_it_is_refused(self):
        ai = TacticalAI()
        c, o = _mage(), _ogre(12, 5)
        o.hp = 3
        b = _battle(c, o)
        b.spawn_spell_terrain(get_spell("Cloudkill"), c, 7, 5)
        self.assertFalse(ai._is_safe_passable(b, 7, 5, o))

    def test_the_ai_walks_around_a_hazard_when_it_can(self):
        random.seed(2)
        c, o = _mage(), _ogre(12, 5)
        b = _battle(c, o)
        b.spawn_spell_terrain(get_spell("Spike Growth"), c, 7, 5)
        hp = o.hp
        o.reset_turn()
        TacticalAI().calculate_turn(o, b)
        landed = b.get_terrain_at(int(o.grid_x), int(o.grid_y))
        self.assertNotEqual(
            getattr(landed, "terrain_type", ""), "spike_growth",
            "ended its move standing in the spikes")
        self.assertEqual(o.hp, hp)

    def test_hazard_cost_reflects_the_danger(self):
        ai = TacticalAI()
        c, o = _mage(), _ogre()
        b = _battle(c, o)
        b.spawn_spell_terrain(get_spell("Cloudkill"), c, 6, 5)
        deadly = ai._terrain_hazard_cost(b.get_terrain_at(6, 5), o)
        b.terrain = []
        b.spawn_spell_terrain(get_spell("Spike Growth"), c, 6, 5)
        mild = ai._terrain_hazard_cost(b.get_terrain_at(6, 5), o)
        self.assertGreater(deadly, mild)

    def test_the_caster_is_not_scared_of_its_own_spirit_guardians(self):
        ai = TacticalAI()
        c = _mage(2, 5)
        o = _ogre(8, 5)
        b = _battle(c, o)
        b.spawn_spell_terrain(get_spell("Spirit Guardians"), c, 2, 5)
        t = b.get_terrain_at(2, 5)
        self.assertEqual(ai._terrain_hazard_cost(t, c), 0.0)
        self.assertGreater(ai._terrain_hazard_cost(t, o), 0.0)

    def test_standing_in_a_cloud_scores_worse_than_clean_ground(self):
        ai = TacticalAI()
        c = _mage(8, 5)
        o = _ogre(14, 5)
        b = _battle(c, o)
        b.spawn_spell_terrain(get_spell("Cloudkill"), o, 8, 5)
        inside = ai._get_terrain_advantage_score(c, b, 8, 5)
        clean = ai._get_terrain_advantage_score(c, b, 2, 5)
        self.assertLess(inside, clean)


class TestAutoBattleWithTerrain(unittest.TestCase):
    def test_a_fight_full_of_zones_still_resolves(self):
        from states.battle_state import BattleState

        class _FM:
            def __init__(self):
                self.screen = pygame.display.get_surface()
                self.running = True
                self.states = {}

            def change_state(self, *a, **k):
                pass

        random.seed(17)
        pcs = [Entity(library.get_monster("Archmage"), 3, 3 + i,
                      is_player=True) for i in range(2)]
        foes = [Entity(library.get_monster("Ogre"), 12, 4 + i * 2,
                       is_player=False) for i in range(3)]
        bs = BattleState(_FM(), entities=pcs + foes)
        caster = pcs[0]
        for name, cx, cy in (("Spike Growth", 7, 4),
                             ("Web", 8, 8),
                             ("Cloudkill", 10, 6),
                             ("Wall of Fire", 6, 10)):
            bs.battle.spawn_spell_terrain(get_spell(name), caster, cx, cy)
        bs._set_ai_mode("full_auto")
        for _ in range(3000):
            bs._process_auto_battle()
            if not bs.auto_battle:
                break
            if (not [e for e in bs.battle.entities
                     if e.is_player and e.hp > 0]
                    or not [e for e in bs.battle.entities
                            if not e.is_player and e.hp > 0]):
                break
        else:
            self.fail("auto-battle never finished with terrain on the field")


if __name__ == "__main__":
    unittest.main()
