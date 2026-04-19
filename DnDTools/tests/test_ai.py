"""Tests for engine/ai/ – Tactical AI module structure and basic functionality."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import unittest
import random
from data.models import CreatureStats, AbilityScores, Action, Feature, SpellInfo
from engine.entities import Entity
from engine.ai import TacticalAI, TurnPlan, ActionStep, _get_spell_damage_dice
from engine.ai.constants import (
    KILL_POTENTIAL_BONUS, FOCUS_FIRE_WEIGHT, DODGE_HP_THRESHOLD,
)
from engine.ai.utils import _get_effective_caster_level
from engine.ai.models import ActionStep as ModelActionStep, TurnPlan as ModelTurnPlan
from engine.battle import BattleSystem


def _make_entity(name="Test", is_player=True, hp=50, ac=15, x=5.0, y=5.0,
                 strength=10, dexterity=10, constitution=10, speed=30,
                 size="Medium", features=None, actions=None, spells_known=None,
                 **kwargs):
    stats = CreatureStats(
        name=name, size=size, hit_points=hp, armor_class=ac, speed=speed,
        abilities=AbilityScores(strength=strength, dexterity=dexterity,
                                constitution=constitution),
        features=features or [],
        actions=actions or [Action(name="Sword", attack_bonus=5, damage_dice="1d8",
                                   damage_bonus=3, damage_type="slashing", range=5)],
        spells_known=spells_known or [],
        **kwargs,
    )
    return Entity(stats, x, y, is_player=is_player)


def _make_battle(entities, log_lines=None):
    if log_lines is None:
        log_lines = []
    return BattleSystem(log_callback=log_lines.append, initial_entities=entities)


class TestAIPackageImports(unittest.TestCase):
    """Verify that the refactored ai/ package exports everything correctly."""

    def test_tactical_ai_importable(self):
        self.assertIsNotNone(TacticalAI)

    def test_turn_plan_importable(self):
        self.assertIsNotNone(TurnPlan)

    def test_action_step_importable(self):
        self.assertIsNotNone(ActionStep)

    def test_models_match_package_exports(self):
        """Models imported from ai.models should be the same as from ai."""
        self.assertIs(ActionStep, ModelActionStep)
        self.assertIs(TurnPlan, ModelTurnPlan)

    def test_constants_importable(self):
        self.assertEqual(KILL_POTENTIAL_BONUS, 50)
        self.assertEqual(FOCUS_FIRE_WEIGHT, 40)
        self.assertAlmostEqual(DODGE_HP_THRESHOLD, 0.40)


class TestActionStep(unittest.TestCase):
    def test_create_attack_step(self):
        step = ActionStep(step_type="attack", description="Sword attack")
        self.assertEqual(step.step_type, "attack")
        self.assertEqual(step.damage, 0)
        self.assertFalse(step.is_crit)

    def test_create_spell_step(self):
        spell = SpellInfo(name="Fireball", level=3, damage_dice="8d6")
        step = ActionStep(step_type="spell", spell=spell, slot_used=3)
        self.assertEqual(step.spell.name, "Fireball")
        self.assertEqual(step.slot_used, 3)

    def test_create_move_step(self):
        step = ActionStep(step_type="move", new_x=3.0, new_y=4.0,
                          old_x=1.0, old_y=1.0, movement_ft=15.0)
        self.assertEqual(step.new_x, 3.0)
        self.assertAlmostEqual(step.movement_ft, 15.0)


class TestTurnPlan(unittest.TestCase):
    def test_empty_plan(self):
        plan = TurnPlan()
        self.assertIsNone(plan.entity)
        self.assertEqual(len(plan.steps), 0)
        self.assertFalse(plan.skipped)

    def test_skipped_plan(self):
        plan = TurnPlan(skipped=True, skip_reason="Stunned")
        self.assertTrue(plan.skipped)
        self.assertEqual(plan.skip_reason, "Stunned")


class TestEffectiveCasterLevel(unittest.TestCase):
    def test_player_character_level(self):
        e = _make_entity(character_level=10)
        level = _get_effective_caster_level(e)
        self.assertEqual(level, 10)

    def test_monster_uses_cr(self):
        e = _make_entity(challenge_rating=5.0, character_level=0)
        level = _get_effective_caster_level(e)
        self.assertEqual(level, 5)

    def test_cr_zero_returns_one(self):
        e = _make_entity(challenge_rating=0.0, character_level=0)
        level = _get_effective_caster_level(e)
        self.assertEqual(level, 1)


class TestSpellDamageDice(unittest.TestCase):
    def test_non_cantrip_unchanged(self):
        spell = SpellInfo(name="Fireball", level=3, damage_dice="8d6")
        e = _make_entity(character_level=10)
        result = _get_spell_damage_dice(spell, e)
        self.assertEqual(result, "8d6")

    def test_cantrip_scales_at_level_5(self):
        spell = SpellInfo(name="Fire Bolt", level=0, damage_dice="1d10")
        e = _make_entity(character_level=5)
        result = _get_spell_damage_dice(spell, e)
        self.assertEqual(result, "2d10")

    def test_cantrip_scales_at_level_11(self):
        spell = SpellInfo(name="Fire Bolt", level=0, damage_dice="1d10")
        e = _make_entity(character_level=11)
        result = _get_spell_damage_dice(spell, e)
        self.assertEqual(result, "3d10")


class TestTacticalAIBasic(unittest.TestCase):
    def test_create_tactical_ai(self):
        ai = TacticalAI()
        self.assertIsNotNone(ai)

    def test_compute_turn_for_stunned_entity(self):
        """Stunned entity should get a skipped turn."""
        random.seed(42)
        hero = _make_entity("Hero", is_player=True, x=0, y=0)
        goblin = _make_entity("Goblin", is_player=False, x=3, y=0, hp=20, ac=13,
                              dexterity=14)
        goblin.add_condition("Stunned")
        battle = _make_battle([hero, goblin])
        battle.start_combat()
        ai = TacticalAI()
        plan = ai.calculate_turn(goblin, battle)
        self.assertIsInstance(plan, TurnPlan)
        self.assertTrue(plan.skipped)

    def test_compute_turn_for_incapacitated_entity(self):
        """Incapacitated entity should get a skipped turn."""
        random.seed(42)
        hero = _make_entity("Hero", is_player=True, x=0, y=0)
        goblin = _make_entity("Goblin", is_player=False, x=3, y=0, hp=20)
        goblin.add_condition("Incapacitated")
        battle = _make_battle([hero, goblin])
        battle.start_combat()
        ai = TacticalAI()
        plan = ai.calculate_turn(goblin, battle)
        self.assertIsInstance(plan, TurnPlan)
        self.assertTrue(plan.skipped)

    def test_compute_turn_returns_steps(self):
        """A healthy goblin adjacent to an enemy should produce attack steps."""
        random.seed(42)
        hero = _make_entity("Hero", is_player=True, x=0, y=0, hp=50)
        goblin = _make_entity("Goblin", is_player=False, x=1, y=0, hp=20, ac=13,
                              strength=12, dexterity=14)
        battle = _make_battle([hero, goblin])
        battle.start_combat()
        ai = TacticalAI()
        plan = ai.calculate_turn(goblin, battle)
        self.assertIsInstance(plan, TurnPlan)
        self.assertFalse(plan.skipped)
        # Should have at least one step (move or attack)
        self.assertGreater(len(plan.steps), 0)

    def test_compute_turn_for_ranged_enemy(self):
        """An archer far from enemies should try to attack from range."""
        random.seed(42)
        hero = _make_entity("Hero", is_player=True, x=0, y=0, hp=50)
        archer = _make_entity("Archer", is_player=False, x=10, y=0, hp=20,
                              dexterity=16,
                              actions=[Action(name="Longbow", attack_bonus=5,
                                              damage_dice="1d8", damage_bonus=3,
                                              damage_type="piercing", range=150,
                                              long_range=600)])
        battle = _make_battle([hero, archer])
        battle.start_combat()
        ai = TacticalAI()
        plan = ai.calculate_turn(archer, battle)
        self.assertFalse(plan.skipped)


class TestUpcastScaling(unittest.TestCase):
    def test_combine_dice(self):
        from engine.ai.utils import _combine_dice
        self.assertEqual(_combine_dice("", "1d6"), "1d6")
        self.assertEqual(_combine_dice("3d6", ""), "3d6")
        self.assertEqual(_combine_dice("3d6", "2d6"), "3d6+2d6")

    def test_scale_dice_by_count(self):
        from engine.ai.utils import _scale_dice_by_count
        self.assertEqual(_scale_dice_by_count("1d6", 3), "3d6")
        self.assertEqual(_scale_dice_by_count("1d6+2", 3), "3d6+2")
        self.assertEqual(_scale_dice_by_count("2d4+1", 2), "4d4+1")
        self.assertEqual(_scale_dice_by_count("1d8", 0), "1d8")
        self.assertEqual(_scale_dice_by_count("1d8", 1), "1d8")

    def test_fireball_upcast(self):
        from data.spells import get_spell
        fb = get_spell("Fireball")
        caster = _make_entity("Wiz", is_player=True)
        base = _get_spell_damage_dice(fb, caster, slot_used=3)
        upcast_5 = _get_spell_damage_dice(fb, caster, slot_used=5)
        self.assertEqual(base, "8d6")
        self.assertEqual(upcast_5, "8d6+2d6")

    def test_magic_missile_upcast(self):
        from data.spells import get_spell
        from engine.ai.utils import _get_spell_damage_dice
        mm = get_spell("Magic Missile")
        caster = _make_entity("Wiz", is_player=True)
        l3 = _get_spell_damage_dice(mm, caster, slot_used=3)
        # Magic Missile scaling = "1d4+1" per slot above 1st, so +2 slots = +2d4+2
        # Scaled by 2 -> "2d4+1" (flat bonus preserved once per term)
        self.assertIn("d4", l3)


class TestOpportunityAttack(unittest.TestCase):
    def test_opportunity_attack_calculation(self):
        """Should return an ActionStep or None for opportunity attacks."""
        random.seed(42)
        hero = _make_entity("Hero", is_player=True, x=0, y=0)
        goblin = _make_entity("Goblin", is_player=False, x=1, y=0, hp=20)
        battle = _make_battle([hero, goblin])
        battle.start_combat()
        ai = TacticalAI()
        # calculate_opportunity_attack takes (entity, target, battle)
        result = ai.calculate_opportunity_attack(hero, goblin, battle)
        # Returns ActionStep or None
        self.assertTrue(result is None or isinstance(result, ActionStep))


class TestCounterspellDecision(unittest.TestCase):
    """Tests for TacticalAI.should_counterspell heuristics."""

    def _make_wizard(self, is_player):
        from data.spells import get_spell
        return _make_entity(
            "Wiz", is_player=is_player, hp=40, ac=12,
            spells_known=[get_spell("Counterspell"), get_spell("Fireball"),
                          get_spell("Shield"), get_spell("Magic Missile")],
            spell_slots={"1st": 4, "2nd": 3, "3rd": 3, "4th": 1},
            character_level=9, spellcasting_ability="Intelligence",
            spell_save_dc=15, spell_attack_bonus=7, proficiency_bonus=4,
        )

    def test_counter_high_level_spell(self):
        """Always worth countering lvl 3+ spells when slot auto-succeeds."""
        from data.spells import get_spell
        ai = TacticalAI()
        reactor = self._make_wizard(False)
        caster = self._make_wizard(True)
        hero = _make_entity("Hero", is_player=True, x=0, y=0)
        battle = _make_battle([hero, reactor, caster])
        battle.start_combat()
        self.assertTrue(ai.should_counterspell(reactor, caster, get_spell("Fireball"), 3, battle))

    def test_do_not_counter_ally(self):
        """Never counter a same-team caster (e.g. friendly Bless)."""
        from data.spells import get_spell
        ai = TacticalAI()
        reactor = self._make_wizard(False)
        ally = self._make_wizard(False)
        battle = _make_battle([reactor, ally])
        battle.start_combat()
        self.assertFalse(ai.should_counterspell(reactor, ally, get_spell("Fireball"), 3, battle))

    def test_skip_low_level_buff(self):
        """Don't burn a lvl 3 slot on a no-threat lvl 1 Mage Armor cast."""
        from data.spells import get_spell
        ai = TacticalAI()
        reactor = self._make_wizard(False)
        caster = self._make_wizard(True)
        battle = _make_battle([reactor, caster])
        battle.start_combat()
        # Mage Armor is lvl 1, not priority, not AoE, not control
        self.assertFalse(ai.should_counterspell(reactor, caster, get_spell("Mage Armor"), 1, battle))

    def test_counter_reaction_used(self):
        """Reaction already spent — cannot counter."""
        from data.spells import get_spell
        ai = TacticalAI()
        reactor = self._make_wizard(False)
        caster = self._make_wizard(True)
        battle = _make_battle([reactor, caster])
        battle.start_combat()
        reactor.reaction_used = True
        self.assertFalse(ai.should_counterspell(reactor, caster, get_spell("Fireball"), 3, battle))


class TestSilveryBarbsDecision(unittest.TestCase):
    """Tests for TacticalAI.should_silvery_barbs heuristics."""

    def _make_caster(self, is_player, x=5.0, y=5.0):
        from data.spells import get_spell
        return _make_entity(
            "Warlock", is_player=is_player, x=x, y=y, hp=30, ac=12,
            spells_known=[get_spell("Silvery Barbs")],
            spell_slots={"1st": 2},
            character_level=5, spellcasting_ability="Charisma",
        )

    def test_react_on_crit(self):
        ai = TacticalAI()
        reactor = self._make_caster(False, x=2, y=2)
        attacker = _make_entity("Hero", is_player=True, x=0, y=0)
        target = _make_entity("Ally", is_player=False, x=1, y=1, hp=20)
        battle = _make_battle([attacker, target, reactor])
        battle.start_combat()
        step = ActionStep(step_type="attack", attacker=attacker,
                          attack_roll=28, nat_roll=20, is_crit=True)
        self.assertTrue(ai.should_silvery_barbs(reactor, attacker, target, step, battle))

    def test_skip_far_comfortable_hit(self):
        """Don't waste a slot on a hit that rolled way over AC."""
        ai = TacticalAI()
        reactor = self._make_caster(False, x=2, y=2)
        attacker = _make_entity("Hero", is_player=True, x=0, y=0)
        target = _make_entity("Ally", is_player=False, x=1, y=1, hp=20, ac=10)
        battle = _make_battle([attacker, target, reactor])
        battle.start_combat()
        # Hit total 22 vs AC 10: reroll unlikely to miss, not a crit
        step = ActionStep(step_type="attack", attacker=attacker,
                          attack_roll=22, nat_roll=17, is_crit=False)
        self.assertFalse(ai.should_silvery_barbs(reactor, attacker, target, step, battle))

    def test_react_on_tight_hit(self):
        """Hit just barely above AC — reroll is valuable."""
        ai = TacticalAI()
        reactor = self._make_caster(False, x=2, y=2)
        attacker = _make_entity("Hero", is_player=True, x=0, y=0)
        target = _make_entity("Ally", is_player=False, x=1, y=1, hp=20, ac=15)
        battle = _make_battle([attacker, target, reactor])
        battle.start_combat()
        step = ActionStep(step_type="attack", attacker=attacker,
                          attack_roll=16, nat_roll=10, is_crit=False)
        self.assertTrue(ai.should_silvery_barbs(reactor, attacker, target, step, battle))

    def test_skip_out_of_range(self):
        """Reactor too far from attacker (> 60 ft)."""
        ai = TacticalAI()
        reactor = self._make_caster(False, x=20, y=20)
        attacker = _make_entity("Hero", is_player=True, x=0, y=0)
        target = _make_entity("Ally", is_player=False, x=19, y=19, hp=20)
        battle = _make_battle([attacker, target, reactor])
        battle.start_combat()
        step = ActionStep(step_type="attack", attacker=attacker,
                          attack_roll=30, nat_roll=20, is_crit=True)
        self.assertFalse(ai.should_silvery_barbs(reactor, attacker, target, step, battle))


if __name__ == "__main__":
    unittest.main()
