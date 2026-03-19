"""
D&D 5e 2014 Encounter Difficulty Calculator & Random Encounter Tables.

Based on DMG Chapter 3 (pp. 81-85):
- XP Thresholds per character level
- Encounter multipliers for number of monsters
- CR to XP mapping
- Random encounter tables by environment and party level

Usage:
    from data.encounters import (
        calculate_encounter_difficulty, get_xp_for_cr,
        XP_THRESHOLDS, CR_XP_TABLE, RANDOM_ENCOUNTERS,
    )
"""
from typing import List, Dict, Tuple, Optional
import random


# ============================================================================
# XP THRESHOLDS PER CHARACTER LEVEL (DMG p. 82)
# ============================================================================

XP_THRESHOLDS: Dict[int, Dict[str, int]] = {
    1:  {"easy": 25,   "medium": 50,   "hard": 75,    "deadly": 100},
    2:  {"easy": 50,   "medium": 100,  "hard": 150,   "deadly": 200},
    3:  {"easy": 75,   "medium": 150,  "hard": 225,   "deadly": 400},
    4:  {"easy": 125,  "medium": 250,  "hard": 375,   "deadly": 500},
    5:  {"easy": 250,  "medium": 500,  "hard": 750,   "deadly": 1100},
    6:  {"easy": 300,  "medium": 600,  "hard": 900,   "deadly": 1400},
    7:  {"easy": 350,  "medium": 750,  "hard": 1100,  "deadly": 1700},
    8:  {"easy": 450,  "medium": 900,  "hard": 1400,  "deadly": 2100},
    9:  {"easy": 550,  "medium": 1100, "hard": 1600,  "deadly": 2400},
    10: {"easy": 600,  "medium": 1200, "hard": 1900,  "deadly": 2800},
    11: {"easy": 800,  "medium": 1600, "hard": 2400,  "deadly": 3600},
    12: {"easy": 1000, "medium": 2000, "hard": 3000,  "deadly": 4500},
    13: {"easy": 1100, "medium": 2200, "hard": 3400,  "deadly": 5100},
    14: {"easy": 1250, "medium": 2500, "hard": 3800,  "deadly": 5700},
    15: {"easy": 1400, "medium": 2800, "hard": 4300,  "deadly": 6400},
    16: {"easy": 1600, "medium": 3200, "hard": 4800,  "deadly": 7200},
    17: {"easy": 2000, "medium": 3900, "hard": 5900,  "deadly": 8800},
    18: {"easy": 2100, "medium": 4200, "hard": 6300,  "deadly": 9500},
    19: {"easy": 2400, "medium": 4900, "hard": 7300,  "deadly": 10900},
    20: {"easy": 2800, "medium": 5700, "hard": 8500,  "deadly": 12700},
}

# ============================================================================
# CR TO XP TABLE (DMG p. 275)
# ============================================================================

CR_XP_TABLE: Dict[str, int] = {
    "0":    10,
    "1/8":  25,
    "1/4":  50,
    "1/2":  100,
    "1":    200,
    "2":    450,
    "3":    700,
    "4":    1100,
    "5":    1800,
    "6":    2300,
    "7":    2900,
    "8":    3900,
    "9":    5000,
    "10":   5900,
    "11":   7200,
    "12":   8400,
    "13":   10000,
    "14":   11500,
    "15":   13000,
    "16":   15000,
    "17":   18000,
    "18":   20000,
    "19":   22000,
    "20":   25000,
    "21":   33000,
    "22":   41000,
    "23":   50000,
    "24":   62000,
    "25":   75000,
    "26":   90000,
    "27":   105000,
    "28":   120000,
    "29":   135000,
    "30":   155000,
}

# ============================================================================
# ENCOUNTER MULTIPLIERS (DMG p. 82)
# ============================================================================

ENCOUNTER_MULTIPLIERS: List[Tuple[int, float]] = [
    # (max_monster_count, multiplier)
    (1,  1.0),
    (2,  1.5),
    (6,  2.0),
    (10, 2.5),
    (14, 3.0),
    (999, 4.0),
]


def get_encounter_multiplier(num_monsters: int, num_players: int = 4) -> float:
    """Get the XP multiplier for encounter difficulty based on number of monsters.
    Adjusts for party size < 3 or > 5 per DMG guidelines."""
    for max_count, mult in ENCOUNTER_MULTIPLIERS:
        if num_monsters <= max_count:
            base_mult = mult
            break
    else:
        base_mult = 4.0

    # Party size adjustment (DMG p. 83)
    if num_players < 3:
        # Use next higher multiplier
        idx = next((i for i, (mc, _) in enumerate(ENCOUNTER_MULTIPLIERS) if num_monsters <= mc), len(ENCOUNTER_MULTIPLIERS) - 1)
        if idx < len(ENCOUNTER_MULTIPLIERS) - 1:
            base_mult = ENCOUNTER_MULTIPLIERS[idx + 1][1]
    elif num_players > 5:
        # Use next lower multiplier
        idx = next((i for i, (mc, _) in enumerate(ENCOUNTER_MULTIPLIERS) if num_monsters <= mc), 0)
        if idx > 0:
            base_mult = ENCOUNTER_MULTIPLIERS[idx - 1][1]

    return base_mult


def get_xp_for_cr(cr_string: str) -> int:
    """Get XP value for a CR string (e.g., '1/2', '5', '1/4')."""
    return CR_XP_TABLE.get(str(cr_string), 0)


def get_party_thresholds(levels: List[int]) -> Dict[str, int]:
    """Calculate total XP thresholds for a party given a list of character levels."""
    thresholds = {"easy": 0, "medium": 0, "hard": 0, "deadly": 0}
    for lvl in levels:
        lvl = max(1, min(20, lvl))
        for diff in thresholds:
            thresholds[diff] += XP_THRESHOLDS[lvl][diff]
    return thresholds


def calculate_encounter_difficulty(
    monster_crs: List[str],
    party_levels: List[int],
) -> Dict:
    """
    Calculate encounter difficulty for a party vs a group of monsters.

    Args:
        monster_crs: List of CR strings for each monster (e.g., ["5", "1/2", "1/2"])
        party_levels: List of character levels (e.g., [5, 5, 4, 5])

    Returns dict with:
        - total_xp: Raw XP total
        - adjusted_xp: XP after multiplier
        - multiplier: The encounter multiplier used
        - difficulty: "easy", "medium", "hard", "deadly", or "trivial"
        - thresholds: Party XP thresholds
        - xp_per_player: XP reward per player (raw, not adjusted)
    """
    if not monster_crs or not party_levels:
        return {
            "total_xp": 0, "adjusted_xp": 0, "multiplier": 1.0,
            "difficulty": "trivial", "thresholds": get_party_thresholds(party_levels or [1]),
            "xp_per_player": 0,
        }

    total_xp = sum(get_xp_for_cr(cr) for cr in monster_crs)
    num_monsters = len(monster_crs)
    num_players = len(party_levels)
    multiplier = get_encounter_multiplier(num_monsters, num_players)
    adjusted_xp = int(total_xp * multiplier)

    thresholds = get_party_thresholds(party_levels)

    if adjusted_xp >= thresholds["deadly"]:
        difficulty = "deadly"
    elif adjusted_xp >= thresholds["hard"]:
        difficulty = "hard"
    elif adjusted_xp >= thresholds["medium"]:
        difficulty = "medium"
    elif adjusted_xp >= thresholds["easy"]:
        difficulty = "easy"
    else:
        difficulty = "trivial"

    xp_per_player = total_xp // max(1, num_players)

    return {
        "total_xp": total_xp,
        "adjusted_xp": adjusted_xp,
        "multiplier": multiplier,
        "difficulty": difficulty,
        "thresholds": thresholds,
        "xp_per_player": xp_per_player,
    }


# ============================================================================
# RANDOM ENCOUNTER TABLES (by environment, DMG pp. 92-112 style)
# ============================================================================

RANDOM_ENCOUNTERS: Dict[str, Dict[str, list]] = {
    "forest": {
        "tier1": [
            {"roll": "1-5",   "encounter": "1d4 Twig Blight", "cr_each": "1/8", "notes": "Kasvillisuuden seassa piileskeleviä"},
            {"roll": "6-10",  "encounter": "2d4 Wolf", "cr_each": "1/4", "notes": "Nälkäinen susilauma"},
            {"roll": "11-15", "encounter": "1 Owlbear", "cr_each": "3", "notes": "Reviiriään puolustava pöllökarhu"},
            {"roll": "16-18", "encounter": "1d4 Bandit + 1 Bandit Captain", "cr_each": "1/8", "notes": "Rosvojoukko väijytyksessä"},
            {"roll": "19-20", "encounter": "1 Green Hag", "cr_each": "3", "notes": "Noita tarjoaa kauppaa — varokaa!"},
        ],
        "tier2": [
            {"roll": "1-5",   "encounter": "1d6 Dire Wolf", "cr_each": "1", "notes": "Suuret sudet metsästävät"},
            {"roll": "6-10",  "encounter": "1 Shambling Mound", "cr_each": "5", "notes": "Kasaantuva kasvimassa"},
            {"roll": "11-15", "encounter": "1d4 Ettercap + 2d4 Giant Spider", "cr_each": "2", "notes": "Hämähäkkipesä puiden joukossa"},
            {"roll": "16-18", "encounter": "1 Treant", "cr_each": "9", "notes": "Vanha puu herää — ystävä vai vihollinen?"},
            {"roll": "19-20", "encounter": "1 Young Green Dragon", "cr_each": "8", "notes": "Nuori vihreä lohikäärme"},
        ],
    },
    "road": {
        "tier1": [
            {"roll": "1-5",   "encounter": "1d6 Bandit", "cr_each": "1/8", "notes": "Tienryöstäjät"},
            {"roll": "6-10",  "encounter": "1 Merchant caravan", "cr_each": "0", "notes": "Kauppakaravaani — mahdollisuus kaupankäyntiin"},
            {"roll": "11-15", "encounter": "2d4 Wolf", "cr_each": "1/4", "notes": "Sudet uhkaavat leiripaikalla"},
            {"roll": "16-18", "encounter": "1 Knight + 2 Guard", "cr_each": "3", "notes": "Ritari matkaseurueeneen — kyselee uutisia"},
            {"roll": "19-20", "encounter": "1 Ogre", "cr_each": "2", "notes": "Örkki vaatii tietullia"},
        ],
        "tier2": [
            {"roll": "1-5",   "encounter": "2d4 Bandit + 1 Bandit Captain", "cr_each": "1/8", "notes": "Organisoitu rosvojoukko"},
            {"roll": "6-10",  "encounter": "1d4 Hobgoblin + 1 Hobgoblin Captain", "cr_each": "1/2", "notes": "Hobgoblin-partio"},
            {"roll": "11-15", "encounter": "1 Revenant", "cr_each": "5", "notes": "Kosto-haamu etsii jotakuta"},
            {"roll": "16-18", "encounter": "1d4 Troll", "cr_each": "5", "notes": "Trollit sillan alla"},
            {"roll": "19-20", "encounter": "1 Adult Red Dragon (flyover)", "cr_each": "17", "notes": "Lohikäärme lentää yli — huomioi vai piilottaudu?"},
        ],
    },
    "dungeon": {
        "tier1": [
            {"roll": "1-5",   "encounter": "2d4 Skeleton", "cr_each": "1/4", "notes": "Luurankoja vartioimassa"},
            {"roll": "6-10",  "encounter": "1d4 Zombie", "cr_each": "1/4", "notes": "Hitaasti laahaavia zombeja"},
            {"roll": "11-15", "encounter": "1 Mimic", "cr_each": "2", "notes": "Matkija aarrearkun muodossa"},
            {"roll": "16-18", "encounter": "1 Gelatinous Cube", "cr_each": "2", "notes": "Läpinäkyvä hyytykuutio käytävässä"},
            {"roll": "19-20", "encounter": "1 Spectator", "cr_each": "3", "notes": "Pienikokoinen Beholder-sukulainen vartioi aarretta"},
        ],
        "tier2": [
            {"roll": "1-5",   "encounter": "2d6 Skeleton + 1 Wight", "cr_each": "1/4", "notes": "Epäkuolleiden joukko komentajineen"},
            {"roll": "6-10",  "encounter": "1d4 Wraith", "cr_each": "5", "notes": "Haamuja pimeässä"},
            {"roll": "11-15", "encounter": "1 Beholder Zombie", "cr_each": "5", "notes": "Beholder-zombie laboratorion jäänne"},
            {"roll": "16-18", "encounter": "1 Mind Flayer", "cr_each": "7", "notes": "Psioninen kauhukala pimeissä käytävissä"},
            {"roll": "19-20", "encounter": "1 Young Black Dragon", "cr_each": "7", "notes": "Nuori musta lohikäärme pesässään"},
        ],
    },
    "mountain": {
        "tier1": [
            {"roll": "1-5",   "encounter": "1d4 Blood Hawk", "cr_each": "1/8", "notes": "Aggressiiviset haukat hyökkäävät"},
            {"roll": "6-10",  "encounter": "1 Giant Eagle", "cr_each": "1", "notes": "Jättikotka — voi olla avulias tai vihamielinen"},
            {"roll": "11-15", "encounter": "1d4 Harpy", "cr_each": "1", "notes": "Harpyijat laulavat houkuttelevasti"},
            {"roll": "16-18", "encounter": "1 Ogre", "cr_each": "2", "notes": "Luolan suulla asuva örkki"},
            {"roll": "19-20", "encounter": "1 Manticore", "cr_each": "3", "notes": "Mantikora vuorihyllyllä"},
        ],
        "tier2": [
            {"roll": "1-5",   "encounter": "1d4 Griffon", "cr_each": "2", "notes": "Griffoni-parvi pesää puolustaen"},
            {"roll": "6-10",  "encounter": "1 Stone Giant", "cr_each": "7", "notes": "Kivijättiläinen heittää kiviä"},
            {"roll": "11-15", "encounter": "1 Roc", "cr_each": "11", "notes": "Valtava Roc-lintu taivaalla"},
            {"roll": "16-18", "encounter": "1d4 Hill Giant", "cr_each": "5", "notes": "Kukkulajättiläiset metsästävät"},
            {"roll": "19-20", "encounter": "1 Adult White Dragon", "cr_each": "13", "notes": "Valkoinen lohikäärme jäähuipulla"},
        ],
    },
    "urban": {
        "tier1": [
            {"roll": "1-5",   "encounter": "1d4 Thug", "cr_each": "1/2", "notes": "Katurosvot pimeässä kujassa"},
            {"roll": "6-10",  "encounter": "1 Spy", "cr_each": "1", "notes": "Vakooja seuraa ryhmää"},
            {"roll": "11-15", "encounter": "2d4 Bandit", "cr_each": "1/8", "notes": "Jengi vaatii 'suojelurahaa'"},
            {"roll": "16-18", "encounter": "1 Doppelganger", "cr_each": "3", "notes": "Muodonmuuttaja esittää tuttua NPC:tä"},
            {"roll": "19-20", "encounter": "1 Wererat", "cr_each": "2", "notes": "Ihmisrotta viemäreissä"},
        ],
        "tier2": [
            {"roll": "1-5",   "encounter": "1d4 Assassin", "cr_each": "8", "notes": "Palkatut salamurhaajat"},
            {"roll": "6-10",  "encounter": "1 Vampire Spawn", "cr_each": "5", "notes": "Vampyyrin kätyri öisellä kadulla"},
            {"roll": "11-15", "encounter": "1 Mage + 2 Guard", "cr_each": "6", "notes": "Roistovelho apureineen"},
            {"roll": "16-18", "encounter": "1d4 Shadow", "cr_each": "1/2", "notes": "Varjoja hautausmaan luona"},
            {"roll": "19-20", "encounter": "1 Rakshasa (disguised)", "cr_each": "13", "notes": "Rakshasa naamioituneena aatelisena"},
        ],
    },
}


def roll_random_encounter(environment: str, tier: str = "tier1") -> Optional[dict]:
    """Roll a random encounter for an environment.
    Returns encounter dict or None if no table exists."""
    table = RANDOM_ENCOUNTERS.get(environment, {}).get(tier, [])
    if not table:
        return None
    roll = random.randint(1, 20)
    for entry in table:
        parts = entry["roll"].split("-")
        low = int(parts[0])
        high = int(parts[-1])
        if low <= roll <= high:
            return {**entry, "actual_roll": roll}
    return table[-1]  # fallback


def get_encounter_environments() -> List[str]:
    """List all available encounter environments."""
    return sorted(RANDOM_ENCOUNTERS.keys())


def get_encounter_tiers(environment: str) -> List[str]:
    """List available tiers for an environment."""
    return sorted(RANDOM_ENCOUNTERS.get(environment, {}).keys())


# ============================================================================
# LOOT TABLES (DMG pp. 136-139 simplified)
# ============================================================================

INDIVIDUAL_TREASURE: Dict[str, list] = {
    "cr0-4": [
        {"roll": "1-30",  "treasure": "5d6 cp"},
        {"roll": "31-60", "treasure": "4d6 sp"},
        {"roll": "61-70", "treasure": "3d6 ep"},
        {"roll": "71-95", "treasure": "3d6 gp"},
        {"roll": "96-100","treasure": "1d6 pp"},
    ],
    "cr5-10": [
        {"roll": "1-30",  "treasure": "4d6x100 cp + 1d6x10 ep"},
        {"roll": "31-60", "treasure": "6d6x10 sp + 2d6x10 gp"},
        {"roll": "61-70", "treasure": "3d6x10 ep + 2d6x10 gp"},
        {"roll": "71-95", "treasure": "4d6x10 gp"},
        {"roll": "96-100","treasure": "2d6x10 gp + 3d6 pp"},
    ],
    "cr11-16": [
        {"roll": "1-20",  "treasure": "4d6x100 sp + 1d6x100 gp"},
        {"roll": "21-35", "treasure": "1d6x100 ep + 1d6x100 gp"},
        {"roll": "36-75", "treasure": "2d6x100 gp + 1d6x10 pp"},
        {"roll": "76-100","treasure": "2d6x100 gp + 2d6x10 pp"},
    ],
    "cr17+": [
        {"roll": "1-15",  "treasure": "2d6x1000 ep + 8d6x100 gp"},
        {"roll": "16-55", "treasure": "1d6x1000 gp + 1d6x100 pp"},
        {"roll": "56-100","treasure": "1d6x1000 gp + 2d6x100 pp"},
    ],
}

TREASURE_HOARD_ITEMS: Dict[str, dict] = {
    "cr0-4": {
        "coins": "6d6x100 cp, 3d6x100 sp, 2d6x10 gp",
        "gems_art": [
            {"roll": "1-6",   "item": "—"},
            {"roll": "7-16",  "item": "2d6 x 10 gp gems"},
            {"roll": "17-26", "item": "2d4 x 25 gp art objects"},
            {"roll": "27-36", "item": "2d6 x 50 gp gems"},
            {"roll": "37-44", "item": "2d6 x 10 gp gems + 1d6 Magic Items (Table A)"},
            {"roll": "45-52", "item": "2d4 x 25 gp art + 1d6 Magic Items (Table A)"},
            {"roll": "53-60", "item": "2d6 x 50 gp gems + 1d6 Magic Items (Table A)"},
            {"roll": "61-65", "item": "2d6 x 10 gp gems + 1d4 Magic Items (Table B)"},
            {"roll": "66-70", "item": "2d4 x 25 gp art + 1d4 Magic Items (Table B)"},
            {"roll": "71-75", "item": "2d6 x 50 gp gems + 1d4 Magic Items (Table B)"},
            {"roll": "76-78", "item": "2d6 x 10 gp gems + 1d4 Magic Items (Table C)"},
            {"roll": "79-80", "item": "2d4 x 25 gp art + 1d4 Magic Items (Table C)"},
            {"roll": "81-85", "item": "2d6 x 50 gp gems + 1d4 Magic Items (Table C)"},
            {"roll": "86-92", "item": "2d4 x 25 gp art + 1d4 Magic Items (Table F)"},
            {"roll": "93-97", "item": "2d6 x 50 gp gems + 1d4 Magic Items (Table F)"},
            {"roll": "98-99", "item": "2d4 x 25 gp art + 1 Magic Item (Table G)"},
            {"roll": "100",   "item": "2d6 x 50 gp gems + 1 Magic Item (Table G)"},
        ],
    },
    "cr5-10": {
        "coins": "2d6x100 cp, 2d6x1000 sp, 6d6x100 gp, 3d6x10 pp",
        "gems_art": [
            {"roll": "1-4",   "item": "—"},
            {"roll": "5-10",  "item": "2d4 x 25 gp art objects"},
            {"roll": "11-16", "item": "3d6 x 50 gp gems"},
            {"roll": "17-22", "item": "3d6 x 100 gp gems"},
            {"roll": "23-28", "item": "2d4 x 250 gp art objects"},
            {"roll": "29-32", "item": "2d4 x 25 gp art + 1d6 Magic Items (Table A)"},
            {"roll": "33-36", "item": "3d6 x 50 gp gems + 1d6 Magic Items (Table A)"},
            {"roll": "37-40", "item": "3d6 x 100 gp gems + 1d6 Magic Items (Table A)"},
            {"roll": "41-44", "item": "2d4 x 250 gp art + 1d6 Magic Items (Table A)"},
            {"roll": "45-49", "item": "2d4 x 25 gp art + 1d4 Magic Items (Table B)"},
            {"roll": "50-54", "item": "3d6 x 50 gp gems + 1d4 Magic Items (Table B)"},
            {"roll": "55-59", "item": "3d6 x 100 gp gems + 1d4 Magic Items (Table B)"},
            {"roll": "60-63", "item": "2d4 x 250 gp art + 1d4 Magic Items (Table B)"},
            {"roll": "64-66", "item": "2d4 x 25 gp art + 1d4 Magic Items (Table C)"},
            {"roll": "67-69", "item": "3d6 x 50 gp gems + 1d4 Magic Items (Table C)"},
            {"roll": "70-72", "item": "3d6 x 100 gp gems + 1d4 Magic Items (Table C)"},
            {"roll": "73-74", "item": "2d4 x 250 gp art + 1d4 Magic Items (Table C)"},
            {"roll": "75-76", "item": "2d4 x 25 gp art + 1 Magic Item (Table D)"},
            {"roll": "77-78", "item": "3d6 x 50 gp gems + 1 Magic Item (Table D)"},
            {"roll": "79",    "item": "3d6 x 100 gp gems + 1 Magic Item (Table D)"},
            {"roll": "80",    "item": "2d4 x 250 gp art + 1 Magic Item (Table D)"},
            {"roll": "81-84", "item": "2d4 x 25 gp art + 1d4 Magic Items (Table F)"},
            {"roll": "85-88", "item": "3d6 x 50 gp gems + 1d4 Magic Items (Table F)"},
            {"roll": "89-91", "item": "3d6 x 100 gp gems + 1d4 Magic Items (Table F)"},
            {"roll": "92-94", "item": "2d4 x 250 gp art + 1d4 Magic Items (Table F)"},
            {"roll": "95-96", "item": "3d6 x 100 gp gems + 1d4 Magic Items (Table G)"},
            {"roll": "97-98", "item": "2d4 x 250 gp art + 1 Magic Item (Table G)"},
            {"roll": "99",    "item": "3d6 x 100 gp gems + 1 Magic Item (Table H)"},
            {"roll": "100",   "item": "2d4 x 250 gp art + 1 Magic Item (Table H)"},
        ],
    },
}


MAGIC_ITEM_TABLES: Dict[str, list] = {
    "A": [
        "Potion of Healing", "Spell Scroll (cantrip)", "Spell Scroll (1st level)",
        "Potion of Climbing", "Potion of Animal Friendship",
    ],
    "B": [
        "Potion of Greater Healing", "Spell Scroll (2nd level)", "Bag of Holding",
        "Cloak of Protection", "Boots of Elvenkind", "Gauntlets of Ogre Power",
        "Goggles of Night", "Pearl of Power", "Wand of Magic Missiles",
    ],
    "C": [
        "Potion of Superior Healing", "Spell Scroll (3rd level)", "+1 Weapon",
        "+1 Shield", "+1 Armor", "Ring of Protection", "Amulet of Proof Against Detection",
        "Bracers of Defense", "Cloak of Displacement",
    ],
    "D": [
        "Potion of Supreme Healing", "Spell Scroll (6th level)", "+2 Weapon",
        "+2 Shield", "+2 Armor", "Ring of Resistance", "Staff of Healing",
    ],
    "F": [
        "+1 Weapon", "Shield +1", "Sentinel Shield", "Cloak of the Manta Ray",
        "Amulet of Health", "Belt of Hill Giant Strength", "Boots of Speed",
        "Flame Tongue", "Ring of Spell Storing",
    ],
    "G": [
        "+2 Weapon", "Shield +2", "Armor +2", "Ring of Regeneration",
        "Staff of Power", "Robe of Stars", "Belt of Fire Giant Strength",
    ],
    "H": [
        "+3 Weapon", "+3 Armor", "Holy Avenger", "Ring of Three Wishes",
        "Vorpal Sword", "Staff of the Magi", "Belt of Storm Giant Strength",
    ],
}


def roll_individual_treasure(cr_range: str = "cr0-4") -> str:
    """Roll individual treasure for a defeated creature. Returns description string."""
    table = INDIVIDUAL_TREASURE.get(cr_range, INDIVIDUAL_TREASURE["cr0-4"])
    roll = random.randint(1, 100)
    for entry in table:
        parts = entry["roll"].split("-")
        low = int(parts[0])
        high = int(parts[-1])
        if low <= roll <= high:
            return entry["treasure"]
    return table[-1]["treasure"]


def roll_magic_item(table_letter: str = "A") -> str:
    """Roll a random magic item from a DMG table."""
    items = MAGIC_ITEM_TABLES.get(table_letter.upper(), MAGIC_ITEM_TABLES["A"])
    return random.choice(items)


def generate_loot(cr_range: str = "cr0-4", num_creatures: int = 1, hoard: bool = False) -> Dict:
    """Generate loot for an encounter.

    Args:
        cr_range: Creature CR range ("cr0-4", "cr5-10", "cr11-16", "cr17+")
        num_creatures: Number of creatures for individual treasure
        hoard: If True, roll treasure hoard instead of individual

    Returns dict with loot description.
    """
    if hoard:
        hoard_data = TREASURE_HOARD_ITEMS.get(cr_range, TREASURE_HOARD_ITEMS["cr0-4"])
        roll = random.randint(1, 100)
        gems_art = "—"
        for entry in hoard_data["gems_art"]:
            parts = entry["roll"].split("-")
            low = int(parts[0])
            high = int(parts[-1])
            if low <= roll <= high:
                gems_art = entry["item"]
                break
        return {
            "type": "hoard",
            "coins": hoard_data["coins"],
            "gems_art_magic": gems_art,
            "roll": roll,
        }
    else:
        treasures = []
        for _ in range(num_creatures):
            treasures.append(roll_individual_treasure(cr_range))
        return {
            "type": "individual",
            "treasures": treasures,
        }
