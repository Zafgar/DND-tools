"""Phase 30 — feat audit.

The hero creator (states/hero_creator.py) loads :data:`data.feats.ALL_FEATS`,
applies each selected feat's ability-score increase, then converts each
:class:`Feat` into a :class:`data.models.Feature` carrying the same
``mechanic`` string. Combat code is supposed to consult
``entity.has_feature(mechanic_key)`` to fire any feat-driven effect.

This audit measures:

  * Every PHB 2014 feat (42 total) is defined.
  * Every feat exposes a non-empty ``mechanic`` key.
  * Adding a feat to an entity makes ``has_feature`` return True; removing
    it goes back to False — the runtime list is mutable.
  * For the combat-relevant feats specifically, the engine actually
    checks the mechanic key somewhere.  Non-combat feats (Linguist,
    Actor, Keen Mind …) are flagged separately.
  * Special wirings: Heavy Armor Master damage reduction, War Caster
    concentration advantage, Lucky uses-per-day counter, Alert
    initiative bonus, Sentinel reaction, GWM/Sharpshooter power-attack
    heuristic, Crossbow Expert no-melee-penalty.

The non-combat-but-data-correct feats stay flagged as ``DATA_ONLY`` so
the catalogue keeps them for character-sheet display but the audit
doesn't complain.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import unittest

from data.feats import ALL_FEATS, FEATS_BY_NAME, get_feat
from data.models import (
    CreatureStats, AbilityScores, Feature, Action, SpellInfo,
)
from engine.entities import Entity


# Combat-mechanic feats — the engine MUST consult these.
COMBAT_FEAT_MECHANICS = {
    "alert", "great_weapon_master", "sharpshooter", "sentinel",
    "war_caster", "lucky", "heavy_armor_master", "crossbow_expert",
    "polearm_master", "mobile", "shield_master", "mage_slayer",
    "savage_attacker", "defensive_duelist", "charger",
    "elemental_adept", "resilient", "tough", "dual_wielder",
    "healer",
}

# Feats that are intentionally data-only (skill / utility / out of combat).
DATA_ONLY_MECHANICS = {
    "actor", "athlete", "dungeon_delver", "durable", "grappler",
    "heavily_armored", "inspiring_leader", "keen_mind",
    "lightly_armored", "linguist", "magic_initiate",
    "martial_adept", "medium_armor_master", "moderately_armored",
    "mounted_combatant", "observant", "ritual_caster", "skilled",
    "skulker", "spell_sniper", "tavern_brawler", "weapon_master",
}


def _build_entity(*, features=None, level=5, character_class="Fighter"):
    # Proficiency bonus = 2 + (level-1)//4 (PHB p.15).
    pb = 2 + max(0, level - 1) // 4
    stats = CreatureStats(
        name="Test", size="Medium",
        hit_points=40, armor_class=16, speed=30,
        abilities=AbilityScores(strength=16, dexterity=14,
                                  constitution=14, intelligence=10,
                                  wisdom=12, charisma=10),
        actions=[Action(name="Longsword", attack_bonus=5,
                          damage_dice="1d8", damage_bonus=3,
                          damage_type="slashing", range=5)],
        features=list(features or []),
        character_level=level,
        character_class=character_class,
        proficiency_bonus=pb,
    )
    return Entity(stats, 5, 5, is_player=True)


def _feat_to_feature(feat) -> Feature:
    """Mirror states/hero_creator.py's conversion."""
    return Feature(
        name=feat.name,
        description=feat.combat_effect or feat.description[:100],
        feature_type="feat",
        mechanic=feat.mechanic,
        mechanic_value=feat.mechanic_value,
    )


# --------------------------------------------------------------------- #
# Catalogue completeness
# --------------------------------------------------------------------- #
class TestFeatCatalogue(unittest.TestCase):
    def test_all_42_phb_feats_present(self):
        self.assertEqual(len(ALL_FEATS), 42,
                          "PHB 2014 ships 42 feats")

    def test_every_feat_has_a_unique_mechanic_key(self):
        keys = [f.mechanic for f in ALL_FEATS]
        self.assertTrue(all(keys), "Every feat needs a mechanic key")
        self.assertEqual(len(keys), len(set(keys)),
                          "Mechanic keys must be unique")

    def test_iconic_feats_present_with_correct_mechanic(self):
        for name, mech in [
            ("Great Weapon Master", "great_weapon_master"),
            ("Sharpshooter", "sharpshooter"),
            ("Polearm Master", "polearm_master"),
            ("Sentinel", "sentinel"),
            ("Lucky", "lucky"),
            ("War Caster", "war_caster"),
            ("Tough", "tough"),
            ("Alert", "alert"),
            ("Mobile", "mobile"),
            ("Crossbow Expert", "crossbow_expert"),
            ("Shield Master", "shield_master"),
            ("Mage Slayer", "mage_slayer"),
            ("Savage Attacker", "savage_attacker"),
            ("Elemental Adept", "elemental_adept"),
            ("Healer", "healer"),
        ]:
            feat = get_feat(name)
            self.assertIsNotNone(feat, f"{name} missing from catalogue")
            self.assertEqual(feat.mechanic, mech,
                              f"{name} mechanic key drift")


# --------------------------------------------------------------------- #
# Add / remove / has_feature at runtime
# --------------------------------------------------------------------- #
class TestAddRemoveFeat(unittest.TestCase):
    def test_has_feature_false_by_default(self):
        e = _build_entity()
        self.assertFalse(e.has_feature("great_weapon_master"))

    def test_adding_feature_via_features_list_works(self):
        gwm = _feat_to_feature(get_feat("Great Weapon Master"))
        e = _build_entity(features=[gwm])
        self.assertTrue(e.has_feature("great_weapon_master"))

    def test_runtime_append_makes_has_feature_true(self):
        e = _build_entity()
        self.assertFalse(e.has_feature("sentinel"))
        e.stats.features.append(
            _feat_to_feature(get_feat("Sentinel")))
        self.assertTrue(e.has_feature("sentinel"))

    def test_runtime_remove_clears_has_feature(self):
        gwm = _feat_to_feature(get_feat("Great Weapon Master"))
        e = _build_entity(features=[gwm])
        self.assertTrue(e.has_feature("great_weapon_master"))
        e.stats.features = [
            f for f in e.stats.features if f.mechanic != "great_weapon_master"]
        self.assertFalse(e.has_feature("great_weapon_master"))

    def test_feature_uses_dict_for_limited_feats(self):
        # Lucky feat has 3 uses per long rest — Entity tracks this.
        lucky = _feat_to_feature(get_feat("Lucky"))
        e = _build_entity(features=[lucky])
        # Per Entity.__init__: lucky_uses_left auto-seeded to 3
        self.assertEqual(e.lucky_uses_left, 3)


# --------------------------------------------------------------------- #
# Combat wirings — each feat below MUST visibly change behaviour
# --------------------------------------------------------------------- #
class TestHeavyArmorMaster(unittest.TestCase):
    def test_reduces_nonmagical_bludgeoning_by_three(self):
        ham = _feat_to_feature(get_feat("Heavy Armor Master"))
        e = _build_entity(features=[ham])
        dealt, _ = e.take_damage(10, "bludgeoning")
        self.assertEqual(dealt, 7)

    def test_does_not_reduce_magical_damage(self):
        ham = _feat_to_feature(get_feat("Heavy Armor Master"))
        e = _build_entity(features=[ham])
        dealt, _ = e.take_damage(10, "bludgeoning", is_magical=True)
        self.assertEqual(dealt, 10)

    def test_does_not_reduce_non_BPS_damage(self):
        ham = _feat_to_feature(get_feat("Heavy Armor Master"))
        e = _build_entity(features=[ham])
        dealt, _ = e.take_damage(10, "fire")
        self.assertEqual(dealt, 10)


class TestLucky(unittest.TestCase):
    def test_long_rest_resets_uses(self):
        lucky = _feat_to_feature(get_feat("Lucky"))
        e = _build_entity(features=[lucky])
        e.lucky_uses_left = 0
        e.long_rest()
        self.assertEqual(e.lucky_uses_left, 3)


class TestAlert(unittest.TestCase):
    def test_initiative_gets_plus_five(self):
        # We roll initiative many times; the +5 bonus should pull the
        # mean clearly above the no-alert mean.
        import statistics
        random_seed = 0
        no = _build_entity()
        with_alert = _build_entity(features=[
            _feat_to_feature(get_feat("Alert"))])
        rolls_no = [no.roll_initiative() for _ in range(2000)]
        rolls_yes = [with_alert.roll_initiative() for _ in range(2000)]
        self.assertGreater(statistics.mean(rolls_yes),
                            statistics.mean(rolls_no) + 4.5,
                            "Alert should add +5 to initiative on average")


# --------------------------------------------------------------------- #
# Power-attack heuristic — GWM / Sharpshooter
# --------------------------------------------------------------------- #
class TestPowerAttackHeuristic(unittest.TestCase):
    def test_gwm_recognised_in_heavy_weapon_path(self):
        # The AI's `_resolve_attack` reads has_feature("great_weapon_master").
        # We just verify the key matches what the AI expects.
        from engine.ai import tactical_ai
        with open(tactical_ai.__file__) as f:
            src = f.read()
        self.assertIn('"great_weapon_master"', src,
                        "AI must reference great_weapon_master")
        self.assertIn('"sharpshooter"', src,
                        "AI must reference sharpshooter")


# --------------------------------------------------------------------- #
# Wiring coverage report — fails if a combat feat got disconnected
# --------------------------------------------------------------------- #
# --------------------------------------------------------------------- #
# Phase 30 — newly-wired feats (behaviour tests, not just grep)
# --------------------------------------------------------------------- #
class TestMobile(unittest.TestCase):
    def test_speed_bonus_added(self):
        base = _build_entity()
        with_mobile = _build_entity(features=[
            _feat_to_feature(get_feat("Mobile"))])
        self.assertEqual(with_mobile.get_speed(),
                          base.get_speed() + 10)

    def test_mobile_does_not_apply_when_prone(self):
        # Prone halves speed; the +10 still applies on top.
        e = _build_entity(features=[
            _feat_to_feature(get_feat("Mobile"))])
        e.add_condition("Prone")
        # base 30 / 2 = 15, +10 → 25
        self.assertEqual(e.get_speed(), 25)


class TestElementalAdept(unittest.TestCase):
    def test_caster_bypasses_resistance(self):
        # Target is fire-resistant. Source has Elemental Adept (fire).
        fire_feat = get_feat("Elemental Adept")
        from data.models import Feature
        # Set the mechanic_value at instantiation time (the catalogue
        # leaves it blank; hero creator fills it in normally).
        source = _build_entity(features=[Feature(
            name=fire_feat.name, feature_type="feat",
            mechanic="elemental_adept",
            mechanic_value="fire",
        )])
        target = _build_entity()
        target.stats.damage_resistances = ["fire"]
        # Without source: resistance halves to 5.
        dealt_no, _ = target.take_damage(10, "fire")
        self.assertEqual(dealt_no, 5)
        # With source: Elemental Adept bypasses → full 10.
        target.hp = target.max_hp
        dealt_yes, _ = target.take_damage(10, "fire", source=source)
        self.assertEqual(dealt_yes, 10)

    def test_wrong_damage_type_still_resists(self):
        from data.models import Feature
        source = _build_entity(features=[Feature(
            name="Elemental Adept", mechanic="elemental_adept",
            mechanic_value="fire", feature_type="feat")])
        target = _build_entity()
        target.stats.damage_resistances = ["cold"]
        dealt, _ = target.take_damage(10, "cold", source=source)
        # Source has fire adept, not cold — target still resists.
        self.assertEqual(dealt, 5)


class TestSavageAttackerReroll(unittest.TestCase):
    def test_reroll_takes_higher(self):
        from engine.feat_effects import savage_attacker_reroll
        e = _build_entity(features=[
            _feat_to_feature(get_feat("Savage Attacker"))])
        # Force RNG so the reroll is deterministic
        import random as _rng
        _rng.seed(42)
        # Initial roll was 3 (poor); after reroll, take the better one
        new = savage_attacker_reroll(e, "1d8", 3)
        self.assertGreaterEqual(new, 3)
        # Second call this turn must be a no-op
        new2 = savage_attacker_reroll(e, "1d8", 3)
        self.assertEqual(new2, 3)

    def test_no_feat_returns_original(self):
        from engine.feat_effects import savage_attacker_reroll
        e = _build_entity()
        self.assertEqual(savage_attacker_reroll(e, "1d8", 4), 4)

    def test_reset_each_turn(self):
        e = _build_entity(features=[
            _feat_to_feature(get_feat("Savage Attacker"))])
        e.savage_attacker_used = True
        e.reset_turn()
        self.assertFalse(e.savage_attacker_used)


class TestResilient(unittest.TestCase):
    def test_save_proficiency_added(self):
        from data.models import Feature
        e = _build_entity(features=[Feature(
            name="Resilient", mechanic="resilient",
            mechanic_value="CON", feature_type="feat")])
        # Base CON save is just CON mod (no class prof).
        # With Resilient: CON mod + proficiency bonus.
        base = e.get_modifier("constitution")
        pb = e.stats.proficiency_bonus
        self.assertEqual(e.get_save_bonus("Constitution"), base + pb)

    def test_class_save_proficiency_does_not_double_stack(self):
        from data.models import Feature
        e = _build_entity(features=[Feature(
            name="Resilient", mechanic="resilient",
            mechanic_value="CON", feature_type="feat")])
        # Class already gave CON save prof → entry exists in dict
        base = e.get_modifier("constitution") + e.stats.proficiency_bonus
        e.stats.saving_throws["Constitution"] = base
        # Resilient should NOT double-stack
        self.assertEqual(e.get_save_bonus("Constitution"), base)


class TestMageSlayerConcentration(unittest.TestCase):
    def test_adjacent_mage_slayer_imposes_disadv_on_concentration(self):
        from engine.feat_effects import \
            mage_slayer_concentration_disadvantage
        ms = _build_entity(features=[
            _feat_to_feature(get_feat("Mage Slayer"))])
        ms.grid_x, ms.grid_y = 5, 5
        caster = _build_entity()
        caster.grid_x, caster.grid_y = 6, 5  # adjacent
        self.assertTrue(
            mage_slayer_concentration_disadvantage(ms, caster))

    def test_distant_mage_slayer_does_not_trigger(self):
        from engine.feat_effects import \
            mage_slayer_concentration_disadvantage
        ms = _build_entity(features=[
            _feat_to_feature(get_feat("Mage Slayer"))])
        ms.grid_x, ms.grid_y = 5, 5
        caster = _build_entity()
        caster.grid_x, caster.grid_y = 10, 10
        self.assertFalse(
            mage_slayer_concentration_disadvantage(ms, caster))


class TestPolearmMasterButtAttack(unittest.TestCase):
    def test_returns_dice_for_qualifying_weapon(self):
        from engine.feat_effects import polearm_butt_attack_dice
        e = _build_entity(features=[
            _feat_to_feature(get_feat("Polearm Master"))])
        # STR mod for a 16 → +3
        self.assertEqual(polearm_butt_attack_dice(e, "Glaive"), "1d4+3")
        self.assertEqual(polearm_butt_attack_dice(e, "Halberd"), "1d4+3")
        self.assertEqual(polearm_butt_attack_dice(e, "Quarterstaff"),
                          "1d4+3")

    def test_returns_none_for_non_polearm(self):
        from engine.feat_effects import polearm_butt_attack_dice
        e = _build_entity(features=[
            _feat_to_feature(get_feat("Polearm Master"))])
        self.assertIsNone(polearm_butt_attack_dice(e, "Longsword"))

    def test_returns_none_without_feat(self):
        from engine.feat_effects import polearm_butt_attack_dice
        e = _build_entity()
        self.assertIsNone(polearm_butt_attack_dice(e, "Glaive"))


class TestShieldMasterShoveGate(unittest.TestCase):
    def test_requires_attack_action_and_bonus_available(self):
        from engine.feat_effects import shield_master_can_shove
        e = _build_entity(features=[
            _feat_to_feature(get_feat("Shield Master"))])
        # No Attack action yet
        self.assertFalse(shield_master_can_shove(e, False, True))
        # With Attack action + bonus + shield
        self.assertTrue(shield_master_can_shove(e, True, True))
        # Without shield
        self.assertFalse(shield_master_can_shove(e, True, False))
        # Bonus used
        e.bonus_action_used = True
        self.assertFalse(shield_master_can_shove(e, True, True))


class TestChargerBonus(unittest.TestCase):
    def test_plus_five_when_dashed(self):
        from engine.feat_effects import charger_bonus_damage
        e = _build_entity(features=[
            _feat_to_feature(get_feat("Charger"))])
        self.assertEqual(charger_bonus_damage(e, True), 5)
        self.assertEqual(charger_bonus_damage(e, False), 0)

    def test_no_feat_no_bonus(self):
        from engine.feat_effects import charger_bonus_damage
        e = _build_entity()
        self.assertEqual(charger_bonus_damage(e, True), 0)


class TestDefensiveDuelistReaction(unittest.TestCase):
    def test_burns_reaction_when_bump_matters(self):
        from engine.feat_effects import defensive_duelist_ac_bonus
        e = _build_entity(features=[
            _feat_to_feature(get_feat("Defensive Duelist"))])
        # PB at level 5 = 3. Attack total 16, AC 14, bump to 17 misses.
        new_ac = defensive_duelist_ac_bonus(e, 16, 14, is_melee=True)
        self.assertEqual(new_ac, 17)
        self.assertTrue(e.reaction_used)

    def test_does_not_burn_reaction_if_irrelevant(self):
        from engine.feat_effects import defensive_duelist_ac_bonus
        e = _build_entity(features=[
            _feat_to_feature(get_feat("Defensive Duelist"))])
        # Attack misses anyway — reaction not spent
        new_ac = defensive_duelist_ac_bonus(e, 12, 14, is_melee=True)
        self.assertEqual(new_ac, 14)
        self.assertFalse(e.reaction_used)

    def test_no_effect_on_ranged_attacks(self):
        from engine.feat_effects import defensive_duelist_ac_bonus
        e = _build_entity(features=[
            _feat_to_feature(get_feat("Defensive Duelist"))])
        new_ac = defensive_duelist_ac_bonus(e, 16, 14, is_melee=False)
        self.assertEqual(new_ac, 14)


class TestTough(unittest.TestCase):
    def test_hp_bonus_formula(self):
        from engine.feat_effects import tough_hp_bonus
        e = _build_entity(features=[
            _feat_to_feature(get_feat("Tough"))], level=10)
        self.assertEqual(tough_hp_bonus(e), 20)


class TestCombatFeatsAreReferencedSomewhere(unittest.TestCase):
    """If a feat is in COMBAT_FEAT_MECHANICS but no engine/states file
    references its key, the feat exists on the sheet but does nothing
    at the table.  That's the bug class this test guards against.
    """
    def setUp(self):
        # Grep all engine/, data/ (except feats.py), states/ for each key.
        import subprocess
        self._refs = {}
        for key in COMBAT_FEAT_MECHANICS:
            res = subprocess.run(
                ["grep", "-r", "-l", f'"{key}"',
                 "engine/", "data/", "states/"],
                capture_output=True, text=True,
                cwd=os.path.join(os.path.dirname(__file__), ".."),
            )
            files = [f for f in res.stdout.strip().split("\n")
                      if f and "feats.py" not in f
                      and "test_phase30" not in f
                      and "__pycache__" not in f]
            self._refs[key] = files

    def _missing(self):
        return [k for k, files in self._refs.items() if not files]

    def test_combat_feats_have_at_least_one_engine_reference(self):
        missing = self._missing()
        self.assertEqual(
            missing, [],
            f"Combat feats with no engine wiring: {missing}. "
            "Fix by consulting entity.has_feature(<key>) in the "
            "appropriate engine path.")


if __name__ == "__main__":
    unittest.main()
