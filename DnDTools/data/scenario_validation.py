"""Scenario navigation validation — checks that the AI can actually
play through an authored scenario.

The core question we answer: from every party-spawn cell, can a unit
walk to at least one monster cell? If not, the scenario has a sealed
room or an unreachable enemy and combat will deadlock.

Pure logic; no pygame. Tests in tests/test_scenario_validation.py.
"""
from __future__ import annotations

from collections import deque
from typing import Iterable, List, Tuple

from data.scenarios import Scenario
from engine.terrain import TERRAIN_TYPES


# --------------------------------------------------------------------- #
# Passability — cheap version that only inspects the scenario's tile
# list (no BattleSystem instantiation needed).
# --------------------------------------------------------------------- #
def _tile_blocks(scenario: Scenario, x: int, y: int) -> bool:
    """True if the cell is impassable for navigation.

    Layered tile semantics:
      * If any tile at (x, y) is a door (open OR locked), the cell is
        passable — combat code can open / pick / break it. A door
        layered on top of a wall therefore overrides the wall.
      * Otherwise, the cell is blocked if any tile here is impassable
        and not a door, OR is a gap (chasm).
    """
    tiles_here = []
    for t in scenario.tiles:
        if t.x <= x < t.x + t.w and t.y <= y < t.y + t.h:
            tiles_here.append(t)
    if not tiles_here:
        return False
    # Door anywhere at this cell → passable
    for t in tiles_here:
        props = TERRAIN_TYPES.get(t.terrain_type, {})
        if props.get("door"):
            return False
    for t in tiles_here:
        props = TERRAIN_TYPES.get(t.terrain_type, {})
        if not props.get("passable", True):
            return True
        if props.get("is_gap"):
            return True
    return False


# --------------------------------------------------------------------- #
# BFS-based reachability
# --------------------------------------------------------------------- #
def reachable_cells(scenario: Scenario, start_x: int, start_y: int,
                      *, max_x: int = 60, max_y: int = 60) -> set:
    """Return the set of (x, y) cells reachable from ``(start_x,
    start_y)`` walking 4-direction over passable tiles within a
    ``max_x x max_y`` bounding box (default 60x60 covers all bundled
    scenarios)."""
    if _tile_blocks(scenario, start_x, start_y):
        return set()
    seen = {(start_x, start_y)}
    queue = deque([(start_x, start_y)])
    while queue:
        x, y = queue.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if (nx, ny) in seen:
                continue
            if not (0 <= nx < max_x and 0 <= ny < max_y):
                continue
            if _tile_blocks(scenario, nx, ny):
                continue
            seen.add((nx, ny))
            queue.append((nx, ny))
    return seen


def party_can_reach_monster(scenario: Scenario,
                              *, max_x: int = 60,
                              max_y: int = 60) -> dict:
    """Verify every party_spawn can reach at least one monster.

    Returns a structured report:
      ``{
         ok: bool,
         per_spawn: [(spawn_xy, reachable_monster_count), ...],
         orphan_spawns: [(x, y), ...],
         orphan_monsters: [(x, y), ...]
      }``

    A spawn is "orphan" when none of the scenario's monsters lies in
    its reachable set; a monster is "orphan" when no spawn can reach
    it.
    """
    monster_cells = {(m.x, m.y) for m in scenario.monsters}
    per_spawn = []
    orphan_spawns = []
    reached_by_any = set()
    for sx, sy in scenario.party_spawns:
        reach = reachable_cells(scenario, sx, sy, max_x=max_x, max_y=max_y)
        hit = reach & monster_cells
        per_spawn.append(((sx, sy), len(hit)))
        if not hit:
            orphan_spawns.append((sx, sy))
        reached_by_any |= hit
    orphan_monsters = sorted(monster_cells - reached_by_any)
    return {
        "ok": not orphan_spawns and not orphan_monsters,
        "per_spawn": per_spawn,
        "orphan_spawns": orphan_spawns,
        "orphan_monsters": orphan_monsters,
    }


def validate_all_scenarios(scenarios: Iterable[Scenario]) -> List[dict]:
    """Run :func:`party_can_reach_monster` on every scenario and return
    the failing reports (each augmented with the scenario's id+name)."""
    out = []
    for s in scenarios:
        rep = party_can_reach_monster(s)
        if not rep["ok"]:
            rep["scenario_id"] = s.id
            rep["scenario_name"] = s.name
            out.append(rep)
    return out
