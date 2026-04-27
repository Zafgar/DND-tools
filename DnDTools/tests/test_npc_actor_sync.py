"""Phase 11e — NPC ↔ Actor sync + searchable dropdown tests."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest

from data.world import World, NPC, Location
from data.actors import ActorRegistry
from data.npc_actor_sync import (
    ensure_actor_for_npc, sync_npc_changes_to_actor, unlink_npc,
    search_npcs, search_actors, search_locations,
    search_actors_for_npc_link,
)


def _world(*npcs, locs=None):
    w = World()
    for n in npcs:
        w.npcs[n.id] = n
    for loc in locs or []:
        w.locations[loc.id] = loc
    return w


class TestEnsureActorForNPC(unittest.TestCase):
    def test_creates_actor_for_unlinked_npc(self):
        npc = NPC(id="n1", name="Mira Vardun",
                   notes="Vardun Keep castellan",
                   tags=["fort", "noble"])
        w = _world(npc)
        reg = ActorRegistry()
        actor = ensure_actor_for_npc(w, "n1", reg)
        self.assertIsNotNone(actor)
        self.assertEqual(actor.kind, "npc")
        self.assertEqual(actor.name, "Mira Vardun")
        self.assertIn("fort", actor.tags)
        self.assertEqual(npc.actor_id, actor.id)

    def test_returns_existing_actor_on_repeat(self):
        npc = NPC(id="n1", name="Jolan")
        w = _world(npc)
        reg = ActorRegistry()
        a1 = ensure_actor_for_npc(w, "n1", reg)
        a2 = ensure_actor_for_npc(w, "n1", reg)
        self.assertIs(a1, a2)
        self.assertEqual(len(reg), 1)

    def test_unknown_npc_returns_none(self):
        self.assertIsNone(ensure_actor_for_npc(World(), "nope",
                                                  ActorRegistry()))


class TestSyncNpcChanges(unittest.TestCase):
    def test_pushes_name_notes_tags(self):
        npc = NPC(id="n1", name="Old Name")
        w = _world(npc)
        reg = ActorRegistry()
        actor = ensure_actor_for_npc(w, "n1", reg)

        npc.name = "New Name"
        npc.notes = "Updated DM notes"
        npc.tags = ["merchant", "shady"]
        sync_npc_changes_to_actor(npc, reg)
        self.assertEqual(actor.name, "New Name")
        self.assertEqual(actor.notes, "Updated DM notes")
        self.assertEqual(set(actor.tags), {"merchant", "shady"})

    def test_unlinked_npc_returns_none(self):
        npc = NPC(id="n1", name="X")
        self.assertIsNone(sync_npc_changes_to_actor(npc, ActorRegistry()))

    def test_unlink_clears_actor_id(self):
        npc = NPC(id="n1", name="X")
        w = _world(npc)
        reg = ActorRegistry()
        ensure_actor_for_npc(w, "n1", reg)
        self.assertTrue(unlink_npc(npc))
        self.assertEqual(npc.actor_id, "")
        self.assertFalse(unlink_npc(npc))   # already unlinked


class TestSearchNPCs(unittest.TestCase):
    def setUp(self):
        self.w = _world(
            NPC(id="n1", name="Lady Mira Vardun",
                  occupation="Castellan", tags=["fort", "noble"]),
            NPC(id="n2", name="Jolan Ves",
                  occupation="Harbourmaster", tags=["docks"]),
            NPC(id="n3", name="Captain Arys Tarn",
                  faction="Tarn Trading House"),
        )

    def test_empty_query_returns_all(self):
        self.assertEqual(len(search_npcs(self.w)), 3)

    def test_name_match(self):
        r = search_npcs(self.w, "mira")
        self.assertEqual(len(r), 1)
        self.assertEqual(r[0].id, "n1")

    def test_occupation_match(self):
        r = search_npcs(self.w, "harbour")
        self.assertEqual([n.id for n in r], ["n2"])

    def test_tag_match(self):
        r = search_npcs(self.w, "noble")
        self.assertEqual([n.id for n in r], ["n1"])

    def test_faction_match(self):
        r = search_npcs(self.w, "tarn")
        self.assertEqual([n.id for n in r], ["n3"])

    def test_sorted_alphabetically(self):
        r = search_npcs(self.w, "")
        names = [n.name for n in r]
        self.assertEqual(names, sorted(names, key=str.lower))


class TestSearchActors(unittest.TestCase):
    def setUp(self):
        self.reg = ActorRegistry()
        self.reg.create("Alara", kind="hero", tags=["pc"])
        self.reg.create("Mira", kind="npc")
        self.reg.create("Stormchaser", kind="vehicle",
                          notes="Brig in the harbour")

    def test_kind_filter(self):
        npcs = search_actors(self.reg, "", kind="npc")
        self.assertEqual([a.name for a in npcs], ["Mira"])

    def test_query_matches_name(self):
        r = search_actors(self.reg, "alara")
        self.assertEqual([a.name for a in r], ["Alara"])

    def test_query_matches_notes(self):
        r = search_actors(self.reg, "harbour")
        self.assertEqual([a.name for a in r], ["Stormchaser"])

    def test_unknown_kind_falls_back_to_all(self):
        r = search_actors(self.reg, "", kind="dragonborn")
        self.assertEqual(len(r), 3)


class TestSearchLocations(unittest.TestCase):
    def setUp(self):
        self.w = _world(
            locs=[
                Location(id="l1", name="Arenhold", location_type="town",
                          description="Port-city.", tags=["coast"]),
                Location(id="l2", name="Vardun Keep", location_type="fort"),
                Location(id="l3", name="Silverbough Forest",
                          location_type="wilderness"),
            ],
        )

    def test_query(self):
        r = search_locations(self.w, "silver")  # matches Silverbough
        self.assertEqual([loc.id for loc in r], ["l3"])

    def test_type_filter(self):
        r = search_locations(self.w, "", location_type="fort")
        self.assertEqual([loc.id for loc in r], ["l2"])

    def test_combined(self):
        r = search_locations(self.w, "port", location_type="town")
        self.assertEqual([loc.id for loc in r], ["l1"])


class TestActorPickerForNPC(unittest.TestCase):
    def test_excludes_existing_link(self):
        npc = NPC(id="n1", name="Mira")
        w = _world(npc)
        reg = ActorRegistry()
        ensure_actor_for_npc(w, "n1", reg)
        # Add another candidate
        reg.create("Jolan", kind="npc")
        results = search_actors_for_npc_link(w, reg, "",
                                                exclude_npc_id="n1")
        names = [a.name for a in results]
        self.assertIn("Jolan", names)
        self.assertNotIn("Mira", names)


class TestNPCSerializationKeepsActorId(unittest.TestCase):
    def test_actor_id_field_default_empty(self):
        npc = NPC(id="n1", name="X")
        self.assertEqual(npc.actor_id, "")

    def test_actor_id_persists_on_dataclass(self):
        npc = NPC(id="n1", name="X", actor_id="actor_abc")
        self.assertEqual(npc.actor_id, "actor_abc")


if __name__ == "__main__":
    unittest.main()
