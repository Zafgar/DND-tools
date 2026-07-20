"""Phase 47 — Talo Baenrahel playable stat blocks are in the library and
wired to their NPCs, and their core mechanics are engine-legal."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import unittest

from data.library import MonsterLibrary
from data.novus_somnium import build_novus_somnium
from engine.entities import Entity


BAENRAHEL = [
    ("Velve Dro Crossbow Sentry", 2.0),
    ("Velve Dro Warrior", 3.0),
    ("Baenrahel Aether Vanguard", 7.0),
    ("Baenrahel Blood-Weaver", 8.0),
    ("Elarae Baenrahel", 14.0),
    ("Dravin Baenrahel", 14.0),
]


class TestLibraryHasBaenrahel(unittest.TestCase):
    def setUp(self):
        self.lib = MonsterLibrary()

    def test_all_present_with_correct_cr(self):
        for name, cr in BAENRAHEL:
            m = self.lib.get_monster(name)
            self.assertEqual(m.challenge_rating, cr, name)

    def test_instantiate_as_entities(self):
        for name, _ in BAENRAHEL:
            e = Entity(self.lib.get_monster(name), 0, 0, is_player=False)
            self.assertGreater(e.max_hp, 0, name)
            self.assertGreater(e.armor_class, 0, name)

    def test_bosses_are_legendary(self):
        for name in ("Elarae Baenrahel", "Dravin Baenrahel"):
            m = self.lib.get_monster(name)
            self.assertEqual(m.legendary_action_count, 3, name)
            self.assertEqual(m.legendary_resistance_count, 3, name)

    def test_elarae_casts(self):
        m = self.lib.get_monster("Elarae Baenrahel")
        self.assertTrue(m.spells_known)
        self.assertEqual(m.spell_save_dc, 19)
        self.assertTrue(any(c.name == "Fire Bolt" for c in m.cantrips))

    def test_magic_resistance_wired_for_engine(self):
        # Engine reads has_feature("magic_resistance").
        for name in ("Elarae Baenrahel", "Dravin Baenrahel",
                     "Baenrahel Aether Vanguard", "Baenrahel Blood-Weaver"):
            e = Entity(self.lib.get_monster(name), 0, 0, is_player=False)
            self.assertTrue(e.has_feature("magic_resistance"), name)

    def test_vanguard_is_mage_slayer(self):
        e = Entity(self.lib.get_monster("Baenrahel Aether Vanguard"),
                   0, 0, is_player=False)
        self.assertTrue(e.has_feature("mage_slayer"))

    def test_multiattack_and_poison_rider(self):
        m = self.lib.get_monster("Dravin Baenrahel")
        ma = next(a for a in m.actions if a.is_multiattack)
        self.assertEqual(ma.multiattack_count, 4)
        scim = next(a for a in m.actions if a.name == "Velve Dro Scimitar")
        self.assertEqual(scim.applies_condition, "Poisoned")
        self.assertEqual(scim.condition_dc, 17)

    def test_legendary_resistance_initialized_on_entity(self):
        e = Entity(self.lib.get_monster("Elarae Baenrahel"), 0, 0,
                   is_player=False)
        self.assertEqual(e.legendary_resistances_left, 3)


class TestNpcsWiredToStatBlocks(unittest.TestCase):
    def test_elarae_and_dravin_point_to_monsters(self):
        camp = build_novus_somnium()
        npcs = camp.world_data["npcs"]
        self.assertEqual(npcs["npc_elarae"]["stat_source"],
                         "monster:Elarae Baenrahel")
        self.assertEqual(npcs["npc_dravin"]["stat_source"],
                         "monster:Dravin Baenrahel")

    def test_stat_sources_resolve_in_library(self):
        lib = MonsterLibrary()
        camp = build_novus_somnium()
        for nid in ("npc_elarae", "npc_dravin"):
            src = camp.world_data["npcs"][nid]["stat_source"]
            name = src.split(":", 1)[1]
            self.assertIsNotNone(lib.get_monster(name))


class TestWhitestoneConstructs(unittest.TestCase):
    def setUp(self):
        self.lib = MonsterLibrary()

    def test_present_with_correct_cr(self):
        for name, cr in [("Automata Trooper", 4.0),
                         ("Whitestone Colossus", 14.0)]:
            self.assertEqual(self.lib.get_monster(name).challenge_rating, cr)

    def test_constructs_immune_to_poison_and_charm(self):
        from engine.entities import Entity
        for name in ("Automata Trooper", "Whitestone Colossus"):
            m = self.lib.get_monster(name)
            self.assertIn("poison", m.damage_immunities)
            self.assertIn("Charmed", m.condition_immunities)
            Entity(m, 0, 0, is_player=False)  # must instantiate

    def test_colossus_is_legendary(self):
        m = self.lib.get_monster("Whitestone Colossus")
        self.assertEqual(m.legendary_action_count, 3)


class TestZertathBosses(unittest.TestCase):
    def setUp(self):
        self.lib = MonsterLibrary()

    def test_present_with_correct_cr(self):
        for name, cr in [("Cazna Icharyd", 20.0), ("Dantrag Dyrr", 14.0),
                         ("Nhilymra Zaer'vyn", 13.0),
                         ("Zhindia Oblodra", 14.0),
                         ('"Murtunut" Thol', 6.0)]:
            self.assertEqual(self.lib.get_monster(name).challenge_rating, cr)

    def test_cazna_is_mythic_caster(self):
        m = self.lib.get_monster("Cazna Icharyd")
        self.assertEqual(m.legendary_resistance_count, 5)
        self.assertEqual(m.spell_save_dc, 21)
        self.assertTrue(m.spells_known)

    def test_existing_npcs_repointed_to_new_blocks(self):
        camp = build_novus_somnium()
        npcs = camp.world_data["npcs"]
        self.assertEqual(npcs["npc_cazna"]["stat_source"],
                         "monster:Cazna Icharyd")
        self.assertEqual(npcs["npc_dantrag"]["stat_source"],
                         "monster:Dantrag Dyrr")
        self.assertEqual(npcs["npc_nhilymra"]["stat_source"],
                         "monster:Nhilymra Zaer'vyn")

    def test_all_zertath_stat_sources_resolve(self):
        camp = build_novus_somnium()
        for nid in ("npc_cazna", "npc_dantrag", "npc_nhilymra",
                    "npc_zhindia", "npc_thol"):
            src = camp.world_data["npcs"][nid]["stat_source"]
            self.assertIsNotNone(self.lib.get_monster(src.split(":", 1)[1]))


class TestMaclebarNesting(unittest.TestCase):
    def test_fort_nested_under_maclebar(self):
        camp = build_novus_somnium()
        locs = camp.world_data["locations"]
        self.assertIn("loc_maclebar", locs)
        self.assertEqual(locs["loc_fort_whitestone"]["parent_id"],
                         "loc_maclebar")
        self.assertIn("loc_fort_whitestone",
                      locs["loc_maclebar"]["children_ids"])
        self.assertIn("loc_protocol_omega",
                      locs["loc_fort_whitestone"]["children_ids"])


if __name__ == "__main__":
    unittest.main()
