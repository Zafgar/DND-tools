"""
D&D 5e 2014 Rules Engine
========================
Central rules reference for the AI and battle system. Every rule here is based on
the 2014 Player's Handbook, Monster Manual, and Dungeon Master's Guide.

This module is the SINGLE SOURCE OF TRUTH for how 5e mechanics work.
Both the AI (engine/ai.py) and the battle system (engine/battle.py) must defer
to the helpers in this file.
"""
import random
import math
from typing import TYPE_CHECKING, Optional, List, Tuple

if TYPE_CHECKING:
    from engine.entities import Entity
    from engine.battle import BattleSystem


# ============================================================
# SIZE CATEGORIES (PHB p.191, MM p.6)
# ============================================================
# 5e sizes in order from smallest to largest.
# Used for grapple/shove eligibility and movement-through rules.
SIZE_ORDER = {
    "Tiny": 0,
    "Small": 1,
    "Medium": 2,
    "Large": 3,
    "Huge": 4,
    "Gargantuan": 5,
}


def get_size_rank(size: str) -> int:
    """Return numeric size rank. Case-insensitive, defaults to Medium."""
    for key, val in SIZE_ORDER.items():
        if key.lower() == size.strip().lower():
            return val
    return 2  # Medium default


def size_difference(entity_a: "Entity", entity_b: "Entity") -> int:
    """Return how many size categories A is larger than B (negative = smaller)."""
    return get_size_rank(entity_a.stats.size) - get_size_rank(entity_b.stats.size)


# ============================================================
# GRAPPLE RULES (PHB p.195)
# ============================================================
# - Replaces one Attack in the Attack action (not the whole action).
# - Attacker makes Athletics check vs target's Athletics or Acrobatics (target chooses).
# - Target must be no more than ONE size larger than the grappler.
# - Grappled condition: speed becomes 0, can't benefit from speed bonuses.
# - Grapple ends if:
#   a) Grappler is incapacitated
#   b) Effect moves grappled creature out of grappler's reach
#   c) Grappled creature uses action to escape (Athletics or Acrobatics vs grappler's Athletics)
# - Moving a grappled creature: grappler's speed is HALVED while dragging/carrying,
#   unless the grappled creature is two or more sizes smaller.

def can_grapple(grappler: "Entity", target: "Entity") -> Tuple[bool, str]:
    """
    Check if grappler can attempt to grapple target.
    Returns (allowed, reason).

    PHB p.195:
    - Must have a free hand (we don't track hands, so we allow it).
    - Target must be no more than one size larger.
    - Grappler must not be incapacitated.
    """
    if grappler.is_incapacitated():
        return False, "Grappler is incapacitated"

    diff = size_difference(target, grappler)  # positive = target is larger
    if diff > 1:
        return False, f"{target.name} is too large to grapple ({target.stats.size} vs {grappler.stats.size})"

    return True, ""


def resolve_grapple(grappler: "Entity", target: "Entity") -> Tuple[bool, str]:
    """
    Resolve a grapple attempt.

    PHB p.195: Contested check.
    Grappler: Athletics check
    Target: Athletics OR Acrobatics (whichever is higher - AI picks best)

    Returns (success, log_message).
    """
    allowed, reason = can_grapple(grappler, target)
    if not allowed:
        return False, reason

    # Check target condition immunities
    if "Grappled" in [c.lower() if isinstance(c, str) else c for c in target.stats.condition_immunities]:
        return False, f"{target.name} is immune to being Grappled"

    # Grappler rolls Athletics
    grappler_bonus = grappler.get_skill_bonus("Athletics")
    if grappler_bonus == 0:
        grappler_bonus = grappler.get_modifier("Strength")
    else:
        grappler_bonus = max(grappler_bonus, grappler.get_modifier("Strength"))
    grappler_roll = random.randint(1, 20) + grappler_bonus

    # Target rolls Athletics or Acrobatics (whichever is better)
    target_athletics = target.get_skill_bonus("Athletics")
    if target_athletics == 0:
        target_athletics = target.get_modifier("Strength")
    target_acrobatics = target.get_skill_bonus("Acrobatics")
    if target_acrobatics == 0:
        target_acrobatics = target.get_modifier("Dexterity")
    target_bonus = max(target_athletics, target_acrobatics)
    target_roll = random.randint(1, 20) + target_bonus

    if grappler_roll >= target_roll:
        return True, (f"{grappler.name} grapples {target.name}! "
                      f"(Athletics {grappler_roll} vs {target_roll})")
    else:
        return False, (f"{grappler.name} fails to grapple {target.name}. "
                       f"(Athletics {grappler_roll} vs {target_roll})")


def resolve_grapple_escape(grappled: "Entity", grappler: "Entity") -> Tuple[bool, str]:
    """
    Resolve a grapple escape attempt (uses grappled creature's action).

    PHB p.195: Grappled creature uses action to escape.
    Contested: target's Athletics or Acrobatics vs grappler's Athletics.
    """
    # Grappler's Athletics
    grappler_bonus = grappler.get_skill_bonus("Athletics")
    if grappler_bonus == 0:
        grappler_bonus = grappler.get_modifier("Strength")
    grappler_roll = random.randint(1, 20) + grappler_bonus

    # Escapee's Athletics or Acrobatics
    esc_athletics = grappled.get_skill_bonus("Athletics")
    if esc_athletics == 0:
        esc_athletics = grappled.get_modifier("Strength")
    esc_acrobatics = grappled.get_skill_bonus("Acrobatics")
    if esc_acrobatics == 0:
        esc_acrobatics = grappled.get_modifier("Dexterity")
    esc_bonus = max(esc_athletics, esc_acrobatics)
    esc_roll = random.randint(1, 20) + esc_bonus

    if esc_roll >= grappler_roll:
        return True, (f"{grappled.name} breaks free from {grappler.name}'s grapple! "
                      f"({esc_roll} vs {grappler_roll})")
    else:
        return False, (f"{grappled.name} fails to escape {grappler.name}'s grapple. "
                       f"({esc_roll} vs {grappler_roll})")


def get_grapple_drag_speed_multiplier(grappler: "Entity", grappled: "Entity") -> float:
    """
    PHB p.195: When you move, you can drag or carry the grappled creature with
    you, but your speed is halved, unless the creature is two or more sizes
    smaller than you.
    """
    diff = size_difference(grappler, grappled)  # positive = grappler is bigger
    if diff >= 2:
        return 1.0  # No penalty
    return 0.5  # Half speed


# ============================================================
# SHOVE RULES (PHB p.195-196)
# ============================================================
# - Replaces one Attack in the Attack action.
# - Contested check: attacker's Athletics vs target's Athletics or Acrobatics.
# - Target must be no more than ONE size larger.
# - On success: knock prone OR push 5 feet away.

def can_shove(shover: "Entity", target: "Entity") -> Tuple[bool, str]:
    """
    Check if shover can attempt to shove target.

    PHB p.195:
    - Target must be no more than one size larger.
    - Shover must not be incapacitated.
    """
    if shover.is_incapacitated():
        return False, "Shover is incapacitated"

    diff = size_difference(target, shover)  # positive = target is larger
    if diff > 1:
        return False, f"{target.name} is too large to shove ({target.stats.size} vs {shover.stats.size})"

    return True, ""


def resolve_shove(shover: "Entity", target: "Entity", prone: bool = True) -> Tuple[bool, str]:
    """
    Resolve a shove attempt.

    PHB p.195: Contested check.
    Shover: Athletics
    Target: Athletics or Acrobatics (target's choice, AI picks best)

    prone=True -> knock prone; prone=False -> push 5ft away
    Returns (success, log_message).
    """
    allowed, reason = can_shove(shover, target)
    if not allowed:
        return False, reason

    # Shover rolls Athletics
    shover_bonus = shover.get_skill_bonus("Athletics")
    if shover_bonus == 0:
        shover_bonus = shover.get_modifier("Strength")
    else:
        shover_bonus = max(shover_bonus, shover.get_modifier("Strength"))
    shover_roll = random.randint(1, 20) + shover_bonus

    # Target rolls Athletics or Acrobatics
    target_athletics = target.get_skill_bonus("Athletics")
    if target_athletics == 0:
        target_athletics = target.get_modifier("Strength")
    target_acrobatics = target.get_skill_bonus("Acrobatics")
    if target_acrobatics == 0:
        target_acrobatics = target.get_modifier("Dexterity")
    target_bonus = max(target_athletics, target_acrobatics)
    target_roll = random.randint(1, 20) + target_bonus

    effect = "prone" if prone else "pushed 5 ft"
    if shover_roll >= target_roll:
        return True, (f"{shover.name} shoves {target.name} ({effect})! "
                      f"(Athletics {shover_roll} vs {target_roll})")
    else:
        return False, (f"{shover.name} fails to shove {target.name}. "
                       f"(Athletics {shover_roll} vs {target_roll})")


# ============================================================
# PRONE + GRAPPLE INTERACTION (PHB p.190-191, p.195)
# ============================================================
# KEY RULE: Standing up from Prone costs half your movement speed.
# If your speed is 0 (e.g. from Grappled condition), you CANNOT stand up.
# This makes Grapple + Shove Prone a devastating combo.

def can_stand_from_prone(entity: "Entity") -> Tuple[bool, str]:
    """
    PHB p.190-191: Standing up costs half your movement speed.
    You can't stand up if you don't have enough movement, or if your speed is 0.

    Critical interaction: Grappled creatures have speed 0, so they CANNOT stand
    from prone while grappled.
    """
    if not entity.has_condition("Prone"):
        return False, "Not prone"

    effective_speed = entity.get_speed()
    if effective_speed <= 0:
        # This catches Grappled, Restrained, Stunned, etc.
        reasons = []
        if entity.has_condition("Grappled"):
            reasons.append("grappled (speed 0)")
        if entity.has_condition("Restrained"):
            reasons.append("restrained (speed 0)")
        if entity.has_condition("Stunned"):
            reasons.append("stunned")
        if entity.has_condition("Paralyzed"):
            reasons.append("paralyzed")
        reason_str = ", ".join(reasons) if reasons else "speed is 0"
        return False, f"Cannot stand: {reason_str}"

    # Check if enough movement left
    stand_cost = effective_speed / 2.0
    if entity.movement_left < stand_cost:
        return False, f"Not enough movement to stand ({entity.movement_left:.0f}/{stand_cost:.0f} ft needed)"

    return True, ""


def stand_from_prone_cost(entity: "Entity") -> float:
    """Return the movement cost to stand from prone (half total speed)."""
    return entity.get_speed() / 2.0


# ============================================================
# FRIGHTENED CONDITION (PHB p.290)
# ============================================================
# - Disadvantage on ability checks and attack rolls while source of fear is visible.
# - Can't willingly move closer to the source of its fear.
# - The condition ends if the source is no longer within line of sight.

def can_move_toward_fear_source(entity: "Entity", target_x: float, target_y: float,
                                 fear_source: "Entity") -> Tuple[bool, str]:
    """
    PHB p.290: A frightened creature can't willingly move closer to the source
    of its fear.

    Returns (allowed, reason).
    """
    if not entity.has_condition("Frightened") or not fear_source:
        return True, ""

    if fear_source.hp <= 0:
        return True, ""  # Source is dead, fear should end

    # Current distance to source
    current_dist = math.hypot(entity.grid_x - fear_source.grid_x,
                              entity.grid_y - fear_source.grid_y)
    # New distance after proposed move
    new_dist = math.hypot(target_x - fear_source.grid_x,
                          target_y - fear_source.grid_y)

    if new_dist < current_dist - 0.1:  # Small tolerance for floating point
        return False, f"Frightened: cannot move closer to {fear_source.name}"

    return True, ""


# ============================================================
# LEGENDARY ACTIONS (MM p.11)
# ============================================================
# - A legendary creature can take a certain number of legendary actions,
#   choosing from the options defined for that creature.
# - Only ONE legendary action can be used at a time, and only at the END of
#   another creature's turn.
# - A creature regains spent legendary actions at the start of its turn.
# - Legendary actions can't be used while incapacitated or otherwise unable to
#   take actions.

def can_use_legendary_action(entity: "Entity") -> Tuple[bool, str]:
    """Check if entity can use a legendary action right now."""
    if entity.legendary_actions_left <= 0:
        return False, "No legendary actions remaining"
    if entity.is_incapacitated():
        return False, "Incapacitated - cannot use legendary actions"
    if entity.hp <= 0:
        return False, "Defeated"
    return True, ""


# ============================================================
# LEGENDARY RESISTANCE (MM p.11)
# ============================================================
# - When a legendary creature fails a saving throw, it can choose to
#   succeed instead. Limited uses per day (usually 3).

def can_use_legendary_resistance(entity: "Entity") -> bool:
    """Check if entity can use legendary resistance."""
    return entity.legendary_resistances_left > 0 and entity.hp > 0


def use_legendary_resistance(entity: "Entity") -> str:
    """Use one legendary resistance. Returns log message."""
    entity.legendary_resistances_left -= 1
    remaining = entity.legendary_resistances_left
    return (f"{entity.name} uses Legendary Resistance! (Automatic save success, "
            f"{remaining} remaining)")


# Conditions that are severe enough to always warrant LR usage
_LR_ALWAYS_USE_CONDITIONS = {
    "Stunned", "Paralyzed", "Petrified", "Banished", "Unconscious",
    "Dominated", "Incapacitated", "Polymorphed",
}
# Conditions worth using LR if the creature has 2+ remaining
_LR_MODERATE_CONDITIONS = {
    "Frightened", "Charmed", "Blinded", "Restrained", "Prone",
    "Deafened", "Poisoned", "Grappled", "Slowed",
}


def _should_use_legendary_resistance(entity, applies_condition: str, damage_dice: str) -> bool:
    """Strategic LR decision. Always use for save-or-suck, conserve for minor effects."""
    lr_left = entity.legendary_resistances_left

    # Severe conditions: always use LR
    if applies_condition in _LR_ALWAYS_USE_CONDITIONS:
        return True

    # Moderate conditions: use if 2+ LR left
    if applies_condition in _LR_MODERATE_CONDITIONS:
        return lr_left >= 2

    # Any other named condition: use if 3+ LR left
    if applies_condition:
        return lr_left >= 3

    # Damage-only save (no condition): only use LR if damage would be
    # lethal or near-lethal (> 40% of remaining HP)
    if damage_dice:
        from engine.dice import average_damage
        avg = average_damage(damage_dice)
        if avg >= entity.hp * 0.4:
            return True

    # Minor effect with no condition and low damage: conserve LR
    return False


# ============================================================
# LAIR ACTIONS (MM p.11)
# ============================================================
# - On initiative count 20 (losing initiative ties), the creature can use
#   a lair action to cause one of the following effects:
# - The creature can't use the same lair action two rounds in a row.
# - Lair actions are NOT available outside the creature's lair.
# - We track lair activation in the main menu (setting is_lair_active on the battle).

LAIR_INITIATIVE = 20  # Lair actions always happen at initiative 20


def should_use_lair_action(owner: "Entity") -> bool:
    """Check if a lair owner should use their lair action this round."""
    if owner.hp <= 0:
        return False
    if owner.is_incapacitated():
        return False
    lair_actions = [a for a in owner.stats.actions if a.action_type == "lair"]
    return len(lair_actions) > 0


# ============================================================
# RESISTANCE & IMMUNITY (PHB p.197)
# ============================================================
# - Resistance: take half damage of that type (rounded down).
# - Vulnerability: take double damage.
# - Immunity: take zero damage.
# - Multiple sources of resistance/vulnerability don't stack.

def apply_damage_modifiers(amount: int, damage_type: str, target: "Entity") -> int:
    """
    Apply resistance, immunity, and vulnerability to damage.
    Returns modified damage amount.

    PHB p.197: If a creature has resistance AND vulnerability to same type,
    they cancel out. Multiple instances of same modifier don't stack.
    """
    if amount <= 0 or not damage_type:
        return amount

    dtype_lower = damage_type.lower()

    # Check immunity first
    if dtype_lower in [x.lower() for x in target.stats.damage_immunities]:
        return 0

    is_resistant = dtype_lower in [x.lower() for x in target.stats.damage_resistances]
    is_vulnerable = dtype_lower in [x.lower() for x in target.stats.damage_vulnerabilities]

    # Rage resistance to B/P/S
    if target.rage_active and dtype_lower in ("bludgeoning", "piercing", "slashing"):
        is_resistant = True

    # Petrified: resistance to all damage
    if target.has_condition("Petrified"):
        is_resistant = True

    # If both resistant and vulnerable, they cancel
    if is_resistant and is_vulnerable:
        return amount
    if is_resistant:
        return amount // 2
    if is_vulnerable:
        return amount * 2

    return amount


# ============================================================
# CONDITION IMMUNITY CHECKS
# ============================================================

def is_immune_to_condition(entity: "Entity", condition: str) -> bool:
    """Check if entity is immune to a specific condition."""
    return condition in entity.stats.condition_immunities


# ============================================================
# ATTACK ADVANTAGE / DISADVANTAGE RESOLUTION (PHB p.173)
# ============================================================
# If you have both advantage and disadvantage, they cancel out regardless
# of how many sources of each you have.

def resolve_advantage_disadvantage(has_advantage: bool, has_disadvantage: bool) -> str:
    """
    PHB p.173: If circumstances cause a roll to have both advantage and
    disadvantage, you are considered to have neither. This is true even if
    multiple circumstances impose disadvantage and only one grants advantage,
    or vice versa.

    Returns: "advantage", "disadvantage", or "normal"
    """
    if has_advantage and has_disadvantage:
        return "normal"
    if has_advantage:
        return "advantage"
    if has_disadvantage:
        return "disadvantage"
    return "normal"


# ============================================================
# SAVING THROW RULES
# ============================================================

def make_saving_throw(entity: "Entity", ability: str, dc: int,
                      battle: "BattleSystem" = None,
                      advantage: bool = False,
                      disadvantage: bool = False,
                      applies_condition: str = "",
                      damage_dice: str = "",
                      damage_type: str = "") -> Tuple[bool, int, str]:
    """
    Make a saving throw for an entity.

    Returns (success, total_roll, log_message).
    Handles:
    - Legendary Resistance
    - Advantage/Disadvantage
    - Auto-fail from conditions (Paralyzed/Stunned/Unconscious fail STR/DEX)
    - Magic Resistance (advantage on saves vs spells)
    """
    from data.conditions import CONDITION_EFFECTS

    # Auto-fail STR/DEX saves for certain conditions
    ability_lower = ability.lower()
    for cond in entity.conditions:
        effects = CONDITION_EFFECTS.get(cond, {})
        if ability_lower in ("strength", "str") and effects.get("fail_str_save"):
            # Legendary Resistance can override auto-fail
            if can_use_legendary_resistance(entity):
                msg = use_legendary_resistance(entity)
                return True, 0, msg
            return False, 0, f"{entity.name} auto-fails {ability} save ({cond})"
        if ability_lower in ("dexterity", "dex") and effects.get("fail_dex_save"):
            if can_use_legendary_resistance(entity):
                msg = use_legendary_resistance(entity)
                return True, 0, msg
            return False, 0, f"{entity.name} auto-fails {ability} save ({cond})"

    # Calculate bonus
    if battle:
        bonus = battle.get_total_save_bonus(entity, ability)
    else:
        bonus = entity.get_save_bonus(ability)

    # Check for Magic Resistance feature
    has_magic_resistance = any(
        f.name == "Magic Resistance" or f.mechanic == "magic_resistance"
        for f in entity.stats.features
    )
    if has_magic_resistance:
        advantage = True

    # Gnome Cunning: advantage on INT/WIS/CHA saves vs magic
    if any(rt.mechanic == "gnome_cunning" for rt in entity.stats.racial_traits):
        if ability_lower in ("intelligence", "wisdom", "charisma", "int", "wis", "cha"):
            advantage = True

    # PHB p.291: Exhaustion level 3+ gives disadvantage on attack rolls AND saving throws
    if entity.exhaustion >= 3:
        disadvantage = True

    # Conditions that impose disadvantage on DEX saves (Restrained, Slowed)
    if ability_lower in ("dexterity", "dex"):
        for cond in entity.conditions:
            effects = CONDITION_EFFECTS.get(cond, {})
            if effects.get("dex_save_disadvantage"):
                disadvantage = True
                break

    # Danger Sense (Barbarian): advantage on DEX saves you can see
    if entity.has_feature("danger_sense") and ability_lower in ("dexterity", "dex"):
        if not entity.has_condition("Blinded") and not entity.is_incapacitated():
            advantage = True

    # Fey Ancestry (Elf/Half-Elf): advantage on saves vs being Charmed
    if any(rt.mechanic == "fey_ancestry" for rt in entity.stats.racial_traits):
        if applies_condition and applies_condition.lower() in ("charmed",):
            advantage = True

    # Brave (Halfling): advantage on saves vs being Frightened
    if any(rt.mechanic == "brave" for rt in entity.stats.racial_traits):
        if applies_condition and applies_condition.lower() in ("frightened",):
            advantage = True

    # Dwarven Resilience / Stout Resilience (PHB p.20/p.28):
    # Advantage on saves against poison (both the Poisoned condition AND poison damage)
    if any(rt.mechanic in ("dwarven_resilience", "stout_resilience")
           for rt in entity.stats.racial_traits):
        is_poison_related = (
            (applies_condition and applies_condition.lower() == "poisoned")
            or (damage_type and damage_type.lower() == "poison")
        )
        if is_poison_related:
            advantage = True

    # Resolve advantage/disadvantage
    roll_type = resolve_advantage_disadvantage(advantage, disadvantage)

    if roll_type == "advantage":
        r1 = random.randint(1, 20)
        r2 = random.randint(1, 20)
        roll = max(r1, r2)
    elif roll_type == "disadvantage":
        r1 = random.randint(1, 20)
        r2 = random.randint(1, 20)
        roll = min(r1, r2)
    else:
        roll = random.randint(1, 20)

    total = roll + bonus
    success = total >= dc

    # Legendary Resistance on failure (MM p.11: creature CHOOSES to succeed)
    # Strategic usage: save LR for dangerous effects, don't burn on minor damage
    if not success and can_use_legendary_resistance(entity):
        should_use_lr = _should_use_legendary_resistance(
            entity, applies_condition, damage_dice)
        if should_use_lr:
            msg = use_legendary_resistance(entity)
            return True, total, msg

    status = "SUCCESS" if success else "FAIL"
    adv_str = f" ({roll_type})" if roll_type != "normal" else ""
    msg = f"{entity.name} {ability} save: {total} (d20={roll}+{bonus}){adv_str} vs DC {dc} -> {status}"
    return success, total, msg


# ============================================================
# MOVEMENT THROUGH CREATURES (PHB p.191)
# ============================================================
# - You can move through a nonhostile creature's space.
# - You can move through a hostile creature's space only if it is at least
#   two sizes larger or smaller than you.
# - Another creature's space is difficult terrain for you.
# - You can't willingly end your move in another creature's space.

def can_move_through_creature(mover: "Entity", blocker: "Entity") -> bool:
    """
    PHB p.191: Can the mover pass through the blocker's space?
    """
    if mover.is_player == blocker.is_player:
        return True  # Allied creatures

    diff = abs(size_difference(mover, blocker))
    if diff >= 2:
        return True  # Two+ sizes apart

    # Halfling Nimbleness: can move through space of any creature larger
    if any(rt.mechanic == "halfling_nimbleness" for rt in mover.stats.racial_traits):
        if get_size_rank(blocker.stats.size) > get_size_rank(mover.stats.size):
            return True

    return False


# ============================================================
# OPPORTUNITY ATTACK RULES (PHB p.195)
# ============================================================
# - When a hostile creature you can see moves out of your reach, you can use
#   your reaction to make one melee attack against it.
# - The attack interrupts the provoking creature's movement.
# - Doesn't trigger if you Disengage.
# - Doesn't trigger if moved by forced movement (shove, spell effect).

def can_make_opportunity_attack(reactor: "Entity", mover: "Entity",
                                 was_adjacent: bool, is_adjacent_now: bool) -> bool:
    """Check if reactor can make an opportunity attack against mover."""
    if reactor.hp <= 0:
        return False
    if reactor.reaction_used:
        return False
    if reactor.is_incapacitated():
        return False
    if mover.is_disengaging:
        # Sentinel feat overrides Disengage
        if not reactor.has_feature("sentinel"):
            return False
    if reactor.is_player == mover.is_player:
        return False  # Same team
    if not was_adjacent:
        return False
    if is_adjacent_now:
        return False  # Still in reach, didn't leave
    return True


# ============================================================
# CONCENTRATION RULES (PHB p.203)
# ============================================================
# - When you take damage while concentrating, make a Constitution saving throw.
# - DC = 10 or half the damage taken, whichever is higher.
# - If you cast another concentration spell, you lose concentration on the first.
# - If you are incapacitated or killed, you lose concentration.

def concentration_save_dc(damage_taken: int) -> int:
    """Calculate the DC for a concentration saving throw."""
    return max(10, damage_taken // 2)


# ============================================================
# COVER RULES (PHB p.196)
# ============================================================
# Half cover: +2 AC, +2 DEX saves
# Three-quarters cover: +5 AC, +5 DEX saves
# Total cover: can't be targeted directly

COVER_BONUSES = {
    "none": 0,
    "half": 2,
    "three_quarters": 5,
    "total": 999,  # Can't target
}


# ============================================================
# EXHAUSTION (PHB p.291)
# ============================================================
EXHAUSTION_EFFECTS = {
    1: "Disadvantage on ability checks",
    2: "Speed halved",
    3: "Disadvantage on attack rolls and saving throws",
    4: "Hit point maximum halved",
    5: "Speed reduced to 0",
    6: "Death",
}


def get_exhaustion_effects(level: int) -> list:
    """Return all active exhaustion effects at the given level (cumulative)."""
    effects = []
    for lvl in range(1, min(level + 1, 7)):
        if lvl in EXHAUSTION_EFFECTS:
            effects.append(EXHAUSTION_EFFECTS[lvl])
    return effects
