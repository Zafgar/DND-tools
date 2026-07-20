"""Phase 46 — RAW correctness fixes locked by regression tests.

Covers the confirmed findings from the 5e (2014) rules audit:

  * Damage while at 0 HP → death save failures (1 / 2 on crit),
    instant death when damage ≥ HP max (PHB p.197).
  * Concentration: temp-HP absorption still forces the save at the
    full damage value (Sage Advice); a killed NPC caster always drops
    concentration; ending concentration removes the linked effects and
    conditions from every target (PHB p.203); Haste ends with a
    lethargy turn (PHB p.250).
  * Restrained imposes disadvantage on DEX saves (PHB p.292).
  * Prone no longer halves speed; crawling doubles movement cost and
    standing up costs half speed (PHB p.190-191).
  * Sentinel: Disengage does not prevent the Sentinel OA.
  * Lethargic blocks actions but does not break concentration.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import unittest
from unittest import mock

from data.models import CreatureStats, AbilityScores, Action, Feature, SpellInfo
from engine.entities import Entity
from engine.battle import BattleSystem


def _make_entity(name="Test", is_player=True, hp=50, ac=15, x=5.0, y=5.0,
                 strength=10, dexterity=10, constitution=10, speed=30,
                 size="Medium", features=None, actions=None, **kwargs):
    stats = CreatureStats(
        name=name, size=size, hit_points=hp, armor_class=ac, speed=speed,
        abilities=AbilityScores(strength=strength, dexterity=dexterity,
                                constitution=constitution),
        features=features or [],
        actions=actions or [Action(name="Sword", attack_bonus=5,
                                   damage_dice="1d8", damage_bonus=3,
                                   damage_type="slashing", range=5)],
        **kwargs,
    )
    return Entity(stats, x, y, is_player=is_player)


def _conc_spell(name="Bless"):
    return SpellInfo(name=name, level=1, concentration=True)


class TestDamageAtZeroHP(unittest.TestCase):
    """PHB p.197 — damage while already at 0 HP."""

    def _downed_player(self):
        e = _make_entity("Hero", is_player=True, hp=30)
        e.take_damage(30)
        self.assertEqual(e.hp, 0)
        self.assertTrue(e.has_condition("Unconscious"))
        self.assertEqual(e.death_save_failures, 0)
        return e

    def test_normal_hit_adds_one_failure(self):
        e = self._downed_player()
        e.take_damage(5)
        self.assertEqual(e.death_save_failures, 1)

    def test_crit_hit_adds_two_failures(self):
        e = self._downed_player()
        e.take_damage(5, is_crit=True)
        self.assertEqual(e.death_save_failures, 2)

    def test_third_failure_means_death(self):
        e = self._downed_player()
        e.take_damage(5)
        e.take_damage(5, is_crit=True)
        self.assertEqual(e.death_save_failures, 3)

    def test_massive_damage_at_zero_is_instant_death(self):
        e = self._downed_player()
        e.take_damage(30)  # == max HP
        self.assertEqual(e.death_save_failures, 3)
        self.assertIn("MASSIVE", e.death_save_history)

    def test_damage_breaks_stabilization(self):
        e = self._downed_player()
        e.is_stable = True
        e.take_damage(4)
        self.assertFalse(e.is_stable)
        self.assertEqual(e.death_save_failures, 1)


class TestConcentrationDamage(unittest.TestCase):
    def test_temp_hp_absorption_still_forces_save(self):
        e = _make_entity("Caster", hp=40)
        e.temp_hp = 20
        e.start_concentration(_conc_spell())
        # Force every d20 to roll 1 → the save, if rolled, must fail.
        with mock.patch("engine.entities.random.randint", return_value=1):
            dealt, broke = e.take_damage(10)
        self.assertTrue(broke, "temp-HP-absorbed damage must still force "
                                "a concentration save")
        self.assertIsNone(e.concentrating_on)

    def test_dc_uses_full_damage_not_post_temp_amount(self):
        e = _make_entity("Caster", hp=40)
        e.temp_hp = 20
        e.start_concentration(_conc_spell())
        # Damage 30 → DC 15. Roll 12 (+0 Con) fails vs 15, but would
        # pass vs the old post-absorption DC max(10, 10//2)=10.
        with mock.patch("engine.entities.random.randint", return_value=12):
            dealt, broke = e.take_damage(30)
        self.assertTrue(broke)

    def test_killed_npc_drops_concentration(self):
        npc = _make_entity("Mage", is_player=False, hp=10)
        npc.start_concentration(_conc_spell("Banishment"))
        # Pass the damage save (roll 20) — death itself must end it.
        with mock.patch("engine.entities.random.randint", return_value=20):
            npc.take_damage(15)
        self.assertLessEqual(npc.hp, 0)
        self.assertIsNone(npc.concentrating_on)


class TestConcentrationEffectCleanup(unittest.TestCase):
    """PHB p.203 — ending concentration ends the spell's effects."""

    def test_drop_removes_linked_effect(self):
        caster = _make_entity("Cleric")
        ally = _make_entity("Fighter")
        caster.start_concentration(_conc_spell("Bless"))
        ally.active_effects["Bless"] = 10
        caster.register_concentration_effect(ally, "effect", "Bless")
        caster.drop_concentration()
        self.assertNotIn("Bless", ally.active_effects)

    def test_drop_removes_linked_condition(self):
        caster = _make_entity("Wizard")
        victim = _make_entity("Orc", is_player=False)
        caster.start_concentration(_conc_spell("Hold Person"))
        victim.add_condition("Paralyzed")
        caster.register_concentration_effect(victim, "condition", "Paralyzed")
        caster.drop_concentration()
        self.assertFalse(victim.has_condition("Paralyzed"))

    def test_new_concentration_spell_cleans_old_effects(self):
        caster = _make_entity("Cleric")
        ally = _make_entity("Fighter")
        caster.start_concentration(_conc_spell("Bless"))
        ally.active_effects["Bless"] = 10
        caster.register_concentration_effect(ally, "effect", "Bless")
        caster.start_concentration(_conc_spell("Hold Person"))
        self.assertNotIn("Bless", ally.active_effects)

    def test_haste_end_applies_lethargy(self):
        caster = _make_entity("Wizard")
        ally = _make_entity("Fighter")
        caster.start_concentration(_conc_spell("Haste"))
        ally.active_effects["Haste"] = 10
        caster.register_concentration_effect(ally, "effect", "Haste")
        caster.drop_concentration()
        self.assertNotIn("Haste", ally.active_effects)
        self.assertTrue(ally.has_condition("Lethargic"))
        self.assertEqual(ally.active_effects.get("Lethargic"), 2)

    def test_lethargic_blocks_speed_but_not_concentration(self):
        e = _make_entity("Sorcerer")
        e.start_concentration(_conc_spell("Bless"))
        e.apply_haste_lethargy()
        self.assertEqual(e.get_speed(), 0.0)
        self.assertTrue(e.is_incapacitated())
        self.assertIsNotNone(e.concentrating_on,
                             "Haste lethargy must not break concentration")

    def test_incapacitated_still_breaks_concentration(self):
        e = _make_entity("Sorcerer")
        e.start_concentration(_conc_spell("Bless"))
        e.add_condition("Stunned")
        self.assertIsNone(e.concentrating_on)

    def test_stale_link_is_tolerated(self):
        caster = _make_entity("Cleric")
        ally = _make_entity("Fighter")
        caster.start_concentration(_conc_spell("Bless"))
        caster.register_concentration_effect(ally, "effect", "Bless")
        # Effect already expired naturally — cleanup must not raise.
        caster.drop_concentration()
        self.assertEqual(caster.concentration_links, [])


class TestRestrainedDexSaves(unittest.TestCase):
    def test_restrained_gives_dex_save_disadvantage(self):
        from engine.rules import make_saving_throw
        e = _make_entity("Rogue", dexterity=14)
        e.add_condition("Restrained")
        # Disadvantage → two rolls, min() taken. Feed 20 then 1:
        # with disadvantage the result is 1 (+2 dex) = 3 → fails DC 10.
        rolls = iter([20, 1])
        with mock.patch("engine.dice.random.randint",
                        side_effect=lambda a, b: next(rolls)):
            ok, total, msg = make_saving_throw(e, "Dexterity", 10)
        self.assertFalse(ok, "Restrained must impose disadvantage on "
                             "DEX saves (min of two rolls)")

    def test_unrestrained_dex_save_single_roll(self):
        from engine.rules import make_saving_throw
        e = _make_entity("Rogue", dexterity=14)
        rolls = iter([20, 1])
        with mock.patch("engine.dice.random.randint",
                        side_effect=lambda a, b: next(rolls)):
            ok, total, msg = make_saving_throw(e, "Dexterity", 10)
        self.assertTrue(ok)


class TestProneMovement(unittest.TestCase):
    """PHB p.190-191: prone doesn't halve speed; crawling costs double;
    standing costs half speed."""

    def test_prone_does_not_halve_speed(self):
        e = _make_entity("Fighter", speed=30)
        e.add_condition("Prone")
        self.assertEqual(e.get_speed(), 30.0)

    def test_crawl_costs_double(self):
        e = _make_entity("Fighter", speed=30, x=2, y=2)
        battle = BattleSystem(log_callback=lambda s: None,
                              initial_entities=[e])
        self.assertEqual(battle.get_terrain_movement_cost(3, 3, e), 1.0)
        e.add_condition("Prone")
        self.assertEqual(battle.get_terrain_movement_cost(3, 3, e), 2.0)

    def test_stand_up_costs_half_true_speed(self):
        from engine.rules import stand_from_prone_cost
        e = _make_entity("Fighter", speed=30)
        e.add_condition("Prone")
        self.assertEqual(stand_from_prone_cost(e), 15.0)


class TestSentinelVsDisengage(unittest.TestCase):
    def test_disengage_prevents_normal_oa(self):
        mover = _make_entity("Rogue", is_player=True, x=5, y=5)
        watcher = _make_entity("Orc", is_player=False, x=6, y=5)
        battle = BattleSystem(log_callback=lambda s: None,
                              initial_entities=[mover, watcher])
        mover.is_disengaging = True
        mover.grid_x, mover.grid_y = 9.0, 5.0
        oas = battle.check_opportunity_attacks(mover, 5.0, 5.0)
        self.assertEqual(oas, [])

    def test_sentinel_ignores_disengage(self):
        mover = _make_entity("Rogue", is_player=True, x=5, y=5)
        watcher = _make_entity(
            "Guard", is_player=False, x=6, y=5,
            features=[Feature(name="Sentinel", mechanic="sentinel")])
        battle = BattleSystem(log_callback=lambda s: None,
                              initial_entities=[mover, watcher])
        mover.is_disengaging = True
        mover.grid_x, mover.grid_y = 9.0, 5.0
        oas = battle.check_opportunity_attacks(mover, 5.0, 5.0)
        self.assertIn(watcher, oas)


if __name__ == "__main__":
    unittest.main()


class TestNoDoubleDeathSaveInBattleState(unittest.TestCase):
    """Regression: death-save failures at 0 HP are applied once (inside
    take_damage), not doubled by battle_state's resolution path."""

    def _setup(self):
        import pygame
        pygame.init()
        pygame.display.set_mode((320, 240))
        from states.battle_state import BattleState
        from engine.ai import ActionStep

        class FM:
            def __init__(s):
                s.screen = pygame.display.get_surface()
                s.running = True

            def change_state(s, *a, **k):
                pass

        hero = _make_entity("Hero", is_player=True, hp=30)
        foe = _make_entity("Orc", is_player=False, hp=30, x=6, y=5)
        bs = BattleState(FM(), entities=[hero, foe])
        hero.take_damage(30)  # down the hero (Unconscious, 0 failures)
        self.assertTrue(hero.has_condition("Unconscious"))
        self.assertEqual(hero.death_save_failures, 0)
        return bs, hero, foe, ActionStep

    def test_normal_hit_on_downed_adds_one_failure(self):
        bs, hero, foe, ActionStep = self._setup()
        step = ActionStep("attack")
        step.attacker = foe
        step.target = hero
        step.damage = 5
        step.damage_type = "slashing"
        step.is_crit = False
        bs._resolve_target_outcome(step, hero, "hit")
        self.assertEqual(hero.death_save_failures, 1)

    def test_crit_on_downed_adds_two_failures(self):
        bs, hero, foe, ActionStep = self._setup()
        step = ActionStep("attack")
        step.attacker = foe
        step.target = hero
        step.damage = 5
        step.damage_type = "slashing"
        step.is_crit = True
        bs._resolve_target_outcome(step, hero, "crit")
        self.assertEqual(hero.death_save_failures, 2)
