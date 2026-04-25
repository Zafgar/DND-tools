"""Travel pace + rest mechanics (PHB 5e 2014).

Pure-logic helpers; no pygame. Source: PHB pp.181-186.

Coverage:
  * Pace → distance per hour / per day (slow/normal/fast).
  * Forced march DC + per-PC exhaustion outcome.
  * Long rest length + exhaustion relief.
  * Short rest length.
  * Sleep deprivation: if a creature gets less than 8h of sleep in
    24h, it doesn't benefit from a long rest (no exhaustion relief).
  * Apply forced march to a list of PCs (each with Constitution
    save modifier and current exhaustion).
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Iterable, List


# --------------------------------------------------------------------- #
# Pace
# --------------------------------------------------------------------- #
PACE = {
    "slow":   {"mph": 2, "miles_per_day": 18,
                "effects": ("able_to_use_stealth",)},
    "normal": {"mph": 3, "miles_per_day": 24, "effects": ()},
    "fast":   {"mph": 4, "miles_per_day": 30,
                "effects": ("perception_disadvantage",)},
}

NORMAL_TRAVEL_HOURS = 8     # PHB p.181: 8h normal travel day
LONG_REST_HOURS = 8         # PHB p.186
SHORT_REST_HOURS = 1        # PHB p.186
ELF_TRANCE_HOURS = 4        # PHB p.23: elves trance for 4h = full long rest


def miles_in_hours(pace: str, hours: float) -> float:
    """Miles travelled in ``hours`` at ``pace``."""
    if pace not in PACE:
        raise ValueError(f"Unknown pace {pace!r}; expected one of {list(PACE)}")
    return PACE[pace]["mph"] * max(0.0, float(hours))


def miles_per_day(pace: str) -> int:
    return PACE[pace]["miles_per_day"]


# --------------------------------------------------------------------- #
# Forced march (PHB p.181)
# --------------------------------------------------------------------- #
def forced_march_dc(extra_hours: int) -> int:
    """DC 10 + 1 per hour past the 8-hour normal travel day. Returns 10
    if extra_hours <= 0 (no forced march)."""
    return 10 + max(0, int(extra_hours))


def forced_march_outcome(extra_hours: int, con_save_total: int) -> dict:
    """Compute the result of a single forced-march save.

    ``con_save_total`` is the d20 + Con bonus the PC rolled.
    Returns ``{dc, succeeded, exhaustion_gained}``.
    """
    dc = forced_march_dc(extra_hours)
    ok = con_save_total >= dc
    return {
        "dc": dc,
        "succeeded": ok,
        "exhaustion_gained": 0 if ok else 1,
    }


def simulate_forced_march(extra_hours: int, con_modifier: int,
                            *, advantage: bool = False,
                            disadvantage: bool = False,
                            rng: random.Random = None) -> dict:
    """Roll a Con save with the given modifier and return the outcome.

    ``advantage`` and ``disadvantage`` cancel out when both set.
    """
    rng = rng or random.Random()
    if advantage and disadvantage:
        advantage = disadvantage = False
    rolls = [rng.randint(1, 20)]
    if advantage or disadvantage:
        rolls.append(rng.randint(1, 20))
    natural = max(rolls) if advantage else min(rolls)
    return forced_march_outcome(extra_hours, natural + int(con_modifier))


# --------------------------------------------------------------------- #
# Rest (PHB p.186)
# --------------------------------------------------------------------- #
@dataclass
class PartyMemberPace:
    """Lightweight DTO so callers can drive march math without pulling
    in the full Entity/CreatureStats hierarchy. ``con_modifier`` is the
    PC's CON save bonus (CON modifier, plus proficiency if proficient)."""
    name: str
    con_modifier: int = 0
    exhaustion: int = 0
    is_elf_trance: bool = False


def long_rest_relief(pc: PartyMemberPace, hours_slept: float) -> int:
    """How many levels of exhaustion ``pc`` recovers after a rest of
    ``hours_slept`` hours.

    PHB: a long rest needs 8 hours (or 4 for an elf in trance) to count.
    A rest shorter than that grants no benefit.  At most one level of
    exhaustion is removed per long rest (PHB p.291)."""
    needed = ELF_TRANCE_HOURS if pc.is_elf_trance else LONG_REST_HOURS
    if hours_slept < needed:
        return 0
    return min(pc.exhaustion, 1)


def apply_long_rest(pc: PartyMemberPace, hours_slept: float) -> int:
    """Mutate ``pc.exhaustion`` for a long rest. Returns levels removed."""
    relief = long_rest_relief(pc, hours_slept)
    pc.exhaustion = max(0, pc.exhaustion - relief)
    return relief


def short_rest_grants_benefit(hours: float) -> bool:
    """PHB p.186: a short rest is at least 1 hour long."""
    return hours >= SHORT_REST_HOURS


# --------------------------------------------------------------------- #
# Travel-day simulation (forced march for an entire party)
# --------------------------------------------------------------------- #
def simulate_travel_day(party: Iterable[PartyMemberPace],
                         pace: str = "normal",
                         hours_walked: int = NORMAL_TRAVEL_HOURS,
                         *, rng: random.Random = None) -> dict:
    """Walk ``party`` for ``hours_walked`` at ``pace``. If the party
    walked beyond NORMAL_TRAVEL_HOURS, every PC rolls a Con save and
    accumulates exhaustion on failure.

    Mutates ``pc.exhaustion`` on each failing PartyMemberPace. Returns
    a structured report:
      ``{
         pace: str,
         hours_walked: int,
         miles_travelled: float,
         extra_hours: int,
         dc: int,
         saves: [{name, total, succeeded, exhaustion_gained, exhaustion_total}, ...],
         deaths: [name, ...]   # PCs who hit exhaustion 6
      }``
    """
    rng = rng or random.Random()
    pace = pace if pace in PACE else "normal"
    hours_walked = int(max(0, hours_walked))
    extra = max(0, hours_walked - NORMAL_TRAVEL_HOURS)
    miles = miles_in_hours(pace, hours_walked)

    saves = []
    deaths = []
    party_list = list(party)
    for pc in party_list:
        if extra <= 0:
            saves.append({
                "name": pc.name, "total": None, "succeeded": True,
                "exhaustion_gained": 0,
                "exhaustion_total": pc.exhaustion,
            })
            continue
        out = simulate_forced_march(extra, pc.con_modifier, rng=rng)
        pc.exhaustion = min(6, pc.exhaustion + out["exhaustion_gained"])
        saves.append({
            "name": pc.name,
            "total": None,   # natural roll obscured; only outcome reported
            "succeeded": out["succeeded"],
            "exhaustion_gained": out["exhaustion_gained"],
            "exhaustion_total": pc.exhaustion,
        })
        if pc.exhaustion >= 6:
            deaths.append(pc.name)

    return {
        "pace": pace,
        "hours_walked": hours_walked,
        "miles_travelled": miles,
        "extra_hours": extra,
        "dc": forced_march_dc(extra) if extra > 0 else None,
        "saves": saves,
        "deaths": deaths,
    }


# --------------------------------------------------------------------- #
# Exhaustion description (PHB p.291)
# --------------------------------------------------------------------- #
EXHAUSTION_EFFECTS = (
    "None",                                                     # 0
    "Disadvantage on ability checks",                           # 1
    "Speed halved",                                             # 2
    "Disadvantage on attack rolls and saving throws",           # 3
    "Hit point maximum halved",                                 # 4
    "Speed reduced to 0",                                       # 5
    "Death",                                                    # 6
)


def exhaustion_description(level: int) -> str:
    level = max(0, min(6, int(level)))
    return EXHAUSTION_EFFECTS[level]
