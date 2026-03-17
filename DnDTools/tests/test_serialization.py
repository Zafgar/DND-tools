"""Tests for data/serialization.py – generic dataclass serialization."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest
from data.models import CreatureStats, AbilityScores, Action, SpellInfo, Feature, Item
from data.serialization import serialize, serialize_full, deserialize


class TestSerializeBasic(unittest.TestCase):
    def test_simple_dataclass(self):
        ab = AbilityScores(strength=18, dexterity=14)
        data = serialize(ab)
        self.assertEqual(data["strength"], 18)
        self.assertEqual(data["dexterity"], 14)
        # Default values should be omitted by serialize()
        self.assertNotIn("constitution", data)

    def test_serialize_full_includes_defaults(self):
        ab = AbilityScores(strength=18)
        data = serialize_full(ab)
        self.assertIn("constitution", data)
        self.assertEqual(data["constitution"], 10)

    def test_non_dataclass_raises(self):
        with self.assertRaises(TypeError):
            serialize("not a dataclass")
        with self.assertRaises(TypeError):
            serialize_full(42)


class TestDeserializeBasic(unittest.TestCase):
    def test_simple_roundtrip(self):
        ab = AbilityScores(strength=20, dexterity=16, constitution=14,
                           intelligence=12, wisdom=8, charisma=10)
        data = serialize_full(ab)
        restored = deserialize(AbilityScores, data)
        self.assertEqual(restored.strength, 20)
        self.assertEqual(restored.dexterity, 16)
        self.assertEqual(restored.wisdom, 8)

    def test_missing_fields_get_defaults(self):
        """Backward compatibility: missing fields should use defaults."""
        data = {"strength": 16}
        ab = deserialize(AbilityScores, data)
        self.assertEqual(ab.strength, 16)
        self.assertEqual(ab.dexterity, 10)  # default

    def test_bad_input_raises(self):
        with self.assertRaises(TypeError):
            deserialize(AbilityScores, "not a dict")
        with self.assertRaises(TypeError):
            deserialize(str, {"a": 1})


class TestNestedDataclass(unittest.TestCase):
    def test_creature_with_abilities(self):
        stats = CreatureStats(
            name="Goblin", size="Small", hit_points=7, armor_class=15,
            abilities=AbilityScores(strength=8, dexterity=14, constitution=10),
        )
        data = serialize(stats)
        self.assertEqual(data["name"], "Goblin")
        self.assertIsInstance(data["abilities"], dict)
        self.assertEqual(data["abilities"]["strength"], 8)

        restored = deserialize(CreatureStats, data)
        self.assertEqual(restored.name, "Goblin")
        self.assertEqual(restored.abilities.strength, 8)
        self.assertEqual(restored.abilities.dexterity, 14)

    def test_creature_with_actions(self):
        action = Action(name="Scimitar", attack_bonus=4, damage_dice="1d6",
                        damage_bonus=2, damage_type="slashing", range=5)
        stats = CreatureStats(
            name="Goblin", hit_points=7, armor_class=15,
            abilities=AbilityScores(strength=8, dexterity=14),
            actions=[action],
        )
        data = serialize(stats)
        self.assertEqual(len(data["actions"]), 1)
        self.assertEqual(data["actions"][0]["name"], "Scimitar")

        restored = deserialize(CreatureStats, data)
        self.assertEqual(len(restored.actions), 1)
        self.assertIsInstance(restored.actions[0], Action)
        self.assertEqual(restored.actions[0].name, "Scimitar")
        self.assertEqual(restored.actions[0].damage_bonus, 2)


class TestListsAndDicts(unittest.TestCase):
    def test_list_of_primitives(self):
        action = Action(name="Sword", properties=["finesse", "light"])
        data = serialize(action)
        self.assertEqual(data["properties"], ["finesse", "light"])

        restored = deserialize(Action, data)
        self.assertEqual(restored.properties, ["finesse", "light"])

    def test_dict_field(self):
        stats = CreatureStats(
            name="Rogue", hit_points=30, armor_class=14,
            abilities=AbilityScores(dexterity=16),
            skills={"Stealth": 7, "Perception": 3},
        )
        data = serialize(stats)
        self.assertEqual(data["skills"]["Stealth"], 7)

        restored = deserialize(CreatureStats, data)
        self.assertEqual(restored.skills["Stealth"], 7)


class TestRoundtrip(unittest.TestCase):
    def test_full_creature_roundtrip(self):
        """A complex creature survives serialize -> deserialize."""
        spell = SpellInfo(name="Fireball", level=3, damage_dice="8d6",
                          damage_type="fire", aoe_radius=20, aoe_shape="sphere",
                          save_ability="Dexterity", range=150)
        feature = Feature(name="Pack Tactics",
                          description="Advantage when ally is adjacent")
        stats = CreatureStats(
            name="Goblin Boss", size="Small", hit_points=21, armor_class=17,
            abilities=AbilityScores(strength=10, dexterity=14, constitution=10,
                                    intelligence=10, wisdom=8, charisma=10),
            actions=[Action(name="Scimitar", attack_bonus=4, damage_dice="1d6",
                            damage_bonus=2, damage_type="slashing")],
            spells_known=[spell],
            features=[feature],
            challenge_rating=1.0,
            proficiency_bonus=2,
            speed=30,
        )
        data = serialize(stats)
        restored = deserialize(CreatureStats, data)

        self.assertEqual(restored.name, "Goblin Boss")
        self.assertEqual(restored.hit_points, 21)
        self.assertEqual(restored.abilities.dexterity, 14)
        self.assertEqual(restored.actions[0].name, "Scimitar")
        self.assertEqual(restored.spells_known[0].name, "Fireball")
        self.assertEqual(restored.spells_known[0].aoe_radius, 20)
        self.assertEqual(restored.features[0].name, "Pack Tactics")
        self.assertEqual(restored.challenge_rating, 1.0)

    def test_empty_creature_roundtrip(self):
        """Minimal creature with all defaults."""
        stats = CreatureStats(name="Dummy", hit_points=1, armor_class=10,
                              abilities=AbilityScores())
        data = serialize(stats)
        restored = deserialize(CreatureStats, data)
        self.assertEqual(restored.name, "Dummy")
        self.assertEqual(restored.hit_points, 1)
        self.assertEqual(restored.actions, [])
        self.assertEqual(restored.spells_known, [])


if __name__ == "__main__":
    unittest.main()
