"""Find Familiar — PHB p.240. Familiar stat blocks + a summon helper.

A familiar is a tiny CR-0 creature (cat, owl, hawk, raven, spider,
rat, octopus, seahorse, quipper, …) bonded to its caster. It shares
its master's senses (touch sight), can deliver touch spells, and
takes the Help action to grant advantage. PHB rules (p.240):

  * 1 hour cast (ritual). Out-of-combat in practice.
  * Familiar is a celestial / fey / fiend (player picks alignment).
  * If reduced to 0 HP it disappears; recast brings it back.
  * Master may dismiss it temporarily into a pocket dimension.
  * Master can use action to see through familiar's eyes.

Implementation here keeps it data-light: stat block per kind, a
``summon_familiar(battle, owner, kind=...)`` helper that spawns a
combat Entity bound to the owner (``is_summon`` + ``summon_owner``).

Pure logic plus optional summon plumbing — no pygame.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class FamiliarKind:
    """One of the PHB-allowed familiar shapes."""
    key: str
    name: str
    size: str
    hp: int = 1
    ac: int = 11
    speed: int = 30
    fly_speed: int = 0
    swim_speed: int = 0
    climb_speed: int = 0
    perception: int = 13
    stealth: int = 0
    description: str = ""
    notes: str = ""


# --------------------------------------------------------------------- #
# Catalog (PHB p.240 default list — 11 of the named options)
# --------------------------------------------------------------------- #
FAMILIARS: Dict[str, FamiliarKind] = {
    "owl": FamiliarKind(
        key="owl", name="Owl", size="Tiny",
        speed=5, fly_speed=60, perception=15, stealth=4,
        description="Silent flier with keen sight in dim light.",
        notes="Flyby (no OA when leaving reach). 120ft darkvision.",
    ),
    "cat": FamiliarKind(
        key="cat", name="Cat", size="Tiny",
        speed=40, climb_speed=30, perception=13, stealth=4,
        description="Quiet, agile, hunts mice.",
        notes="Keen Smell.",
    ),
    "hawk": FamiliarKind(
        key="hawk", name="Hawk", size="Tiny",
        speed=10, fly_speed=60, perception=14,
        description="Daylight flier; sees prey at long range.",
        notes="Keen Sight (advantage on Perception).",
    ),
    "raven": FamiliarKind(
        key="raven", name="Raven", size="Tiny",
        speed=10, fly_speed=50, perception=14,
        description="Clever scavenger that mimics speech.",
        notes="Mimicry: simple words/sounds.",
    ),
    "spider": FamiliarKind(
        key="spider", name="Spider", size="Tiny",
        speed=20, climb_speed=20, perception=10, stealth=4,
        description="Climber with web sense.",
        notes="Web Sense + Walker.",
    ),
    "rat": FamiliarKind(
        key="rat", name="Rat", size="Tiny",
        speed=20, perception=10,
        description="Sneaky scurrying scout.",
        notes="Keen Smell.",
    ),
    "frog": FamiliarKind(
        key="frog", name="Frog", size="Tiny",
        speed=20, swim_speed=20, perception=10, stealth=3,
        description="Amphibious sneak.",
        notes="Amphibious; -2 speed jumping (PHB).",
    ),
    "octopus": FamiliarKind(
        key="octopus", name="Octopus", size="Small",
        speed=5, swim_speed=30, perception=11, stealth=4,
        description="Underwater familiar; ink cloud.",
        notes="Underwater Camouflage; Water Breathing only.",
    ),
    "seahorse": FamiliarKind(
        key="seahorse", name="Seahorse", size="Tiny",
        speed=0, swim_speed=20, perception=10,
        description="Aquatic only — no land movement.",
        notes="Water Breathing only.",
    ),
    "fish": FamiliarKind(
        key="fish", name="Quipper", size="Tiny",
        speed=0, swim_speed=40, perception=12,
        description="Aquatic toothy fish.",
        notes="Pack Tactics (advantage when ally adjacent).",
    ),
    "weasel": FamiliarKind(
        key="weasel", name="Weasel", size="Tiny",
        speed=30, perception=13, stealth=5,
        description="Tiny stealthy hunter.",
        notes="Keen Hearing & Smell.",
    ),
}


# --------------------------------------------------------------------- #
# Query API
# --------------------------------------------------------------------- #
def list_familiars() -> List[FamiliarKind]:
    return list(FAMILIARS.values())


def list_keys() -> List[str]:
    return list(FAMILIARS.keys())


def get_familiar(key: str) -> FamiliarKind:
    if key not in FAMILIARS:
        raise KeyError(
            f"Unknown familiar {key!r}. Known: {sorted(FAMILIARS)}"
        )
    return FAMILIARS[key]


def aquatic_only(key: str) -> bool:
    """True for familiars that can't survive on land (seahorse / quipper)."""
    return key in ("seahorse", "fish")


# --------------------------------------------------------------------- #
# Summon plumbing
# --------------------------------------------------------------------- #
def build_familiar_stats(kind: FamiliarKind):
    """Return a CreatureStats matching the familiar's PHB block."""
    from data.models import CreatureStats, AbilityScores

    # Familiars use d4 hit dice with effective ability scores tiny.
    # Set abilities to mod ~+0 so Help action is plausible.
    stats = CreatureStats(
        name=kind.name,
        size=kind.size,
        hit_points=max(1, kind.hp),
        armor_class=kind.ac,
        speed=kind.speed,
        fly_speed=kind.fly_speed,
        swim_speed=kind.swim_speed,
        climb_speed=kind.climb_speed,
        challenge_rating=0,
        abilities=AbilityScores(strength=2, dexterity=15, constitution=8,
                                  intelligence=2, wisdom=12, charisma=7),
        creature_type="beast",
        skills={"Perception": kind.perception - 10,
                "Stealth": kind.stealth} if kind.stealth else
                {"Perception": kind.perception - 10},
    )
    return stats


def summon_familiar(battle, owner, kind: str = "owl",
                      x: Optional[int] = None,
                      y: Optional[int] = None,
                      duration_rounds: int = 100):
    """Spawn a familiar bound to ``owner`` at ``(x, y)`` (defaults to
    one cell east of the owner). Returns the spawned Entity.

    The familiar is registered as a summon so it shares the owner's
    initiative, dies cleanly when reduced to 0 HP, and is filtered out
    of monster XP / kill stats.
    """
    if isinstance(kind, str):
        familiar_kind = get_familiar(kind)
    else:
        familiar_kind = kind   # already a FamiliarKind

    if x is None:
        x = int(owner.grid_x) + 1
    if y is None:
        y = int(owner.grid_y)

    stats = build_familiar_stats(familiar_kind)
    summon = battle.spawn_summon(
        owner=owner,
        name=stats.name,
        x=x, y=y,
        hp=stats.hit_points,
        ac=stats.armor_class,
        damage_dice="",                # familiars don't attack
        damage_type="",
        duration=duration_rounds,
        spell_name="Find Familiar",
    )
    # Carry over flight + swim + perception from the kind so the DM
    # can position it correctly.
    summon.stats.fly_speed = familiar_kind.fly_speed
    summon.stats.swim_speed = familiar_kind.swim_speed
    summon.stats.climb_speed = familiar_kind.climb_speed
    summon.stats.size = familiar_kind.size
    return summon


def dismiss_familiar(battle, owner) -> int:
    """Remove every Find Familiar summon owned by ``owner``. Returns
    how many were dismissed."""
    dismissed = 0
    for ent in list(battle.entities):
        if (ent.is_summon and ent.summon_owner is owner
                and ent.summon_spell_name == "Find Familiar"):
            battle.entities.remove(ent)
            dismissed += 1
    return dismissed


def list_familiars_of(battle, owner) -> list:
    """All live Find Familiar summons owned by ``owner``."""
    return [e for e in battle.entities
            if e.is_summon and e.summon_owner is owner
            and e.summon_spell_name == "Find Familiar"]
