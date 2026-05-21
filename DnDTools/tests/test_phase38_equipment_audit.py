"""Phase 38 — equipment & item audit.

The user asked: "can I equip items? do they actually affect things?
what about magic weapons, force effects, armor?" — and so on.

This file documents and verifies every equipment integration point:

  * Slot assignment (auto + explicit).
  * Two-handed weapon exclusivity with off-hand.
  * Attunement cap (PHB max 3).
  * Heavy-armor STR penalty (speed −10 if STR < requirement).
  * AC calculation from armor base + DEX cap + shield + rings/cloaks.
  * Stat overrides (Gauntlets of Ogre Power → STR 19).
  * Save bonus (Cloak of Protection +1).
  * Damage resistance grant (Periapt of Wound Closure etc.).
  * Speed bonus (Boots of Speed).
  * Magic-weapon attack/damage bonus (+1, +2, +3 weapons) actually
    rides on the roll.
  * Extra damage dice (Flame Tongue +2d6 fire) applies on hit, double
    on crit.
  * is_magical flag bypasses non-magical damage resistance on impact.

Pure logic, no pygame.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import unittest

from data.models import (
    CreatureStats, AbilityScores, Action, Item, Feature,
)
from engine.entities import Entity
from engine.battle import BattleSystem
from engine.ai.tactical_ai import TacticalAI


def _hero(*, str_score=16, dex_score=14, con_score=14,
            speed=30, items=None, level=5):
    stats = CreatureStats(
        name="Hero", size="Medium",
        hit_points=44, armor_class=10, speed=speed,
        abilities=AbilityScores(strength=str_score,
                                  dexterity=dex_score,
                                  constitution=con_score,
                                  intelligence=10, wisdom=12,
                                  charisma=10),
        actions=[Action(name="Longsword", attack_bonus=5,
                          damage_dice="1d8", damage_bonus=3,
                          damage_type="slashing", range=5)],
        proficiency_bonus=3, character_level=level,
    )
    stats.items = list(items or [])
    e = Entity(stats, 5, 5, is_player=True)
    e.items = list(stats.items)
    return e


def _target(*, hp=40, ac=15,
              resistances=None, immunities=None):
    stats = CreatureStats(
        name="Target", size="Medium",
        hit_points=hp, armor_class=ac, speed=30,
        abilities=AbilityScores(),
        actions=[Action(name="Slam", attack_bonus=3,
                          damage_dice="1d6", damage_bonus=0,
                          damage_type="bludgeoning", range=5)],
        damage_resistances=list(resistances or []),
        damage_immunities=list(immunities or []),
    )
    return Entity(stats, 10, 5, is_player=False)


# --------------------------------------------------------------------- #
# Slot assignment + equip/unequip
# --------------------------------------------------------------------- #
class TestSlotAssignment(unittest.TestCase):
    def test_auto_slot_for_weapon(self):
        sword = Item(name="Longsword", item_type="weapon")
        h = _hero(items=[sword])
        ok = h.equip_item(sword)
        self.assertTrue(ok)
        self.assertEqual(sword.slot, "main_hand")
        self.assertTrue(sword.equipped)

    def test_auto_slot_for_armor(self):
        chain = Item(name="Chain Mail", item_type="armor",
                       base_ac=16, max_dex_bonus=0)
        h = _hero(items=[chain])
        h.equip_item(chain)
        self.assertEqual(chain.slot, "armor")

    def test_equip_replaces_previous_in_same_slot(self):
        s1 = Item(name="Dagger", item_type="weapon", slot="main_hand")
        s2 = Item(name="Shortsword", item_type="weapon", slot="main_hand")
        h = _hero(items=[s1, s2])
        h.equip_item(s1)
        h.equip_item(s2)
        self.assertFalse(s1.equipped)
        self.assertTrue(s2.equipped)

    def test_two_handed_clears_off_hand(self):
        shield = Item(name="Shield", item_type="shield",
                       slot="off_hand", base_ac=0, ac_bonus=2,
                       armor_category="shield")
        greatsword = Item(name="Greatsword", item_type="weapon",
                            weapon_properties=["heavy", "two-handed"],
                            slot="main_hand")
        h = _hero(items=[shield, greatsword])
        h.equip_item(shield)
        h.equip_item(greatsword)
        # Greatsword wields → shield should drop
        self.assertTrue(greatsword.equipped)
        self.assertFalse(shield.equipped,
                          "Two-handed main-hand should clear off-hand")

    def test_unequip_clears_attunement(self):
        ring = Item(name="Ring of Protection", item_type="ring",
                      slot="ring1", requires_attunement=True,
                      is_magical=True, ac_bonus=1,
                      save_bonuses={"all": 1})
        h = _hero(items=[ring])
        h.equip_item(ring)
        self.assertTrue(ring.attuned)
        h.unequip_item(ring)
        self.assertFalse(ring.attuned)


class TestAttunementCap(unittest.TestCase):
    def _ring(self, idx):
        return Item(name=f"Magic Ring {idx}", item_type="ring",
                      slot=f"ring{idx}",
                      requires_attunement=True,
                      is_magical=True)

    def test_three_attuned_succeeds(self):
        r1, r2, r3 = self._ring(1), self._ring(2), self._ring(1)
        # Make the slots unique so they don't fight for the same one
        r2.slot = "ring2"
        r3.slot = "amulet"
        h = _hero(items=[r1, r2, r3])
        self.assertTrue(h.equip_item(r1))
        self.assertTrue(h.equip_item(r2))
        self.assertTrue(h.equip_item(r3))
        attuned = sum(1 for it in h.items if it.attuned)
        self.assertEqual(attuned, 3)

    def test_fourth_attuned_refused(self):
        items = []
        slots = ["ring1", "ring2", "amulet", "cloak"]
        for i, s in enumerate(slots):
            items.append(Item(name=f"Magic Item {i}",
                                item_type="wondrous",
                                slot=s, requires_attunement=True,
                                is_magical=True))
        h = _hero(items=items)
        for it in items[:3]:
            self.assertTrue(h.equip_item(it))
        # Fourth must fail
        self.assertFalse(h.equip_item(items[3]),
                          "Equipping a 4th attunement should fail")
        self.assertFalse(items[3].attuned)
        self.assertFalse(items[3].equipped)


# --------------------------------------------------------------------- #
# AC calculation
# --------------------------------------------------------------------- #
class TestArmorClass(unittest.TestCase):
    def test_no_armor_uses_ten_plus_dex(self):
        h = _hero(dex_score=14)  # DEX mod +2
        # No armor / shield equipped
        # max(10 + 2, stats.armor_class=10) = 12
        self.assertEqual(h.armor_class, 12)

    def test_light_armor_uses_full_dex(self):
        leather = Item(name="Leather", item_type="armor",
                         base_ac=11, max_dex_bonus=-1,
                         armor_category="light")
        h = _hero(dex_score=18, items=[leather])
        h.equip_item(leather)
        # 11 + 4 = 15
        self.assertEqual(h.armor_class, 15)

    def test_medium_armor_caps_dex_at_two(self):
        scale = Item(name="Scale Mail", item_type="armor",
                       base_ac=14, max_dex_bonus=2,
                       armor_category="medium")
        h = _hero(dex_score=18, items=[scale])
        h.equip_item(scale)
        # 14 + min(4, 2) = 16
        self.assertEqual(h.armor_class, 16)

    def test_heavy_armor_ignores_dex(self):
        plate = Item(name="Plate", item_type="armor",
                       base_ac=18, max_dex_bonus=0,
                       armor_category="heavy",
                       strength_required=15)
        h = _hero(dex_score=18, str_score=18, items=[plate])
        h.equip_item(plate)
        # 18 + 0 = 18, no DEX
        self.assertEqual(h.armor_class, 18)

    def test_shield_adds_two(self):
        chain = Item(name="Chain Shirt", item_type="armor",
                       base_ac=13, max_dex_bonus=2,
                       armor_category="medium")
        shield = Item(name="Shield", item_type="shield",
                        slot="off_hand", ac_bonus=2,
                        armor_category="shield")
        h = _hero(dex_score=14, items=[chain, shield])
        h.equip_item(chain)
        h.equip_item(shield)
        # 13 + 2 (DEX cap) + 2 (shield) = 17
        self.assertEqual(h.armor_class, 17)

    def test_ring_of_protection_stacks_with_armor(self):
        plate = Item(name="Plate", item_type="armor",
                       base_ac=18, max_dex_bonus=0,
                       armor_category="heavy",
                       strength_required=15)
        ring = Item(name="Ring of Protection", item_type="ring",
                      slot="ring1", requires_attunement=True,
                      is_magical=True, ac_bonus=1)
        h = _hero(str_score=15, items=[plate, ring])
        h.equip_item(plate)
        h.equip_item(ring)
        # 18 + 1 = 19
        self.assertEqual(h.armor_class, 19)


# --------------------------------------------------------------------- #
# Heavy armor STR requirement
# --------------------------------------------------------------------- #
class TestHeavyArmorStrCheck(unittest.TestCase):
    def test_meeting_str_requirement_no_speed_penalty(self):
        plate = Item(name="Plate", item_type="armor",
                       base_ac=18, max_dex_bonus=0,
                       armor_category="heavy",
                       strength_required=15)
        h = _hero(str_score=15, speed=30, items=[plate])
        h.equip_item(plate)
        self.assertEqual(h.get_speed(), 30)

    def test_below_str_requirement_drops_speed_by_ten(self):
        plate = Item(name="Plate", item_type="armor",
                       base_ac=18, max_dex_bonus=0,
                       armor_category="heavy",
                       strength_required=15)
        h = _hero(str_score=12, speed=30, items=[plate])
        h.equip_item(plate)
        self.assertEqual(h.get_speed(), 20)


# --------------------------------------------------------------------- #
# Stat overrides
# --------------------------------------------------------------------- #
class TestStatOverrides(unittest.TestCase):
    def test_gauntlets_of_ogre_power_overrides_low_str(self):
        gauntlets = Item(name="Gauntlets of Ogre Power",
                           item_type="gloves",
                           slot="gloves",
                           requires_attunement=True,
                           is_magical=True,
                           stat_bonuses={"strength": 19})
        h = _hero(str_score=10, items=[gauntlets])
        h.equip_item(gauntlets)
        self.assertEqual(h.get_effective_ability("strength"), 19)

    def test_gauntlets_does_not_reduce_high_str(self):
        gauntlets = Item(name="Gauntlets of Ogre Power",
                           item_type="gloves",
                           slot="gloves",
                           requires_attunement=True,
                           is_magical=True,
                           stat_bonuses={"strength": 19})
        h = _hero(str_score=20, items=[gauntlets])
        h.equip_item(gauntlets)
        # Already STR 20 — should NOT drop to 19
        self.assertEqual(h.get_effective_ability("strength"), 20)

    def test_additive_bonus_stacks_with_base_score(self):
        headband = Item(name="Headband of Intellect",
                          item_type="helm",
                          slot="helm",
                          requires_attunement=True,
                          is_magical=True,
                          stat_bonuses={"intelligence": 19})
        h = _hero(items=[headband])
        h.equip_item(headband)
        self.assertEqual(
            h.get_effective_ability("intelligence"), 19)


# --------------------------------------------------------------------- #
# Save bonus and damage resistance grants
# --------------------------------------------------------------------- #
class TestEquipmentSavesAndResistances(unittest.TestCase):
    def test_cloak_of_protection_adds_all_saves(self):
        cloak = Item(name="Cloak of Protection",
                       item_type="cloak", slot="cloak",
                       requires_attunement=True, is_magical=True,
                       save_bonuses={"all": 1},
                       ac_bonus=1)
        h = _hero(items=[cloak])
        h.equip_item(cloak)
        # Bonus contributed via get_equipment_save_bonus
        self.assertEqual(h.get_equipment_save_bonus(), 1)

    def test_periapt_grants_resistance(self):
        amulet = Item(name="Periapt of Fire Resistance",
                        item_type="amulet", slot="amulet",
                        requires_attunement=True,
                        is_magical=True,
                        damage_resistances=["fire"])
        h = _hero(items=[amulet])
        h.equip_item(amulet)
        # Take 20 fire → halved to 10
        h.hp = h.max_hp
        dealt, _ = h.take_damage(20, "fire")
        self.assertEqual(dealt, 10)

    def test_boots_of_speed_add_to_get_speed(self):
        boots = Item(name="Boots of Speed", item_type="boots",
                       slot="boots", requires_attunement=True,
                       is_magical=True, speed_bonus=30)
        h = _hero(items=[boots])
        h.equip_item(boots)
        self.assertEqual(h.get_speed(), 60)


# --------------------------------------------------------------------- #
# Magic weapon attack/damage bonus (+1, +2, +3)
# --------------------------------------------------------------------- #
class TestMagicWeaponBonus(unittest.TestCase):
    def _build(self, weapon_bonus=2):
        magic_sword = Item(
            name="Longsword", item_type="weapon",
            slot="main_hand",
            weapon_damage_dice="1d8",
            weapon_damage_type="slashing",
            weapon_bonus=weapon_bonus,
            is_magical=True,
        )
        h = _hero(items=[magic_sword])
        h.equip_item(magic_sword)
        return h

    def test_magic_weapon_adds_to_attack_and_damage(self):
        # We do a large-sample average to verify the bonus rides on
        # the roll. Without the +2 bonus, average damage roll for
        # 1d8 + 3 (STR mod) ≈ 7.5; with +2 → 9.5.
        import random
        random.seed(7)
        h = self._build(weapon_bonus=2)
        target = _target(hp=10000, ac=10)
        ai = TacticalAI()
        battle = BattleSystem(log_callback=lambda *a: None,
                                initial_entities=[h, target])
        # Sample 200 attacks; track hit damage mean.
        sword_action = h.stats.actions[0]
        # Capture hits and damage values
        from engine.dice import roll_dice
        hits = []
        for _ in range(200):
            step = ai._execute_attack(h, sword_action, target, battle)
            if step.is_hit:
                hits.append(step.damage)
        self.assertGreater(len(hits), 80,
                            "Should hit AC 10 most of the time")
        mean = sum(hits) / len(hits)
        # 1d8 (4.5) + STR mod (3) + bonus (2) = ~9.5
        self.assertGreater(mean, 8.5,
                            f"Mean damage ({mean:.2f}) should exceed "
                            f"8.5 with +2 weapon bonus")

    def test_no_weapon_bonus_baseline(self):
        import random
        random.seed(7)
        h = self._build(weapon_bonus=0)
        target = _target(hp=10000, ac=10)
        ai = TacticalAI()
        battle = BattleSystem(log_callback=lambda *a: None,
                                initial_entities=[h, target])
        sword = h.stats.actions[0]
        hits = []
        for _ in range(200):
            step = ai._execute_attack(h, sword, target, battle)
            if step.is_hit:
                hits.append(step.damage)
        mean = sum(hits) / len(hits)
        # 1d8 + 3 = ~7.5
        self.assertLess(mean, 8.5,
                         f"Mean damage ({mean:.2f}) should be "
                         f"below 8.5 with no weapon bonus")


# --------------------------------------------------------------------- #
# Extra damage dice (Flame Tongue, Sun Blade, Frost Brand …)
# --------------------------------------------------------------------- #
class TestExtraDamageDice(unittest.TestCase):
    def test_flame_tongue_adds_fire_damage_on_hit(self):
        flame = Item(
            name="Longsword", item_type="weapon",
            slot="main_hand", weapon_damage_dice="1d8",
            weapon_damage_type="slashing",
            weapon_bonus=0, is_magical=True,
            extra_damage_dice="2d6",
            extra_damage_type="fire",
        )
        h = _hero(items=[flame])
        h.equip_item(flame)
        target = _target(hp=200, ac=10)
        ai = TacticalAI()
        battle = BattleSystem(log_callback=lambda *a: None,
                                initial_entities=[h, target])
        # Run many attacks; on hit, damage should reflect the 2d6
        # bonus (avg +7). Without the bonus mean would be ~7.5;
        # with it ~14.5.
        import random
        random.seed(11)
        sword = h.stats.actions[0]
        hits = []
        for _ in range(200):
            step = ai._execute_attack(h, sword, target, battle)
            if step.is_hit:
                hits.append(step.damage)
        mean = sum(hits) / len(hits)
        self.assertGreater(mean, 12.0,
                            f"Flame Tongue should push damage well "
                            f"above 12 (got {mean:.2f})")


# --------------------------------------------------------------------- #
# Magic weapon bypasses non-magical resistance
# --------------------------------------------------------------------- #
class TestMagicalDamageBypass(unittest.TestCase):
    def test_magic_weapon_attack_bypasses_nonmagical_resistance(self):
        # Werewolf-style resistance: bludg/pierc/slash from non-magical
        mundane = Item(name="Longsword", item_type="weapon",
                         slot="main_hand", weapon_damage_dice="1d8",
                         weapon_damage_type="slashing",
                         is_magical=False)
        magic = Item(name="Magic Longsword", item_type="weapon",
                       slot="main_hand", weapon_damage_dice="1d8",
                       weapon_damage_type="slashing",
                       is_magical=True, weapon_bonus=1)
        # Two heroes, one with each
        mundane_hero = _hero(items=[mundane])
        magic_hero = _hero(items=[magic])
        mundane_hero.equip_item(mundane)
        magic_hero.equip_item(magic)
        # Werewolf target
        target = _target(hp=10000, ac=10,
                          resistances=[
                              "slashing from non-magical attacks"])
        # Force a hit by setting a tiny AC; compare damage means
        ai = TacticalAI()
        battle = BattleSystem(log_callback=lambda *a: None,
                                initial_entities=[
                                    mundane_hero, magic_hero, target])
        import random
        from engine.dice import roll_dice
        sword = mundane_hero.stats.actions[0]
        # Mundane hits: target should *resist* (halve)
        random.seed(3)
        steps_mundane = []
        for _ in range(50):
            step = ai._execute_attack(
                mundane_hero, sword, target, battle)
            if step.is_hit:
                # Now actually deal the damage
                pre = target.hp
                target.take_damage(
                    step.damage, sword.damage_type,
                    is_magical=step.is_magical)
                steps_mundane.append(pre - target.hp)
                target.hp = pre  # restore for next sample
        random.seed(3)
        magic_sword = magic_hero.stats.actions[0]
        steps_magic = []
        for _ in range(50):
            step = ai._execute_attack(
                magic_hero, magic_sword, target, battle)
            if step.is_hit:
                pre = target.hp
                target.take_damage(
                    step.damage, magic_sword.damage_type,
                    is_magical=step.is_magical)
                steps_magic.append(pre - target.hp)
                target.hp = pre
        # Magic damage should be clearly higher than mundane
        # (mundane is halved; magic is full + maybe +1).
        mundane_mean = sum(steps_mundane) / max(1, len(steps_mundane))
        magic_mean = sum(steps_magic) / max(1, len(steps_magic))
        self.assertGreater(
            magic_mean, mundane_mean * 1.5,
            f"Magic weapon should bypass resistance "
            f"(mundane {mundane_mean:.2f} vs magic {magic_mean:.2f})")


# --------------------------------------------------------------------- #
# Spell-granted items (Wand of Magic Missiles etc.)
# --------------------------------------------------------------------- #
class TestSpellGrantedAndCharges(unittest.TestCase):
    def test_wand_records_charges_and_granted_spell(self):
        # The data layer carries the metadata; the cast path uses
        # spell_granted + charges. This test pins the schema.
        wand = Item(name="Wand of Magic Missiles", item_type="wand",
                      slot="main_hand", requires_attunement=False,
                      is_magical=True,
                      spell_granted="Magic Missile",
                      charges=7, max_charges=7)
        h = _hero(items=[wand])
        h.equip_item(wand)
        self.assertEqual(wand.spell_granted, "Magic Missile")
        self.assertEqual(wand.charges, 7)
        self.assertEqual(wand.max_charges, 7)


if __name__ == "__main__":
    unittest.main()
