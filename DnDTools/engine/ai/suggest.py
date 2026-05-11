"""Suggest-only mode — plan a turn without consuming the entity's
action economy.

The full ``TacticalAI.calculate_turn`` is meant to drive an actual
turn: it mutates ``entity.bonus_action_used`` flags, spends feature
uses, etc. For "what would the AI do here?" suggestions (used by
the human-driven turn UI's hint panel), we want a *dry-run* plan.

``suggest_turn(entity, battle)`` snapshots the mutated fields,
delegates to the planner, then restores the snapshot before
returning the plan. The plan steps reference the live entity but
their execution is the caller's responsibility.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict


# Fields the planner mutates as part of "consuming" a step
_SNAPSHOT_ATTRS = (
    "action_used", "bonus_action_used", "reaction_used",
    "movement_left", "reckless_attack_active",
    "feature_uses", "spell_slots",
    "rage_active", "rage_rounds",
    "ki_points_left", "sorcery_points_left",
    "lay_on_hands_left", "bardic_inspiration_left",
    "legendary_actions_left", "legendary_resistances_left",
    "hit_dice_remaining", "death_save_successes",
    "death_save_failures", "is_stable",
)


def _snapshot(entity) -> Dict[str, Any]:
    snap: Dict[str, Any] = {}
    for name in _SNAPSHOT_ATTRS:
        if hasattr(entity, name):
            val = getattr(entity, name)
            snap[name] = deepcopy(val)
    return snap


def _restore(entity, snap: Dict[str, Any]):
    for name, val in snap.items():
        try:
            setattr(entity, name, val)
        except Exception:
            pass


def suggest_turn(entity, battle, ai=None):
    """Return the plan that ``ai.calculate_turn(entity, battle)``
    would produce, WITHOUT permanently consuming any of the entity's
    resources.

    ``ai`` defaults to ``battle.ai``.  Caller can then prompt the
    DM "execute this plan?" and only call the real planner (which
    DOES consume resources) on confirm.
    """
    if ai is None:
        ai = battle.ai
    snap = _snapshot(entity)
    try:
        plan = ai.calculate_turn(entity, battle)
    finally:
        _restore(entity, snap)
    return plan


def describe_plan(plan) -> str:
    """Compact human-readable rendering of a plan for a suggestion
    tooltip. Empty string when the plan is skipped or has no steps."""
    if plan is None or plan.skipped:
        return f"Skip — {getattr(plan, 'skip_reason', '') or 'no action'}"
    lines = []
    for step in (plan.steps or []):
        desc = getattr(step, "description", "") or getattr(
            step, "action_name", "") or step.step_type
        lines.append(f"• {desc}")
    return "\n".join(lines)
