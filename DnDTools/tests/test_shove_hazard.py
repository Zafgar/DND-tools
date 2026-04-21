"""Phase 4a — Shove-to-hazard & push-off-cliff tests.

Covers:
  * BattleSystem.push_entity — straight-line push, stops at walls/occupied,
    pushes into gaps (fall damage), pushes into lava (hazard damage),
    pushes off a platform edge (fall damage).
  * TacticalAI._score_shove_to_hazard — AI scoring of destination tiles.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import unittest
import random

from data.models import CreatureStats, AbilityScores, Action
from engine.entities import Entity
from engine.battle import BattleSystem
from engine.terrain import TerrainObject
from engine.ai.tactical_ai import TacticalAI


def _make_entity(name="Test", is_player=True, hp=50, ac=15, x=5.0, y=5.0,
                 strength=14, dexterity=10, speed=30, size="Medium"):
    stats = CreatureStats(
        name=name, size=size, hit_points=hp, armor_class=ac, speed=speed,
        abilities=AbilityScores(strength=strength, dexterity=dexterity),
        actions=[Action(name="Sword", attack_bonus=5, damage_dice="1d8",
                        damage_bonus=3, damage_type="slashing", range=5)],
    )
    return Entity(stats, x, y, is_player=is_player)


def _make_battle(entities=None):
    log = []
    b = BattleSystem(log_callback=log.append, initial_entities=entities or [])
    return b, log


class TestPushEntityBasic(unittest.TestCase):
    def test_push_east_5ft_one_square(self):
        target = _make_entity("Goblin", is_player=False, x=5, y=5)
        battle, _ = _make_battle([target])
        info = battle.push_entity(target, from_x=4.0, from_y=5.0, distance=5)
        self.assertEqual(info["moved_cells"], 1)
        self.assertEqual(int(target.grid_x), 6)
        self.assertEqual(int(target.grid_y), 5)

    def test_push_zero_distance_noop(self):
        target = _make_entity("Goblin", is_player=False, x=5, y=5)
        battle, _ = _make_battle([target])
        info = battle.push_entity(target, from_x=4.0, from_y=5.0, distance=0)
        self.assertEqual(info["moved_cells"], 0)

    def test_push_dead_target_noop(self):
        target = _make_entity("Goblin", is_player=False, x=5, y=5)
        target.hp = 0
        battle, _ = _make_battle([target])
        info = battle.push_entity(target, from_x=4.0, from_y=5.0, distance=5)
        self.assertEqual(info["moved_cells"], 0)

    def test_push_zero_relative_position(self):
        # pusher standing on same cell — no direction; push should no-op
        target = _make_entity("Goblin", is_player=False, x=5, y=5)
        battle, _ = _make_battle([target])
        info = battle.push_entity(target, from_x=5.0, from_y=5.0, distance=5)
        self.assertEqual(info["moved_cells"], 0)

    def test_push_south(self):
        target = _make_entity("Goblin", is_player=False, x=5, y=5)
        battle, _ = _make_battle([target])
        info = battle.push_entity(target, from_x=5.0, from_y=4.0, distance=5)
        self.assertEqual(int(target.grid_y), 6)
        self.assertEqual(int(target.grid_x), 5)


class TestPushEntityBlocked(unittest.TestCase):
    def test_stops_at_wall(self):
        target = _make_entity("Goblin", is_player=False, x=5, y=5)
        battle, _ = _make_battle([target])
        battle.terrain.append(TerrainObject(terrain_type="wall", grid_x=6, grid_y=5))
        start_x = target.grid_x
        info = battle.push_entity(target, from_x=4.0, from_y=5.0, distance=5)
        self.assertEqual(info["moved_cells"], 0)
        self.assertEqual(target.grid_x, start_x)

    def test_stops_at_occupied(self):
        target = _make_entity("Goblin", is_player=False, x=5, y=5)
        blocker = _make_entity("Orc", is_player=False, x=6, y=5)
        battle, _ = _make_battle([target, blocker])
        info = battle.push_entity(target, from_x=4.0, from_y=5.0, distance=5)
        self.assertEqual(info["moved_cells"], 0)
        self.assertEqual(int(target.grid_x), 5)


class TestPushEntityHazards(unittest.TestCase):
    def test_push_into_chasm_falls(self):
        target = _make_entity("Goblin", is_player=False, x=5, y=5, hp=50)
        battle, _ = _make_battle([target])
        battle.terrain.append(TerrainObject(terrain_type="chasm_20", grid_x=6, grid_y=5))
        random.seed(42)
        info = battle.push_entity(target, from_x=4.0, from_y=5.0, distance=5)
        self.assertTrue(info["fell_into_gap"])
        self.assertEqual(info["moved_cells"], 1)
        # Pushed into the gap
        self.assertEqual(info["final_cell"], (6, 5))

    def test_push_into_lava_takes_damage(self):
        target = _make_entity("Goblin", is_player=False, x=5, y=5, hp=100)
        battle, _ = _make_battle([target])
        battle.terrain.append(TerrainObject(terrain_type="lava", grid_x=6, grid_y=5))
        before = target.hp
        random.seed(7)
        info = battle.push_entity(target, from_x=4.0, from_y=5.0, distance=5)
        self.assertEqual(info["moved_cells"], 1)
        # Lava is 10d10 fire - should always deal damage
        self.assertGreater(info["hazard_damage"], 0)
        self.assertLess(target.hp, before)
        self.assertEqual(info["destination_type"], "lava")

    def test_push_into_spikes(self):
        target = _make_entity("Goblin", is_player=False, x=5, y=5, hp=50)
        battle, _ = _make_battle([target])
        battle.terrain.append(TerrainObject(terrain_type="spikes", grid_x=6, grid_y=5))
        random.seed(11)
        info = battle.push_entity(target, from_x=4.0, from_y=5.0, distance=5)
        self.assertEqual(info["moved_cells"], 1)
        self.assertGreater(info["hazard_damage"], 0)

    def test_push_off_platform_fall(self):
        target = _make_entity("Goblin", is_player=False, x=5, y=5, hp=50)
        target.elevation = 20
        battle, _ = _make_battle([target])
        # target stands on platform_20 at (5,5); ground at (6,5) is elev 0
        battle.terrain.append(TerrainObject(terrain_type="platform_20",
                                            grid_x=5, grid_y=5))
        random.seed(3)
        info = battle.push_entity(target, from_x=4.0, from_y=5.0, distance=5)
        self.assertEqual(info["moved_cells"], 1)
        self.assertGreaterEqual(info["fell_from"], 10)


class TestPushEntityDirection(unittest.TestCase):
    def test_diagonal_push_picks_dominant_axis_x(self):
        target = _make_entity("Goblin", is_player=False, x=5, y=5)
        battle, _ = _make_battle([target])
        # pusher much further west than north
        info = battle.push_entity(target, from_x=0.0, from_y=4.5, distance=5)
        self.assertEqual(info["moved_cells"], 1)
        # Should snap to east (x) since dx >> dy
        self.assertEqual(int(target.grid_x), 6)
        self.assertEqual(int(target.grid_y), 5)

    def test_diagonal_push_picks_dominant_axis_y(self):
        target = _make_entity("Goblin", is_player=False, x=5, y=5)
        battle, _ = _make_battle([target])
        info = battle.push_entity(target, from_x=4.5, from_y=0.0, distance=5)
        self.assertEqual(info["moved_cells"], 1)
        # Should snap to south
        self.assertEqual(int(target.grid_y), 6)


class TestScoreShoveToHazard(unittest.TestCase):
    def _setup(self, attacker_x=4, attacker_y=5, target_x=5, target_y=5):
        att = _make_entity("Att", is_player=True, x=attacker_x, y=attacker_y)
        tgt = _make_entity("Tgt", is_player=False, x=target_x, y=target_y)
        battle, _ = _make_battle([att, tgt])
        return att, tgt, battle

    def test_zero_for_plain_ground(self):
        att, tgt, battle = self._setup()
        score = TacticalAI()._score_shove_to_hazard(att, tgt, battle)
        self.assertEqual(score, 0.0)

    def test_high_for_chasm(self):
        att, tgt, battle = self._setup()
        battle.terrain.append(TerrainObject(terrain_type="chasm_20",
                                            grid_x=6, grid_y=5))
        score = TacticalAI()._score_shove_to_hazard(att, tgt, battle)
        self.assertGreater(score, 20)  # chasm base bonus + fall damage

    def test_very_high_for_lava_chasm(self):
        att, tgt, battle = self._setup()
        battle.terrain.append(TerrainObject(terrain_type="lava_chasm",
                                            grid_x=6, grid_y=5))
        score = TacticalAI()._score_shove_to_hazard(att, tgt, battle)
        # lava_chasm has 10d10 hazard damage = avg 55
        self.assertGreater(score, 50)

    def test_zero_when_target_flying_over_chasm(self):
        att, tgt, battle = self._setup()
        tgt.is_flying = True
        tgt.elevation = 20
        battle.terrain.append(TerrainObject(terrain_type="chasm_20",
                                            grid_x=6, grid_y=5))
        score = TacticalAI()._score_shove_to_hazard(att, tgt, battle)
        # Flying over chasm: no fall, no flat bonus, but lava_chasm has
        # hazard damage. chasm_20 is NOT a hazard, so score should be 0.
        self.assertEqual(score, 0.0)

    def test_score_for_lava_ground(self):
        att, tgt, battle = self._setup()
        battle.terrain.append(TerrainObject(terrain_type="lava",
                                            grid_x=6, grid_y=5))
        score = TacticalAI()._score_shove_to_hazard(att, tgt, battle)
        # lava is 10d10 fire = avg 55, and lava gets 1.5x multiplier
        self.assertGreater(score, 50)

    def test_zero_for_occupied_destination(self):
        att, tgt, battle = self._setup()
        blocker = _make_entity("Block", is_player=False, x=6, y=5)
        battle.entities.append(blocker)
        battle.terrain.append(TerrainObject(terrain_type="lava",
                                            grid_x=6, grid_y=5))
        score = TacticalAI()._score_shove_to_hazard(att, tgt, battle)
        self.assertEqual(score, 0.0)

    def test_zero_for_wall_destination(self):
        att, tgt, battle = self._setup()
        battle.terrain.append(TerrainObject(terrain_type="wall",
                                            grid_x=6, grid_y=5))
        score = TacticalAI()._score_shove_to_hazard(att, tgt, battle)
        self.assertEqual(score, 0.0)

    def test_score_for_platform_edge(self):
        att, tgt, battle = self._setup()
        # target stands on platform_20 at (5,5), pushed east to (6,5) = ground
        battle.terrain.append(TerrainObject(terrain_type="platform_20",
                                            grid_x=5, grid_y=5))
        tgt.elevation = 20
        score = TacticalAI()._score_shove_to_hazard(att, tgt, battle)
        # 20ft drop = 2d6 ≈ 7 avg
        self.assertGreater(score, 5)


if __name__ == "__main__":
    unittest.main()
