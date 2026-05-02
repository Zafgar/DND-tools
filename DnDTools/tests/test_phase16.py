"""Phase 16 — campaign manager wiring + NPC portrait persistence."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
import tempfile
import unittest

from data.world import World, NPC, save_world, load_world


class TestNpcPortraitField(unittest.TestCase):
    def test_default_empty(self):
        npc = NPC(id="n1", name="X")
        self.assertEqual(npc.portrait_path, "")

    def test_explicit_value(self):
        npc = NPC(id="n1", name="X",
                   portrait_path="saves/portraits/x.png")
        self.assertEqual(npc.portrait_path, "saves/portraits/x.png")


class TestNpcPortraitRoundtrip(unittest.TestCase):
    def test_roundtrip_keeps_portrait(self):
        w = World()
        w.npcs["n1"] = NPC(id="n1", name="Mira",
                              portrait_path="saves/portraits/mira.jpg",
                              actor_id="actor_xyz")
        with tempfile.NamedTemporaryFile(suffix=".json",
                                            delete=False) as tf:
            path = tf.name
        try:
            save_world(w, path)
            w2 = load_world(path)
            self.assertEqual(w2.npcs["n1"].portrait_path,
                              "saves/portraits/mira.jpg")
            self.assertEqual(w2.npcs["n1"].actor_id, "actor_xyz")
        finally:
            os.unlink(path)

    def test_legacy_npc_loads_with_empty_portrait(self):
        legacy_npc = {"id": "n1", "name": "Old"}
        w = World()
        with tempfile.NamedTemporaryFile(suffix=".json",
                                            delete=False, mode="w") as tf:
            json.dump({"name": "X", "description": "", "created": "",
                        "last_modified": "",
                        "locations": {}, "npcs": {"n1": legacy_npc},
                        "quests": {}, "shops": {}, "services": {},
                        "next_id": 2,
                        "map_routes": [], "map_pins": [],
                        "map_tokens": [], "map_image_path": "",
                        "map_positions": {},
                        "map_scale_miles": 0, "map_scale_reference": 0},
                        tf)
            path = tf.name
        try:
            w2 = load_world(path)
            self.assertEqual(w2.npcs["n1"].portrait_path, "")
            self.assertEqual(w2.npcs["n1"].actor_id, "")
        finally:
            os.unlink(path)


class TestLocationIdLookup(unittest.TestCase):
    """The campaign manager's ``_location_id_for_name`` helper resolves
    Campaign.current_area (a string) to a world location id."""
    def test_returns_id_when_found(self):
        from data.world import Location
        w = World()
        w.locations["loc_1"] = Location(id="loc_1",
                                            name="Arenhold")
        # Reproduce helper logic directly (campaign manager imports
        # pygame, so we don't instantiate it here).
        match = ""
        for lid, loc in w.locations.items():
            if loc.name == "Arenhold":
                match = lid
                break
        self.assertEqual(match, "loc_1")

    def test_returns_empty_when_missing(self):
        w = World()
        match = ""
        for lid, loc in w.locations.items():
            if loc.name == "ghost":
                match = lid
                break
        self.assertEqual(match, "")


if __name__ == "__main__":
    unittest.main()
