"""
army_sim — abstract army-vs-army combat simulation.

Turns two pools of creatures into a simple attrition model the DM can run
at the campaign scale (e.g. "Tarmaas 120 spearmen vs Oblitus 80 bandits").
The model is intentionally coarse — it uses mean damage per round and
hit chance estimated from AC + attack bonus, then runs a small Monte Carlo
to report win rate + expected casualties.

Hooks
-----
* ``unit_from_stats(stats, count)`` — build a ``UnitStack`` from the
  campaign's ``CreatureStats`` library entry.
* ``army_from_map_object(world_engine_obj, count_override=None)`` — pull
  a ``UnitStack`` out of a map token's ``unit_type`` / ``unit_count``
  fields.
* ``simulate(army_a, army_b, rounds=60)`` — single deterministic trial;
  returns ``SimulationResult``.
* ``monte_carlo(army_a, army_b, trials=50)`` — aggregates over trials
  with damage jitter; returns ``MonteCarloResult``.

The module has *no* pygame dependency so it can be unit-tested independently.
"""
from __future__ import annotations

import math
import random
import re
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Tuple


# ----------------------------------------------------------------------
# Unit / army data model
# ----------------------------------------------------------------------

@dataclass
class UnitStack:
    name: str = "Unit"
    count: int = 1
    hp_each: int = 8
    ac: int = 12
    to_hit: int = 3
    dpr_each: float = 4.0     # expected damage per round, per model
    speed: int = 30           # feet

    @property
    def total_hp(self) -> int:
        return max(0, int(self.hp_each * self.count))

    @property
    def total_dpr(self) -> float:
        return max(0.0, self.dpr_each * self.count)

    def apply_casualties(self, damage: float) -> int:
        """Reduce count by full models killed; return models lost."""
        if damage <= 0 or self.count <= 0 or self.hp_each <= 0:
            return 0
        killed = int(damage // self.hp_each)
        killed = min(killed, self.count)
        self.count -= killed
        return killed


@dataclass
class Army:
    name: str = "Army"
    banner_color: Tuple[int, int, int] = (180, 180, 180)
    stacks: List[UnitStack] = field(default_factory=list)

    @property
    def total_hp(self) -> int:
        return sum(s.total_hp for s in self.stacks)

    @property
    def total_dpr(self) -> float:
        return sum(s.total_dpr for s in self.stacks)

    @property
    def total_count(self) -> int:
        return sum(s.count for s in self.stacks)

    @property
    def mean_ac(self) -> float:
        c = self.total_count
        if c <= 0:
            return 12.0
        weighted = sum(s.ac * s.count for s in self.stacks)
        return weighted / c

    def is_broken(self) -> bool:
        return self.total_count <= 0 or self.total_hp <= 0


# ----------------------------------------------------------------------
# Result records
# ----------------------------------------------------------------------

@dataclass
class RoundLog:
    round: int
    dmg_a_to_b: float
    dmg_b_to_a: float
    count_a: int
    count_b: int


@dataclass
class SimulationResult:
    winner: str                     # "a", "b", or "draw"
    rounds: int
    casualties_a: int
    casualties_b: int
    survivors_a: int
    survivors_b: int
    log: List[RoundLog] = field(default_factory=list)


@dataclass
class MonteCarloResult:
    trials: int
    a_wins: int
    b_wins: int
    draws: int
    mean_rounds: float
    mean_cas_a: float
    mean_cas_b: float

    @property
    def win_rate_a(self) -> float:
        return self.a_wins / max(1, self.trials)

    @property
    def win_rate_b(self) -> float:
        return self.b_wins / max(1, self.trials)


# ----------------------------------------------------------------------
# Damage / hit modelling
# ----------------------------------------------------------------------

def hit_chance(to_hit: int, target_ac: float) -> float:
    """d20 to-hit approximation: need roll >= (ac - to_hit).
    Natural 1 always misses, natural 20 always hits — clamped [0.05, 0.95].
    """
    need = max(2, int(round(target_ac - to_hit)))
    raw = (21 - need) / 20.0
    return max(0.05, min(0.95, raw))


def _parse_damage_dice(expr: str) -> float:
    """Return expected damage of a dice expression like '2d6+3', '1d8'."""
    if not expr:
        return 0.0
    total = 0.0
    for part in re.split(r"[+\-]", expr):
        part = part.strip()
        if not part:
            continue
        m = re.match(r"^(\d+)d(\d+)$", part)
        if m:
            n, die = int(m.group(1)), int(m.group(2))
            total += n * (die + 1) / 2.0
        else:
            try:
                total += int(part)
            except ValueError:
                continue
    # Rough handling of subtraction: re.split drops signs — accept rough estimate.
    return max(0.0, total)


def unit_from_stats(stats, count: int) -> UnitStack:
    """Convert a CreatureStats into a UnitStack. Safe when some fields are
    missing — we fall back to CR-based DPR heuristics."""
    hp = getattr(stats, "hit_points", 10) or 10
    ac = getattr(stats, "armor_class", 12) or 12
    speed = getattr(stats, "speed", 30) or 30
    cr = float(getattr(stats, "challenge_rating", 0.25) or 0.25)

    # Mean damage of the first action whose damage_dice is set. Fallback
    # tables from 5e DMG p.274 based on CR.
    dpr = 0.0
    to_hit = max(2, int(round(2 + cr)))
    actions = getattr(stats, "actions", None) or []
    for a in actions:
        dd = getattr(a, "damage_dice", "") or ""
        if dd:
            bonus = getattr(a, "damage_bonus", 0) or 0
            dpr += _parse_damage_dice(dd) + bonus
            ab = getattr(a, "attack_bonus", 0) or 0
            if ab:
                to_hit = max(to_hit, ab)
            break
    if dpr <= 0:
        # DMG damage-by-CR (slightly flattened).
        dpr = max(1.0, 2 + cr * 4.0)

    return UnitStack(
        name=getattr(stats, "name", "Unit"),
        count=max(1, int(count)),
        hp_each=int(hp), ac=int(ac),
        to_hit=int(to_hit), dpr_each=float(dpr),
        speed=int(speed),
    )


def army_from_map_object(obj, count_override: Optional[int] = None,
                          library=None) -> Optional[Army]:
    """Build a single-stack Army from a MapObject's unit_type/unit_count.
    Resolves the unit type via the passed-in monster library (or
    ``data.library.library`` if omitted). Returns None if the unit can't
    be resolved."""
    unit_type = getattr(obj, "unit_type", "") or ""
    if not unit_type:
        return None
    if library is None:
        from data.library import library as _lib
        library = _lib
    try:
        stats = library.get_monster(unit_type)
    except Exception:
        return None
    count = count_override if count_override is not None else getattr(obj, "unit_count", 0)
    if count <= 0:
        return None
    stack = unit_from_stats(stats, int(count))
    faction = getattr(obj, "faction", "") or unit_type
    return Army(name=faction, stacks=[stack])


# ----------------------------------------------------------------------
# Single-trial simulation
# ----------------------------------------------------------------------

def simulate(army_a: Army, army_b: Army, max_rounds: int = 60,
             rng: Optional[random.Random] = None) -> SimulationResult:
    """Run a single deterministic-ish trial with light damage jitter.

    Each round, each army's expected damage = total_dpr × hit_chance(avg_ac).
    We apply a ±15% jitter to reflect tactics/morale variance. Damage is
    distributed across the defender's stacks in proportion to each stack's
    total_hp, and applied via apply_casualties.
    """
    rng = rng or random.Random()
    log: List[RoundLog] = []

    # Snapshot start counts for casualty reporting
    start_a = army_a.total_count
    start_b = army_b.total_count

    for r in range(1, max_rounds + 1):
        if army_a.is_broken() or army_b.is_broken():
            break

        dmg_ab = _round_damage(army_a, army_b, rng)
        dmg_ba = _round_damage(army_b, army_a, rng)

        _apply_damage(army_b, dmg_ab)
        _apply_damage(army_a, dmg_ba)

        log.append(RoundLog(
            round=r, dmg_a_to_b=dmg_ab, dmg_b_to_a=dmg_ba,
            count_a=army_a.total_count, count_b=army_b.total_count,
        ))

    cas_a = max(0, start_a - army_a.total_count)
    cas_b = max(0, start_b - army_b.total_count)

    if army_a.is_broken() and army_b.is_broken():
        winner = "draw"
    elif army_a.is_broken():
        winner = "b"
    elif army_b.is_broken():
        winner = "a"
    else:
        # Exceeded max_rounds without a decisive result: whoever has more
        # surviving total HP wins by attrition.
        if army_a.total_hp > army_b.total_hp:
            winner = "a"
        elif army_b.total_hp > army_a.total_hp:
            winner = "b"
        else:
            winner = "draw"

    return SimulationResult(
        winner=winner,
        rounds=len(log),
        casualties_a=cas_a,
        casualties_b=cas_b,
        survivors_a=army_a.total_count,
        survivors_b=army_b.total_count,
        log=log,
    )


def _round_damage(attacker: Army, defender: Army, rng: random.Random) -> float:
    if attacker.total_count <= 0 or defender.total_count <= 0:
        return 0.0
    avg_ac = defender.mean_ac
    # Weighted hit chance across attacker stacks
    dmg = 0.0
    for s in attacker.stacks:
        if s.count <= 0:
            continue
        ch = hit_chance(s.to_hit, avg_ac)
        dmg += s.total_dpr * ch
    jitter = 1.0 + rng.uniform(-0.15, 0.15)
    return max(0.0, dmg * jitter)


def _apply_damage(defender: Army, damage: float) -> None:
    if damage <= 0 or defender.total_count <= 0:
        return
    total_hp = defender.total_hp
    if total_hp <= 0:
        return
    for s in defender.stacks:
        if s.count <= 0:
            continue
        share = (s.total_hp / total_hp) * damage
        s.apply_casualties(share)


# ----------------------------------------------------------------------
# Monte Carlo
# ----------------------------------------------------------------------

def monte_carlo(army_a: Army, army_b: Army, trials: int = 50,
                max_rounds: int = 60,
                rng: Optional[random.Random] = None) -> MonteCarloResult:
    rng = rng or random.Random()
    import copy
    a_wins = b_wins = draws = 0
    total_rounds = 0
    total_cas_a = 0
    total_cas_b = 0
    for _ in range(trials):
        a_copy = copy.deepcopy(army_a)
        b_copy = copy.deepcopy(army_b)
        res = simulate(a_copy, b_copy, max_rounds=max_rounds, rng=rng)
        if res.winner == "a":
            a_wins += 1
        elif res.winner == "b":
            b_wins += 1
        else:
            draws += 1
        total_rounds += res.rounds
        total_cas_a += res.casualties_a
        total_cas_b += res.casualties_b
    t = max(1, trials)
    return MonteCarloResult(
        trials=trials,
        a_wins=a_wins, b_wins=b_wins, draws=draws,
        mean_rounds=total_rounds / t,
        mean_cas_a=total_cas_a / t,
        mean_cas_b=total_cas_b / t,
    )
