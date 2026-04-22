"""Phase 4e — Aquatic awareness + swim penalty tests."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import unittest

from data.models import CreatureStats, AbilityScores, Action, Feature
from engine.entities import Entity
from engine.battle import BattleSystem
from engine.terrain import TerrainObject


def _make_entity(name="Test", swim_speed=0, features=None, x=5.0, y=5.0):
    stats = CreatureStats(
        name=name, size="Medium", hit_points=30, armor_class=13, speed=30,
        swim_speed=swim_speed,
        abilities=AbilityScores(strength=12, dexterity=12),
        features=features or [],
        actions=[Action(name="Sword", attack_bonus=3, damage_dice="1d6",
                        damage_bonus=2, damage_type="slashing", range=5)],
    )
    return Entity(stats, x, y, is_player=False)


def _make_battle(entities=None):
    log = []
    b = BattleSystem(log_callback=log.append, initial_entities=entities or [])
    return b, log


class TestIsAquatic(unittest.TestCase):
    def test_landlubber_not_aquatic(self):
        e = _make_entity("Knight")
        self.assertFalse(e.is_aquatic)

    def test_swim_speed_is_aquatic(self):
        e = _make_entity("Merfolk", swim_speed=40)
        self.assertTrue(e.is_aquatic)

    def test_amphibious_feature_is_aquatic(self):
        e = _make_entity("Lizardfolk",
                         features=[Feature(name="Amphibious",
                                            mechanic="amphibious")])
        self.assertTrue(e.is_aquatic)

    def test_water_breathing_is_aquatic(self):
        e = _make_entity("Sahuagin",
                         features=[Feature(name="Water Breathing",
                                            mechanic="water_breathing")])
        self.assertTrue(e.is_aquatic)


class TestWaterMovementCost(unittest.TestCase):
    def test_water_costs_double_for_landlubber(self):
        knight = _make_entity("Knight")
        b, _ = _make_battle([knight])
        b.terrain.append(TerrainObject(terrain_type="water", grid_x=5, grid_y=5))
        self.assertEqual(b.get_terrain_movement_cost(5, 5, knight), 2.0)

    def test_deep_water_costs_double_for_landlubber(self):
        knight = _make_entity("Knight")
        b, _ = _make_battle([knight])
        b.terrain.append(TerrainObject(terrain_type="deep_water", grid_x=5, grid_y=5))
        self.assertEqual(b.get_terrain_movement_cost(5, 5, knight), 2.0)

    def test_water_normal_cost_for_swimmer(self):
        fish = _make_entity("Merfolk", swim_speed=40)
        b, _ = _make_battle([fish])
        b.terrain.append(TerrainObject(terrain_type="water", grid_x=5, grid_y=5))
        self.assertEqual(b.get_terrain_movement_cost(5, 5, fish), 1.0)

    def test_deep_water_normal_cost_for_amphibian(self):
        lizard = _make_entity(
            "Lizardfolk",
            features=[Feature(name="Amphibious", mechanic="amphibious")],
        )
        b, _ = _make_battle([lizard])
        b.terrain.append(TerrainObject(terrain_type="deep_water",
                                       grid_x=5, grid_y=5))
        self.assertEqual(b.get_terrain_movement_cost(5, 5, lizard), 1.0)

    def test_flying_bypasses_water(self):
        drake = _make_entity("Drake")
        drake.is_flying = True
        b, _ = _make_battle([drake])
        b.terrain.append(TerrainObject(terrain_type="deep_water",
                                       grid_x=5, grid_y=5))
        self.assertEqual(b.get_terrain_movement_cost(5, 5, drake), 1.0)

    def test_open_ground_is_normal(self):
        knight = _make_entity("Knight")
        b, _ = _make_battle([knight])
        self.assertEqual(b.get_terrain_movement_cost(5, 5, knight), 1.0)

    def test_difficult_terrain_still_costs_double(self):
        """Non-water difficult terrain (mud/ice/rubble) still 2x for everyone."""
        fish = _make_entity("Merfolk", swim_speed=40)
        b, _ = _make_battle([fish])
        b.terrain.append(TerrainObject(terrain_type="mud", grid_x=5, grid_y=5))
        self.assertEqual(b.get_terrain_movement_cost(5, 5, fish), 2.0)


class TestAquaticPathing(unittest.TestCase):
    """Sanity check: non-aquatic creatures pay more to cross water, so
    A* naturally routes around it; aquatic creatures go straight through."""

    def test_swim_speed_path_cheaper_through_water(self):
        knight = _make_entity("Knight")
        fish = _make_entity("Merfolk", swim_speed=40)
        b, _ = _make_battle([knight, fish])
        # Line of water between (3,5) and (7,5)
        for x in range(4, 7):
            b.terrain.append(TerrainObject(terrain_type="water", grid_x=x, grid_y=5))

        knight_cost = sum(
            b.get_terrain_movement_cost(x, 5, knight) for x in range(4, 7)
        )
        fish_cost = sum(
            b.get_terrain_movement_cost(x, 5, fish) for x in range(4, 7)
        )
        self.assertEqual(knight_cost, 6.0)   # 3 tiles * 2.0
        self.assertEqual(fish_cost, 3.0)     # 3 tiles * 1.0


if __name__ == "__main__":
    unittest.main()
