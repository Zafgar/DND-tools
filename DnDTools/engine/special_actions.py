"""Legendary and lair actions declared as Features.

A monster can declare a legendary or lair action two ways:

  * as an ``Action`` with ``action_type="legendary"`` / ``"lair"``, or
  * as a ``Feature`` with ``feature_type="legendary"`` / ``"lair"``.

The second form is the natural one to write — it is where the cost, the
recharge, the save DC and the prose all live — and it is what the whole
Novus Somnium roster uses. But both consumers (the AI's legendary
planner and the lair-owner scan in ``BattleSystem.start_combat``) only
ever looked for an ``Action``, so a Feature-declared ability was
silently skipped. Twenty-three legendary creatures — the Ancient Red
Dragon, the Beholder, the Pit Fiend, and every campaign boss — never
used a single legendary action, and five bosses' lair actions never
fired at all.

This module resolves a Feature into something executable:

  1. an ``Action`` of the same name if the stat block has one,
  2. otherwise an ``Action`` synthesised from the Feature's own fields
     when it carries damage or a save,
  3. otherwise an intent inferred from the name and description —
     a move, a weapon attack, a spell — so "Legendaarinen: Isku" swings
     the creature's best weapon and "Legendaarinen: Liike" repositions.

Nothing here rolls dice or mutates state; it only describes what the
ability *is* so the callers can score and execute it.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from data.models import Action


# Keyword → intent. Both languages, because the stat blocks are written
# in Finnish and the imported SRD monsters in English.
_MOVE_WORDS = (
    "liike", "liiku", "askel", "harppaus", "siirry", "marssi",
    "move", "step", "slip", "stride", "reposition", "teleport",
    "shift", "march", "prowl",
)
_ATTACK_WORDS = (
    "isku", "iskee", "purenta", "puree", "hyökkä", "kirveenheitto",
    "piiska", "luupiiska", "sivallus", "lyö",
    "attack", "strike", "bite", "claw", "slam", "stomp", "tail",
    "swipe", "blow", "volley", "shot",
)
_SPELL_WORDS = (
    "loitsu", "loitsii", "cantrip", "spell", "cast", "magic",
    "lance", "burst", "bolt", "ray",
)


@dataclass
class SpecialAction:
    """One resolved legendary / lair ability."""
    feature: object            # the source Feature
    action: Optional[Action]   # something executable, or None for "move"
    intent: str                # "attack" | "effect" | "move" | "spell"
    cost: int = 1

    @property
    def name(self) -> str:
        return getattr(self.feature, "name", "") or ""


def _blob(feature) -> str:
    return (f"{getattr(feature, 'name', '')} "
            f"{getattr(feature, 'description', '')}").lower()


def _intent_from_text(feature) -> str:
    text = _blob(feature)
    # Order matters: a "Legendary Cantrip" is a spell even though the
    # description mentions damage, and "Shadow Slip" is a move even
    # though it mentions an attack afterwards.
    for word in _SPELL_WORDS:
        if word in text:
            return "spell"
    for word in _MOVE_WORDS:
        if word in text:
            return "move"
    for word in _ATTACK_WORDS:
        if word in text:
            return "attack"
    return "effect"


def _best_weapon(stats) -> Optional[Action]:
    """The creature's hardest-hitting single attack, for "make one
    attack" style legendary actions."""
    from engine.dice import average_damage
    best, best_dmg = None, -1.0
    for a in stats.actions or ():
        if a.is_multiattack or not a.damage_dice:
            continue
        if a.action_type not in ("action", ""):
            continue
        try:
            dmg = average_damage(a.damage_dice) + a.damage_bonus
        except Exception:
            dmg = 0.0
        if dmg > best_dmg:
            best, best_dmg = a, dmg
    return best


def _action_from_feature(feature, stats) -> Optional[Action]:
    """Synthesise an Action from a Feature that carries its own rules."""
    dice = getattr(feature, "damage_dice", "") or ""
    dc = getattr(feature, "save_dc", 0) or 0
    if not dice and not dc:
        return None
    radius = getattr(feature, "aura_radius", 0) or 0
    return Action(
        name=getattr(feature, "name", "Legendary Action"),
        description=getattr(feature, "description", ""),
        attack_bonus=0,
        damage_dice=dice or "1d1",
        damage_bonus=0,
        damage_type=getattr(feature, "damage_type", "") or "force",
        # An aura_radius means "every creature within X feet of ME". It
        # is centred on the caster by definition, and range 0 is how the
        # AI's AoE planner is told that. Giving it range 30 instead let
        # a dragon aim its Wing Attack like a fireball at a knot of
        # enemies thirty feet away, buffeting people its wings could
        # not possibly touch.
        range=0 if radius else 60,
        action_type="legendary",
        aoe_radius=radius,
        aoe_shape="sphere" if radius else "",
        applies_condition=getattr(feature, "applies_condition", "") or "",
        condition_save=getattr(feature, "save_ability", "") or "",
        condition_dc=dc,
    )


def _clone_as(action: Action, name: str, description: str) -> Action:
    """Copy a weapon attack under the legendary ability's name."""
    import copy as _copy
    clone = _copy.copy(action)
    clone.name = name
    clone.description = description or action.description
    clone.action_type = "legendary"
    clone.is_multiattack = False
    clone.multiattack_count = 1
    clone.multiattack_targets = []
    return clone


def _loose_match(name: str, by_name: dict) -> Optional[Action]:
    """Find the real attack a legendary ability is a wrapper around.

    Stat blocks name the legendary entry "Tail Attack" and the weapon
    itself just "Tail". An exact-name lookup misses that, so the ability
    was synthesised from the Feature's bare damage dice instead and lost
    the weapon's reach — the dragon ended up tail-slapping people sixty
    feet away.
    """
    key = (name or "").strip().lower()
    for suffix in (" attack", " strike", "-isku", " isku"):
        if key.endswith(suffix):
            key = key[: -len(suffix)].strip()
            break
    if not key:
        return None
    for candidate, action in by_name.items():
        if (candidate or "").strip().lower() == key:
            return action
    return None


def resolve_special_actions(stats, kind: str) -> List[SpecialAction]:
    """Every usable legendary (or lair) ability on this stat block.

    ``kind`` is ``"legendary"`` or ``"lair"``. Actions declared the old
    way still win; Features fill in everything the stat block never
    spelled out as an Action.
    """
    out: List[SpecialAction] = []
    seen = set()

    by_name = {}
    for a in stats.actions or ():
        by_name.setdefault(a.name, a)

    # 1. Real Actions of the right type — the original path.
    for a in stats.actions or ():
        if a.action_type != kind:
            continue
        feat = next((f for f in (stats.features or ())
                     if f.name == a.name), None)
        cost = getattr(feat, "legendary_cost", 1) if feat else 1
        out.append(SpecialAction(feature=feat or a, action=a,
                                 intent="attack" if a.damage_dice else "effect",
                                 cost=max(1, cost)))
        seen.add(a.name)

    # 2. Features of the right type that no Action covers.
    for feat in (stats.features or ()):
        if getattr(feat, "feature_type", "") != kind:
            continue
        if feat.name in seen:
            continue
        seen.add(feat.name)
        cost = max(1, getattr(feat, "legendary_cost", 1) or 1)

        # A same-named Action of any type (an "Eye Ray" listed as a
        # normal action, say) is the best executable match.
        twin = by_name.get(feat.name) or _loose_match(feat.name, by_name)
        if twin is not None and twin.damage_dice:
            out.append(SpecialAction(
                feature=feat, action=_clone_as(twin, feat.name,
                                               feat.description),
                intent="attack", cost=cost))
            continue

        built = _action_from_feature(feat, stats)
        if built is not None:
            out.append(SpecialAction(feature=feat, action=built,
                                     intent="attack", cost=cost))
            continue

        intent = _intent_from_text(feat)
        if intent == "attack":
            weapon = _best_weapon(stats)
            if weapon is not None:
                out.append(SpecialAction(
                    feature=feat,
                    action=_clone_as(weapon, feat.name, feat.description),
                    intent="attack", cost=cost))
                continue
            intent = "effect"
        out.append(SpecialAction(feature=feat, action=None, intent=intent,
                                 cost=cost))
    return out


def has_lair_actions(stats) -> bool:
    """True when this stat block declares lair actions either way."""
    if any(a.action_type == "lair" for a in (stats.actions or ())):
        return True
    return any(getattr(f, "feature_type", "") == "lair"
               for f in (stats.features or ()))
