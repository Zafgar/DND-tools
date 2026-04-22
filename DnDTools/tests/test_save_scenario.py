"""Phase 6d — save-current-battle-as-scenario tests."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import unittest
import tempfile

from data import scenarios
from data.models import CreatureStats, AbilityScores, Action
from engine.battle import BattleSystem
from engine.entities import Entity
from engine.terrain import TerrainObject


def _make_entity(name, is_player=False, x=5, y=5):
    stats = CreatureStats(
        name=name, size="Medium", hit_points=30,
        abilities=AbilityScores(strength=10, dexterity=10),
        actions=[Action(name="Sword", attack_bonus=3, damage_dice="1d6",
                        damage_bonus=1, damage_type="slashing", range=5)],
    )
    return Entity(stats, x, y, is_player=is_player)


def _make_battle():
    b = BattleSystem(log_callback=lambda *a: None, initial_entities=[])
    b.entities = []
    b.terrain = []
    return b


class TestScenarioFromBattle(unittest.TestCase):
    def test_basic_snapshot(self):
        b = _make_battle()
        b.terrain.append(TerrainObject(terrain_type="wall", grid_x=5, grid_y=5))
        b.terrain.append(TerrainObject(terrain_type="lava", grid_x=8, grid_y=6))
        b.entities.append(_make_entity("Hero", is_player=True, x=2, y=3))
        b.entities.append(_make_entity("Goblin", is_player=False, x=12, y=5))
        b.entities.append(_make_entity("Goblin 2", is_player=False, x=13, y=5))
        b.weather = "Fog"
        b.ceiling_ft = 15
        s = scenarios.scenario_from_battle(
            b, name="My Ambush", category="dungeon",
            description="Test",
            recommended_level_min=3, recommended_level_max=5,
            tags=("goblin", "ambush"),
        )
        self.assertEqual(s.name, "My Ambush")
        self.assertEqual(s.category, "dungeon")
        self.assertEqual(s.weather, "Fog")
        self.assertEqual(s.ceiling_ft, 15)
        self.assertEqual(len(s.tiles), 2)
        self.assertEqual(len(s.monsters), 2)
        self.assertEqual(s.monsters[0].name, "Goblin")
        self.assertIn((2, 3), s.party_spawns)
        self.assertEqual(s.tags, ("goblin", "ambush"))

    def test_rejects_bad_category_falls_back(self):
        b = _make_battle()
        b.entities.append(_make_entity("Hero", is_player=True))
        b.entities.append(_make_entity("Wolf", is_player=False))
        s = scenarios.scenario_from_battle(b, name="X",
                                            category="bogus_category")
        self.assertEqual(s.category, "outdoor")

    def test_party_spawns_default_when_empty(self):
        b = _make_battle()
        b.entities.append(_make_entity("Wolf", is_player=False))
        s = scenarios.scenario_from_battle(b, name="Solo Wolf")
        self.assertGreater(len(s.party_spawns), 0)

    def test_lair_entities_skipped(self):
        b = _make_battle()
        lair = _make_entity("Dragon Lair", is_player=False, x=0, y=0)
        lair.is_lair = True
        b.entities.append(lair)
        b.entities.append(_make_entity("Wolf", is_player=False, x=10, y=10))
        s = scenarios.scenario_from_battle(b, name="Lair Test")
        names = [m.name for m in s.monsters]
        self.assertNotIn("Dragon Lair", names)
        self.assertIn("Wolf", names)

    def test_summons_skipped(self):
        b = _make_battle()
        summon = _make_entity("Spiritual Weapon", is_player=False)
        summon.is_summon = True
        b.entities.append(summon)
        b.entities.append(_make_entity("Bandit", is_player=False, x=10, y=10))
        s = scenarios.scenario_from_battle(b, name="Test")
        self.assertEqual(len(s.monsters), 1)
        self.assertEqual(s.monsters[0].name, "Bandit")

    def test_monster_positions_rounded_to_int(self):
        b = _make_battle()
        b.entities.append(_make_entity("Wolf", is_player=False, x=10.4, y=5.6))
        s = scenarios.scenario_from_battle(b, name="T")
        self.assertEqual((s.monsters[0].x, s.monsters[0].y), (10, 6))

    def test_recommended_level_clamped(self):
        b = _make_battle()
        b.entities.append(_make_entity("Wolf", is_player=False))
        s = scenarios.scenario_from_battle(b, name="T",
                                            recommended_level_min=5,
                                            recommended_level_max=2)
        # max should never be below min after clamp
        self.assertGreaterEqual(s.recommended_level_max,
                                 s.recommended_level_min)


class TestSaveLoadUserScenario(unittest.TestCase):
    def setUp(self):
        scenarios.reset_user_cache_for_tests()
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        scenarios.reset_user_cache_for_tests()
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _sample(self):
        b = _make_battle()
        b.terrain.append(TerrainObject(terrain_type="wall", grid_x=5, grid_y=5))
        b.entities.append(_make_entity("Hero", is_player=True, x=2, y=2))
        b.entities.append(_make_entity("Bandit", is_player=False, x=10, y=5))
        return scenarios.scenario_from_battle(
            b, name="Sample Ambush", category="bandit_lair",
            description="Test scenario",
        )

    def test_save_creates_file(self):
        s = self._sample()
        path = scenarios.save_user_scenario(s, directory=self.tmpdir)
        self.assertTrue(os.path.isfile(path))
        self.assertTrue(path.endswith(".json"))

    def test_save_slugifies_id(self):
        s = self._sample()
        scenarios.save_user_scenario(s, directory=self.tmpdir)
        self.assertEqual(s.id, "sample_ambush")

    def test_save_reload_roundtrip(self):
        s = self._sample()
        scenarios.save_user_scenario(s, directory=self.tmpdir)

        # Force reload from the temp dir via internals
        scenarios._USER_SCENARIOS.clear()
        # Manually load the saved file
        with open(os.path.join(self.tmpdir, f"{s.id}.json")) as f:
            import json
            loaded = scenarios._scenario_from_dict(json.load(f))
        self.assertEqual(loaded.id, s.id)
        self.assertEqual(loaded.name, s.name)
        self.assertEqual(loaded.category, s.category)
        self.assertEqual(len(loaded.tiles), 1)
        self.assertEqual(len(loaded.monsters), 1)
        self.assertEqual(loaded.monsters[0].name, "Bandit")

    def test_save_replaces_existing_by_id(self):
        s1 = self._sample()
        s1.description = "v1"
        scenarios.save_user_scenario(s1, directory=self.tmpdir)
        s2 = self._sample()  # same name → same slug id
        s2.description = "v2"
        scenarios.save_user_scenario(s2, directory=self.tmpdir)
        matching = [x for x in scenarios._USER_SCENARIOS if x.id == s1.id]
        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0].description, "v2")

    def test_delete_user_scenario(self):
        s = self._sample()
        scenarios.save_user_scenario(s, directory=self.tmpdir)
        self.assertTrue(os.path.isfile(
            os.path.join(self.tmpdir, f"{s.id}.json")))
        ok = scenarios.delete_user_scenario(s.id, directory=self.tmpdir)
        self.assertTrue(ok)
        self.assertFalse(os.path.isfile(
            os.path.join(self.tmpdir, f"{s.id}.json")))
        self.assertNotIn(s.id, {x.id for x in scenarios._USER_SCENARIOS})

    def test_delete_missing_returns_false(self):
        self.assertFalse(scenarios.delete_user_scenario(
            "nope", directory=self.tmpdir))


class TestCatalogIntegration(unittest.TestCase):
    def setUp(self):
        scenarios.reset_user_cache_for_tests()
        self.tmpdir = tempfile.mkdtemp()
        # Reroute the default user scenarios dir for this test
        self._orig_dir = scenarios._USER_SCENARIOS_DIR
        scenarios._USER_SCENARIOS_DIR = self.tmpdir

    def tearDown(self):
        scenarios._USER_SCENARIOS_DIR = self._orig_dir
        scenarios.reset_user_cache_for_tests()
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_user_scenarios_appear_in_list_all(self):
        b = _make_battle()
        b.entities.append(_make_entity("Bandit", is_player=False))
        s = scenarios.scenario_from_battle(b, name="User Skirmish")
        scenarios.save_user_scenario(s)
        all_names = [x.name for x in scenarios.list_all()]
        self.assertIn("User Skirmish", all_names)

    def test_get_scenario_by_user_id(self):
        b = _make_battle()
        b.entities.append(_make_entity("Bandit", is_player=False))
        s = scenarios.scenario_from_battle(b, name="Another", category="cave")
        scenarios.save_user_scenario(s)
        loaded = scenarios.get_scenario(s.id)
        self.assertEqual(loaded.name, "Another")

    def test_user_scenario_visible_in_category_list(self):
        b = _make_battle()
        b.entities.append(_make_entity("Bandit", is_player=False))
        s = scenarios.scenario_from_battle(b, name="Harbor Raid",
                                            category="urban")
        scenarios.save_user_scenario(s)
        urban = scenarios.list_by_category("urban")
        names = [x.name for x in urban]
        self.assertIn("Harbor Raid", names)


if __name__ == "__main__":
    unittest.main()
