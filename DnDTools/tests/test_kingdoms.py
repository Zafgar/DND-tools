"""Tests for the kingdoms navigator data layer."""
import unittest
from dataclasses import dataclass, field
from typing import List, Dict

from data.kingdoms import (
    NPC_ROLE_CATEGORIES, SEED_KINGDOMS, KingdomEntry, CityEntry,
    ensure_kingdoms_on_campaign, sync_kingdoms_to_campaign,
    find_kingdom, find_city, add_kingdom, add_city,
    group_npcs_by_role, search_world_npcs, _role_from_npc,
)


@dataclass
class FakeCampaign:
    kingdoms_data: List[Dict] = field(default_factory=list)


@dataclass
class FakeNPC:
    name: str
    occupation: str = ""
    title: str = ""
    faction: str = ""
    race: str = ""
    location_id: str = ""
    tags: list = field(default_factory=list)
    active: bool = True


@dataclass
class FakeWorld:
    npcs: dict = field(default_factory=dict)


class TestRoleClassification(unittest.TestCase):
    def test_keyword_match(self):
        n = FakeNPC(name="Grim", occupation="Blacksmith")
        self.assertEqual(_role_from_npc(n), "smiths")

    def test_finnish_keyword_match(self):
        n = FakeNPC(name="Aino", occupation="pappi")
        self.assertEqual(_role_from_npc(n), "clergy")

    def test_title_match(self):
        n = FakeNPC(name="Lord X", title="Baron of Frand")
        self.assertEqual(_role_from_npc(n), "rulers")

    def test_unclassified_returns_other(self):
        n = FakeNPC(name="Stranger")
        self.assertEqual(_role_from_npc(n), "other")

    def test_category_list_has_all_keys(self):
        keys = [c["key"] for c in NPC_ROLE_CATEGORIES]
        self.assertIn("rulers", keys)
        self.assertIn("other", keys)  # catch-all present


class TestCampaignIntegration(unittest.TestCase):
    def test_seed_on_empty_campaign(self):
        c = FakeCampaign()
        kingdoms = ensure_kingdoms_on_campaign(c)
        self.assertEqual(len(kingdoms), len(SEED_KINGDOMS))
        keys = {k.key for k in kingdoms}
        self.assertEqual(
            keys, {"tarmaas", "fundarla", "smardu", "aterterra", "oblitus"}
        )

    def test_find_kingdom_and_city(self):
        c = FakeCampaign()
        ensure_kingdoms_on_campaign(c)
        k = find_kingdom(c, "tarmaas")
        self.assertIsNotNone(k)
        self.assertEqual(k.name, "Tarmaas")
        frand = find_city(c, "tarmaas", "frand")
        self.assertIsNotNone(frand)
        self.assertTrue(frand.is_capital)

    def test_add_kingdom_and_city(self):
        c = FakeCampaign()
        ensure_kingdoms_on_campaign(c)
        add_kingdom(c, "new", "Newland", description="test")
        self.assertIsNotNone(find_kingdom(c, "new"))
        add_city(c, "new", "silverport", "Silverport", is_capital=True)
        found = find_city(c, "new", "silverport")
        self.assertIsNotNone(found)
        self.assertEqual(find_kingdom(c, "new").capital_key, "silverport")

    def test_sync_round_trip(self):
        c = FakeCampaign()
        ensure_kingdoms_on_campaign(c)
        add_city(c, "tarmaas", "sharn", "Sharn")
        sync_kingdoms_to_campaign(c)
        self.assertTrue(len(c.kingdoms_data) >= 5)
        # Build a fresh campaign with the persisted data; should restore Sharn.
        c2 = FakeCampaign(kingdoms_data=c.kingdoms_data)
        restored = ensure_kingdoms_on_campaign(c2)
        tarmaas = next(k for k in restored if k.key == "tarmaas")
        self.assertIn("sharn", [ci.key for ci in tarmaas.cities])


class TestGrouping(unittest.TestCase):
    def test_group_npcs_by_role(self):
        world = FakeWorld()
        world.npcs = {
            "n1": FakeNPC(name="King Elric",  occupation="King",
                          location_id="loc_frand"),
            "n2": FakeNPC(name="Gorim",       occupation="blacksmith",
                          location_id="loc_frand"),
            "n3": FakeNPC(name="Tilda",       occupation="farmer",
                          location_id="loc_frand"),
            "n4": FakeNPC(name="Wanderer",    occupation="",
                          location_id="loc_elsewhere"),
        }
        groups = group_npcs_by_role(world, "loc_frand")
        self.assertEqual(len(groups["rulers"]), 1)
        self.assertEqual(len(groups["smiths"]), 1)
        self.assertEqual(len(groups["workers"]), 1)
        self.assertEqual(len(groups["other"]), 0)

    def test_search_world_npcs(self):
        world = FakeWorld()
        world.npcs = {
            "n1": FakeNPC(name="King Elric"),
            "n2": FakeNPC(name="Gorim", occupation="Blacksmith"),
            "n3": FakeNPC(name="Tilda", occupation="Farmer"),
        }
        self.assertEqual(
            [n.name for n in search_world_npcs(world, "blacksmith")], ["Gorim"]
        )
        self.assertEqual(len(search_world_npcs(world, "")), 0)
        self.assertEqual(
            sorted(n.name for n in search_world_npcs(world, "i")),
            ["Gorim", "King Elric", "Tilda"],
        )


if __name__ == "__main__":
    unittest.main()
