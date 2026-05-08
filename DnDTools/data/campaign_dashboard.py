"""Campaign overview dashboard helper.

Aggregates the most-asked campaign-state numbers into a single
dataclass the DM can render at a glance:

  * Party size + total HP / max HP
  * Total party gold (shared + per-PC)
  * Active vs total NPC counts
  * Shop / service / quest totals
  * Active vs completed quest counts
  * Current area name + town summary

Pure logic; no pygame.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from data.campaign import Campaign
from data.world import World
from data.town_economy import town_summary, TownSummary


@dataclass
class CampaignOverview:
    party_size: int = 0
    party_active: int = 0
    party_total_hp: int = 0
    party_total_max_hp: int = 0
    party_total_exhaustion: int = 0
    party_gold_shared: float = 0.0
    party_gold_per_pc: float = 0.0
    party_inventory_size: int = 0

    npc_total: int = 0
    npc_alive: int = 0
    location_total: int = 0
    location_settlements: int = 0

    shop_total: int = 0
    service_total: int = 0

    quest_total: int = 0
    quest_active: int = 0
    quest_completed: int = 0

    current_area: str = ""
    current_area_summary: Optional[TownSummary] = None

    encounters_total: int = 0
    encounters_completed: int = 0

    session_number: int = 0
    time_of_day: str = ""

    headlines: List[str] = field(default_factory=list)


_SETTLEMENT_KINDS = {"capital", "city", "town", "village", "fort",
                       "kingdom", "country", "stronghold", "outpost",
                       "hamlet"}


def build_overview(campaign: Campaign,
                      world: Optional[World] = None) -> CampaignOverview:
    """Assemble a :class:`CampaignOverview`. ``world`` defaults to the
    campaign's loaded World when reachable."""
    o = CampaignOverview()
    party = campaign.party or []
    o.party_size = len(party)
    o.party_active = sum(1 for m in party if getattr(m, "active", True))
    for m in party:
        hd = m.hero_data or {}
        max_hp = int(hd.get("hit_points", 0)) or 0
        cur = int(m.current_hp) if (
            getattr(m, "current_hp", -1) is not None
            and m.current_hp >= 0) else max_hp
        o.party_total_max_hp += max_hp
        o.party_total_hp += cur
        o.party_total_exhaustion += int(getattr(m, "exhaustion", 0) or 0)
        o.party_gold_per_pc += float(getattr(m, "gold", 0.0) or 0.0)
    o.party_gold_shared = float(getattr(campaign, "party_gold", 0.0) or 0.0)
    o.party_inventory_size = len(getattr(campaign, "party_inventory",
                                            []) or [])
    o.session_number = int(getattr(campaign, "session_number", 0) or 0)
    o.time_of_day = getattr(campaign, "time_of_day", "") or ""
    o.encounters_total = len(getattr(campaign, "encounters", []) or [])
    o.encounters_completed = sum(
        1 for e in (campaign.encounters or [])
        if getattr(e, "completed", False)
    )

    if world is not None:
        o.npc_total = len(world.npcs)
        o.npc_alive = sum(
            1 for n in world.npcs.values()
            if getattr(n, "alive", True)
        )
        o.location_total = len(world.locations)
        o.location_settlements = sum(
            1 for l in world.locations.values()
            if (l.location_type or "").lower() in _SETTLEMENT_KINDS
        )
        o.shop_total = len(getattr(world, "shops", {}) or {})
        o.service_total = len(getattr(world, "services", {}) or {})
        o.quest_total = len(world.quests)
        o.quest_active = sum(
            1 for q in world.quests.values()
            if (getattr(q, "status", "") or "").lower()
            in ("active", "not_started", "")
        )
        o.quest_completed = sum(
            1 for q in world.quests.values()
            if (getattr(q, "status", "") or "").lower() == "completed"
        )

    o.current_area = getattr(campaign, "current_area", "") or ""
    if world is not None and o.current_area:
        for lid, loc in world.locations.items():
            if loc.name == o.current_area:
                o.current_area_summary = town_summary(world, lid)
                break

    o.headlines = _headlines(o)
    return o


def _headlines(o: CampaignOverview) -> List[str]:
    """Short list of one-line callouts the DM should know now."""
    out: List[str] = []
    if o.party_total_max_hp > 0:
        ratio = o.party_total_hp / max(1, o.party_total_max_hp)
        if ratio < 0.4:
            out.append(
                f"Party HP critical: "
                f"{o.party_total_hp}/{o.party_total_max_hp}"
            )
        elif ratio < 0.7:
            out.append(
                f"Party wounded: "
                f"{o.party_total_hp}/{o.party_total_max_hp}"
            )
    if o.party_total_exhaustion >= 2:
        out.append(f"Exhaustion accumulating ({o.party_total_exhaustion})")
    if o.quest_active > 0:
        out.append(f"{o.quest_active} active quest"
                    f"{'s' if o.quest_active != 1 else ''}")
    if o.encounters_total and o.encounters_completed < o.encounters_total:
        remaining = o.encounters_total - o.encounters_completed
        out.append(f"{remaining} encounter"
                    f"{'s' if remaining != 1 else ''} prepared but unrun")
    if o.npc_total >= 50:
        out.append(f"NPC roster: {o.npc_total}")
    if o.party_inventory_size >= 5:
        out.append(f"{o.party_inventory_size} items in shared inventory")
    return out
