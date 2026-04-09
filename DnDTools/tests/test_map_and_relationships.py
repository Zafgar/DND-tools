"""Tests for map pin management, hero relationships, and campaign serialization."""
import sys
import os
import json
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import unittest
from data.world import (
    World, MapPin, MAP_PIN_TYPES, Location,
    add_pin, remove_pin, get_pin_by_id, get_pins_at_location,
    get_pins_by_type, get_visible_pins, search_pins,
    save_world, load_world, generate_id, add_location, add_npc,
)
from data.campaign import (
    Campaign, PartyMember, CampaignNote, HeroRelationship,
    save_campaign, load_campaign,
)


class TestMapPin(unittest.TestCase):
    def setUp(self):
        self.world = World(name="Test World")

    def test_add_pin(self):
        pin = add_pin(self.world, "Marker 1", "poi", 25.0, 75.0)
        self.assertEqual(len(self.world.map_pins), 1)
        self.assertEqual(pin.name, "Marker 1")
        self.assertEqual(pin.pin_type, "poi")
        self.assertEqual(pin.map_x, 25.0)
        self.assertEqual(pin.map_y, 75.0)
        self.assertTrue(pin.id.startswith("pin_"))

    def test_add_multiple_pins(self):
        add_pin(self.world, "Pin A", "note")
        add_pin(self.world, "Pin B", "danger")
        add_pin(self.world, "Pin C", "treasure")
        self.assertEqual(len(self.world.map_pins), 3)
        # Each pin should have a unique ID
        ids = [p.id for p in self.world.map_pins]
        self.assertEqual(len(set(ids)), 3)

    def test_remove_pin(self):
        pin = add_pin(self.world, "To Remove", "note")
        pid = pin.id
        self.assertEqual(len(self.world.map_pins), 1)
        remove_pin(self.world, pid)
        self.assertEqual(len(self.world.map_pins), 0)

    def test_remove_nonexistent_pin(self):
        add_pin(self.world, "Stay", "note")
        remove_pin(self.world, "nonexistent_id")
        self.assertEqual(len(self.world.map_pins), 1)

    def test_get_pin_by_id(self):
        pin = add_pin(self.world, "Find Me", "quest")
        found = get_pin_by_id(self.world, pin.id)
        self.assertIsNotNone(found)
        self.assertEqual(found.name, "Find Me")
        # Non-existent
        self.assertIsNone(get_pin_by_id(self.world, "fake_id"))

    def test_get_pins_at_location(self):
        loc = add_location(self.world, "Town", "city")
        add_pin(self.world, "Pin A", "note", location_id=loc.id)
        add_pin(self.world, "Pin B", "danger", location_id=loc.id)
        add_pin(self.world, "Pin C", "note", location_id="other_loc")
        result = get_pins_at_location(self.world, loc.id)
        self.assertEqual(len(result), 2)

    def test_get_pins_by_type(self):
        add_pin(self.world, "A", "note")
        add_pin(self.world, "B", "danger")
        add_pin(self.world, "C", "note")
        notes = get_pins_by_type(self.world, "note")
        self.assertEqual(len(notes), 2)
        dangers = get_pins_by_type(self.world, "danger")
        self.assertEqual(len(dangers), 1)

    def test_get_visible_pins(self):
        p1 = add_pin(self.world, "Visible", "note")
        p2 = add_pin(self.world, "Hidden", "note")
        p2.visible = False
        visible = get_visible_pins(self.world)
        self.assertEqual(len(visible), 1)
        self.assertEqual(visible[0].name, "Visible")

    def test_search_pins(self):
        add_pin(self.world, "Dragon Lair", "danger", description="Red dragon lives here")
        add_pin(self.world, "Treasure Cave", "treasure", notes="Gold and gems")
        results = search_pins(self.world, "dragon")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "Dragon Lair")
        results2 = search_pins(self.world, "gold")
        self.assertEqual(len(results2), 1)
        self.assertEqual(results2[0].name, "Treasure Cave")

    def test_pin_types_constant(self):
        self.assertIn("note", MAP_PIN_TYPES)
        self.assertIn("poi", MAP_PIN_TYPES)
        self.assertIn("danger", MAP_PIN_TYPES)
        self.assertIn("treasure", MAP_PIN_TYPES)
        self.assertIn("quest", MAP_PIN_TYPES)
        self.assertIn("camp", MAP_PIN_TYPES)
        self.assertIn("custom", MAP_PIN_TYPES)
        for pt in MAP_PIN_TYPES.values():
            self.assertIn("icon", pt)
            self.assertIn("color", pt)
            self.assertIn("label", pt)

    def test_pin_links(self):
        pin = add_pin(self.world, "Link Pin", "note")
        pin.links = ["https://example.com", "/docs/notes.txt"]
        self.assertEqual(len(pin.links), 2)
        self.assertTrue(pin.links[0].startswith("http"))


class TestMapPinSerialization(unittest.TestCase):
    def test_save_load_pins(self):
        world = World(name="Pin World")
        pin = add_pin(world, "Test Pin", "danger", 30.5, 60.2,
                       description="A dangerous area",
                       notes="Watch out for traps")
        pin.links = ["https://example.com/map"]
        pin.npc_ids = ["npc_1"]

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            save_world(world, path)
            loaded = load_world(path)
            self.assertEqual(len(loaded.map_pins), 1)
            lp = loaded.map_pins[0]
            self.assertEqual(lp.name, "Test Pin")
            self.assertEqual(lp.pin_type, "danger")
            self.assertAlmostEqual(lp.map_x, 30.5)
            self.assertAlmostEqual(lp.map_y, 60.2)
            self.assertEqual(lp.description, "A dangerous area")
            self.assertEqual(lp.notes, "Watch out for traps")
            self.assertEqual(lp.links, ["https://example.com/map"])
            self.assertEqual(lp.npc_ids, ["npc_1"])
            self.assertTrue(lp.visible)
        finally:
            os.unlink(path)

    def test_backward_compat_no_pins(self):
        """Loading a world without map_pins should default to empty list."""
        data = {"name": "Old World", "locations": {}, "npcs": {}, "quests": {},
                "next_id": 1, "map_routes": [], "map_image_path": "", "map_positions": {}}
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            json.dump(data, f)
            path = f.name
        try:
            loaded = load_world(path)
            self.assertEqual(loaded.map_pins, [])
        finally:
            os.unlink(path)


class TestHeroRelationship(unittest.TestCase):
    def test_create_relationship(self):
        rel = HeroRelationship(
            target_name="Gandalf",
            target_id="npc_1",
            target_type="npc",
            attitude="friendly",
            description="Trusted mentor",
        )
        self.assertEqual(rel.target_name, "Gandalf")
        self.assertEqual(rel.target_type, "npc")
        self.assertEqual(rel.attitude, "friendly")
        self.assertEqual(rel.description, "Trusted mentor")

    def test_default_values(self):
        rel = HeroRelationship()
        self.assertEqual(rel.target_name, "")
        self.assertEqual(rel.target_type, "npc")
        self.assertEqual(rel.attitude, "neutral")
        self.assertEqual(rel.notes, "")

    def test_hero_type_relationship(self):
        rel = HeroRelationship(
            target_name="Legolas",
            target_type="hero",
            attitude="allied",
        )
        self.assertEqual(rel.target_type, "hero")
        self.assertEqual(rel.attitude, "allied")


class TestPartyMemberRelationshipsAndLinks(unittest.TestCase):
    def test_member_has_relationships(self):
        member = PartyMember()
        self.assertEqual(member.relationships, [])
        member.relationships.append(HeroRelationship(
            target_name="Barkeep",
            target_type="npc",
            attitude="friendly",
        ))
        self.assertEqual(len(member.relationships), 1)

    def test_member_has_links(self):
        member = PartyMember()
        self.assertEqual(member.links, [])
        member.links.append("https://dndbeyond.com/characters/12345")
        member.links.append("/docs/backstory.txt")
        self.assertEqual(len(member.links), 2)

    def test_campaign_note_links_and_pinned(self):
        note = CampaignNote(text="Important session note", pinned=True)
        note.links = ["https://example.com/session1"]
        self.assertTrue(note.pinned)
        self.assertEqual(len(note.links), 1)


class TestCampaignSerialization(unittest.TestCase):
    def test_save_load_hero_relationships(self):
        campaign = Campaign(name="Test Campaign")
        member = PartyMember(
            hero_data={"name": "Aragorn", "character_class": "Ranger", "character_level": 10},
        )
        member.relationships = [
            HeroRelationship(target_name="Gandalf", target_id="npc_1",
                             target_type="npc", attitude="friendly",
                             description="Trusted advisor"),
            HeroRelationship(target_name="Legolas", target_type="hero",
                             attitude="allied", description="Battle companion"),
        ]
        member.links = ["https://example.com/sheet", "/docs/backstory.md"]
        campaign.party.append(member)

        note = CampaignNote(text="Session 1 notes", pinned=True)
        note.links = ["https://example.com/recap"]
        campaign.notes.append(note)

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            save_campaign(campaign, path)
            loaded = load_campaign(path)

            self.assertEqual(len(loaded.party), 1)
            lm = loaded.party[0]
            self.assertEqual(len(lm.relationships), 2)
            self.assertEqual(lm.relationships[0].target_name, "Gandalf")
            self.assertEqual(lm.relationships[0].attitude, "friendly")
            self.assertEqual(lm.relationships[0].description, "Trusted advisor")
            self.assertEqual(lm.relationships[1].target_type, "hero")
            self.assertEqual(lm.relationships[1].target_name, "Legolas")
            self.assertEqual(lm.links, ["https://example.com/sheet", "/docs/backstory.md"])

            self.assertEqual(len(loaded.notes), 1)
            self.assertTrue(loaded.notes[0].pinned)
            self.assertEqual(loaded.notes[0].links, ["https://example.com/recap"])
        finally:
            os.unlink(path)

    def test_backward_compat_no_relationships(self):
        """Loading a campaign without relationships/links fields should default to empty."""
        data = {
            "name": "Old Campaign",
            "party": [{"hero_data": {"name": "OldHero"}}],
            "notes": [{"text": "Old note", "timestamp": "", "category": "general"}],
        }
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            json.dump(data, f)
            path = f.name
        try:
            loaded = load_campaign(path)
            self.assertEqual(len(loaded.party), 1)
            self.assertEqual(loaded.party[0].relationships, [])
            self.assertEqual(loaded.party[0].links, [])
            self.assertEqual(loaded.notes[0].links, [])
            self.assertFalse(loaded.notes[0].pinned)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
