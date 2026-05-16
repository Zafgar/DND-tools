"""Shop preset library — one-click pre-built inventories.

The campaign-manager Shop panel exposes a "Lisää PHB-valikoima"
button.  This module defines what gets dropped in based on the shop's
:attr:`shop_type` and the chosen preset key:

  * ``"basic"`` — small PHB starting inventory matching the type
    (blacksmith → daggers, hand axes, longswords; herbalist →
    antitoxin, healer's kit, poultices).
  * ``"stocked"`` — broader catalogue for tier-2+ shops.
  * ``"library_tier1"`` / ``"library_tier2"`` / ``"library_tier3"`` —
    scroll libraries with XGtE-priced spell scrolls (cantrip → 5th /
    6th / 9th level respectively).
  * ``"temple_services"`` — adds a list of :class:`Service` entries
    instead of inventory (lesser restoration, raise dead, …).

Each function returns a list of ``(item_name, quantity, price_gp)``
tuples — the campaign manager calls :func:`apply_preset_to_shop` to
merge them onto a Shop.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

from data.world import Shop, ShopItem
from data.shop_catalog import get_item_price


# --------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------- #

def _scroll_lines_through(top_level: int) -> List[Tuple[str, int, float]]:
    """Build a scroll library running from cantrips up to ``top_level``."""
    from data.price_book import scroll_centre_price
    from data.spells import _spells
    by_level: Dict[int, List[str]] = {}
    for nm, info in _spells.items():
        lvl = int(getattr(info, "level", 0) or 0)
        by_level.setdefault(lvl, []).append(nm)
    out: List[Tuple[str, int, float]] = []
    for lvl in range(0, top_level + 1):
        for nm in sorted(by_level.get(lvl, []))[:6]:
            out.append((f"Scroll of {nm}", 1,
                          float(scroll_centre_price(lvl))))
    return out


# --------------------------------------------------------------------- #
# Type-keyed presets — each value: {preset_key: builder_callable}
# --------------------------------------------------------------------- #

def _basic_blacksmith() -> List[Tuple[str, int, float]]:
    names = [
        ("Dagger", 6), ("Handaxe", 4), ("Mace", 3),
        ("Shortsword", 3), ("Longsword", 2), ("Warhammer", 2),
        ("Spear", 4), ("Shield", 4),
        ("Leather Armor", 2), ("Chain Shirt", 2),
    ]
    return [(n, q, get_item_price(n)) for n, q in names]


def _stocked_blacksmith() -> List[Tuple[str, int, float]]:
    names = [
        ("Greatsword", 2), ("Battleaxe", 3), ("Greataxe", 2),
        ("Halberd", 2), ("Glaive", 2), ("Pike", 2),
        ("Crossbow (Heavy)", 2), ("Crossbow Bolt (20)", 6),
        ("Chain Mail", 2), ("Splint", 1), ("Plate", 1),
    ]
    return _basic_blacksmith() + [
        (n, q, get_item_price(n)) for n, q in names
    ]


def _basic_general_store() -> List[Tuple[str, int, float]]:
    names = [
        ("Backpack", 4), ("Bedroll", 4), ("Rope (50 ft)", 6),
        ("Torch", 30), ("Rations (1 day)", 50), ("Waterskin", 5),
        ("Tinderbox", 3), ("Tent (Two-Person)", 2),
        ("Lantern (Hooded)", 3), ("Oil Flask", 12), ("Crowbar", 2),
        ("Grappling Hook", 3), ("Piton (10)", 4), ("Chain (10 ft)", 2),
        ("Mess Kit", 4), ("Mirror (Steel)", 2), ("Whetstone", 5),
        ("Pouch", 6), ("Sack", 6),
    ]
    return [(n, q, get_item_price(n)) for n, q in names]


def _basic_alchemist() -> List[Tuple[str, int, float]]:
    names = [
        ("Potion of Healing", 8), ("Antitoxin", 4),
        ("Acid (vial)", 4), ("Alchemist's Fire (flask)", 4),
        ("Holy Water (flask)", 2), ("Oil Flask", 6),
        ("Alchemist's Supplies", 1), ("Healer's Kit", 4),
    ]
    return [(n, q, get_item_price(n)) for n, q in names]


def _stocked_alchemist() -> List[Tuple[str, int, float]]:
    names = [
        ("Potion of Greater Healing", 4),
        ("Potion of Climbing", 2),
        ("Potion of Water Breathing", 1),
        ("Potion of Fire Breath", 1),
        ("Potion of Animal Friendship", 1),
        ("Potion of Mind Reading", 1),
    ]
    return _basic_alchemist() + [
        (n, q, get_item_price(n)) for n, q in names
    ]


def _basic_jeweler() -> List[Tuple[str, int, float]]:
    return [
        ("Silver Ring", 6, 25.0),
        ("Gold Ring", 4, 250.0),
        ("Silver Necklace", 4, 50.0),
        ("Gold Necklace", 2, 500.0),
        ("Gemstone (small)", 8, 100.0),
        ("Gemstone (large)", 2, 1_000.0),
        ("Jeweler's Tools", 1, 25.0),
    ]


def _basic_herbalist() -> List[Tuple[str, int, float]]:
    names = [
        ("Healer's Kit", 4), ("Antitoxin", 6),
        ("Herbalism Kit", 2), ("Potion of Healing", 6),
        ("Vial", 8), ("Soap", 6),
    ]
    return [(n, q, get_item_price(n)) for n, q in names]


def _basic_scribe() -> List[Tuple[str, int, float]]:
    names = [
        ("Ink (1 oz)", 10), ("Parchment (1 sheet)", 60),
        ("Quill", 12), ("Book", 4), ("Calligrapher's Supplies", 1),
        ("Map or Scroll Case", 6), ("Sealing Wax", 8),
    ]
    return [(n, q, get_item_price(n)) for n, q in names]


def _basic_temple() -> List[Tuple[str, int, float]]:
    # The temple stocks consumables; spellcasting services come via
    # :func:`temple_service_presets` below.
    return [
        ("Holy Water (flask)", 6, 25.0),
        ("Healer's Kit", 4, 5.0),
        ("Holy Symbol (wooden)", 4, 5.0),
        ("Holy Symbol (silvered)", 2, 25.0),
        ("Censer", 2, 5.0),
        ("Vestments", 4, 5.0),
    ]


# --------------------------------------------------------------------- #
# Scroll libraries — XGtE-priced
# --------------------------------------------------------------------- #
def _library_tier1() -> List[Tuple[str, int, float]]:
    return _scroll_lines_through(2)


def _library_tier2() -> List[Tuple[str, int, float]]:
    return _scroll_lines_through(5)


def _library_tier3() -> List[Tuple[str, int, float]]:
    return _scroll_lines_through(9)


# --------------------------------------------------------------------- #
# Preset registry
# --------------------------------------------------------------------- #
# Maps (shop_type, preset_key) → builder callable.  The first key in
# ``SHOP_PRESETS_BY_TYPE`` is the default for the type.
SHOP_PRESETS_BY_TYPE: Dict[str, Dict[str, callable]] = {
    "general_store": {
        "basic":   _basic_general_store,
        "stocked": lambda: _basic_general_store() + [
            ("Climber's Kit", 2, get_item_price("Climber's Kit")),
            ("Spyglass", 1, get_item_price("Spyglass")),
            ("Antitoxin", 4, get_item_price("Antitoxin")),
            ("Hunting Trap", 2, get_item_price("Hunting Trap")),
        ],
    },
    "blacksmith": {
        "basic":   _basic_blacksmith,
        "stocked": _stocked_blacksmith,
    },
    "armorer": {
        "basic": lambda: [
            (n, q, get_item_price(n))
            for n, q in [
                ("Leather Armor", 4), ("Studded Leather", 3),
                ("Chain Shirt", 3), ("Scale Mail", 2),
                ("Breastplate", 2), ("Half Plate", 1),
                ("Chain Mail", 2), ("Splint", 1), ("Plate", 1),
                ("Shield", 6),
            ]
        ],
    },
    "alchemist": {
        "basic":   _basic_alchemist,
        "stocked": _stocked_alchemist,
    },
    "jeweler": {
        "basic": _basic_jeweler,
    },
    "herbalist": {
        "basic": _basic_herbalist,
    },
    "scribe": {
        "basic":          _basic_scribe,
        "library_tier1":  _library_tier1,
        "library_tier2":  _library_tier2,
        "library_tier3":  _library_tier3,
    },
    "library": {
        "library_tier1": _library_tier1,
        "library_tier2": _library_tier2,
        "library_tier3": _library_tier3,
    },
    "magic_shop": {
        "basic": lambda: [
            ("Potion of Healing", 6, 50.0),
            ("Potion of Greater Healing", 3, 200.0),
            ("Spell Component Pouch", 4, 25.0),
            ("Arcane Focus (Crystal)", 2, 10.0),
            ("Arcane Focus (Orb)", 2, 20.0),
            ("Arcane Focus (Staff)", 2, 5.0),
            ("Druidic Focus (Wand)", 2, 10.0),
        ],
        "library_tier1": _library_tier1,
        "library_tier2": _library_tier2,
    },
    "tavern": {
        "basic": lambda: [
            ("Ale (gallon)", 30, 0.2),
            ("Wine (bottle)", 20, 2.0),
            ("Mead (pitcher)", 20, 1.0),
            ("Meal (squalid)", 30, 0.03),
            ("Meal (poor)", 30, 0.1),
            ("Meal (modest)", 20, 0.3),
            ("Meal (comfortable)", 10, 0.5),
            ("Room (modest, 1 night)", 8, 0.5),
            ("Room (comfortable, 1 night)", 4, 0.8),
            ("Stables (per night)", 6, 0.5),
        ],
    },
    "temple": {
        "basic": _basic_temple,
    },
}


def list_presets_for(shop_type: str) -> List[str]:
    return list(SHOP_PRESETS_BY_TYPE.get(shop_type, {}).keys())


def preset_items(shop_type: str, preset_key: str
                  ) -> List[Tuple[str, int, float]]:
    """Return the raw ``(name, qty, price_gp)`` tuples for a preset."""
    tbl = SHOP_PRESETS_BY_TYPE.get(shop_type, {})
    builder = tbl.get(preset_key)
    if builder is None:
        return []
    return list(builder())


def apply_preset_to_shop(shop: Shop, preset_key: str,
                          *, replace: bool = False) -> int:
    """Merge a preset into ``shop.inventory``.  Returns the number of
    rows added.  If ``replace`` is True, the shop's existing inventory
    is wiped first.

    Duplicate names are merged additively (stack count increases).
    """
    items = preset_items(shop.shop_type, preset_key)
    if not items:
        return 0
    if replace:
        shop.inventory = []
    existing_by_name = {it.item_name: it for it in shop.inventory}
    added = 0
    for name, qty, price in items:
        cur = existing_by_name.get(name)
        if cur is None:
            cur = ShopItem(item_name=name, base_price_gp=float(price),
                            current_price_gp=float(price),
                            quantity=int(qty))
            shop.inventory.append(cur)
            existing_by_name[name] = cur
            added += 1
        else:
            if cur.quantity == -1 or qty == -1:
                cur.quantity = -1
            else:
                cur.quantity = (cur.quantity or 0) + int(qty)
    return added


# --------------------------------------------------------------------- #
# Temple service presets — service rows, not shop items
# --------------------------------------------------------------------- #
def temple_service_presets() -> List[Tuple[str, int, str]]:
    """Return ``(name, gp_price, description)`` tuples for the standard
    temple spellcasting menu (lesser restoration, remove curse, raise
    dead, …).  Caller can create :class:`data.world.Service` entries
    from the result.
    """
    from data.price_book import SPELLCASTING_SERVICE_PRICE
    rows: List[Tuple[str, int, str]] = []
    for spell_name, gp in sorted(SPELLCASTING_SERVICE_PRICE.items(),
                                    key=lambda kv: kv[1]):
        rows.append((spell_name, gp,
                       f"Cast {spell_name} on behalf of customer."))
    return rows
