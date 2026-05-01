"""Town economy + relationship + town-summary helpers.

Pure logic, no pygame. Three loosely-connected concerns the campaign
manager UI needs to talk to:

1. **Buy / sell** (Phase 14b) — moves an item from a Shop's inventory
   to the party (decrementing stack, debiting party gold, crediting
   shop gold) and the reverse for sells.

2. **Relationship matrix** (Phase 14c) — every NPC has a set of
   per-PC ``NPCRelationship`` entries. We expose helpers to fetch,
   set, +/- the attitude score, and bulk-list "everyone who
   feels X about hero Y".

3. **Town summary** (Phase 14d) — given a ``location_id``, return all
   the world data attached to it (NPCs, shops, services, child
   locations) so the town drill-down view can render it without
   re-querying every dict every frame.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from data.world import (
    World, Location, NPC, NPCRelationship, Shop, ShopItem, Service,
)


# --------------------------------------------------------------------- #
# Buy / sell
# --------------------------------------------------------------------- #
@dataclass
class TransactionResult:
    """Outcome of a buy / sell call."""
    success: bool
    reason: str = ""
    item_name: str = ""
    quantity: int = 0
    price_gp: float = 0.0


def buy_from_shop(shop: Shop, item_name: str, *,
                    quantity: int = 1,
                    party_gold: float = 0.0) -> TransactionResult:
    """Buy ``quantity`` of ``item_name`` from ``shop`` if the party
    can afford it and stock is available.

    Caller is responsible for deducting ``result.price_gp`` from the
    party's gold pool — kept out of this helper so it works with any
    party-gold representation.
    """
    if quantity <= 0:
        return TransactionResult(False, "quantity must be positive",
                                  item_name=item_name)
    item = _find_item(shop, item_name)
    if item is None:
        return TransactionResult(False, "item not in stock",
                                  item_name=item_name)
    if item.quantity != -1 and item.quantity < quantity:
        return TransactionResult(False, "insufficient stock",
                                  item_name=item_name,
                                  quantity=item.quantity)
    unit = (item.current_price_gp
             if item.current_price_gp > 0
             else item.base_price_gp)
    total = unit * quantity * max(0.0, shop.sell_markup or 1.0)
    if party_gold < total:
        return TransactionResult(False, "party can't afford",
                                  item_name=item_name,
                                  quantity=quantity, price_gp=total)
    if item.quantity != -1:
        item.quantity -= quantity
    shop.gold = max(0.0, shop.gold + total)
    return TransactionResult(True, "ok", item_name=item_name,
                              quantity=quantity, price_gp=total)


def sell_to_shop(shop: Shop, item_name: str, *,
                   quantity: int = 1,
                   base_price_gp: float = 0.0) -> TransactionResult:
    """Sell ``quantity`` of ``item_name`` to ``shop``. The shop pays
    ``base_price_gp * quantity * shop.buy_markup`` from its gold and
    adds the items to its inventory."""
    if quantity <= 0:
        return TransactionResult(False, "quantity must be positive",
                                  item_name=item_name)
    payout = max(0.0, base_price_gp * quantity * (shop.buy_markup or 0.5))
    if shop.gold < payout:
        return TransactionResult(False, "shop can't afford",
                                  item_name=item_name,
                                  quantity=quantity,
                                  price_gp=payout)
    shop.gold -= payout
    item = _find_item(shop, item_name)
    if item is None:
        shop.inventory.append(ShopItem(
            item_name=item_name,
            base_price_gp=base_price_gp,
            current_price_gp=base_price_gp,
            quantity=quantity,
        ))
    else:
        if item.quantity == -1:
            pass  # unlimited stock — selling adds no extra
        else:
            item.quantity += quantity
    return TransactionResult(True, "ok", item_name=item_name,
                              quantity=quantity, price_gp=payout)


def restock_item(shop: Shop, item_name: str, *,
                   quantity: int = 1,
                   base_price_gp: Optional[float] = None) -> bool:
    """Top-up a shop's stock without paying gold (DM bookkeeping)."""
    item = _find_item(shop, item_name)
    if item is None:
        if base_price_gp is None:
            base_price_gp = 0.0
        shop.inventory.append(ShopItem(
            item_name=item_name,
            base_price_gp=base_price_gp,
            current_price_gp=base_price_gp,
            quantity=quantity,
        ))
        return True
    if item.quantity == -1:
        return True
    item.quantity += quantity
    return True


def _find_item(shop: Shop, item_name: str) -> Optional[ShopItem]:
    key = item_name.strip().lower()
    for it in shop.inventory:
        if it.item_name.lower() == key:
            return it
    return None


# --------------------------------------------------------------------- #
# Relationships
# --------------------------------------------------------------------- #
ATTITUDES = ("hostile", "unfriendly", "neutral", "friendly", "allied")
_ATTITUDE_SCORE = {
    "hostile":    -2,
    "unfriendly": -1,
    "neutral":     0,
    "friendly":   +1,
    "allied":     +2,
}


def attitude_score(attitude: str) -> int:
    """Numeric -2..+2 from the attitude string. Unknown → 0."""
    return _ATTITUDE_SCORE.get((attitude or "neutral").lower(), 0)


def attitude_from_score(score: int) -> str:
    """Inverse: clamp + map back to canonical attitude."""
    score = max(-2, min(2, int(score)))
    for name, val in _ATTITUDE_SCORE.items():
        if val == score:
            return name
    return "neutral"


def get_relationship(npc: NPC,
                       hero_name: str) -> Optional[NPCRelationship]:
    """Find ``npc``'s relationship row for ``hero_name``."""
    if not hero_name:
        return None
    key = hero_name.strip().lower()
    for r in getattr(npc, "relationships", []) or []:
        if r.hero_name.lower() == key:
            return r
    return None


def set_attitude(npc: NPC, hero_name: str, attitude: str,
                   notes: str = "") -> NPCRelationship:
    """Upsert ``npc``'s relationship row for ``hero_name``."""
    if not hasattr(npc, "relationships") or npc.relationships is None:
        npc.relationships = []
    if attitude not in ATTITUDES:
        attitude = "neutral"
    existing = get_relationship(npc, hero_name)
    if existing is None:
        existing = NPCRelationship(hero_name=hero_name,
                                     attitude=attitude,
                                     notes=notes)
        npc.relationships.append(existing)
    else:
        existing.attitude = attitude
        if notes:
            existing.notes = notes
    return existing


def adjust_attitude(npc: NPC, hero_name: str, delta: int,
                      append_note: str = "") -> NPCRelationship:
    """Bump or drop the attitude by ``delta`` steps, clamped to
    -2..+2. Optionally append a note."""
    rel = get_relationship(npc, hero_name)
    cur = attitude_score(rel.attitude) if rel else 0
    new_attitude = attitude_from_score(cur + delta)
    rel = set_attitude(npc, hero_name, new_attitude)
    if append_note:
        if rel.notes:
            rel.notes = rel.notes + " — " + append_note
        else:
            rel.notes = append_note
    return rel


def list_relationships_to_hero(world: World, hero_name: str
                                  ) -> List[Tuple[NPC, NPCRelationship]]:
    """Return every (npc, relationship) pair where the NPC has any
    note about ``hero_name``."""
    out = []
    for npc in world.npcs.values():
        rel = get_relationship(npc, hero_name)
        if rel is not None:
            out.append((npc, rel))
    return out


def list_relationships_of_npc(npc: NPC) -> List[NPCRelationship]:
    return list(getattr(npc, "relationships", []) or [])


# --------------------------------------------------------------------- #
# Town summary
# --------------------------------------------------------------------- #
@dataclass
class TownSummary:
    """Everything attached to one location, ready to render."""
    location: Location
    npcs: List[NPC] = field(default_factory=list)
    shops: List[Shop] = field(default_factory=list)
    services: List[Service] = field(default_factory=list)
    child_locations: List[Location] = field(default_factory=list)
    quest_count: int = 0


def town_summary(world: World,
                   location_id: str) -> Optional[TownSummary]:
    """Aggregate everything in ``world`` that points at the given
    location id."""
    if location_id not in world.locations:
        return None
    loc = world.locations[location_id]
    npcs = [n for n in world.npcs.values()
            if n.location_id == location_id]
    shops = [s for s in world.shops.values()
             if s.location_id == location_id]
    services = [s for s in world.services.values()
                if s.location_id == location_id]
    child_locs = [
        world.locations[cid]
        for cid in (loc.children_ids or [])
        if cid in world.locations
    ]
    quest_count = sum(
        1 for q in world.quests.values()
        if location_id in (q.location_ids or [])
    )
    return TownSummary(
        location=loc,
        npcs=sorted(npcs, key=lambda n: n.name.lower()),
        shops=sorted(shops, key=lambda s: s.name.lower()),
        services=sorted(services, key=lambda s: s.name.lower()),
        child_locations=sorted(child_locs, key=lambda l: l.name.lower()),
        quest_count=quest_count,
    )
