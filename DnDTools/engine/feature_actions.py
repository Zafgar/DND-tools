"""Using a character's abilities from the DM panel.

Clicking a feature used to tick a usage counter and write a line in the
log. Nothing else happened: Second Wind healed nobody, Action Surge
granted no action, Nature's Veil left the ranger perfectly visible.
Across the 47 hero sheets, 149 distinct abilities were reachable from
the panel and exactly two of them changed anything.

Most of those 149 do not need to be clicked at all — Sneak Attack,
Danger Sense, Great Weapon Master and seventy-odd others are applied by
the engine while it rolls, and a button for them is a lie. The 67 that a
player actually declares are the ones that need to work.

This module answers three questions about any feature:

  classify()   is this passive, a state you switch on, or a use?
  describe()   what will happen, in Finnish, before you commit
  activate()   do it — spend the resource and apply the effect

Named handlers cover the class features with real rules. Everything else
falls through to a reader that takes the feature's own description at its
word: dice to heal or grant as temporary hit points, a condition to
apply, a flight speed to gain, an extra action to hand back.
"""
from __future__ import annotations

import re

from engine.dice import roll_dice

# --------------------------------------------------------------------- #
# Classification
# --------------------------------------------------------------------- #
PASSIVE = "passive"      # the engine applies it; nothing to press
TOGGLE = "toggle"        # a state you switch on and off
USE = "use"              # spend it now for an effect

# Mechanics the engine reads while resolving rolls. A button for these
# would suggest the DM has to remember them, which is exactly backwards.
_ENGINE_APPLIED = {
    "sneak_attack", "danger_sense", "feral_instinct", "brutal_critical",
    "savage_attacks", "great_weapon_master", "sharpshooter", "alert",
    "lucky", "tough", "mobile", "magic_resistance", "pack_tactics",
    "evasion", "elusive", "fey_ancestry", "extra_attack",
    "extra_attack_2", "extra_attack_3", "fighting_style",
    "fighting_style_twf", "two_weapon_fighting", "dual_wielder",
    "improved_critical", "superior_critical", "colossus_slayer",
    "agonizing_blast", "empowered_evocation", "elemental_affinity",
    "divine_strike", "improved_divine_smite", "aura_of_protection",
    "aura_of_courage", "blindsense", "blindsight", "truesight",
    "devils_sight", "devil_sight", "water_breathing", "amphibious",
    "draconic_resilience", "survivor", "relentless_endurance",
    "heavy_armor_master", "defensive_duelist", "mage_slayer",
    "polearm_master", "crossbow_expert", "shield_master", "sentinel",
    "charger", "war_caster", "ki_empowered_strikes", "magic_weapons",
    "sculpt_spells", "totem_bear", "aggressive", "nimble_escape",
    "savage_attacker", "giants_might", "genies_wrath", "gathered_swarm",
    "dreadful_strikes", "wails_from_grave", "psionic_power",
    "regeneration", "fast_movement", "stunning_strike",
    "battle_master_maneuvers", "superiority_dice", "metamagic",
}

_TOGGLES = {
    "rage": "rage_active",
    "reckless_attack": "reckless_attack_active",
}

# Wording that means "the player declares this on their turn".
_DECLARED_WORDS = ("bonus action", "as an action", "action:", "reaction",
                   "spend", "expend", "1/", "/short rest", "/long rest",
                   "/day", "toiminto")


def _text(feature) -> str:
    return f"{getattr(feature, 'name', '')} " \
           f"{getattr(feature, 'description', '')}".lower()


def _mech(feature) -> str:
    return (getattr(feature, "mechanic", "") or "").strip().lower()


def classify(feature) -> str:
    """Passive, toggle or use."""
    mech = _mech(feature)
    if mech in _TOGGLES:
        return TOGGLE
    if mech in _ENGINE_APPLIED:
        return PASSIVE
    if getattr(feature, "uses_per_day", -1) > 0 or \
            getattr(feature, "recharge", ""):
        return USE
    txt = _text(feature)
    if any(w in txt for w in _DECLARED_WORDS):
        return USE
    return PASSIVE


# --------------------------------------------------------------------- #
# Reading a feature's own words
# --------------------------------------------------------------------- #
_TEMP_HP = re.compile(r"(\d+d\d+(?:\s*\+\s*\d+)?)\s*(?:temp(?:orary)?\s*"
                      r"(?:hit points|hp))", re.I)
_HEAL = re.compile(r"heal(?:ing|s)?\s*(\d+d\d+(?:\s*\+\s*\d+)?)", re.I)
_FLY = re.compile(r"(\d+)\s*ft\s*flying speed", re.I)

_SELF_CONDITIONS = (
    ("invisible", "Invisible"),
    ("dodge", "Dodge"),
)


def _dice(expr: str) -> str:
    return expr.replace(" ", "")


def describe(feature, entity=None) -> str:
    """One line, in Finnish, saying what pressing this will do."""
    kind = classify(feature)
    if kind == PASSIVE:
        return "Passiivinen — moottori huomioi tämän automaattisesti " \
               "heitoissa. Ei tarvitse painaa."
    if kind == TOGGLE:
        flag = _TOGGLES[_mech(feature)]
        on = bool(getattr(entity, flag, False)) if entity is not None else False
        return ("Kytkin — nyt PÄÄLLÄ, klikkaus sammuttaa."
                if on else "Kytkin — klikkaus laittaa päälle.")
    bits = []
    txt = _text(feature)
    m = _TEMP_HP.search(txt)
    if m:
        bits.append(f"tilapäisiä osumapisteitä {_dice(m.group(1))}")
    m = _HEAL.search(txt)
    if m:
        bits.append(f"parantaa {_dice(m.group(1))}")
    if _FLY.search(txt):
        bits.append("antaa lentonopeuden")
    for word, cond in _SELF_CONDITIONS:
        if word in txt:
            bits.append(f"asettaa tilan {cond}")
            break
    if "additional action" in txt or "extra action" in txt:
        bits.append("antaa yhden lisätoiminnon")
    n = getattr(feature, "uses_per_day", -1)
    if n > 0:
        left = (entity.feature_uses.get(feature.name, n)
                if entity is not None else n)
        bits.append(f"käyttöjä {left}/{n}")
    return "Käytettävä — " + (", ".join(bits) if bits
                              else "kuluttaa käytön; vaikutus pöydässä")


# --------------------------------------------------------------------- #
# Named handlers
# --------------------------------------------------------------------- #
def _h_second_wind(entity, feature, battle):
    lvl = max(1, getattr(entity.stats, "character_level", 1))
    healed = entity.heal(roll_dice("1d10") + lvl)
    return True, f"Second Wind: {healed} osumapistettä takaisin."


def _h_action_surge(entity, feature, battle):
    entity.action_used = False
    return True, "Action Surge: yksi ylimääräinen toiminto tällä vuorolla."


def _h_lay_on_hands(entity, feature, battle):
    pool = getattr(entity, "lay_on_hands_left", 0)
    if pool <= 0:
        return False, "Lay on Hands: parannusvarasto on tyhjä."
    amount = min(pool, max(1, entity.max_hp - entity.hp))
    entity.lay_on_hands_left = pool - amount
    healed = entity.heal(amount)
    return True, (f"Lay on Hands: {healed} osumapistettä "
                  f"({entity.lay_on_hands_left} jäljellä varastossa). "
                  f"Kohdista toiseen hahmoon oikean paneelin HP-napeilla "
                  f"jos hoidat jotakuta muuta.")


def _h_patient_defense(entity, feature, battle):
    if getattr(entity, "ki_points_left", 0) <= 0:
        return False, "Ei ki-pisteitä jäljellä."
    entity.ki_points_left -= 1
    entity.add_condition("Dodge")
    entity.bonus_action_used = True
    return True, (f"Patient Defense: Dodge bonustoimintona "
                  f"({entity.ki_points_left} ki jäljellä).")


def _h_ki(entity, feature, battle):
    if getattr(entity, "ki_points_left", 0) <= 0:
        return False, "Ei ki-pisteitä jäljellä."
    entity.ki_points_left -= 1
    return True, (f"{feature.name}: 1 ki käytetty "
                  f"({entity.ki_points_left} jäljellä).")


def _h_bardic(entity, feature, battle):
    if getattr(entity, "bardic_inspiration_left", 0) <= 0:
        return False, "Bardic Inspiration on käytetty loppuun."
    entity.bardic_inspiration_left -= 1
    entity.bonus_action_used = True
    die = "d10" if "d10" in _text(feature) else "d6"
    return True, (f"Bardic Inspiration: liittolainen saa {die} lisättäväksi "
                  f"heittoon ({entity.bardic_inspiration_left} jäljellä).")


def _h_channel_divinity(entity, feature, battle):
    left = getattr(entity, "channel_divinity_left", 0)
    if left <= 0:
        return False, "Channel Divinity on käytetty."
    entity.channel_divinity_left = left - 1
    entity.action_used = True
    return True, (f"{feature.name}: käytetty "
                  f"({entity.channel_divinity_left} jäljellä).")


def _h_sorcery(entity, feature, battle):
    cost = 2 if "2 sorcery" in _text(feature) else 1
    left = getattr(entity, "sorcery_points_left", 0)
    if left < cost:
        return False, f"Loitsupisteitä ei riitä ({left}/{cost})."
    entity.sorcery_points_left = left - cost
    return True, (f"{feature.name}: {cost} loitsupistettä käytetty "
                  f"({entity.sorcery_points_left} jäljellä).")


def _h_uncanny_dodge(entity, feature, battle):
    if entity.reaction_used:
        return False, "Reaktio on jo käytetty tällä kierroksella."
    entity.reaction_used = True
    return True, ("Uncanny Dodge: seuraavan näkemäsi hyökkäyksen vahinko "
                  "puolittuu. Vähennä puolet HP-napeista.")


def _h_reaction(entity, feature, battle):
    if entity.reaction_used:
        return False, "Reaktio on jo käytetty tällä kierroksella."
    entity.reaction_used = True
    return True, f"{feature.name}: reaktio käytetty."


_HANDLERS = {
    "second_wind": _h_second_wind,
    "action_surge": _h_action_surge,
    "lay_on_hands": _h_lay_on_hands,
    "patient_defense": _h_patient_defense,
    "flurry_of_blows": _h_ki,
    "step_of_wind": _h_ki,
    "wholeness_of_body": _h_ki,
    "bardic_inspiration": _h_bardic,
    "channel_divinity": _h_channel_divinity,
    "quickened_spell": _h_sorcery,
    "twinned_spell": _h_sorcery,
    "font_of_magic": _h_sorcery,
    "uncanny_dodge": _h_uncanny_dodge,
    "cutting_words": _h_reaction,
    "deflect_missiles": _h_reaction,
    "indomitable": _h_reaction,
}


# --------------------------------------------------------------------- #
# Generic activation, read from the feature's own description
# --------------------------------------------------------------------- #
def _generic(entity, feature, battle):
    txt = _text(feature)
    done = []

    m = _TEMP_HP.search(txt)
    if m:
        amount = roll_dice(_dice(m.group(1)))
        entity.add_temp_hp(amount)
        done.append(f"{amount} tilapäistä osumapistettä")
    else:
        m = _HEAL.search(txt)
        if m:
            healed = entity.heal(roll_dice(_dice(m.group(1))))
            done.append(f"parani {healed}")

    m = _FLY.search(txt)
    if m and entity.start_flying():
        entity.elevation = max(entity.elevation, 5)
        done.append(f"lentää ({m.group(1)} ft)")

    for word, cond in _SELF_CONDITIONS:
        if word in txt and not entity.has_condition(cond):
            entity.add_condition(cond)
            done.append(f"tila {cond}")
            break

    if "additional action" in txt or "extra action" in txt:
        entity.action_used = False
        done.append("yksi lisätoiminto")

    if "bonus action" in txt and not entity.bonus_action_used:
        entity.bonus_action_used = True
        done.append("bonustoiminto käytetty")

    if done:
        return True, f"{feature.name}: " + ", ".join(done) + "."
    return True, (f"{feature.name}: käytetty. Vaikutus ratkaistaan "
                  f"pöydässä — {(getattr(feature, 'description', '') or '')[:70]}")


def activate(entity, feature, battle=None):
    """Use an ability. Returns (happened, message for the log)."""
    if entity is None or feature is None:
        return False, ""
    kind = classify(feature)

    if kind == PASSIVE:
        return False, (f"{feature.name} on passiivinen — moottori laskee "
                       f"sen automaattisesti, sitä ei tarvitse käyttää.")

    if kind == TOGGLE:
        flag = _TOGGLES[_mech(feature)]
        if _mech(feature) == "rage":
            if getattr(entity, "rage_active", False):
                entity.end_rage()
                return True, f"{entity.name}: Rage päättyi."
            if entity.start_rage():
                return True, (f"{entity.name}: RAGE! "
                              f"+{entity.get_rage_damage_bonus()} "
                              f"lähivahinkoa, vastustus lyönti/viilto/"
                              f"murskaus, {entity.rages_left} jäljellä.")
            return False, f"{entity.name}: raivoja ei ole jäljellä."
        on = not getattr(entity, flag, False)
        setattr(entity, flag, on)
        return True, (f"{entity.name}: {feature.name} "
                      f"{'PÄÄLLÄ' if on else 'pois'}.")

    # A use: spend the charge first, then apply the effect.
    limited = (getattr(feature, "uses_per_day", -1) > 0
               or getattr(feature, "recharge", ""))
    if limited and not entity.can_use_feature(feature.name):
        return False, f"{feature.name}: ei käyttöjä jäljellä."

    handler = _HANDLERS.get(_mech(feature))
    ok, msg = (handler(entity, feature, battle) if handler
               else _generic(entity, feature, battle))
    if ok and limited:
        entity.use_feature(feature.name)
        n = getattr(feature, "uses_per_day", 0)
        left = n - entity.feature_uses.get(feature.name, 0)
        if n > 0:
            msg += f" ({left}/{n} jäljellä)"
    return ok, msg
