"""Phase 34/35/36 — reactions, monster catalog, subclass features.

Three independent audits in one file (they share fixtures).

Phase 34 — Reaction advisor:
  * Counterspell option fires for high-impact enemy casts
  * Shield option recommends USE when +5 AC flips the hit to miss
  * Absorb Elements recommends USE for elemental damage when fragile
  * Hellish Rebuke recommends USE when meaningful damage taken
  * Cutting Words recommends USE when subtract would flip outcome

Phase 35 — Monster catalog gap-fill:
  * Tarrasque present and statted correctly
  * Solar present and statted correctly

Phase 36 — Subclass feature helpers:
  * Battle Master superiority dice + maneuver advisor
  * Sorcerer metamagic cost & advisor (Quickened, Twinned, Careful, …)
  * Wizard Arcane Recovery cap + slot restoration
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
from data.spells import _spells, get_spell
from engine.entities import Entity
from engine.battle import BattleSystem
from engine.ai.tactical_ai import TacticalAI


def _wizard(*, level=9, slots=None, spells=None, x=5, y=5):
    stats = CreatureStats(
        name="Wizard", size="Medium",
        hit_points=40, armor_class=12, speed=30,
        abilities=AbilityScores(strength=8, dexterity=14,
                                  constitution=14, intelligence=18,
                                  wisdom=12, charisma=10),
        actions=[], proficiency_bonus=4,
        character_level=level, character_class="Wizard",
    )
    stats.spellcasting_ability = "intelligence"
    stats.spell_save_dc = 15
    stats.spell_attack_bonus = 7
    stats.spell_slots = slots or {
        "1st": 4, "2nd": 3, "3rd": 3, "4th": 2, "5th": 1,
        "6th": 0, "7th": 0, "8th": 0, "9th": 0,
    }
    stats.spells_known = list(spells or [])
    e = Entity(stats, x, y, is_player=True)
    e.spell_slots = dict(stats.spell_slots)
    return e


def _basic_target(x=10, y=10, ac=15, hp=20):
    stats = CreatureStats(
        name="Target", size="Medium",
        hit_points=hp, armor_class=ac, speed=30,
        abilities=AbilityScores(),
        actions=[Action(name="Slam", attack_bonus=3,
                          damage_dice="1d6", damage_bonus=0,
                          damage_type="bludgeoning", range=5)],
    )
    return Entity(stats, x, y, is_player=True)


def _enemy_caster(x=10, y=5):
    stats = CreatureStats(
        name="Necromancer", size="Medium",
        hit_points=60, armor_class=14, speed=30,
        abilities=AbilityScores(strength=8, dexterity=12,
                                  constitution=14, intelligence=18,
                                  wisdom=12, charisma=10),
        actions=[], proficiency_bonus=4, character_level=9,
    )
    stats.spellcasting_ability = "intelligence"
    stats.spell_save_dc = 15
    stats.spell_attack_bonus = 7
    return Entity(stats, x, y, is_player=False)


# --------------------------------------------------------------------- #
# Phase 34 — Reaction advisor
# --------------------------------------------------------------------- #
class TestReactionAdvisor(unittest.TestCase):
    def test_counterspell_option_fires_on_high_level_spell(self):
        from engine.reaction_advisor import analyse_enemy_spell
        wiz = _wizard(spells=[_spells["Counterspell"]])
        enemy = _enemy_caster()
        b = BattleSystem(log_callback=lambda *a: None,
                          initial_entities=[wiz, enemy])
        fireball = _spells["Fireball"]
        prompt = analyse_enemy_spell(
            enemy, fireball, spell_level=3, battle=b,
            potential_reactors=[wiz])
        names = [o.reaction_name for o in prompt.options]
        self.assertIn("Counterspell", names)
        # Recommended — Fireball at level 3 is worth countering
        rec = next(o for o in prompt.options
                    if o.reaction_name == "Counterspell")
        self.assertTrue(rec.recommendation)

    def test_counterspell_not_offered_without_slot(self):
        from engine.reaction_advisor import analyse_enemy_spell
        wiz = _wizard(slots={"1st": 4, "2nd": 3, "3rd": 0,
                                "4th": 0, "5th": 0, "6th": 0,
                                "7th": 0, "8th": 0, "9th": 0},
                       spells=[_spells["Counterspell"]])
        enemy = _enemy_caster()
        b = BattleSystem(log_callback=lambda *a: None,
                          initial_entities=[wiz, enemy])
        prompt = analyse_enemy_spell(
            enemy, _spells["Fireball"], spell_level=3,
            battle=b, potential_reactors=[wiz])
        names = [o.reaction_name for o in prompt.options]
        self.assertNotIn("Counterspell", names)

    def test_shield_recommends_when_plus_five_flips_outcome(self):
        from engine.reaction_advisor import analyse_incoming_attack
        wiz = _wizard(spells=[_spells["Shield"]])
        # AC is 12; attacker rolled 14 (hits by 2). +5 AC → 17 (miss)
        enemy = _enemy_caster()
        b = BattleSystem(log_callback=lambda *a: None,
                          initial_entities=[wiz, enemy])
        prompt = analyse_incoming_attack(
            target=wiz, attacker=enemy,
            attack_total=14, ac_now=12, battle=b,
            potential_reactors=[wiz])
        s = next((o for o in prompt.options
                   if o.reaction_name == "Shield"), None)
        self.assertIsNotNone(s)
        self.assertTrue(s.recommendation)
        self.assertIn("turns it into a miss", s.reason)

    def test_shield_no_recommend_when_already_misses(self):
        from engine.reaction_advisor import analyse_incoming_attack
        wiz = _wizard(spells=[_spells["Shield"]])
        enemy = _enemy_caster()
        b = BattleSystem(log_callback=lambda *a: None,
                          initial_entities=[wiz, enemy])
        prompt = analyse_incoming_attack(
            target=wiz, attacker=enemy,
            attack_total=10, ac_now=12, battle=b,
            potential_reactors=[wiz])
        s = next(o for o in prompt.options
                  if o.reaction_name == "Shield")
        self.assertFalse(s.recommendation)
        self.assertIn("already missed", s.reason)

    def test_absorb_elements_recommends_on_big_elemental_hit(self):
        from engine.reaction_advisor import analyse_incoming_damage
        wiz = _wizard(spells=[_spells["Absorb Elements"]])
        enemy = _enemy_caster()
        b = BattleSystem(log_callback=lambda *a: None,
                          initial_entities=[wiz, enemy])
        prompt = analyse_incoming_damage(
            target=wiz, attacker=enemy,
            damage=28, damage_type="fire", battle=b)
        opt = next(o for o in prompt.options
                    if o.reaction_name == "Absorb Elements")
        self.assertTrue(opt.recommendation)

    def test_absorb_elements_skipped_on_non_elemental(self):
        from engine.reaction_advisor import analyse_incoming_damage
        wiz = _wizard(spells=[_spells["Absorb Elements"]])
        enemy = _enemy_caster()
        b = BattleSystem(log_callback=lambda *a: None,
                          initial_entities=[wiz, enemy])
        prompt = analyse_incoming_damage(
            target=wiz, attacker=enemy,
            damage=20, damage_type="psychic", battle=b)
        names = [o.reaction_name for o in prompt.options]
        self.assertNotIn("Absorb Elements", names)

    def test_hellish_rebuke_recommends_on_meaningful_damage(self):
        from engine.reaction_advisor import analyse_incoming_damage
        wiz = _wizard(spells=[_spells["Hellish Rebuke"]])
        enemy = _enemy_caster()
        b = BattleSystem(log_callback=lambda *a: None,
                          initial_entities=[wiz, enemy])
        prompt = analyse_incoming_damage(
            target=wiz, attacker=enemy,
            damage=15, damage_type="slashing", battle=b)
        opt = next(o for o in prompt.options
                    if o.reaction_name == "Hellish Rebuke")
        self.assertTrue(opt.recommendation)


# --------------------------------------------------------------------- #
# Phase 35 — Monster catalog: Tarrasque + Solar
# --------------------------------------------------------------------- #
class TestMonsterCatalogExpansion(unittest.TestCase):
    def test_tarrasque_present(self):
        from data.monsters.cr_17plus import monsters
        names = [m.name for m in monsters]
        self.assertIn("Tarrasque", names)
        t = next(m for m in monsters if m.name == "Tarrasque")
        self.assertEqual(t.challenge_rating, 30.0)
        self.assertEqual(t.legendary_action_count, 3)
        self.assertEqual(t.legendary_resistance_count, 3)
        # Has Reflective Carapace
        feats = {f.name for f in t.features}
        self.assertIn("Reflective Carapace", feats)
        # Has multiattack
        ma = next((a for a in t.actions if a.is_multiattack), None)
        self.assertIsNotNone(ma)
        self.assertEqual(ma.multiattack_count, 5)

    def test_solar_present(self):
        from data.monsters.cr_17plus import monsters
        names = [m.name for m in monsters]
        self.assertIn("Solar", names)
        s = next(m for m in monsters if m.name == "Solar")
        self.assertEqual(s.challenge_rating, 21.0)
        # Solar can fly
        self.assertEqual(s.fly_speed, 150)
        # Has Healing Touch action
        actions = {a.name for a in s.actions}
        self.assertIn("Healing Touch", actions)
        self.assertIn("Slaying Longsword", actions)


# --------------------------------------------------------------------- #
# Phase 36 — Subclass features: Battle Master, Metamagic, Arcane Recovery
# --------------------------------------------------------------------- #
class TestBattleMasterManeuvers(unittest.TestCase):
    def _bm(self, level=5, dice_left=4, maneuvers=None):
        stats = CreatureStats(
            name="BM", size="Medium",
            hit_points=44, armor_class=18, speed=30,
            abilities=AbilityScores(strength=18, dexterity=14,
                                      constitution=14, intelligence=10,
                                      wisdom=12, charisma=10),
            actions=[Action(name="Sword", attack_bonus=6,
                              damage_dice="1d8", damage_bonus=4,
                              damage_type="slashing", range=5)],
            features=[Feature(
                name="Battle Master Maneuvers",
                mechanic="battle_master_maneuvers",
                mechanic_value=",".join(maneuvers or [
                    "Trip Attack", "Riposte", "Precision Attack",
                ]),
                feature_type="class",
            )],
            proficiency_bonus=3,
            character_level=level,
        )
        e = Entity(stats, 5, 5, is_player=True)
        e.superiority_dice_left = dice_left
        return e

    def test_die_size_by_level(self):
        from engine.subclass_features import superiority_dice_size
        self.assertEqual(superiority_dice_size(self._bm(level=5)), 8)
        self.assertEqual(superiority_dice_size(self._bm(level=10)), 10)
        self.assertEqual(superiority_dice_size(self._bm(level=18)), 12)

    def test_has_die_and_consume(self):
        from engine.subclass_features import (
            has_superiority_die, use_superiority_die,
        )
        bm = self._bm(dice_left=2)
        self.assertTrue(has_superiority_die(bm))
        roll = use_superiority_die(bm)
        self.assertGreaterEqual(roll, 1)
        self.assertLessEqual(roll, 8)
        self.assertEqual(bm.superiority_dice_left, 1)

    def test_no_die_left_blocks(self):
        from engine.subclass_features import (
            has_superiority_die, use_superiority_die,
        )
        bm = self._bm(dice_left=0)
        self.assertFalse(has_superiority_die(bm))
        self.assertEqual(use_superiority_die(bm), 0)

    def test_advisor_recommends_precision_when_miss_by_small_margin(self):
        from engine.subclass_features import maneuver_advisor
        bm = self._bm()
        recs = maneuver_advisor(bm, {
            "trigger": "on-attack-roll",
            "attack_total": 12,
            "target_ac": 17,  # miss by 5, die size 8
        })
        names = [r[0] for r in recs]
        self.assertIn("Precision Attack", names)

    def test_advisor_recommends_riposte_on_miss_reaction(self):
        from engine.subclass_features import maneuver_advisor
        bm = self._bm()
        recs = maneuver_advisor(bm, {"trigger": "reaction-on-miss"})
        names = [r[0] for r in recs]
        self.assertIn("Riposte", names)

    def test_advisor_recommends_pushing_attack_near_hazard(self):
        from engine.subclass_features import maneuver_advisor
        bm = self._bm(maneuvers=["Pushing Attack"])
        recs = maneuver_advisor(bm, {
            "trigger": "on-hit",
            "hazard_within_15": True,
        })
        names = [r[0] for r in recs]
        self.assertIn("Pushing Attack", names)


class TestMetamagic(unittest.TestCase):
    def _sorc(self, sp_points=5, metamagic=None):
        stats = CreatureStats(
            name="Sorc", size="Medium",
            hit_points=38, armor_class=13, speed=30,
            abilities=AbilityScores(charisma=18),
            actions=[],
            features=[Feature(
                name="Metamagic", mechanic="metamagic",
                mechanic_value=",".join(metamagic or [
                    "Quickened Spell", "Twinned Spell",
                    "Careful Spell", "Subtle Spell",
                ]),
                feature_type="class",
            )],
            proficiency_bonus=3,
            character_level=5,
        )
        e = Entity(stats, 5, 5, is_player=True)
        e.sorcery_points_left = sp_points
        return e

    def test_quickened_costs_two_sorcery_points(self):
        from engine.subclass_features import (
            sorcery_cost, can_apply_metamagic, apply_metamagic,
        )
        self.assertEqual(sorcery_cost("Quickened Spell"), 2)
        s = self._sorc(sp_points=2)
        self.assertTrue(can_apply_metamagic(s, "Quickened Spell"))
        self.assertTrue(apply_metamagic(s, "Quickened Spell"))
        self.assertEqual(s.sorcery_points_left, 0)

    def test_twinned_scales_with_spell_level(self):
        from engine.subclass_features import sorcery_cost
        self.assertEqual(sorcery_cost("Twinned Spell", 3), 3)
        self.assertEqual(sorcery_cost("Twinned Spell", 5), 5)
        # Min 1 for cantrips
        self.assertEqual(sorcery_cost("Twinned Spell", 0), 1)

    def test_metamagic_not_in_known_blocks(self):
        from engine.subclass_features import can_apply_metamagic
        s = self._sorc(metamagic=["Twinned Spell"])
        self.assertFalse(can_apply_metamagic(s, "Heightened Spell"))

    def test_advisor_suggests_careful_when_allies_in_aoe(self):
        from engine.subclass_features import metamagic_advisor
        s = self._sorc()
        fireball = _spells["Fireball"]
        recs = metamagic_advisor(s, fireball, allies_in_aoe=2)
        names = [r[0] for r in recs]
        self.assertIn("Careful Spell", names)

    def test_advisor_suggests_quickened_after_action(self):
        from engine.subclass_features import metamagic_advisor
        s = self._sorc()
        firebolt = _spells["Fire Bolt"]
        recs = metamagic_advisor(s, firebolt, already_used_action=True)
        names = [r[0] for r in recs]
        self.assertIn("Quickened Spell", names)


class TestArcaneRecovery(unittest.TestCase):
    def _wiz(self, level=5):
        stats = CreatureStats(
            name="Wiz", size="Medium",
            hit_points=30, armor_class=12, speed=30,
            abilities=AbilityScores(intelligence=18),
            actions=[],
            features=[Feature(
                name="Arcane Recovery", mechanic="arcane_recovery",
                feature_type="class", uses_per_day=1,
            )],
            proficiency_bonus=3,
            character_level=level,
        )
        stats.spell_slots = {"1st": 4, "2nd": 3, "3rd": 2,
                              "4th": 0, "5th": 0,
                              "6th": 0, "7th": 0, "8th": 0,
                              "9th": 0}
        e = Entity(stats, 5, 5, is_player=True)
        e.spell_slots = dict(stats.spell_slots)
        e.feature_uses["Arcane Recovery"] = 1
        return e

    def test_cap_is_ceil_half_level(self):
        from engine.subclass_features import arcane_recovery_max_levels
        self.assertEqual(arcane_recovery_max_levels(self._wiz(5)), 3)
        self.assertEqual(arcane_recovery_max_levels(self._wiz(10)), 5)
        self.assertEqual(arcane_recovery_max_levels(self._wiz(1)), 1)

    def test_can_restore_within_cap(self):
        from engine.subclass_features import apply_arcane_recovery
        w = self._wiz(5)
        # Consume some slots first
        w.spell_slots["3rd"] = 0
        w.spell_slots["2nd"] = 0
        ok, msg = apply_arcane_recovery(w, {3: 1})  # 3 slot-levels = cap
        self.assertTrue(ok)
        self.assertEqual(w.spell_slots["3rd"], 1)
        # Used up for the day
        self.assertFalse(
            apply_arcane_recovery(w, {1: 1})[0],
            "Should refuse second use same day")

    def test_cannot_restore_above_cap(self):
        from engine.subclass_features import apply_arcane_recovery
        w = self._wiz(5)
        # Cap is 3 slot-levels; ask for 4
        ok, msg = apply_arcane_recovery(w, {2: 2})  # 4 levels
        self.assertFalse(ok)
        self.assertIn("exceeds cap", msg)

    def test_cannot_restore_sixth_level_or_higher(self):
        from engine.subclass_features import apply_arcane_recovery
        w = self._wiz(level=12)  # cap = 6
        ok, msg = apply_arcane_recovery(w, {6: 1})
        self.assertFalse(ok)
        self.assertIn("6th-level", msg)


if __name__ == "__main__":
    unittest.main()
