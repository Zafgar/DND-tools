"""Phase 19 — quick-create + multi-pick + calendar tests."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
import tempfile
import unittest

from data.world import World, Location, NPC
from data.campaign import Campaign, save_campaign, load_campaign
from data.actors import ActorRegistry
from data.npc_quick_create import quick_create_npc, QuickCreateResult
from data.campaign_calendar import (
    TIME_OF_DAY_CYCLE, DAYS_PER_MONTH, MONTHS_PER_YEAR,
    advance_time_of_day, advance_days, time_of_day_step,
    set_calendar, format_date, month_name, set_month_names,
)
from states.multi_pick_helpers import (
    toggle_in_list, MultiNPCPicker, MultiLocationPicker,
)


# --------------------------------------------------------------------- #
# 19c — Quick-create NPC
# --------------------------------------------------------------------- #
class TestQuickCreateNPC(unittest.TestCase):
    def test_basic_create_no_portrait(self):
        w = World()
        reg = ActorRegistry()
        rep = quick_create_npc(w, name="Mira", race="Elf",
                                  occupation="Castellan",
                                  registry=reg)
        self.assertTrue(rep.npc_id)
        self.assertTrue(rep.actor_id)
        self.assertEqual(rep.portrait_path, "")
        self.assertEqual(w.npcs[rep.npc_id].name, "Mira")
        self.assertEqual(w.npcs[rep.npc_id].occupation, "Castellan")
        self.assertEqual(reg.get(rep.actor_id).name, "Mira")

    def test_links_npc_to_location_by_id(self):
        w = World()
        w.locations["loc1"] = Location(id="loc1", name="X",
                                          location_type="town")
        rep = quick_create_npc(w, name="Y", location_id="loc1",
                                  registry=ActorRegistry())
        self.assertIn(rep.npc_id, w.locations["loc1"].npc_ids)

    def test_empty_name_warns(self):
        rep = quick_create_npc(World(), name="",
                                  registry=ActorRegistry())
        self.assertEqual(rep.npc_id, "")
        self.assertIn("name required", rep.warnings)

    def test_imports_portrait_when_path_supplied(self):
        with tempfile.NamedTemporaryFile(suffix=".jpg",
                                            delete=False) as tf:
            tf.write(b"x")
            src = tf.name
        try:
            w = World()
            reg = ActorRegistry()
            rep = quick_create_npc(w, name="Mira",
                                      portrait_src_path=src,
                                      registry=reg)
            self.assertTrue(rep.portrait_path)
            # NPC + Actor both got the portrait path
            self.assertEqual(w.npcs[rep.npc_id].portrait_path,
                              rep.portrait_path)
            self.assertEqual(reg.get(rep.actor_id).portrait_path,
                              rep.portrait_path)
            # Cleanup
            from data.portrait_loader import PROJECT_ROOT
            full = os.path.join(PROJECT_ROOT, rep.portrait_path)
            if os.path.isfile(full):
                os.unlink(full)
        finally:
            os.unlink(src)


# --------------------------------------------------------------------- #
# 19d — Multi-pick toggle
# --------------------------------------------------------------------- #
class TestToggleInList(unittest.TestCase):
    def test_add(self):
        lst: list = []
        self.assertTrue(toggle_in_list("x", lst))
        self.assertEqual(lst, ["x"])

    def test_remove(self):
        lst = ["x", "y"]
        self.assertFalse(toggle_in_list("x", lst))
        self.assertEqual(lst, ["y"])

    def test_empty_id(self):
        lst = ["x"]
        self.assertFalse(toggle_in_list("", lst))
        self.assertEqual(lst, ["x"])


class TestMultiNPCPicker(unittest.TestCase):
    def test_query_returns_npcs(self):
        w = World()
        w.npcs["a"] = NPC(id="a", name="Alara",
                            occupation="Ranger")
        w.npcs["b"] = NPC(id="b", name="Bran",
                            occupation="Castellan",
                            faction="Vardun")
        picked = []
        p = MultiNPCPicker(w, on_pick=lambda i: picked.append(i))
        p.open(anchor_rect=(0, 0, 200, 30))
        labels = [e.label for e in p._dropdown._results]
        self.assertEqual(set(labels), {"Alara", "Bran"})
        # Sub-label includes occupation + faction
        bran = next(e for e in p._dropdown._results if e.label == "Bran")
        self.assertIn("Castellan", bran.sub)
        self.assertIn("Vardun", bran.sub)


class TestMultiLocationPicker(unittest.TestCase):
    def test_filters_by_type(self):
        w = World()
        w.locations["a"] = Location(id="a", name="A City",
                                       location_type="city")
        w.locations["b"] = Location(id="b", name="A Forest",
                                       location_type="wilderness")
        picked = []
        p = MultiLocationPicker(w, on_pick=lambda i: picked.append(i),
                                   location_type="city")
        p.open(anchor_rect=(0, 0, 200, 30))
        ids = [e.id for e in p._dropdown._results]
        self.assertEqual(ids, ["a"])


# --------------------------------------------------------------------- #
# 19e — Calendar
# --------------------------------------------------------------------- #
class TestTimeOfDayStep(unittest.TestCase):
    def test_cycle(self):
        cur = "dawn"
        rolled_count = 0
        for _ in range(len(TIME_OF_DAY_CYCLE)):
            nxt, rolled = time_of_day_step(cur)
            if rolled:
                rolled_count += 1
            cur = nxt
        self.assertEqual(rolled_count, 1)
        self.assertEqual(cur, "dawn")

    def test_unknown_falls_back_to_day(self):
        nxt, _ = time_of_day_step("twilight_zone")
        # day → dusk
        self.assertEqual(nxt, "dusk")

    def test_advance_rolls_calendar_at_midnight(self):
        c = Campaign()
        c.time_of_day = "night"
        c.in_game_day = 1
        info = advance_time_of_day(c)
        self.assertEqual(info["time_of_day"], "dawn")
        self.assertTrue(info["rolled"])
        self.assertEqual(info["day"], 2)


class TestAdvanceDays(unittest.TestCase):
    def test_simple_increment(self):
        c = Campaign()
        c.in_game_day = 5
        advance_days(c, 3)
        self.assertEqual(c.in_game_day, 8)

    def test_month_overflow(self):
        c = Campaign()
        c.in_game_day = 28
        advance_days(c, 5)
        self.assertEqual(c.in_game_day, 33 - DAYS_PER_MONTH)
        self.assertEqual(c.in_game_month, 2)

    def test_year_overflow(self):
        c = Campaign()
        c.in_game_day = 1
        c.in_game_month = MONTHS_PER_YEAR
        c.in_game_year = 1
        advance_days(c, DAYS_PER_MONTH)
        # crossed into next year, month 1
        self.assertEqual(c.in_game_month, 1)
        self.assertEqual(c.in_game_year, 2)

    def test_zero_no_op(self):
        c = Campaign(in_game_day=10)
        advance_days(c, 0)
        self.assertEqual(c.in_game_day, 10)


class TestSetCalendar(unittest.TestCase):
    def test_clamps(self):
        c = Campaign()
        set_calendar(c, day=99, month=15, year=0)
        self.assertEqual(c.in_game_day, DAYS_PER_MONTH)
        self.assertEqual(c.in_game_month, MONTHS_PER_YEAR)
        self.assertEqual(c.in_game_year, 1)

    def test_time_of_day_validated(self):
        c = Campaign()
        set_calendar(c, time_of_day="hyperspace")
        self.assertEqual(c.time_of_day, "day")
        set_calendar(c, time_of_day="night")
        self.assertEqual(c.time_of_day, "night")


class TestFormatDate(unittest.TestCase):
    def test_format_includes_ordinal(self):
        c = Campaign(in_game_day=1, in_game_month=1, in_game_year=1492)
        s = format_date(c)
        self.assertIn("1st", s)
        self.assertIn("Hammer", s)

    def test_format_2nd_3rd(self):
        c = Campaign(in_game_day=2, in_game_month=2, in_game_year=1)
        self.assertIn("2nd", format_date(c))
        c.in_game_day = 3
        self.assertIn("3rd", format_date(c))

    def test_teens_use_th(self):
        c = Campaign(in_game_day=11, in_game_month=1, in_game_year=1)
        self.assertIn("11th", format_date(c))
        c.in_game_day = 12
        self.assertIn("12th", format_date(c))
        c.in_game_day = 13
        self.assertIn("13th", format_date(c))


class TestMonthNames(unittest.TestCase):
    def test_default(self):
        self.assertEqual(month_name(1), "Hammer")
        self.assertEqual(month_name(12), "Nightal")

    def test_clamped(self):
        self.assertEqual(month_name(0), "Hammer")
        self.assertEqual(month_name(99), "Nightal")

    def test_set_month_names_validates_length(self):
        with self.assertRaises(ValueError):
            set_month_names(["Jan", "Feb"])


class TestCampaignCalendarRoundtrip(unittest.TestCase):
    def test_persists(self):
        c = Campaign(in_game_day=15, in_game_month=6,
                       in_game_year=1492, time_of_day="dusk")
        with tempfile.NamedTemporaryFile(suffix=".json",
                                            delete=False) as tf:
            path = tf.name
        try:
            save_campaign(c, path)
            c2 = load_campaign(path)
            self.assertEqual(c2.in_game_day, 15)
            self.assertEqual(c2.in_game_month, 6)
            self.assertEqual(c2.in_game_year, 1492)
            self.assertEqual(c2.time_of_day, "dusk")
        finally:
            os.unlink(path)

    def test_legacy_save_defaults(self):
        legacy = {
            "name": "old", "description": "", "created": "",
            "last_modified": "", "party": [], "time_of_day": "day",
            "current_area": "", "session_number": 1,
            "encounters": [], "areas": [], "notes": [],
            "world_data": {}, "kingdoms_data": [],
            "primary_world_map_id": "", "active_map_id": "",
            "settings": {},
        }
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w",
                                            delete=False) as tf:
            json.dump(legacy, tf)
            path = tf.name
        try:
            c = load_campaign(path)
            self.assertEqual(c.in_game_day, 1)
            self.assertEqual(c.in_game_month, 1)
            self.assertEqual(c.in_game_year, 1)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
