"""Phase 7c — flight (crow flies) distance + map scale editor tests."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import math
import unittest

from data.map_engine import WorldMap, MapLayer
from data.map_travel import (
    flight_distance_miles, flight_time_days, flight_time_hours,
    set_map_scale, set_travel_speed_per_day, map_scale_summary,
)


def _wm(width=100, height=100, scale=1.0, speed=24.0):
    wm = WorldMap(name="T", width=width, height=height, tile_size=1,
                   scale_miles_per_pct=scale,
                   travel_speed_miles_per_day=speed)
    wm.layers = [MapLayer(id="L0", name="Surface")]
    wm.annotations = []
    return wm


class TestFlightDistance(unittest.TestCase):
    def test_horizontal_run(self):
        wm = _wm()
        d = flight_distance_miles(wm, 0, 50, 100, 50)
        self.assertAlmostEqual(d, 100.0, places=4)

    def test_vertical_on_square_map(self):
        wm = _wm()
        d = flight_distance_miles(wm, 50, 0, 50, 100)
        self.assertAlmostEqual(d, 100.0, places=4)

    def test_diagonal_pythagorean(self):
        wm = _wm()
        # 30%-40%-50% triangle on a square map
        d = flight_distance_miles(wm, 0, 0, 30, 40)
        self.assertAlmostEqual(d, 50.0, places=4)

    def test_zero_distance(self):
        wm = _wm()
        self.assertEqual(flight_distance_miles(wm, 50, 50, 50, 50), 0.0)

    def test_aspect_aware_on_wide_map(self):
        wm = _wm(width=200, height=100)
        # vertical 10% on 2:1 map = aspect 0.5 → 5 miles at scale 1
        d = flight_distance_miles(wm, 50, 0, 50, 10)
        self.assertAlmostEqual(d, 5.0, places=4)

    def test_scale_doubles_distance(self):
        wm = _wm(scale=2.0)
        d = flight_distance_miles(wm, 0, 50, 100, 50)
        self.assertAlmostEqual(d, 200.0, places=4)


class TestFlightTime(unittest.TestCase):
    def test_one_day_at_100_mpd(self):
        wm = _wm()
        d = flight_time_days(wm, 0, 50, 100, 50,
                              fly_speed_miles_per_day=100)
        self.assertAlmostEqual(d, 1.0)

    def test_zero_speed_inf(self):
        wm = _wm()
        self.assertEqual(
            flight_time_days(wm, 0, 0, 100, 0, fly_speed_miles_per_day=0),
            float("inf"),
        )

    def test_hourly_calc(self):
        wm = _wm()
        # 100 mi @ 50 mph = 2 hours
        h = flight_time_hours(wm, 0, 50, 100, 50, fly_speed_mph=50)
        self.assertAlmostEqual(h, 2.0)


class TestSetMapScale(unittest.TestCase):
    def test_set_positive(self):
        wm = _wm(scale=1.0)
        self.assertTrue(set_map_scale(wm, 5.0))
        self.assertEqual(wm.scale_miles_per_pct, 5.0)

    def test_reject_zero(self):
        wm = _wm(scale=1.0)
        self.assertFalse(set_map_scale(wm, 0))
        self.assertEqual(wm.scale_miles_per_pct, 1.0)

    def test_reject_negative(self):
        wm = _wm(scale=1.0)
        self.assertFalse(set_map_scale(wm, -3.0))
        self.assertEqual(wm.scale_miles_per_pct, 1.0)

    def test_reject_nan(self):
        wm = _wm(scale=1.0)
        self.assertFalse(set_map_scale(wm, float("nan")))
        self.assertEqual(wm.scale_miles_per_pct, 1.0)

    def test_reject_garbage(self):
        wm = _wm(scale=1.0)
        self.assertFalse(set_map_scale(wm, "fast"))
        self.assertEqual(wm.scale_miles_per_pct, 1.0)


class TestSetTravelSpeed(unittest.TestCase):
    def test_set_positive(self):
        wm = _wm(speed=24)
        self.assertTrue(set_travel_speed_per_day(wm, 30))
        self.assertEqual(wm.travel_speed_miles_per_day, 30)

    def test_reject_zero(self):
        wm = _wm(speed=24)
        self.assertFalse(set_travel_speed_per_day(wm, 0))
        self.assertEqual(wm.travel_speed_miles_per_day, 24)


class TestMapScaleSummary(unittest.TestCase):
    def test_default_world(self):
        wm = _wm(scale=1.0, speed=24.0)
        s = map_scale_summary(wm)
        self.assertEqual(s["miles_per_pct"], 1.0)
        self.assertEqual(s["travel_miles_per_day"], 24.0)
        self.assertAlmostEqual(s["miles_per_pct_per_day"], 24.0)

    def test_zero_scale_safe(self):
        wm = _wm(scale=0.0)
        s = map_scale_summary(wm)
        self.assertEqual(s["miles_per_pct_per_day"], 0.0)


if __name__ == "__main__":
    unittest.main()
