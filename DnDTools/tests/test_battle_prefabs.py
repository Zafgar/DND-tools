"""Phase 7e — battle-map furnished prefab tests."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import unittest

from data.battle_prefabs import (
    PREFABS, PrefabTile, Prefab,
    list_prefabs, list_by_category, get_prefab, categories,
    apply_prefab, prefab_footprint,
)
from engine.battle import BattleSystem
from engine.terrain import TerrainObject, TERRAIN_TYPES


def _make_battle():
    b = BattleSystem(log_callback=lambda *a: None, initial_entities=[])
    b.entities = []
    b.terrain = []
    return b


class TestCatalog(unittest.TestCase):
    def test_known_prefabs_present(self):
        for k in ("small_hut", "cottage", "tavern_common", "shop",
                  "smithy", "watchtower", "stables",
                  "barracks_room", "treasure_vault", "shrine",
                  "campsite", "wagon_circle", "well_yard",
                  "ruined_tower"):
            self.assertIn(k, PREFABS)

    def test_get_prefab(self):
        p = get_prefab("small_hut")
        self.assertEqual(p.name, "Small Hut")
        self.assertGreater(len(p.tiles), 0)

    def test_get_unknown_raises(self):
        with self.assertRaises(KeyError):
            get_prefab("teleporter_pad")

    def test_list_prefabs(self):
        self.assertGreater(len(list_prefabs()), 5)

    def test_categories_complete(self):
        cats = set(categories())
        for needed in ("building", "room", "encampment", "decor", "ruin"):
            self.assertIn(needed, cats)

    def test_list_by_category(self):
        rooms = list_by_category("room")
        self.assertGreater(len(rooms), 0)
        for p in rooms:
            self.assertEqual(p.category, "room")

    def test_all_prefab_tiles_use_known_terrain(self):
        for p in PREFABS.values():
            for t in p.tiles:
                self.assertIn(t.terrain_type, TERRAIN_TYPES,
                              f"{p.key} uses unknown terrain "
                              f"{t.terrain_type!r}")


class TestPrefabFootprint(unittest.TestCase):
    def test_3x3_hut(self):
        p = get_prefab("small_hut")
        self.assertEqual(prefab_footprint(p), (3, 3))

    def test_6x5_tavern(self):
        p = get_prefab("tavern_common")
        self.assertEqual(prefab_footprint(p), (6, 5))


class TestApplyPrefab(unittest.TestCase):
    def test_drop_at_anchor(self):
        b = _make_battle()
        n = apply_prefab(b, get_prefab("small_hut"), anchor_x=10, anchor_y=10)
        self.assertEqual(n, len(get_prefab("small_hut").tiles))
        # Anchor cell should now hold the NW corner wall
        nw = next(t for t in b.terrain
                  if int(t.grid_x) == 10 and int(t.grid_y) == 10)
        self.assertEqual(nw.terrain_type, "wall")

    def test_anchor_offset(self):
        b = _make_battle()
        apply_prefab(b, get_prefab("small_hut"), anchor_x=20, anchor_y=15)
        # Door sits at (anchor_x+1, anchor_y) = (21, 15)
        door = next((t for t in b.terrain
                     if int(t.grid_x) == 21 and int(t.grid_y) == 15
                     and t.terrain_type == "door"), None)
        self.assertIsNotNone(door)

    def test_furnishing_present(self):
        b = _make_battle()
        apply_prefab(b, get_prefab("tavern_common"),
                      anchor_x=0, anchor_y=0)
        types = [t.terrain_type for t in b.terrain]
        self.assertIn("table", types)
        self.assertIn("fire", types)
        self.assertIn("door", types)

    def test_replace_existing_clears_overlap(self):
        b = _make_battle()
        # Pre-place a tree where the prefab's NW corner will go
        b.terrain.append(TerrainObject(terrain_type="tree",
                                        grid_x=10, grid_y=10))
        apply_prefab(b, get_prefab("small_hut"),
                      anchor_x=10, anchor_y=10,
                      replace_existing=True)
        # Tree should have been cleared, only wall remains at (10,10)
        at_corner = [t for t in b.terrain
                     if int(t.grid_x) == 10 and int(t.grid_y) == 10]
        types = sorted(t.terrain_type for t in at_corner)
        self.assertEqual(types, ["wall"])

    def test_no_replace_keeps_overlap(self):
        b = _make_battle()
        b.terrain.append(TerrainObject(terrain_type="tree",
                                        grid_x=10, grid_y=10))
        apply_prefab(b, get_prefab("small_hut"),
                      anchor_x=10, anchor_y=10,
                      replace_existing=False)
        at_corner = [t for t in b.terrain
                     if int(t.grid_x) == 10 and int(t.grid_y) == 10]
        types = sorted(t.terrain_type for t in at_corner)
        # Both tree and wall stack on the cell
        self.assertEqual(types, ["tree", "wall"])

    def test_multiple_drops(self):
        b = _make_battle()
        apply_prefab(b, get_prefab("small_hut"),
                      anchor_x=0, anchor_y=0)
        apply_prefab(b, get_prefab("small_hut"),
                      anchor_x=10, anchor_y=0)
        # Both huts present
        walls_at_0_0 = [t for t in b.terrain
                        if int(t.grid_x) == 0 and t.terrain_type == "wall"]
        walls_at_10_0 = [t for t in b.terrain
                         if int(t.grid_x) == 10 and t.terrain_type == "wall"]
        self.assertGreater(len(walls_at_0_0), 0)
        self.assertGreater(len(walls_at_10_0), 0)


class TestPrefabBuilderHelpers(unittest.TestCase):
    def test_wall_rect_4x4_count(self):
        # 4x4 hollow rect should have 4*2 + 2*2 = 12 wall tiles
        b = _make_battle()
        apply_prefab(b, get_prefab("cottage"),
                      anchor_x=0, anchor_y=0)
        walls = [t for t in b.terrain if t.terrain_type == "wall"]
        # 12 wall tiles + door replaces 1 wall → 11 walls actually placed
        # (the prefab leaves the wall and adds the door on top)
        self.assertGreaterEqual(len(walls), 11)


if __name__ == "__main__":
    unittest.main()
