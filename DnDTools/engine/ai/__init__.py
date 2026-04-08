"""
D&D 5e 2014 Tactical AI for NPCs and Auto-Battle Heroes.
Re-exports all public symbols so that existing imports like
    from engine.ai import TacticalAI, TurnPlan, ActionStep
continue to work unchanged.
"""
from engine.ai.models import ActionStep, TurnPlan
from engine.ai.constants import *
from engine.ai.utils import _get_effective_caster_level, _get_spell_damage_dice
from engine.ai.tactical_ai import TacticalAI

__all__ = [
    "ActionStep",
    "TurnPlan",
    "TacticalAI",
    "_get_effective_caster_level",
    "_get_spell_damage_dice",
]
