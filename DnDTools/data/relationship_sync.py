"""Dual-relationship sync — keep NPC↔Hero attitudes consistent on
both sides without forcing the DM to update each independently.

Two sources of truth, deliberately:

  * ``NPC.relationships`` — list of :class:`NPCRelationship` rows
    (one per PC the NPC has any opinion about). Lives in the world.
  * ``PartyMember.relationships`` — list of :class:`HeroRelationship`
    rows the PC keeps about NPCs (and other PCs).

When the DM updates one direction (typically the NPC side via the
relationship matrix widget), the other direction needs to follow
so the campaign manager's hero panel doesn't drift out of date.
This module exposes ``sync_attitude_both_ways`` and a campaign-
wide ``rebuild_dual_relationships`` for one-shot reconciliation
after data import.

Pure logic; no pygame.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from data.campaign import Campaign, PartyMember, HeroRelationship
from data.world import World, NPC, NPCRelationship
from data.town_economy import (
    set_attitude as set_npc_attitude,
    get_relationship as get_npc_relationship,
    ATTITUDES,
)


def _find_party_member(campaign: Campaign,
                          hero_name: str) -> Optional[PartyMember]:
    if not hero_name:
        return None
    key = hero_name.strip().lower()
    for member in (campaign.party or []):
        hd = getattr(member, "hero_data", {}) or {}
        if (hd.get("name", "") or "").lower() == key:
            return member
    return None


def _get_hero_rel(member: PartyMember,
                    target_id: str,
                    target_name: str = "") -> Optional[HeroRelationship]:
    if not hasattr(member, "relationships") or member.relationships is None:
        return None
    for r in member.relationships:
        if target_id and r.target_id == target_id:
            return r
        if target_name and r.target_name.lower() == target_name.lower():
            return r
    return None


def set_hero_relationship(member: PartyMember, *,
                            target_id: str = "",
                            target_name: str = "",
                            attitude: str = "neutral",
                            target_type: str = "npc",
                            description: str = "",
                            notes: str = "") -> HeroRelationship:
    """Upsert a hero's relationship row to (target_id, target_name).
    Either id or name (preferably both) must be supplied."""
    if not hasattr(member, "relationships") or member.relationships is None:
        member.relationships = []
    if attitude not in ATTITUDES and attitude not in (
            "romantic", "rival"):
        attitude = "neutral"
    existing = _get_hero_rel(member, target_id, target_name)
    if existing is None:
        existing = HeroRelationship(
            target_name=target_name or "",
            target_id=target_id or "",
            target_type=target_type,
            attitude=attitude,
            description=description,
            notes=notes,
        )
        member.relationships.append(existing)
        return existing
    existing.attitude = attitude
    if target_id:
        existing.target_id = target_id
    if target_name:
        existing.target_name = target_name
    if description:
        existing.description = description
    if notes:
        existing.notes = notes
    return existing


def sync_attitude_both_ways(campaign: Campaign, world: World, *,
                               npc_id: str, hero_name: str,
                               attitude: str,
                               notes: str = "") -> dict:
    """Authoritative call: set ``attitude`` on both sides.

    NPC side: ``set_attitude`` upserts the NPCRelationship row.
    Hero side: matching PartyMember gets / updates a HeroRelationship
    row pointing at the NPC.

    Returns a small dict telling the caller whether both sides were
    found / updated.
    """
    info = {"npc_updated": False, "hero_updated": False,
            "missing_party_member": False, "missing_npc": False}
    npc = world.npcs.get(npc_id)
    if npc is None:
        info["missing_npc"] = True
        return info

    set_npc_attitude(npc, hero_name, attitude, notes=notes)
    info["npc_updated"] = True

    member = _find_party_member(campaign, hero_name)
    if member is None:
        info["missing_party_member"] = True
        return info
    set_hero_relationship(
        member,
        target_id=npc_id,
        target_name=npc.name,
        attitude=attitude,
        target_type="npc",
        notes=notes,
    )
    info["hero_updated"] = True
    return info


# --------------------------------------------------------------------- #
# One-shot reconciliation
# --------------------------------------------------------------------- #
def rebuild_dual_relationships(campaign: Campaign,
                                  world: World) -> dict:
    """Walk every NPC's ``relationships`` list and mirror each row
    onto the matching PartyMember as a HeroRelationship. Useful
    after a bulk import where only one side was populated.

    Returns a count summary.
    """
    rep = {"npc_to_hero_synced": 0, "hero_to_npc_synced": 0,
            "skipped_no_member": 0, "skipped_no_npc": 0}
    member_by_lname = {}
    for m in (campaign.party or []):
        nm = (m.hero_data or {}).get("name", "") or ""
        if nm:
            member_by_lname[nm.lower()] = m

    # NPC → Hero
    for npc in world.npcs.values():
        for r in (getattr(npc, "relationships", []) or []):
            member = member_by_lname.get(r.hero_name.strip().lower())
            if member is None:
                rep["skipped_no_member"] += 1
                continue
            set_hero_relationship(
                member,
                target_id=npc.id,
                target_name=npc.name,
                attitude=r.attitude,
                target_type="npc",
                notes=r.notes,
            )
            rep["npc_to_hero_synced"] += 1

    # Hero → NPC (catch any HeroRelationship rows that weren't
    # represented on the NPC side)
    npc_by_id = {nid: n for nid, n in world.npcs.items()}
    npc_by_lname = {n.name.lower(): n for n in world.npcs.values()}
    for member in (campaign.party or []):
        nm = (member.hero_data or {}).get("name", "") or ""
        for r in (getattr(member, "relationships", []) or []):
            if (getattr(r, "target_type", "npc") or "npc") != "npc":
                continue
            npc = (npc_by_id.get(r.target_id) if r.target_id
                    else npc_by_lname.get(r.target_name.lower()))
            if npc is None:
                rep["skipped_no_npc"] += 1
                continue
            existing = get_npc_relationship(npc, nm)
            if existing is None:
                set_npc_attitude(npc, nm, r.attitude, r.notes)
                rep["hero_to_npc_synced"] += 1
    return rep


# --------------------------------------------------------------------- #
# Read helpers used by UI panels
# --------------------------------------------------------------------- #
def hero_attitude_to_npc(member: PartyMember,
                            npc_id: str = "",
                            npc_name: str = "") -> str:
    """Return the hero's recorded attitude to ``npc_id`` / ``npc_name``,
    or 'neutral' if no row exists."""
    r = _get_hero_rel(member, npc_id, npc_name)
    return r.attitude if r else "neutral"


def list_npc_attitudes_for_hero(world: World,
                                   hero_name: str
                                   ) -> List[Tuple[NPC, str]]:
    """Every NPC with a recorded attitude toward ``hero_name``."""
    out = []
    key = (hero_name or "").strip().lower()
    for npc in world.npcs.values():
        for r in (getattr(npc, "relationships", []) or []):
            if r.hero_name.lower() == key:
                out.append((npc, r.attitude))
                break
    return out
