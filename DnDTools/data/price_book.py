"""D&D 5e price book — canonical PHB / DMG / XGtE pricing for spell
scrolls, magic-item rarity tiers, spellcasting services and bulk
adventurer gear.

The :mod:`data.shop_catalog` module already carries a flat dict of
named items.  This module adds the *rules-level* views the DM needs
when running the game:

  * :data:`SPELL_SCROLL_BASE_PRICE` — XGtE p. 133 table (cantrip = 30 gp,
    1st = 50–100, 2nd = 200–400, …).
  * :data:`MAGIC_ITEM_PRICE_BAND` — XGtE p. 135 magic-item rarity
    tiers (common 50–100, uncommon 101–500, rare 501–5000, very rare
    5001–50000, legendary 50001+).
  * :data:`SPELLCASTING_SERVICE_PRICE` — typical NPC spellcaster
    service fees (identify 100 gp, lesser restoration 90 gp, raise
    dead 1250 gp, …) so the DM can quote a price instantly.
  * :func:`scroll_price_for_spell(spell_name)` — looks up a spell in
    ``data.spells`` and returns the centre of its scroll price band.

Pure logic, no pygame.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple


# --------------------------------------------------------------------- #
# Spell scrolls (Xanathar's Guide p. 133)
# --------------------------------------------------------------------- #
# Each entry: (low, high) inclusive gold-piece range.
SPELL_SCROLL_BASE_PRICE: Dict[int, Tuple[int, int]] = {
    0: (30, 50),       # Cantrip
    1: (50, 100),
    2: (200, 400),
    3: (500, 750),
    4: (1000, 2500),
    5: (3000, 6000),
    6: (8000, 15000),
    7: (16000, 25000),
    8: (28000, 40000),
    9: (50000, 75000),
}


def scroll_price_band(level: int) -> Tuple[int, int]:
    return SPELL_SCROLL_BASE_PRICE.get(max(0, min(9, level)),
                                          (30, 50))


def scroll_centre_price(level: int) -> int:
    lo, hi = scroll_price_band(level)
    return (lo + hi) // 2


def scroll_price_for_spell(spell_name: str) -> int:
    """Look up a spell by name (case-insensitive prefix) and return the
    centre of its scroll price band.  Returns 50 gp when unknown."""
    try:
        from data.spells import _spells
    except Exception:  # pragma: no cover
        return 50
    target = (spell_name or "").strip().lower()
    if not target:
        return 50
    for nm, info in _spells.items():
        if nm.lower() == target or nm.lower().startswith(target):
            return scroll_centre_price(int(getattr(info, "level", 0) or 0))
    return 50


# --------------------------------------------------------------------- #
# Magic-item rarity bands (Xanathar's Guide p. 135)
# --------------------------------------------------------------------- #
MAGIC_ITEM_PRICE_BAND: Dict[str, Tuple[int, int]] = {
    "common":      (50,     100),
    "uncommon":    (101,    500),
    "rare":        (501,    5_000),
    "very_rare":   (5_001,  50_000),
    "legendary":   (50_001, 250_000),
}


def magic_item_centre_price(rarity: str) -> int:
    lo, hi = MAGIC_ITEM_PRICE_BAND.get(
        (rarity or "common").lower().replace(" ", "_"),
        (50, 100))
    return (lo + hi) // 2


def magic_item_band_label(rarity: str) -> str:
    lo, hi = MAGIC_ITEM_PRICE_BAND.get(
        (rarity or "common").lower().replace(" ", "_"),
        (50, 100))
    return f"{lo:,}–{hi:,} gp"


# --------------------------------------------------------------------- #
# Spellcasting services — DMG p. 159 + community-standard fees
# --------------------------------------------------------------------- #
# Each entry: gp cost (does not include material components the caster
# must supply).
SPELLCASTING_SERVICE_PRICE: Dict[str, int] = {
    # Cantrips
    "Light":                       5,
    "Mending":                     10,
    "Guidance":                    10,
    # 1st level
    "Cure Wounds":                 10,
    "Healing Word":                10,
    "Bless":                       10,
    "Detect Magic":                20,
    "Identify":                    20,    # +100 gp material
    "Comprehend Languages":        20,
    "Purify Food and Drink":       10,
    # 2nd level
    "Lesser Restoration":          40,
    "Augury":                      40,    # +25 gp material
    "Calm Emotions":               40,
    "Zone of Truth":               40,
    "See Invisibility":            40,
    # 3rd level
    "Speak with Dead":             90,
    "Remove Curse":                90,
    "Tongues":                     90,
    "Revivify":                    100,   # +300 gp diamond
    "Water Breathing":             90,
    # 4th level
    "Divination":                  210,   # +25 gp material
    "Death Ward":                  240,
    # 5th level
    "Greater Restoration":         450,   # +100 gp diamond
    "Raise Dead":                  1_250, # +500 gp diamond
    "Scrying":                     450,   # +1000 gp focus
    "Commune":                     400,
    # 6th level
    "Heal":                        750,
    "True Seeing":                 800,   # +25 gp dust
    "Find the Path":               700,
    # 7th level
    "Resurrection":                3_000, # +1000 gp diamond
    "Plane Shift":                 2_500,
    "Teleport":                    1_800,
    # 8th level
    "Mind Blank":                  4_500,
    # 9th level
    "True Resurrection":           20_000,# +25k gp diamond
    "Wish":                        50_000,
}


def service_price(spell_name: str) -> Optional[int]:
    return SPELLCASTING_SERVICE_PRICE.get(spell_name)


def services_by_level() -> Dict[int, List[Tuple[str, int]]]:
    """Group :data:`SPELLCASTING_SERVICE_PRICE` by spell level (for the
    library / temple price-board UI)."""
    try:
        from data.spells import _spells
    except Exception:  # pragma: no cover
        _spells = {}
    out: Dict[int, List[Tuple[str, int]]] = {}
    for nm, gp in SPELLCASTING_SERVICE_PRICE.items():
        lvl = 0
        info = _spells.get(nm)
        if info is not None:
            lvl = int(getattr(info, "level", 0) or 0)
        out.setdefault(lvl, []).append((nm, gp))
    for lvl in out:
        out[lvl].sort(key=lambda kv: kv[1])
    return out


# --------------------------------------------------------------------- #
# Adventurer-gear bundles (PHB starting equipment, condensed)
# --------------------------------------------------------------------- #
# Each bundle: a list of (item_name, qty) tuples — used by the
# shop-preset library to drop a "Lisää PHB-valikoima" inventory.
PHB_BUNDLES: Dict[str, List[Tuple[str, int]]] = {
    "explorer_pack": [
        ("Backpack", 1), ("Bedroll", 1), ("Mess Kit", 1),
        ("Tinderbox", 1), ("Torch", 10), ("Rations (1 day)", 10),
        ("Waterskin", 1), ("Rope (50 ft)", 1),
    ],
    "burglar_pack": [
        ("Backpack", 1), ("Crowbar", 1), ("Bell", 1),
        ("Candle", 5), ("Tinderbox", 1), ("Ball Bearings (bag)", 1),
        ("Rope (50 ft)", 1),
    ],
    "dungeoneer_pack": [
        ("Backpack", 1), ("Crowbar", 1), ("Hammer", 1),
        ("Piton (10)", 1), ("Torch", 10), ("Tinderbox", 1),
        ("Rations (1 day)", 10), ("Waterskin", 1),
        ("Rope (50 ft)", 1),
    ],
    "priest_pack": [
        ("Backpack", 1), ("Blanket", 1), ("Candle", 10),
        ("Tinderbox", 1), ("Alms Box", 1),
        ("Censer", 1), ("Vestments", 1),
        ("Rations (1 day)", 2), ("Waterskin", 1),
    ],
    "scholar_pack": [
        ("Backpack", 1), ("Book", 1), ("Ink (1 oz)", 1),
        ("Quill", 1), ("Parchment (1 sheet)", 10),
        ("Bag of Sand (small)", 1), ("Knife (small)", 1),
    ],
}


def list_phb_bundles() -> List[str]:
    return sorted(PHB_BUNDLES.keys())


def bundle_total_gp(bundle_key: str) -> float:
    """Total PHB price of the bundle (used by the UI to label the
    button)."""
    from data.shop_catalog import get_item_price
    items = PHB_BUNDLES.get(bundle_key, [])
    return sum(get_item_price(name) * qty for name, qty in items)
