"""Phase 6c — Vehicle MapObject + passenger manifest tests."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest

from data.actors import ActorRegistry, reset_registry_for_tests
from data.map_engine import (
    MapObject, MapLayer, WorldMap, VEHICLE_TYPES,
    _obj_to_dict, _obj_from_dict,
)
from data.vehicles import (
    is_vehicle, add_passenger, remove_passenger, list_passengers,
    transfer_passenger, clear_passengers, describe_vehicle,
    scrub_actor_from_all,
)


def _wm_with_vehicle(ship_type="ship"):
    wm = WorldMap(name="T", width=100, height=100, tile_size=1)
    wm.layers = [MapLayer(id="L0", name="Sea")]
    ship = MapObject(x=10, y=10, object_type=ship_type, label="Stormchaser")
    wm.layers[0].objects.append(ship)
    return wm, ship


class TestVehicleIdentification(unittest.TestCase):
    def test_all_declared_types(self):
        for t in VEHICLE_TYPES:
            obj = MapObject(x=0, y=0, object_type=t)
            self.assertTrue(is_vehicle(obj), f"{t} should be a vehicle")

    def test_non_vehicle_objects(self):
        for t in ("info_pin", "town", "party_token", "army_token"):
            obj = MapObject(x=0, y=0, object_type=t)
            self.assertFalse(is_vehicle(obj))


class TestAddRemovePassenger(unittest.TestCase):
    def setUp(self):
        self.reg = ActorRegistry()
        self.alara = self.reg.create("Alara", kind="hero")
        self.bran  = self.reg.create("Bran", kind="npc")

    def test_add_single_passenger(self):
        _, ship = _wm_with_vehicle()
        ok = add_passenger(ship, self.alara.id, registry=self.reg)
        self.assertTrue(ok)
        self.assertEqual(ship.passenger_actor_ids, [self.alara.id])

    def test_add_rejects_non_vehicle(self):
        obj = MapObject(x=0, y=0, object_type="info_pin")
        ok = add_passenger(obj, self.alara.id, registry=self.reg)
        self.assertFalse(ok)
        self.assertEqual(obj.passenger_actor_ids, [])

    def test_add_rejects_unknown_actor(self):
        _, ship = _wm_with_vehicle()
        ok = add_passenger(ship, "actor_does_not_exist", registry=self.reg)
        self.assertFalse(ok)

    def test_add_idempotent(self):
        _, ship = _wm_with_vehicle()
        add_passenger(ship, self.alara.id, registry=self.reg)
        add_passenger(ship, self.alara.id, registry=self.reg)
        self.assertEqual(ship.passenger_actor_ids.count(self.alara.id), 1)

    def test_remove_passenger(self):
        _, ship = _wm_with_vehicle()
        add_passenger(ship, self.alara.id, registry=self.reg)
        self.assertTrue(remove_passenger(ship, self.alara.id))
        self.assertEqual(ship.passenger_actor_ids, [])

    def test_remove_missing_returns_false(self):
        _, ship = _wm_with_vehicle()
        self.assertFalse(remove_passenger(ship, "nope"))

    def test_clear_passengers(self):
        _, ship = _wm_with_vehicle()
        add_passenger(ship, self.alara.id, registry=self.reg)
        add_passenger(ship, self.bran.id, registry=self.reg)
        self.assertEqual(clear_passengers(ship), 2)
        self.assertEqual(ship.passenger_actor_ids, [])


class TestListPassengers(unittest.TestCase):
    def setUp(self):
        self.reg = ActorRegistry()
        self.alara = self.reg.create("Alara", kind="hero")
        self.bran  = self.reg.create("Bran", kind="npc")
        _, self.ship = _wm_with_vehicle()
        add_passenger(self.ship, self.alara.id, registry=self.reg)
        add_passenger(self.ship, self.bran.id, registry=self.reg)

    def test_returns_actor_objects(self):
        riders = list_passengers(self.ship, registry=self.reg)
        self.assertEqual({r.name for r in riders}, {"Alara", "Bran"})

    def test_skips_unknown_ids(self):
        self.ship.passenger_actor_ids.append("actor_ghost")
        riders = list_passengers(self.ship, registry=self.reg)
        self.assertEqual(len(riders), 2)  # ghost skipped

    def test_empty_for_non_vehicle(self):
        obj = MapObject(x=0, y=0, object_type="town")
        self.assertEqual(list_passengers(obj, registry=self.reg), [])


class TestTransferPassenger(unittest.TestCase):
    def setUp(self):
        self.reg = ActorRegistry()
        self.hero = self.reg.create("Alara", kind="hero")
        self.wm = WorldMap(name="T", width=100, height=100, tile_size=1)
        self.wm.layers = [MapLayer(id="L0", name="Sea")]
        self.ship = MapObject(x=10, y=10, object_type="ship", label="A")
        self.air = MapObject(x=20, y=20, object_type="airship", label="B")
        self.wm.layers[0].objects.extend([self.ship, self.air])
        add_passenger(self.ship, self.hero.id, registry=self.reg)

    def test_transfer_success(self):
        ok = transfer_passenger(self.ship, self.air, self.hero.id,
                                 registry=self.reg)
        self.assertTrue(ok)
        self.assertNotIn(self.hero.id, self.ship.passenger_actor_ids)
        self.assertIn(self.hero.id, self.air.passenger_actor_ids)

    def test_transfer_rejects_non_vehicle_src(self):
        bad_src = MapObject(x=0, y=0, object_type="info_pin")
        ok = transfer_passenger(bad_src, self.air, self.hero.id,
                                 registry=self.reg)
        self.assertFalse(ok)

    def test_transfer_rejects_non_vehicle_dst(self):
        bad_dst = MapObject(x=0, y=0, object_type="info_pin")
        ok = transfer_passenger(self.ship, bad_dst, self.hero.id,
                                 registry=self.reg)
        self.assertFalse(ok)
        # Source should still have the passenger
        self.assertIn(self.hero.id, self.ship.passenger_actor_ids)

    def test_transfer_fails_if_not_aboard_src(self):
        other = self.reg.create("Mari", kind="npc")
        ok = transfer_passenger(self.ship, self.air, other.id,
                                 registry=self.reg)
        self.assertFalse(ok)


class TestDescribeVehicle(unittest.TestCase):
    def setUp(self):
        self.reg = ActorRegistry()
        self.alara = self.reg.create("Alara", kind="hero")
        self.bran  = self.reg.create("Bran", kind="npc")
        _, self.ship = _wm_with_vehicle()

    def test_empty_ship(self):
        s = describe_vehicle(self.ship, registry=self.reg)
        self.assertIn("empty", s.lower())

    def test_with_riders(self):
        add_passenger(self.ship, self.alara.id, registry=self.reg)
        add_passenger(self.ship, self.bran.id, registry=self.reg)
        s = describe_vehicle(self.ship, registry=self.reg)
        self.assertIn("Alara", s)
        self.assertIn("Bran", s)
        self.assertIn("2 aboard", s)

    def test_truncates_to_five_plus_count(self):
        for i in range(7):
            a = self.reg.create(f"Crew{i}", kind="npc")
            add_passenger(self.ship, a.id, registry=self.reg)
        s = describe_vehicle(self.ship, registry=self.reg)
        self.assertIn("+2", s)
        self.assertIn("7 aboard", s)


class TestScrubActor(unittest.TestCase):
    def test_scrub_from_multiple_vehicles(self):
        reg = ActorRegistry()
        alara = reg.create("Alara", kind="hero")
        wm = WorldMap(name="T", width=100, height=100, tile_size=1)
        wm.layers = [MapLayer(id="L0", name="S")]
        ship = MapObject(x=0, y=0, object_type="ship")
        wagon = MapObject(x=10, y=10, object_type="wagon")
        not_vehicle = MapObject(x=20, y=20, object_type="npc_token")
        wm.layers[0].objects.extend([ship, wagon, not_vehicle])
        add_passenger(ship, alara.id, registry=reg)
        add_passenger(wagon, alara.id, registry=reg)
        n = scrub_actor_from_all(wm, alara.id)
        self.assertEqual(n, 2)
        self.assertNotIn(alara.id, ship.passenger_actor_ids)
        self.assertNotIn(alara.id, wagon.passenger_actor_ids)


class TestSerialization(unittest.TestCase):
    def test_passengers_roundtrip(self):
        ship = MapObject(x=1, y=2, object_type="ship", label="S",
                          passenger_actor_ids=["actor_a", "actor_b"])
        d = _obj_to_dict(ship)
        self.assertEqual(d["passenger_actor_ids"], ["actor_a", "actor_b"])
        ship2 = _obj_from_dict(d)
        self.assertEqual(ship2.passenger_actor_ids, ["actor_a", "actor_b"])
        self.assertEqual(ship2.object_type, "ship")

    def test_legacy_object_gets_empty_list(self):
        obj = _obj_from_dict({"id": "obj1", "x": 0, "y": 0,
                               "object_type": "ship"})
        self.assertEqual(obj.passenger_actor_ids, [])


if __name__ == "__main__":
    unittest.main()
