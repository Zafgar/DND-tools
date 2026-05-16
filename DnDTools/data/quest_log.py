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
