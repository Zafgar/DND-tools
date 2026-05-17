"""Quest log helpers — append events, query reverse links, summarise.

The :class:`data.world.Quest` model carries:

  * ``giver_npc_id`` / ``turn_in_npc_id`` — single-NPC scalar links.
  * ``npc_ids`` / ``shop_ids`` / ``location_ids`` — many-to-many lists.
  * ``monster_names`` — free-form monster keywords for kill objectives.
  * ``log`` — a chronological :class:`QuestLogEntry` list.

This module sits between the campaign manager UI and that data:

  * :func:`log_event` — append a structured entry with the right
    ``kind`` field so the quest-log widget can colour-code it.
  * :func:`pay_npc` / :func:`receive_from_npc` / :func:`kill_monster`
    / :func:`deliver_item` — typed shortcuts that combine "do the
    thing" with "write a log line".
  * :func:`quests_for_npc` / :func:`quests_for_shop` /
    :func:`quests_for_location` — reverse lookups so the NPC and shop
    sheets can render "Active quests touching this entity".
  * :func:`reward_summary` / :func:`gold_movements` — quick rollups.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from data.world import Quest, QuestLogEntry, World


# --------------------------------------------------------------------- #
# Append helpers
# --------------------------------------------------------------------- #

def _now_stamp(campaign=None) -> str:
    """Return a session-relative timestamp, e.g. ``"S3 D5"``.  Falls
    back to wall-clock when no campaign is supplied."""
    if campaign is not None:
        try:
            return (f"S{int(getattr(campaign, 'session_number', 0) or 0)} "
                     f"D{int(getattr(campaign, 'in_game_day', 0) or 0)}")
        except Exception:
            pass
    import time
    return time.strftime("%Y-%m-%d %H:%M")


def log_event(quest: Quest, *, kind: str = "note",
               description: str = "",
               gold_delta: float = 0.0,
               npc_id: str = "", shop_id: str = "",
               monster_name: str = "", item_name: str = "",
               campaign=None) -> QuestLogEntry:
    entry = QuestLogEntry(
        timestamp=_now_stamp(campaign),
        kind=kind, description=description,
        gold_delta=float(gold_delta), npc_id=npc_id, shop_id=shop_id,
        monster_name=monster_name, item_name=item_name,
    )
    quest.log.append(entry)
    return entry


def pay_npc(quest: Quest, npc_id: str, amount_gp: float, *,
             description: str = "", campaign=None) -> QuestLogEntry:
    """Log "the party paid this NPC ``amount_gp`` gold for this quest"
    and (if the campaign is given) decrement ``Campaign.party_gold``."""
    if campaign is not None and hasattr(campaign, "party_gold"):
        campaign.party_gold = max(
            0.0, float(campaign.party_gold) - float(amount_gp))
    desc = description or f"Maksettu {amount_gp:.0f} gp NPC:lle."
    return log_event(quest, kind="transaction", description=desc,
                      gold_delta=-float(amount_gp), npc_id=npc_id,
                      campaign=campaign)


def receive_from_npc(quest: Quest, npc_id: str, amount_gp: float,
                       *, description: str = "",
                       campaign=None) -> QuestLogEntry:
    if campaign is not None and hasattr(campaign, "party_gold"):
        campaign.party_gold = float(campaign.party_gold) + float(amount_gp)
    desc = description or f"Saatu {amount_gp:.0f} gp NPC:ltä."
    return log_event(quest, kind="transaction", description=desc,
                      gold_delta=+float(amount_gp), npc_id=npc_id,
                      campaign=campaign)


def kill_monster(quest: Quest, monster_name: str, *,
                   description: str = "",
                   campaign=None) -> QuestLogEntry:
    desc = description or f"Tappio: {monster_name}."
    return log_event(quest, kind="kill", description=desc,
                      monster_name=monster_name, campaign=campaign)


def deliver_item(quest: Quest, item_name: str, *,
                   npc_id: str = "", description: str = "",
                   campaign=None) -> QuestLogEntry:
    desc = description or f"Toimitettu: {item_name}."
    return log_event(quest, kind="deliver", description=desc,
                      item_name=item_name, npc_id=npc_id,
                      campaign=campaign)


def complete_quest(quest: Quest, *, description: str = "",
                     campaign=None) -> QuestLogEntry:
    quest.status = "completed"
    quest.completed_date = _now_stamp(campaign)
    desc = description or "Tehtävä päätetty: valmis."
    return log_event(quest, kind="complete", description=desc,
                      campaign=campaign)


# --------------------------------------------------------------------- #
# Reverse lookups
# --------------------------------------------------------------------- #

def quests_for_npc(world: World, npc_id: str,
                    *, status: Optional[str] = None) -> List[Quest]:
    if not npc_id or not world:
        return []
    out: List[Quest] = []
    for q in world.quests.values():
        if status and q.status != status:
            continue
        if (npc_id == q.giver_npc_id
                or npc_id == q.turn_in_npc_id
                or npc_id in (q.npc_ids or [])
                or any(o.target_npc_id == npc_id
                        for o in (q.objectives or []))):
            out.append(q)
    return out


def quests_for_shop(world: World, shop_id: str,
                      *, status: Optional[str] = None) -> List[Quest]:
    if not shop_id or not world:
        return []
    out: List[Quest] = []
    for q in world.quests.values():
        if status and q.status != status:
            continue
        if shop_id in (q.shop_ids or []):
            out.append(q)
    return out


def quests_for_location(world: World, location_id: str,
                          *, status: Optional[str] = None
                          ) -> List[Quest]:
    if not location_id or not world:
        return []
    out: List[Quest] = []
    for q in world.quests.values():
        if status and q.status != status:
            continue
        if (location_id in (q.location_ids or [])
                or location_id == q.map_pin_location_id
                or any(o.target_location_id == location_id
                        for o in (q.objectives or []))):
            out.append(q)
    return out


def quests_for_monster(world: World, monster_name: str,
                         *, status: Optional[str] = None
                         ) -> List[Quest]:
    if not monster_name or not world:
        return []
    needle = monster_name.lower()
    out: List[Quest] = []
    for q in world.quests.values():
        if status and q.status != status:
            continue
        if any(needle == m.lower()
                 for m in (q.monster_names or [])):
            out.append(q)
    return out


# --------------------------------------------------------------------- #
# Roll-ups
# --------------------------------------------------------------------- #

def gold_movements(quest: Quest) -> Dict[str, float]:
    """Return ``{"received": …, "paid": …, "net": …}`` from the
    chronological log."""
    rec = 0.0
    paid = 0.0
    for e in quest.log:
        if e.gold_delta > 0:
            rec += e.gold_delta
        elif e.gold_delta < 0:
            paid += -e.gold_delta
    return {"received": rec, "paid": paid, "net": rec - paid}


def reward_summary(quest: Quest) -> str:
    """Human-readable reward line for the quest list row."""
    bits: List[str] = []
    if quest.reward_xp:
        bits.append(f"{int(quest.reward_xp)} XP")
    if quest.reward_gold:
        bits.append(f"{float(quest.reward_gold):.0f} gp")
    if quest.reward_items:
        first = quest.reward_items[0]
        if len(quest.reward_items) > 1:
            first += f" +{len(quest.reward_items) - 1}"
        bits.append(first)
    return "  ·  ".join(bits) if bits else "—"


def objective_progress(quest: Quest) -> str:
    objs = quest.objectives or []
    if not objs:
        return ""
    done = sum(1 for o in objs if o.completed)
    return f"{done}/{len(objs)}"


# --------------------------------------------------------------------- #
# Phase 27a — map-pin auto-overlay support
# --------------------------------------------------------------------- #

def quests_pinned_at(world: World, location_id: str,
                      *, statuses=("active", "on_hold")) -> List[Quest]:
    """Return every quest whose ``map_pin_location_id`` matches the
    given location and whose status is one we render on the map.

    The world-map view calls this for each visible location so it can
    paint a small banner next to the node.
    """
    if not location_id or not world:
        return []
    out: List[Quest] = []
    for q in world.quests.values():
        if statuses and q.status not in statuses:
            continue
        if q.map_pin_location_id == location_id:
            out.append(q)
    return out


# --------------------------------------------------------------------- #
# Phase 27b — shop commission helpers
# --------------------------------------------------------------------- #

def commission_party(shop, item_name: str, price_gp: float,
                       *, deposit_gp: float = 0.0,
                       due_in_days: int = 0,
                       description: str = "",
                       linked_quest=None,
                       campaign=None):
    """Record a party commission with this shop and (optionally) log a
    transaction line on a linked quest.  Returns the new
    :class:`ShopCommission`.
    """
    from data.world import ShopCommission
    cid = f"comm_{len(shop.commissions) + 1}"
    while any(c.id == cid for c in shop.commissions):
        cid = f"{cid}_x"
    c = ShopCommission(
        id=cid, item_name=item_name, price_gp=float(price_gp),
        deposit_paid_gp=float(deposit_gp),
        due_in_days=int(due_in_days),
        description=description, customer_is_party=True,
        linked_quest_id=getattr(linked_quest, "id", "") or "",
    )
    shop.commissions.append(c)
    if linked_quest is not None and deposit_gp > 0:
        pay_npc(linked_quest, shop.owner_npc_id, deposit_gp,
                  description=f"Käsiraha: {item_name}",
                  campaign=campaign)
        if shop.id and shop.id not in linked_quest.shop_ids:
            linked_quest.shop_ids.append(shop.id)
    return c


def mark_commission_ready(shop, commission_id: str,
                            *, linked_quest=None,
                            campaign=None) -> bool:
    """Flip a commission to ``"ready"``.  When a linked quest is given,
    drop a log line so the DM remembers."""
    for c in shop.commissions:
        if c.id == commission_id:
            c.status = "ready"
            if linked_quest is not None:
                log_event(linked_quest, kind="note",
                            description=f"{c.item_name} valmis "
                                         f"{shop.name}-kaupasta.",
                            shop_id=shop.id, item_name=c.item_name,
                            campaign=campaign)
            return True
    return False


def deliver_commission(shop, commission_id: str,
                         *, linked_quest=None,
                         campaign=None) -> bool:
    """Mark a commission delivered and (when a quest is linked) charge
    the remainder of the price to the party.
    """
    for c in shop.commissions:
        if c.id != commission_id:
            continue
        remainder = max(0.0, c.price_gp - c.deposit_paid_gp)
        c.status = "delivered"
        c.deposit_paid_gp = c.price_gp
        if linked_quest is not None:
            if remainder > 0:
                pay_npc(linked_quest, shop.owner_npc_id, remainder,
                          description=f"Maksu lopusta: {c.item_name}",
                          campaign=campaign)
            deliver_item(linked_quest, c.item_name,
                            description=f"Vastaanotettu {c.item_name} "
                                         f"({shop.name}).",
                            campaign=campaign)
        return True
    return False


def cancel_commission(shop, commission_id: str) -> bool:
    for c in shop.commissions:
        if c.id == commission_id:
            c.status = "cancelled"
            return True
    return False


def active_commissions(shop) -> List:
    return [c for c in shop.commissions
             if c.status in ("in_progress", "ready")]


def map_pin_colour_for_quest(quest: Quest) -> tuple:
    """Banner colour by priority — urgent reds, high yellows, the rest
    grey-blue.  Returned as a 3-tuple suitable for pygame."""
    pri = (getattr(quest, "priority", "normal") or "normal").lower()
    if pri == "urgent":
        return (220, 80, 70)
    if pri == "high":
        return (220, 170, 70)
    if pri == "low":
        return (120, 130, 140)
    return (110, 180, 240)
