"""Phase 8c — Find Familiar + familiar stat block tests."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import unittest

from data.familiars import (
    FAMILIARS, FamiliarKind, list_familiars, list_keys, get_familiar,
    aquatic_only, build_familiar_stats,
    summon_familiar, dismiss_familiar, list_familiars_of,
)
from data.models import CreatureStats, AbilityScores, Action
from engine.battle import BattleSystem
from engine.entities import Entity


def _make_caster(x=5.0, y=5.0):
    stats = CreatureStats(
        name="Wizard", size="Medium", hit_points=24, armor_class=12,
        speed=30,
        abilities=AbilityScores(strength=8, dexterity=14,
                                  constitution=12, intelligence=18,
                                  wisdom=12, charisma=10),
        spellcasting_ability="Intelligence",
        proficiency_bonus=2,
        actions=[Action(name="Dagger", attack_bonus=4, damage_dice="1d4",
                        damage_bonus=2, damage_type="piercing", range=5)],
    )
    return Entity(stats, x, y, is_player=True)


def _make_battle(*entities):
    b = BattleSystem(log_callback=lambda *a: None,
                      initial_entities=list(entities))
    return b


class TestCatalog(unittest.TestCase):
    def test_phb_options_present(self):
        for k in ("cat", "owl", "hawk", "raven", "spider", "rat",
                  "frog", "octopus", "seahorse", "fish", "weasel"):
            self.assertIn(k, FAMILIARS)

    def test_get_familiar(self):
        owl = get_familiar("owl")
        self.assertEqual(owl.name, "Owl")
        self.assertGreater(owl.fly_speed, 0)

    def test_get_unknown_raises(self):
        with self.assertRaises(KeyError):
            get_familiar("dragon")

    def test_owl_flies(self):
        self.assertGreater(get_familiar("owl").fly_speed, 0)
        self.assertGreater(get_familiar("hawk").fly_speed, 0)
        self.assertGreater(get_familiar("raven").fly_speed, 0)

    def test_aquatic_only(self):
        self.assertTrue(aquatic_only("seahorse"))
        self.assertTrue(aquatic_only("fish"))
        self.assertFalse(aquatic_only("owl"))
        self.assertFalse(aquatic_only("octopus"))  # amphibious

    def test_list_keys_matches_catalog(self):
        self.assertEqual(set(list_keys()), set(FAMILIARS.keys()))

    def test_list_familiars(self):
        self.assertEqual(len(list_familiars()), len(FAMILIARS))


class TestStats(unittest.TestCase):
    def test_build_familiar_stats_owl(self):
        stats = build_familiar_stats(get_familiar("owl"))
        self.assertEqual(stats.name, "Owl")
        self.assertEqual(stats.size, "Tiny")
        self.assertGreaterEqual(stats.hit_points, 1)
        self.assertGreater(stats.fly_speed, 0)
        # Owl has stealth 4 → must surface in skills
        self.assertEqual(stats.skills.get("Stealth", 0), 4)

    def test_build_familiar_stats_seahorse(self):
        stats = build_familiar_stats(get_familiar("seahorse"))
        self.assertEqual(stats.speed, 0)
        self.assertGreater(stats.swim_speed, 0)


class TestSummonFamiliar(unittest.TestCase):
    def test_summon_default_owl(self):
        caster = _make_caster()
        b = _make_battle(caster)
        ent = summon_familiar(b, caster, kind="owl")
        self.assertIs(ent.summon_owner, caster)
        self.assertTrue(ent.is_summon)
        self.assertIn("Owl", ent.name)
        self.assertEqual(ent.summon_spell_name, "Find Familiar")
        self.assertGreater(ent.stats.fly_speed, 0)
        # Sits one cell east by default
        self.assertEqual(int(ent.grid_x), int(caster.grid_x) + 1)
        self.assertEqual(int(ent.grid_y), int(caster.grid_y))

    def test_summon_explicit_position(self):
        caster = _make_caster()
        b = _make_battle(caster)
        ent = summon_familiar(b, caster, kind="cat", x=10, y=8)
        self.assertEqual(int(ent.grid_x), 10)
        self.assertEqual(int(ent.grid_y), 8)

    def test_summon_unknown_kind_raises(self):
        caster = _make_caster()
        b = _make_battle(caster)
        with self.assertRaises(KeyError):
            summon_familiar(b, caster, kind="dragon")

    def test_summon_size_carried_over(self):
        caster = _make_caster()
        b = _make_battle(caster)
        ent = summon_familiar(b, caster, kind="octopus")
        self.assertEqual(ent.stats.size, "Small")

    def test_summon_inherits_player_side(self):
        caster = _make_caster()
        b = _make_battle(caster)
        owl = summon_familiar(b, caster, kind="owl")
        self.assertEqual(owl.is_player, caster.is_player)

    def test_summon_added_to_battle(self):
        caster = _make_caster()
        b = _make_battle(caster)
        ent = summon_familiar(b, caster)
        self.assertIn(ent, b.entities)


class TestListAndDismiss(unittest.TestCase):
    def test_list_familiars_of(self):
        caster = _make_caster()
        b = _make_battle(caster)
        summon_familiar(b, caster, kind="owl")
        familiars = list_familiars_of(b, caster)
        self.assertEqual(len(familiars), 1)

    def test_dismiss_removes_familiars(self):
        caster = _make_caster()
        b = _make_battle(caster)
        summon_familiar(b, caster, kind="owl")
        summon_familiar(b, caster, kind="cat")
        n = dismiss_familiar(b, caster)
        self.assertEqual(n, 2)
        self.assertEqual(list_familiars_of(b, caster), [])

    def test_dismiss_only_owner_familiars(self):
        c1 = _make_caster(x=5)
        c2 = _make_caster(x=10)
        b = _make_battle(c1, c2)
        summon_familiar(b, c1, kind="owl")
        summon_familiar(b, c2, kind="cat")
        n = dismiss_familiar(b, c1)
        self.assertEqual(n, 1)
        self.assertEqual(len(list_familiars_of(b, c2)), 1)

    def test_dismiss_skips_other_summons(self):
        """A Spiritual Weapon belonging to the same caster must NOT be
        removed by dismiss_familiar — it's a different spell."""
        caster = _make_caster()
        b = _make_battle(caster)
        sw = b.spawn_summon(owner=caster, name="Spiritual Weapon",
                              x=3, y=3, spell_name="Spiritual Weapon")
        summon_familiar(b, caster, kind="owl")
        n = dismiss_familiar(b, caster)
        self.assertEqual(n, 1)   # only the owl
        self.assertIn(sw, b.entities)


class TestSpellEntry(unittest.TestCase):
    def test_find_familiar_in_spell_list(self):
        from data.spells import get_spell
        sp = get_spell("Find Familiar")
        self.assertEqual(sp.level, 1)
        self.assertTrue(sp.ritual)
        self.assertEqual(sp.summon_name, "Familiar")


if __name__ == "__main__":
    unittest.main()
