"""Tests for engine/battle.py – BattleSystem combat mechanics."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import unittest
import random
import tempfile
import json
from data.models import CreatureStats, AbilityScores, Action, Feature, SpellInfo
from engine.entities import Entity
from engine.battle import BattleSystem
from engine.terrain import TerrainObject


def _make_entity(name="Test", is_player=True, hp=50, ac=15, x=5.0, y=5.0,
                 strength=10, dexterity=10, speed=30, size="Medium",
                 features=None, actions=None, **kwargs):
    stats = CreatureStats(
        name=name, size=size, hit_points=hp, armor_class=ac, speed=speed,
        abilities=AbilityScores(strength=strength, dexterity=dexterity),
        features=features or [],
        actions=actions or [Action(name="Sword", attack_bonus=5, damage_dice="1d8",
                                   damage_bonus=3, damage_type="slashing", range=5)],
        **kwargs,
    )
    return Entity(stats, x, y, is_player=is_player)


def _make_battle(entities=None, log_lines=None):
    if log_lines is None:
        log_lines = []
    battle = BattleSystem(log_callback=log_lines.append, initial_entities=entities or [])
    return battle, log_lines


class TestBattleCreation(unittest.TestCase):
    def test_create_empty_battle(self):
        battle, _ = _make_battle()
        self.assertFalse(battle.combat_started)
        self.assertEqual(battle.round, 1)

    def test_create_with_entities(self):
        hero = _make_entity("Hero", is_player=True, x=1, y=1)
        goblin = _make_entity("Goblin", is_player=False, x=5, y=5)
        battle, _ = _make_battle([hero, goblin])
        self.assertEqual(len(battle.entities), 2)


class TestDistance(unittest.TestCase):
    def test_same_position(self):
        e1 = _make_entity("A", x=5, y=5)
        e2 = _make_entity("B", x=5, y=5)
        battle, _ = _make_battle([e1, e2])
        self.assertAlmostEqual(battle.get_distance(e1, e2), 0.0)

    def test_horizontal_distance(self):
        e1 = _make_entity("A", x=0, y=0)
        e2 = _make_entity("B", x=5, y=0)
        battle, _ = _make_battle([e1, e2])
        dist = battle.get_distance(e1, e2)
        # Distance accounts for size (1 square), so 5 - 1 = 4 squares apart
        self.assertGreater(dist, 0)

    def test_diagonal_distance(self):
        e1 = _make_entity("A", x=0, y=0)
        e2 = _make_entity("B", x=3, y=4)
        battle, _ = _make_battle([e1, e2])
        dist = battle.get_distance(e1, e2)
        self.assertGreater(dist, 0)

    def test_elevation_affects_distance(self):
        e1 = _make_entity("A", x=0, y=0)
        e2 = _make_entity("B", x=0, y=0)
        battle, _ = _make_battle([e1, e2])
        e1.elevation = 0
        e2.elevation = 50
        dist = battle.get_distance(e1, e2)
        self.assertGreater(dist, 0)


class TestAdjacency(unittest.TestCase):
    def test_same_tile_adjacent(self):
        e1 = _make_entity("A", x=5, y=5)
        e2 = _make_entity("B", x=5, y=5)
        battle, _ = _make_battle([e1, e2])
        self.assertTrue(battle.is_adjacent(e1, e2))

    def test_far_apart_not_adjacent(self):
        e1 = _make_entity("A", x=0, y=0)
        e2 = _make_entity("B", x=10, y=10)
        battle, _ = _make_battle([e1, e2])
        self.assertFalse(battle.is_adjacent(e1, e2))


class TestOccupied(unittest.TestCase):
    def test_occupied_position(self):
        e = _make_entity("A", x=5, y=5)
        battle, _ = _make_battle([e])
        self.assertTrue(battle.is_occupied(5, 5))

    def test_unoccupied_position(self):
        e = _make_entity("A", x=5, y=5)
        battle, _ = _make_battle([e])
        self.assertFalse(battle.is_occupied(10, 10))

    def test_exclude_entity(self):
        e = _make_entity("A", x=5, y=5)
        battle, _ = _make_battle([e])
        self.assertFalse(battle.is_occupied(5, 5, exclude=e))

    def test_dead_entity_not_blocking(self):
        e = _make_entity("A", x=5, y=5)
        e.hp = 0
        battle, _ = _make_battle([e])
        self.assertFalse(battle.is_occupied(5, 5))


class TestTerrain(unittest.TestCase):
    def test_add_and_get_terrain(self):
        battle, _ = _make_battle()
        wall = TerrainObject(terrain_type="wall", grid_x=3, grid_y=3)
        battle.add_terrain(wall)
        found = battle.get_terrain_at(3, 3)
        self.assertIsNotNone(found)
        self.assertEqual(found.terrain_type, "wall")

    def test_remove_terrain(self):
        battle, _ = _make_battle()
        wall = TerrainObject(terrain_type="wall", grid_x=3, grid_y=3)
        battle.add_terrain(wall)
        battle.remove_terrain_at(3, 3)
        self.assertIsNone(battle.get_terrain_at(3, 3))

    def test_terrain_blocks_passability(self):
        e = _make_entity("A", x=0, y=0)
        battle, _ = _make_battle([e])
        wall = TerrainObject(terrain_type="wall", grid_x=3, grid_y=3)
        battle.add_terrain(wall)
        self.assertFalse(battle.is_passable(3, 3, exclude=e))

    def test_difficult_terrain_passable(self):
        e = _make_entity("A", x=0, y=0)
        battle, _ = _make_battle([e])
        diff = TerrainObject(terrain_type="difficult", grid_x=3, grid_y=3)
        battle.add_terrain(diff)
        self.assertTrue(battle.is_passable(3, 3, exclude=e))

    def test_movement_cost_difficult(self):
        e = _make_entity("A", x=0, y=0)
        battle, _ = _make_battle([e])
        diff = TerrainObject(terrain_type="difficult", grid_x=3, grid_y=3)
        battle.add_terrain(diff)
        cost = battle.get_terrain_movement_cost(3, 3, entity=e)
        self.assertEqual(cost, 2.0)

    def test_movement_cost_normal(self):
        e = _make_entity("A", x=0, y=0)
        battle, _ = _make_battle([e])
        cost = battle.get_terrain_movement_cost(3, 3, entity=e)
        self.assertEqual(cost, 1.0)

    def test_flying_ignores_difficult_terrain(self):
        e = _make_entity("A", x=0, y=0, fly_speed=60)
        e.start_flying()
        battle, _ = _make_battle([e])
        diff = TerrainObject(terrain_type="difficult", grid_x=3, grid_y=3)
        battle.add_terrain(diff)
        cost = battle.get_terrain_movement_cost(3, 3, entity=e)
        self.assertEqual(cost, 1.0)


class TestLineOfSight(unittest.TestCase):
    def test_clear_los(self):
        e1 = _make_entity("A", x=0, y=0)
        e2 = _make_entity("B", x=5, y=5)
        battle, _ = _make_battle([e1, e2])
        self.assertTrue(battle.has_line_of_sight(e1, e2))

    def test_wall_blocks_los(self):
        e1 = _make_entity("A", x=0, y=5)
        e2 = _make_entity("B", x=10, y=5)
        battle, _ = _make_battle([e1, e2])
        # Place walls between them
        for x in range(3, 8):
            wall = TerrainObject(terrain_type="wall", grid_x=x, grid_y=5)
            battle.add_terrain(wall)
        self.assertFalse(battle.has_line_of_sight(e1, e2))


class TestCombatFlow(unittest.TestCase):
    def test_start_combat(self):
        random.seed(42)
        hero = _make_entity("Hero", is_player=True, x=1, y=1, dexterity=14)
        goblin = _make_entity("Goblin", is_player=False, x=5, y=5, dexterity=14)
        battle, logs = _make_battle([hero, goblin])
        battle.start_combat()
        self.assertTrue(battle.combat_started)
        self.assertEqual(battle.round, 1)
        self.assertIsNotNone(battle.get_current_entity())

    def test_surprise_round(self):
        random.seed(42)
        hero = _make_entity("Hero", is_player=True, x=1, y=1)
        goblin = _make_entity("Goblin", is_player=False, x=5, y=5)
        battle, logs = _make_battle([hero, goblin])
        battle.start_combat(surprise_side="players")
        # Enemies should be surprised
        self.assertTrue(goblin.is_surprised)
        self.assertFalse(hero.is_surprised)

    def test_check_battle_over_no_enemies(self):
        hero = _make_entity("Hero", is_player=True, x=1, y=1)
        goblin = _make_entity("Goblin", is_player=False, x=5, y=5, hp=1)
        battle, _ = _make_battle([hero, goblin])
        goblin.hp = 0
        result = battle.check_battle_over()
        self.assertEqual(result, "players")

    def test_check_battle_over_no_players(self):
        hero = _make_entity("Hero", is_player=True, x=1, y=1, hp=1)
        goblin = _make_entity("Goblin", is_player=False, x=5, y=5)
        battle, _ = _make_battle([hero, goblin])
        hero.hp = 0
        result = battle.check_battle_over()
        self.assertEqual(result, "enemies")

    def test_check_battle_not_over(self):
        hero = _make_entity("Hero", is_player=True, x=1, y=1)
        goblin = _make_entity("Goblin", is_player=False, x=5, y=5)
        battle, _ = _make_battle([hero, goblin])
        result = battle.check_battle_over()
        self.assertIsNone(result)


class TestEnemiesAndAllies(unittest.TestCase):
    def test_get_enemies(self):
        hero = _make_entity("Hero", is_player=True, x=1, y=1)
        goblin1 = _make_entity("Goblin1", is_player=False, x=5, y=5)
        goblin2 = _make_entity("Goblin2", is_player=False, x=6, y=6)
        battle, _ = _make_battle([hero, goblin1, goblin2])
        enemies = battle.get_enemies_of(hero)
        self.assertEqual(len(enemies), 2)

    def test_get_allies(self):
        hero1 = _make_entity("Hero1", is_player=True, x=1, y=1)
        hero2 = _make_entity("Hero2", is_player=True, x=2, y=2)
        goblin = _make_entity("Goblin", is_player=False, x=5, y=5)
        battle, _ = _make_battle([hero1, hero2, goblin])
        allies = battle.get_allies_of(hero1)
        self.assertEqual(len(allies), 1)
        self.assertEqual(allies[0].name, "Hero2")

    def test_dead_not_in_enemies(self):
        hero = _make_entity("Hero", is_player=True, x=1, y=1)
        goblin = _make_entity("Goblin", is_player=False, x=5, y=5)
        battle, _ = _make_battle([hero, goblin])
        goblin.hp = 0
        enemies = battle.get_enemies_of(hero)
        self.assertEqual(len(enemies), 0)

    def test_banished_not_in_enemies(self):
        hero = _make_entity("Hero", is_player=True, x=1, y=1)
        goblin = _make_entity("Goblin", is_player=False, x=5, y=5)
        battle, _ = _make_battle([hero, goblin])
        goblin.add_condition("Banished")
        enemies = battle.get_enemies_of(hero)
        self.assertEqual(len(enemies), 0)


class TestCoverBonus(unittest.TestCase):
    def test_no_cover(self):
        e1 = _make_entity("A", x=0, y=0)
        e2 = _make_entity("B", x=5, y=0)
        battle, _ = _make_battle([e1, e2])
        bonus = battle.get_cover_bonus(e1, e2)
        self.assertEqual(bonus, 0)


class TestDoor(unittest.TestCase):
    def test_toggle_door(self):
        battle, logs = _make_battle()
        door = TerrainObject(terrain_type="door", grid_x=5, grid_y=5)
        battle.add_terrain(door)
        result = battle.toggle_door_at(5, 5)
        self.assertTrue(result)

    def test_toggle_non_door(self):
        battle, _ = _make_battle()
        wall = TerrainObject(terrain_type="wall", grid_x=5, grid_y=5)
        battle.add_terrain(wall)
        result = battle.toggle_door_at(5, 5)
        self.assertFalse(result)


class TestSaveLoad(unittest.TestCase):
    def test_get_state_dict(self):
        hero = _make_entity("Hero", is_player=True, x=1, y=1)
        goblin = _make_entity("Goblin", is_player=False, x=5, y=5)
        battle, _ = _make_battle([hero, goblin])
        state = battle.get_state_dict()
        self.assertIn("entities", state)
        self.assertEqual(len(state["entities"]), 2)
        self.assertIn("round", state)
        self.assertIn("terrain", state)

    def test_state_dict_entity_fields(self):
        hero = _make_entity("Hero", is_player=True, x=1, y=1, hp=40)
        battle, _ = _make_battle([hero])
        hero.hp = 30
        hero.add_condition("Poisoned")
        state = battle.get_state_dict()
        ent = state["entities"][0]
        self.assertEqual(ent["name"], "Hero")
        self.assertEqual(ent["hp"], 30)
        self.assertIn("Poisoned", ent["conditions"])


class TestEntityAt(unittest.TestCase):
    def test_find_entity(self):
        hero = _make_entity("Hero", x=5, y=5)
        battle, _ = _make_battle([hero])
        found = battle.get_entity_at(5, 5)
        self.assertEqual(found, hero)

    def test_no_entity(self):
        battle, _ = _make_battle()
        # Use a position far from any demo entities
        found = battle.get_entity_at(99, 99)
        self.assertIsNone(found)


class TestElevation(unittest.TestCase):
    def test_fall_damage_applied(self):
        e = _make_entity("Climber", hp=100, x=0, y=0)
        battle, logs = _make_battle([e])
        random.seed(42)
        e.elevation = 30
        battle.apply_fall_damage(e, 30)
        self.assertLess(e.hp, 100)
        self.assertTrue(e.has_condition("Prone"))
        self.assertFalse(e.is_flying)

    def test_no_fall_damage_zero(self):
        e = _make_entity("Safe", hp=100, x=0, y=0)
        battle, _ = _make_battle([e])
        battle.apply_fall_damage(e, 0)
        self.assertEqual(e.hp, 100)


if __name__ == "__main__":
    unittest.main()
