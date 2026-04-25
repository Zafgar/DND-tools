"""Phase 7g — scenario AI-navigation validation tests."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest

from data import scenarios
from data.scenarios import (
    Scenario, ScenarioTile, ScenarioMonster, SCENARIOS,
)
from data.scenario_validation import (
    reachable_cells, party_can_reach_monster, validate_all_scenarios,
    _tile_blocks,
)


class TestTileBlocks(unittest.TestCase):
    def test_open_ground_is_passable(self):
        s = Scenario(id="x", name="x", category="cave", description="t",
                      tiles=[], monsters=[], party_spawns=[])
        self.assertFalse(_tile_blocks(s, 5, 5))

    def test_wall_blocks(self):
        s = Scenario(id="x", name="x", category="cave", description="t",
                      tiles=[ScenarioTile("wall", 5, 5)],
                      monsters=[], party_spawns=[])
        self.assertTrue(_tile_blocks(s, 5, 5))
        self.assertFalse(_tile_blocks(s, 4, 5))

    def test_door_does_not_block(self):
        s = Scenario(id="x", name="x", category="cave", description="t",
                      tiles=[ScenarioTile("door", 5, 5)],
                      monsters=[], party_spawns=[])
        self.assertFalse(_tile_blocks(s, 5, 5))

    def test_chasm_blocks(self):
        s = Scenario(id="x", name="x", category="cave", description="t",
                      tiles=[ScenarioTile("chasm_20", 5, 5)],
                      monsters=[], party_spawns=[])
        self.assertTrue(_tile_blocks(s, 5, 5))


class TestReachableCells(unittest.TestCase):
    def test_open_field_full_reach(self):
        s = Scenario(id="x", name="x", category="cave", description="t",
                      tiles=[], monsters=[], party_spawns=[])
        reach = reachable_cells(s, 5, 5, max_x=10, max_y=10)
        self.assertEqual(len(reach), 100)

    def test_walled_off_room(self):
        # 3x3 walled room around (5,5) - only that cell is reachable
        wall_tiles = []
        for x in range(4, 7):
            wall_tiles.append(ScenarioTile("wall", x, 4))
            wall_tiles.append(ScenarioTile("wall", x, 6))
        wall_tiles.append(ScenarioTile("wall", 4, 5))
        wall_tiles.append(ScenarioTile("wall", 6, 5))
        s = Scenario(id="x", name="x", category="cave", description="t",
                      tiles=wall_tiles, monsters=[], party_spawns=[])
        reach = reachable_cells(s, 5, 5, max_x=10, max_y=10)
        self.assertEqual(reach, {(5, 5)})

    def test_door_lets_pathing_through(self):
        # Same wall as before but with a door at (4,5)
        wall_tiles = []
        for x in range(4, 7):
            wall_tiles.append(ScenarioTile("wall", x, 4))
            wall_tiles.append(ScenarioTile("wall", x, 6))
        wall_tiles.append(ScenarioTile("door", 4, 5))
        wall_tiles.append(ScenarioTile("wall", 6, 5))
        s = Scenario(id="x", name="x", category="cave", description="t",
                      tiles=wall_tiles, monsters=[], party_spawns=[])
        reach = reachable_cells(s, 5, 5, max_x=10, max_y=10)
        # Inside (1) + the door cell (1) + the rest of the open grid
        self.assertGreater(len(reach), 1)
        self.assertIn((4, 5), reach)

    def test_blocked_start_is_empty(self):
        s = Scenario(id="x", name="x", category="cave", description="t",
                      tiles=[ScenarioTile("wall", 5, 5)],
                      monsters=[], party_spawns=[])
        self.assertEqual(reachable_cells(s, 5, 5, max_x=10, max_y=10),
                         set())


class TestPartyCanReachMonster(unittest.TestCase):
    def test_simple_open_field(self):
        s = Scenario(id="x", name="x", category="cave", description="t",
                      tiles=[],
                      monsters=[ScenarioMonster("Wolf", 8, 5)],
                      party_spawns=[(2, 5)])
        rep = party_can_reach_monster(s)
        self.assertTrue(rep["ok"])
        self.assertEqual(rep["orphan_spawns"], [])
        self.assertEqual(rep["orphan_monsters"], [])

    def test_unreachable_monster(self):
        # Wall ring around the monster
        wall_tiles = []
        for x in range(7, 10):
            wall_tiles.append(ScenarioTile("wall", x, 4))
            wall_tiles.append(ScenarioTile("wall", x, 6))
        wall_tiles.append(ScenarioTile("wall", 7, 5))
        wall_tiles.append(ScenarioTile("wall", 9, 5))
        s = Scenario(id="x", name="x", category="cave", description="t",
                      tiles=wall_tiles,
                      monsters=[ScenarioMonster("Wolf", 8, 5)],
                      party_spawns=[(2, 5)])
        rep = party_can_reach_monster(s)
        self.assertFalse(rep["ok"])
        self.assertIn((2, 5), rep["orphan_spawns"])
        self.assertIn((8, 5), rep["orphan_monsters"])


class TestBundledScenariosNavigable(unittest.TestCase):
    """Every scenario shipped in the catalog must be navigable —
    every party spawn can reach at least one monster, and no monster
    is unreachable from all spawns."""
    def test_all_authored_scenarios_pass(self):
        bad = validate_all_scenarios(SCENARIOS)
        self.assertEqual(
            bad, [],
            "Authored scenarios with broken navigation:\n"
            + "\n".join(f"  {r['scenario_id']}: orphans={r['orphan_spawns']} "
                         f"unreachable_monsters={r['orphan_monsters']}"
                         for r in bad),
        )

    def test_phase7g_new_scenarios_present(self):
        ids = {s.id for s in SCENARIOS}
        for new_id in ("tavern_brawl", "vault_heist", "caravan_ambush",
                        "ruined_watchtower", "shrine_defense"):
            self.assertIn(new_id, ids, f"Missing new scenario {new_id}")

    def test_monster_count_increased(self):
        # Phase 7g adds ≥5 scenarios on top of the existing catalog
        self.assertGreaterEqual(len(SCENARIOS), 20)


if __name__ == "__main__":
    unittest.main()
