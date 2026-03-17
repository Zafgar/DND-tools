"""
Backward-compatible re-export module.
All classes have been split into separate files for maintainability.
Import from here still works for existing code.
"""
# Base classes and modals
from states.game_state_base import (
    GameState, ScenarioModal, NotesModal, EffectModal, CampaignPickerModal, SAVES_DIR,
)

# Menu
from states.menu_state import MenuState

# Encounter setup
from states.encounter_setup import EncounterSetupState

# Battle (the largest module)
from states.battle_state import (
    BattleState, FloatingText, ImpactFlash, WeatherParticle,
    PANEL_W, TOP_BAR_H, GRID_W, TABS,
    DAMAGE_TYPE_COLORS, CONDITION_BADGES,
)

__all__ = [
    "GameState", "ScenarioModal", "NotesModal", "EffectModal", "CampaignPickerModal",
    "MenuState", "EncounterSetupState", "BattleState",
    "FloatingText", "ImpactFlash", "WeatherParticle",
    "PANEL_W", "TOP_BAR_H", "GRID_W", "TABS", "SAVES_DIR",
    "DAMAGE_TYPE_COLORS", "CONDITION_BADGES",
]
