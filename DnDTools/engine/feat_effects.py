"""Phase 30 — feat-effect helpers.

Central place for the combat-relevant runtime logic of feats from
:mod:`data.feats`.  Each helper consults ``entity.has_feature(<key>)``
and is called from the appropriate engine path:

  * :func:`mobile_speed_bonus` — Entity.get_speed
  * :func:`apply_elemental_adept` — Entity.take_damage
  * :func:`reroll_savage_attacker` — damage-roll site (post-roll
    reroll-once-per-turn for weapon attacks)
  * :func:`defensive_duelist_ac_bonus` — incoming-melee-attack path
  * :func:`mage_slayer_concentration_disadvantage` — concentration
    saves when the breaker is in melee with a Mage Slayer
  * :func:`polearm_butt_attack` — AI bonus-action selector
  * :func:`shield_master_shove` — AI bonus-action selector
  * :func:`charger_attack_bonus` — Charger dash-and-attack variant

Pure logic, no pygame.  Every helper is a no-op when the entity
lacks the relevant feat, so engine paths can call unconditionally.
"""
from __future__ import annotations

import random
from typing import Optional, Tuple

from data.feats import get_feat


# --------------------------------------------------------------------- #
# Mobile — +10 ft speed.  PHB p.168 also grants no-OA-after-attack and
# difficult-terrain-ignored-while-dashing, but those are AI-level
# tactics layered on top of this base bonus.
# --------------------------------------------------------------------- #

def mobile_speed_bonus(entity) -> int:
    return 10 if entity.has_feature("mobile") else 0


# --------------------------------------------------------------------- #
# Elemental Adept — ignore resistance to one damage type and treat any
# damage die that rolls a 1 as a 2.  ``mechanic_value`` carries the
# damage type ("fire", "cold", "acid", "lightning", "thunder").
# --------------------------------------------------------------------- #

def elemental_adept_type(entity) -> str:
    """Return the damage type this entity has Elemental Adept for, or """""
    f = entity.get_feature("elemental_adept")
    return (f.mechanic_value if f else "") or ""


def caster_ignores_resistance(caster, damage_type: str) -> bool:
    """Caster's Elemental Adept bypasses target's resistance to the
    matching damage type."""
    if not caster:
        return False
    return (elemental_adept_type(caster).lower()
             == (damage_type or "").lower()
             and elemental_adept_type(caster) != "")


def apply_elemental_adept_dice_floor(roll_list, caster,
                                       damage_type: str):
    """In-place: any 1 in roll_list becomes a 2 when the caster has
    Elemental Adept for ``damage_type``."""
    if not roll_list or not caster:
        return roll_list
    if not caster_ignores_resistance(caster, damage_type):
        return roll_list
    return [max(2, r) for r in roll_list]


# --------------------------------------------------------------------- #
# Savage Attacker — once per turn, on a weapon attack, reroll the
# damage dice and take the higher total.  We expose a flag and a
# helper; the AI damage path calls it.
# --------------------------------------------------------------------- #

def savage_attacker_reroll(entity, dice_expr: str,
                             rolled_total: int) -> int:
    """Return the better of (rolled_total) and a fresh re-roll, if
    Savage Attacker is available this turn.  Marks the feat as used."""
    if not entity.has_feature("savage_attacker"):
        return rolled_total
    if getattr(entity, "savage_attacker_used", False):
        return rolled_total
    from engine.dice import roll_dice
    fresh = roll_dice(dice_expr) if dice_expr else 0
    entity.savage_attacker_used = True
    return max(rolled_total, fresh)


# --------------------------------------------------------------------- #
# Defensive Duelist — when hit by a melee attack while wielding a
# finesse weapon, react to add proficiency bonus to AC.
# --------------------------------------------------------------------- #

def defensive_duelist_ac_bonus(entity, attack_total: int,
                                  current_ac: int,
                                  is_melee: bool) -> int:
    """Return ``current_ac`` plus any DD reaction bonus that the
    entity would burn to convert a hit into a miss.  Returns the
    original AC unchanged when the feat doesn't apply or the boost
    wouldn't change the outcome."""
    if not entity.has_feature("defensive_duelist"):
        return current_ac
    if not is_melee:
        return current_ac
    if getattr(entity, "reaction_used", False):
        return current_ac
    # Only burn the reaction if the bump would matter.
    pb = getattr(entity.stats, "proficiency_bonus", 2)
    if attack_total >= current_ac and attack_total < current_ac + pb:
        entity.reaction_used = True
        return current_ac + pb
    return current_ac


# --------------------------------------------------------------------- #
# Mage Slayer — when an adjacent enemy casts a spell you can see, you
# get an opportunity attack.  Also: that enemy has disadvantage on
# their concentration save against damage you deal.
# --------------------------------------------------------------------- #

def mage_slayer_oa_should_fire(observer, caster) -> bool:
    if not observer.has_feature("mage_slayer"):
        return False
    if getattr(observer, "reaction_used", False):
        return False
    if observer.hp <= 0:
        return False
    # Adjacent check: within 5 ft (1 square + diagonal)
    dx = abs(observer.grid_x - caster.grid_x)
    dy = abs(observer.grid_y - caster.grid_y)
    return max(dx, dy) <= 1


def mage_slayer_concentration_disadvantage(damager, victim) -> bool:
    """When ``victim`` rolls a concentration save vs damage dealt by
    ``damager``, the save has disadvantage if the damager has Mage
    Slayer and is adjacent."""
    if damager is None or victim is None:
        return False
    if not damager.has_feature("mage_slayer"):
        return False
    dx = abs(damager.grid_x - victim.grid_x)
    dy = abs(damager.grid_y - victim.grid_y)
    return max(dx, dy) <= 1


# --------------------------------------------------------------------- #
# Polearm Master — when wielding glaive/halberd/quarterstaff/spear,
# you get a bonus action attack with the butt end (1d4 + STR).  Also
# triggers OAs on enemies entering your reach.
# --------------------------------------------------------------------- #

_REACH_WEAPONS = {"glaive", "halberd", "quarterstaff", "spear",
                    "pike"}


def polearm_butt_attack_dice(entity, weapon_name: str) -> Optional[str]:
    """If the entity has Polearm Master and is wielding a qualifying
    weapon, return the butt-end damage expression ("1d4+STR mod")."""
    if not entity.has_feature("polearm_master"):
        return None
    if not weapon_name:
        return None
    wl = weapon_name.lower()
    if not any(w in wl for w in _REACH_WEAPONS):
        return None
    str_mod = entity.get_modifier("strength")
    sign = "+" if str_mod >= 0 else "-"
    return f"1d4{sign}{abs(str_mod)}"


# --------------------------------------------------------------------- #
# Shield Master — when you take the Attack action and a shield is
# equipped, you may use a bonus action to try to shove a creature
# within 5 ft.
# --------------------------------------------------------------------- #

def shield_master_can_shove(entity, attack_action_taken: bool,
                              has_shield: bool = True) -> bool:
    if not entity.has_feature("shield_master"):
        return False
    if not attack_action_taken:
        return False
    if not has_shield:
        return False
    if getattr(entity, "bonus_action_used", False):
        return False
    return True


# --------------------------------------------------------------------- #
# Charger — when you use your action to Dash, you may make a melee
# attack with +5 damage as a bonus action (or shove +10 ft).
# --------------------------------------------------------------------- #

def charger_bonus_damage(entity, dashed_this_turn: bool) -> int:
    if not entity.has_feature("charger"):
        return 0
    if not dashed_this_turn:
        return 0
    return 5


# --------------------------------------------------------------------- #
# Tough — already applied as +2 HP per level at hero creation.  This
# helper just confirms the feat is acknowledged (so the audit sees a
# reference) and can be used to display the bonus on the sheet.
# --------------------------------------------------------------------- #

def tough_hp_bonus(entity) -> int:
    if not entity.has_feature("tough"):
        return 0
    lvl = max(1, getattr(entity.stats, "character_level", 1))
    return 2 * lvl


# --------------------------------------------------------------------- #
# Resilient — proficiency in one saving throw.  ``mechanic_value`` is
# the ability code ("CON", "WIS", …).  Hero creator adds this to
# ``stats.saving_throws``.  Helper exists so audit + UI can verify.
# --------------------------------------------------------------------- #

_ABBR_TO_FULL = {
    "STR": "strength", "DEX": "dexterity", "CON": "constitution",
    "INT": "intelligence", "WIS": "wisdom", "CHA": "charisma",
}


def resilient_save_proficiency(entity) -> Optional[str]:
    """Return the lowercase ability name (e.g. ``"constitution"``)
    the entity is proficient in via Resilient, or None."""
    f = entity.get_feature("resilient")
    if not f or not f.mechanic_value:
        return None
    return _ABBR_TO_FULL.get(f.mechanic_value.upper())
