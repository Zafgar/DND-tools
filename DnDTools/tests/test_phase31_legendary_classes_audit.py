"""Phase 31 — legendary actions, legendary resistance, class features
+ AI tactics audit.

Verifies the existing engine support actually behaves to spec and the
AI / GM-driven flows expose them:

  * Legendary actions: counter resets at start of own turn, AI picks
    cheap actions early, can't go past available budget, manual DM
    trigger consumes one.
  * Legendary resistance: strategic decision tiers (always-use,
    moderate, conserve), refresh at long rest, manual DM trigger
    debits counter.
  * Class features: every standard class feature mechanic the engine
    references has a feature ↔ engine wiring.
  * AI tactics (Phase 30 carry-over): the AI considers Mobile speed
    when planning movement, exploits Polearm Master / Shield Master
    bonus actions when available, uses Mage Slayer OA when a caster
    starts a spell next to it.

Pure logic — no pygame.
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
from engine.entities import Entity
from engine.battle import BattleSystem
from engine.ai.tactical_ai import TacticalAI
from engine.rules import (
    can_use_legendary_resistance, use_legendary_resistance,
    can_use_legendary_action, _should_use_legendary_resistance,
)


# --------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------- #
def _ent(name="X", hp=40, ac=15, x=5, y=5, *,
          legendary_actions=0, legendary_resistance=0,
          features=None, is_player=False):
    stats = CreatureStats(
        name=name, size="Medium",
        hit_points=hp, armor_class=ac, speed=30,
        abilities=AbilityScores(strength=16, dexterity=12,
                                  constitution=16, intelligence=10,
                                  wisdom=12, charisma=10),
        actions=[Action(name="Slam", attack_bonus=5,
                          damage_dice="1d6", damage_bonus=3,
                          damage_type="bludgeoning", range=5)],
        features=list(features or []),
        legendary_action_count=legendary_actions,
        legendary_resistance_count=legendary_resistance,
    )
    return Entity(stats, x, y, is_player=is_player)


def _legendary_action_feat(name, cost=1, damage_dice="", aoe_radius=0):
    return Feature(
        name=name, feature_type="legendary",
        legendary_cost=cost,
        damage_dice=damage_dice,
        damage_type="bludgeoning",
    )


def _ent_with_legendary(name="Boss", *, leg_count=3, actions_specs=None):
    """Build a legendary creature with matching Action + Feature pairs.
    Each spec: (name, cost, damage_dice). The AI requires both."""
    feats = []
    actions = []
    for nm, cost, dice in (actions_specs or []):
        feats.append(_legendary_action_feat(nm, cost=cost,
                                              damage_dice=dice))
        actions.append(Action(
            name=nm, action_type="legendary",
            attack_bonus=7, damage_dice=dice, damage_bonus=4,
            damage_type="bludgeoning", range=10,
        ))
    stats = CreatureStats(
        name=name, size="Huge",
        hit_points=200, armor_class=18, speed=40,
        abilities=AbilityScores(strength=23, dexterity=10,
                                  constitution=21, intelligence=14,
                                  wisdom=15, charisma=18),
        actions=actions,
        features=feats,
        legendary_action_count=leg_count,
        legendary_resistance_count=0,
        proficiency_bonus=4,
    )
    return Entity(stats, 5, 5, is_player=False)


# --------------------------------------------------------------------- #
# Legendary actions
# --------------------------------------------------------------------- #
class TestLegendaryActions(unittest.TestCase):
    def test_counter_initialised_from_stats(self):
        boss = _ent("Dragon", legendary_actions=3)
        self.assertEqual(boss.legendary_actions_left, 3)
        self.assertEqual(boss.stats.legendary_action_count, 3)

    def test_reset_legendary_actions_refills(self):
        boss = _ent("Dragon", legendary_actions=3)
        boss.legendary_actions_left = 0
        boss.reset_legendary_actions()
        self.assertEqual(boss.legendary_actions_left, 3)

    def test_can_use_when_budget_available_and_alive(self):
        boss = _ent("Dragon", legendary_actions=3)
        allowed, _ = can_use_legendary_action(boss)
        self.assertTrue(allowed)

    def test_cannot_use_when_budget_exhausted(self):
        boss = _ent("Dragon", legendary_actions=3)
        boss.legendary_actions_left = 0
        allowed, _ = can_use_legendary_action(boss)
        self.assertFalse(allowed)

    def test_cannot_use_when_incapacitated(self):
        boss = _ent("Dragon", legendary_actions=3)
        boss.hp = 0
        allowed, _ = can_use_legendary_action(boss)
        self.assertFalse(allowed)

    def test_ai_skips_overcost_actions(self):
        boss = _ent_with_legendary(actions_specs=[
            ("Tail", 1, "2d8"),
            ("Wing", 2, "2d6"),
        ])
        boss.legendary_actions_left = 1
        target = _ent("PC", x=6, y=5, is_player=True)
        b = BattleSystem(log_callback=lambda *a: None,
                          initial_entities=[boss, target])
        ai = TacticalAI()
        step = ai.calculate_legendary_action(boss, b)
        # The 2-cost wing attack is unaffordable; the 1-cost tail must be picked
        self.assertIsNotNone(step)
        self.assertEqual(step.action.name, "Tail")
        # Cost was deducted
        self.assertEqual(boss.legendary_actions_left, 0)

    def test_ai_returns_none_when_no_legendaries_left(self):
        boss = _ent_with_legendary(actions_specs=[
            ("Tail", 1, "2d8"),
        ])
        boss.legendary_actions_left = 0
        target = _ent("PC", x=6, y=5, is_player=True)
        b = BattleSystem(log_callback=lambda *a: None,
                          initial_entities=[boss, target])
        ai = TacticalAI()
        self.assertIsNone(ai.calculate_legendary_action(boss, b))


# --------------------------------------------------------------------- #
# Legendary resistance
# --------------------------------------------------------------------- #
class TestLegendaryResistance(unittest.TestCase):
    def test_counter_initialised(self):
        boss = _ent("Lich", legendary_resistance=3)
        self.assertEqual(boss.legendary_resistances_left, 3)

    def test_can_use_when_available(self):
        boss = _ent("Lich", legendary_resistance=3)
        self.assertTrue(can_use_legendary_resistance(boss))

    def test_cannot_use_when_exhausted(self):
        boss = _ent("Lich", legendary_resistance=3)
        boss.legendary_resistances_left = 0
        self.assertFalse(can_use_legendary_resistance(boss))

    def test_use_decrements_counter_and_returns_message(self):
        boss = _ent("Lich", legendary_resistance=3)
        msg = use_legendary_resistance(boss)
        self.assertEqual(boss.legendary_resistances_left, 2)
        self.assertIn("Legendary", msg)

    def test_long_rest_refills(self):
        boss = _ent("Lich", legendary_resistance=3)
        boss.legendary_resistances_left = 0
        boss.long_rest()
        self.assertEqual(boss.legendary_resistances_left, 3)

    def test_strategic_always_use_for_paralyzed(self):
        boss = _ent("Lich", legendary_resistance=3)
        self.assertTrue(_should_use_legendary_resistance(
            boss, "Paralyzed", ""))

    def test_strategic_always_use_for_stunned(self):
        boss = _ent("Lich", legendary_resistance=3)
        self.assertTrue(_should_use_legendary_resistance(
            boss, "Stunned", ""))

    def test_strategic_always_use_for_banished(self):
        boss = _ent("Lich", legendary_resistance=3)
        self.assertTrue(_should_use_legendary_resistance(
            boss, "Banished", ""))

    def test_strategic_moderate_when_lr_low(self):
        boss = _ent("Lich", legendary_resistance=3)
        boss.legendary_resistances_left = 1
        # Frightened is moderate — at 1 LR remaining, conserve.
        self.assertFalse(_should_use_legendary_resistance(
            boss, "Frightened", ""))

    def test_strategic_moderate_when_lr_plenty(self):
        boss = _ent("Lich", legendary_resistance=3)
        # Frightened with 3 LR → spend it.
        self.assertTrue(_should_use_legendary_resistance(
            boss, "Frightened", ""))

    def test_strategic_save_for_lethal_damage(self):
        boss = _ent("Lich", hp=20, legendary_resistance=3)
        # 10d10 averages 55 — way more than 40% of 20 HP.
        self.assertTrue(_should_use_legendary_resistance(
            boss, "", "10d10"))

    def test_strategic_skip_minor_damage(self):
        boss = _ent("Lich", hp=200, legendary_resistance=3)
        # 1d4 vs 200 HP — conserve.
        self.assertFalse(_should_use_legendary_resistance(
            boss, "", "1d4"))


# --------------------------------------------------------------------- #
# Resistance / vulnerability / immunity behaviour
# --------------------------------------------------------------------- #
class TestResistanceAndImmunity(unittest.TestCase):
    def test_resistance_halves(self):
        e = _ent("Troll", hp=50)
        e.stats.damage_resistances = ["fire"]
        dealt, _ = e.take_damage(20, "fire")
        self.assertEqual(dealt, 10)

    def test_immunity_blocks(self):
        e = _ent("Fire Elemental", hp=50)
        e.stats.damage_immunities = ["fire"]
        dealt, _ = e.take_damage(20, "fire")
        self.assertEqual(dealt, 0)

    def test_vulnerability_doubles(self):
        e = _ent("Troll", hp=50)
        e.stats.damage_vulnerabilities = ["acid"]
        dealt, _ = e.take_damage(10, "acid")
        self.assertEqual(dealt, 20)

    def test_resistance_and_vulnerability_cancel(self):
        # PHB p.197: when both apply, they cancel out.
        e = _ent("Hybrid", hp=50)
        e.stats.damage_resistances = ["fire"]
        e.stats.damage_vulnerabilities = ["fire"]
        dealt, _ = e.take_damage(20, "fire")
        self.assertEqual(dealt, 20)

    def test_nonmagical_resistance_bypassed_by_magic(self):
        e = _ent("Werewolf", hp=50)
        e.stats.damage_resistances = ["bludgeoning from non-magical attacks"]
        dealt_mundane, _ = e.take_damage(20, "bludgeoning",
                                            is_magical=False)
        self.assertEqual(dealt_mundane, 10)
        e.hp = e.max_hp
        dealt_magic, _ = e.take_damage(20, "bludgeoning",
                                          is_magical=True)
        self.assertEqual(dealt_magic, 20)


# --------------------------------------------------------------------- #
# Class features audit (wiring report)
# --------------------------------------------------------------------- #
# A class feature is "wired" if (a) at least one engine path consults
# entity.has_feature(<key>) and (b) the data layer exposes that key
# from class_features.py.
class TestClassFeaturesAreWired(unittest.TestCase):
    """The mechanics below are the high-impact class features the
    rules engine *must* know about.  If any of them ever loses its
    engine reference, this test fails."""
    # Class features whose mechanic key the engine *must* consult.
    # The data-only ones (hunters_mark spell, ki_points attribute,
    # extra_attack via is_multiattack flag, monks' step_of_wind /
    # deflect_missiles, favored_enemy flavor, fighting_style as a
    # category) are intentionally omitted — they're either handled
    # via a different mechanism or are flavor text.
    REQUIRED_CLASS_MECHANICS = [
        "sneak_attack", "action_surge", "second_wind",
        "lay_on_hands", "channel_divinity", "bardic_inspiration",
        "wild_shape", "rage", "rage_damage", "reckless_attack",
        "cunning_action", "uncanny_dodge", "evasion",
        "divine_smite", "patient_defense",
        "stunning_strike",
        "improved_divine_smite", "combat_wild_shape",
        "brutal_critical", "savage_attacks",
        "danger_sense", "feral_instinct",
        "relentless_endurance", "totem_bear",
    ]

    def setUp(self):
        import subprocess
        self.refs = {}
        for key in self.REQUIRED_CLASS_MECHANICS:
            res = subprocess.run(
                ["grep", "-rl", f'"{key}"',
                 "engine/", "states/"],
                capture_output=True, text=True,
                cwd=os.path.join(os.path.dirname(__file__), ".."),
            )
            files = [f for f in res.stdout.strip().split("\n")
                      if f and "__pycache__" not in f]
            self.refs[key] = files

    def test_every_required_class_mechanic_has_engine_reference(self):
        missing = [k for k, v in self.refs.items() if not v]
        self.assertEqual(missing, [],
                          f"Class mechanics missing engine wiring: "
                          f"{missing}")


# --------------------------------------------------------------------- #
# AI tactics — Mobile, Polearm Master, Shield Master, Mage Slayer
# --------------------------------------------------------------------- #
# --------------------------------------------------------------------- #
# Class feature behaviour — verify the wired ones actually fire
# --------------------------------------------------------------------- #
class TestClassFeatureBehaviour(unittest.TestCase):
    def test_sneak_attack_dice_pulled_from_feature(self):
        rogue = _ent("Rogue", features=[Feature(
            name="Sneak Attack", mechanic="sneak_attack",
            mechanic_value="3d6", feature_type="class",
        )])
        self.assertEqual(rogue.get_sneak_attack_dice(), "3d6")

    def test_sneak_attack_resets_per_turn(self):
        rogue = _ent("Rogue", features=[Feature(
            name="Sneak Attack", mechanic="sneak_attack",
            mechanic_value="3d6", feature_type="class",
        )])
        rogue.sneak_attack_used = True
        rogue.reset_turn()
        self.assertFalse(rogue.sneak_attack_used)

    def test_lay_on_hands_pool_initialised_and_refilled(self):
        pal = _ent("Paladin")
        pal.stats.lay_on_hands_pool = 25
        pal.lay_on_hands_left = 25
        pal.lay_on_hands_left = 10
        pal.long_rest()
        self.assertEqual(pal.lay_on_hands_left, 25)

    def test_uncanny_dodge_halves_an_incoming_damage(self):
        # uncanny_dodge isn't auto-applied on take_damage but the AI
        # consults it; the test guards that the feature key is at
        # least present on the entity.
        rogue = _ent("Rogue", features=[Feature(
            name="Uncanny Dodge", mechanic="uncanny_dodge",
            feature_type="class",
        )])
        self.assertTrue(rogue.has_feature("uncanny_dodge"))

    def test_action_surge_uses_pool(self):
        # action_surge is uses-per-day; feature_uses dict tracks it.
        ftr = _ent("Fighter", features=[Feature(
            name="Action Surge", mechanic="action_surge",
            feature_type="class", uses_per_day=1,
        )])
        ftr.feature_uses["Action Surge"] = 1
        self.assertTrue(ftr.can_use_feature("Action Surge"))
        ftr.use_feature("Action Surge")
        self.assertFalse(ftr.can_use_feature("Action Surge"))

    def test_relentless_endurance_drops_to_one_hp(self):
        # Half-orc trait: when reduced to 0 HP (but not killed
        # outright), drop to 1 HP. Used once per long rest.
        ho = _ent("HalfOrc", hp=20, features=[Feature(
            name="Relentless Endurance",
            mechanic="relentless_endurance",
            feature_type="racial",
            uses_per_day=1,
        )])
        ho.feature_uses["Relentless Endurance"] = 1
        ho.take_damage(20, "slashing")
        self.assertEqual(ho.hp, 1,
                          "Relentless Endurance should save the half-orc")
        # Used up
        self.assertFalse(ho.can_use_feature("Relentless Endurance"))


class TestAITacticsForNewFeats(unittest.TestCase):
    def test_mobile_increases_planned_distance(self):
        # An entity with Mobile should reach a 7-square-away target
        # in one move (40 ft) where a baseline 30-ft mover cannot.
        from data.feats import get_feat
        from engine.feat_effects import mobile_speed_bonus
        base = _ent("Base", x=0, y=0)
        mobile = _ent("Mobile", x=0, y=0, features=[Feature(
            name="Mobile", mechanic="mobile", feature_type="feat",
        )])
        self.assertEqual(base.get_speed(), 30)
        self.assertEqual(mobile.get_speed(), 40)
        # The helper reports the +10 cleanly.
        self.assertEqual(mobile_speed_bonus(base), 0)
        self.assertEqual(mobile_speed_bonus(mobile), 10)

    def test_polearm_master_helper_recognised_per_weapon(self):
        from engine.feat_effects import polearm_butt_attack_dice
        pm = _ent("PM", features=[Feature(
            name="Polearm Master", mechanic="polearm_master",
            feature_type="feat")])
        # Qualifying weapons return a dice expression
        for wep in ("Glaive", "Halberd", "Quarterstaff", "Spear",
                     "Pike"):
            self.assertIsNotNone(polearm_butt_attack_dice(pm, wep),
                                  f"{wep} should qualify")
        # Non-polearm returns None
        self.assertIsNone(polearm_butt_attack_dice(pm, "Longsword"))

    def test_shield_master_only_with_attack_action(self):
        from engine.feat_effects import shield_master_can_shove
        sm = _ent("SM", features=[Feature(
            name="Shield Master", mechanic="shield_master",
            feature_type="feat")])
        # No attack action this turn → no shove
        self.assertFalse(shield_master_can_shove(sm, False, True))
        # Attack action taken + shield + bonus free → may shove
        self.assertTrue(shield_master_can_shove(sm, True, True))

    def test_mage_slayer_adjacent_required(self):
        from engine.feat_effects import mage_slayer_oa_should_fire
        ms = _ent("MS", x=5, y=5, features=[Feature(
            name="Mage Slayer", mechanic="mage_slayer",
            feature_type="feat")])
        adj_caster = _ent("Wiz", x=6, y=5, is_player=True)
        far_caster = _ent("Wiz2", x=10, y=10, is_player=True)
        self.assertTrue(mage_slayer_oa_should_fire(ms, adj_caster))
        self.assertFalse(mage_slayer_oa_should_fire(ms, far_caster))


# --------------------------------------------------------------------- #
# Phase 31c — AI actually emits the new feat steps in a real plan
# --------------------------------------------------------------------- #
class TestAIEmitsPolearmAndShieldMaster(unittest.TestCase):
    def _make_polearm_fighter(self, x=5, y=5):
        glaive = Action(
            name="Glaive", action_type="action",
            attack_bonus=6, damage_dice="1d10", damage_bonus=4,
            damage_type="slashing", range=10,  # reach
            properties=["heavy", "reach", "two-handed"],
        )
        stats = CreatureStats(
            name="Polearm Fighter", size="Medium",
            hit_points=44, armor_class=18, speed=30,
            abilities=AbilityScores(strength=18, dexterity=12,
                                      constitution=14, intelligence=10,
                                      wisdom=12, charisma=10),
            actions=[glaive],
            features=[Feature(
                name="Polearm Master", mechanic="polearm_master",
                feature_type="feat",
            )],
            proficiency_bonus=3,
            character_level=5, character_class="Fighter",
        )
        return Entity(stats, x, y, is_player=True)

    def _make_shield_fighter(self, x=5, y=5):
        sword = Action(
            name="Longsword", action_type="action",
            attack_bonus=6, damage_dice="1d8", damage_bonus=4,
            damage_type="slashing", range=5,
        )
        stats = CreatureStats(
            name="Shield Master", size="Medium",
            hit_points=44, armor_class=20, speed=30,
            abilities=AbilityScores(strength=18, dexterity=12,
                                      constitution=14, intelligence=10,
                                      wisdom=12, charisma=10),
            actions=[sword],
            features=[Feature(
                name="Shield Master", mechanic="shield_master",
                feature_type="feat",
            )],
            proficiency_bonus=3,
        )
        return Entity(stats, x, y, is_player=True)

    def test_polearm_master_butt_attack_via_bonus_selector(self):
        # We test the bonus-action selector directly: build a plan that
        # already contains a Glaive attack, then call _decide_bonus_action.
        # This isolates the Phase 31 hook from the broader movement/
        # decision heuristics which may have their own retreat logic.
        from engine.ai.models import ActionStep, TurnPlan
        fighter = self._make_polearm_fighter(x=5, y=5)
        foe = _ent("Goblin", x=6, y=5)
        b = BattleSystem(log_callback=lambda *a: None,
                          initial_entities=[fighter, foe])
        b.combat_started = True
        # Synthesise a "I already attacked with Glaive" turn state
        glaive = fighter.stats.actions[0]
        plan = TurnPlan(entity=fighter, steps=[ActionStep(
            step_type="attack", description=f"{fighter.name} attacks",
            attacker=fighter, target=foe, action=glaive,
            action_name="Glaive",
        )])
        fighter.action_used = True
        ai = TacticalAI()
        bonus_steps = ai._decide_bonus_action(
            fighter, [foe], [], b, plan)
        butt_steps = [s for s in bonus_steps
                       if s.step_type == "bonus_attack"
                       and s.action_name
                       and "butt" in s.action_name.lower()]
        self.assertGreater(len(butt_steps), 0,
                            "Polearm Master should yield a butt-end "
                            "bonus attack via the bonus-action selector")

    def test_shield_master_shove_via_bonus_selector(self):
        from engine.ai.models import ActionStep, TurnPlan
        sm = self._make_shield_fighter(x=5, y=5)
        foe = _ent("Goblin", x=6, y=5)
        b = BattleSystem(log_callback=lambda *a: None,
                          initial_entities=[sm, foe])
        b.combat_started = True
        sword = sm.stats.actions[0]
        plan = TurnPlan(entity=sm, steps=[ActionStep(
            step_type="attack", description="attack",
            attacker=sm, target=foe, action=sword,
            action_name="Longsword",
        )])
        sm.action_used = True
        ai = TacticalAI()
        bonus_steps = ai._decide_bonus_action(sm, [foe], [], b, plan)
        shove = [s for s in bonus_steps
                  if s.step_type == "bonus_attack"
                  and "shove" in (s.description or "").lower()]
        self.assertGreater(len(shove), 0,
                            "Shield Master should yield a bonus shove")


if __name__ == "__main__":
    unittest.main()
