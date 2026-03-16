"""
D&D 5e 2014 Item Database — Potions, Equipment, Scrolls, Wondrous Items.
Covers common combat consumables, armor, weapons, and magic items
from early-game (Tier 1-2) through endgame (Tier 3-4).

Usage:
    from data.items import get_item, search_items, get_items_by_type, get_items_by_rarity
    potion = get_item("Potion of Healing")
    fire_res = search_items("fire")
    all_potions = get_items_by_type("potion")
"""
import copy
from typing import List, Optional
from data.models import Item


# ============================================================================
# POTIONS (PHB p.187-188, DMG p.187-188)
# All potions: action to drink (or administer to another), consumable
# ============================================================================

_potions = [
    # -- Healing Potions (DMG p.187) --
    Item(name="Potion of Healing", item_type="potion", uses=1, rarity="common",
         heals="2d4+2", description="Regain 2d4+2 HP."),
    Item(name="Potion of Greater Healing", item_type="potion", uses=1, rarity="uncommon",
         heals="4d4+4", description="Regain 4d4+4 HP."),
    Item(name="Potion of Superior Healing", item_type="potion", uses=1, rarity="rare",
         heals="8d4+8", description="Regain 8d4+8 HP."),
    Item(name="Potion of Supreme Healing", item_type="potion", uses=1, rarity="very_rare",
         heals="10d4+20", description="Regain 10d4+20 HP."),

    # -- Buff Potions (DMG p.187-189) --
    Item(name="Potion of Fire Resistance", item_type="potion", uses=1, rarity="uncommon",
         buff="resistance:fire", description="Resistance to fire damage for 1 hour."),
    Item(name="Potion of Cold Resistance", item_type="potion", uses=1, rarity="uncommon",
         buff="resistance:cold", description="Resistance to cold damage for 1 hour."),
    Item(name="Potion of Lightning Resistance", item_type="potion", uses=1, rarity="uncommon",
         buff="resistance:lightning", description="Resistance to lightning damage for 1 hour."),
    Item(name="Potion of Acid Resistance", item_type="potion", uses=1, rarity="uncommon",
         buff="resistance:acid", description="Resistance to acid damage for 1 hour."),
    Item(name="Potion of Necrotic Resistance", item_type="potion", uses=1, rarity="uncommon",
         buff="resistance:necrotic", description="Resistance to necrotic damage for 1 hour."),
    Item(name="Potion of Poison Resistance", item_type="potion", uses=1, rarity="uncommon",
         buff="resistance:poison", description="Resistance to poison damage for 1 hour."),
    Item(name="Potion of Heroism", item_type="potion", uses=1, rarity="rare",
         buff="temp_hp:10", description="Gain 10 temp HP and Bless effect for 1 hour."),
    Item(name="Potion of Speed", item_type="potion", uses=1, rarity="very_rare",
         buff="haste", description="Haste effect for 1 minute (no concentration)."),
    Item(name="Potion of Invulnerability", item_type="potion", uses=1, rarity="rare",
         buff="resistance:all", description="Resistance to all damage for 1 minute."),
    Item(name="Potion of Hill Giant Strength", item_type="potion", uses=1, rarity="uncommon",
         buff="strength:21", description="STR becomes 21 for 1 hour.",
         stat_bonuses={"strength": 21}),
    Item(name="Potion of Frost Giant Strength", item_type="potion", uses=1, rarity="rare",
         buff="strength:23", description="STR becomes 23 for 1 hour.",
         stat_bonuses={"strength": 23}),
    Item(name="Potion of Fire Giant Strength", item_type="potion", uses=1, rarity="rare",
         buff="strength:25", description="STR becomes 25 for 1 hour.",
         stat_bonuses={"strength": 25}),
    Item(name="Potion of Cloud Giant Strength", item_type="potion", uses=1, rarity="very_rare",
         buff="strength:27", description="STR becomes 27 for 1 hour.",
         stat_bonuses={"strength": 27}),
    Item(name="Potion of Flying", item_type="potion", uses=1, rarity="very_rare",
         buff="fly:60", description="Gain 60 ft fly speed for 1 hour."),

    # -- Offensive Potions --
    Item(name="Oil of Sharpness", item_type="potion", uses=1, rarity="very_rare",
         buff="weapon_bonus:3", description="Weapon becomes +3 for 1 hour."),
    Item(name="Potion of Poison", item_type="potion", uses=1, rarity="uncommon",
         damage_dice="3d6", applies_condition="Poisoned",
         description="Target takes 3d6 poison and is Poisoned. DC 13 CON save halves and avoids condition."),

    # -- Utility Potions --
    Item(name="Antitoxin", item_type="potion", uses=1, rarity="common",
         buff="advantage:poison_saves", description="Advantage on saves vs poison for 1 hour."),
    Item(name="Potion of Invisibility", item_type="potion", uses=1, rarity="very_rare",
         buff="invisible", description="Invisible for 1 hour or until you attack/cast."),
]

# ============================================================================
# SCROLLS (DMG p.199-200)
# Action to read, consumable, requires spell on your class list
# ============================================================================

_scrolls = [
    # Tier 1-2
    Item(name="Scroll of Shield", item_type="scroll", uses=1, rarity="common",
         spell_granted="Shield", description="Cast Shield (reaction, +5 AC until next turn)."),
    Item(name="Scroll of Cure Wounds", item_type="scroll", uses=1, rarity="common",
         heals="1d8+3", spell_granted="Cure Wounds",
         description="Cast Cure Wounds at 1st level."),
    Item(name="Scroll of Healing Word", item_type="scroll", uses=1, rarity="common",
         heals="1d4+3", spell_granted="Healing Word",
         description="Cast Healing Word at 1st level (bonus action, 60 ft)."),
    Item(name="Scroll of Bless", item_type="scroll", uses=1, rarity="common",
         spell_granted="Bless", description="Cast Bless (concentration, 3 targets +1d4 attacks/saves)."),
    Item(name="Scroll of Protection from Evil and Good", item_type="scroll", uses=1, rarity="common",
         spell_granted="Protection from Evil and Good",
         description="Protection from aberrations, celestials, elementals, fey, fiends, undead."),
    Item(name="Scroll of Misty Step", item_type="scroll", uses=1, rarity="uncommon",
         spell_granted="Misty Step", description="Bonus action teleport 30 ft."),
    Item(name="Scroll of Lesser Restoration", item_type="scroll", uses=1, rarity="uncommon",
         spell_granted="Lesser Restoration",
         description="End one disease or condition: blinded, deafened, paralyzed, poisoned."),
    Item(name="Scroll of Counterspell", item_type="scroll", uses=1, rarity="uncommon",
         spell_granted="Counterspell", description="Reaction: counter a spell being cast (auto if 3rd or lower)."),

    # Tier 2-3
    Item(name="Scroll of Revivify", item_type="scroll", uses=1, rarity="rare",
         spell_granted="Revivify", heals="1",
         description="Return creature dead <1 min to life with 1 HP."),
    Item(name="Scroll of Fireball", item_type="scroll", uses=1, rarity="uncommon",
         spell_granted="Fireball", damage_dice="8d6",
         description="Cast Fireball (8d6 fire, 20ft sphere, DC 15 DEX save)."),
    Item(name="Scroll of Haste", item_type="scroll", uses=1, rarity="rare",
         spell_granted="Haste", description="Haste one creature (concentration, 1 min)."),
    Item(name="Scroll of Dispel Magic", item_type="scroll", uses=1, rarity="uncommon",
         spell_granted="Dispel Magic", description="End one spell of 3rd level or lower on target."),

    # Tier 3-4
    Item(name="Scroll of Greater Restoration", item_type="scroll", uses=1, rarity="rare",
         spell_granted="Greater Restoration",
         description="End one: charmed, petrified, curse, ability reduction, or max HP reduction."),
    Item(name="Scroll of Raise Dead", item_type="scroll", uses=1, rarity="rare",
         spell_granted="Raise Dead", heals="1",
         description="Return creature dead <10 days to life with 1 HP."),
    Item(name="Scroll of Wall of Force", item_type="scroll", uses=1, rarity="rare",
         spell_granted="Wall of Force",
         description="Create invisible wall. Nothing physically passes through. 10 min."),
]

# ============================================================================
# WEAPONS (PHB p.146-149)
# ============================================================================

_weapons = [
    # -- Simple Melee --
    Item(name="Dagger", item_type="weapon", uses=-1, rarity="common",
         slot="main_hand", weapon_damage_dice="1d4", weapon_damage_type="piercing",
         weapon_properties=["finesse", "light", "thrown"], weapon_range=5, weapon_long_range=60,
         weapon_category="simple_melee", description="Simple melee weapon."),
    Item(name="Handaxe", item_type="weapon", uses=-1, rarity="common",
         slot="main_hand", weapon_damage_dice="1d6", weapon_damage_type="slashing",
         weapon_properties=["light", "thrown"], weapon_range=5, weapon_long_range=60,
         weapon_category="simple_melee", description="Simple melee weapon."),
    Item(name="Javelin", item_type="weapon", uses=-1, rarity="common",
         slot="main_hand", weapon_damage_dice="1d6", weapon_damage_type="piercing",
         weapon_properties=["thrown"], weapon_range=30, weapon_long_range=120,
         weapon_category="simple_melee", description="Simple melee weapon."),
    Item(name="Mace", item_type="weapon", uses=-1, rarity="common",
         slot="main_hand", weapon_damage_dice="1d6", weapon_damage_type="bludgeoning",
         weapon_category="simple_melee", description="Simple melee weapon."),
    Item(name="Quarterstaff", item_type="weapon", uses=-1, rarity="common",
         slot="main_hand", weapon_damage_dice="1d6", weapon_damage_type="bludgeoning",
         weapon_properties=["versatile"], weapon_category="simple_melee",
         description="Simple melee weapon. Versatile (1d8)."),
    Item(name="Spear", item_type="weapon", uses=-1, rarity="common",
         slot="main_hand", weapon_damage_dice="1d6", weapon_damage_type="piercing",
         weapon_properties=["thrown", "versatile"], weapon_range=5, weapon_long_range=60,
         weapon_category="simple_melee", description="Simple melee weapon. Versatile (1d8)."),

    # -- Martial Melee --
    Item(name="Battleaxe", item_type="weapon", uses=-1, rarity="common",
         slot="main_hand", weapon_damage_dice="1d8", weapon_damage_type="slashing",
         weapon_properties=["versatile"], weapon_category="martial_melee",
         description="Martial melee weapon. Versatile (1d10)."),
    Item(name="Greataxe", item_type="weapon", uses=-1, rarity="common",
         slot="main_hand", weapon_damage_dice="1d12", weapon_damage_type="slashing",
         weapon_properties=["heavy", "two-handed"], weapon_category="martial_melee",
         description="Martial melee weapon."),
    Item(name="Greatsword", item_type="weapon", uses=-1, rarity="common",
         slot="main_hand", weapon_damage_dice="2d6", weapon_damage_type="slashing",
         weapon_properties=["heavy", "two-handed"], weapon_category="martial_melee",
         description="Martial melee weapon."),
    Item(name="Longsword", item_type="weapon", uses=-1, rarity="common",
         slot="main_hand", weapon_damage_dice="1d8", weapon_damage_type="slashing",
         weapon_properties=["versatile"], weapon_category="martial_melee",
         description="Martial melee weapon. Versatile (1d10)."),
    Item(name="Rapier", item_type="weapon", uses=-1, rarity="common",
         slot="main_hand", weapon_damage_dice="1d8", weapon_damage_type="piercing",
         weapon_properties=["finesse"], weapon_category="martial_melee",
         description="Martial melee weapon."),
    Item(name="Scimitar", item_type="weapon", uses=-1, rarity="common",
         slot="main_hand", weapon_damage_dice="1d6", weapon_damage_type="slashing",
         weapon_properties=["finesse", "light"], weapon_category="martial_melee",
         description="Martial melee weapon."),
    Item(name="Shortsword", item_type="weapon", uses=-1, rarity="common",
         slot="main_hand", weapon_damage_dice="1d6", weapon_damage_type="piercing",
         weapon_properties=["finesse", "light"], weapon_category="martial_melee",
         description="Martial melee weapon."),
    Item(name="Warhammer", item_type="weapon", uses=-1, rarity="common",
         slot="main_hand", weapon_damage_dice="1d8", weapon_damage_type="bludgeoning",
         weapon_properties=["versatile"], weapon_category="martial_melee",
         description="Martial melee weapon. Versatile (1d10)."),
    Item(name="Maul", item_type="weapon", uses=-1, rarity="common",
         slot="main_hand", weapon_damage_dice="2d6", weapon_damage_type="bludgeoning",
         weapon_properties=["heavy", "two-handed"], weapon_category="martial_melee",
         description="Martial melee weapon."),
    Item(name="Halberd", item_type="weapon", uses=-1, rarity="common",
         slot="main_hand", weapon_damage_dice="1d10", weapon_damage_type="slashing",
         weapon_properties=["heavy", "reach", "two-handed"], weapon_range=10,
         weapon_category="martial_melee", description="Martial melee weapon. Reach 10ft."),

    # -- Ranged --
    Item(name="Shortbow", item_type="weapon", uses=-1, rarity="common",
         slot="main_hand", weapon_damage_dice="1d6", weapon_damage_type="piercing",
         weapon_properties=["two-handed"], weapon_range=80, weapon_long_range=320,
         weapon_category="simple_ranged", description="Simple ranged weapon."),
    Item(name="Longbow", item_type="weapon", uses=-1, rarity="common",
         slot="main_hand", weapon_damage_dice="1d8", weapon_damage_type="piercing",
         weapon_properties=["heavy", "two-handed"], weapon_range=150, weapon_long_range=600,
         weapon_category="martial_ranged", description="Martial ranged weapon."),
    Item(name="Light Crossbow", item_type="weapon", uses=-1, rarity="common",
         slot="main_hand", weapon_damage_dice="1d8", weapon_damage_type="piercing",
         weapon_properties=["loading", "two-handed"], weapon_range=80, weapon_long_range=320,
         weapon_category="simple_ranged", description="Simple ranged weapon."),
    Item(name="Heavy Crossbow", item_type="weapon", uses=-1, rarity="common",
         slot="main_hand", weapon_damage_dice="1d10", weapon_damage_type="piercing",
         weapon_properties=["heavy", "loading", "two-handed"], weapon_range=100, weapon_long_range=400,
         weapon_category="martial_ranged", description="Martial ranged weapon."),
    Item(name="Hand Crossbow", item_type="weapon", uses=-1, rarity="common",
         slot="main_hand", weapon_damage_dice="1d6", weapon_damage_type="piercing",
         weapon_properties=["light", "loading"], weapon_range=30, weapon_long_range=120,
         weapon_category="martial_ranged", description="Martial ranged weapon."),

    # -- Magic Weapons (DMG) --
    Item(name="+1 Longsword", item_type="weapon", uses=-1, rarity="uncommon",
         slot="main_hand", weapon_damage_dice="1d8", weapon_damage_type="slashing",
         weapon_properties=["versatile"], weapon_category="martial_melee",
         weapon_bonus=1, is_magical=True,
         description="+1 to attack and damage rolls."),
    Item(name="+2 Longsword", item_type="weapon", uses=-1, rarity="rare",
         slot="main_hand", weapon_damage_dice="1d8", weapon_damage_type="slashing",
         weapon_properties=["versatile"], weapon_category="martial_melee",
         weapon_bonus=2, is_magical=True,
         description="+2 to attack and damage rolls."),
    Item(name="+3 Longsword", item_type="weapon", uses=-1, rarity="very_rare",
         slot="main_hand", weapon_damage_dice="1d8", weapon_damage_type="slashing",
         weapon_properties=["versatile"], weapon_category="martial_melee",
         weapon_bonus=3, is_magical=True,
         description="+3 to attack and damage rolls."),
    Item(name="+1 Greatsword", item_type="weapon", uses=-1, rarity="uncommon",
         slot="main_hand", weapon_damage_dice="2d6", weapon_damage_type="slashing",
         weapon_properties=["heavy", "two-handed"], weapon_category="martial_melee",
         weapon_bonus=1, is_magical=True,
         description="+1 to attack and damage rolls."),
    Item(name="+1 Rapier", item_type="weapon", uses=-1, rarity="uncommon",
         slot="main_hand", weapon_damage_dice="1d8", weapon_damage_type="piercing",
         weapon_properties=["finesse"], weapon_category="martial_melee",
         weapon_bonus=1, is_magical=True,
         description="+1 to attack and damage rolls."),
    Item(name="+2 Rapier", item_type="weapon", uses=-1, rarity="rare",
         slot="main_hand", weapon_damage_dice="1d8", weapon_damage_type="piercing",
         weapon_properties=["finesse"], weapon_category="martial_melee",
         weapon_bonus=2, is_magical=True,
         description="+2 to attack and damage rolls."),
    Item(name="+1 Longbow", item_type="weapon", uses=-1, rarity="uncommon",
         slot="main_hand", weapon_damage_dice="1d8", weapon_damage_type="piercing",
         weapon_properties=["heavy", "two-handed"], weapon_range=150, weapon_long_range=600,
         weapon_category="martial_ranged", weapon_bonus=1, is_magical=True,
         description="+1 to attack and damage rolls."),
    Item(name="+2 Longbow", item_type="weapon", uses=-1, rarity="rare",
         slot="main_hand", weapon_damage_dice="1d8", weapon_damage_type="piercing",
         weapon_properties=["heavy", "two-handed"], weapon_range=150, weapon_long_range=600,
         weapon_category="martial_ranged", weapon_bonus=2, is_magical=True,
         description="+2 to attack and damage rolls."),
    Item(name="+1 Greataxe", item_type="weapon", uses=-1, rarity="uncommon",
         slot="main_hand", weapon_damage_dice="1d12", weapon_damage_type="slashing",
         weapon_properties=["heavy", "two-handed"], weapon_category="martial_melee",
         weapon_bonus=1, is_magical=True,
         description="+1 to attack and damage rolls."),
    Item(name="+1 Warhammer", item_type="weapon", uses=-1, rarity="uncommon",
         slot="main_hand", weapon_damage_dice="1d8", weapon_damage_type="bludgeoning",
         weapon_properties=["versatile"], weapon_category="martial_melee",
         weapon_bonus=1, is_magical=True,
         description="+1 to attack and damage rolls."),
    Item(name="+1 Hand Crossbow", item_type="weapon", uses=-1, rarity="uncommon",
         slot="main_hand", weapon_damage_dice="1d6", weapon_damage_type="piercing",
         weapon_properties=["light", "loading"], weapon_range=30, weapon_long_range=120,
         weapon_category="martial_ranged", weapon_bonus=1, is_magical=True,
         description="+1 to attack and damage rolls."),

    # -- Special Magic Weapons --
    Item(name="Flame Tongue Longsword", item_type="weapon", uses=-1, rarity="rare",
         slot="main_hand", weapon_damage_dice="1d8", weapon_damage_type="slashing",
         weapon_properties=["versatile"], weapon_category="martial_melee",
         is_magical=True, requires_attunement=True,
         extra_damage_dice="2d6", extra_damage_type="fire",
         description="While lit (bonus action), +2d6 fire damage and sheds light."),
    Item(name="Frost Brand Longsword", item_type="weapon", uses=-1, rarity="very_rare",
         slot="main_hand", weapon_damage_dice="1d8", weapon_damage_type="slashing",
         weapon_properties=["versatile"], weapon_category="martial_melee",
         is_magical=True, requires_attunement=True,
         extra_damage_dice="1d6", extra_damage_type="cold",
         damage_resistances=["fire"],
         description="+1d6 cold damage. Resistance to fire."),
    Item(name="Flame Tongue Greatsword", item_type="weapon", uses=-1, rarity="rare",
         slot="main_hand", weapon_damage_dice="2d6", weapon_damage_type="slashing",
         weapon_properties=["heavy", "two-handed"], weapon_category="martial_melee",
         is_magical=True, requires_attunement=True,
         extra_damage_dice="2d6", extra_damage_type="fire",
         description="While lit (bonus action), +2d6 fire damage."),
    Item(name="Sun Blade", item_type="weapon", uses=-1, rarity="rare",
         slot="main_hand", weapon_damage_dice="1d8", weapon_damage_type="radiant",
         weapon_properties=["finesse", "versatile"], weapon_category="martial_melee",
         weapon_bonus=2, is_magical=True, requires_attunement=True,
         description="+2 weapon. Radiant damage. +1d8 vs undead."),
    Item(name="Dragon Slayer Longsword", item_type="weapon", uses=-1, rarity="rare",
         slot="main_hand", weapon_damage_dice="1d8", weapon_damage_type="slashing",
         weapon_properties=["versatile"], weapon_category="martial_melee",
         weapon_bonus=1, is_magical=True,
         description="+1 weapon. +3d6 damage vs dragons."),
    Item(name="Vicious Rapier", item_type="weapon", uses=-1, rarity="rare",
         slot="main_hand", weapon_damage_dice="1d8", weapon_damage_type="piercing",
         weapon_properties=["finesse"], weapon_category="martial_melee",
         is_magical=True, description="On nat 20, deal extra 7 damage."),
    Item(name="Javelin of Lightning", item_type="weapon", uses=1, rarity="uncommon",
         slot="main_hand", weapon_damage_dice="1d6", weapon_damage_type="piercing",
         weapon_properties=["thrown"], weapon_range=30, weapon_long_range=120,
         weapon_category="simple_melee", is_magical=True,
         damage_dice="4d6", description="Throw: 4d6 lightning in 120ft line, DC 13 DEX save."),
]

# ============================================================================
# ARMOR & SHIELDS (PHB p.144-146)
# ============================================================================

_armor = [
    # -- Light Armor --
    Item(name="Padded Armor", item_type="armor", uses=-1, rarity="common",
         slot="armor", base_ac=11, max_dex_bonus=-1, armor_category="light",
         stealth_disadvantage=True, description="Light armor. AC 11 + DEX."),
    Item(name="Leather Armor", item_type="armor", uses=-1, rarity="common",
         slot="armor", base_ac=11, max_dex_bonus=-1, armor_category="light",
         description="Light armor. AC 11 + DEX."),
    Item(name="Studded Leather Armor", item_type="armor", uses=-1, rarity="common",
         slot="armor", base_ac=12, max_dex_bonus=-1, armor_category="light",
         description="Light armor. AC 12 + DEX."),

    # -- Medium Armor --
    Item(name="Hide Armor", item_type="armor", uses=-1, rarity="common",
         slot="armor", base_ac=12, max_dex_bonus=2, armor_category="medium",
         description="Medium armor. AC 12 + DEX (max 2)."),
    Item(name="Chain Shirt", item_type="armor", uses=-1, rarity="common",
         slot="armor", base_ac=13, max_dex_bonus=2, armor_category="medium",
         description="Medium armor. AC 13 + DEX (max 2)."),
    Item(name="Scale Mail", item_type="armor", uses=-1, rarity="common",
         slot="armor", base_ac=14, max_dex_bonus=2, armor_category="medium",
         stealth_disadvantage=True, description="Medium armor. AC 14 + DEX (max 2)."),
    Item(name="Breastplate", item_type="armor", uses=-1, rarity="common",
         slot="armor", base_ac=14, max_dex_bonus=2, armor_category="medium",
         description="Medium armor. AC 14 + DEX (max 2)."),
    Item(name="Half Plate", item_type="armor", uses=-1, rarity="common",
         slot="armor", base_ac=15, max_dex_bonus=2, armor_category="medium",
         stealth_disadvantage=True, description="Medium armor. AC 15 + DEX (max 2)."),

    # -- Heavy Armor --
    Item(name="Ring Mail", item_type="armor", uses=-1, rarity="common",
         slot="armor", base_ac=14, max_dex_bonus=0, armor_category="heavy",
         stealth_disadvantage=True, description="Heavy armor. AC 14."),
    Item(name="Chain Mail", item_type="armor", uses=-1, rarity="common",
         slot="armor", base_ac=16, max_dex_bonus=0, armor_category="heavy",
         stealth_disadvantage=True, strength_required=13,
         description="Heavy armor. AC 16. STR 13 required."),
    Item(name="Splint Armor", item_type="armor", uses=-1, rarity="common",
         slot="armor", base_ac=17, max_dex_bonus=0, armor_category="heavy",
         stealth_disadvantage=True, strength_required=15,
         description="Heavy armor. AC 17. STR 15 required."),
    Item(name="Plate Armor", item_type="armor", uses=-1, rarity="common",
         slot="armor", base_ac=18, max_dex_bonus=0, armor_category="heavy",
         stealth_disadvantage=True, strength_required=15,
         description="Heavy armor. AC 18. STR 15 required."),

    # -- Magic Armor --
    Item(name="+1 Chain Mail", item_type="armor", uses=-1, rarity="rare",
         slot="armor", base_ac=16, max_dex_bonus=0, armor_category="heavy",
         ac_bonus=1, is_magical=True, stealth_disadvantage=True, strength_required=13,
         description="AC 17. Magic armor."),
    Item(name="+1 Plate Armor", item_type="armor", uses=-1, rarity="rare",
         slot="armor", base_ac=18, max_dex_bonus=0, armor_category="heavy",
         ac_bonus=1, is_magical=True, stealth_disadvantage=True, strength_required=15,
         description="AC 19. Magic armor."),
    Item(name="+2 Plate Armor", item_type="armor", uses=-1, rarity="very_rare",
         slot="armor", base_ac=18, max_dex_bonus=0, armor_category="heavy",
         ac_bonus=2, is_magical=True, stealth_disadvantage=True, strength_required=15,
         description="AC 20. Magic armor."),
    Item(name="+3 Plate Armor", item_type="armor", uses=-1, rarity="legendary",
         slot="armor", base_ac=18, max_dex_bonus=0, armor_category="heavy",
         ac_bonus=3, is_magical=True, stealth_disadvantage=True, strength_required=15,
         description="AC 21. Magic armor."),
    Item(name="+1 Studded Leather", item_type="armor", uses=-1, rarity="rare",
         slot="armor", base_ac=12, max_dex_bonus=-1, armor_category="light",
         ac_bonus=1, is_magical=True,
         description="AC 13 + DEX. Magic armor."),
    Item(name="+2 Studded Leather", item_type="armor", uses=-1, rarity="very_rare",
         slot="armor", base_ac=12, max_dex_bonus=-1, armor_category="light",
         ac_bonus=2, is_magical=True,
         description="AC 14 + DEX. Magic armor."),
    Item(name="+1 Half Plate", item_type="armor", uses=-1, rarity="rare",
         slot="armor", base_ac=15, max_dex_bonus=2, armor_category="medium",
         ac_bonus=1, is_magical=True, stealth_disadvantage=True,
         description="AC 16 + DEX (max 2). Magic armor."),
    Item(name="+1 Breastplate", item_type="armor", uses=-1, rarity="rare",
         slot="armor", base_ac=14, max_dex_bonus=2, armor_category="medium",
         ac_bonus=1, is_magical=True,
         description="AC 15 + DEX (max 2). Magic armor."),
    Item(name="Mithral Half Plate", item_type="armor", uses=-1, rarity="uncommon",
         slot="armor", base_ac=15, max_dex_bonus=2, armor_category="medium",
         is_magical=True, description="No stealth disadvantage. AC 15 + DEX (max 2)."),
    Item(name="Adamantine Plate", item_type="armor", uses=-1, rarity="uncommon",
         slot="armor", base_ac=18, max_dex_bonus=0, armor_category="heavy",
         is_magical=True, stealth_disadvantage=True, strength_required=15,
         description="AC 18. Crits against you become normal hits."),

    # -- Shields --
    Item(name="Shield", item_type="shield", uses=-1, rarity="common",
         slot="off_hand", ac_bonus=2, armor_category="shield",
         description="+2 AC."),
    Item(name="+1 Shield", item_type="shield", uses=-1, rarity="uncommon",
         slot="off_hand", ac_bonus=3, armor_category="shield", is_magical=True,
         description="+3 AC."),
    Item(name="+2 Shield", item_type="shield", uses=-1, rarity="rare",
         slot="off_hand", ac_bonus=4, armor_category="shield", is_magical=True,
         description="+4 AC."),
    Item(name="+3 Shield", item_type="shield", uses=-1, rarity="very_rare",
         slot="off_hand", ac_bonus=5, armor_category="shield", is_magical=True,
         description="+5 AC."),
    Item(name="Sentinel Shield", item_type="shield", uses=-1, rarity="uncommon",
         slot="off_hand", ac_bonus=2, armor_category="shield", is_magical=True,
         description="+2 AC. Advantage on initiative and Perception checks."),
    Item(name="Shield of Missile Attraction", item_type="shield", uses=-1, rarity="rare",
         slot="off_hand", ac_bonus=2, armor_category="shield", is_magical=True,
         requires_attunement=True,
         description="+2 AC. Resistance to ranged weapon attacks while attuned."),
]

# ============================================================================
# WONDROUS ITEMS, RINGS, CLOAKS, ETC. (DMG Chapter 7)
# ============================================================================

_wondrous = [
    # -- Cloaks --
    Item(name="Cloak of Protection", item_type="cloak", uses=-1, rarity="uncommon",
         slot="cloak", ac_bonus=1, save_bonuses={"all": 1},
         requires_attunement=True, is_magical=True,
         description="+1 AC and +1 all saving throws."),
    Item(name="Cloak of Displacement", item_type="cloak", uses=-1, rarity="rare",
         slot="cloak", requires_attunement=True, is_magical=True,
         buff="displacement",
         description="Attacks against you have disadvantage. Resets if you take damage."),
    Item(name="Cloak of the Bat", item_type="cloak", uses=-1, rarity="rare",
         slot="cloak", requires_attunement=True, is_magical=True,
         description="Advantage on Stealth. In dim light/darkness: fly 40 ft."),
    Item(name="Mantle of Spell Resistance", item_type="cloak", uses=-1, rarity="rare",
         slot="cloak", requires_attunement=True, is_magical=True,
         description="Advantage on saving throws against spells."),

    # -- Rings --
    Item(name="Ring of Protection", item_type="ring", uses=-1, rarity="rare",
         slot="ring1", ac_bonus=1, save_bonuses={"all": 1},
         requires_attunement=True, is_magical=True,
         description="+1 AC and +1 all saving throws."),
    Item(name="Ring of Spell Storing", item_type="ring", uses=-1, rarity="rare",
         slot="ring1", requires_attunement=True, is_magical=True,
         description="Store up to 5 levels of spells. Any creature can cast stored spells."),
    Item(name="Ring of Evasion", item_type="ring", uses=3, rarity="rare",
         slot="ring1", requires_attunement=True, is_magical=True,
         description="3 charges. Reaction: turn failed DEX save into success."),
    Item(name="Ring of Free Action", item_type="ring", uses=-1, rarity="rare",
         slot="ring1", requires_attunement=True, is_magical=True,
         condition_immunities=["Paralyzed", "Restrained"],
         description="Can't be paralyzed or restrained. Ignore difficult terrain."),
    Item(name="Ring of Resistance (Fire)", item_type="ring", uses=-1, rarity="rare",
         slot="ring1", requires_attunement=True, is_magical=True,
         damage_resistances=["fire"],
         description="Resistance to fire damage."),

    # -- Amulets --
    Item(name="Amulet of Health", item_type="amulet", uses=-1, rarity="rare",
         slot="amulet", stat_bonuses={"constitution": 19},
         requires_attunement=True, is_magical=True,
         description="CON becomes 19."),
    Item(name="Periapt of Wound Closure", item_type="amulet", uses=-1, rarity="uncommon",
         slot="amulet", requires_attunement=True, is_magical=True,
         description="Stabilize automatically at 0 HP. Double HP from hit dice healing."),
    Item(name="Periapt of Proof Against Poison", item_type="amulet", uses=-1, rarity="uncommon",
         slot="amulet", is_magical=True,
         damage_immunities=["poison"], condition_immunities=["Poisoned"],
         description="Immune to poison damage and Poisoned condition."),
    Item(name="Amulet of Proof Against Detection", item_type="amulet", uses=-1, rarity="uncommon",
         slot="amulet", requires_attunement=True, is_magical=True,
         description="Hidden from divination magic. Can't be targeted by scrying."),

    # -- Boots --
    Item(name="Boots of Speed", item_type="boots", uses=-1, rarity="rare",
         slot="boots", requires_attunement=True, is_magical=True,
         speed_bonus=99,  # 99 = double speed marker
         description="Bonus action: double speed for 10 min. Attacks of opportunity have disadvantage."),
    Item(name="Boots of Elvenkind", item_type="boots", uses=-1, rarity="uncommon",
         slot="boots", is_magical=True,
         skill_bonuses={"Stealth": 5},
         description="Advantage on Stealth checks."),
    Item(name="Boots of Striding and Springing", item_type="boots", uses=-1, rarity="uncommon",
         slot="boots", requires_attunement=True, is_magical=True,
         speed_bonus=0,  # Speed becomes 30 minimum
         description="Speed can't be reduced below 30. Triple jump distance."),
    Item(name="Winged Boots", item_type="boots", uses=-1, rarity="uncommon",
         slot="boots", requires_attunement=True, is_magical=True,
         description="Fly speed equal to walking speed for 4 hours per day."),

    # -- Gloves / Gauntlets --
    Item(name="Gauntlets of Ogre Power", item_type="gloves", uses=-1, rarity="uncommon",
         slot="gloves", stat_bonuses={"strength": 19},
         requires_attunement=True, is_magical=True,
         description="STR becomes 19."),
    Item(name="Gloves of Missile Snaring", item_type="gloves", uses=-1, rarity="uncommon",
         slot="gloves", requires_attunement=True, is_magical=True,
         description="Reaction: reduce ranged weapon hit damage by 1d10 + DEX."),
    Item(name="Gloves of Thievery", item_type="gloves", uses=-1, rarity="uncommon",
         slot="gloves", is_magical=True,
         skill_bonuses={"Sleight of Hand": 5},
         description="+5 Sleight of Hand. Invisible while worn."),

    # -- Belts --
    Item(name="Belt of Hill Giant Strength", item_type="belt", uses=-1, rarity="rare",
         slot="belt", stat_bonuses={"strength": 21},
         requires_attunement=True, is_magical=True,
         description="STR becomes 21."),
    Item(name="Belt of Fire Giant Strength", item_type="belt", uses=-1, rarity="very_rare",
         slot="belt", stat_bonuses={"strength": 25},
         requires_attunement=True, is_magical=True,
         description="STR becomes 25."),
    Item(name="Belt of Storm Giant Strength", item_type="belt", uses=-1, rarity="legendary",
         slot="belt", stat_bonuses={"strength": 29},
         requires_attunement=True, is_magical=True,
         description="STR becomes 29."),
    Item(name="Belt of Dwarvenkind", item_type="belt", uses=-1, rarity="rare",
         slot="belt", requires_attunement=True, is_magical=True,
         stat_bonuses={"constitution": 2},
         damage_resistances=["poison"],
         description="+2 CON. Advantage vs poison. Resistance to poison."),

    # -- Helms --
    Item(name="Helm of Brilliance", item_type="helm", uses=-1, rarity="very_rare",
         slot="helm", requires_attunement=True, is_magical=True,
         damage_resistances=["fire"],
         description="Gems cast spells. Fire resistance. Melee weapons deal +1d6 fire."),
    Item(name="Headband of Intellect", item_type="helm", uses=-1, rarity="uncommon",
         slot="helm", stat_bonuses={"intelligence": 19},
         requires_attunement=True, is_magical=True,
         description="INT becomes 19."),
    Item(name="Circlet of Blasting", item_type="helm", uses=1, rarity="uncommon",
         slot="helm", is_magical=True, damage_dice="4d6",
         description="Once per dawn: cast Scorching Ray (3 rays, +5 to hit, 2d6 fire each)."),

    # -- Wands & Staves --
    Item(name="Wand of Magic Missiles", item_type="wand", uses=-1, rarity="uncommon",
         slot="main_hand", is_magical=True, charges=7, max_charges=7,
         description="7 charges. 1 charge = Magic Missile (3 darts, 1d4+1 each). Extra charges for more darts."),
    Item(name="Wand of Fireballs", item_type="wand", uses=-1, rarity="rare",
         slot="main_hand", is_magical=True, charges=7, max_charges=7,
         requires_attunement=True, spell_granted="Fireball",
         description="7 charges. 1 charge = Fireball (8d6). Extra charges increase level."),
    Item(name="Wand of Lightning Bolts", item_type="wand", uses=-1, rarity="rare",
         slot="main_hand", is_magical=True, charges=7, max_charges=7,
         requires_attunement=True, spell_granted="Lightning Bolt",
         description="7 charges. 1 charge = Lightning Bolt (8d6)."),
    Item(name="Staff of Healing", item_type="wand", uses=-1, rarity="rare",
         slot="main_hand", is_magical=True, charges=10, max_charges=10,
         requires_attunement=True,
         heals="2d8+4", spell_granted="Cure Wounds",
         description="10 charges. Cure Wounds (1), Lesser Restoration (2), Mass Cure Wounds (5)."),
    Item(name="Staff of Power", item_type="wand", uses=-1, rarity="very_rare",
         slot="main_hand", is_magical=True, charges=20, max_charges=20,
         requires_attunement=True, weapon_bonus=2, ac_bonus=2,
         save_bonuses={"all": 2},
         description="+2 weapon/AC/saves. 20 charges for various spells."),

    # -- Misc Combat Items --
    Item(name="Bag of Holding", item_type="misc", uses=-1, rarity="uncommon",
         is_magical=True,
         description="Holds up to 500 lb in extradimensional space."),
    Item(name="Immovable Rod", item_type="misc", uses=-1, rarity="uncommon",
         is_magical=True,
         description="Button: rod stays fixed in place. Holds up to 8000 lb."),
    Item(name="Rope of Entanglement", item_type="misc", uses=-1, rarity="rare",
         is_magical=True, applies_condition="Restrained",
         description="Bonus action: entangle creature within 20 ft. DC 20 STR or escape DC 20."),
    Item(name="Necklace of Fireballs", item_type="misc", uses=6, rarity="rare",
         is_magical=True, damage_dice="8d6",
         description="Detach a bead and throw 60 ft. 5d6 fire, 20 ft radius. Extra beads add 1d6."),
    Item(name="Bead of Force", item_type="misc", uses=1, rarity="rare",
         is_magical=True, damage_dice="5d4",
         description="Throw 60 ft. 5d4 force damage. DC 15 DEX or trapped in sphere."),
    Item(name="Dust of Disappearance", item_type="misc", uses=1, rarity="uncommon",
         is_magical=True, buff="invisible",
         description="Throw in air: all within 10 ft invisible for 2d4 minutes."),

    # -- Ioun Stones --
    Item(name="Ioun Stone of Protection", item_type="wondrous", uses=-1, rarity="rare",
         requires_attunement=True, is_magical=True,
         ac_bonus=1, description="+1 AC."),
    Item(name="Ioun Stone of Greater Absorption", item_type="wondrous", uses=-1, rarity="legendary",
         requires_attunement=True, is_magical=True,
         description="Cancel spells of 8th level or lower targeting only you."),

    # -- Eyes / Goggles --
    Item(name="Eyes of the Eagle", item_type="wondrous", uses=-1, rarity="uncommon",
         requires_attunement=True, is_magical=True,
         skill_bonuses={"Perception": 5},
         description="Advantage on Perception checks that rely on sight."),
    Item(name="Goggles of Night", item_type="wondrous", uses=-1, rarity="uncommon",
         is_magical=True, description="Darkvision 60 ft."),
]

# ============================================================================
# MUNDANE ADVENTURING GEAR (PHB p.148-153)
# ============================================================================

_adventuring_gear = [
    Item(name="Healer's Kit", item_type="misc", uses=10, rarity="common",
         description="10 uses. Stabilize a creature at 0 HP without Medicine check."),
    Item(name="Alchemist's Fire", item_type="misc", uses=1, rarity="common",
         damage_dice="1d4", description="Ranged attack (20 ft). 1d4 fire/turn until DC 10 DEX to extinguish."),
    Item(name="Holy Water", item_type="misc", uses=1, rarity="common",
         damage_dice="2d6",
         description="Ranged attack (20 ft). 2d6 radiant to fiends and undead."),
    Item(name="Acid Vial", item_type="misc", uses=1, rarity="common",
         damage_dice="2d6",
         description="Ranged attack (20 ft). 2d6 acid damage."),
    Item(name="Ball Bearings", item_type="misc", uses=1, rarity="common",
         description="Cover 10x10 ft. Creatures entering: DC 10 DEX or fall Prone."),
    Item(name="Caltrops", item_type="misc", uses=1, rarity="common",
         damage_dice="1",
         description="Cover 5x5 ft. Entering: 1 piercing, DC 15 DEX or stop + movement 0."),
    Item(name="Net", item_type="weapon", uses=-1, rarity="common",
         slot="main_hand", weapon_range=5, weapon_long_range=15,
         weapon_category="simple_ranged", applies_condition="Restrained",
         description="Restrained on hit. DC 10 STR or cut with 5 slashing to escape."),
    Item(name="Torch", item_type="misc", uses=-1, rarity="common",
         damage_dice="1", description="Improvised weapon: 1 fire damage. Light 20/40 ft."),
    Item(name="Manacles", item_type="misc", uses=-1, rarity="common",
         applies_condition="Restrained",
         description="Restrain a creature. DC 20 STR or DC 15 DEX (thieves' tools) to escape."),
    Item(name="Oil Flask", item_type="misc", uses=1, rarity="common",
         damage_dice="5", description="Splash 5 ft. If ignited: 5 fire damage for 2 rounds."),
]


# ============================================================================
# MASTER REGISTRY & LOOKUP
# ============================================================================

_all_items: dict = {}  # name -> Item (built lazily)


def _build_registry():
    """Build the item lookup dictionary from all category lists."""
    global _all_items
    if _all_items:
        return
    for item_list in [_potions, _scrolls, _weapons, _armor, _wondrous, _adventuring_gear]:
        for item in item_list:
            _all_items[item.name.lower()] = item


def get_item(name: str, **overrides) -> Item:
    """Get a copy of an item by exact name (case-insensitive).
    Optional keyword overrides are applied to the copy.

    Usage:
        potion = get_item("Potion of Healing")
        magic_sword = get_item("+1 Longsword", equipped=True, attuned=True)
    """
    _build_registry()
    template = _all_items.get(name.lower())
    if template is None:
        raise KeyError(f"Item not found: '{name}'. Use search_items() to find items.")
    item = copy.deepcopy(template)
    for k, v in overrides.items():
        if hasattr(item, k):
            setattr(item, k, v)
    return item


def search_items(query: str, item_type: str = "", rarity: str = "") -> List[Item]:
    """Search items by name substring (case-insensitive).
    Optionally filter by item_type and/or rarity.

    Usage:
        search_items("healing")          -> all healing potions
        search_items("fire")             -> fire-related items
        search_items("", item_type="potion")  -> all potions
        search_items("plate", rarity="rare")  -> rare plate armor
    """
    _build_registry()
    query_lower = query.lower()
    results = []
    for item in _all_items.values():
        if query_lower and query_lower not in item.name.lower() and query_lower not in item.description.lower():
            continue
        if item_type and item.item_type != item_type:
            continue
        if rarity and item.rarity != rarity:
            continue
        results.append(copy.deepcopy(item))
    results.sort(key=lambda i: i.name)
    return results


def get_items_by_type(item_type: str) -> List[Item]:
    """Get all items of a specific type.
    Types: potion, scroll, weapon, armor, shield, cloak, ring, amulet,
           boots, gloves, belt, helm, wand, wondrous, misc
    """
    return search_items("", item_type=item_type)


def get_items_by_rarity(rarity: str) -> List[Item]:
    """Get all items of a specific rarity.
    Rarities: common, uncommon, rare, very_rare, legendary, artifact
    """
    return search_items("", rarity=rarity)


def get_all_item_names() -> List[str]:
    """Get sorted list of all item names."""
    _build_registry()
    return sorted(item.name for item in _all_items.values())


def get_starter_kit(character_class: str) -> List[Item]:
    """Get a starter equipment kit for a class (Level 1-4 tier).
    Returns items already marked as equipped where appropriate.
    """
    kits = {
        "Barbarian": [
            get_item("Greataxe", equipped=True, slot="main_hand"),
            get_item("Javelin"),
            get_item("Potion of Healing"),
            get_item("Potion of Healing"),
        ],
        "Fighter": [
            get_item("Longsword", equipped=True, slot="main_hand"),
            get_item("Shield", equipped=True, slot="off_hand"),
            get_item("Chain Mail", equipped=True, slot="armor"),
            get_item("Heavy Crossbow"),
            get_item("Potion of Healing"),
            get_item("Potion of Healing"),
        ],
        "Paladin": [
            get_item("Longsword", equipped=True, slot="main_hand"),
            get_item("Shield", equipped=True, slot="off_hand"),
            get_item("Chain Mail", equipped=True, slot="armor"),
            get_item("Javelin"),
            get_item("Potion of Healing"),
            get_item("Potion of Healing"),
            get_item("Holy Water"),
        ],
        "Ranger": [
            get_item("Longbow", equipped=True, slot="main_hand"),
            get_item("Shortsword"),
            get_item("Studded Leather Armor", equipped=True, slot="armor"),
            get_item("Potion of Healing"),
            get_item("Potion of Healing"),
        ],
        "Rogue": [
            get_item("Rapier", equipped=True, slot="main_hand"),
            get_item("Dagger"),
            get_item("Studded Leather Armor", equipped=True, slot="armor"),
            get_item("Potion of Healing"),
            get_item("Potion of Healing"),
            get_item("Ball Bearings"),
            get_item("Caltrops"),
        ],
        "Wizard": [
            get_item("Quarterstaff", equipped=True, slot="main_hand"),
            get_item("Potion of Healing"),
            get_item("Potion of Healing"),
            get_item("Scroll of Shield"),
        ],
        "Sorcerer": [
            get_item("Dagger", equipped=True, slot="main_hand"),
            get_item("Potion of Healing"),
            get_item("Potion of Healing"),
            get_item("Scroll of Shield"),
        ],
        "Warlock": [
            get_item("Quarterstaff", equipped=True, slot="main_hand"),
            get_item("Studded Leather Armor", equipped=True, slot="armor"),
            get_item("Potion of Healing"),
            get_item("Potion of Healing"),
        ],
        "Cleric": [
            get_item("Mace", equipped=True, slot="main_hand"),
            get_item("Shield", equipped=True, slot="off_hand"),
            get_item("Chain Mail", equipped=True, slot="armor"),
            get_item("Potion of Healing"),
            get_item("Potion of Healing"),
            get_item("Holy Water"),
        ],
        "Bard": [
            get_item("Rapier", equipped=True, slot="main_hand"),
            get_item("Studded Leather Armor", equipped=True, slot="armor"),
            get_item("Dagger"),
            get_item("Potion of Healing"),
            get_item("Potion of Healing"),
        ],
        "Druid": [
            get_item("Quarterstaff", equipped=True, slot="main_hand"),
            get_item("Leather Armor", equipped=True, slot="armor"),
            get_item("Shield", equipped=True, slot="off_hand"),
            get_item("Potion of Healing"),
            get_item("Potion of Healing"),
        ],
        "Monk": [
            get_item("Quarterstaff", equipped=True, slot="main_hand"),
            get_item("Dagger"),
            get_item("Potion of Healing"),
            get_item("Potion of Healing"),
        ],
    }
    return kits.get(character_class, [get_item("Potion of Healing"), get_item("Potion of Healing")])


def get_hero_items(character_class: str, level: int) -> List[Item]:
    """Get appropriate items for a pre-built hero at a given level tier.

    Level 10 = Tier 2 (uncommon + some rare magic items, greater healing)
    Level 15 = Tier 3 (rare + some very rare, superior healing)
    Level 20 = Tier 4 (very rare + legendary, supreme healing)
    """
    items = []

    # Healing potions scale with tier
    if level <= 10:
        items.extend([get_item("Potion of Greater Healing") for _ in range(3)])
        items.append(get_item("Potion of Healing"))
    elif level <= 15:
        items.extend([get_item("Potion of Superior Healing") for _ in range(3)])
        items.append(get_item("Potion of Greater Healing"))
    else:
        items.extend([get_item("Potion of Supreme Healing") for _ in range(3)])
        items.append(get_item("Potion of Superior Healing"))

    # Resistance potions (everyone gets some)
    items.append(get_item("Potion of Fire Resistance"))

    # Class-specific loadouts
    if character_class == "Barbarian":
        if level <= 10:
            items.append(get_item("+1 Greataxe", equipped=True, slot="main_hand"))
            items.append(get_item("Javelin"))
            items.append(get_item("Gauntlets of Ogre Power", equipped=True, slot="gloves"))
        elif level <= 15:
            items.append(get_item("Flame Tongue Greatsword", equipped=True, slot="main_hand", attuned=True))
            items.append(get_item("Javelin"))
            items.append(get_item("Belt of Hill Giant Strength", equipped=True, slot="belt", attuned=True))
            items.append(get_item("Cloak of Protection", equipped=True, slot="cloak", attuned=True))
        else:
            items.append(get_item("Flame Tongue Greatsword", equipped=True, slot="main_hand", attuned=True))
            items.append(get_item("Belt of Fire Giant Strength", equipped=True, slot="belt", attuned=True))
            items.append(get_item("Cloak of Protection", equipped=True, slot="cloak", attuned=True))
            items.append(get_item("Potion of Speed"))

    elif character_class == "Fighter":
        if level <= 10:
            items.append(get_item("+1 Longsword", equipped=True, slot="main_hand"))
            items.append(get_item("+1 Shield", equipped=True, slot="off_hand"))
            items.append(get_item("+1 Plate Armor", equipped=True, slot="armor"))
            items.append(get_item("Heavy Crossbow"))
        elif level <= 15:
            items.append(get_item("+2 Longsword", equipped=True, slot="main_hand"))
            items.append(get_item("+1 Shield", equipped=True, slot="off_hand"))
            items.append(get_item("+1 Plate Armor", equipped=True, slot="armor"))
            items.append(get_item("Cloak of Protection", equipped=True, slot="cloak", attuned=True))
            items.append(get_item("Ring of Protection", equipped=True, slot="ring1", attuned=True))
            items.append(get_item("Heavy Crossbow"))
        else:
            items.append(get_item("+3 Longsword", equipped=True, slot="main_hand"))
            items.append(get_item("+2 Shield", equipped=True, slot="off_hand"))
            items.append(get_item("+2 Plate Armor", equipped=True, slot="armor"))
            items.append(get_item("Cloak of Protection", equipped=True, slot="cloak", attuned=True))
            items.append(get_item("Potion of Speed"))

    elif character_class == "Paladin":
        if level <= 10:
            items.append(get_item("+1 Longsword", equipped=True, slot="main_hand"))
            items.append(get_item("+1 Shield", equipped=True, slot="off_hand"))
            items.append(get_item("+1 Plate Armor", equipped=True, slot="armor"))
            items.append(get_item("Javelin"))
            items.append(get_item("Holy Water"))
        elif level <= 15:
            items.append(get_item("Sun Blade", equipped=True, slot="main_hand", attuned=True))
            items.append(get_item("+1 Shield", equipped=True, slot="off_hand"))
            items.append(get_item("+1 Plate Armor", equipped=True, slot="armor"))
            items.append(get_item("Amulet of Health", equipped=True, slot="amulet", attuned=True))
            items.append(get_item("Holy Water"))
        else:
            items.append(get_item("Sun Blade", equipped=True, slot="main_hand", attuned=True))
            items.append(get_item("+2 Shield", equipped=True, slot="off_hand"))
            items.append(get_item("+2 Plate Armor", equipped=True, slot="armor"))
            items.append(get_item("Amulet of Health", equipped=True, slot="amulet", attuned=True))
            items.append(get_item("Potion of Speed"))

    elif character_class == "Ranger":
        if level <= 10:
            items.append(get_item("+1 Longbow", equipped=True, slot="main_hand"))
            items.append(get_item("+1 Studded Leather", equipped=True, slot="armor"))
            items.append(get_item("Shortsword"))
            items.append(get_item("Cloak of Protection", equipped=True, slot="cloak", attuned=True))
        elif level <= 15:
            items.append(get_item("+2 Longbow", equipped=True, slot="main_hand"))
            items.append(get_item("+2 Studded Leather", equipped=True, slot="armor"))
            items.append(get_item("Shortsword"))
            items.append(get_item("Cloak of Protection", equipped=True, slot="cloak", attuned=True))
            items.append(get_item("Boots of Speed", equipped=True, slot="boots", attuned=True))
            items.append(get_item("Ring of Protection", equipped=True, slot="ring1", attuned=True))
        else:
            items.append(get_item("+2 Longbow", equipped=True, slot="main_hand"))
            items.append(get_item("+2 Studded Leather", equipped=True, slot="armor"))
            items.append(get_item("Cloak of Protection", equipped=True, slot="cloak", attuned=True))
            items.append(get_item("Boots of Speed", equipped=True, slot="boots", attuned=True))
            items.append(get_item("Ring of Protection", equipped=True, slot="ring1", attuned=True))
            items.append(get_item("Potion of Speed"))

    elif character_class == "Rogue":
        if level <= 10:
            items.append(get_item("+1 Rapier", equipped=True, slot="main_hand"))
            items.append(get_item("+1 Studded Leather", equipped=True, slot="armor"))
            items.append(get_item("Dagger"))
            items.append(get_item("Boots of Elvenkind", equipped=True, slot="boots"))
            items.append(get_item("Caltrops"))
            items.append(get_item("Ball Bearings"))
        elif level <= 15:
            items.append(get_item("+2 Rapier", equipped=True, slot="main_hand"))
            items.append(get_item("+2 Studded Leather", equipped=True, slot="armor"))
            items.append(get_item("Dagger"))
            items.append(get_item("Cloak of Displacement", equipped=True, slot="cloak", attuned=True))
            items.append(get_item("Boots of Speed", equipped=True, slot="boots", attuned=True))
            items.append(get_item("Ring of Free Action", equipped=True, slot="ring1", attuned=True))
        else:
            items.append(get_item("+2 Rapier", equipped=True, slot="main_hand"))
            items.append(get_item("+2 Studded Leather", equipped=True, slot="armor"))
            items.append(get_item("Cloak of Displacement", equipped=True, slot="cloak", attuned=True))
            items.append(get_item("Boots of Speed", equipped=True, slot="boots", attuned=True))
            items.append(get_item("Ring of Evasion", equipped=True, slot="ring1", attuned=True))
            items.append(get_item("Potion of Invisibility"))

    elif character_class == "Wizard":
        if level <= 10:
            items.append(get_item("Quarterstaff", equipped=True, slot="main_hand"))
            items.append(get_item("Cloak of Protection", equipped=True, slot="cloak", attuned=True))
            items.append(get_item("Scroll of Counterspell"))
            items.append(get_item("Scroll of Shield"))
            items.append(get_item("Wand of Magic Missiles"))
        elif level <= 15:
            items.append(get_item("Staff of Power", equipped=True, slot="main_hand", attuned=True))
            items.append(get_item("Cloak of Protection", equipped=True, slot="cloak", attuned=True))
            items.append(get_item("Ring of Protection", equipped=True, slot="ring1", attuned=True))
            items.append(get_item("Scroll of Counterspell"))
            items.append(get_item("Scroll of Wall of Force"))
        else:
            items.append(get_item("Staff of Power", equipped=True, slot="main_hand", attuned=True))
            items.append(get_item("Cloak of Protection", equipped=True, slot="cloak", attuned=True))
            items.append(get_item("Ring of Protection", equipped=True, slot="ring1", attuned=True))
            items.append(get_item("Scroll of Counterspell"))
            items.append(get_item("Potion of Speed"))
            items.append(get_item("Ioun Stone of Protection", attuned=True))

    elif character_class == "Cleric":
        if level <= 10:
            items.append(get_item("+1 Warhammer", equipped=True, slot="main_hand"))
            items.append(get_item("+1 Shield", equipped=True, slot="off_hand"))
            items.append(get_item("+1 Chain Mail", equipped=True, slot="armor"))
            items.append(get_item("Holy Water"))
            items.append(get_item("Periapt of Wound Closure", equipped=True, slot="amulet"))
        elif level <= 15:
            items.append(get_item("+1 Warhammer", equipped=True, slot="main_hand"))
            items.append(get_item("+1 Shield", equipped=True, slot="off_hand"))
            items.append(get_item("+1 Plate Armor", equipped=True, slot="armor"))
            items.append(get_item("Amulet of Health", equipped=True, slot="amulet", attuned=True))
            items.append(get_item("Cloak of Protection", equipped=True, slot="cloak", attuned=True))
            items.append(get_item("Staff of Healing"))
        else:
            items.append(get_item("+1 Warhammer", equipped=True, slot="main_hand"))
            items.append(get_item("+2 Shield", equipped=True, slot="off_hand"))
            items.append(get_item("+2 Plate Armor", equipped=True, slot="armor"))
            items.append(get_item("Amulet of Health", equipped=True, slot="amulet", attuned=True))
            items.append(get_item("Cloak of Protection", equipped=True, slot="cloak", attuned=True))
            items.append(get_item("Staff of Healing", attuned=True))

    elif character_class == "Warlock":
        if level <= 10:
            items.append(get_item("Quarterstaff", equipped=True, slot="main_hand"))
            items.append(get_item("+1 Studded Leather", equipped=True, slot="armor"))
            items.append(get_item("Cloak of Protection", equipped=True, slot="cloak", attuned=True))
            items.append(get_item("Scroll of Counterspell"))
        elif level <= 15:
            items.append(get_item("Quarterstaff", equipped=True, slot="main_hand"))
            items.append(get_item("+2 Studded Leather", equipped=True, slot="armor"))
            items.append(get_item("Cloak of Protection", equipped=True, slot="cloak", attuned=True))
            items.append(get_item("Ring of Protection", equipped=True, slot="ring1", attuned=True))
            items.append(get_item("Boots of Speed", equipped=True, slot="boots", attuned=True))
        else:
            items.append(get_item("Quarterstaff", equipped=True, slot="main_hand"))
            items.append(get_item("+2 Studded Leather", equipped=True, slot="armor"))
            items.append(get_item("Cloak of Protection", equipped=True, slot="cloak", attuned=True))
            items.append(get_item("Ring of Protection", equipped=True, slot="ring1", attuned=True))
            items.append(get_item("Boots of Speed", equipped=True, slot="boots", attuned=True))
            items.append(get_item("Potion of Speed"))

    elif character_class == "Sorcerer":
        if level <= 10:
            items.append(get_item("Dagger", equipped=True, slot="main_hand"))
            items.append(get_item("Cloak of Protection", equipped=True, slot="cloak", attuned=True))
            items.append(get_item("Scroll of Counterspell"))
            items.append(get_item("Scroll of Shield"))
        elif level <= 15:
            items.append(get_item("Dagger", equipped=True, slot="main_hand"))
            items.append(get_item("Cloak of Protection", equipped=True, slot="cloak", attuned=True))
            items.append(get_item("Ring of Protection", equipped=True, slot="ring1", attuned=True))
            items.append(get_item("Headband of Intellect", equipped=True, slot="helm", attuned=True))
            items.append(get_item("Scroll of Counterspell"))
        else:
            items.append(get_item("Dagger", equipped=True, slot="main_hand"))
            items.append(get_item("Cloak of Protection", equipped=True, slot="cloak", attuned=True))
            items.append(get_item("Ring of Protection", equipped=True, slot="ring1", attuned=True))
            items.append(get_item("Ioun Stone of Protection", attuned=True))
            items.append(get_item("Potion of Speed"))

    elif character_class == "Bard":
        if level <= 10:
            items.append(get_item("+1 Rapier", equipped=True, slot="main_hand"))
            items.append(get_item("+1 Studded Leather", equipped=True, slot="armor"))
            items.append(get_item("Cloak of Protection", equipped=True, slot="cloak", attuned=True))
            items.append(get_item("Scroll of Healing Word"))
        elif level <= 15:
            items.append(get_item("+2 Rapier", equipped=True, slot="main_hand"))
            items.append(get_item("+2 Studded Leather", equipped=True, slot="armor"))
            items.append(get_item("Cloak of Displacement", equipped=True, slot="cloak", attuned=True))
            items.append(get_item("Boots of Elvenkind", equipped=True, slot="boots"))
            items.append(get_item("Ring of Protection", equipped=True, slot="ring1", attuned=True))
        else:
            items.append(get_item("+2 Rapier", equipped=True, slot="main_hand"))
            items.append(get_item("+2 Studded Leather", equipped=True, slot="armor"))
            items.append(get_item("Cloak of Displacement", equipped=True, slot="cloak", attuned=True))
            items.append(get_item("Ring of Protection", equipped=True, slot="ring1", attuned=True))
            items.append(get_item("Boots of Speed", equipped=True, slot="boots", attuned=True))

    elif character_class == "Druid":
        if level <= 10:
            items.append(get_item("Quarterstaff", equipped=True, slot="main_hand"))
            items.append(get_item("Shield", equipped=True, slot="off_hand"))
            items.append(get_item("Leather Armor", equipped=True, slot="armor"))
            items.append(get_item("Cloak of Protection", equipped=True, slot="cloak", attuned=True))
        elif level <= 15:
            items.append(get_item("Quarterstaff", equipped=True, slot="main_hand"))
            items.append(get_item("+1 Shield", equipped=True, slot="off_hand"))
            items.append(get_item("+1 Studded Leather", equipped=True, slot="armor"))
            items.append(get_item("Cloak of Protection", equipped=True, slot="cloak", attuned=True))
            items.append(get_item("Ring of Protection", equipped=True, slot="ring1", attuned=True))
            items.append(get_item("Staff of Healing", attuned=True))
        else:
            items.append(get_item("Quarterstaff", equipped=True, slot="main_hand"))
            items.append(get_item("+2 Shield", equipped=True, slot="off_hand"))
            items.append(get_item("+2 Studded Leather", equipped=True, slot="armor"))
            items.append(get_item("Cloak of Protection", equipped=True, slot="cloak", attuned=True))
            items.append(get_item("Ring of Protection", equipped=True, slot="ring1", attuned=True))
            items.append(get_item("Staff of Healing", attuned=True))

    elif character_class == "Monk":
        if level <= 10:
            items.append(get_item("Quarterstaff", equipped=True, slot="main_hand"))
            items.append(get_item("Dagger"))
            items.append(get_item("Cloak of Protection", equipped=True, slot="cloak", attuned=True))
            items.append(get_item("Boots of Speed", equipped=True, slot="boots", attuned=True))
        elif level <= 15:
            items.append(get_item("Quarterstaff", equipped=True, slot="main_hand"))
            items.append(get_item("Cloak of Protection", equipped=True, slot="cloak", attuned=True))
            items.append(get_item("Boots of Speed", equipped=True, slot="boots", attuned=True))
            items.append(get_item("Ring of Protection", equipped=True, slot="ring1", attuned=True))
            items.append(get_item("Bracers of Defense", equipped=True, slot="gloves", attuned=True)) if False else None  # Not in DB yet
            items.append(get_item("Gauntlets of Ogre Power", equipped=True, slot="gloves", attuned=True))
        else:
            items.append(get_item("Quarterstaff", equipped=True, slot="main_hand"))
            items.append(get_item("Cloak of Protection", equipped=True, slot="cloak", attuned=True))
            items.append(get_item("Boots of Speed", equipped=True, slot="boots", attuned=True))
            items.append(get_item("Ring of Protection", equipped=True, slot="ring1", attuned=True))
            items.append(get_item("Potion of Speed"))

    # Filter out None values (from conditional items)
    items = [i for i in items if i is not None]
    return items
