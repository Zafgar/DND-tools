"""Phase 40/41/42 — NPC graph + mini-card content (pure logic).

UI-agnostic computations behind three features:

  * Phase 40 — add-link form: validation + commit live in
    :mod:`data.npc_directory`; this module just supplies the choice
    lists (target NPCs, link kinds).
  * Phase 41 — hover mini-card: :func:`mini_card_content` returns the
    compact field set the tooltip renders.
  * Phase 42 — relationship graph: :func:`build_graph` collects the
    nodes + edges for a filtered NPC set, and
    :func:`circular_layout` / :func:`force_directed_layout` compute
    deterministic node positions the viewer caches once per open.

Keeping the layout math here (no pygame) means the graph can be unit
tested for "no overlaps / edges connect real nodes / layout is
deterministic" without a display surface.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from data.world import World, NPC
from data import npc_directory as nd


# --------------------------------------------------------------------- #
# Edge colours by link kind (shared by graph viewer + detail modal)
# --------------------------------------------------------------------- #
LINK_KIND_COLOR = {
    "rival":       (220, 110, 90),
    "enemy":       (220, 70, 70),
    "mentor":      (110, 180, 240),
    "protege":     (110, 180, 240),
    "patron":      (200, 170, 80),
    "subordinate": (200, 170, 80),
    "family":      (150, 200, 130),
    "ally":        (90, 200, 120),
    "friend":      (90, 200, 160),
    "lover":       (220, 130, 200),
    "contact":     (160, 160, 180),
    "other":       (140, 140, 150),
}


# --------------------------------------------------------------------- #
# Phase 41 — hover mini-card
# --------------------------------------------------------------------- #

def mini_card_content(world: World, npc: NPC,
                        campaign=None) -> dict:
    """Return the compact info a hover tooltip shows for an NPC.

    Kept tiny on purpose — name, identity line, faction, location,
    top 3 links, primary organisation, portrait path. The renderer
    decides layout; this guarantees the *content* is consistent and
    testable.
    """
    identity_bits = [b for b in (npc.race, npc.gender, npc.age,
                                    npc.alignment) if b]
    location_name = ""
    if npc.location_id and world:
        loc = world.locations.get(npc.location_id)
        if loc is not None:
            location_name = loc.name

    # Top 3 links (already name-resolved, sorted by kind)
    links = nd.npc_links_of(world, npc.id) if world else []
    top_links = [
        f"{l['kind']}: {l['target_name']}" for l in links[:3]
    ]

    # Primary organisation (first membership)
    primary_org = ""
    org_rank = ""
    if campaign is not None:
        try:
            from data import organizations as orgs
            hits = orgs.organisations_for_npc(campaign, npc.id)
            if not hits and npc.name:
                hits = orgs.organisations_for_npc_name(
                    campaign, npc.name)
            if hits:
                primary_org = hits[0].name
                m = hits[0].member_for_npc(npc.id)
                if m and m.rank_key:
                    r = hits[0].rank(m.rank_key)
                    org_rank = r.name if r else m.rank_key
        except Exception:
            pass

    return {
        "name": npc.name,
        "title": npc.title,
        "identity": "  ·  ".join(identity_bits),
        "occupation": npc.occupation,
        "faction": npc.faction,
        "location": location_name,
        "portrait_path": npc.portrait_path,
        "links": top_links,
        "link_count": len(links),
        "organisation": primary_org,
        "org_rank": org_rank,
        "alive": npc.alive,
    }


# --------------------------------------------------------------------- #
# Phase 42 — relationship graph
# --------------------------------------------------------------------- #

@dataclass
class GraphNode:
    id: str
    name: str
    faction: str = ""
    # Filled by layout
    x: float = 0.0
    y: float = 0.0
    degree: int = 0           # number of edges touching this node


@dataclass
class GraphEdge:
    source: str
    target: str
    kind: str = "other"
    notes: str = ""


@dataclass
class NpcGraph:
    nodes: List[GraphNode] = field(default_factory=list)
    edges: List[GraphEdge] = field(default_factory=list)

    def node(self, npc_id: str) -> Optional[GraphNode]:
        for n in self.nodes:
            if n.id == npc_id:
                return n
        return None


def build_graph(world: World, *,
                  npc_ids: Optional[List[str]] = None,
                  faction: str = "",
                  organisation_key: str = "",
                  campaign=None,
                  include_isolated: bool = True) -> NpcGraph:
    """Build the relationship graph for a filtered NPC set.

    Edges are de-duplicated (A→B and B→A with the same kind collapse
    into a single undirected edge for rendering).  ``include_isolated``
    keeps NPCs with no links visible as lone nodes.
    """
    # Determine candidate NPC ids
    if npc_ids is not None:
        candidates = {nid for nid in npc_ids if nid in world.npcs}
    else:
        candidates = set(world.npcs.keys())

    # Faction / organisation filters
    if faction:
        candidates = {nid for nid in candidates
                       if faction.lower() in
                       (world.npcs[nid].faction or "").lower()}
    org_members = None
    if organisation_key and campaign is not None:
        try:
            from data import organizations as orgs
            o = orgs.find_organisation(campaign, organisation_key)
            if o is not None:
                org_members = {m.npc_id for m in o.members if m.npc_id}
        except Exception:
            org_members = None
    if org_members is not None:
        candidates &= org_members

    # Collect edges among candidates
    edges: List[GraphEdge] = []
    seen_pairs = set()
    degree: Dict[str, int] = {nid: 0 for nid in candidates}
    for nid in candidates:
        npc = world.npcs[nid]
        for link in (getattr(npc, "npc_links", None) or []):
            tgt = link.get("target_id", "")
            if tgt not in candidates:
                continue
            pair = tuple(sorted((nid, tgt)))
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            edges.append(GraphEdge(
                source=nid, target=tgt,
                kind=link.get("kind", "other"),
                notes=link.get("notes", ""),
            ))
            degree[nid] = degree.get(nid, 0) + 1
            degree[tgt] = degree.get(tgt, 0) + 1

    # Build node list
    nodes: List[GraphNode] = []
    for nid in candidates:
        deg = degree.get(nid, 0)
        if deg == 0 and not include_isolated:
            continue
        npc = world.npcs[nid]
        nodes.append(GraphNode(
            id=nid, name=npc.name,
            faction=npc.faction or "",
            degree=deg,
        ))
    # Stable ordering: highest-degree first, then name
    nodes.sort(key=lambda n: (-n.degree, n.name.lower()))
    return NpcGraph(nodes=nodes, edges=edges)


def circular_layout(graph: NpcGraph, *,
                      cx: float, cy: float,
                      radius: float) -> None:
    """Place nodes evenly on a circle (deterministic). Mutates node
    x/y in place. High-degree hubs are placed first (spread out)."""
    n = len(graph.nodes)
    if n == 0:
        return
    for i, node in enumerate(graph.nodes):
        angle = (2 * math.pi * i) / n - math.pi / 2
        node.x = cx + radius * math.cos(angle)
        node.y = cy + radius * math.sin(angle)


def force_directed_layout(graph: NpcGraph, *,
                            width: float, height: float,
                            iterations: int = 60,
                            seed: int = 1) -> None:
    """Deterministic Fruchterman-Reingold-ish layout. Mutates node
    x/y. Seeded so the viewer (and tests) get the same picture every
    time for the same graph."""
    import random as _r
    rng = _r.Random(seed)
    n = len(graph.nodes)
    if n == 0:
        return
    if n == 1:
        graph.nodes[0].x = width / 2
        graph.nodes[0].y = height / 2
        return

    # Seed positions on a circle (deterministic) then relax.
    circular_layout(graph, cx=width / 2, cy=height / 2,
                      radius=min(width, height) * 0.35)
    # Tiny deterministic jitter so symmetric graphs don't lock up
    for node in graph.nodes:
        node.x += rng.uniform(-5, 5)
        node.y += rng.uniform(-5, 5)

    area = width * height
    k = math.sqrt(area / n) * 0.8     # ideal edge length
    pos = {node.id: [node.x, node.y] for node in graph.nodes}
    adj = {node.id: set() for node in graph.nodes}
    for e in graph.edges:
        if e.source in adj and e.target in adj:
            adj[e.source].add(e.target)
            adj[e.target].add(e.source)

    temp = min(width, height) * 0.1
    cooling = temp / (iterations + 1)
    ids = [node.id for node in graph.nodes]
    for _ in range(iterations):
        disp = {nid: [0.0, 0.0] for nid in ids}
        # Repulsion (all pairs)
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                a, b = ids[i], ids[j]
                dx = pos[a][0] - pos[b][0]
                dy = pos[a][1] - pos[b][1]
                dist = math.hypot(dx, dy) or 0.01
                force = (k * k) / dist
                ux, uy = dx / dist, dy / dist
                disp[a][0] += ux * force
                disp[a][1] += uy * force
                disp[b][0] -= ux * force
                disp[b][1] -= uy * force
        # Attraction (edges)
        for e in graph.edges:
            if e.source not in pos or e.target not in pos:
                continue
            dx = pos[e.source][0] - pos[e.target][0]
            dy = pos[e.source][1] - pos[e.target][1]
            dist = math.hypot(dx, dy) or 0.01
            force = (dist * dist) / k
            ux, uy = dx / dist, dy / dist
            disp[e.source][0] -= ux * force
            disp[e.source][1] -= uy * force
            disp[e.target][0] += ux * force
            disp[e.target][1] += uy * force
        # Apply with cooling + clamp to bounds
        for nid in ids:
            dx, dy = disp[nid]
            d = math.hypot(dx, dy) or 0.01
            step = min(d, temp)
            pos[nid][0] += (dx / d) * step
            pos[nid][1] += (dy / d) * step
            pos[nid][0] = max(40, min(width - 40, pos[nid][0]))
            pos[nid][1] = max(40, min(height - 40, pos[nid][1]))
        temp = max(1.0, temp - cooling)

    for node in graph.nodes:
        node.x, node.y = pos[node.id]


def nearest_node(graph: NpcGraph, x: float, y: float,
                   max_dist: float = 24.0) -> Optional[GraphNode]:
    """Return the node whose centre is within ``max_dist`` of (x, y),
    or None. Used for click / hover hit-testing."""
    best = None
    best_d = max_dist
    for node in graph.nodes:
        d = math.hypot(node.x - x, node.y - y)
        if d <= best_d:
            best_d = d
            best = node
    return best
