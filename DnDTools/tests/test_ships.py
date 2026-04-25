"""Phase 7d — ship catalog, sea routes and fares."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest

from data.ships import (
    SHIP_TYPES, ShipType, get_ship, list_ship_types,
    passenger_fare_gp, cargo_fare_gp, voyage_days, voyage_estimate,
    cheapest_ship, fastest_ship,
    is_sea_route, is_air_route, can_traverse,
)
from data.map_engine import AnnotationPath, MapObject


class TestShipCatalog(unittest.TestCase):
    def test_known_ships_present(self):
        for k in ("rowboat", "keelboat", "longship", "sailing_ship",
                  "warship", "galley", "airship"):
            self.assertIn(k, SHIP_TYPES)

    def test_get_ship(self):
        s = get_ship("sailing_ship")
        self.assertEqual(s.name, "Sailing Ship")
        self.assertGreater(s.miles_per_day, 0)

    def test_get_unknown_raises(self):
        with self.assertRaises(KeyError):
            get_ship("submarine")

    def test_all_ships_have_positive_speed(self):
        for s in list_ship_types():
            self.assertGreater(s.miles_per_day, 0,
                               f"{s.key} has nonsensical speed")

    def test_daily_charter_property(self):
        s = get_ship("sailing_ship")
        self.assertGreater(s.daily_charter_gp, 0)


class TestPassengerFare(unittest.TestCase):
    def test_basic_fare(self):
        s = get_ship("sailing_ship")  # 0.2 gp/mi
        self.assertAlmostEqual(passenger_fare_gp(s, 100, 1), 20.0)

    def test_multiple_passengers(self):
        s = get_ship("sailing_ship")
        self.assertAlmostEqual(passenger_fare_gp(s, 100, 4), 80.0)

    def test_zero_distance(self):
        s = get_ship("sailing_ship")
        self.assertEqual(passenger_fare_gp(s, 0, 4), 0.0)

    def test_zero_passengers(self):
        s = get_ship("sailing_ship")
        self.assertEqual(passenger_fare_gp(s, 100, 0), 0.0)

    def test_overcap_clipped(self):
        s = get_ship("rowboat")  # cap 4
        # Asks for 10, only charges for 4
        full = passenger_fare_gp(s, 100, 4)
        over = passenger_fare_gp(s, 100, 10)
        self.assertEqual(over, full)


class TestCargoFare(unittest.TestCase):
    def test_basic_cargo(self):
        s = get_ship("sailing_ship")  # 0.05 gp / ton-mi
        self.assertAlmostEqual(cargo_fare_gp(s, 100, 10), 50.0)

    def test_overcap_cargo_clipped(self):
        s = get_ship("rowboat")  # cargo_tons=0
        self.assertEqual(cargo_fare_gp(s, 100, 5), 0.0)


class TestVoyageDays(unittest.TestCase):
    def test_days(self):
        s = get_ship("sailing_ship")  # 48 mpd
        self.assertAlmostEqual(voyage_days(s, 96), 2.0)

    def test_zero_miles(self):
        self.assertEqual(voyage_days(get_ship("sailing_ship"), 0), 0)


class TestVoyageEstimate(unittest.TestCase):
    def test_full_estimate(self):
        s = get_ship("sailing_ship")
        v = voyage_estimate(s, 200, passengers=4, cargo_tons=5)
        self.assertEqual(v["ship"], "sailing_ship")
        self.assertAlmostEqual(v["days"], 200/48)
        self.assertAlmostEqual(v["passenger_fare_gp"], 4 * 0.2 * 200)
        self.assertAlmostEqual(v["cargo_fare_gp"], 5 * 0.05 * 200)
        self.assertAlmostEqual(v["total_gp"],
                                v["passenger_fare_gp"] + v["cargo_fare_gp"])
        self.assertFalse(v["exceeded_passengers"])
        self.assertFalse(v["exceeded_cargo"])

    def test_flags_overcap(self):
        s = get_ship("rowboat")  # 4 / 0
        v = voyage_estimate(s, 50, passengers=10, cargo_tons=2)
        self.assertTrue(v["exceeded_passengers"])
        self.assertTrue(v["exceeded_cargo"])


class TestShipPicker(unittest.TestCase):
    def test_cheapest_for_party_of_4(self):
        v = cheapest_ship(miles=100, passengers=4)
        self.assertIsNotNone(v)
        # Rowboat is the cheapest at 0.05 gp/mi for 4 → 20 gp
        self.assertEqual(v["ship"], "rowboat")
        self.assertAlmostEqual(v["total_gp"], 20.0)

    def test_cheapest_when_cargo_demands_bigger_hull(self):
        v = cheapest_ship(miles=100, passengers=4, cargo_tons=50)
        self.assertIsNotNone(v)
        # Rowboat / keelboat / longship can't fit 50t cargo
        self.assertNotIn(v["ship"], ("rowboat", "keelboat", "longship"))

    def test_fastest_for_party_of_4(self):
        v = fastest_ship(miles=100, passengers=4)
        self.assertEqual(v["ship"], "airship")  # 192 mpd

    def test_no_ship_fits_returns_none(self):
        # 1000 passengers — no hull fits
        self.assertIsNone(cheapest_ship(miles=100, passengers=1000))


class TestRouteValidation(unittest.TestCase):
    def test_sea_route_detection(self):
        p = AnnotationPath(id="P", path_type="sea_route")
        self.assertTrue(is_sea_route(p))
        self.assertFalse(is_air_route(p))

    def test_air_route_detection(self):
        p = AnnotationPath(id="P", path_type="air_route")
        self.assertTrue(is_air_route(p))

    def test_sea_route_rejects_walking_party(self):
        p = AnnotationPath(id="P", path_type="sea_route")
        party = MapObject(x=0, y=0, object_type="party_token")
        self.assertFalse(can_traverse(p, party))

    def test_sea_route_accepts_ship(self):
        p = AnnotationPath(id="P", path_type="sea_route")
        ship = MapObject(x=0, y=0, object_type="ship")
        self.assertTrue(can_traverse(p, ship))

    def test_sea_route_accepts_airship(self):
        p = AnnotationPath(id="P", path_type="sea_route")
        air = MapObject(x=0, y=0, object_type="airship")
        self.assertTrue(can_traverse(p, air))

    def test_air_route_rejects_ship(self):
        p = AnnotationPath(id="P", path_type="air_route")
        ship = MapObject(x=0, y=0, object_type="ship")
        self.assertFalse(can_traverse(p, ship))

    def test_road_accepts_anyone(self):
        p = AnnotationPath(id="P", path_type="road")
        for k in ("party_token", "caravan", "ship", "airship",
                  "army_token"):
            obj = MapObject(x=0, y=0, object_type=k)
            self.assertTrue(can_traverse(p, obj),
                            f"Road should accept {k}")


if __name__ == "__main__":
    unittest.main()
