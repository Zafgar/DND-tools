"""Phase 6a — ActorRegistry + shared token identity tests."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import unittest
import tempfile
import json

from data.actors import (
    Actor, ActorRegistry, ACTOR_KINDS,
    get_registry, reset_registry_for_tests, save_registry,
    DEFAULT_WORLD_PX, DEFAULT_TOWN_PX,
)
from data.map_engine import MapObject
from data.models import CreatureStats, AbilityScores, Action
from engine.entities import Entity
from engine.battle import BattleSystem
from engine.battle_serialization import get_state_dict, restore_state


class TestActor(unittest.TestCase):
    def test_default_fields(self):
        a = Actor(name="Alara")
        self.assertTrue(a.id.startswith("actor_"))
        self.assertEqual(a.kind, "npc")
        self.assertEqual(a.world_px, DEFAULT_WORLD_PX)
        self.assertEqual(a.town_px, DEFAULT_TOWN_PX)
        self.assertEqual(a.passenger_ids, [])

    def test_invalid_kind_falls_to_unknown(self):
        a = Actor(name="X", kind="dragonborn")
        self.assertEqual(a.kind, "unknown")

    def test_color_list_is_coerced_to_tuple(self):
        a = Actor(name="X", color=[10, 20, 30])
        self.assertEqual(a.color, (10, 20, 30))

    def test_to_from_dict_roundtrip(self):
        a = Actor(name="Alara", kind="hero", color=(12, 34, 56),
                   notes="brave", tags=["pc", "ranger"])
        d = a.to_dict()
        b = Actor.from_dict(d)
        self.assertEqual(a.id, b.id)
        self.assertEqual(b.name, "Alara")
        self.assertEqual(b.color, (12, 34, 56))
        self.assertEqual(b.tags, ["pc", "ranger"])


class TestRegistryCRUD(unittest.TestCase):
    def setUp(self):
        self.reg = ActorRegistry()

    def test_create_assigns_id(self):
        a = self.reg.create("Bran", kind="hero")
        self.assertTrue(a.id)
        self.assertIn(a.id, self.reg)
        self.assertEqual(len(self.reg), 1)

    def test_get_missing_returns_none(self):
        self.assertIsNone(self.reg.get("nope"))

    def test_remove_existing(self):
        a = self.reg.create("X")
        self.assertTrue(self.reg.remove(a.id))
        self.assertNotIn(a.id, self.reg)

    def test_remove_missing_returns_false(self):
        self.assertFalse(self.reg.remove("nope"))

    def test_list_by_kind(self):
        self.reg.create("A", kind="hero")
        self.reg.create("B", kind="npc")
        self.reg.create("C", kind="hero")
        heroes = self.reg.list_by_kind("hero")
        self.assertEqual(len(heroes), 2)

    def test_get_by_name(self):
        a = self.reg.create("Alara")
        self.assertIs(self.reg.get_by_name("ALARA"), a)
        self.assertIs(self.reg.get_by_name("  alara  "), a)

    def test_list_all_is_sorted_case_insensitive(self):
        self.reg.create("zed")
        self.reg.create("Alara")
        self.reg.create("mari")
        names = [a.name for a in self.reg.list_all()]
        self.assertEqual(names, ["Alara", "mari", "zed"])

    def test_all_kinds_valid(self):
        for k in ACTOR_KINDS:
            self.assertIn(k, ACTOR_KINDS)


class TestVehiclePassengers(unittest.TestCase):
    def setUp(self):
        self.reg = ActorRegistry()
        self.ship = self.reg.create("Stormchaser", kind="vehicle")
        self.hero = self.reg.create("Alara", kind="hero")
        self.npc = self.reg.create("Bran", kind="npc")

    def test_add_passenger(self):
        self.assertTrue(self.reg.add_passenger(self.ship.id, self.hero.id))
        self.assertIn(self.hero.id, self.ship.passenger_ids)

    def test_add_passenger_rejects_non_vehicle(self):
        self.assertFalse(self.reg.add_passenger(self.hero.id, self.npc.id))

    def test_add_passenger_rejects_unknown_passenger(self):
        self.assertFalse(self.reg.add_passenger(self.ship.id, "nope"))

    def test_add_passenger_idempotent(self):
        self.reg.add_passenger(self.ship.id, self.hero.id)
        self.reg.add_passenger(self.ship.id, self.hero.id)
        self.assertEqual(self.ship.passenger_ids.count(self.hero.id), 1)

    def test_remove_passenger(self):
        self.reg.add_passenger(self.ship.id, self.hero.id)
        self.assertTrue(self.reg.remove_passenger(self.ship.id, self.hero.id))
        self.assertNotIn(self.hero.id, self.ship.passenger_ids)

    def test_remove_actor_purges_passenger_refs(self):
        self.reg.add_passenger(self.ship.id, self.hero.id)
        self.reg.remove(self.hero.id)
        self.assertNotIn(self.hero.id, self.ship.passenger_ids)


class TestResolve(unittest.TestCase):
    def setUp(self):
        self.reg = ActorRegistry()
        self.hero = self.reg.create("Alara", kind="hero",
                                     color=(40, 200, 90), notes="ranger")

    def test_resolve_mapobject(self):
        obj = MapObject(x=10, y=10, object_type="info_pin",
                        actor_id=self.hero.id)
        resolved = self.reg.resolve(obj)
        self.assertIs(resolved, self.hero)

    def test_resolve_entity(self):
        stats = CreatureStats(
            name="Alara", size="Medium", hit_points=30,
            abilities=AbilityScores(strength=10, dexterity=14),
            actions=[Action(name="Bow", attack_bonus=5, damage_dice="1d8",
                            damage_bonus=3, damage_type="piercing", range=60)],
        )
        e = Entity(stats, 5, 5, is_player=True)
        e.actor_id = self.hero.id
        resolved = self.reg.resolve(e)
        self.assertIs(resolved, self.hero)

    def test_resolve_empty_actor_id(self):
        obj = MapObject(x=0, y=0)
        self.assertIsNone(self.reg.resolve(obj))

    def test_resolve_unknown_id(self):
        obj = MapObject(x=0, y=0, actor_id="actor_does_not_exist")
        self.assertIsNone(self.reg.resolve(obj))


class TestPersistence(unittest.TestCase):
    def test_save_and_load_roundtrip(self):
        reg = ActorRegistry()
        reg.create("Alara", kind="hero", color=(10, 20, 30),
                    notes="pc", tags=["ranger"])
        reg.create("Stormchaser", kind="vehicle")

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
            path = tf.name
        try:
            reg.save(path)
            reg2 = ActorRegistry()
            self.assertTrue(reg2.load(path))
            self.assertEqual(len(reg2), 2)
            alara = reg2.get_by_name("Alara")
            self.assertIsNotNone(alara)
            self.assertEqual(alara.color, (10, 20, 30))
            self.assertEqual(alara.tags, ["ranger"])
        finally:
            os.unlink(path)

    def test_load_missing_file_returns_false(self):
        reg = ActorRegistry()
        self.assertFalse(reg.load("/nonexistent/123.json"))

    def test_load_invalid_json_returns_false(self):
        reg = ActorRegistry()
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False,
                                          mode="w") as tf:
            tf.write("not json")
            path = tf.name
        try:
            self.assertFalse(reg.load(path))
        finally:
            os.unlink(path)


class TestSingleton(unittest.TestCase):
    def setUp(self):
        reset_registry_for_tests()

    def tearDown(self):
        reset_registry_for_tests()

    def test_singleton_identity(self):
        r1 = get_registry()
        r2 = get_registry()
        self.assertIs(r1, r2)

    def test_reset_rebuilds(self):
        r1 = get_registry()
        reset_registry_for_tests()
        r2 = get_registry()
        self.assertIsNot(r1, r2)


class TestMapObjectSerialization(unittest.TestCase):
    def test_actor_id_roundtrip(self):
        from data.map_engine import _obj_to_dict, _obj_from_dict
        obj = MapObject(x=1.0, y=2.0, object_type="npc_token",
                         actor_id="actor_xyz", label="Alara")
        d = _obj_to_dict(obj)
        self.assertEqual(d["actor_id"], "actor_xyz")
        obj2 = _obj_from_dict(d)
        self.assertEqual(obj2.actor_id, "actor_xyz")

    def test_legacy_object_without_actor_id(self):
        from data.map_engine import _obj_from_dict
        obj = _obj_from_dict({"id": "obj_1", "x": 0, "y": 0,
                               "object_type": "info_pin"})
        self.assertEqual(obj.actor_id, "")


class TestEntitySerialization(unittest.TestCase):
    def test_entity_actor_id_roundtrip(self):
        stats = CreatureStats(
            name="Guard", size="Medium", hit_points=15,
            abilities=AbilityScores(strength=10, dexterity=10),
            actions=[Action(name="Sword", attack_bonus=3, damage_dice="1d6",
                            damage_bonus=1, damage_type="slashing", range=5)],
        )
        e = Entity(stats, 5, 5, is_player=False)
        e.actor_id = "actor_abc"
        b = BattleSystem(log_callback=lambda *a: None, initial_entities=[e])
        data = get_state_dict(b)
        ent_data = next(ed for ed in data["entities"] if ed["name"] == "Guard")
        self.assertEqual(ent_data["actor_id"], "actor_abc")

        # Restore into a fresh battle and confirm the field survives
        b2 = BattleSystem(log_callback=lambda *a: None, initial_entities=[])
        restore_state(b2, data)
        guard = next(en for en in b2.entities if en.name == "Guard")
        self.assertEqual(guard.actor_id, "actor_abc")

    def test_entity_default_actor_id_empty(self):
        stats = CreatureStats(
            name="X", hit_points=10,
            abilities=AbilityScores(strength=10, dexterity=10),
        )
        e = Entity(stats, 0, 0)
        self.assertEqual(e.actor_id, "")


if __name__ == "__main__":
    unittest.main()
