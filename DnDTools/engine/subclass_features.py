"""Phase 36 — subclass-feature helpers.

Battle Master Combat Maneuvers (PHB p.73), Sorcerer Metamagic (PHB
p.101) and Wizard Arcane Recovery (PHB p.115) — three subclass
mechanics that were previously data-only.

Each helper:

  * Reads a feature key off the entity (``battle_master_maneuvers``,
    ``metamagic``, ``arcane_recovery``).
  * Reads / writes the matching resource pool (``superiority_dice``,
    ``sorcery_points_left``).
  * Returns a structured result the AI / DM advisor can render.

Pure logic, no pygame.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# --------------------------------------------------------------------- #
# Battle Master combat maneuvers (PHB p.73)
# --------------------------------------------------------------------- #
# Each maneuver: name → (description, trigger, suggests-when)
BATTLE_MASTER_MANEUVERS: Dict[str, Dict[str, str]] = {
    "Trip Attack": {
        "trigger": "on-hit",
        "effect": "Target STR save or knocked Prone",
        "suggests_when": "Adjacent ally can attack with advantage "
                          "vs the prone target",
    },
    "Riposte": {
        "trigger": "reaction-on-miss",
        "effect": "When a creature misses you in melee, attack it",
        "suggests_when": "Enemy missed you in melee and reaction free",
    },
    "Disarming Attack": {
        "trigger": "on-hit",
        "effect": "Target STR save or drop one held item",
        "suggests_when": "Enemy wields a magic weapon",
    },
    "Menacing Attack": {
        "trigger": "on-hit",
        "effect": "Target WIS save or Frightened of you "
                   "until end of your next turn",
        "suggests_when": "Frightened would disadvantage enemy attacks",
    },
    "Pushing Attack": {
        "trigger": "on-hit",
        "effect": "Target STR save or pushed 15 ft",
        "suggests_when": "Hazard within 15 ft (cliff, lava)",
    },
    "Sweeping Attack": {
        "trigger": "on-hit",
        "effect": "Roll superiority die; second creature within "
                   "5 ft takes that much damage",
        "suggests_when": "Two enemies are adjacent to you",
    },
    "Precision Attack": {
        "trigger": "on-attack-roll",
        "effect": "Add superiority die to attack roll",
        "suggests_when": "Attack would miss by ≤ die max",
    },
    "Goading Attack": {
        "trigger": "on-hit",
        "effect": "Target WIS save or has disadvantage on attacks "
                   "vs anyone but you",
        "suggests_when": "Ally is fragile, draws enemy to tank",
    },
    "Maneuvering Attack": {
        "trigger": "on-hit",
        "effect": "An ally can move half its speed without OAs",
        "suggests_when": "Ally needs to disengage from melee",
    },
    "Parry": {
        "trigger": "reaction-on-hit",
        "effect": "Reduce incoming melee damage by die + DEX mod",
        "suggests_when": "Took a big melee hit",
    },
}


def superiority_dice_size(entity) -> int:
    """PHB p.73: d8 (3rd-9th), d10 (10th-17th), d12 (18+)."""
    lvl = max(1, getattr(entity.stats, "character_level", 1))
    if lvl >= 18:
        return 12
    if lvl >= 10:
        return 10
    return 8


def has_superiority_die(entity) -> bool:
    if not entity.has_feature("battle_master_maneuvers") \
            and not entity.has_feature("superiority_dice"):
        return False
    return getattr(entity, "superiority_dice_left", 0) > 0


def use_superiority_die(entity) -> int:
    """Spend a superiority die and return the roll."""
    if not has_superiority_die(entity):
        return 0
    entity.superiority_dice_left -= 1
    return random.randint(1, superiority_dice_size(entity))


def available_maneuvers(entity) -> List[str]:
    """Return the maneuver names this Battle Master knows.  Stored on
    the entity feature's ``mechanic_value`` as a comma-separated list."""
    f = entity.get_feature("battle_master_maneuvers")
    if not f:
        return []
    if not f.mechanic_value:
        # Default starter set if not configured
        return ["Trip Attack", "Riposte", "Precision Attack"]
    return [s.strip() for s in f.mechanic_value.split(",") if s.strip()]


def maneuver_advisor(entity, situation: dict) -> List[Tuple[str, str]]:
    """Return [(maneuver_name, reason)] sorted by recommended-first.

    ``situation`` (dict) describes the moment:
      ``trigger``: "on-hit" | "on-attack-roll" | "reaction-on-miss"
                   | "reaction-on-hit"
      ``attack_total``: int (when known)
      ``target_ac``: int
      ``took_damage``: int (incoming melee hit size)
      ``adjacent_enemies``: int
      ``hazard_within_15``: bool
      ``ally_disengaging``: bool
      ``enemy_magic_weapon``: bool
    """
    if not has_superiority_die(entity):
        return []
    known = available_maneuvers(entity)
    out: List[Tuple[str, str]] = []
    trigger = situation.get("trigger", "")
    for m in known:
        meta = BATTLE_MASTER_MANEUVERS.get(m, {})
        if trigger and meta.get("trigger") != trigger:
            continue
        # Reason-based recommendation
        if m == "Precision Attack":
            atk = situation.get("attack_total", 0)
            ac = situation.get("target_ac", 0)
            die_max = superiority_dice_size(entity)
            if 0 < ac - atk <= die_max:
                out.append((m, f"Miss by {ac - atk}; die ≤ "
                                f"{die_max} flips it"))
            else:
                continue
        elif m == "Trip Attack":
            if situation.get("adjacent_enemies", 0) >= 2 or \
                    situation.get("ally_in_melee"):
                out.append((m, "Prone gives allies adv on melee"))
            else:
                continue
        elif m == "Riposte":
            if trigger == "reaction-on-miss":
                out.append((m, "Free attack on the miss"))
            else:
                continue
        elif m == "Parry":
            if trigger == "reaction-on-hit" and \
                    situation.get("took_damage", 0) >= 10:
                out.append((m, f"Took {situation['took_damage']}; "
                                f"die + DEX reduces it"))
            else:
                continue
        elif m == "Pushing Attack":
            if situation.get("hazard_within_15"):
                out.append((m, "Hazard within 15 ft — push them in"))
            else:
                continue
        elif m == "Sweeping Attack":
            if situation.get("adjacent_enemies", 0) >= 2:
                out.append((m, "Two adjacent enemies"))
            else:
                continue
        elif m == "Disarming Attack":
            if situation.get("enemy_magic_weapon"):
                out.append((m, "Force enemy to drop magic weapon"))
            else:
                continue
        elif m == "Menacing Attack":
            out.append((m, "Frightened cripples enemy offence"))
        elif m == "Maneuvering Attack":
            if situation.get("ally_disengaging"):
                out.append((m, "Lets ally retreat without OA"))
            else:
                continue
        elif m == "Goading Attack":
            if situation.get("fragile_ally"):
                out.append((m, "Pull aggro off the fragile ally"))
            else:
                continue
        else:
            out.append((m, meta.get("effect", "")))
    return out


# --------------------------------------------------------------------- #
# Sorcerer Metamagic (PHB p.101)
# --------------------------------------------------------------------- #
# Each metamagic: name → (sorcery cost, condition / advice)
METAMAGIC: Dict[str, Dict[str, str]] = {
    "Careful Spell": {
        "cost_per_target": "1",
        "effect": "Up to CHA mod allies auto-pass the save",
        "suggests_when": "Allies in your AoE",
    },
    "Distant Spell": {
        "cost": "1",
        "effect": "Double a non-self spell's range, or touch → 30 ft",
        "suggests_when": "Target is just out of normal range",
    },
    "Empowered Spell": {
        "cost": "1",
        "effect": "Reroll up to CHA mod damage dice",
        "suggests_when": "Rolled multiple low damage dice",
    },
    "Extended Spell": {
        "cost": "1",
        "effect": "Double a spell's duration (max 24h)",
        "suggests_when": "Long-duration buff on the party",
    },
    "Heightened Spell": {
        "cost": "3",
        "effect": "One target rolls the first save with disadv",
        "suggests_when": "Save-or-suck spell on the BBEG",
    },
    "Quickened Spell": {
        "cost": "2",
        "effect": "Cast a 1-action spell as a bonus action",
        "suggests_when": "Want to cast two spells this turn",
    },
    "Subtle Spell": {
        "cost": "1",
        "effect": "Cast without verbal/somatic components",
        "suggests_when": "Silenced / grappled / hiding",
    },
    "Twinned Spell": {
        "cost": "spell_level",  # special: cost = spell level (min 1)
        "effect": "Target a second creature with the same spell "
                   "(single-target spells only)",
        "suggests_when": "Two priority targets within range",
    },
}


def sorcery_cost(metamagic_name: str, spell_level: int = 1) -> int:
    """Return the sorcery point cost (Twinned scales with level)."""
    info = METAMAGIC.get(metamagic_name, {})
    cost = info.get("cost", info.get("cost_per_target", "1"))
    if cost == "spell_level":
        return max(1, spell_level)
    try:
        return int(cost)
    except ValueError:
        return 1


def can_apply_metamagic(entity, metamagic_name: str,
                          spell_level: int = 1) -> bool:
    if not entity.has_feature("metamagic"):
        return False
    f = entity.get_feature("metamagic")
    known = []
    if f and f.mechanic_value:
        known = [s.strip() for s in f.mechanic_value.split(",")
                  if s.strip()]
    else:
        # Default: assume Quickened + Twinned (typical starter set)
        known = ["Quickened Spell", "Twinned Spell"]
    if metamagic_name not in known:
        return False
    cost = sorcery_cost(metamagic_name, spell_level)
    return getattr(entity, "sorcery_points_left", 0) >= cost


def apply_metamagic(entity, metamagic_name: str,
                      spell_level: int = 1) -> bool:
    if not can_apply_metamagic(entity, metamagic_name, spell_level):
        return False
    cost = sorcery_cost(metamagic_name, spell_level)
    entity.sorcery_points_left -= cost
    return True


def metamagic_advisor(entity, spell, *, allies_in_aoe: int = 0,
                         second_target_available: bool = False,
                         already_used_action: bool = False,
                         allies_silenced: bool = False
                         ) -> List[Tuple[str, str]]:
    """Suggest the best metamagic for this cast.  Returns
    [(name, reason)]."""
    if not entity.has_feature("metamagic"):
        return []
    out: List[Tuple[str, str]] = []
    spell_level = getattr(spell, "level", 1) if spell else 1
    is_aoe = bool(spell and (spell.aoe_radius or spell.aoe_shape))
    is_single = (not is_aoe and getattr(spell, "targets", "single") == "single")

    if is_aoe and allies_in_aoe > 0 \
            and can_apply_metamagic(entity, "Careful Spell",
                                       spell_level):
        out.append(("Careful Spell",
                      f"{allies_in_aoe} ally/allies in AoE — protect "
                      f"them"))
    if is_single and second_target_available \
            and can_apply_metamagic(entity, "Twinned Spell",
                                       spell_level):
        out.append(("Twinned Spell",
                      f"Hit a second priority target with the same "
                      f"{getattr(spell, 'name', 'spell')}"))
    if already_used_action \
            and can_apply_metamagic(entity, "Quickened Spell",
                                       spell_level):
        out.append(("Quickened Spell",
                      "Fit a second spell into this turn as bonus"))
    if allies_silenced \
            and can_apply_metamagic(entity, "Subtle Spell",
                                       spell_level):
        out.append(("Subtle Spell",
                      "No V/S components needed under silence"))
    return out


# --------------------------------------------------------------------- #
# Wizard Arcane Recovery (PHB p.115)
# --------------------------------------------------------------------- #

def arcane_recovery_max_levels(entity) -> int:
    """Wizard regains slots totalling up to ceil(level/2) on short rest.
    None of the slots may be 6th level or higher."""
    if not entity.has_feature("arcane_recovery"):
        return 0
    lvl = max(1, getattr(entity.stats, "character_level", 1))
    return (lvl + 1) // 2  # ceil(lvl/2)


def arcane_recovery_used_this_day(entity) -> bool:
    """Tracked via a feature_uses counter — 1/day."""
    return entity.feature_uses.get("Arcane Recovery", 0) <= 0


def apply_arcane_recovery(entity, slots_to_restore: Dict[int, int]
                            ) -> Tuple[bool, str]:
    """Restore the requested slots, validating PHB caps:

      * Total slot levels ≤ ceil(wizard_level / 2)
      * No slot above 5th level

    Returns ``(ok, message)``.
    """
    if not entity.has_feature("arcane_recovery"):
        return False, "Entity has no Arcane Recovery feature"
    if arcane_recovery_used_this_day(entity):
        return False, "Arcane Recovery already used this day"
    cap = arcane_recovery_max_levels(entity)
    total = sum(int(lvl) * int(n) for lvl, n in slots_to_restore.items())
    if total > cap:
        return False, (f"Requested {total} slot-levels exceeds cap "
                        f"of {cap}")
    if any(int(lvl) >= 6 for lvl in slots_to_restore):
        return False, "Arcane Recovery cannot restore 6th-level+ slots"
    _LEVEL_KEYS = {1:"1st",2:"2nd",3:"3rd",4:"4th",5:"5th"}
    for lvl, n in slots_to_restore.items():
        key = _LEVEL_KEYS.get(int(lvl))
        if not key:
            return False, f"Invalid slot level: {lvl}"
        entity.spell_slots[key] = entity.spell_slots.get(key, 0) + int(n)
    # Mark as used
    entity.feature_uses["Arcane Recovery"] = 0
    return True, (f"Restored {total} slot-levels via Arcane Recovery")
