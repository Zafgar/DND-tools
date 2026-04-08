"""Tests for new features: multiclass, i18n, encounter balance."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import unittest
from data.models import CreatureStats, AbilityScores, Action
from engine.entities import Entity
from i18n import t, set_language, get_language, available_languages


def _make_entity(name="Test", is_player=True, hp=50, ac=15, character_class="",
                 character_level=0, multiclass=None, **kwargs):
    stats = CreatureStats(
        name=name, hit_points=hp, armor_class=ac,
        abilities=AbilityScores(),
        character_class=character_class,
        character_level=character_level,
        multiclass=multiclass or {},
        **kwargs,
    )
    return Entity(stats, 5.0, 5.0, is_player=is_player)


class TestMulticlass(unittest.TestCase):
    def test_single_class(self):
        e = _make_entity(character_class="Fighter", character_level=10)
        self.assertFalse(e.is_multiclass)
        self.assertEqual(e.get_class_level("Fighter"), 10)
        self.assertEqual(e.get_class_level("Wizard"), 0)
        self.assertEqual(e.class_summary, "Fighter 10")

    def test_multiclass(self):
        e = _make_entity(multiclass={"Fighter": 5, "Wizard": 3})
        self.assertTrue(e.is_multiclass)
        self.assertEqual(e.get_class_level("Fighter"), 5)
        self.assertEqual(e.get_class_level("Wizard"), 3)
        self.assertEqual(e.get_class_level("Rogue"), 0)
        self.assertIn("Fighter 5", e.class_summary)
        self.assertIn("Wizard 3", e.class_summary)

    def test_no_class(self):
        e = _make_entity()
        self.assertFalse(e.is_multiclass)
        self.assertEqual(e.get_class_level("Fighter"), 0)
        self.assertEqual(e.class_summary, "")


class TestI18n(unittest.TestCase):
    def setUp(self):
        set_language("en")

    def test_english_default(self):
        self.assertEqual(get_language(), "en")
        self.assertEqual(t("combat.round"), "ROUND")

    def test_finnish(self):
        set_language("fi")
        self.assertEqual(t("combat.round"), "KIERROS")
        self.assertEqual(t("combat.started"), "TAISTELU ALKAA")
        self.assertEqual(t("ui.save"), "Tallenna")

    def test_fallback_to_english(self):
        set_language("fi")
        # A key only in English should fall back
        self.assertEqual(t("nonexistent.key"), "nonexistent.key")

    def test_unknown_key_returns_key(self):
        result = t("this.does.not.exist")
        self.assertEqual(result, "this.does.not.exist")

    def test_available_languages(self):
        langs = available_languages()
        self.assertIn("en", langs)
        self.assertIn("fi", langs)

    def test_set_invalid_language_ignored(self):
        set_language("xx")
        self.assertEqual(get_language(), "en")

    def test_conditions_translated(self):
        set_language("fi")
        self.assertEqual(t("condition.prone"), "Maassa")
        self.assertEqual(t("condition.stunned"), "Tyrmistynyt")

    def test_encounter_labels(self):
        set_language("fi")
        self.assertEqual(t("encounter.easy"), "HELPPO")
        self.assertEqual(t("encounter.deadly"), "TAPPAVA")

    def tearDown(self):
        set_language("en")


class TestHealReturnValue(unittest.TestCase):
    def test_heal_returns_amount(self):
        e = _make_entity(hp=50)
        e.hp = 20
        healed = e.heal(15)
        self.assertEqual(healed, 15)
        self.assertEqual(e.hp, 35)

    def test_heal_capped_returns_actual(self):
        e = _make_entity(hp=50)
        e.hp = 45
        healed = e.heal(20)
        self.assertEqual(healed, 5)
        self.assertEqual(e.hp, 50)

    def test_heal_at_full_returns_zero(self):
        e = _make_entity(hp=50)
        healed = e.heal(10)
        self.assertEqual(healed, 0)


if __name__ == "__main__":
    unittest.main()
