"""Suunniteltu siirto toteutuu juuri niin kuin se suunniteltiin.

Kun AI lakkasi liikuttamasta tokeneita suunnitteluvaiheessa, siirto ja
sen sivuvaikutukset — korkeus, otteessa raahattavat, tilaisuushyökkäys —
piti alkaa kulkea askeleen mukana. Kaikki tässä tiedostossa olevat viat
löytyivät ajamalla oikeita taisteluita, eivät koodia lukemalla.
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

from data.models import CreatureStats, AbilityScores, Action
from engine.entities import Entity
from engine.battle import BattleSystem
from engine.terrain import TerrainObject
from engine.ai import ActionStep
from engine.ai.tactical_ai import _drag_snapshot


def _mk(name, x, y, is_player=False, size="Medium", reach=5, hp=40):
    s = CreatureStats(name=name, hit_points=hp, armor_class=13, speed=30,
                      size=size,
                      abilities=AbilityScores(strength=18, dexterity=12),
                      actions=[Action("Claw", "Melee", 6, "1d8", 3,
                                      "slashing", range=reach)])
    return Entity(s, float(x), float(y), is_player=is_player)


def _battle(ents, terrain=None):
    b = BattleSystem(lambda m: None, ents)
    b.terrain = terrain or []
    return b


def _grapple(holder, victim):
    holder.grappling.append(victim)
    victim.grappled_by = holder
    victim.add_condition("Grappled")


# ===================================================================== #
# 1. ALTITUDE TRAVELS WITH THE STEP
# ===================================================================== #
class TestPlannedAltitude(unittest.TestCase):
    """Suunnittelu peruutetaan, joten lentoonlähtö katosi ja siirto
    toteutui maan tasalla — suoraan patsaan sisään."""

    def _statue_map(self):
        st = TerrainObject(terrain_type="statue", grid_x=6, grid_y=3,
                           elevation=10)
        return [st]

    def test_a_move_carries_the_height_it_was_planned_at(self):
        dragon = _mk("Dragon", 2, 3, size="Huge")
        b = _battle([dragon], self._statue_map())
        b.apply_planned_move(dragon, 4, 3, elevation=30.0, flying=True)
        self.assertTrue(dragon.is_flying)
        self.assertEqual(dragon.elevation, 30.0)
        # Footprint covers the statue, but it is thirty feet overhead.
        self.assertTrue(b.is_passable(4, 3, exclude=dragon))

    def test_without_the_height_the_same_move_is_illegal(self):
        dragon = _mk("Dragon", 2, 3, size="Huge")
        b = _battle([dragon], self._statue_map())
        b.apply_planned_move(dragon, 4, 3)
        self.assertFalse(dragon.is_flying)
        self.assertFalse(b.is_passable(4, 3, exclude=dragon))

    def test_a_step_records_the_altitude_the_planner_used(self):
        st = ActionStep("move")
        self.assertIsNone(st.new_elevation)
        self.assertIsNone(st.new_flying)


# ===================================================================== #
# 2. DRAGGING A GRAPPLED CREATURE
# ===================================================================== #
class TestDraggingAGrappledCreature(unittest.TestCase):

    def test_the_plan_says_where_the_victim_lands(self):
        # A fifteen-foot walk leaves the victim trailing one square
        # behind, not dumped back at the origin three squares away.
        pal = _mk("Paladin", 5, 3, is_player=True)
        ogre = _mk("Ogre", 6, 3, size="Large")
        b = _battle([pal, ogre])
        _grapple(pal, ogre)
        b.apply_planned_move(pal, 2, 3, dragged=[(ogre, 3.0, 3.0)])
        self.assertEqual((pal.grid_x, pal.grid_y), (2.0, 3.0))
        self.assertEqual((ogre.grid_x, ogre.grid_y), (3.0, 3.0))
        self.assertTrue(b.is_adjacent(pal, ogre),
                        "raahattu jäi hyökkäysetäisyyden ulkopuolelle")

    def test_an_empty_plan_list_drags_nobody(self):
        # A grapple made LATER in the same turn is already on the
        # creature when the move is approved; it must not be dragged.
        dragon = _mk("Dragon", 8, 3, size="Huge", reach=15)
        weapon = _mk("Spiritual Weapon", 2, 3, is_player=True)
        b = _battle([dragon, weapon])
        _grapple(dragon, weapon)
        b.apply_planned_move(dragon, 5, 3, dragged=[])
        self.assertEqual((weapon.grid_x, weapon.grid_y), (2.0, 3.0),
                         "suunnitelma ei raahannut ketään, mutta joku "
                         "liikkui silti")

    def test_no_plan_list_falls_back_to_the_vacated_square(self):
        holder = _mk("Bugbear", 5, 3)
        victim = _mk("Scout", 6, 3, is_player=True)
        b = _battle([holder, victim])
        _grapple(holder, victim)
        b.apply_planned_move(holder, 4, 3)
        self.assertEqual((victim.grid_x, victim.grid_y), (5.0, 3.0))

    def test_a_long_jump_does_not_leave_the_victim_behind(self):
        # No plan list and a move too long for the vacated square to
        # still be in reach: the victim is placed next to the mover.
        holder = _mk("Bugbear", 5, 3)
        victim = _mk("Scout", 6, 3, is_player=True)
        b = _battle([holder, victim])
        _grapple(holder, victim)
        b.apply_planned_move(holder, 12, 3)
        self.assertTrue(b.is_adjacent(holder, victim) or
                        victim not in holder.grappling)

    def test_a_teleport_ends_the_grapple_and_drags_nobody(self):
        rogue = _mk("Rogue", 5, 3, is_player=True)
        mage = _mk("Archmage", 6, 3)
        b = _battle([rogue, mage])
        _grapple(rogue, mage)
        b.apply_planned_move(rogue, 11, 3, teleport=True)
        self.assertEqual((mage.grid_x, mage.grid_y), (6.0, 3.0))
        self.assertEqual(rogue.grappling, [])
        self.assertFalse(mage.has_condition("Grappled"))
        self.assertIsNone(mage.grappled_by)

    def test_a_hold_that_cannot_reach_breaks_instead_of_yanking(self):
        # The victim teleported away earlier; the next step the holder
        # takes must not pull them back across the map.
        rogue = _mk("Rogue", 5, 3, is_player=True)
        mage = _mk("Archmage", 5, 3)
        b = _battle([rogue, mage])
        _grapple(rogue, mage)
        mage.grid_x, mage.grid_y = 15.0, 12.0      # blinked away
        b.apply_planned_move(rogue, 6, 3)
        self.assertEqual((mage.grid_x, mage.grid_y), (15.0, 12.0))
        self.assertNotIn(mage, rogue.grappling)
        self.assertFalse(mage.has_condition("Grappled"))

    def test_break_all_grapples_works_in_both_directions(self):
        a = _mk("A", 3, 3)
        bb = _mk("B", 4, 3)
        c = _mk("C", 2, 3)
        _grapple(a, bb)      # A holds B
        _grapple(c, a)       # C holds A
        a.break_all_grapples()
        self.assertEqual(a.grappling, [])
        self.assertEqual(c.grappling, [])
        self.assertIsNone(a.grappled_by)
        self.assertIsNone(bb.grappled_by)
        self.assertFalse(a.has_condition("Grappled"))
        self.assertFalse(bb.has_condition("Grappled"))

    def test_the_snapshot_helper_records_positions_not_just_names(self):
        holder = _mk("Bugbear", 5, 3)
        victim = _mk("Scout", 6, 3, is_player=True)
        _grapple(holder, victim)
        snap = _drag_snapshot(holder)
        self.assertEqual(snap, [(victim, 6.0, 3.0)])
        # A corpse is not dragged.
        victim.hp = 0
        self.assertEqual(_drag_snapshot(holder), [])

    def test_the_snapshot_of_an_empty_hold_is_an_empty_list(self):
        # Not None: "dragged nobody" has to be distinguishable from
        # "nobody asked", because the two behave differently.
        lone = _mk("Goblin", 3, 3)
        self.assertEqual(_drag_snapshot(lone), [])


if __name__ == "__main__":
    unittest.main()
