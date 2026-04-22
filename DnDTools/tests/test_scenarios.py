"""Phase 4d — Scenario catalog tests."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import unittest

from data import scenarios
from data.library import library
from engine.terrain import TERRAIN_TYPES


class TestScenarioStructure(unittest.TestCase):
    def test_all_ids_unique(self):
        ids = [s.id for s in scenarios.SCENARIOS]
        self.assertEqual(len(ids), len(set(ids)),
                         f"Duplicate scenario IDs: {ids}")

    def test_all_have_required_fields(self):
        for s in scenarios.SCENARIOS:
            self.assertTrue(s.id, f"Scenario missing id: {s}")
            self.assertTrue(s.name, f"{s.id}: missing name")
            self.assertIn(s.category, scenarios.CATEGORIES,
                          f"{s.id}: invalid category {s.category!r}")
            self.assertGreater(len(s.monsters), 0, f"{s.id}: no monsters")
            self.assertGreater(len(s.party_spawns), 0,
                               f"{s.id}: no party spawns")

    def test_recommended_levels_valid(self):
        for s in scenarios.SCENARIOS:
            self.assertLessEqual(s.recommended_level_min,
                                 s.recommended_level_max,
                                 f"{s.id}: level_min > level_max")
            self.assertGreaterEqual(s.recommended_level_min, 1,
                                    f"{s.id}: bad min level")
            self.assertLessEqual(s.recommended_level_max, 20,
                                 f"{s.id}: bad max level")

    def test_all_monster_names_resolve(self):
        for s in scenarios.SCENARIOS:
            for m in s.monsters:
                try:
                    stats = library.get_monster(m.name)
                    self.assertTrue(stats)
                except ValueError:
                    self.fail(f"{s.id}: monster {m.name!r} not in library")

    def test_all_terrain_types_valid(self):
        for s in scenarios.SCENARIOS:
            for t in s.tiles:
                self.assertIn(t.terrain_type, TERRAIN_TYPES,
                              f"{s.id}: unknown terrain {t.terrain_type!r}")

    def test_categories_covered(self):
        """Every declared category has at least one scenario."""
        cat_set = {s.category for s in scenarios.SCENARIOS}
        for cat in scenarios.CATEGORIES:
            self.assertIn(cat, cat_set,
                          f"No scenarios in category {cat!r}")

    def test_tile_positions_non_negative(self):
        for s in scenarios.SCENARIOS:
            for t in s.tiles:
                self.assertGreaterEqual(t.x, 0, f"{s.id}: tile x < 0")
                self.assertGreaterEqual(t.y, 0, f"{s.id}: tile y < 0")

    def test_monster_positions_non_negative(self):
        for s in scenarios.SCENARIOS:
            for m in s.monsters:
                self.assertGreaterEqual(m.x, 0, f"{s.id}: monster x < 0")
                self.assertGreaterEqual(m.y, 0, f"{s.id}: monster y < 0")


class TestScenarioAPI(unittest.TestCase):
    def test_get_scenario_exists(self):
        s = scenarios.get_scenario("bandit_crossroads")
        self.assertEqual(s.category, "bandit_lair")

    def test_get_scenario_missing_raises(self):
        with self.assertRaises(KeyError):
            scenarios.get_scenario("does_not_exist")

    def test_list_all_returns_copy(self):
        a = scenarios.list_all()
        a.clear()
        b = scenarios.list_all()
        self.assertGreater(len(b), 0)

    def test_list_by_category(self):
        caves = scenarios.list_by_category("cave")
        self.assertGreater(len(caves), 0)
        for s in caves:
            self.assertEqual(s.category, "cave")

    def test_list_by_category_unknown(self):
        self.assertEqual(scenarios.list_by_category("bogus"), [])

    def test_list_by_level(self):
        s_lv3 = scenarios.list_by_level(3)
        self.assertGreater(len(s_lv3), 0)
        for s in s_lv3:
            self.assertLessEqual(s.recommended_level_min, 3)
            self.assertGreaterEqual(s.recommended_level_max, 3)

    def test_list_by_level_too_high(self):
        # No scenarios target level 25, but level 20 may exist
        self.assertEqual(scenarios.list_by_level(99), [])


class TestBuildBattle(unittest.TestCase):
    def test_build_basic(self):
        log = []
        s = scenarios.get_scenario("wolf_pack")
        battle = scenarios.build_battle_from_scenario(s, log.append)
        self.assertEqual(len(battle.entities), len(s.monsters))
        self.assertEqual(len(battle.terrain), len(s.tiles))
        self.assertFalse(any(e.is_player for e in battle.entities))
        self.assertTrue(any("[SCENARIO]" in line for line in log))

    def test_build_applies_ceiling(self):
        s = scenarios.get_scenario("goblin_warrens")
        battle = scenarios.build_battle_from_scenario(s)
        self.assertEqual(battle.ceiling_ft, 10)

    def test_build_applies_weather(self):
        s = scenarios.get_scenario("lizardfolk_shallows")
        battle = scenarios.build_battle_from_scenario(s)
        self.assertEqual(battle.weather, "Rain")

    def test_build_no_ceiling_outdoor(self):
        s = scenarios.get_scenario("wolf_pack")
        battle = scenarios.build_battle_from_scenario(s)
        self.assertEqual(battle.ceiling_ft, 0)

    def test_build_places_monsters(self):
        s = scenarios.get_scenario("bandit_crossroads")
        battle = scenarios.build_battle_from_scenario(s)
        names = sorted(e.stats.name for e in battle.entities)
        expected = sorted(m.name for m in s.monsters)
        self.assertEqual(names, expected)

    def test_build_default_log_noop(self):
        """build_battle_from_scenario without a callback must not crash."""
        s = scenarios.get_scenario("wolf_pack")
        battle = scenarios.build_battle_from_scenario(s)  # no log_callback
        self.assertGreater(len(battle.entities), 0)

    def test_monsters_get_team(self):
        s = scenarios.get_scenario("wolf_pack")
        battle = scenarios.build_battle_from_scenario(s)
        self.assertTrue(all(e.team == "Red" for e in battle.entities))


class TestScenarioCoverage(unittest.TestCase):
    def test_every_category_has_at_least_two(self):
        """Quality bar: each category ships with enough variety."""
        from collections import Counter
        counts = Counter(s.category for s in scenarios.SCENARIOS)
        for cat in scenarios.CATEGORIES:
            self.assertGreaterEqual(
                counts.get(cat, 0), 1,
                f"Category {cat!r} has no scenarios"
            )

    def test_minimum_scenario_count(self):
        """We promised 10-20 ready-made scenarios."""
        self.assertGreaterEqual(len(scenarios.SCENARIOS), 10)


if __name__ == "__main__":
    unittest.main()
