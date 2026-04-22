"""Phase 5a — Scenario picker helper tests (pure-logic, no UI).

The modal itself (states/scenario_picker_modal.py) is thin pygame
wiring around these helpers. We verify the logic that the modal feeds
into encounter_setup here.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import unittest

from data import scenarios
from data.scenarios import (
    scenario_monsters_as_entities,
    apply_scenario_to_battle,
)
from engine.battle import BattleSystem


class TestScenarioMonstersAsEntities(unittest.TestCase):
    def test_wolf_pack_all_monsters(self):
        s = scenarios.get_scenario("wolf_pack")
        ents = scenario_monsters_as_entities(s)
        self.assertEqual(len(ents), len(s.monsters))
        for e in ents:
            self.assertFalse(e.is_player)

    def test_duplicates_are_disambiguated(self):
        """Five wolves should get unique names (Wolf, Wolf 2, ...)."""
        s = scenarios.get_scenario("wolf_pack")
        ents = scenario_monsters_as_entities(s)
        wolf_only = [e.name for e in ents
                     if e.name.startswith("Wolf") and "Dire" not in e.name]
        self.assertEqual(len(wolf_only), 5)
        self.assertEqual(len(set(wolf_only)), 5)

    def test_respects_existing_roster(self):
        """If 'Goblin' is already in the roster, the new ones start at 'Goblin 2'."""
        s = scenarios.get_scenario("goblin_warrens")
        first = scenario_monsters_as_entities(s)   # 7 Goblin + Boss + Worg
        second = scenario_monsters_as_entities(s, existing_roster=first)
        names = [e.name for e in second]
        # All names must still be unique within the second batch
        self.assertEqual(len(names), len(set(names)))
        # And none collides with any name in `first`
        existing = {e.name for e in first}
        for n in names:
            self.assertNotIn(n, existing)

    def test_positions_preserved(self):
        s = scenarios.get_scenario("bandit_crossroads")
        ents = scenario_monsters_as_entities(s)
        for mon, ent in zip(s.monsters, ents):
            self.assertEqual(ent.grid_x, mon.x)
            self.assertEqual(ent.grid_y, mon.y)

    def test_team_assignment(self):
        s = scenarios.get_scenario("orc_raid")
        ents = scenario_monsters_as_entities(s)
        self.assertTrue(all(e.team == "Red" for e in ents))

    def test_unknown_monster_skipped(self):
        """scenario_monsters_as_entities tolerates a missing monster name."""
        from data.scenarios import Scenario, ScenarioMonster
        bad = Scenario(id="test", name="T", category="cave",
                       description="x",
                       monsters=[
                           ScenarioMonster("Wolf", 5, 5),
                           ScenarioMonster("Definitely Not A Real Monster", 6, 6),
                       ],
                       party_spawns=[(0, 0)])
        ents = scenario_monsters_as_entities(bad)
        self.assertEqual(len(ents), 1)
        self.assertEqual(ents[0].stats.name, "Wolf")


class TestApplyScenarioToBattle(unittest.TestCase):
    def _battle(self):
        return BattleSystem(log_callback=lambda *a: None, initial_entities=[])

    def test_terrain_and_ceiling(self):
        b = self._battle()
        b.terrain = []
        s = scenarios.get_scenario("goblin_warrens")  # ceiling_ft=10
        apply_scenario_to_battle(s, b)
        self.assertEqual(len(b.terrain), len(s.tiles))
        self.assertEqual(b.ceiling_ft, 10)

    def test_weather_applied(self):
        b = self._battle()
        b.terrain = []
        s = scenarios.get_scenario("lizardfolk_shallows")  # weather="Rain"
        apply_scenario_to_battle(s, b)
        self.assertEqual(b.weather, "Rain")

    def test_no_ceiling_outdoor(self):
        b = self._battle()
        b.terrain = []
        s = scenarios.get_scenario("wolf_pack")
        apply_scenario_to_battle(s, b)
        self.assertEqual(b.ceiling_ft, 0)

    def test_does_not_touch_monsters(self):
        b = self._battle()
        b.entities = []
        b.terrain = []
        s = scenarios.get_scenario("wolf_pack")
        apply_scenario_to_battle(s, b)
        self.assertEqual(b.entities, [])

    def test_lair_only_set_when_enabled(self):
        b = self._battle()
        b.terrain = []
        b.lair_enabled = False
        s = scenarios.get_scenario("wolf_pack")   # lair_enabled=False
        apply_scenario_to_battle(s, b)
        self.assertFalse(b.lair_enabled)


if __name__ == "__main__":
    unittest.main()
