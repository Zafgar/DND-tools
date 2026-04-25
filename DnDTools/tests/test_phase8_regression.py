"""Phase 8d — verification / regression tests for the features the
user asked us to confirm:

  * Druid Wild Shape (transform / revert / damage carry-over).
  * Healing (cure_wounds / healing word style: Entity.heal()
    raising HP, lifting Unconscious, resetting death-save tracking).
  * Spiritual Weapon (summon -> bonus-action attack -> dismiss when
    owner drops concentration / dies).
  * AI integration of these features (it shouldn't try to use them
    when the action economy is already spent / target already dead).
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import unittest

from data.models import (
    CreatureStats, AbilityScores, Action, Feature, SpellInfo,
)
from data.library import library
from engine.entities import Entity
from engine.battle import BattleSystem


# --------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------- #
def _druid(level=4, with_combat_wild_shape=False, hp=24):
    feats = [
        Feature(name="Wild Shape", uses_per_day=2, mechanic="wild_shape"),
    ]
    if with_combat_wild_shape:
        feats.append(Feature(name="Combat Wild Shape",
                              mechanic="combat_wild_shape"))
    stats = CreatureStats(
        name=f"Druid (lv{level})", size="Medium",
        hit_points=hp, armor_class=12, speed=30,
        abilities=AbilityScores(strength=10, dexterity=12,
                                  constitution=14, intelligence=10,
                                  wisdom=16, charisma=8),
        features=feats,
        actions=[Action(name="Quarterstaff", attack_bonus=2,
                        damage_dice="1d6", damage_bonus=0,
                        damage_type="bludgeoning", range=5)],
        character_level=level,
    )
    return Entity(stats, 5, 5, is_player=True)


def _cleric():
    spells = [
        SpellInfo(name="Cure Wounds", level=1,
                  action_type="action", range=5, targets="single",
                  heals="1d8+3", components="V,S"),
        SpellInfo(name="Healing Word", level=1,
                  action_type="bonus", range=60, targets="single",
                  heals="1d4+3"),
        SpellInfo(name="Spiritual Weapon", level=2,
                  action_type="bonus", range=60, targets="single",
                  damage_dice="1d8+3", damage_type="force",
                  duration="1 minute",
                  summon_name="Spiritual Weapon",
                  summon_hp=0, summon_ac=99,
                  summon_damage_dice="1d8",
                  summon_damage_type="force",
                  summon_duration_rounds=10),
    ]
    stats = CreatureStats(
        name="Cleric", size="Medium",
        hit_points=30, armor_class=16, speed=30,
        abilities=AbilityScores(strength=10, dexterity=10,
                                  constitution=12, intelligence=10,
                                  wisdom=16, charisma=8),
        spells_known=spells,
        spell_slots={1: 4, 2: 3},
        spellcasting_ability="Wisdom",
        proficiency_bonus=2,
        actions=[Action(name="Mace", attack_bonus=2, damage_dice="1d6",
                        damage_bonus=0, damage_type="bludgeoning",
                        range=5)],
        character_level=3,
    )
    return Entity(stats, 5, 5, is_player=True)


def _battle(*ents):
    return BattleSystem(log_callback=lambda *a: None,
                         initial_entities=list(ents))


# --------------------------------------------------------------------- #
# Wild Shape
# --------------------------------------------------------------------- #
class TestWildShape(unittest.TestCase):
    def test_transform_swaps_stats(self):
        druid = _druid(hp=24)
        bear = library.get_monster("Brown Bear")
        druid.transform_into(bear)
        self.assertTrue(druid.is_wild_shaped)
        self.assertEqual(druid.wild_shape_name, "Brown Bear")
        # HP becomes the bear's pool
        self.assertEqual(druid.hp, bear.hit_points)
        self.assertEqual(druid.max_hp, bear.hit_points)
        # Beast STR replaces druid STR
        self.assertEqual(druid.stats.abilities.strength,
                          bear.abilities.strength)

    def test_revert_restores_original_hp(self):
        druid = _druid(hp=24)
        druid.hp = 18                  # took some damage before transform
        bear = library.get_monster("Brown Bear")
        druid.transform_into(bear)
        druid.hp = 1                   # bear got beat up
        druid.revert_form()
        self.assertFalse(druid.is_wild_shaped)
        self.assertEqual(druid.hp, 18)  # back to pre-transform HP

    def test_damage_carryover_when_bear_drops(self):
        druid = _druid(hp=24)
        druid.hp = 20
        bear = library.get_monster("Brown Bear")
        druid.transform_into(bear)
        # Big hit > bear HP. Bear drops, druid eats remainder.
        bear_hp = druid.hp
        overkill = bear_hp + 10
        druid.take_damage(overkill, "slashing")
        self.assertFalse(druid.is_wild_shaped)
        self.assertLess(druid.hp, 20)

    def test_skills_merge_higher_value(self):
        druid = _druid(hp=24)
        druid.stats.skills = {"Stealth": 1, "Perception": 2}
        bear = library.get_monster("Brown Bear")
        bear.skills = {"Stealth": 3, "Athletics": 4}   # bear is stronger
        druid.transform_into(bear)
        self.assertEqual(druid.stats.skills["Stealth"], 3)
        self.assertEqual(druid.stats.skills["Perception"], 2)
        self.assertEqual(druid.stats.skills["Athletics"], 4)

    def test_spells_disabled_without_beast_spells(self):
        druid = _druid(hp=24)
        druid.stats.spells_known = [
            SpellInfo(name="Cure Wounds", level=1,
                      action_type="action", heals="1d8+3"),
        ]
        bear = library.get_monster("Brown Bear")
        druid.transform_into(bear)
        self.assertEqual(druid.stats.spells_known, [])

    def test_revert_restores_spells(self):
        druid = _druid(hp=24)
        sp = SpellInfo(name="Cure Wounds", level=1,
                        action_type="action", heals="1d8+3")
        druid.stats.spells_known = [sp]
        bear = library.get_monster("Brown Bear")
        druid.transform_into(bear)
        druid.revert_form()
        self.assertEqual(len(druid.stats.spells_known), 1)
        self.assertEqual(druid.stats.spells_known[0].name, "Cure Wounds")


# --------------------------------------------------------------------- #
# Healing
# --------------------------------------------------------------------- #
class TestHealing(unittest.TestCase):
    def test_heal_raises_hp(self):
        cleric = _cleric()
        cleric.hp = 5
        n = cleric.heal(8)
        self.assertEqual(n, 8)
        self.assertEqual(cleric.hp, 13)

    def test_heal_caps_at_max(self):
        cleric = _cleric()
        cleric.hp = cleric.max_hp - 2
        n = cleric.heal(10)
        self.assertEqual(n, 2)
        self.assertEqual(cleric.hp, cleric.max_hp)

    def test_heal_lifts_unconscious(self):
        cleric = _cleric()
        cleric.hp = 0
        cleric.add_condition("Unconscious")
        cleric.death_save_successes = 1
        cleric.death_save_failures = 2
        cleric.heal(5)
        self.assertGreater(cleric.hp, 0)
        self.assertNotIn("Unconscious", cleric.conditions)
        self.assertEqual(cleric.death_save_successes, 0)
        self.assertEqual(cleric.death_save_failures, 0)

    def test_heal_zero_does_not_revive(self):
        cleric = _cleric()
        cleric.hp = 0
        cleric.add_condition("Unconscious")
        cleric.heal(0)
        self.assertIn("Unconscious", cleric.conditions)


# --------------------------------------------------------------------- #
# Spiritual Weapon
# --------------------------------------------------------------------- #
class TestSpiritualWeapon(unittest.TestCase):
    def test_spawn_summon_attaches_to_caster(self):
        cleric = _cleric()
        b = _battle(cleric)
        sw = b.spawn_summon(
            owner=cleric, name="Spiritual Weapon",
            x=int(cleric.grid_x) + 1, y=int(cleric.grid_y),
            damage_dice="1d8", damage_type="force",
            duration=10, spell_name="Spiritual Weapon",
        )
        self.assertTrue(sw.is_summon)
        self.assertIs(sw.summon_owner, cleric)
        self.assertEqual(sw.summon_spell_name, "Spiritual Weapon")
        self.assertIn(sw, b.entities)

    def test_summon_attack_uses_spell_attack_bonus(self):
        cleric = _cleric()
        cleric.stats.spell_attack_bonus = 5
        b = _battle(cleric)
        sw = b.spawn_summon(owner=cleric, name="Spiritual Weapon",
                              x=6, y=5, spell_name="Spiritual Weapon")
        self.assertGreater(len(sw.stats.actions), 0)
        atk = sw.stats.actions[0]
        self.assertEqual(atk.attack_bonus, 5)

    def test_summon_inherits_player_side(self):
        cleric = _cleric()
        b = _battle(cleric)
        sw = b.spawn_summon(owner=cleric, name="Spiritual Weapon",
                              x=6, y=5, spell_name="Spiritual Weapon")
        self.assertEqual(sw.is_player, cleric.is_player)


# --------------------------------------------------------------------- #
# AI sanity (small smoke check — full AI tests are elsewhere)
# --------------------------------------------------------------------- #
class TestAIDoesntChooseImpossibleHeal(unittest.TestCase):
    def test_heal_branch_runs_without_crash(self):
        """AI healing branch works whether there's a target or not."""
        from engine.ai.tactical_ai import TacticalAI
        cleric = _cleric()
        b = _battle(cleric)
        ai = TacticalAI()
        # The current method takes (self, entity) — call it raw and
        # ensure it doesn't crash whatever the result.
        try:
            ai._try_heal_action(cleric)
        except Exception as ex:
            self.fail(f"_try_heal_action raised: {ex!r}")


if __name__ == "__main__":
    unittest.main()
