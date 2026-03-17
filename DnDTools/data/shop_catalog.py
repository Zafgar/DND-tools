"""
D&D 5e 2014 Shop Catalog — Prices, shop types, level-appropriate inventories.

PHB Chapter 5 equipment prices, DMG magic item pricing, shop type definitions,
automatic inventory generation, and price modifier system.

Usage:
    from data.shop_catalog import (get_item_price, get_item_tooltip,
        generate_shop_inventory, SHOP_TYPES, apply_price_modifier)
"""
import random
import copy
from typing import List, Dict, Optional, Tuple


# ============================================================================
# D&D 5e PHB / DMG ITEM PRICES (in gold pieces)
# Sources: PHB p.145-150 (equipment), DMG p.135 (magic items)
# ============================================================================

ITEM_PRICES: Dict[str, float] = {
    # -- Simple Melee Weapons (PHB p.149) --
    "Club": 0.1,
    "Dagger": 2.0,
    "Greatclub": 0.2,
    "Handaxe": 5.0,
    "Javelin": 0.5,
    "Light Hammer": 2.0,
    "Mace": 5.0,
    "Quarterstaff": 0.2,
    "Sickle": 1.0,
    "Spear": 1.0,

    # -- Simple Ranged Weapons (PHB p.149) --
    "Light Crossbow": 25.0,
    "Dart": 0.05,
    "Shortbow": 25.0,
    "Sling": 0.1,

    # -- Martial Melee Weapons (PHB p.149) --
    "Battleaxe": 10.0,
    "Flail": 10.0,
    "Glaive": 20.0,
    "Greataxe": 30.0,
    "Greatsword": 50.0,
    "Halberd": 20.0,
    "Lance": 10.0,
    "Longsword": 15.0,
    "Maul": 10.0,
    "Morningstar": 15.0,
    "Pike": 5.0,
    "Rapier": 25.0,
    "Scimitar": 25.0,
    "Shortsword": 10.0,
    "Trident": 5.0,
    "War Pick": 5.0,
    "Warhammer": 15.0,
    "Whip": 2.0,

    # -- Martial Ranged Weapons (PHB p.149) --
    "Hand Crossbow": 75.0,
    "Heavy Crossbow": 50.0,
    "Longbow": 50.0,

    # -- Ammunition (PHB p.150) --
    "Arrows (20)": 1.0,
    "Bolts (20)": 1.0,
    "Sling Bullets (20)": 0.04,
    "Blowgun Needles (50)": 1.0,

    # -- Light Armor (PHB p.145) --
    "Padded Armor": 5.0,
    "Leather Armor": 10.0,
    "Studded Leather Armor": 45.0,
    "Studded Leather": 45.0,

    # -- Medium Armor (PHB p.145) --
    "Hide Armor": 10.0,
    "Chain Shirt": 50.0,
    "Scale Mail": 50.0,
    "Breastplate": 400.0,
    "Half Plate": 750.0,

    # -- Heavy Armor (PHB p.145) --
    "Ring Mail": 30.0,
    "Chain Mail": 75.0,
    "Splint Armor": 200.0,
    "Plate Armor": 1500.0,

    # -- Shields (PHB p.145) --
    "Shield": 10.0,

    # -- Adventuring Gear (PHB p.150-153) --
    "Healer's Kit": 5.0,
    "Alchemist's Fire": 50.0,
    "Holy Water": 25.0,
    "Acid Vial": 25.0,
    "Ball Bearings": 1.0,
    "Caltrops": 1.0,
    "Net": 1.0,
    "Torch": 0.01,
    "Manacles": 2.0,
    "Oil Flask": 0.1,
    "Rope (50 ft)": 1.0,
    "Grappling Hook": 2.0,
    "Crowbar": 2.0,
    "Hammer": 1.0,
    "Piton (10)": 0.5,
    "Tinderbox": 0.5,
    "Waterskin": 0.2,
    "Bedroll": 1.0,
    "Mess Kit": 0.2,
    "Rations (1 day)": 0.5,
    "Backpack": 2.0,
    "Lantern (Hooded)": 5.0,
    "Lantern (Bullseye)": 10.0,
    "Mirror (Steel)": 5.0,
    "Vial": 1.0,
    "Ink (1 oz)": 10.0,
    "Parchment (1 sheet)": 0.1,
    "Pouch": 0.5,
    "Sack": 0.01,
    "Chest": 5.0,
    "Lock": 10.0,
    "Chain (10 ft)": 5.0,
    "Bell": 1.0,
    "Candle": 0.01,
    "Chalk (1 piece)": 0.01,
    "Component Pouch": 25.0,
    "Spellcasting Focus (Arcane)": 10.0,
    "Spellcasting Focus (Druidic)": 5.0,
    "Holy Symbol": 5.0,
    "Thieves' Tools": 25.0,
    "Herbalism Kit": 5.0,
    "Poisoner's Kit": 50.0,
    "Alchemist's Supplies": 50.0,
    "Smith's Tools": 20.0,
    "Brewer's Supplies": 20.0,
    "Carpenter's Tools": 8.0,
    "Cartographer's Tools": 15.0,
    "Cobbler's Tools": 5.0,
    "Cook's Utensils": 1.0,
    "Glassblower's Tools": 30.0,
    "Jeweler's Tools": 25.0,
    "Leatherworker's Tools": 5.0,
    "Mason's Tools": 10.0,
    "Painter's Supplies": 10.0,
    "Potter's Tools": 10.0,
    "Tinker's Tools": 50.0,
    "Weaver's Tools": 1.0,
    "Woodcarver's Tools": 1.0,
    "Disguise Kit": 25.0,
    "Forgery Kit": 15.0,
    "Navigator's Tools": 25.0,
    "Musical Instrument (Common)": 25.0,
    "Playing Card Set": 0.5,
    "Dice Set": 0.1,
    "Tent (Two-Person)": 2.0,
    "Climber's Kit": 25.0,
    "Fishing Tackle": 1.0,
    "Hunting Trap": 5.0,
    "Magnifying Glass": 100.0,
    "Spyglass": 1000.0,
    "Signal Whistle": 0.05,

    # -- Potions (DMG p.187-188) --
    "Potion of Healing": 50.0,
    "Potion of Greater Healing": 150.0,
    "Potion of Superior Healing": 500.0,
    "Potion of Supreme Healing": 5000.0,
    "Potion of Fire Resistance": 300.0,
    "Potion of Cold Resistance": 300.0,
    "Potion of Lightning Resistance": 300.0,
    "Potion of Acid Resistance": 300.0,
    "Potion of Necrotic Resistance": 300.0,
    "Potion of Poison Resistance": 300.0,
    "Potion of Heroism": 500.0,
    "Potion of Speed": 5000.0,
    "Potion of Invulnerability": 5000.0,
    "Potion of Hill Giant Strength": 300.0,
    "Potion of Frost Giant Strength": 500.0,
    "Potion of Fire Giant Strength": 500.0,
    "Potion of Cloud Giant Strength": 5000.0,
    "Potion of Flying": 5000.0,
    "Potion of Invisibility": 5000.0,
    "Potion of Poison": 100.0,
    "Antitoxin": 50.0,
    "Oil of Sharpness": 5000.0,
    "Potion of Growth": 300.0,
    "Potion of Diminution": 300.0,
    "Potion of Water Breathing": 200.0,
    "Potion of Animal Friendship": 200.0,
    "Potion of Clairvoyance": 500.0,
    "Potion of Vitality": 500.0,
    "Philter of Love": 100.0,
    "Elixir of Health": 500.0,
    "Oil of Etherealness": 10000.0,
    "Oil of Slipperiness": 500.0,
    "Sovereign Glue": 5000.0,
    "Universal Solvent": 5000.0,

    # -- Spell Scrolls (DMG p.200) --
    "Scroll of Shield": 50.0,
    "Scroll of Cure Wounds": 50.0,
    "Scroll of Healing Word": 50.0,
    "Scroll of Bless": 50.0,
    "Scroll of Protection from Evil and Good": 50.0,
    "Scroll of Misty Step": 200.0,
    "Scroll of Lesser Restoration": 200.0,
    "Scroll of Counterspell": 500.0,
    "Scroll of Revivify": 500.0,
    "Scroll of Fireball": 500.0,
    "Scroll of Haste": 500.0,
    "Scroll of Dispel Magic": 500.0,
    "Scroll of Greater Restoration": 2500.0,
    "Scroll of Raise Dead": 2500.0,
    "Scroll of Wall of Force": 2500.0,
    # Generic scroll pricing by spell level (DMG p.200)
    "Spell Scroll (Cantrip)": 25.0,
    "Spell Scroll (1st)": 75.0,
    "Spell Scroll (2nd)": 150.0,
    "Spell Scroll (3rd)": 300.0,
    "Spell Scroll (4th)": 500.0,
    "Spell Scroll (5th)": 1000.0,
    "Spell Scroll (6th)": 2000.0,
    "Spell Scroll (7th)": 5000.0,
    "Spell Scroll (8th)": 10000.0,
    "Spell Scroll (9th)": 25000.0,

    # -- Magic Weapons (DMG p.213) --
    "+1 Longsword": 1000.0,
    "+2 Longsword": 5000.0,
    "+3 Longsword": 25000.0,
    "+1 Greatsword": 1000.0,
    "+1 Rapier": 1000.0,
    "+2 Rapier": 5000.0,
    "+1 Longbow": 1000.0,
    "+2 Longbow": 5000.0,
    "+1 Greataxe": 1000.0,
    "+1 Warhammer": 1000.0,
    "+1 Hand Crossbow": 1000.0,
    "+1 Shortsword": 1000.0,
    "+1 Dagger": 1000.0,
    "Flame Tongue Longsword": 10000.0,
    "Frost Brand Longsword": 10000.0,
    "Flame Tongue Greatsword": 10000.0,
    "Frost Brand Greatsword": 10000.0,
    "Sun Blade": 15000.0,
    "Dragon Slayer Longsword": 5000.0,
    "Vicious Rapier": 2500.0,
    "Javelin of Lightning": 2500.0,
    "Dagger of Venom": 2500.0,
    "Oathbow": 15000.0,
    "Vorpal Sword": 50000.0,
    "Holy Avenger": 50000.0,

    # -- Magic Armor (DMG p.152) --
    "+1 Chain Mail": 1500.0,
    "+1 Plate Armor": 5000.0,
    "+2 Plate Armor": 15000.0,
    "+3 Plate Armor": 50000.0,
    "+1 Studded Leather": 1500.0,
    "+2 Studded Leather": 5000.0,
    "+1 Half Plate": 2500.0,
    "+1 Breastplate": 2500.0,
    "Mithral Half Plate": 2500.0,
    "Mithral Chain Shirt": 1500.0,
    "Adamantine Plate": 5000.0,
    "Dragon Scale Mail": 10000.0,
    "Armor of Resistance": 5000.0,
    "Demon Armor": 10000.0,

    # -- Magic Shields (DMG p.200) --
    "+1 Shield": 1500.0,
    "+2 Shield": 5000.0,
    "+3 Shield": 25000.0,
    "Sentinel Shield": 2500.0,
    "Shield of Missile Attraction": 5000.0,
    "Animated Shield": 10000.0,
    "Spellguard Shield": 15000.0,

    # -- Wondrous Items — Cloaks (DMG p.159) --
    "Cloak of Protection": 3500.0,
    "Cloak of Displacement": 10000.0,
    "Cloak of the Bat": 10000.0,
    "Cloak of Elvenkind": 2500.0,
    "Cloak of Invisibility": 50000.0,
    "Cloak of the Manta Ray": 2500.0,
    "Mantle of Spell Resistance": 15000.0,
    "Cape of the Mountebank": 5000.0,

    # -- Wondrous Items — Rings (DMG p.191-193) --
    "Ring of Protection": 3500.0,
    "Ring of Spell Storing": 10000.0,
    "Ring of Evasion": 10000.0,
    "Ring of Free Action": 10000.0,
    "Ring of Resistance (Fire)": 5000.0,
    "Ring of Resistance (Cold)": 5000.0,
    "Ring of Resistance (Lightning)": 5000.0,
    "Ring of Resistance (Poison)": 5000.0,
    "Ring of Invisibility": 50000.0,
    "Ring of Regeneration": 50000.0,
    "Ring of Spell Turning": 50000.0,
    "Ring of Telekinesis": 25000.0,
    "Ring of Mind Shielding": 5000.0,
    "Ring of Water Walking": 2500.0,
    "Ring of Swimming": 2500.0,
    "Ring of Warmth": 2500.0,
    "Ring of Feather Falling": 2500.0,
    "Ring of Jumping": 2500.0,
    "Ring of Animal Influence": 2500.0,

    # -- Wondrous Items — Amulets & Necklaces (DMG p.150-152) --
    "Amulet of Health": 5000.0,
    "Periapt of Wound Closure": 5000.0,
    "Periapt of Proof Against Poison": 5000.0,
    "Amulet of Proof Against Detection": 5000.0,
    "Necklace of Fireballs": 5000.0,
    "Necklace of Adaptation": 2500.0,
    "Necklace of Prayer Beads": 10000.0,
    "Medallion of Thoughts": 2500.0,
    "Brooch of Shielding": 5000.0,
    "Scarab of Protection": 50000.0,

    # -- Wondrous Items — Boots (DMG p.156) --
    "Boots of Speed": 5000.0,
    "Boots of Elvenkind": 2500.0,
    "Boots of Striding and Springing": 2500.0,
    "Boots of the Winterlands": 2500.0,
    "Boots of Levitation": 5000.0,
    "Winged Boots": 5000.0,
    "Slippers of Spider Climbing": 5000.0,

    # -- Wondrous Items — Gloves & Bracers (DMG p.172) --
    "Gauntlets of Ogre Power": 5000.0,
    "Gloves of Missile Snaring": 5000.0,
    "Gloves of Thievery": 2500.0,
    "Gloves of Swimming and Climbing": 2500.0,
    "Bracers of Defense": 5000.0,
    "Bracers of Archery": 2500.0,

    # -- Wondrous Items — Belts (DMG p.155) --
    "Belt of Hill Giant Strength": 5000.0,
    "Belt of Frost Giant Strength": 10000.0,
    "Belt of Fire Giant Strength": 15000.0,
    "Belt of Stone Giant Strength": 15000.0,
    "Belt of Cloud Giant Strength": 25000.0,
    "Belt of Storm Giant Strength": 50000.0,
    "Belt of Dwarvenkind": 5000.0,

    # -- Wondrous Items — Headwear (DMG p.173-174) --
    "Helm of Brilliance": 15000.0,
    "Headband of Intellect": 5000.0,
    "Circlet of Blasting": 2500.0,
    "Eyes of the Eagle": 2500.0,
    "Goggles of Night": 2500.0,
    "Eyes of Charming": 5000.0,
    "Eyes of Minute Seeing": 2500.0,
    "Hat of Disguise": 2500.0,
    "Helm of Comprehending Languages": 2500.0,
    "Helm of Telepathy": 5000.0,
    "Cap of Water Breathing": 2500.0,

    # -- Wondrous Items — Wands & Staves (DMG p.211-212) --
    "Wand of Magic Missiles": 5000.0,
    "Wand of Fireballs": 15000.0,
    "Wand of Lightning Bolts": 15000.0,
    "Wand of the War Mage +1": 1500.0,
    "Wand of the War Mage +2": 5000.0,
    "Wand of the War Mage +3": 15000.0,
    "Wand of Web": 5000.0,
    "Wand of Fear": 5000.0,
    "Wand of Paralysis": 10000.0,
    "Wand of Polymorph": 15000.0,
    "Wand of Binding": 5000.0,
    "Wand of Enemy Detection": 5000.0,
    "Wand of Magic Detection": 2500.0,
    "Wand of Secrets": 2500.0,
    "Staff of Healing": 10000.0,
    "Staff of Power": 50000.0,
    "Staff of the Magi": 100000.0,
    "Staff of Fire": 15000.0,
    "Staff of Frost": 15000.0,
    "Staff of Striking": 15000.0,
    "Staff of Thunder and Lightning": 15000.0,
    "Staff of Charming": 10000.0,
    "Staff of Swarming Insects": 10000.0,
    "Staff of the Woodlands": 15000.0,
    "Staff of the Python": 5000.0,
    "Staff of Withering": 5000.0,
    "Rod of the Pact Keeper +1": 1500.0,
    "Rod of the Pact Keeper +2": 5000.0,
    "Rod of the Pact Keeper +3": 15000.0,

    # -- Wondrous Items — Miscellaneous (DMG various) --
    "Bag of Holding": 500.0,
    "Immovable Rod": 5000.0,
    "Rope of Entanglement": 5000.0,
    "Bead of Force": 2500.0,
    "Dust of Disappearance": 2500.0,
    "Ioun Stone of Protection": 5000.0,
    "Ioun Stone of Greater Absorption": 15000.0,
    "Ioun Stone of Awareness": 5000.0,
    "Ioun Stone of Fortitude": 5000.0,
    "Ioun Stone of Insight": 5000.0,
    "Ioun Stone of Agility": 5000.0,
    "Ioun Stone of Strength": 5000.0,
    "Portable Hole": 5000.0,
    "Bag of Tricks (Gray)": 500.0,
    "Bag of Tricks (Rust)": 500.0,
    "Bag of Tricks (Tan)": 500.0,
    "Decanter of Endless Water": 2500.0,
    "Deck of Illusions": 2500.0,
    "Eversmoking Bottle": 2500.0,
    "Folding Boat": 5000.0,
    "Horseshoes of Speed": 5000.0,
    "Dimensional Shackles": 5000.0,
    "Iron Bands of Bilarro": 5000.0,
    "Lantern of Revealing": 2500.0,
    "Gem of Seeing": 15000.0,
    "Gem of Brightness": 2500.0,
    "Carpet of Flying (3x5)": 5000.0,
    "Carpet of Flying (4x6)": 10000.0,
    "Figurine of Wondrous Power (Silver Raven)": 500.0,
    "Figurine of Wondrous Power (Bronze Griffon)": 5000.0,
    "Figurine of Wondrous Power (Onyx Dog)": 5000.0,
    "Horn of Blasting": 5000.0,
    "Instrument of the Bards (Doss Lute)": 5000.0,
    "Instrument of the Bards (Canaith Mandolin)": 10000.0,
    "Instrument of the Bards (Cli Lyre)": 15000.0,
    "Wind Fan": 2500.0,
    "Robe of Useful Items": 500.0,
    "Robe of Eyes": 15000.0,
    "Robe of the Archmagi": 50000.0,
    "Robe of Stars": 25000.0,
    "Cube of Force": 15000.0,
    "Crystal Ball": 25000.0,
    "Chime of Opening": 2500.0,
    "Alchemy Jug": 2500.0,
    "Rope of Climbing": 500.0,
    "Sending Stones": 5000.0,

    # -- Mundane Services & Mounts (PHB p.157-159) --
    "Riding Horse": 75.0,
    "Draft Horse": 50.0,
    "Warhorse": 400.0,
    "Pony": 30.0,
    "Mastiff": 25.0,
    "Saddle (Riding)": 10.0,
    "Saddle (Military)": 20.0,
    "Saddle (Exotic)": 60.0,
    "Barding (Chain)": 300.0,
    "Barding (Plate)": 6000.0,
    "Cart": 15.0,
    "Wagon": 35.0,
    "Rowboat": 50.0,
    "Sailing Ship": 10000.0,
}


# ============================================================================
# ITEM TOOLTIPS — hover descriptions for DM reference
# ============================================================================

ITEM_TOOLTIPS: Dict[str, str] = {
    # Potions
    "Potion of Healing": "Regain 2d4+2 HP. Action to drink.",
    "Potion of Greater Healing": "Regain 4d4+4 HP. Action to drink.",
    "Potion of Superior Healing": "Regain 8d4+8 HP. Action to drink.",
    "Potion of Supreme Healing": "Regain 10d4+20 HP. Action to drink.",
    "Potion of Fire Resistance": "Resistance to fire damage for 1 hour.",
    "Potion of Cold Resistance": "Resistance to cold damage for 1 hour.",
    "Potion of Lightning Resistance": "Resistance to lightning damage for 1 hour.",
    "Potion of Acid Resistance": "Resistance to acid damage for 1 hour.",
    "Potion of Necrotic Resistance": "Resistance to necrotic damage for 1 hour.",
    "Potion of Poison Resistance": "Resistance to poison damage for 1 hour.",
    "Potion of Heroism": "10 temp HP + Bless (no concentration) for 1 hour.",
    "Potion of Speed": "Haste effect for 1 minute. No concentration required.",
    "Potion of Invulnerability": "Resistance to ALL damage for 1 minute.",
    "Potion of Hill Giant Strength": "STR becomes 21 for 1 hour. No effect if STR already 21+.",
    "Potion of Frost Giant Strength": "STR becomes 23 for 1 hour.",
    "Potion of Fire Giant Strength": "STR becomes 25 for 1 hour.",
    "Potion of Cloud Giant Strength": "STR becomes 27 for 1 hour.",
    "Potion of Flying": "Flying speed equal to walking speed for 1 hour.",
    "Potion of Invisibility": "Invisible for 1 hour. Ends if you attack or cast a spell.",
    "Potion of Poison": "Appears to be another potion. DC 13 CON save or 3d6 poison + poisoned 24h.",
    "Potion of Growth": "Enlarge effect for 1d4 hours. Adv on STR checks, +1d4 weapon damage.",
    "Potion of Diminution": "Reduce effect for 1d4 hours. Disadv on STR checks, -1d4 weapon damage.",
    "Potion of Water Breathing": "Breathe underwater for 1 hour.",
    "Potion of Animal Friendship": "Cast Animal Friendship (DC 13) for 1 hour.",
    "Potion of Clairvoyance": "Cast Clairvoyance. No concentration.",
    "Potion of Vitality": "Remove exhaustion, cure disease/poison, max HP on hit dice for 24h.",
    "Antitoxin": "Advantage on saves vs. poison for 1 hour.",
    "Oil of Sharpness": "Coat weapon: +3 to attack and damage for 1 hour.",
    "Oil of Etherealness": "Ethereal Plane for 1 hour. Visible as ghostly form.",
    "Oil of Slipperiness": "Freedom of Movement effect for 8 hours, or coat 10ft area.",

    # Scrolls
    "Scroll of Shield": "Reaction: +5 AC until start of next turn, blocks Magic Missile.",
    "Scroll of Cure Wounds": "Touch: heal 1d8 + spellcasting mod HP.",
    "Scroll of Healing Word": "Bonus action, 60ft: heal 1d4 + spellcasting mod HP.",
    "Scroll of Bless": "Up to 3 creatures add 1d4 to attacks and saves. Concentration.",
    "Scroll of Misty Step": "Bonus action teleport 30 ft to visible space.",
    "Scroll of Lesser Restoration": "End one disease or condition (blind/deaf/paralyzed/poisoned).",
    "Scroll of Counterspell": "Reaction: auto-counter spell level 3 or lower. Higher: DC 10 + spell level.",
    "Scroll of Revivify": "Touch creature dead <1 min: return to 1 HP. 300gp diamonds consumed.",
    "Scroll of Fireball": "150ft, 20ft sphere: 8d6 fire, DEX save half.",
    "Scroll of Haste": "Double speed, +2 AC, extra action. Concentration 1 min. Lethargy after.",
    "Scroll of Dispel Magic": "End spells level 3 or lower. Higher: DC 10 + spell level.",
    "Scroll of Greater Restoration": "End one: reduce ability, petrified, curse, attunement, HP max reduce.",
    "Scroll of Raise Dead": "Dead <10 days returns to 1 HP. -4 penalty to rolls, removed by long rests.",
    "Scroll of Wall of Force": "Invisible wall, immune to all damage. Concentration 10 min.",

    # Magic Weapons
    "+1 Longsword": "+1 to attack and damage rolls. Uncommon, requires attunement.",
    "+2 Longsword": "+2 to attack and damage rolls. Rare, requires attunement.",
    "+3 Longsword": "+3 to attack and damage rolls. Very Rare, requires attunement.",
    "Flame Tongue Longsword": "Command word: 2d6 extra fire damage. Bright light 40ft, dim 40ft more.",
    "Frost Brand Longsword": "1d6 extra cold. Fire resistance while held. Extinguish flames 30ft.",
    "Flame Tongue Greatsword": "Command word: 2d6 extra fire damage. Bright light 40ft, dim 40ft more.",
    "Sun Blade": "Radiant damage, +2 to attack/damage. Finesse. 1d8/1d10 + extra vs undead.",
    "Dragon Slayer Longsword": "+1 weapon. +3d6 extra damage against dragons.",
    "Vicious Rapier": "On nat 20: extra 2d6 damage of the weapon's type.",
    "Javelin of Lightning": "Throw: 4d6 lightning to all in 120ft line. DEX save half. 1/dawn.",
    "Dagger of Venom": "+1 dagger. 1/day: coat with poison, 2d10 poison + poisoned 1 min.",
    "Oathbow": "Sworn Enemy: adv on attacks, +3d6 damage. Disadv with other weapons. 1/dawn.",
    "Vorpal Sword": "+3. Nat 20 vs creature with head: decapitate (instant kill). Ignores resistance.",
    "Holy Avenger": "+3 weapon. +2d10 radiant vs fiends/undead. 10ft aura: adv on saves vs spells.",

    # Magic Armor
    "+1 Chain Mail": "+1 AC (total AC 17). Requires attunement.",
    "+1 Plate Armor": "+1 AC (total AC 19). Requires attunement.",
    "+2 Plate Armor": "+2 AC (total AC 20). Requires attunement.",
    "+3 Plate Armor": "+3 AC (total AC 21). Requires attunement.",
    "Mithral Half Plate": "No stealth disadvantage. Medium armor, AC 15 + DEX (max 2).",
    "Mithral Chain Shirt": "No stealth disadvantage. Medium armor, AC 13 + DEX (max 2).",
    "Adamantine Plate": "Critical hits become normal hits. AC 18.",
    "Dragon Scale Mail": "+1 AC, adv on saves vs dragon breath, resistance to one damage type.",
    "Armor of Resistance": "Resistance to one damage type. Requires attunement.",
    "Animated Shield": "Bonus action: shield floats, +2 AC, free hands. Lasts 1 min.",
    "Spellguard Shield": "Adv on saves vs spells. Spell attacks have disadv against you.",
    "Sentinel Shield": "Adv on initiative and Perception checks.",

    # Wondrous — Cloaks
    "Cloak of Protection": "+1 AC and +1 to all saving throws. Requires attunement.",
    "Cloak of Displacement": "Attacks have disadvantage vs you. Ends when hit, resets on your turn.",
    "Cloak of the Bat": "Adv on Stealth. Fly 40ft in dim/dark. Can polymorph into bat.",
    "Cloak of Elvenkind": "Adv on Stealth checks. Disadv on Perception checks to see you.",
    "Cloak of Invisibility": "Invisible while wearing hood. 2 hours total, recharges after 12h rest.",
    "Mantle of Spell Resistance": "Advantage on saving throws against spells.",

    # Wondrous — Rings
    "Ring of Protection": "+1 AC and +1 to all saving throws. Requires attunement.",
    "Ring of Spell Storing": "Store up to 5 levels of spells. Anyone can cast stored spells.",
    "Ring of Evasion": "Reaction: auto-succeed DEX save. 3 charges, regain 1d3 at dawn.",
    "Ring of Free Action": "Difficult terrain costs no extra movement. Can't be paralyzed/restrained.",
    "Ring of Invisibility": "Action: invisible until you attack/cast. Requires attunement.",

    # Wondrous — Boots
    "Boots of Speed": "Bonus action: double speed, +2 AC vs opportunity attacks. 10 min/day.",
    "Boots of Elvenkind": "Advantage on Stealth checks (silent movement).",
    "Boots of Striding and Springing": "Speed becomes 30ft min. Triple jump distance.",
    "Winged Boots": "Flying speed equal to walking speed. 4 hours, recharges after 12h rest.",

    # Wondrous — Gloves & Bracers
    "Gauntlets of Ogre Power": "STR becomes 19. No effect if STR already 19+.",
    "Gloves of Missile Snaring": "Reaction: reduce ranged weapon damage by 1d10 + DEX. 0 = catch.",
    "Gloves of Thievery": "+5 to Sleight of Hand, +5 to lockpicking. Invisible while worn.",
    "Bracers of Defense": "+2 AC when wearing no armor and not using a shield.",
    "Bracers of Archery": "+2 damage with ranged attacks using longbow/shortbow. Proficiency.",

    # Wondrous — Belts
    "Belt of Hill Giant Strength": "STR becomes 21. Requires attunement.",
    "Belt of Frost Giant Strength": "STR becomes 23. Requires attunement.",
    "Belt of Fire Giant Strength": "STR becomes 25. Requires attunement.",
    "Belt of Stone Giant Strength": "STR becomes 23. Requires attunement.",
    "Belt of Cloud Giant Strength": "STR becomes 27. Requires attunement.",
    "Belt of Storm Giant Strength": "STR becomes 29. Requires attunement.",
    "Belt of Dwarvenkind": "+2 CON. Darkvision 60ft. Adv vs poison. Grow beard.",

    # Wondrous — Head
    "Helm of Brilliance": "Fire/daylight/prismatic spray/wall of fire. Gems power abilities.",
    "Headband of Intellect": "INT becomes 19. Requires attunement.",
    "Circlet of Blasting": "Scorching Ray 1/day (3 rays, +5, 2d6 fire each).",
    "Eyes of the Eagle": "Advantage on Perception checks that rely on sight. See 1 mile clearly.",
    "Goggles of Night": "Darkvision 60ft (or extend existing by 60ft).",
    "Hat of Disguise": "Cast Disguise Self at will. Requires attunement.",

    # Wondrous — Wands & Staves
    "Wand of Magic Missiles": "7 charges. Spend 1+ charges: Magic Missile (3 darts + 1/extra charge).",
    "Wand of Fireballs": "7 charges. Spend 1+ charges: Fireball (8d6 + 1d6/extra charge).",
    "Wand of Lightning Bolts": "7 charges. Spend 1+ charges: Lightning Bolt (8d6 + 1d6/extra).",
    "Staff of Healing": "10 charges. Cure Wounds(1), Lesser Restoration(2), Mass Cure Wounds(5).",
    "Staff of Power": "+2 attack/damage/spell DC. 20 charges. Fireball, hold monster, etc. Retributive Strike.",
    "Staff of the Magi": "+2 spell attack. Absorb spells. 50 charges. Legendary artifact.",

    # Wondrous — Misc
    "Bag of Holding": "Interior: 64 cubic ft, 500 lbs. Always weighs 15 lbs. Breathing: 10 min.",
    "Immovable Rod": "Button: fix in place. Holds 8000 lbs. DC 30 STR to move.",
    "Rope of Entanglement": "Command: restrain creature within 20ft. DC 20 STR/DEX to escape.",
    "Bead of Force": "Throw 60ft: 5d4 force in 10ft sphere. Failed DC 15 DEX: trapped in sphere 1min.",
    "Necklace of Fireballs": "Detach beads and throw: Fireball 8d6 per bead. DEX save.",

    # Mundane Gear
    "Healer's Kit": "10 uses. Stabilize dying creature without Medicine check.",
    "Alchemist's Fire": "Throw 20ft: 1d4 fire/turn. DC 10 DEX to extinguish. Action.",
    "Holy Water": "Throw 20ft: 2d6 radiant to fiend/undead. DEX to hit.",
    "Acid Vial": "Throw 20ft: 2d6 acid damage. DEX to hit.",
    "Thieves' Tools": "Required for picking locks and disarming traps. DEX check.",
    "Herbalism Kit": "Create antitoxin and potions of healing with proficiency.",
    "Poisoner's Kit": "Create and apply poisons with proficiency.",
    "Component Pouch": "Contains material components for spells (non-costly).",
}


# ============================================================================
# MAGIC ITEM RARITY PRICE RANGES (DMG p.135)
# ============================================================================

RARITY_PRICE_RANGE: Dict[str, Tuple[float, float]] = {
    "common": (50, 100),
    "uncommon": (100, 500),
    "rare": (500, 5000),
    "very_rare": (5000, 50000),
    "legendary": (50000, 500000),
    "artifact": (500000, 1000000),
}


# ============================================================================
# SHOP TYPES — category definitions with level-appropriate inventories
# ============================================================================

SHOP_TYPES: Dict[str, dict] = {
    "general_store": {
        "name": "General Store",
        "description": "Basic supplies, adventuring gear, and common consumables.",
        "icon": "GS",
        "item_categories": ["gear", "tool", "supply"],
        "base_items": [
            "Torch", "Rope (50 ft)", "Backpack", "Bedroll", "Rations (1 day)",
            "Waterskin", "Tinderbox", "Pouch", "Sack", "Candle", "Chalk (1 piece)",
            "Oil Flask", "Tent (Two-Person)", "Mess Kit", "Fishing Tackle",
            "Lantern (Hooded)", "Mirror (Steel)", "Bell", "Crowbar",
            "Grappling Hook", "Piton (10)", "Chest", "Lock", "Chain (10 ft)",
            "Signal Whistle", "Ink (1 oz)", "Parchment (1 sheet)", "Vial",
            "Healer's Kit", "Dice Set", "Playing Card Set",
        ],
        "level_items": {
            # Tier 1 (1-4): basic supplies
            1: [],
            # Tier 2 (5-10): better supplies
            5: ["Climber's Kit", "Magnifying Glass", "Spyglass",
                "Hunting Trap", "Manacles", "Antitoxin"],
            # Tier 3 (11-16): some uncommon items
            11: ["Bag of Holding", "Rope of Climbing",
                 "Robe of Useful Items", "Alchemy Jug"],
            # Tier 4 (17-20): rare mundane+
            17: ["Chime of Opening", "Lantern of Revealing",
                 "Decanter of Endless Water"],
        },
    },

    "blacksmith": {
        "name": "Blacksmith / Armorer",
        "description": "Weapons, armor, shields. May carry +1 items at higher tiers.",
        "icon": "BS",
        "item_categories": ["weapon", "armor", "shield"],
        "base_items": [
            # Simple weapons
            "Dagger", "Handaxe", "Javelin", "Mace", "Quarterstaff", "Spear",
            # Martial weapons
            "Longsword", "Shortsword", "Greatsword", "Battleaxe", "Warhammer",
            "Rapier", "Scimitar", "Greataxe", "Halberd", "Maul",
            # Ranged
            "Shortbow", "Longbow", "Light Crossbow", "Heavy Crossbow",
            "Arrows (20)", "Bolts (20)",
            # Armor
            "Leather Armor", "Studded Leather Armor", "Chain Shirt",
            "Scale Mail", "Chain Mail", "Shield",
        ],
        "level_items": {
            1: [],
            5: ["Breastplate", "Half Plate", "Splint Armor",
                "Hand Crossbow", "Glaive", "Pike", "Flail", "Morningstar",
                "Lance", "Trident", "War Pick", "Whip"],
            9: ["Plate Armor",
                "+1 Longsword", "+1 Shortsword", "+1 Dagger",
                "+1 Chain Mail", "+1 Shield"],
            13: ["+1 Greatsword", "+1 Greataxe", "+1 Warhammer",
                 "+1 Rapier", "+1 Longbow", "+1 Hand Crossbow",
                 "+1 Plate Armor", "+1 Studded Leather",
                 "+1 Half Plate", "+1 Breastplate",
                 "Mithral Chain Shirt", "Mithral Half Plate"],
            17: ["+2 Longsword", "+2 Rapier", "+2 Longbow",
                 "+2 Plate Armor", "+2 Studded Leather",
                 "Adamantine Plate", "+2 Shield"],
        },
    },

    "magic_shop": {
        "name": "Arcane Emporium",
        "description": "Magic items, wondrous items, and enchanted equipment.",
        "icon": "ME",
        "item_categories": ["wondrous", "magic_weapon", "magic_armor"],
        "base_items": [
            "Component Pouch", "Spellcasting Focus (Arcane)",
            "Ink (1 oz)", "Parchment (1 sheet)", "Vial",
            "Spell Scroll (Cantrip)", "Spell Scroll (1st)",
        ],
        "level_items": {
            1: ["Scroll of Shield", "Scroll of Cure Wounds",
                "Scroll of Healing Word", "Scroll of Bless",
                "Scroll of Protection from Evil and Good"],
            5: ["Bag of Holding", "Cloak of Protection",
                "Ring of Protection", "Goggles of Night",
                "Eyes of the Eagle", "Hat of Disguise",
                "Wand of Magic Detection", "Wand of Secrets",
                "Boots of Elvenkind", "Cloak of Elvenkind",
                "Circlet of Blasting", "Gloves of Thievery",
                "Scroll of Misty Step", "Scroll of Lesser Restoration",
                "Spell Scroll (2nd)", "Spell Scroll (3rd)",
                "Wand of the War Mage +1", "Rod of the Pact Keeper +1",
                "Gem of Brightness", "Wind Fan",
                "Ring of Water Walking", "Ring of Warmth",
                "Ring of Feather Falling", "Ring of Jumping",
                "Medallion of Thoughts", "Necklace of Adaptation",
                "Bracers of Archery", "Sending Stones"],
            9: ["Cloak of Displacement", "Boots of Speed", "Winged Boots",
                "Gauntlets of Ogre Power", "Headband of Intellect",
                "Amulet of Health", "Belt of Hill Giant Strength",
                "Bracers of Defense", "Gloves of Missile Snaring",
                "Ring of Evasion", "Ring of Free Action",
                "Ring of Spell Storing", "Wand of Magic Missiles",
                "Brooch of Shielding", "Periapt of Wound Closure",
                "Scroll of Counterspell", "Scroll of Fireball",
                "Scroll of Haste", "Scroll of Revivify",
                "Spell Scroll (4th)", "Spell Scroll (5th)",
                "Wand of the War Mage +2", "Rod of the Pact Keeper +2",
                "Necklace of Fireballs", "Amulet of Proof Against Detection",
                "Ring of Mind Shielding", "Cape of the Mountebank",
                "Figurine of Wondrous Power (Bronze Griffon)",
                "Horn of Blasting", "Immovable Rod",
                "Instrument of the Bards (Doss Lute)",
                "Bead of Force", "Dust of Disappearance"],
            13: ["Mantle of Spell Resistance", "Belt of Frost Giant Strength",
                 "Belt of Fire Giant Strength", "Helm of Brilliance",
                 "Wand of Fireballs", "Wand of Lightning Bolts",
                 "Wand of Polymorph", "Wand of Paralysis",
                 "Staff of Healing", "Staff of Fire", "Staff of Frost",
                 "Staff of Striking",
                 "Cloak of the Bat", "Ring of Telekinesis",
                 "Scroll of Greater Restoration", "Scroll of Raise Dead",
                 "Spell Scroll (6th)", "Spell Scroll (7th)",
                 "Wand of the War Mage +3", "Rod of the Pact Keeper +3",
                 "Ioun Stone of Protection", "Ioun Stone of Awareness",
                 "Robe of Eyes", "Gem of Seeing", "Cube of Force",
                 "Instrument of the Bards (Canaith Mandolin)",
                 "Dragon Scale Mail", "Animated Shield"],
            17: ["Staff of Power", "Staff of the Magi",
                 "Cloak of Invisibility", "Ring of Invisibility",
                 "Ring of Regeneration", "Ring of Spell Turning",
                 "Belt of Cloud Giant Strength", "Belt of Storm Giant Strength",
                 "Scarab of Protection", "Robe of the Archmagi",
                 "Robe of Stars", "Crystal Ball",
                 "Spell Scroll (8th)", "Spell Scroll (9th)",
                 "Carpet of Flying (3x5)", "Carpet of Flying (4x6)"],
        },
    },

    "potion_shop": {
        "name": "Apothecary / Potion Shop",
        "description": "Potions, salves, oils, and herbal remedies.",
        "icon": "AP",
        "item_categories": ["potion", "oil"],
        "base_items": [
            "Potion of Healing", "Antitoxin", "Healer's Kit",
            "Herbalism Kit", "Alchemist's Fire", "Acid Vial",
            "Holy Water", "Oil Flask", "Vial",
        ],
        "level_items": {
            1: [],
            5: ["Potion of Greater Healing",
                "Potion of Fire Resistance", "Potion of Cold Resistance",
                "Potion of Lightning Resistance", "Potion of Acid Resistance",
                "Potion of Poison Resistance", "Potion of Necrotic Resistance",
                "Potion of Water Breathing", "Potion of Animal Friendship",
                "Potion of Growth", "Potion of Diminution",
                "Philter of Love", "Potion of Poison",
                "Potion of Hill Giant Strength", "Poisoner's Kit"],
            9: ["Potion of Superior Healing",
                "Potion of Heroism", "Potion of Clairvoyance",
                "Potion of Vitality", "Elixir of Health",
                "Oil of Slipperiness",
                "Potion of Frost Giant Strength",
                "Potion of Fire Giant Strength"],
            13: ["Potion of Supreme Healing", "Potion of Speed",
                 "Potion of Invulnerability", "Potion of Flying",
                 "Potion of Invisibility",
                 "Potion of Cloud Giant Strength",
                 "Oil of Sharpness"],
            17: ["Oil of Etherealness",
                 "Sovereign Glue", "Universal Solvent"],
        },
    },

    "temple": {
        "name": "Temple / Shrine",
        "description": "Divine items, holy symbols, healing, and protective items.",
        "icon": "TM",
        "item_categories": ["divine", "healing"],
        "base_items": [
            "Holy Symbol", "Holy Water", "Healer's Kit",
            "Potion of Healing", "Candle", "Scroll of Cure Wounds",
            "Scroll of Healing Word", "Scroll of Bless",
            "Scroll of Protection from Evil and Good",
        ],
        "level_items": {
            1: [],
            5: ["Potion of Greater Healing",
                "Scroll of Lesser Restoration",
                "Periapt of Wound Closure",
                "Necklace of Prayer Beads",
                "Ring of Warmth"],
            9: ["Potion of Superior Healing",
                "Scroll of Revivify",
                "Scroll of Dispel Magic",
                "Periapt of Proof Against Poison",
                "Amulet of Proof Against Detection",
                "Staff of Healing",
                "Ring of Free Action",
                "Cloak of Protection"],
            13: ["Scroll of Greater Restoration",
                 "Scroll of Raise Dead",
                 "Mace of Disruption",
                 "Potion of Vitality", "Elixir of Health"],
            17: ["Holy Avenger", "Robe of Stars"],
        },
    },

    "stables": {
        "name": "Stables / Animal Handler",
        "description": "Mounts, barding, and related equipment.",
        "icon": "ST",
        "item_categories": ["mount", "barding"],
        "base_items": [
            "Riding Horse", "Pony", "Draft Horse", "Mastiff",
            "Saddle (Riding)", "Saddle (Military)", "Saddle (Exotic)",
            "Cart", "Wagon",
        ],
        "level_items": {
            1: [],
            5: ["Warhorse", "Barding (Chain)"],
            9: ["Barding (Plate)", "Horseshoes of Speed"],
            13: ["Figurine of Wondrous Power (Bronze Griffon)"],
            17: [],
        },
    },

    "tavern": {
        "name": "Tavern / Inn",
        "description": "Food, drink, lodging, rumors, and small goods.",
        "icon": "TV",
        "item_categories": ["food", "drink"],
        "base_items": [
            "Rations (1 day)", "Waterskin", "Dice Set",
            "Playing Card Set", "Torch",
        ],
        "level_items": {
            1: [],
            5: ["Potion of Healing"],
            9: [],
            13: [],
            17: [],
        },
    },

    "thieves_guild": {
        "name": "Black Market / Fence",
        "description": "Shady goods, poisons, thieves' tools, and hard-to-find items.",
        "icon": "BM",
        "item_categories": ["rogue", "poison", "contraband"],
        "base_items": [
            "Thieves' Tools", "Dagger", "Disguise Kit",
            "Poisoner's Kit", "Forgery Kit", "Manacles",
            "Crowbar", "Caltrops", "Ball Bearings",
            "Potion of Poison", "Hand Crossbow",
        ],
        "level_items": {
            1: [],
            5: ["Gloves of Thievery", "Cloak of Elvenkind",
                "Boots of Elvenkind", "Hat of Disguise",
                "+1 Dagger", "+1 Shortsword", "+1 Hand Crossbow"],
            9: ["Cloak of Displacement", "Ring of Mind Shielding",
                "Dagger of Venom", "Dust of Disappearance",
                "Cape of the Mountebank", "Dimensional Shackles",
                "Ring of Evasion"],
            13: ["Cloak of the Bat", "Ring of Invisibility",
                 "Cloak of Invisibility",
                 "Vicious Rapier", "Oathbow"],
            17: ["Vorpal Sword"],
        },
    },

    "scribe": {
        "name": "Scribe / Bookshop",
        "description": "Scrolls, books, maps, writing supplies, and arcane knowledge.",
        "icon": "SC",
        "item_categories": ["scroll", "book", "writing"],
        "base_items": [
            "Ink (1 oz)", "Parchment (1 sheet)", "Vial",
            "Spell Scroll (Cantrip)", "Spell Scroll (1st)",
            "Scroll of Shield", "Scroll of Cure Wounds",
            "Scroll of Healing Word", "Scroll of Bless",
            "Cartographer's Tools",
        ],
        "level_items": {
            1: [],
            5: ["Scroll of Misty Step", "Scroll of Lesser Restoration",
                "Scroll of Protection from Evil and Good",
                "Spell Scroll (2nd)", "Spell Scroll (3rd)",
                "Eyes of Minute Seeing",
                "Helm of Comprehending Languages"],
            9: ["Scroll of Counterspell", "Scroll of Fireball",
                "Scroll of Haste", "Scroll of Revivify",
                "Scroll of Dispel Magic",
                "Spell Scroll (4th)", "Spell Scroll (5th)"],
            13: ["Scroll of Greater Restoration", "Scroll of Raise Dead",
                 "Scroll of Wall of Force",
                 "Spell Scroll (6th)", "Spell Scroll (7th)"],
            17: ["Spell Scroll (8th)", "Spell Scroll (9th)"],
        },
    },
}


# ============================================================================
# PRICE MODIFIER SYSTEM
# ============================================================================

PRICE_MODIFIERS: Dict[str, float] = {
    "very_cheap": 0.5,     # 50% of base price — fire sale, desperation
    "cheap": 0.75,         # 75% — friendly, bulk, competition
    "normal": 1.0,         # 100% — standard PHB price
    "expensive": 1.5,      # 150% — remote, monopoly, rare demand
    "very_expensive": 2.0, # 200% — only source, wartime, exotic location
    "ripoff": 3.0,         # 300% — tourist trap, desperate buyer
}


def apply_price_modifier(base_price: float, modifier: str) -> float:
    """Apply a price modifier to a base price."""
    mult = PRICE_MODIFIERS.get(modifier, 1.0)
    return round(base_price * mult, 1)


def get_item_price(item_name: str) -> float:
    """Get the base PHB/DMG price for an item. Returns 0 if unknown."""
    return ITEM_PRICES.get(item_name, 0.0)


def get_item_tooltip(item_name: str) -> str:
    """Get hover tooltip text for an item."""
    tip = ITEM_TOOLTIPS.get(item_name, "")
    if tip:
        price = get_item_price(item_name)
        if price > 0:
            if price >= 1:
                tip += f" [{price:,.0f} gp]"
            else:
                tip += f" [{price * 10:.0f} sp]"
    return tip


def get_price_display(price_gp: float) -> str:
    """Format price for display: gp, sp, or cp."""
    if price_gp <= 0:
        return "—"
    if price_gp >= 1:
        return f"{price_gp:,.0f} gp"
    sp = price_gp * 10
    if sp >= 1:
        return f"{sp:,.0f} sp"
    cp = price_gp * 100
    return f"{cp:,.0f} cp"


# ============================================================================
# SHOP INVENTORY GENERATION
# ============================================================================

def generate_shop_inventory(
    shop_type: str,
    party_level: int = 1,
    price_modifier: str = "normal",
    max_items: int = 0,
) -> List[Dict]:
    """
    Generate a level-appropriate shop inventory.

    Returns list of dicts: {name, base_price, adjusted_price, tooltip, rarity_hint}
    """
    shop = SHOP_TYPES.get(shop_type)
    if not shop:
        return []

    items = list(shop["base_items"])

    # Add level-appropriate items
    for threshold, level_items in sorted(shop.get("level_items", {}).items()):
        if party_level >= threshold:
            items.extend(level_items)

    # Deduplicate preserving order
    seen = set()
    unique = []
    for name in items:
        if name not in seen:
            seen.add(name)
            unique.append(name)
    items = unique

    # Build inventory entries
    inventory = []
    for name in items:
        base_price = get_item_price(name)
        adj_price = apply_price_modifier(base_price, price_modifier)
        rarity = _guess_rarity(name, base_price)
        inventory.append({
            "name": name,
            "base_price": base_price,
            "adjusted_price": adj_price,
            "price_display": get_price_display(adj_price),
            "tooltip": get_item_tooltip(name),
            "rarity": rarity,
        })

    if max_items > 0 and len(inventory) > max_items:
        # Keep base items, randomly select from extras
        base_count = len(shop["base_items"])
        base = inventory[:base_count]
        extras = inventory[base_count:]
        random.shuffle(extras)
        inventory = base + extras[:max(0, max_items - base_count)]

    return inventory


def suggest_items_for_shop(
    shop_type: str,
    party_level: int = 1,
    count: int = 5,
) -> List[Dict]:
    """
    Suggest additional items that could be added to a shop.
    Returns items NOT in the shop's default inventory but appropriate
    for the level and shop type.
    """
    shop = SHOP_TYPES.get(shop_type)
    if not shop:
        return []

    # Collect all items already in this shop type
    existing = set(shop["base_items"])
    for items in shop.get("level_items", {}).values():
        existing.update(items)

    # Build candidates from price list based on level
    max_price = _level_to_max_price(party_level)
    candidates = []
    for name, price in ITEM_PRICES.items():
        if name in existing:
            continue
        if price > max_price:
            continue
        if price <= 0:
            continue
        # Check category relevance
        if _item_fits_shop(name, shop_type):
            candidates.append({
                "name": name,
                "base_price": price,
                "price_display": get_price_display(price),
                "tooltip": get_item_tooltip(name),
                "rarity": _guess_rarity(name, price),
            })

    random.shuffle(candidates)
    return candidates[:count]


def get_all_shop_types() -> List[Dict]:
    """Get list of all shop types with name and description."""
    return [
        {"key": k, "name": v["name"], "description": v["description"], "icon": v["icon"]}
        for k, v in SHOP_TYPES.items()
    ]


# ============================================================================
# INTERNAL HELPERS
# ============================================================================

def _guess_rarity(name: str, price: float) -> str:
    """Estimate rarity from price."""
    if price <= 100:
        return "common"
    if price <= 500:
        return "uncommon"
    if price <= 5000:
        return "rare"
    if price <= 50000:
        return "very_rare"
    return "legendary"


def _level_to_max_price(level: int) -> float:
    """Max item price affordable/appropriate at this level."""
    if level <= 4:
        return 500       # Tier 1: uncommon max
    if level <= 10:
        return 5000      # Tier 2: rare max
    if level <= 16:
        return 50000     # Tier 3: very rare max
    return 500000        # Tier 4: legendary


def _item_fits_shop(item_name: str, shop_type: str) -> bool:
    """Rough check if an item thematically fits a shop type."""
    name_lower = item_name.lower()

    if shop_type == "general_store":
        # Mundane gear
        return (not name_lower.startswith("+") and
                "scroll" not in name_lower and
                "potion" not in name_lower and
                "wand" not in name_lower and
                "staff" not in name_lower and
                "ring of" not in name_lower and
                "cloak of" not in name_lower and
                "belt of" not in name_lower and
                "flame" not in name_lower and
                "frost brand" not in name_lower)

    if shop_type == "blacksmith":
        weapon_words = ["sword", "axe", "hammer", "dagger", "bow", "crossbow",
                        "mace", "flail", "spear", "javelin", "halberd", "glaive",
                        "pike", "rapier", "scimitar", "maul", "whip", "lance",
                        "trident", "arrows", "bolts"]
        armor_words = ["armor", "plate", "mail", "leather", "shield", "breastplate",
                       "half plate", "mithral", "adamantine"]
        return any(w in name_lower for w in weapon_words + armor_words)

    if shop_type == "magic_shop":
        magic_words = ["ring of", "cloak of", "boots of", "belt of", "gauntlets",
                       "bracers", "amulet", "wand of", "staff of", "rod of",
                       "ioun", "helm of", "headband", "circlet", "eyes of",
                       "goggles", "cape", "mantle", "robe of", "necklace",
                       "periapt", "brooch", "hat of", "gem of", "figurine",
                       "horn of", "instrument", "carpet", "cube", "crystal",
                       "scroll", "spell scroll"]
        return (any(w in name_lower for w in magic_words) or
                name_lower.startswith("+"))

    if shop_type == "potion_shop":
        return ("potion" in name_lower or "oil " in name_lower or
                "antitoxin" in name_lower or "elixir" in name_lower or
                "philter" in name_lower or "sovereign" in name_lower or
                "universal" in name_lower or
                "healer" in name_lower or "herbalism" in name_lower or
                "poisoner" in name_lower or "alchemist" in name_lower or
                "acid" in name_lower or "holy water" in name_lower)

    if shop_type == "temple":
        divine_words = ["holy", "healing", "cure", "restoration", "bless",
                        "protection", "raise", "revivify", "periapt",
                        "amulet", "prayer", "potion of healing"]
        return any(w in name_lower for w in divine_words)

    if shop_type == "stables":
        return ("horse" in name_lower or "pony" in name_lower or
                "saddle" in name_lower or "barding" in name_lower or
                "cart" in name_lower or "wagon" in name_lower or
                "mastiff" in name_lower or "horseshoes" in name_lower or
                "figurine" in name_lower)

    if shop_type == "thieves_guild":
        rogue_words = ["dagger", "thieves", "disguise", "forgery", "poison",
                       "cloak of", "boots of elven", "gloves of thiev",
                       "hand crossbow", "vicious", "hat of disguise",
                       "ring of mind", "ring of invis", "cloak of invis",
                       "cloak of disp", "cape of", "dust", "dimensional",
                       "ring of evasion", "manacles", "caltrops",
                       "ball bearings", "crowbar"]
        return any(w in name_lower for w in rogue_words)

    if shop_type == "scribe":
        return ("scroll" in name_lower or "spell scroll" in name_lower or
                "ink" in name_lower or "parchment" in name_lower or
                "cartographer" in name_lower or "eyes of minute" in name_lower or
                "helm of comprehend" in name_lower)

    return False
