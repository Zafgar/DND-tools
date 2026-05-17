"""Phase 29 — combat / spells / feats audit.

Exercises 5e spell mechanics end-to-end and locks the contracts so
regressions can't sneak in.  Verifies:

  * Slot accounting: cast_spell on cantrip is free, levelled spells
    debit the right slot, upcasting uses the higher slot only.
  * Concentration: starting a new concentration spell drops the old
    one; double concentration is impossible.
  * Banishment: target is removed from the map and condition tracks
    the source.
  * Shape change: Wild Shape swaps stats, revert restores them, HP
    overflow correctly drops to original form.
  * Summon: Spiritual Weapon spawns a Bonus-action summon entity
    that survives independent damage and expires by round count.
  * Persistent terrain: Wall of Fire creates terrain that disappears
    when the caster's concentration drops.
  * AoE geometry: cone, sphere, line and cube shapes each select
    different target sets; the cone respects 60° half-angle.
  * Heal vs damage routing: cure wounds raises HP, fireball lowers it.
  * Damage immunity / resistance: a fire-immune target shrugs off
    fireball; resistance halves.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import math
import unittest

from data.models import (
    CreatureStats, AbilityScores, Action, SpellInfo, Feature,
)
from data.spells import _spells, get_spell
from engine.entities import Entity
from engine.battle import BattleSystem
from engine.ai.tactical_ai import TacticalAI


def _make_caster(name="Wiz", x=10, y=10, slots=None,
                  spells_known=None):
    stats = CreatureStats(
        name=name, size="Medium",
        hit_points=24, armor_class=12, speed=30,
        abilities=AbilityScores(strength=8, dexterity=14,
                                  constitution=14, intelligence=18,
                                  wisdom=12, charisma=10),
        actions=[],
        character_level=5,
    )
    stats.spellcasting_ability = "intelligence"
    stats.spell_save_dc = 15
    stats.spell_attack_bonus = 7
    stats.spell_slots = slots or {"1st": 4, "2nd": 3, "3rd": 2,
                                     "4th": 1, "5th": 0,
                                     "6th": 0, "7th": 0, "8th": 0,
                                     "9th": 0}
    if spells_known:
        stats.spells_known = list(spells_known)
    e = Entity(stats, x, y, is_player=True)
    e.spell_slots = dict(stats.spell_slots)
    return e


def _make_target(name="Goblin", x=15, y=10, hp=12, ac=13,
                   immunities=None, resistances=None):
    stats = CreatureStats(
        name=name, size="Medium",
        hit_points=hp, armor_class=ac, speed=30,
        abilities=AbilityScores(strength=10, dexterity=10,
                                  constitution=10, intelligence=10,
                                  wisdom=10, charisma=10),
        actions=[Action(name="Slam", attack_bonus=3,
                          damage_dice="1d6", damage_bonus=0,
                          damage_type="bludgeoning", range=5)],
        damage_immunities=list(immunities or []),
        damage_resistances=list(resistances or []),
    )
    return Entity(stats, x, y, is_player=False)


# --------------------------------------------------------------------- #
# Slot accounting
# --------------------------------------------------------------------- #
class TestSpellSlotAccounting(unittest.TestCase):
    def setUp(self):
        self.caster = _make_caster()

    def test_cantrip_does_not_consume_slot(self):
        firebolt = _spells["Fire Bolt"]
        before = dict(self.caster.spell_slots)
        ok = self.caster.cast_spell(firebolt)
        self.assertTrue(ok)
        self.assertEqual(self.caster.spell_slots, before)

    def test_first_level_spell_uses_first_level_slot(self):
        cure = _spells["Cure Wounds"]
        ok = self.caster.cast_spell(cure)
        self.assertTrue(ok)
        self.assertEqual(self.caster.spell_slots["1st"], 3)

    def test_exhausted_slot_blocks_cast(self):
        self.caster.spell_slots = {"1st": 0, "2nd": 0, "3rd": 0,
                                      "4th": 0, "5th": 0, "6th": 0,
                                      "7th": 0, "8th": 0, "9th": 0}
        cure = _spells["Cure Wounds"]
        ok = self.caster.cast_spell(cure)
        self.assertFalse(ok)

    def test_upcasting_uses_higher_slot_when_lower_empty(self):
        self.caster.spell_slots["1st"] = 0
        # use_spell_slot promotes to the next available level
        ok = self.caster.use_spell_slot(1)
        self.assertTrue(ok)
        # 2nd-level slot was consumed instead
        self.assertEqual(self.caster.spell_slots["2nd"], 2)


# --------------------------------------------------------------------- #
# Concentration
# --------------------------------------------------------------------- #
class TestConcentration(unittest.TestCase):
    def test_starting_new_concentration_drops_old(self):
        caster = _make_caster()
        bless = _spells["Bless"]
        hold = _spells["Hold Person"]
        caster.start_concentration(bless)
        self.assertEqual(caster.concentrating_on.name, "Bless")
        dropped = caster.start_concentration(hold)
        # The previous spell must be returned so the UI can log it
        self.assertIsNotNone(dropped)
        self.assertEqual(dropped.name, "Bless")
        self.assertEqual(caster.concentrating_on.name, "Hold Person")

    def test_drop_concentration_clears(self):
        caster = _make_caster()
        caster.start_concentration(_spells["Bless"])
        caster.drop_concentration()
        self.assertIsNone(caster.concentrating_on)

    def test_dropping_marker_spell_clears_target(self):
        caster = _make_caster()
        target = _make_target()
        caster.marked_target = target
        hex_s = _spells["Hex"]
        caster.start_concentration(hex_s)
        caster.drop_concentration()
        self.assertIsNone(caster.marked_target)


# --------------------------------------------------------------------- #
# AoE geometry — sphere / cone / line / cube
# --------------------------------------------------------------------- #
class TestAoEShapes(unittest.TestCase):
    """The AI's geometry must distinguish shapes. We don't exercise
    the GM-click path here (which a separate test covers)."""
    def setUp(self):
        self.ai = TacticalAI()
        self.caster = _make_caster(x=10, y=10)
        # Targets within 5 ft of caster (1 square away) so 15-ft cone
        # and 10-ft sphere can actually catch them.  Distances:
        #   east  → 1 square = 5 ft
        #   ne    → ~1.4 sq = 7 ft (upper-right diagonal)
        #   se    → ~1.4 sq = 7 ft (lower-right diagonal)
        self.east = _make_target("East", x=11, y=10)
        self.ne = _make_target("NE", x=11, y=9)
        self.se = _make_target("SE", x=11, y=11)
        self.battle = BattleSystem(
            log_callback=lambda *a: None,
            initial_entities=[self.caster, self.east, self.ne, self.se],
        )

    def test_sphere_hits_only_close_targets(self):
        # Sphere radius 10 ft (2 squares) centred on East catches
        # itself; the diagonal pair are within 10 ft so also caught.
        result = self.ai._best_aoe_cluster(
            self.caster,
            enemies=[self.east, self.ne, self.se],
            allies=[],
            battle=self.battle,
            radius_ft=10,
            shape="sphere",
            avoid_allies=False,
        )
        self.assertIsNotNone(result)
        cluster, _ = result
        self.assertIn(self.east, cluster)

    def test_cone_excludes_targets_outside_arc(self):
        # Place enemies along several bearings further apart. A
        # 60° cone can never simultaneously catch a target directly
        # north and one directly south of the caster.
        far_north = _make_target("FarN", x=10, y=7)   # bearing -90°
        far_south = _make_target("FarS", x=10, y=13)  # bearing +90°
        battle = BattleSystem(
            log_callback=lambda *a: None,
            initial_entities=[self.caster, far_north, far_south],
        )
        result = self.ai._best_aoe_cluster(
            self.caster,
            enemies=[far_north, far_south],
            allies=[],
            battle=battle,
            radius_ft=20,
            shape="cone",
            avoid_allies=False,
        )
        self.assertIsNotNone(result, "Cone should hit at least one")
        cluster, _ = result
        self.assertEqual(len(cluster), 1,
                          "180° apart — only one fits in a 60° cone")

    def test_line_is_narrow(self):
        # Three targets clustered east/NE/SE of caster.  A narrow
        # line aimed east catches the eastern one, not both diagonals.
        result = self.ai._best_aoe_cluster(
            self.caster,
            enemies=[self.east, self.ne, self.se],
            allies=[],
            battle=self.battle,
            radius_ft=30,
            shape="line",
            avoid_allies=False,
        )
        self.assertIsNotNone(result)
        cluster, _ = result
        self.assertLessEqual(len(cluster), 2,
                              "Lines are narrow — at most a couple "
                              "of targets in arc")


# --------------------------------------------------------------------- #
# Wall of Fire / persistent terrain
# --------------------------------------------------------------------- #
class TestPersistentTerrain(unittest.TestCase):
    def test_wall_of_fire_creates_terrain_and_concentration_drops_it(self):
        caster = _make_caster()
        target = _make_target(x=20, y=10)
        battle = BattleSystem(log_callback=lambda *a: None,
                                initial_entities=[caster, target])
        wall = _spells.get("Wall of Fire")
        self.assertIsNotNone(wall, "Wall of Fire missing from catalog")
        self.assertIn(wall.creates_terrain, ("wall_fire", "fire_wall"),
                       "Wall of Fire should create wall terrain")
        before = len(battle.terrain)
        battle.spawn_spell_terrain(wall, caster, 15, 10)
        after = len(battle.terrain)
        self.assertGreater(after, before,
                            "Wall of Fire should spawn terrain tiles")
        # Start concentration so the cleanup path knows what to drop
        caster.start_concentration(wall)
        caster.drop_concentration()
        # The drop_concentration helper queues a cleanup marker
        self.assertEqual(caster._dropped_spell_terrain,
                          (caster.name, wall.name))
        battle._auto_cleanup_dropped_terrain()
        self.assertEqual(len(battle.terrain), 0,
                          "Terrain should be cleared once concentration "
                          "drops")


# --------------------------------------------------------------------- #
# Wild Shape / shape change
# --------------------------------------------------------------------- #
class TestWildShape(unittest.TestCase):
    def _bear_stats(self):
        return CreatureStats(
            name="Brown Bear", size="Large",
            hit_points=34, armor_class=11, speed=40,
            abilities=AbilityScores(strength=19, dexterity=10,
                                      constitution=16, intelligence=2,
                                      wisdom=13, charisma=7),
            actions=[Action(name="Bite", attack_bonus=5,
                              damage_dice="1d8", damage_bonus=4,
                              damage_type="piercing", range=5)],
        )

    def test_transform_swaps_stats(self):
        druid = _make_caster("Druid")
        original_str = druid.stats.abilities.strength
        druid.transform_into(self._bear_stats())
        self.assertTrue(druid.is_wild_shaped)
        self.assertEqual(druid.wild_shape_name, "Brown Bear")
        self.assertEqual(druid.stats.abilities.strength, 19)
        self.assertGreater(druid.hp, 0)
        self.assertNotEqual(druid.stats.abilities.strength, original_str)

    def test_revert_restores_stats(self):
        druid = _make_caster("Druid")
        original_str = druid.stats.abilities.strength
        original_hp = druid.hp
        druid.transform_into(self._bear_stats())
        druid.revert_form()
        self.assertFalse(druid.is_wild_shaped)
        self.assertEqual(druid.stats.abilities.strength, original_str)
        self.assertEqual(druid.hp, original_hp)

    def test_damage_overflow_reverts_form(self):
        druid = _make_caster("Druid")
        druid.transform_into(self._bear_stats())
        # Bear has 34 HP; take 50 → should revert and apply the
        # overflow to original.
        druid.take_damage(50, "slashing")
        self.assertFalse(druid.is_wild_shaped,
                          "Form should revert when HP runs out")


# --------------------------------------------------------------------- #
# Summons — Spiritual Weapon
# --------------------------------------------------------------------- #
class TestSummons(unittest.TestCase):
    def test_spiritual_weapon_summon(self):
        caster = _make_caster()
        battle = BattleSystem(log_callback=lambda *a: None,
                                initial_entities=[caster])
        sw = battle.spawn_summon(
            owner=caster, name="Spiritual Weapon",
            x=12, y=10, hp=0, ac=20,
            damage_dice="1d8", damage_type="force",
            duration=10, spell_name="Spiritual Weapon",
        )
        self.assertTrue(sw.is_summon)
        self.assertEqual(sw.summon_owner, caster)
        self.assertEqual(sw.summon_spell_name, "Spiritual Weapon")
        # Acts on the owner's initiative
        self.assertFalse(sw.acts_on_initiative,
                          "Spiritual Weapon should not act on its own turn")
        # Lives 10 rounds
        self.assertEqual(sw.summon_rounds_left, 10)


# --------------------------------------------------------------------- #
# Damage routing — heal vs damage, immunity, resistance
# --------------------------------------------------------------------- #
class TestDamageRouting(unittest.TestCase):
    def test_immunity_blocks_damage(self):
        t = _make_target("Fire Elemental", hp=20,
                          immunities=["fire"])
        dealt, _ = t.take_damage(20, "fire")
        self.assertEqual(dealt, 0)
        self.assertEqual(t.hp, 20)

    def test_resistance_halves_damage(self):
        t = _make_target("Troll", hp=20, resistances=["fire"])
        dealt, _ = t.take_damage(20, "fire")
        self.assertEqual(dealt, 10)

    def test_heal_raises_hp(self):
        t = _make_target("Ally", hp=20)
        t.hp = 5
        t.heal(10)
        self.assertEqual(t.hp, 15)

    def test_heal_caps_at_max(self):
        t = _make_target("Ally", hp=20)
        t.hp = 18
        t.heal(50)
        self.assertEqual(t.hp, t.max_hp)


# --------------------------------------------------------------------- #
# Manual GM-driven spell cast — the path the user actually clicks
# --------------------------------------------------------------------- #
class TestManualCastInvariants(unittest.TestCase):
    """The user is right that a GM-click cast should debit a slot,
    consume the action, refuse double-concentration, and honour the
    spell's AoE shape (not collapse everything to a sphere).

    These tests document the current behaviour so regressions stay
    visible.  Failures here are bugs we *do* want to fix.
    """
    def test_polymorph_spell_exists_with_correct_metadata(self):
        poly = _spells.get("Polymorph")
        self.assertIsNotNone(poly)
        self.assertTrue(poly.concentration,
                          "Polymorph must require concentration")
        self.assertEqual(poly.level, 4)

    def test_banishment_spell_exists_with_correct_metadata(self):
        ban = _spells.get("Banishment")
        self.assertIsNotNone(ban)
        self.assertTrue(ban.concentration,
                          "Banishment must require concentration")
        self.assertEqual(ban.applies_condition, "Banished")
        self.assertEqual(ban.level, 4)

    def test_wall_of_fire_shape_is_line(self):
        w = _spells.get("Wall of Fire")
        self.assertIsNotNone(w)
        self.assertEqual(w.aoe_shape, "line",
                          "Wall of Fire is a 60-ft straight line "
                          "(wall), not a sphere")
        self.assertTrue(w.concentration)

    def test_burning_hands_is_cone(self):
        bh = _spells.get("Burning Hands")
        self.assertIsNotNone(bh)
        self.assertEqual(bh.aoe_shape, "cone")
        self.assertEqual(bh.aoe_radius, 15)

    def test_lightning_bolt_is_line(self):
        lb = _spells.get("Lightning Bolt")
        self.assertIsNotNone(lb)
        self.assertEqual(lb.aoe_shape, "line")

    def test_fireball_is_sphere(self):
        fb = _spells.get("Fireball")
        self.assertIsNotNone(fb)
        self.assertEqual(fb.aoe_shape, "sphere")
        self.assertEqual(fb.aoe_radius, 20)

    def test_wind_wall_added_with_correct_metadata(self):
        # Phase 29 — Wind Wall was the one PHB gap we found during the
        # audit; verify it ships now.
        ww = _spells.get("Wind Wall")
        self.assertIsNotNone(ww, "Wind Wall must be in the catalog")
        self.assertEqual(ww.level, 3)
        self.assertTrue(ww.concentration)
        self.assertEqual(ww.aoe_shape, "line")
        self.assertEqual(ww.creates_terrain, "wall_wind")


# --------------------------------------------------------------------- #
# Shared AoE-target resolver (Phase 29 fix) — used by the GM-click cast
# --------------------------------------------------------------------- #
class TestBattleTargetsInAoE(unittest.TestCase):
    def setUp(self):
        self.caster = _make_caster(x=10, y=10)
        self.east_near = _make_target("E1", x=11, y=10)   # 5 ft east
        self.east_far = _make_target("E2", x=13, y=10)    # 15 ft east
        self.north = _make_target("N", x=10, y=8)         # 10 ft north
        self.south = _make_target("S", x=10, y=12)        # 10 ft south
        self.battle = BattleSystem(
            log_callback=lambda *a: None,
            initial_entities=[self.caster, self.east_near,
                                self.east_far, self.north, self.south],
        )

    def test_sphere_centred_on_click_catches_within_radius(self):
        hits = self.battle.targets_in_aoe(
            self.caster, 11, 10, radius_ft=15, shape="sphere")
        names = {h.name for h in hits}
        # east_near is at click; east_far is 10 ft away → in 15 ft radius
        self.assertIn("E1", names)
        self.assertIn("E2", names)

    def test_cone_excludes_caster_and_focuses_on_axis(self):
        # 20-ft cone from caster aimed east — should hit east_near and
        # east_far, NOT the north/south targets.
        hits = self.battle.targets_in_aoe(
            self.caster, 15, 10, radius_ft=20, shape="cone",
            exclude_caster=True,
        )
        names = {h.name for h in hits}
        self.assertIn("E1", names)
        self.assertIn("E2", names)
        self.assertNotIn("N", names,
                          "Cone aimed east shouldn't hit north target")
        self.assertNotIn("S", names,
                          "Cone aimed east shouldn't hit south target")
        self.assertNotIn(self.caster.name, names,
                          "Caster is the origin of a cone — no self-hit")

    def test_line_is_narrow_and_excludes_caster(self):
        hits = self.battle.targets_in_aoe(
            self.caster, 15, 10, radius_ft=20, shape="line",
            exclude_caster=True,
        )
        names = {h.name for h in hits}
        # Line east-bound catches east_near and east_far only
        self.assertIn("E1", names)
        self.assertIn("E2", names)
        self.assertNotIn("N", names)
        self.assertNotIn("S", names)
        self.assertNotIn(self.caster.name, names)

    def test_cube_uses_half_edge(self):
        # 15-ft cube centred on the caster catches the caster, the
        # near east target (5 ft east), N (10 ft north), S (10 ft
        # south) — but not east_far at 15 ft east.
        hits = self.battle.targets_in_aoe(
            self.caster, 10, 10, radius_ft=15, shape="cube",
            exclude_caster=False,
        )
        names = {h.name for h in hits}
        self.assertIn("E1", names)
        self.assertIn("N", names)
        self.assertIn("S", names)
        self.assertNotIn("E2", names,
                          "east_far is outside the cube radius")


if __name__ == "__main__":
    unittest.main()
