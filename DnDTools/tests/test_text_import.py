"""Phase 12a — bulk text import tests."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest
import tempfile

from data.world import World
from data.text_import import (
    import_text, import_file, ImportReport,
    _tokenize, _detect_section, _split_npc_qualifier,
    _infer_location_type,
)


SAMPLE = """\
## Locations
- Arenhold (town): Port-city on Greysea, trade hub.
    Tags: coast, merchants
- Vardun Keep (fort): Crumbling wall, goblin probes.
    Tags: ruins, military
- Silverbough Forest (wilderness): Fey-touched.

## NPCs
- Lady Mira Vardun (Castellan, Vardun Keep): Stern but fair.
    Tags: noble
- Harbourmaster Jolan Ves (Harbourmaster, Arenhold): Tracks every ship.
- Captain Arys Tarn (Captain @ Tarn Trading House): Ruthless merchant.

## Quests
- Goblin Investigation: Find the goblin source near Vardun Keep.

## Notes
- World tone: gritty frontier.
"""


class TestSectionDetection(unittest.TestCase):
    def test_known_aliases(self):
        for alias, expected in (
            ("Locations", "locations"),
            ("CITIES", "locations"),
            ("Settlements", "locations"),
            ("NPCs", "npcs"),
            ("Characters", "npcs"),
            ("Quests", "quests"),
            ("Hooks", "quests"),
            ("Notes", "notes"),
            ("Lore", "notes"),
        ):
            self.assertEqual(_detect_section(alias), expected,
                              f"alias {alias!r}")

    def test_unknown_returns_none(self):
        self.assertIsNone(_detect_section("Inventory"))


class TestQualifierParsing(unittest.TestCase):
    def test_occupation_only(self):
        self.assertEqual(_split_npc_qualifier("Castellan"),
                          ("Castellan", "", ""))

    def test_occupation_and_location(self):
        self.assertEqual(_split_npc_qualifier("Castellan, Vardun Keep"),
                          ("Castellan", "Vardun Keep", ""))

    def test_at_sign_is_faction(self):
        self.assertEqual(_split_npc_qualifier("Captain @ Tarn House"),
                          ("Captain", "", "Tarn House"))


class TestLocationTypeInference(unittest.TestCase):
    def test_recognises_keywords(self):
        self.assertEqual(_infer_location_type("town"), "town")
        self.assertEqual(_infer_location_type("Capital city"), "capital")
        self.assertEqual(_infer_location_type("ruined fort"), "fort")
        self.assertEqual(_infer_location_type("ancient cave"), "cave")

    def test_falls_back_to_region(self):
        self.assertEqual(_infer_location_type("planet"), "region")
        self.assertEqual(_infer_location_type(""), "region")


class TestTokenize(unittest.TestCase):
    def test_groups_into_sections(self):
        tokens = _tokenize(SAMPLE)
        self.assertEqual(len(tokens["locations"]), 3)
        self.assertEqual(len(tokens["npcs"]), 3)
        self.assertEqual(len(tokens["quests"]), 1)
        self.assertEqual(len(tokens["notes"]), 1)

    def test_continuation_lines_extend_description(self):
        text = "## Locations\n- A: First.\n  Continuing.\n"
        loc = _tokenize(text)["locations"][0]
        self.assertIn("Continuing", loc.description)
        self.assertIn("First", loc.description)

    def test_tags_continuation_line(self):
        text = "## Locations\n- A (town): X.\n    Tags: a, b, c\n"
        loc = _tokenize(text)["locations"][0]
        self.assertEqual(loc.tags, ["a", "b", "c"])


class TestImportText(unittest.TestCase):
    def test_creates_locations(self):
        w = World()
        r = import_text(w, SAMPLE)
        self.assertEqual(r.locations_created, 3)
        self.assertEqual(len(w.locations), 3)
        names = sorted(loc.name for loc in w.locations.values())
        self.assertEqual(names,
                          ["Arenhold", "Silverbough Forest", "Vardun Keep"])

    def test_assigns_loctype(self):
        w = World()
        import_text(w, SAMPLE)
        types = {loc.name: loc.location_type
                  for loc in w.locations.values()}
        self.assertEqual(types["Arenhold"], "town")
        self.assertEqual(types["Vardun Keep"], "fort")
        self.assertEqual(types["Silverbough Forest"], "wilderness")

    def test_assigns_tags(self):
        w = World()
        import_text(w, SAMPLE)
        ar = next(l for l in w.locations.values() if l.name == "Arenhold")
        self.assertEqual(ar.tags, ["coast", "merchants"])

    def test_creates_npcs_with_links(self):
        w = World()
        import_text(w, SAMPLE)
        self.assertEqual(len(w.npcs), 3)
        mira = next(n for n in w.npcs.values()
                    if n.name.startswith("Lady Mira"))
        self.assertEqual(mira.occupation, "Castellan")
        # Location hint resolved to the Vardun Keep loc id
        self.assertTrue(mira.location_id)
        vardun = w.locations[mira.location_id]
        self.assertEqual(vardun.name, "Vardun Keep")

    def test_npc_faction_via_at(self):
        w = World()
        import_text(w, SAMPLE)
        arys = next(n for n in w.npcs.values()
                    if n.name.startswith("Captain Arys"))
        self.assertEqual(arys.occupation, "Captain")
        self.assertEqual(arys.faction, "Tarn Trading House")

    def test_creates_quests(self):
        w = World()
        import_text(w, SAMPLE)
        self.assertEqual(len(w.quests), 1)
        q = next(iter(w.quests.values()))
        self.assertEqual(q.name, "Goblin Investigation")
        self.assertIn("goblin", q.description.lower())

    def test_idempotent_on_reimport(self):
        w = World()
        r1 = import_text(w, SAMPLE)
        r2 = import_text(w, SAMPLE)
        self.assertEqual(r1.locations_created, 3)
        self.assertEqual(r2.locations_created, 0)
        self.assertEqual(r2.locations_updated, 3)
        self.assertEqual(len(w.locations), 3)
        self.assertEqual(len(w.npcs), 3)

    def test_update_merges_tags(self):
        w = World()
        import_text(w, SAMPLE)
        # Re-import with extra tag for Arenhold
        more = ("## Locations\n"
                "- Arenhold (town): Port-city.\n"
                "    Tags: capital, coast\n")
        import_text(w, more)
        ar = next(l for l in w.locations.values() if l.name == "Arenhold")
        # Existing 'coast' kept, new 'capital' added; 'merchants' kept
        self.assertIn("coast", ar.tags)
        self.assertIn("capital", ar.tags)
        self.assertIn("merchants", ar.tags)

    def test_warning_for_unresolved_location_hint(self):
        w = World()
        text = ("## NPCs\n"
                "- Solo NPC (Wanderer, Atlantis): Lost soul.\n")
        r = import_text(w, text)
        self.assertEqual(r.npcs_created, 1)
        self.assertTrue(any("Atlantis" in w for w in r.warnings))

    def test_empty_text(self):
        w = World()
        r = import_text(w, "")
        self.assertEqual(r.total_changes, 0)

    def test_summary_string(self):
        w = World()
        r = import_text(w, SAMPLE)
        s = r.summary()
        self.assertIn("locations", s)
        self.assertIn("NPCs", s)


class TestImportFile(unittest.TestCase):
    def test_reads_from_file(self):
        with tempfile.NamedTemporaryFile("w", suffix=".md",
                                            delete=False) as tf:
            tf.write(SAMPLE)
            path = tf.name
        try:
            w = World()
            r = import_file(w, path)
            self.assertEqual(r.locations_created, 3)
            self.assertEqual(r.npcs_created, 3)
        finally:
            os.unlink(path)

    def test_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            import_file(World(), "/nope/missing.md")


class TestPlainBulletWithoutQualifier(unittest.TestCase):
    def test_plain_name_only_creates_with_default(self):
        w = World()
        r = import_text(w, "## Locations\n- Lonely Hill\n")
        self.assertEqual(r.locations_created, 1)
        loc = next(iter(w.locations.values()))
        self.assertEqual(loc.name, "Lonely Hill")
        self.assertEqual(loc.location_type, "region")


if __name__ == "__main__":
    unittest.main()
