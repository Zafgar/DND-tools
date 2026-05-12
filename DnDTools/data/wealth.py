"""Aggregate wealth helpers — bridge between :mod:`data.currency`,
:mod:`data.world` NPCs/Shops, and :mod:`data.kingdoms` cities.

The campaign manager needs three views:

  * **Per actor** — what coins does this NPC / shopkeeper carry?
  * **Per city** — sum of every NPC, shop, bank holding and the city's
    crown treasury, expressed in gold.
  * **Per kingdom** — sum across all cities + kingdom's own treasury.

The legacy ``NPC.gold`` / ``Shop.gold`` fields stay as the simple float
view. When ``.wealth`` (a dict of coin counts) is empty, the float is
treated as the source of truth; when ``.wealth`` is populated, it wins
and overrides the float.

Pure logic, no pygame.
"""
from __future__ import annotations

from typing import List, Optional, Tuple

from data.currency import Coins


# ----------------------------------------------------------------------
# Per-actor coin readers
# ----------------------------------------------------------------------

def _coins_from_breakdown(breakdown: dict) -> Coins:
    """Build a :class:`Coins` from a stored ``{"pp": 1, "gp": 2, …}`` dict."""
    if not breakdown:
        return Coins()
    return Coins(
        cp=int(breakdown.get("cp", 0) or 0),
        sp=int(breakdown.get("sp", 0) or 0),
        ep=int(breakdown.get("ep", 0) or 0),
        gp=int(breakdown.get("gp", 0) or 0),
        pp=int(breakdown.get("pp", 0) or 0),
    )


def _breakdown_from_coins(c: Coins) -> dict:
    return {
        "pp": int(c.pp), "gp": int(c.gp), "ep": int(c.ep),
        "sp": int(c.sp), "cp": int(c.cp),
    }


def npc_coins(npc) -> Coins:
    """Return the NPC's wealth as :class:`Coins`. Falls back to
    converting the legacy ``gold`` float when no breakdown is set."""
    breakdown = getattr(npc, "wealth", None) or {}
    if breakdown:
        return _coins_from_breakdown(breakdown)
    g = float(getattr(npc, "gold", 0.0) or 0.0)
    return Coins.from_gp(g)


def set_npc_coins(npc, coins: Coins) -> None:
    """Store ``coins`` on the NPC and keep ``.gold`` in sync as a mirror."""
    if not hasattr(npc, "wealth"):
        try:
            setattr(npc, "wealth", {})
        except Exception:
            return
    npc.wealth = _breakdown_from_coins(coins)
    npc.gold = coins.total_gp()


def shop_coins(shop) -> Coins:
    breakdown = getattr(shop, "wealth", None) or {}
    if breakdown:
        return _coins_from_breakdown(breakdown)
    return Coins.from_gp(float(getattr(shop, "gold", 0.0) or 0.0))


def set_shop_coins(shop, coins: Coins) -> None:
    if not hasattr(shop, "wealth"):
        try:
            setattr(shop, "wealth", {})
        except Exception:
            return
    shop.wealth = _breakdown_from_coins(coins)
    shop.gold = coins.total_gp()


# ----------------------------------------------------------------------
# Per-city collectors
# ----------------------------------------------------------------------

def npcs_in_location(world, location_id: str) -> List:
    if not world or not location_id:
        return []
    return [n for n in world.npcs.values()
             if getattr(n, "active", True)
             and getattr(n, "location_id", "") == location_id]


def shops_in_location(world, location_id: str) -> List:
    if not world or not location_id:
        return []
    return [s for s in getattr(world, "shops", {}).values()
             if getattr(s, "location_id", "") == location_id]


def banks_in_location(world, location_id: str) -> List:
    return [s for s in shops_in_location(world, location_id)
             if getattr(s, "is_bank", False)]


# ----------------------------------------------------------------------
# City / kingdom totals
# ----------------------------------------------------------------------

def city_npc_wealth_gp(world, location_id: str) -> float:
    return sum(npc_coins(n).total_gp()
                for n in npcs_in_location(world, location_id))


def city_shop_wealth_gp(world, location_id: str) -> float:
    return sum(shop_coins(s).total_gp()
                for s in shops_in_location(world, location_id))


def city_bank_holdings_gp(world, location_id: str) -> float:
    return sum(float(getattr(s, "bank_holdings_gp", 0.0) or 0.0)
                for s in banks_in_location(world, location_id))


def city_total_wealth_gp(world, city) -> float:
    """Aggregate gold (in gp) attached to a city: crown treasury + every
    NPC, every shop, plus any customer deposits in city banks.

    ``city`` is a :class:`data.kingdoms.CityEntry` (uses its
    ``treasury_gp`` and ``location_id``).
    """
    if city is None:
        return 0.0
    location_id = getattr(city, "location_id", "") or ""
    total = float(getattr(city, "treasury_gp", 0.0) or 0.0)
    if world is not None and location_id:
        total += city_npc_wealth_gp(world, location_id)
        total += city_shop_wealth_gp(world, location_id)
        total += city_bank_holdings_gp(world, location_id)
    return total


def city_wealth_breakdown(world, city) -> dict:
    """Itemised breakdown for the navigator UI:
    ``{"crown": …, "npcs": …, "shops": …, "banks": …, "total": …}``."""
    if city is None:
        return {"crown": 0.0, "npcs": 0.0, "shops": 0.0,
                "banks": 0.0, "total": 0.0}
    location_id = getattr(city, "location_id", "") or ""
    crown = float(getattr(city, "treasury_gp", 0.0) or 0.0)
    if world is None or not location_id:
        return {"crown": crown, "npcs": 0.0, "shops": 0.0,
                "banks": 0.0, "total": crown}
    npcs = city_npc_wealth_gp(world, location_id)
    shops = city_shop_wealth_gp(world, location_id)
    banks = city_bank_holdings_gp(world, location_id)
    return {"crown": crown, "npcs": npcs, "shops": shops,
            "banks": banks, "total": crown + npcs + shops + banks}


def kingdom_total_wealth_gp(world, kingdom) -> float:
    """Sum of crown treasury + every city's full breakdown."""
    if kingdom is None:
        return 0.0
    total = float(getattr(kingdom, "treasury_gp", 0.0) or 0.0)
    for c in getattr(kingdom, "cities", []):
        total += city_total_wealth_gp(world, c)
    return total


def world_total_wealth_gp(world, campaign) -> float:
    from data.kingdoms import ensure_kingdoms_on_campaign
    return sum(kingdom_total_wealth_gp(world, k)
                for k in ensure_kingdoms_on_campaign(campaign))


# ----------------------------------------------------------------------
# Wealth-tier suggestions (auto-fill new NPCs with realistic coin piles)
# ----------------------------------------------------------------------

# PHB-inspired starting wealth bands — broad enough to give the UI a
# sensible default when the DM creates a new NPC at a given wealth
# level on a given location.  Values are in gp.
_WEALTH_TIER_GP = {
    "squalid":       0.5,
    "poor":          5.0,
    "modest":        25.0,
    "comfortable":   100.0,
    "wealthy":       500.0,
    "aristocratic":  2500.0,
}


def suggest_coins_for_wealth_tier(tier: str) -> Coins:
    """Return a normalised :class:`Coins` pile sized to ``tier``."""
    gp = _WEALTH_TIER_GP.get((tier or "").lower(), 25.0)
    return Coins.from_gp(gp)


def wealth_tiers() -> Tuple[str, ...]:
    return tuple(_WEALTH_TIER_GP.keys())
