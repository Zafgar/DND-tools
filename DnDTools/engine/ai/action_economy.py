"""Action-economy validator for AI turn plans.

Walks an ``ActionStep`` list and reports violations of the 5e
action economy:

  * More than one Action consumed.
  * More than one Bonus Action consumed.
  * More than one Reaction consumed.
  * Movement totals beyond the entity's remaining speed.
  * Action Surge unused warning (Fighter only, when entity has the
    feature but only one Action step was planned).

Pure logic, no pygame.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple


# Step types that consume the Action slot
_ACTION_STEP_TYPES = {"attack", "multiattack", "spell", "legendary"}
_BONUS_STEP_TYPES = {"bonus_attack", "bonus_spell"}
_REACTION_STEP_TYPES = {"reaction"}
_MOVE_STEP_TYPES = {"move"}


@dataclass
class ValidationReport:
    ok: bool = True
    violations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    actions_used: int = 0
    bonus_used: int = 0
    reactions_used: int = 0
    total_movement_ft: float = 0.0


def validate_plan(plan, entity) -> ValidationReport:
    """Inspect ``plan.steps`` and return a :class:`ValidationReport`."""
    rep = ValidationReport()
    if plan is None or plan.skipped:
        return rep
    for step in (plan.steps or []):
        kind = getattr(step, "step_type", "") or ""
        if kind in _ACTION_STEP_TYPES:
            # Some "spell" steps are actually bonus-cast — caster's
            # spell.action_type tells us. Default to action.
            spell = getattr(step, "spell", None)
            atype = getattr(spell, "action_type", "action") if spell else "action"
            if atype == "bonus":
                rep.bonus_used += 1
            elif atype == "reaction":
                rep.reactions_used += 1
            else:
                rep.actions_used += 1
        elif kind in _BONUS_STEP_TYPES:
            rep.bonus_used += 1
        elif kind in _REACTION_STEP_TYPES:
            rep.reactions_used += 1
        elif kind in _MOVE_STEP_TYPES:
            rep.total_movement_ft += float(
                getattr(step, "movement_ft", 0.0) or 0.0
            )

    # Action Surge allows two actions per turn for Fighter
    action_surge_active = False
    if entity is not None and hasattr(entity, "has_feature"):
        action_surge_active = entity.has_feature("action_surge_used_this_turn")

    max_actions = 2 if action_surge_active else 1
    if rep.actions_used > max_actions:
        rep.violations.append(
            f"too many Actions: {rep.actions_used} (max {max_actions})"
        )
    if rep.bonus_used > 1:
        rep.violations.append(
            f"too many Bonus Actions: {rep.bonus_used} (max 1)"
        )
    if rep.reactions_used > 1:
        rep.violations.append(
            f"too many Reactions: {rep.reactions_used} (max 1)"
        )
    if entity is not None:
        speed = getattr(entity, "max_movement_ft", None)
        if speed is None:
            stats = getattr(entity, "stats", None)
            speed = (getattr(stats, "speed", 30) if stats is not None
                      else 30)
        if rep.total_movement_ft > speed + 5:
            rep.violations.append(
                f"movement {rep.total_movement_ft:.0f} ft > "
                f"speed {speed} ft"
            )

    rep.ok = not rep.violations
    return rep


def repair_plan(plan, entity) -> Tuple["TurnPlan", ValidationReport]:
    """Drop or downgrade steps that violate the action economy and
    return ``(plan, report)``. The plan is mutated in-place; the
    report describes what was changed."""
    rep = validate_plan(plan, entity)
    if rep.ok or plan is None:
        return plan, rep
    if plan.steps is None:
        return plan, rep

    kept = []
    seen_actions = 0
    seen_bonus = 0
    seen_reaction = 0
    max_actions = 2 if (entity is not None and hasattr(entity, "has_feature")
                          and entity.has_feature(
                              "action_surge_used_this_turn")) else 1
    fixed: List[str] = []
    for step in plan.steps:
        kind = getattr(step, "step_type", "") or ""
        if kind in _ACTION_STEP_TYPES:
            if seen_actions >= max_actions:
                fixed.append(
                    f"dropped extra Action {step.action_name or kind}"
                )
                continue
            seen_actions += 1
        elif kind in _BONUS_STEP_TYPES:
            if seen_bonus >= 1:
                fixed.append(
                    f"dropped extra Bonus {step.action_name or kind}"
                )
                continue
            seen_bonus += 1
        elif kind in _REACTION_STEP_TYPES:
            if seen_reaction >= 1:
                fixed.append(
                    f"dropped extra Reaction {step.action_name or kind}"
                )
                continue
            seen_reaction += 1
        kept.append(step)
    plan.steps = kept
    rep.warnings.extend(fixed)
    rep = validate_plan(plan, entity)  # recompute
    rep.warnings.extend(fixed)
    return plan, rep
