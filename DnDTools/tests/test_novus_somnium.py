"""Phase 6e — Novus Somnium starter campaign tests."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest
import tempfile
import json

from data.actors import ActorRegistry
from data import novus_somnium as ns
from data.campaign import Campaign


class TestBuild(unittest.TestCase):
    def test_build_returns_campaign(self):
        c = ns.build_novus_somnium()
        self.assertIsInstance(c, Campaign)
        self.assertEqual(c.name, "Novus Somnium")
        self.assertTrue(c.description)

    def test_has_expected_areas(self):
        c = ns.build_novus_somnium()
        names = {a.name for a in c.areas}
        self.assertIn("Arenhold, the Port-City", names)
        self.assertIn("Vardun Keep", names)
        self.assertIn("Silverbough Forest", names)

    def test_has_encounters(self):
        c = ns.build_novus_somnium()
        self.assertGreaterEqual(len(c.encounters), 3)
        for e in c.encounters:
            self.assertTrue(e.name)
            self.assertTrue(e.description)

    def test_encounters_reference_areas(self):
        c = ns.build_novus_somnium()
        area_names = {a.name for a in c.areas}
        for e in c.encounters:
            self.assertIn(e.area_name, area_names,
                          f"{e.name} points at unknown area {e.area_name!r}")

    def test_has_notes(self):
        c = ns.build_novus_somnium()
        self.assertGreaterEqual(len(c.notes), 1)

    def test_current_area_valid(self):
        c = ns.build_novus_somnium()
        area_names = {a.name for a in c.areas}
        self.assertIn(c.current_area, area_names)


class TestSeedActors(unittest.TestCase):
    def test_seed_creates_actors(self):
        reg = ActorRegistry()
        actors = ns.seed_novus_somnium_actors(registry=reg)
        self.assertGreaterEqual(len(actors), 5)
        names = {a.name for a in actors}
        self.assertIn("Lady Mira Vardun", names)
        self.assertIn("Harbourmaster Jolan Ves", names)

    def test_seed_is_idempotent(self):
        reg = ActorRegistry()
        ns.seed_novus_somnium_actors(registry=reg)
        n1 = len(reg)
        ns.seed_novus_somnium_actors(registry=reg)
        self.assertEqual(len(reg), n1)

    def test_includes_vehicle(self):
        reg = ActorRegistry()
        ns.seed_novus_somnium_actors(registry=reg)
        stormchaser = reg.get_by_name("The Stormchaser")
        self.assertIsNotNone(stormchaser)
        self.assertEqual(stormchaser.kind, "vehicle")

    def test_respects_preexisting_actor(self):
        """If a name-collision actor already exists, we don't create a
        second entry with a new id."""
        reg = ActorRegistry()
        pre = reg.create("Lady Mira Vardun", kind="hero",
                          notes="My own version")
        actors = ns.seed_novus_somnium_actors(registry=reg)
        mira = reg.get_by_name("Lady Mira Vardun")
        self.assertIs(mira, pre)
        self.assertEqual(mira.notes, "My own version")


class TestEnsureDefaultCampaign(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.registry = ActorRegistry()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_creates_on_fresh_dir(self):
        path = ns.ensure_default_campaign(campaigns_dir=self.tmpdir,
                                            registry=self.registry)
        self.assertTrue(os.path.isfile(path))
        self.assertTrue(path.endswith("Novus Somnium.json"))

    def test_file_is_valid_campaign_json(self):
        path = ns.ensure_default_campaign(campaigns_dir=self.tmpdir,
                                            registry=self.registry)
        with open(path) as f:
            data = json.load(f)
        self.assertEqual(data["name"], "Novus Somnium")
        self.assertGreaterEqual(len(data.get("areas", [])), 3)

    def test_idempotent_no_overwrite(self):
        """If the file already exists we don't overwrite it — the DM's
        edits survive the next startup."""
        path = ns.ensure_default_campaign(campaigns_dir=self.tmpdir,
                                            registry=self.registry)
        # Mutate the file to prove it's kept
        with open(path) as f:
            data = json.load(f)
        data["description"] = "HANDS OFF"
        with open(path, "w") as f:
            json.dump(data, f)

        ns.ensure_default_campaign(campaigns_dir=self.tmpdir,
                                     registry=self.registry)
        with open(path) as f:
            data2 = json.load(f)
        self.assertEqual(data2["description"], "HANDS OFF")

    def test_actors_seeded(self):
        ns.ensure_default_campaign(campaigns_dir=self.tmpdir,
                                     registry=self.registry)
        self.assertIsNotNone(self.registry.get_by_name("Lady Mira Vardun"))
        self.assertIsNotNone(self.registry.get_by_name("The Stormchaser"))


if __name__ == "__main__":
    unittest.main()
