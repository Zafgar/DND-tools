"""Phase 51 — spells are one central library; stat blocks reference by
name and are re-bound to the library on load (no per-block holders)."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import unittest

import data.spells as spells_mod
from data.spells import get_spell, has_spell, rebind_to_library
from data.models import CreatureStats, AbilityScores, SpellInfo
from data.library import MonsterLibrary


class TestNameBasedAuthoring(unittest.TestCase):
    def test_spell_names_resolve_from_library(self):
        cs = CreatureStats(name="Mage", spell_names=["Fireball", "Shield"])
        self.assertEqual([s.name for s in cs.spells_known],
                         ["Fireball", "Shield"])
        # Resolved objects carry the library's real data, not placeholders.
        fb = cs.spells_known[0]
        self.assertEqual(fb.name, "Fireball")
        self.assertTrue(fb.damage_dice)  # library defines damage

    def test_cantrip_names_get_spell_attack_bonus(self):
        cs = CreatureStats(name="Mage", spell_attack_bonus=11,
                           cantrip_names=["Fire Bolt", "Ray of Frost"])
        self.assertEqual([c.attack_bonus_fixed for c in cs.cantrips], [11, 11])

    def test_explicit_spells_known_not_overwritten(self):
        # Back-compat: if someone still passes SpellInfo objects, keep them.
        custom = SpellInfo("Custom Bolt", level=1)
        cs = CreatureStats(name="X", spells_known=[custom])
        self.assertIs(cs.spells_known[0], custom)


class TestRebindToLibrary(unittest.TestCase):
    def test_stale_embedded_spell_is_rebound(self):
        # A stat block carrying an out-of-date copy of a library spell.
        stale = get_spell("Fireball")
        stale.damage_dice = "1d1"  # deliberately wrong
        cs = CreatureStats(name="Old", spells_known=[stale])
        rebind_to_library(cs)
        self.assertEqual(cs.spells_known[0].damage_dice,
                         spells_mod._spells["Fireball"].damage_dice)

    def test_rebind_preserves_attack_bonus_fixed(self):
        c = get_spell("Fire Bolt", attack_bonus_fixed=7)
        cs = CreatureStats(name="Mon", cantrips=[c])
        rebind_to_library(cs)
        self.assertEqual(cs.cantrips[0].attack_bonus_fixed, 7)

    def test_rebind_keeps_unknown_spell(self):
        custom = SpellInfo("Totally Homebrew", level=3)
        cs = CreatureStats(name="Y", spells_known=[custom])
        rebind_to_library(cs)
        self.assertEqual(cs.spells_known[0].name, "Totally Homebrew")

    def test_rebind_is_idempotent(self):
        cs = CreatureStats(name="Z", spell_names=["Shield", "Counterspell"])
        rebind_to_library(cs)
        rebind_to_library(cs)
        self.assertEqual([s.name for s in cs.spells_known],
                         ["Shield", "Counterspell"])


class TestLibraryMonstersUseCentralSpells(unittest.TestCase):
    def setUp(self):
        self.lib = MonsterLibrary()

    def test_json_monster_spell_matches_library(self):
        oni = self.lib.get_monster("Oni")
        cc = next(s for s in oni.spells_known if s.name == "Cone of Cold")
        self.assertEqual(cc.damage_dice,
                         spells_mod._spells["Cone of Cold"].damage_dice)

    def test_converted_boss_has_spells_from_library(self):
        cazna = self.lib.get_monster("Cazna Icharyd")
        # CR 26 archmage: the full 9th-level list, resolved by name from
        # the central library.
        self.assertGreaterEqual(len(cazna.spells_known), 30)
        self.assertEqual(len(cazna.cantrips), 5)
        self.assertTrue(all(c.attack_bonus_fixed == 17 for c in cazna.cantrips))
        # Every known spell exists in the central library (no orphans).
        for s in cazna.spells_known:
            self.assertTrue(has_spell(s.name), f"{s.name} not in library")


if __name__ == "__main__":
    unittest.main()
