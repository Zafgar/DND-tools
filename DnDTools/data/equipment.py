"""
D&D 5e 2014 Equipment Database (PHB Ch.5)
Weapons, Armor, Shields, and Magic Items with full mechanical stats.
"""
from data.models import Item


# ============================================================
# PHB Weapons (p.149)
# ============================================================

def _weapon(name, dice, dmg_type, properties=None, range_=5, long_range=0,
            category="simple_melee", bonus=0, magical=False, extra_dice="",
            extra_type="", rarity="common", attune=False, desc="", slot="main_hand"):
    props = properties or []
    return Item(
        name=name, item_type="weapon", uses=-1, description=desc,
        equipped=False, slot=slot, rarity=rarity,
        requires_attunement=attune, is_magical=magical,
        weapon_damage_dice=dice, weapon_damage_type=dmg_type,
        weapon_properties=props, weapon_range=range_, weapon_long_range=long_range,
        weapon_bonus=bonus, weapon_category=category,
        extra_damage_dice=extra_dice, extra_damage_type=extra_type,
    )


def _armor(name, base_ac, category, max_dex=-1, stealth_disadv=False,
           str_req=0, bonus=0, magical=False, rarity="common", attune=False,
           desc="", resistances=None, immunities=None, cond_immunities=None,
           save_bonuses=None):
    return Item(
        name=name, item_type="armor", uses=-1, description=desc,
        equipped=False, slot="armor", rarity=rarity,
        requires_attunement=attune, is_magical=magical,
        base_ac=base_ac, ac_bonus=bonus, max_dex_bonus=max_dex,
        armor_category=category, stealth_disadvantage=stealth_disadv,
        strength_required=str_req,
        damage_resistances=resistances or [],
        damage_immunities=immunities or [],
        condition_immunities=cond_immunities or [],
        save_bonuses=save_bonuses or {},
    )


def _shield(name, bonus=2, magical=False, rarity="common", attune=False, desc="",
            ac_extra=0, save_bonuses=None):
    return Item(
        name=name, item_type="shield", uses=-1, description=desc,
        equipped=False, slot="off_hand", rarity=rarity,
        requires_attunement=attune, is_magical=magical,
        armor_category="shield", ac_bonus=bonus + ac_extra,
        save_bonuses=save_bonuses or {},
    )


# ---- Simple Melee Weapons ----
CLUB = _weapon("Club", "1d4", "bludgeoning", ["light"], category="simple_melee")
DAGGER = _weapon("Dagger", "1d4", "piercing", ["finesse", "light", "thrown"],
                 range_=20, long_range=60, category="simple_melee")
GREATCLUB = _weapon("Greatclub", "1d8", "bludgeoning", ["two-handed"], category="simple_melee")
HANDAXE = _weapon("Handaxe", "1d6", "slashing", ["light", "thrown"],
                  range_=20, long_range=60, category="simple_melee")
JAVELIN = _weapon("Javelin", "1d6", "piercing", ["thrown"],
                  range_=30, long_range=120, category="simple_melee")
LIGHT_HAMMER = _weapon("Light Hammer", "1d4", "bludgeoning", ["light", "thrown"],
                       range_=20, long_range=60, category="simple_melee")
MACE = _weapon("Mace", "1d6", "bludgeoning", category="simple_melee")
QUARTERSTAFF = _weapon("Quarterstaff", "1d6", "bludgeoning", ["versatile"], category="simple_melee")
SICKLE = _weapon("Sickle", "1d4", "slashing", ["light"], category="simple_melee")
SPEAR = _weapon("Spear", "1d6", "piercing", ["thrown", "versatile"],
                range_=20, long_range=60, category="simple_melee")

# ---- Simple Ranged Weapons ----
LIGHT_CROSSBOW = _weapon("Light Crossbow", "1d8", "piercing", ["loading", "two-handed"],
                         range_=80, long_range=320, category="simple_ranged")
DART = _weapon("Dart", "1d4", "piercing", ["finesse", "thrown"],
               range_=20, long_range=60, category="simple_ranged")
SHORTBOW = _weapon("Shortbow", "1d6", "piercing", ["two-handed"],
                   range_=80, long_range=320, category="simple_ranged")
SLING = _weapon("Sling", "1d4", "bludgeoning", [],
                range_=30, long_range=120, category="simple_ranged")

# ---- Martial Melee Weapons ----
BATTLEAXE = _weapon("Battleaxe", "1d8", "slashing", ["versatile"], category="martial_melee")
FLAIL = _weapon("Flail", "1d8", "bludgeoning", category="martial_melee")
GLAIVE = _weapon("Glaive", "1d10", "slashing", ["heavy", "reach", "two-handed"],
                 range_=10, category="martial_melee")
GREATAXE = _weapon("Greataxe", "1d12", "slashing", ["heavy", "two-handed"], category="martial_melee")
GREATSWORD = _weapon("Greatsword", "2d6", "slashing", ["heavy", "two-handed"], category="martial_melee")
HALBERD = _weapon("Halberd", "1d10", "slashing", ["heavy", "reach", "two-handed"],
                  range_=10, category="martial_melee")
LANCE = _weapon("Lance", "1d12", "piercing", ["reach"], range_=10, category="martial_melee")
LONGSWORD = _weapon("Longsword", "1d8", "slashing", ["versatile"], category="martial_melee")
MAUL = _weapon("Maul", "2d6", "bludgeoning", ["heavy", "two-handed"], category="martial_melee")
MORNINGSTAR = _weapon("Morningstar", "1d8", "piercing", category="martial_melee")
PIKE = _weapon("Pike", "1d10", "piercing", ["heavy", "reach", "two-handed"],
               range_=10, category="martial_melee")
RAPIER = _weapon("Rapier", "1d8", "piercing", ["finesse"], category="martial_melee")
SCIMITAR = _weapon("Scimitar", "1d6", "slashing", ["finesse", "light"], category="martial_melee")
SHORTSWORD = _weapon("Shortsword", "1d6", "piercing", ["finesse", "light"], category="martial_melee")
TRIDENT = _weapon("Trident", "1d6", "piercing", ["thrown", "versatile"],
                  range_=20, long_range=60, category="martial_melee")
WAR_PICK = _weapon("War Pick", "1d8", "piercing", category="martial_melee")
WARHAMMER = _weapon("Warhammer", "1d8", "bludgeoning", ["versatile"], category="martial_melee")
WHIP = _weapon("Whip", "1d4", "slashing", ["finesse", "reach"], range_=10, category="martial_melee")

# ---- Martial Ranged Weapons ----
HAND_CROSSBOW = _weapon("Hand Crossbow", "1d6", "piercing", ["light", "loading"],
                        range_=30, long_range=120, category="martial_ranged")
HEAVY_CROSSBOW = _weapon("Heavy Crossbow", "1d10", "piercing", ["heavy", "loading", "two-handed"],
                         range_=100, long_range=400, category="martial_ranged")
LONGBOW = _weapon("Longbow", "1d8", "piercing", ["heavy", "two-handed"],
                  range_=150, long_range=600, category="martial_ranged")


# ============================================================
# PHB Armor (p.145)
# ============================================================

# ---- Light Armor ----
PADDED_ARMOR = _armor("Padded Armor", 11, "light", max_dex=-1, stealth_disadv=True)
LEATHER_ARMOR = _armor("Leather Armor", 11, "light")
STUDDED_LEATHER = _armor("Studded Leather", 12, "light")

# ---- Medium Armor ----
HIDE_ARMOR = _armor("Hide Armor", 12, "medium", max_dex=2)
CHAIN_SHIRT = _armor("Chain Shirt", 13, "medium", max_dex=2)
SCALE_MAIL = _armor("Scale Mail", 14, "medium", max_dex=2, stealth_disadv=True)
BREASTPLATE = _armor("Breastplate", 14, "medium", max_dex=2)
HALF_PLATE = _armor("Half Plate", 15, "medium", max_dex=2, stealth_disadv=True)

# ---- Heavy Armor ----
RING_MAIL = _armor("Ring Mail", 14, "heavy", max_dex=0, stealth_disadv=True)
CHAIN_MAIL = _armor("Chain Mail", 16, "heavy", max_dex=0, stealth_disadv=True, str_req=13)
SPLINT_ARMOR = _armor("Splint Armor", 17, "heavy", max_dex=0, stealth_disadv=True, str_req=15)
PLATE_ARMOR = _armor("Plate Armor", 18, "heavy", max_dex=0, stealth_disadv=True, str_req=15)

# ---- Shields ----
SHIELD = _shield("Shield")


# ============================================================
# Magic Weapons (DMG)
# ============================================================

def magic_weapon(base_name, bonus, base_item=None):
    """Create a +1/+2/+3 version of a weapon."""
    if base_item is None:
        base_item = WEAPON_DB.get(base_name)
        if not base_item:
            return None
    import copy
    w = copy.deepcopy(base_item)
    w.name = f"{base_name} +{bonus}"
    w.weapon_bonus = bonus
    w.is_magical = True
    w.rarity = {1: "uncommon", 2: "rare", 3: "very_rare"}.get(bonus, "uncommon")
    return w


def magic_armor(base_name, bonus, base_item=None):
    """Create a +1/+2/+3 version of armor."""
    if base_item is None:
        base_item = ARMOR_DB.get(base_name)
        if not base_item:
            return None
    import copy
    a = copy.deepcopy(base_item)
    a.name = f"{base_name} +{bonus}"
    a.ac_bonus = bonus
    a.is_magical = True
    a.rarity = {1: "uncommon", 2: "rare", 3: "very_rare"}.get(bonus, "uncommon")
    return a


# ---- Named Magic Weapons ----
FLAME_TONGUE_LONGSWORD = _weapon(
    "Flame Tongue Longsword", "1d8", "slashing", ["versatile"],
    category="martial_melee", bonus=0, magical=True,
    extra_dice="2d6", extra_type="fire", rarity="rare", attune=True,
    desc="While attuned, you can ignite the blade (bonus action). Deals +2d6 fire damage.")

FROST_BRAND_GREATSWORD = _weapon(
    "Frost Brand Greatsword", "2d6", "slashing", ["heavy", "two-handed"],
    category="martial_melee", bonus=0, magical=True,
    extra_dice="1d6", extra_type="cold", rarity="very_rare", attune=True,
    desc="Deals +1d6 cold damage. Resistance to fire damage while attuned.")

SUNBLADE = _weapon(
    "Sun Blade", "1d8", "radiant", ["finesse", "versatile"],
    category="martial_melee", bonus=2, magical=True,
    rarity="rare", attune=True,
    desc="+2 weapon. Deals radiant damage. +2d6 vs undead.")

VICIOUS_RAPIER = _weapon(
    "Vicious Rapier", "1d8", "piercing", ["finesse"],
    category="martial_melee", bonus=0, magical=True,
    rarity="rare", desc="When you roll a 20 on attack, deal +7 damage.")

JAVELIN_OF_LIGHTNING = _weapon(
    "Javelin of Lightning", "1d6", "piercing", ["thrown"],
    range_=30, long_range=120, category="simple_melee", magical=True,
    rarity="uncommon", desc="Transform into lightning bolt (4d6 lightning, DEX save DC 13).")

DAGGER_OF_VENOM = _weapon(
    "Dagger of Venom", "1d4", "piercing", ["finesse", "light", "thrown"],
    range_=20, long_range=60, category="simple_melee", bonus=1, magical=True,
    rarity="rare", desc="+1. Once/day coat with poison: +2d10 poison, DC 15 CON or Poisoned 1 min.")

OATHBOW = _weapon(
    "Oathbow", "1d8", "piercing", ["heavy", "two-handed"],
    range_=150, long_range=600, category="martial_ranged", magical=True,
    extra_dice="3d6", extra_type="piercing", rarity="very_rare", attune=True,
    desc="Sworn enemy takes +3d6. Advantage on attacks vs sworn enemy.")

VORPAL_SWORD = _weapon(
    "Vorpal Sword", "2d6", "slashing", ["heavy", "two-handed"],
    category="martial_melee", bonus=3, magical=True,
    rarity="legendary", attune=True,
    desc="+3. On natural 20: decapitate (if creature has head and <200 HP).")

HOLY_AVENGER = _weapon(
    "Holy Avenger", "2d6", "slashing", ["heavy", "two-handed"],
    category="martial_melee", bonus=3, magical=True,
    extra_dice="2d10", extra_type="radiant", rarity="legendary", attune=True,
    desc="+3. +2d10 radiant vs fiends/undead. 10ft aura: allies +save bonus = CHA mod.")

# ---- Named Magic Armor ----
MITHRAL_CHAIN_SHIRT = _armor(
    "Mithral Chain Shirt", 13, "medium", max_dex=2, stealth_disadv=False,
    magical=True, rarity="uncommon", desc="No Stealth disadvantage. No STR requirement.")

ADAMANTINE_PLATE = _armor(
    "Adamantine Plate", 18, "heavy", max_dex=0, stealth_disadv=True, str_req=15,
    magical=True, rarity="uncommon", desc="Critical hits become normal hits.")

DRAGON_SCALE_MAIL = _armor(
    "Dragon Scale Mail", 14, "medium", max_dex=2, stealth_disadv=True,
    bonus=1, magical=True, rarity="very_rare", attune=True,
    resistances=["fire"],
    desc="+1. Advantage on saves vs dragon breath. Resistance to one damage type.")

ARMOR_OF_RESISTANCE = _armor(
    "Armor of Resistance", 16, "heavy", max_dex=0, stealth_disadv=True, str_req=13,
    magical=True, rarity="rare", attune=True,
    resistances=["fire"],
    desc="Resistance to one damage type (specified at creation).")

SHIELD_PLUS_1 = _shield("Shield +1", bonus=2, magical=True, rarity="uncommon", ac_extra=1)
SHIELD_PLUS_2 = _shield("Shield +2", bonus=2, magical=True, rarity="rare", ac_extra=2)
SHIELD_PLUS_3 = _shield("Shield +3", bonus=2, magical=True, rarity="very_rare", ac_extra=3)
ANIMATED_SHIELD = _shield(
    "Animated Shield", bonus=2, magical=True, rarity="very_rare", attune=True,
    desc="Bonus action: flies and protects you. Frees your hand.")
SPELLGUARD_SHIELD = _shield(
    "Spellguard Shield", bonus=2, magical=True, rarity="very_rare", attune=True,
    save_bonuses={"spell": 99},  # advantage on saves vs spells
    desc="Advantage on saves vs spells. Spell attacks have disadvantage against you.")


# ============================================================
# Wondrous Items & Accessories
# ============================================================

def _wondrous(name, slot, rarity="uncommon", attune=False, desc="",
              ac_bonus=0, stat_bonuses=None, save_bonuses=None, skill_bonuses=None,
              resistances=None, immunities=None, cond_immunities=None,
              speed_bonus=0, charges=0, max_charges=0, spell_granted=""):
    return Item(
        name=name, item_type="wondrous", uses=-1, description=desc,
        equipped=False, slot=slot, rarity=rarity,
        requires_attunement=attune, is_magical=True,
        ac_bonus=ac_bonus,
        stat_bonuses=stat_bonuses or {},
        save_bonuses=save_bonuses or {},
        skill_bonuses=skill_bonuses or {},
        damage_resistances=resistances or [],
        damage_immunities=immunities or [],
        condition_immunities=cond_immunities or [],
        speed_bonus=speed_bonus,
        charges=charges, max_charges=max_charges,
        spell_granted=spell_granted,
    )


# ---- Cloaks ----
CLOAK_OF_PROTECTION = _wondrous(
    "Cloak of Protection", "cloak", "uncommon", attune=True,
    ac_bonus=1, save_bonuses={"all": 1},
    desc="+1 AC, +1 to all saving throws.")

CLOAK_OF_DISPLACEMENT = _wondrous(
    "Cloak of Displacement", "cloak", "rare", attune=True,
    desc="Attacks against you have disadvantage. Ends when hit, resets on your turn.")

CLOAK_OF_ELVENKIND = _wondrous(
    "Cloak of Elvenkind", "cloak", "uncommon", attune=True,
    skill_bonuses={"Stealth": 99},  # 99 = advantage
    desc="Advantage on Stealth checks. Perception checks to find you have disadvantage.")

# ---- Rings ----
RING_OF_PROTECTION = _wondrous(
    "Ring of Protection", "ring1", "rare", attune=True,
    ac_bonus=1, save_bonuses={"all": 1},
    desc="+1 AC, +1 to all saving throws.")

RING_OF_RESISTANCE = _wondrous(
    "Ring of Resistance", "ring1", "rare", attune=True,
    resistances=["fire"],
    desc="Resistance to one damage type (gem determines type).")

RING_OF_SPELL_STORING = _wondrous(
    "Ring of Spell Storing", "ring1", "rare", attune=True,
    charges=5, max_charges=5,
    desc="Store up to 5 levels of spells. Expend charges to cast stored spells.")

RING_OF_EVASION = _wondrous(
    "Ring of Evasion", "ring1", "rare", attune=True,
    charges=3, max_charges=3,
    desc="3 charges. Reaction: turn failed DEX save into success. Regains 1d3 at dawn.")

# ---- Amulets & Necklaces ----
AMULET_OF_HEALTH = _wondrous(
    "Amulet of Health", "amulet", "rare", attune=True,
    stat_bonuses={"constitution": 19},
    desc="CON score becomes 19 while attuned.")

PERIAPT_OF_WOUND_CLOSURE = _wondrous(
    "Periapt of Wound Closure", "amulet", "uncommon", attune=True,
    desc="Stabilize at 0 HP. Double dice on HD healing.")

AMULET_OF_PROOF_AGAINST_DETECTION = _wondrous(
    "Amulet of Proof Against Detection", "amulet", "uncommon", attune=True,
    desc="Hidden from divination magic. Can't be targeted by divination or perceived through scrying.")

NECKLACE_OF_FIREBALLS = _wondrous(
    "Necklace of Fireballs", "amulet", "rare",
    charges=6, max_charges=6, spell_granted="Fireball",
    desc="Detach beads to cast Fireball (3d6 per bead, DEX DC 15).")

# ---- Boots ----
BOOTS_OF_SPEED = _wondrous(
    "Boots of Speed", "boots", "rare", attune=True,
    speed_bonus=99,  # 99 = double speed
    desc="Bonus action: double speed for 10 minutes. Attacks of opportunity have disadvantage.")

BOOTS_OF_ELVENKIND = _wondrous(
    "Boots of Elvenkind", "boots", "uncommon",
    skill_bonuses={"Stealth": 99},
    desc="Steps make no sound. Advantage on Stealth checks to move silently.")

WINGED_BOOTS = _wondrous(
    "Winged Boots", "boots", "uncommon", attune=True,
    desc="Fly speed equal to walking speed for 4 hours.")

BOOTS_OF_STRIDING = _wondrous(
    "Boots of Striding and Springing", "boots", "uncommon", attune=True,
    speed_bonus=0,  # Sets minimum speed to 30
    desc="Speed can't be reduced below 30. Jump distance x3.")

# ---- Gloves & Gauntlets ----
GAUNTLETS_OF_OGRE_POWER = _wondrous(
    "Gauntlets of Ogre Power", "gloves", "uncommon", attune=True,
    stat_bonuses={"strength": 19},
    desc="STR score becomes 19 while attuned.")

GLOVES_OF_MISSILE_SNARING = _wondrous(
    "Gloves of Missile Snaring", "gloves", "uncommon", attune=True,
    desc="Reaction: reduce ranged weapon damage by 1d10 + DEX mod. If reduced to 0, catch it.")

GLOVES_OF_THIEVERY = _wondrous(
    "Gloves of Thievery", "gloves", "uncommon",
    skill_bonuses={"Sleight of Hand": 5},
    desc="+5 to Sleight of Hand and lockpicking. Invisible while worn.")

BRACERS_OF_DEFENSE = _wondrous(
    "Bracers of Defense", "gloves", "rare", attune=True,
    ac_bonus=2,
    desc="+2 AC while wearing no armor and not using a shield.")

BRACERS_OF_ARCHERY = _wondrous(
    "Bracers of Archery", "gloves", "uncommon", attune=True,
    desc="+2 damage with longbow and shortbow. Proficiency with both.")

# ---- Belts ----
BELT_OF_GIANT_STRENGTH_HILL = _wondrous(
    "Belt of Hill Giant Strength", "belt", "rare", attune=True,
    stat_bonuses={"strength": 21},
    desc="STR score becomes 21.")

BELT_OF_GIANT_STRENGTH_FROST = _wondrous(
    "Belt of Frost Giant Strength", "belt", "very_rare", attune=True,
    stat_bonuses={"strength": 23},
    desc="STR score becomes 23.")

BELT_OF_GIANT_STRENGTH_FIRE = _wondrous(
    "Belt of Fire Giant Strength", "belt", "very_rare", attune=True,
    stat_bonuses={"strength": 25},
    desc="STR score becomes 25.")

BELT_OF_GIANT_STRENGTH_STORM = _wondrous(
    "Belt of Storm Giant Strength", "belt", "legendary", attune=True,
    stat_bonuses={"strength": 29},
    desc="STR score becomes 29.")

BELT_OF_DWARVENKIND = _wondrous(
    "Belt of Dwarvenkind", "belt", "rare", attune=True,
    stat_bonuses={"constitution": 2},  # +2 CON (max 20)
    resistances=["poison"],
    desc="+2 CON (max 20). Resistance to poison. Advantage on poison saves. Darkvision 60ft.")

# ---- Helms ----
HELM_OF_BRILLIANCE = _wondrous(
    "Helm of Brilliance", "helm", "very_rare", attune=True,
    resistances=["fire"],
    charges=10, max_charges=10,
    desc="Fire resistance. Cast fire spells using charges. Undead in 30ft take radiant damage.")

HEADBAND_OF_INTELLECT = _wondrous(
    "Headband of Intellect", "helm", "uncommon", attune=True,
    stat_bonuses={"intelligence": 19},
    desc="INT score becomes 19 while attuned.")

CIRCLET_OF_BLASTING = _wondrous(
    "Circlet of Blasting", "helm", "uncommon",
    spell_granted="Scorching Ray",
    desc="Cast Scorching Ray (1/day) at +5 to hit.")

# ---- Consumables ----
POTION_OF_HEALING = Item(
    name="Potion of Healing", item_type="potion", uses=1,
    description="Regain 2d4+2 hit points.", heals="2d4+2")

POTION_OF_GREATER_HEALING = Item(
    name="Potion of Greater Healing", item_type="potion", uses=1,
    description="Regain 4d4+4 hit points.", heals="4d4+4", rarity="uncommon")

POTION_OF_SUPERIOR_HEALING = Item(
    name="Potion of Superior Healing", item_type="potion", uses=1,
    description="Regain 8d4+8 hit points.", heals="8d4+8", rarity="rare")

POTION_OF_SUPREME_HEALING = Item(
    name="Potion of Supreme Healing", item_type="potion", uses=1,
    description="Regain 10d4+20 hit points.", heals="10d4+20", rarity="very_rare")

POTION_OF_SPEED = Item(
    name="Potion of Speed", item_type="potion", uses=1,
    description="Haste effect for 1 minute (no concentration).",
    buff="haste", rarity="very_rare")

POTION_OF_RESISTANCE = Item(
    name="Potion of Resistance (Fire)", item_type="potion", uses=1,
    description="Resistance to fire damage for 1 hour.",
    buff="resistance:fire", rarity="uncommon")

POTION_OF_INVULNERABILITY = Item(
    name="Potion of Invulnerability", item_type="potion", uses=1,
    description="Resistance to all damage for 1 minute.",
    buff="resistance:all", rarity="rare")


# ============================================================
# Lookup Tables
# ============================================================

# All base weapons indexed by name
WEAPON_DB = {
    "Club": CLUB, "Dagger": DAGGER, "Greatclub": GREATCLUB,
    "Handaxe": HANDAXE, "Javelin": JAVELIN, "Light Hammer": LIGHT_HAMMER,
    "Mace": MACE, "Quarterstaff": QUARTERSTAFF, "Sickle": SICKLE, "Spear": SPEAR,
    "Light Crossbow": LIGHT_CROSSBOW, "Dart": DART, "Shortbow": SHORTBOW, "Sling": SLING,
    "Battleaxe": BATTLEAXE, "Flail": FLAIL, "Glaive": GLAIVE,
    "Greataxe": GREATAXE, "Greatsword": GREATSWORD, "Halberd": HALBERD,
    "Lance": LANCE, "Longsword": LONGSWORD, "Maul": MAUL, "Morningstar": MORNINGSTAR,
    "Pike": PIKE, "Rapier": RAPIER, "Scimitar": SCIMITAR, "Shortsword": SHORTSWORD,
    "Trident": TRIDENT, "War Pick": WAR_PICK, "Warhammer": WARHAMMER, "Whip": WHIP,
    "Hand Crossbow": HAND_CROSSBOW, "Heavy Crossbow": HEAVY_CROSSBOW, "Longbow": LONGBOW,
}

# All base armor indexed by name
ARMOR_DB = {
    "Padded Armor": PADDED_ARMOR, "Leather Armor": LEATHER_ARMOR,
    "Studded Leather": STUDDED_LEATHER,
    "Hide Armor": HIDE_ARMOR, "Chain Shirt": CHAIN_SHIRT,
    "Scale Mail": SCALE_MAIL, "Breastplate": BREASTPLATE, "Half Plate": HALF_PLATE,
    "Ring Mail": RING_MAIL, "Chain Mail": CHAIN_MAIL,
    "Splint Armor": SPLINT_ARMOR, "Plate Armor": PLATE_ARMOR,
}

SHIELD_DB = {
    "Shield": SHIELD, "Shield +1": SHIELD_PLUS_1,
    "Shield +2": SHIELD_PLUS_2, "Shield +3": SHIELD_PLUS_3,
    "Animated Shield": ANIMATED_SHIELD, "Spellguard Shield": SPELLGUARD_SHIELD,
}

# Magic weapons
MAGIC_WEAPON_DB = {
    "Flame Tongue Longsword": FLAME_TONGUE_LONGSWORD,
    "Frost Brand Greatsword": FROST_BRAND_GREATSWORD,
    "Sun Blade": SUNBLADE,
    "Vicious Rapier": VICIOUS_RAPIER,
    "Javelin of Lightning": JAVELIN_OF_LIGHTNING,
    "Dagger of Venom": DAGGER_OF_VENOM,
    "Oathbow": OATHBOW,
    "Vorpal Sword": VORPAL_SWORD,
    "Holy Avenger": HOLY_AVENGER,
}

# Magic armor
MAGIC_ARMOR_DB = {
    "Mithral Chain Shirt": MITHRAL_CHAIN_SHIRT,
    "Adamantine Plate": ADAMANTINE_PLATE,
    "Dragon Scale Mail": DRAGON_SCALE_MAIL,
    "Armor of Resistance": ARMOR_OF_RESISTANCE,
}

# Wondrous items
WONDROUS_DB = {
    "Cloak of Protection": CLOAK_OF_PROTECTION,
    "Cloak of Displacement": CLOAK_OF_DISPLACEMENT,
    "Cloak of Elvenkind": CLOAK_OF_ELVENKIND,
    "Ring of Protection": RING_OF_PROTECTION,
    "Ring of Resistance": RING_OF_RESISTANCE,
    "Ring of Spell Storing": RING_OF_SPELL_STORING,
    "Ring of Evasion": RING_OF_EVASION,
    "Amulet of Health": AMULET_OF_HEALTH,
    "Periapt of Wound Closure": PERIAPT_OF_WOUND_CLOSURE,
    "Necklace of Fireballs": NECKLACE_OF_FIREBALLS,
    "Boots of Speed": BOOTS_OF_SPEED,
    "Boots of Elvenkind": BOOTS_OF_ELVENKIND,
    "Winged Boots": WINGED_BOOTS,
    "Gauntlets of Ogre Power": GAUNTLETS_OF_OGRE_POWER,
    "Gloves of Missile Snaring": GLOVES_OF_MISSILE_SNARING,
    "Bracers of Defense": BRACERS_OF_DEFENSE,
    "Bracers of Archery": BRACERS_OF_ARCHERY,
    "Belt of Hill Giant Strength": BELT_OF_GIANT_STRENGTH_HILL,
    "Belt of Frost Giant Strength": BELT_OF_GIANT_STRENGTH_FROST,
    "Belt of Fire Giant Strength": BELT_OF_GIANT_STRENGTH_FIRE,
    "Belt of Storm Giant Strength": BELT_OF_GIANT_STRENGTH_STORM,
    "Belt of Dwarvenkind": BELT_OF_DWARVENKIND,
    "Helm of Brilliance": HELM_OF_BRILLIANCE,
    "Headband of Intellect": HEADBAND_OF_INTELLECT,
    "Circlet of Blasting": CIRCLET_OF_BLASTING,
}

# Consumables
CONSUMABLE_DB = {
    "Potion of Healing": POTION_OF_HEALING,
    "Potion of Greater Healing": POTION_OF_GREATER_HEALING,
    "Potion of Superior Healing": POTION_OF_SUPERIOR_HEALING,
    "Potion of Supreme Healing": POTION_OF_SUPREME_HEALING,
    "Potion of Speed": POTION_OF_SPEED,
    "Potion of Resistance (Fire)": POTION_OF_RESISTANCE,
    "Potion of Invulnerability": POTION_OF_INVULNERABILITY,
}

# Master database of all items
ALL_ITEMS_DB = {}
ALL_ITEMS_DB.update(WEAPON_DB)
ALL_ITEMS_DB.update(ARMOR_DB)
ALL_ITEMS_DB.update(SHIELD_DB)
ALL_ITEMS_DB.update(MAGIC_WEAPON_DB)
ALL_ITEMS_DB.update(MAGIC_ARMOR_DB)
ALL_ITEMS_DB.update(WONDROUS_DB)
ALL_ITEMS_DB.update(CONSUMABLE_DB)


def get_item(name: str) -> "Item | None":
    """Get a deep copy of an item from the database by name."""
    import copy
    item = ALL_ITEMS_DB.get(name)
    if item:
        return copy.deepcopy(item)
    # Try +1/+2/+3 variants
    for bonus in (1, 2, 3):
        for base_name in WEAPON_DB:
            if name == f"{base_name} +{bonus}":
                return magic_weapon(base_name, bonus)
        for base_name in ARMOR_DB:
            if name == f"{base_name} +{bonus}":
                return magic_armor(base_name, bonus)
    return None


def get_all_weapons():
    """Get list of all weapon names (base + magic)."""
    names = list(WEAPON_DB.keys()) + list(MAGIC_WEAPON_DB.keys())
    # Add +1/+2/+3 variants of common weapons
    for base in ["Longsword", "Greatsword", "Rapier", "Shortsword", "Longbow",
                 "Greataxe", "Warhammer", "Battleaxe", "Dagger", "Hand Crossbow"]:
        for b in (1, 2, 3):
            names.append(f"{base} +{b}")
    return sorted(names)


def get_all_armor():
    """Get list of all armor names (base + magic)."""
    names = list(ARMOR_DB.keys()) + list(MAGIC_ARMOR_DB.keys())
    for base in ["Leather Armor", "Studded Leather", "Chain Mail", "Plate Armor",
                 "Breastplate", "Half Plate", "Scale Mail", "Chain Shirt"]:
        for b in (1, 2, 3):
            names.append(f"{base} +{b}")
    return sorted(names)


def get_all_shields():
    """Get list of all shield names."""
    return sorted(SHIELD_DB.keys())


def get_all_wondrous():
    """Get list of all wondrous item names."""
    return sorted(WONDROUS_DB.keys())


def get_all_consumables():
    """Get list of all consumable names."""
    return sorted(CONSUMABLE_DB.keys())


def get_equipment_by_slot(slot: str):
    """Get all items that go in a specific equipment slot."""
    results = []
    for name, item in ALL_ITEMS_DB.items():
        if item.slot == slot or (slot == "armor" and item.item_type == "armor"):
            results.append(name)
    return sorted(results)
