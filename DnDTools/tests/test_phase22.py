"""Phase 22 — living world (currency, demographics, kingdoms, organisations).

  22a: D&D 5e currency arithmetic + parsing.
  22b: Biome-based demographics suggester.
  22c: Kingdom + city rich fields and Novus Somnium seed data.
  22d: Organisation model + Brotherhood of Glorious Sun seed.
  22e: Relation matrix helpers (city/kingdom).
  22f: Aggregate helpers (population, treasury).
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import json
import unittest

from data.currency import (
    Coins, coins_from_string, total_cp_of,
)
from data.demographics import (
    suggest_demographics, biome_for_location_type, known_biomes,
    COMMON_RACES,
)
from data import kingdoms as kg
from data import organizations as orgs


class _FakeCampaign:
    """Tiny stand-in for ``Campaign`` — only the attributes our helpers
    touch."""
    def __init__(self):
        self.kingdoms_data = None
        self.organisations_data = None


# --------------------------------------------------------------------- #
# 22a — Currency
# --------------------------------------------------------------------- #
class TestCurrency(unittest.TestCase):
    def test_total_conversions(self):
        c = Coins(pp=1, gp=2, sp=3, cp=4)
        # 1pp=1000cp, 2gp=200cp, 3sp=30cp, 4cp=4cp → 1234
        self.assertEqual(c.total_cp(), 1234)
        self.assertAlmostEqual(c.total_gp(), 12.34, places=2)

    def test_from_cp_and_normalise(self):
        c = Coins.from_cp(1234)
        # The normalised form should preserve total cp
        self.assertEqual(c.total_cp(), 1234)

    def test_from_gp(self):
        c = Coins.from_gp(15)
        self.assertEqual(c.total_cp(), 1500)

    def test_can_afford_and_pay(self):
        purse = Coins(gp=10)
        # ``can_afford`` takes a price in gp
        self.assertTrue(purse.can_afford(5))
        self.assertFalse(purse.can_afford(20))
        # ``pay`` mutates in place; remaining purse drops to 7gp
        self.assertTrue(purse.pay(3))
        self.assertEqual(purse.total_cp(), 700)

    def test_arithmetic(self):
        a = Coins(gp=5)
        b = Coins(sp=20)
        s = a + b
        self.assertEqual(s.total_cp(), 700)
        # 5gp = 500cp, minus 10sp = 100cp → 400cp
        d = a - Coins(sp=10)
        self.assertEqual(d.total_cp(), 400)

    def test_parser(self):
        c = coins_from_string("12pp 4gp 50sp")
        self.assertEqual(c.pp, 12)
        self.assertEqual(c.gp, 4)
        self.assertEqual(c.sp, 50)
        # Bare number defaults to gp; the result is normalised (100gp →
        # 10pp) so we check the cp total rather than the bucket layout.
        c2 = coins_from_string("100")
        self.assertEqual(c2.total_gp(), 100.0)

    def test_total_cp_of_iterable(self):
        total = total_cp_of([Coins(gp=1), Coins(sp=10)])
        # 1gp + 10sp = 100cp + 100cp = 200cp
        self.assertEqual(total, 200)

    def test_short_renders_largest_first(self):
        s = Coins(pp=1, gp=2, sp=3).short()
        # Largest denomination first
        self.assertTrue(s.startswith("1pp"))


# --------------------------------------------------------------------- #
# 22b — Demographics
# --------------------------------------------------------------------- #
class TestDemographics(unittest.TestCase):
    def test_known_biomes_has_core_entries(self):
        b = set(known_biomes())
        for required in ("human_heartland", "forest", "underdark",
                          "mountain", "coast", "desert"):
            self.assertIn(required, b)

    def test_suggest_human_heartland_majority_human(self):
        d = suggest_demographics("human_heartland",
                                   total_population=10_000)
        self.assertEqual(d.biome, "human_heartland")
        self.assertEqual(d.majority_race(), "Human")
        # The breakdown should be close to 100% — biome defaults may
        # leave a small rounded gap (e.g. 98 instead of 100), which is
        # fine.
        total_pct = sum(d.by_race.values())
        self.assertAlmostEqual(total_pct, 100.0, delta=5.0)

    def test_population_by_race_sums_to_total(self):
        d = suggest_demographics("forest", total_population=1000)
        races = d.population_by_race()
        # Allow rounding slack of a couple of heads
        self.assertAlmostEqual(sum(races.values()), 1000, delta=5)

    def test_underdark_majority_is_subterranean(self):
        d = suggest_demographics("underdark", total_population=1000)
        maj = d.majority_race()
        self.assertIn(maj, {"Drow", "Duergar", "Svirfneblin", "Goblin",
                              "Orc"})

    def test_unknown_biome_falls_back(self):
        d = suggest_demographics("not_a_real_biome")
        # Falls back to a reasonable default (human heartland)
        self.assertGreater(len(d.by_race), 0)

    def test_biome_for_location_type(self):
        self.assertEqual(biome_for_location_type("city"), "cosmopolitan")
        self.assertEqual(biome_for_location_type("wilderness"), "forest")
        self.assertEqual(biome_for_location_type("dungeon"), "underdark")

    def test_common_races_includes_phb(self):
        for r in ("Human", "Elf", "Dwarf", "Halfling", "Half-Orc"):
            self.assertIn(r, COMMON_RACES)


# --------------------------------------------------------------------- #
# 22c — Kingdoms rich data + seed
# --------------------------------------------------------------------- #
class TestKingdomsSeed(unittest.TestCase):
    def test_seed_has_five_novus_somnium_kingdoms(self):
        keys = {k.key for k in kg.SEED_KINGDOMS}
        self.assertEqual(keys,
                          {"tarmaas", "fundarla", "smardu",
                           "aterterra", "oblitus"})

    def test_seed_kingdoms_have_population_and_treasury(self):
        for k in kg.SEED_KINGDOMS:
            self.assertGreater(k.population, 0,
                                f"{k.key} missing population")
            self.assertGreater(k.treasury_gp, 0,
                                f"{k.key} missing treasury")
            self.assertTrue(k.motto, f"{k.key} missing motto")

    def test_tarmaas_has_frand_capital(self):
        tarmaas = next(k for k in kg.SEED_KINGDOMS if k.key == "tarmaas")
        self.assertEqual(tarmaas.capital_key, "frand")
        cities = [c.key for c in tarmaas.cities]
        self.assertIn("frand", cities)
        frand = next(c for c in tarmaas.cities if c.key == "frand")
        self.assertTrue(frand.is_capital)
        self.assertGreater(frand.population, 0)

    def test_kingdom_round_trip_serialisation(self):
        c = _FakeCampaign()
        kg.ensure_kingdoms_on_campaign(c)
        kg.sync_kingdoms_to_campaign(c)
        s = json.dumps(c.kingdoms_data)
        c2 = _FakeCampaign()
        c2.kingdoms_data = json.loads(s)
        ks2 = kg.ensure_kingdoms_on_campaign(c2)
        # All five present, populations match
        self.assertEqual([k.key for k in ks2],
                          [k.key for k in kg.SEED_KINGDOMS])
        for orig, restored in zip(kg.SEED_KINGDOMS, ks2):
            self.assertEqual(orig.population, restored.population)
            self.assertEqual(orig.treasury_gp, restored.treasury_gp)
            self.assertEqual(orig.relations, restored.relations)


# --------------------------------------------------------------------- #
# 22e — Relation matrices
# --------------------------------------------------------------------- #
class TestKingdomRelations(unittest.TestCase):
    def setUp(self):
        self.camp = _FakeCampaign()
        kg.ensure_kingdoms_on_campaign(self.camp)

    def test_matrix_includes_self_diagonal(self):
        m = kg.kingdom_relation_matrix(self.camp)
        for k, row in m.items():
            self.assertEqual(row[k], "self")

    def test_seed_tarmaas_fundarla_are_allies(self):
        self.assertEqual(
            kg.get_kingdom_relation(self.camp, "tarmaas", "fundarla"),
            "ally")

    def test_set_kingdom_relation_is_symmetric(self):
        kg.set_kingdom_relation(self.camp, "smardu", "oblitus", "at_war")
        self.assertEqual(
            kg.get_kingdom_relation(self.camp, "smardu", "oblitus"),
            "at_war")
        self.assertEqual(
            kg.get_kingdom_relation(self.camp, "oblitus", "smardu"),
            "at_war")

    def test_unknown_level_normalised_to_neutral(self):
        kg.set_kingdom_relation(self.camp, "tarmaas", "smardu",
                                 "frenemies-of-fortune")
        self.assertEqual(
            kg.get_kingdom_relation(self.camp, "tarmaas", "smardu"),
            "neutral")

    def test_city_relation_matrix_for_kingdom_with_one_city(self):
        # Tarmaas seed has only Frand — matrix should be {"frand":
        # {"frand": "self"}}
        m = kg.city_relation_matrix(self.camp, "tarmaas")
        self.assertEqual(m, {"frand": {"frand": "self"}})

    def test_city_relation_setter(self):
        # Add a second city to Tarmaas and wire a relation
        kg.add_city(self.camp, "tarmaas", "highmoor", "Highmoor",
                     is_capital=False)
        kg.set_city_relation(self.camp, "tarmaas",
                              "frand", "highmoor", "trade")
        self.assertEqual(
            kg.get_city_relation(self.camp, "tarmaas",
                                  "frand", "highmoor"),
            "trade")
        # And symmetric:
        self.assertEqual(
            kg.get_city_relation(self.camp, "tarmaas",
                                  "highmoor", "frand"),
            "trade")


# --------------------------------------------------------------------- #
# 22f — Aggregates
# --------------------------------------------------------------------- #
class TestAggregates(unittest.TestCase):
    def setUp(self):
        self.camp = _FakeCampaign()
        kg.ensure_kingdoms_on_campaign(self.camp)

    def test_world_population_sums_kingdoms(self):
        total = kg.world_population(self.camp)
        expected = sum(k.population for k in kg.SEED_KINGDOMS)
        self.assertEqual(total, expected)

    def test_world_treasury_sums_all_pools(self):
        total = kg.world_treasury_total_gp(self.camp)
        # Should be at least the crown total of all five kingdoms
        crowns = sum(k.treasury_gp for k in kg.SEED_KINGDOMS)
        self.assertGreaterEqual(total, crowns)

    def test_kingdom_population_falls_back_to_city_sum(self):
        k = kg.KingdomEntry(key="emptyk", name="EmptyK")
        k.cities.append(kg.CityEntry(key="a", name="A", population=100))
        k.cities.append(kg.CityEntry(key="b", name="B", population=250))
        # Explicit total is 0 → sum of cities = 350
        self.assertEqual(kg.kingdom_population(k), 350)

    def test_kingdom_treasury_includes_cities_when_requested(self):
        k = kg.KingdomEntry(key="x", name="X", treasury_gp=100.0)
        k.cities.append(kg.CityEntry(key="a", name="A", treasury_gp=50.0))
        self.assertAlmostEqual(
            kg.kingdom_treasury_total_gp(k, include_cities=True), 150.0)
        self.assertAlmostEqual(
            kg.kingdom_treasury_total_gp(k, include_cities=False), 100.0)


# --------------------------------------------------------------------- #
# 22d — Organisations
# --------------------------------------------------------------------- #
class TestOrganisations(unittest.TestCase):
    def setUp(self):
        self.camp = _FakeCampaign()
        orgs.ensure_organisations_on_campaign(self.camp)

    def test_brotherhood_is_seeded(self):
        b = orgs.find_organisation(
            self.camp, "brotherhood_of_glorious_sun")
        self.assertIsNotNone(b)
        self.assertTrue(b.secret)
        self.assertEqual(b.kind, "brotherhood")
        # Has the expected rank hierarchy
        rank_keys = [r.key for r in b.ranks]
        for required in ("dawn_father", "radiant", "lightbringer",
                          "sun_blade", "acolyte"):
            self.assertIn(required, rank_keys)

    def test_brotherhood_member_lookup(self):
        b = orgs.find_organisation(
            self.camp, "brotherhood_of_glorious_sun")
        frand = b.members_in_city("frand")
        self.assertGreaterEqual(len(frand), 1)
        # Every Frand member should also be in Tarmaas
        for m in frand:
            self.assertEqual(m.kingdom_key, "tarmaas")

    def test_add_and_remove_member(self):
        m = orgs.add_member(
            self.camp, "brotherhood_of_glorious_sun",
            npc_name="Test Initiate", rank_key="acolyte",
            city_key="frand", kingdom_key="tarmaas",
        )
        self.assertIsNotNone(m)
        self.assertTrue(m.active)
        # Round-trip resolves to organisations_for_npc_name
        hits = orgs.organisations_for_npc_name(self.camp, "Test Initiate")
        self.assertEqual(len(hits), 1)
        # Soft-delete
        ok = orgs.remove_member(
            self.camp, "brotherhood_of_glorious_sun",
            npc_name="Test Initiate")
        self.assertTrue(ok)
        hits = orgs.organisations_for_npc_name(self.camp, "Test Initiate")
        self.assertEqual(hits, [])

    def test_organisations_in_city_and_kingdom(self):
        in_frand = orgs.organisations_in_city(self.camp, "frand")
        in_oblitus = orgs.organisations_in_kingdom(self.camp, "oblitus")
        names = {o.key for o in in_frand}
        self.assertIn("brotherhood_of_glorious_sun", names)
        names = {o.key for o in in_oblitus}
        self.assertIn("brotherhood_of_glorious_sun", names)

    def test_organisation_round_trip_serialisation(self):
        orgs.sync_organisations_to_campaign(self.camp)
        s = json.dumps(self.camp.organisations_data)
        camp2 = _FakeCampaign()
        camp2.organisations_data = json.loads(s)
        rt = orgs.ensure_organisations_on_campaign(camp2)
        self.assertEqual(len(rt), len(orgs.SEED_ORGANISATIONS))
        # Same names + member counts
        for orig, restored in zip(orgs.SEED_ORGANISATIONS, rt):
            self.assertEqual(orig.key, restored.key)
            self.assertEqual(len(orig.members), len(restored.members))


# --------------------------------------------------------------------- #
# Novus Somnium build integration
# --------------------------------------------------------------------- #
class TestNovusSomniumPreseed(unittest.TestCase):
    """build_novus_somnium should now carry kingdoms + organisations."""
    def test_build_has_seeded_kingdoms(self):
        from data.novus_somnium import build_novus_somnium
        camp = build_novus_somnium()
        self.assertGreaterEqual(len(camp.kingdoms_data), 5)
        keys = {k.get("key") for k in camp.kingdoms_data}
        for required in ("tarmaas", "fundarla", "smardu",
                          "aterterra", "oblitus"):
            self.assertIn(required, keys)

    def test_build_has_seeded_organisations(self):
        from data.novus_somnium import build_novus_somnium
        camp = build_novus_somnium()
        self.assertGreaterEqual(len(camp.organisations_data), 1)
        keys = {o.get("key") for o in camp.organisations_data}
        self.assertIn("brotherhood_of_glorious_sun", keys)


if __name__ == "__main__":
    unittest.main()
