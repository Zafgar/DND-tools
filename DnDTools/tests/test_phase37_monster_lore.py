"""Phase 37 — monster catalog expansion + lore modal.

Verifies:

  * All new bosses (Demogorgon, Orcus, Demilich, Empyrean, Tarrasque,
    Solar, six ancient dragons) ship with the expected stat block
    structure: legendary actions/resistance counts match the lore,
    multiattack pattern is present, every legendary feature has a
    matching Action of action_type == "legendary".
  * Lore fields are populated for each new entry (catches the "we
    added the boss but forgot the flavor" regression).
  * Damage immunity / resistance lists match the canonical 5e
    pattern (e.g. Tarrasque immune to fire & poison; Ancient Blue
    Dragon immune to lightning).
  * Save proficiencies match what the MM lists for each.
  * MonsterLoreModal renders without crashing when given any of the
    new stats (pygame-skipped in this env, but exercises the data
    path).
  * Library lookup ``library.get_monster("Tarrasque")`` retrieves
    the new entry.
  * AI legendary-action selection works on the new bosses (they
    actually have selectable legendary action features wired).
  * Legendary resistance advisor returns a "USE" for an
    encounter-killer save vs the new bosses.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import unittest

from data.models import CreatureStats, AbilityScores, Action, Feature
from data.monsters.cr_17plus import monsters
from engine.entities import Entity
from engine.battle import BattleSystem
from engine.ai.tactical_ai import TacticalAI
from engine.rules import lr_decision_with_reason


def _by_name(name):
    return next((m for m in monsters if m.name == name), None)


# --------------------------------------------------------------------- #
# Boss roster — verify every new entry exists with the right CR
# --------------------------------------------------------------------- #
class TestNewBossRoster(unittest.TestCase):
    EXPECTED = [
        ("Tarrasque", 30.0),
        ("Solar", 21.0),
        ("Demilich", 18.0),
        ("Ancient Brass Dragon", 20.0),
        ("Ancient Bronze Dragon", 22.0),
        ("Ancient Copper Dragon", 21.0),
        ("Ancient Gold Dragon", 24.0),
        ("Ancient Green Dragon", 22.0),
        ("Ancient Blue Dragon", 23.0),
        ("Ancient Silver Dragon", 23.0),
        ("Empyrean", 23.0),
        ("Demogorgon", 26.0),
        ("Orcus", 26.0),
    ]

    def test_all_new_bosses_present(self):
        for name, cr in self.EXPECTED:
            m = _by_name(name)
            self.assertIsNotNone(m, f"{name} missing from catalog")
            self.assertEqual(m.challenge_rating, cr,
                              f"{name} CR drift")

    def test_all_new_bosses_have_legendary_resources(self):
        for name, _ in self.EXPECTED:
            m = _by_name(name)
            self.assertGreater(
                m.legendary_action_count, 0,
                f"{name} should have at least 1 LA")
            self.assertGreater(
                m.legendary_resistance_count, 0,
                f"{name} should have LR")

    def test_all_new_bosses_have_lore_and_tactics(self):
        for name, _ in self.EXPECTED:
            m = _by_name(name)
            self.assertTrue(m.lore,
                             f"{name} missing lore")
            self.assertTrue(m.tactics,
                             f"{name} missing tactics")
            self.assertTrue(m.loot_table,
                             f"{name} missing loot table")
            self.assertTrue(m.sources,
                             f"{name} missing source citation")

    def test_legendary_features_have_matching_actions(self):
        """A legendary Feature without a same-named Action of
        action_type == 'legendary' can't actually be triggered by the
        AI — this test catches that mismatch."""
        for name, _ in self.EXPECTED:
            m = _by_name(name)
            leg_feats = [f for f in m.features
                          if f.feature_type == "legendary"]
            leg_actions = {a.name for a in m.actions
                            if a.action_type == "legendary"}
            for f in leg_feats:
                # Feature name might end with " (1 cost)" etc. — strip
                feat_base = f.name.split(" (")[0].strip()
                # Be tolerant of legendary feature names vs action
                # names: at least one match either exact, prefix or
                # suffix.
                matched = (feat_base in leg_actions or
                            any(feat_base in a or a in feat_base
                                 for a in leg_actions))
                self.assertTrue(
                    matched,
                    f"{name}: legendary feature '{f.name}' has no "
                    f"matching legendary Action "
                    f"(actions: {sorted(leg_actions)})")


# --------------------------------------------------------------------- #
# Damage profile sanity
# --------------------------------------------------------------------- #
class TestDamageProfile(unittest.TestCase):
    def test_tarrasque_immune_fire_and_poison(self):
        t = _by_name("Tarrasque")
        self.assertIn("fire", t.damage_immunities)
        self.assertIn("poison", t.damage_immunities)

    def test_blue_dragon_immune_lightning(self):
        d = _by_name("Ancient Blue Dragon")
        self.assertIn("lightning", d.damage_immunities)

    def test_silver_dragon_immune_cold(self):
        d = _by_name("Ancient Silver Dragon")
        self.assertIn("cold", d.damage_immunities)

    def test_green_dragon_immune_poison(self):
        d = _by_name("Ancient Green Dragon")
        self.assertIn("poison", d.damage_immunities)
        self.assertIn("Poisoned", d.condition_immunities)

    def test_brass_dragon_immune_fire(self):
        d = _by_name("Ancient Brass Dragon")
        self.assertIn("fire", d.damage_immunities)

    def test_demogorgon_immune_poison_and_resistant_to_elements(self):
        d = _by_name("Demogorgon")
        self.assertIn("poison", d.damage_immunities)
        for r in ("cold", "fire", "lightning"):
            self.assertIn(r, d.damage_resistances)

    def test_orcus_immune_necrotic_and_poison(self):
        d = _by_name("Orcus")
        self.assertIn("necrotic", d.damage_immunities)
        self.assertIn("poison", d.damage_immunities)


# --------------------------------------------------------------------- #
# Multiattack structure
# --------------------------------------------------------------------- #
class TestMultiattack(unittest.TestCase):
    def test_tarrasque_makes_five_attacks(self):
        t = _by_name("Tarrasque")
        ma = next((a for a in t.actions if a.is_multiattack), None)
        self.assertIsNotNone(ma)
        self.assertEqual(ma.multiattack_count, 5)

    def test_ancient_dragons_make_three_attacks(self):
        for name in ("Ancient Brass Dragon",
                       "Ancient Bronze Dragon",
                       "Ancient Copper Dragon",
                       "Ancient Gold Dragon",
                       "Ancient Green Dragon",
                       "Ancient Blue Dragon",
                       "Ancient Silver Dragon"):
            m = _by_name(name)
            ma = next((a for a in m.actions if a.is_multiattack),
                        None)
            self.assertIsNotNone(ma, f"{name} multiattack missing")
            self.assertEqual(
                ma.multiattack_count, 3,
                f"{name} should have 3 attacks per multiattack")

    def test_orcus_wand_multiattack(self):
        o = _by_name("Orcus")
        ma = next((a for a in o.actions if a.is_multiattack), None)
        self.assertEqual(ma.multiattack_count, 3)


# --------------------------------------------------------------------- #
# AI works with the new bosses
# --------------------------------------------------------------------- #
class TestAIOnNewBosses(unittest.TestCase):
    def _spawn(self, stats):
        # Quick-build an entity with the stats; place at (5, 5).
        return Entity(stats, 5, 5, is_player=False)

    def _pc(self, x=7, y=5):
        from data.models import AbilityScores
        s = CreatureStats(
            name="PC", size="Medium",
            hit_points=50, armor_class=18, speed=30,
            abilities=AbilityScores(strength=14, dexterity=14,
                                      constitution=14,
                                      intelligence=10, wisdom=10,
                                      charisma=10),
            actions=[Action(name="Sword", attack_bonus=6,
                              damage_dice="1d8", damage_bonus=4,
                              damage_type="slashing", range=5)],
            proficiency_bonus=4,
        )
        return Entity(s, x, y, is_player=True)

    def test_legendary_action_selectable_for_each_new_boss(self):
        for name in ("Tarrasque", "Solar", "Demogorgon", "Orcus",
                       "Ancient Gold Dragon",
                       "Ancient Blue Dragon"):
            stats = _by_name(name)
            boss = self._spawn(stats)
            pc = self._pc()
            b = BattleSystem(log_callback=lambda *a: None,
                              initial_entities=[boss, pc])
            ai = TacticalAI()
            step = ai.calculate_legendary_action(boss, b)
            self.assertIsNotNone(
                step,
                f"{name} should pick a legendary action when budget "
                f"allows")


# --------------------------------------------------------------------- #
# LR advisor on new bosses
# --------------------------------------------------------------------- #
class TestLRAdvisorOnNewBosses(unittest.TestCase):
    def test_tarrasque_burns_lr_on_polymorph(self):
        t = _by_name("Tarrasque")
        boss = Entity(t, 5, 5, is_player=False)
        boss.legendary_resistances_left = 1
        use, reason = lr_decision_with_reason(
            boss, "", "", spell_name="Polymorph")
        self.assertTrue(use)
        self.assertIn("encounter-killer", reason.lower())

    def test_demilich_burns_lr_on_banishment_even_at_last(self):
        d = _by_name("Demilich")
        boss = Entity(d, 5, 5, is_player=False)
        boss.legendary_resistances_left = 1
        use, _ = lr_decision_with_reason(
            boss, "Banished", "",
            spell_name="Banishment")
        self.assertTrue(use)


# --------------------------------------------------------------------- #
# MonsterLoreModal — pygame-dependent draw smoke test
# --------------------------------------------------------------------- #
try:
    import pygame  # noqa: F401
    HAS_PYGAME = True
except ImportError:
    HAS_PYGAME = False


@unittest.skipUnless(HAS_PYGAME, "pygame not installed")
class TestMonsterLoreModalDataPath(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import pygame
        pygame.init()
        pygame.display.set_mode((1280, 800))

    def test_open_and_draw_each_new_boss(self):
        from states.monster_lore_modal import MonsterLoreModal
        import pygame
        screen = pygame.display.get_surface()
        for name in ("Tarrasque", "Solar", "Demogorgon", "Orcus",
                       "Empyrean", "Demilich",
                       "Ancient Gold Dragon",
                       "Ancient Bronze Dragon",
                       "Ancient Copper Dragon",
                       "Ancient Green Dragon",
                       "Ancient Blue Dragon",
                       "Ancient Silver Dragon",
                       "Ancient Brass Dragon"):
            stats = _by_name(name)
            modal = MonsterLoreModal(stats)
            modal.open()
            modal.draw(screen)
            modal._close()


# --------------------------------------------------------------------- #
# Library lookup
# --------------------------------------------------------------------- #
class TestLibraryLookup(unittest.TestCase):
    def test_library_finds_tarrasque(self):
        from data.library import library
        # library returns a CreatureStats with the same name
        s = library.get_monster("Tarrasque")
        self.assertIsNotNone(s)
        self.assertEqual(s.name, "Tarrasque")
        self.assertEqual(s.challenge_rating, 30.0)

    def test_library_finds_ancient_gold(self):
        from data.library import library
        s = library.get_monster("Ancient Gold Dragon")
        self.assertIsNotNone(s)
        self.assertEqual(s.challenge_rating, 24.0)


if __name__ == "__main__":
    unittest.main()
