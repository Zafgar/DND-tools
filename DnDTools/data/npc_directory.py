"""Phase 39 — NPC search, link and inventory helpers.

Mid-to-late-game campaigns accumulate dozens of NPCs.  This module
gives the DM:

  * :func:`search_npcs` — multi-faceted full-text + filter search
    across the world (name, occupation, faction, race, location,
    organisation, tags, notes).
  * Link helpers — bidirectional NPC↔NPC relationships with a
    free-form note explaining the connection.
  * Inventory helpers — structured letters / keys / documents /
    trinkets on top of the legacy free-text ``inventory_items``.
  * Quick navigation — ``locate_npc(world, name_or_id)`` for
    "find that NPC the player mentioned".

Pure logic, no pygame.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from data.world import World, NPC


# --------------------------------------------------------------------- #
# Vocabulary
# --------------------------------------------------------------------- #

LINK_KINDS = [
    "rival", "mentor", "family", "ally", "subordinate", "patron",
    "protege", "lover", "enemy", "friend", "contact", "other",
]


INVENTORY_KINDS = [
    "letter", "key", "document", "trinket", "weapon", "armor",
    "potion", "scroll", "wand", "ring", "amulet", "coin_pouch",
    "tool", "other",
]


# --------------------------------------------------------------------- #
# Search
# --------------------------------------------------------------------- #

@dataclass
class NpcSearchHit:
    npc: NPC
    score: int = 0
    matched_fields: List[str] = field(default_factory=list)


def search_npcs(world: World, query: str = "", *,
                  location_id: str = "", faction: str = "",
                  organisation_key: str = "",
                  tags: Optional[List[str]] = None,
                  alive_only: bool = True,
                  active_only: bool = True,
                  campaign=None,
                  limit: int = 200) -> List[NpcSearchHit]:
    """Return NPCs matching the given filters, sorted by score.

    Free-text ``query`` is searched (case-insensitive) against name,
    occupation, faction, race, title, alignment, notes, backstory,
    appearance and tags.  Each hit field bumps the score, so the
    most specific matches sort first.

    ``organisation_key`` filters via :mod:`data.organizations` —
    must be a key like ``"brotherhood_of_glorious_sun"``.  Requires
    a campaign (so we can read its organisation list).
    """
    q = (query or "").strip().lower()
    tag_set = {t.lower() for t in (tags or [])}
    hits: List[NpcSearchHit] = []

    org_members: Set[str] = set()
    if organisation_key and campaign is not None:
        try:
            from data import organizations as orgs
            o = orgs.find_organisation(campaign, organisation_key)
            if o is not None:
                org_members = {m.npc_id for m in o.members
                                 if m.npc_id}
        except Exception:
            pass

    for npc in world.npcs.values():
        if alive_only and not npc.alive:
            continue
        if active_only and not npc.active:
            continue
        if location_id and npc.location_id != location_id:
            continue
        if faction and faction.lower() not in (npc.faction or "").lower():
            continue
        if organisation_key and npc.id not in org_members:
            continue
        if tag_set:
            npc_tags = {t.lower() for t in (npc.tags or [])}
            if not (tag_set & npc_tags):
                continue

        score = 0
        matched: List[str] = []
        if q:
            # Per-field weighting: exact name match is the strongest
            # signal; tag matches contribute least.
            haystack = {
                "name":        (npc.name, 10),
                "occupation":  (npc.occupation, 4),
                "title":       (npc.title, 3),
                "race":        (npc.race, 2),
                "faction":     (npc.faction, 3),
                "alignment":   (npc.alignment, 1),
                "notes":       (npc.notes, 2),
                "backstory":   (npc.backstory, 2),
                "appearance":  (npc.appearance, 1),
                "personality": (npc.personality, 1),
                "tags":        (" ".join(npc.tags or []), 1),
            }
            for field_name, (val, weight) in haystack.items():
                v = (val or "").lower()
                if not v:
                    continue
                if v == q:
                    score += weight * 4
                    matched.append(field_name)
                elif v.startswith(q):
                    score += weight * 2
                    matched.append(field_name)
                elif q in v:
                    score += weight
                    matched.append(field_name)
            if score == 0:
                continue
        else:
            # No free-text query — every NPC passing filters scores 1
            score = 1

        hits.append(NpcSearchHit(npc=npc, score=score,
                                    matched_fields=matched))

    hits.sort(key=lambda h: (-h.score, h.npc.name.lower()))
    return hits[:limit]


def locate_npc(world: World, name_or_id: str) -> Optional[NPC]:
    """Best-effort: returns the NPC matching exact id, then exact name,
    then case-insensitive name."""
    if not name_or_id:
        return None
    if name_or_id in world.npcs:
        return world.npcs[name_or_id]
    needle = name_or_id.lower()
    for n in world.npcs.values():
        if n.name == name_or_id:
            return n
    for n in world.npcs.values():
        if n.name.lower() == needle:
            return n
    return None


def npcs_at(world: World, location_id: str) -> List[NPC]:
    return [n for n in world.npcs.values()
            if n.active and n.location_id == location_id]


# --------------------------------------------------------------------- #
# Links
# --------------------------------------------------------------------- #

def _ensure_links(npc) -> List[Dict]:
    if not hasattr(npc, "npc_links") or npc.npc_links is None:
        npc.npc_links = []
    return npc.npc_links


def add_npc_link(world: World, src_id: str, target_id: str,
                   kind: str = "other", notes: str = "",
                   *, bidirectional: bool = True) -> bool:
    """Connect two NPCs.  Returns True on success.

    Bidirectional links symmetrically add the inverse (rival ↔ rival,
    family ↔ family, ally ↔ ally) so the DM only needs to record the
    relationship once.  Asymmetric kinds (mentor ↔ protege,
    patron ↔ protege, subordinate ↔ patron) auto-flip.
    """
    if src_id == target_id:
        return False
    src = world.npcs.get(src_id)
    tgt = world.npcs.get(target_id)
    if not src or not tgt:
        return False
    if kind not in LINK_KINDS:
        kind = "other"
    src_links = _ensure_links(src)
    # Don't duplicate
    for ex in src_links:
        if ex.get("target_id") == target_id and ex.get("kind") == kind:
            ex["notes"] = notes or ex.get("notes", "")
            break
    else:
        src_links.append({"target_id": target_id, "kind": kind,
                            "notes": notes})
    if bidirectional:
        inverse_map = {
            "mentor": "protege",
            "protege": "mentor",
            "patron": "subordinate",
            "subordinate": "patron",
        }
        inv = inverse_map.get(kind, kind)
        tgt_links = _ensure_links(tgt)
        for ex in tgt_links:
            if ex.get("target_id") == src_id and ex.get("kind") == inv:
                ex["notes"] = notes or ex.get("notes", "")
                break
        else:
            tgt_links.append({"target_id": src_id, "kind": inv,
                                "notes": notes})
    return True


def remove_npc_link(world: World, src_id: str, target_id: str,
                      *, bidirectional: bool = True) -> bool:
    src = world.npcs.get(src_id)
    if not src:
        return False
    before = len(_ensure_links(src))
    src.npc_links = [l for l in src.npc_links
                       if l.get("target_id") != target_id]
    removed = before - len(src.npc_links)
    if bidirectional:
        tgt = world.npcs.get(target_id)
        if tgt:
            _ensure_links(tgt)
            tgt.npc_links = [l for l in tgt.npc_links
                               if l.get("target_id") != src_id]
    return removed > 0


def npc_links_of(world: World, npc_id: str) -> List[Dict]:
    """Return the link list with target NPC names resolved for UI."""
    npc = world.npcs.get(npc_id)
    if not npc:
        return []
    out = []
    for link in _ensure_links(npc):
        tgt = world.npcs.get(link.get("target_id", ""))
        if tgt is None:
            continue
        out.append({
            "target_id": tgt.id,
            "target_name": tgt.name,
            "target_location_id": tgt.location_id,
            "kind": link.get("kind", "other"),
            "notes": link.get("notes", ""),
        })
    out.sort(key=lambda r: (r["kind"], r["target_name"].lower()))
    return out


def npcs_linking_to(world: World, npc_id: str) -> List[Dict]:
    """Reverse lookup: every NPC who lists this one in their links."""
    if not npc_id:
        return []
    hits = []
    for n in world.npcs.values():
        for link in _ensure_links(n):
            if link.get("target_id") == npc_id:
                hits.append({
                    "source_id": n.id,
                    "source_name": n.name,
                    "kind": link.get("kind", "other"),
                    "notes": link.get("notes", ""),
                })
                break
    return hits


# --------------------------------------------------------------------- #
# Inventory (detailed)
# --------------------------------------------------------------------- #

def _ensure_inventory_detailed(npc) -> List[Dict]:
    if not hasattr(npc, "inventory_detailed") \
            or npc.inventory_detailed is None:
        npc.inventory_detailed = []
    return npc.inventory_detailed


def add_inventory_item(npc, name: str, *, kind: str = "other",
                          description: str = "",
                          quantity: int = 1) -> Dict:
    rows = _ensure_inventory_detailed(npc)
    entry = {"name": name, "kind": kind,
              "description": description,
              "quantity": int(quantity)}
    rows.append(entry)
    return entry


def remove_inventory_item(npc, name: str) -> bool:
    rows = _ensure_inventory_detailed(npc)
    before = len(rows)
    npc.inventory_detailed = [r for r in rows if r.get("name") != name]
    return len(npc.inventory_detailed) < before


def find_inventory_item(npc, name: str) -> Optional[Dict]:
    for it in _ensure_inventory_detailed(npc):
        if it.get("name") == name:
            return it
    return None


def search_npcs_with_item(world: World, item_name_substring: str
                            ) -> List[NPC]:
    """Find every NPC who carries an item whose name contains the
    substring (case-insensitive).  Covers both the legacy
    ``inventory_items`` list of strings AND the new structured
    ``inventory_detailed`` rows."""
    needle = (item_name_substring or "").lower()
    if not needle:
        return []
    out = []
    for n in world.npcs.values():
        if not n.active:
            continue
        for item in (n.inventory_items or []):
            if needle in str(item).lower():
                out.append(n)
                break
        else:
            for it in _ensure_inventory_detailed(n):
                if needle in it.get("name", "").lower():
                    out.append(n)
                    break
    return out


# --------------------------------------------------------------------- #
# Markdown export — for the Copy button in the detail modal
# --------------------------------------------------------------------- #

def npc_to_markdown(world: World, npc: NPC,
                      *, campaign=None) -> str:
    """Render an NPC as a markdown block the DM can paste into notes
    / Discord / a wiki."""
    lines = [f"# {npc.name}"]
    sub = []
    for label, val in (("Race", npc.race), ("Gender", npc.gender),
                         ("Age", npc.age), ("Title", npc.title),
                         ("Alignment", npc.alignment)):
        if val:
            sub.append(f"{label}: {val}")
    if sub:
        lines.append("  ·  ".join(sub))
    if npc.faction:
        lines.append(f"**Faction:** {npc.faction}")
    if npc.occupation:
        lines.append(f"**Occupation:** {npc.occupation}")
    if npc.location_id and world:
        loc = world.locations.get(npc.location_id)
        if loc is not None:
            lines.append(f"**Location:** {loc.name}")
    if npc.appearance:
        lines.append("")
        lines.append(f"_Appearance_: {npc.appearance}")
    if npc.personality:
        lines.append(f"_Personality_: {npc.personality}")
    if npc.backstory:
        lines.append("")
        lines.append("## Backstory")
        lines.append(npc.backstory)
    if npc.notes:
        lines.append("")
        lines.append("## DM Notes")
        lines.append(npc.notes)

    # Organisations
    if campaign is not None:
        try:
            from data import organizations as orgs
            org_hits = orgs.organisations_for_npc(campaign, npc.id)
            if org_hits:
                lines.append("")
                lines.append("## Organisations")
                for o in org_hits:
                    m = o.member_for_npc(npc.id)
                    rank = (o.rank(m.rank_key) if m else None)
                    rank_name = (rank.name
                                  if rank else (m.rank_key
                                                  if m else ""))
                    lines.append(f"- **{o.name}** "
                                  f"({rank_name or 'unknown'})")
        except Exception:
            pass

    # Links
    links = npc_links_of(world, npc.id) if world else []
    if links:
        lines.append("")
        lines.append("## Links")
        for link in links:
            note = f" — _{link['notes']}_" if link['notes'] else ""
            lines.append(f"- {link['kind'].title()}: "
                          f"{link['target_name']}{note}")

    # Inventory
    inv_lines = []
    for it in (npc.inventory_items or []):
        inv_lines.append(f"- {it}")
    for it in (getattr(npc, "inventory_detailed", None) or []):
        qty = f" ×{it.get('quantity', 1)}" \
            if it.get("quantity", 1) > 1 else ""
        desc = f" — {it['description']}" \
            if it.get("description") else ""
        kind = f" [{it['kind']}]" if it.get("kind") else ""
        inv_lines.append(
            f"- {it['name']}{qty}{kind}{desc}")
    if inv_lines:
        lines.append("")
        lines.append("## Inventory")
        lines.extend(inv_lines)

    return "\n".join(lines)
