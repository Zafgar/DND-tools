"""Phase 4c — 3D LOS + indoor ceiling tests."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import unittest

from data.models import CreatureStats, AbilityScores, Action
from engine.entities import Entity
from engine.battle import BattleSystem
from engine.terrain import TerrainObject, check_los_blocked
from engine.battle_serialization import get_state_dict, restore_state


def _make_entity(name="Test", x=5.0, y=5.0, is_player=True, elevation=0,
                 speed=30, fly_speed=0):
    stats = CreatureStats(
        name=name, size="Medium", hit_points=50, armor_class=15, speed=speed,
        fly_speed=fly_speed,
        abilities=AbilityScores(strength=10, dexterity=10),
        actions=[Action(name="Bow", attack_bonus=5, damage_dice="1d8",
                        damage_bonus=3, damage_type="piercing", range=60)],
    )
    e = Entity(stats, x, y, is_player=is_player)
    e.elevation = elevation
    return e


def _make_battle(entities=None):
    log = []
    b = BattleSystem(log_callback=log.append, initial_entities=entities or [])
    return b, log


class TestLOSBackwardCompatible(unittest.TestCase):
    def test_wall_blocks_ground_to_ground(self):
        terrain = [TerrainObject(terrain_type="wall", grid_x=5, grid_y=5)]
        # Old signature (no z): behaves exactly as before
        self.assertTrue(check_los_blocked(terrain, 3, 5, 7, 5))

    def test_no_wall_clear(self):
        self.assertFalse(check_los_blocked([], 3, 5, 7, 5))

    def test_wall_not_on_line(self):
        terrain = [TerrainObject(terrain_type="wall", grid_x=5, grid_y=2)]
        self.assertFalse(check_los_blocked(terrain, 3, 5, 7, 5))


class TestLOS3D(unittest.TestCase):
    def test_flying_shooter_sees_over_wall(self):
        """A wall is 10ft tall. A shooter at 20ft flying over it sees
        another flier at 20ft on the far side."""
        terrain = [TerrainObject(terrain_type="wall", grid_x=5, grid_y=5)]
        blocked = check_los_blocked(terrain, 3, 5, 7, 5, z1=20.0, z2=20.0)
        self.assertFalse(blocked)

    def test_flying_shooter_blocked_by_tall_tree(self):
        """Trees are 20ft tall. A shooter at 20ft is exactly at tree height
        and should be blocked."""
        terrain = [TerrainObject(terrain_type="tree", grid_x=5, grid_y=5)]
        blocked = check_los_blocked(terrain, 3, 5, 7, 5, z1=20.0, z2=20.0)
        self.assertTrue(blocked)

    def test_ground_target_blocked_by_wall(self):
        """Ground-to-ground over a 10ft wall is always blocked (wall top
        at 10ft, sightline at ~5ft eye level)."""
        terrain = [TerrainObject(terrain_type="wall", grid_x=5, grid_y=5)]
        blocked = check_los_blocked(terrain, 3, 5, 7, 5, z1=5.0, z2=5.0)
        self.assertTrue(blocked)

    def test_elevated_shooter_sees_ground_target_past_wall(self):
        """Shooter at 30ft (tower), target at 5ft (ground) with a 10ft
        wall between them. The sightline passes well over the wall at
        its location, so not blocked."""
        terrain = [TerrainObject(terrain_type="wall", grid_x=5, grid_y=5)]
        # Shooter at x=3 z=30, target at x=7 z=5, wall at x=5
        # fraction = 0.5, sightline_z = 30 + 0.5*(5-30) = 17.5
        # wall top = 10 — 10 < 17.5 → NOT blocked
        blocked = check_los_blocked(terrain, 3, 5, 7, 5, z1=30.0, z2=5.0)
        self.assertFalse(blocked)

    def test_fog_cloud_default_blocks_flyers(self):
        """Fog cloud (no explicit los_height_ft) defaults to 100ft cap —
        still blocks flyers at 30ft."""
        terrain = [TerrainObject(terrain_type="fog", grid_x=5, grid_y=5)]
        # If elevation_ft <= 0 and no los_height_ft → fallback 100ft
        blocked = check_los_blocked(terrain, 3, 5, 7, 5, z1=30.0, z2=30.0)
        self.assertTrue(blocked)


class TestBattleSystemLOS3D(unittest.TestCase):
    def test_flying_attackers_see_over_wall(self):
        shooter = _make_entity("Shooter", x=3, y=5, is_player=True, elevation=20)
        shooter.is_flying = True
        target = _make_entity("Target", x=7, y=5, is_player=False, elevation=20)
        target.is_flying = True
        battle, _ = _make_battle([shooter, target])
        battle.terrain.append(TerrainObject(terrain_type="wall", grid_x=5, grid_y=5))
        # Both fly over wall - should have LOS
        self.assertTrue(battle.has_line_of_sight(shooter, target))

    def test_ground_attackers_blocked_by_wall(self):
        shooter = _make_entity("Shooter", x=3, y=5, is_player=True)
        target = _make_entity("Target", x=7, y=5, is_player=False)
        battle, _ = _make_battle([shooter, target])
        battle.terrain.append(TerrainObject(terrain_type="wall", grid_x=5, grid_y=5))
        self.assertFalse(battle.has_line_of_sight(shooter, target))


class TestCeiling(unittest.TestCase):
    def test_default_no_ceiling(self):
        b, _ = _make_battle()
        self.assertEqual(b.ceiling_ft, 0)
        self.assertGreaterEqual(b.max_fly_altitude(), 1000)

    def test_ceiling_limits_fly_altitude(self):
        b, _ = _make_battle()
        b.ceiling_ft = 15
        # Max altitude = ceiling - 5 (creature head-room)
        self.assertEqual(b.max_fly_altitude(), 10)

    def test_clamp_fly_altitude(self):
        e = _make_entity("Drake", fly_speed=60, elevation=30)
        e.is_flying = True
        b, _ = _make_battle([e])
        b.ceiling_ft = 15
        b.clamp_fly_altitude(e)
        self.assertLessEqual(e.elevation, 10)

    def test_clamp_noop_when_no_ceiling(self):
        e = _make_entity("Drake", fly_speed=60, elevation=100)
        e.is_flying = True
        b, _ = _make_battle([e])
        self.assertEqual(b.ceiling_ft, 0)
        b.clamp_fly_altitude(e)
        self.assertEqual(e.elevation, 100)

    def test_clamp_noop_when_not_flying(self):
        e = _make_entity("Drake", fly_speed=60, elevation=30)
        e.is_flying = False
        b, _ = _make_battle([e])
        b.ceiling_ft = 15
        b.clamp_fly_altitude(e)
        self.assertEqual(e.elevation, 30)

    def test_serialization_roundtrip_ceiling(self):
        e = _make_entity("Hero", is_player=True)
        b, _ = _make_battle([e])
        b.ceiling_ft = 20
        data = get_state_dict(b)
        b2, _ = _make_battle([_make_entity("Hero", is_player=True)])
        restore_state(b2, data)
        self.assertEqual(b2.ceiling_ft, 20)


class TestCeilingClampInMovement(unittest.TestCase):
    def test_move_entity_with_elevation_clamps_flyer(self):
        e = _make_entity("Drake", fly_speed=60, x=5, y=5)
        e.is_flying = True
        e.elevation = 50
        b, _ = _make_battle([e])
        b.ceiling_ft = 15
        b.move_entity_with_elevation(e, 6, 5)
        self.assertLessEqual(e.elevation, 10)


if __name__ == "__main__":
    unittest.main()
