"""Global accessor for DMG/optional-rule toggles.

Flags are populated from the active campaign's ``settings`` dict so that
engine code (Entity, BattleSystem, AI) can query variant behaviour without
plumbing the Campaign object through every call site.
"""
from typing import Dict

_DEFAULTS: Dict[str, bool] = {
    "flanking_advantage": False,          # DMG p.251: flanking grants adv on melee
    "slow_natural_healing": False,        # DMG p.267: long rest no longer heals HP
    "gritty_realism": False,              # DMG p.267: short = 8h, long = 7d
    "healers_kit_required": False,        # DMG p.266: hit-dice spend consumes kit
    "cleaving_through_creatures": False,  # DMG p.272: kill-on-hit grants extra swing
}

_FLAGS: Dict[str, bool] = dict(_DEFAULTS)


def get(flag_name: str) -> bool:
    return _FLAGS.get(flag_name, False)


def set_flag(name: str, value: bool) -> None:
    if name in _FLAGS:
        _FLAGS[name] = bool(value)


def get_all() -> Dict[str, bool]:
    return dict(_FLAGS)


def reset_to_defaults() -> None:
    _FLAGS.clear()
    _FLAGS.update(_DEFAULTS)


def load_from_campaign(settings) -> None:
    """Populate active flags from a Campaign.settings dict. Unknown keys
    are ignored; missing keys fall back to defaults."""
    reset_to_defaults()
    if not settings:
        return
    for key in _DEFAULTS:
        if key in settings:
            _FLAGS[key] = bool(settings[key])
