"""Phase 34 — reaction advisor.

Given a trigger (incoming attack, enemy spell cast, damage dealt) and
the list of potential reactors, returns the full slate of reactions
each could fire and a recommendation for each.

The campaign manager / battle UI can render this as a checkbox panel
("Cleric could cast Shield (recommend: USE — would convert hit to
miss)") so the DM sees what's available *before* clicking through.

Pure logic, no pygame. Doesn't mutate entities — the caller decides
which reactions to actually fire.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ReactionOption:
    reactor_name: str
    reactor_id: str                  # Entity name (uniqueish in a battle)
    reaction_name: str               # "Counterspell", "Shield", …
    recommendation: bool             # AI's verdict
    reason: str                      # Human-readable
    resource_cost: str = ""          # "1st-level slot", "reaction", "1 ki"
    affects: str = ""                # "attack vs PC1", "spell from boss"


@dataclass
class ReactionPrompt:
    """Wraps the full list of viable reactions for one trigger."""
    trigger_kind: str                # "incoming_attack" | "enemy_cast" | …
    trigger_summary: str
    options: List[ReactionOption] = field(default_factory=list)

    def recommended(self) -> List[ReactionOption]:
        return [o for o in self.options if o.recommendation]


# --------------------------------------------------------------------- #
# Per-reaction analysers
# --------------------------------------------------------------------- #

def _spell_known(entity, name: str) -> bool:
    """True if the entity has a SpellInfo with this name in spells_known."""
    return any(getattr(s, "name", "") == name
                for s in getattr(entity.stats, "spells_known", []) or [])


def _has_reaction_available(entity) -> bool:
    if getattr(entity, "reaction_used", False):
        return False
    if entity.hp <= 0:
        return False
    if entity.is_incapacitated():
        return False
    return True


def _counterspell_option(reactor, caster, spell, spell_level,
                           battle) -> Optional[ReactionOption]:
    """Bind the existing :func:`TacticalAI.should_counterspell` to a
    structured option object."""
    if not _spell_known(reactor, "Counterspell"):
        return None
    if not reactor.has_spell_slot(3):
        return None
    if not _has_reaction_available(reactor):
        return None
    # Use the existing tactical logic but unwrap the boolean into a
    # reasoned string.
    ai = battle.ai if hasattr(battle, "ai") else None
    use = False
    reason = ""
    if ai is not None:
        try:
            use = ai.should_counterspell(reactor, caster, spell,
                                            spell_level, battle)
        except Exception:
            use = False
    if use:
        reason = (f"Counter {spell.name if spell else 'spell'} "
                   f"(lvl {spell_level}) — high impact")
    else:
        if spell_level <= 2:
            reason = f"Low-level spell (lvl {spell_level}); save slot"
        else:
            reason = f"Not worth countering — save reaction"
    return ReactionOption(
        reactor_name=reactor.name, reactor_id=reactor.name,
        reaction_name="Counterspell",
        recommendation=use, reason=reason,
        resource_cost="3rd+ level slot + reaction",
        affects=f"spell from {caster.name}",
    )


def _shield_option(reactor, attacker, attack_total, ac_now,
                     battle) -> Optional[ReactionOption]:
    """Shield (PHB p.275): +5 AC vs the triggering attack and all
    Magic Missiles until your next turn.  Costs a 1st-level slot."""
    if not _spell_known(reactor, "Shield"):
        return None
    if not reactor.has_spell_slot(1):
        return None
    if not _has_reaction_available(reactor):
        return None
    # The hit MUST currently be a hit but a hit that +5 AC would
    # convert into a miss.
    if attack_total < ac_now:
        return ReactionOption(
            reactor_name=reactor.name, reactor_id=reactor.name,
            reaction_name="Shield",
            recommendation=False,
            reason="Attack already missed — no need for Shield",
            resource_cost="1st-level slot + reaction",
            affects=f"attack from {attacker.name}",
        )
    if attack_total < ac_now + 5:
        return ReactionOption(
            reactor_name=reactor.name, reactor_id=reactor.name,
            reaction_name="Shield",
            recommendation=True,
            reason=f"Hit by {attack_total} vs AC {ac_now}; "
                    f"+5 AC turns it into a miss",
            resource_cost="1st-level slot + reaction",
            affects=f"attack from {attacker.name}",
        )
    # Attack hits even with +5 — only worth it for Magic Missile
    # absorption or if hp is critical
    if reactor.hp <= reactor.max_hp * 0.2:
        return ReactionOption(
            reactor_name=reactor.name, reactor_id=reactor.name,
            reaction_name="Shield",
            recommendation=True,
            reason=f"Critical HP; Shield blocks Magic Missile + "
                    f"future hits this round",
            resource_cost="1st-level slot + reaction",
            affects=f"attack from {attacker.name}",
        )
    return ReactionOption(
        reactor_name=reactor.name, reactor_id=reactor.name,
        reaction_name="Shield",
        recommendation=False,
        reason=f"+5 AC wouldn't block the hit ({attack_total} "
                f"≥ AC {ac_now} + 5); save slot",
        resource_cost="1st-level slot + reaction",
        affects=f"attack from {attacker.name}",
    )


def _absorb_elements_option(reactor, attacker, damage, damage_type,
                              battle) -> Optional[ReactionOption]:
    """Absorb Elements (XGtE p.150): when taking acid/cold/fire/
    lightning/thunder damage, +1d6 + slot bonus resistance to that
    type until next turn, and your next melee hit deals +1d6 of the
    same type. 1st-level slot + reaction."""
    elemental = {"acid", "cold", "fire", "lightning", "thunder"}
    if damage_type.lower() not in elemental:
        return None
    if not _spell_known(reactor, "Absorb Elements"):
        return None
    if not reactor.has_spell_slot(1):
        return None
    if not _has_reaction_available(reactor):
        return None
    # Recommend if damage is substantial (>= 12) or HP is fragile.
    fragile = reactor.hp <= reactor.max_hp * 0.4
    big_hit = damage >= 12
    use = fragile or big_hit
    if use:
        reason = (f"Halves {damage} {damage_type} damage and adds "
                   f"+1d6 {damage_type} to next hit")
    else:
        reason = f"Damage ({damage}) is light; save slot"
    return ReactionOption(
        reactor_name=reactor.name, reactor_id=reactor.name,
        reaction_name="Absorb Elements",
        recommendation=use, reason=reason,
        resource_cost="1st-level slot + reaction",
        affects=f"{damage_type} damage from {attacker.name}",
    )


def _hellish_rebuke_option(reactor, attacker, damage,
                              battle) -> Optional[ReactionOption]:
    """Hellish Rebuke (PHB p.250): tiefling / warlock reaction when
    you take damage from a creature you can see. 2d10 fire damage
    (DEX save half). Costs 1st-level slot OR 1/day racial trait."""
    if not _spell_known(reactor, "Hellish Rebuke"):
        return None
    if not _has_reaction_available(reactor):
        return None
    # Have a 1st-level slot or innate use.
    has_slot = reactor.has_spell_slot(1)
    innate_left = reactor.innate_spell_uses.get("Hellish Rebuke", 0)
    if not has_slot and innate_left <= 0:
        return None
    # Recommend whenever the rebuker took meaningful damage (≥ 5).
    use = damage >= 5
    if use:
        reason = (f"Took {damage} damage; rebuke for ~7 (2d10 fire, "
                   f"DEX half)")
    else:
        reason = f"Only {damage} damage; save reaction"
    return ReactionOption(
        reactor_name=reactor.name, reactor_id=reactor.name,
        reaction_name="Hellish Rebuke",
        recommendation=use, reason=reason,
        resource_cost=("1st-level slot or 1/day racial"
                         if not has_slot else "1st-level slot"),
        affects=f"damage from {attacker.name}",
    )


def _cutting_words_option(reactor, attacker, target, attack_total,
                             ac_now, battle) -> Optional[ReactionOption]:
    """Cutting Words (Bard College of Lore, PHB p.55): when a
    creature you can see within 60 ft makes an attack roll / ability
    check / damage roll, expend Bardic Inspiration to subtract.
    Recommend when subtracting the largest die size would convert a
    hit into a miss."""
    if not reactor.has_feature("cutting_words"):
        return None
    if not _has_reaction_available(reactor):
        return None
    if getattr(reactor, "bardic_inspiration_left", 0) <= 0:
        return None
    # Bardic Inspiration die at college-of-lore levels: d6 (3rd),
    # d8 (5th), d10 (10th), d12 (15th). Approximate by character_level.
    lvl = max(1, getattr(reactor.stats, "character_level", 1))
    avg_subtract = (
        6 if lvl < 5 else 8 if lvl < 10 else 10 if lvl < 15 else 12
    ) / 2.0 + 0.5
    # Recommend if the attack would currently HIT and subtracting the
    # average would convert it to a MISS.
    if attack_total >= ac_now \
            and attack_total - avg_subtract < ac_now:
        reason = (f"Attack ({attack_total} vs AC {ac_now}) likely to "
                   f"miss after ~{int(avg_subtract)} subtract")
        use = True
    else:
        reason = (f"Subtract wouldn't change outcome "
                   f"({attack_total} vs AC {ac_now})")
        use = False
    return ReactionOption(
        reactor_name=reactor.name, reactor_id=reactor.name,
        reaction_name="Cutting Words",
        recommendation=use, reason=reason,
        resource_cost="1 Bardic Inspiration + reaction",
        affects=f"attack from {attacker.name} vs {target.name}",
    )


# --------------------------------------------------------------------- #
# Top-level analyses — gather options for one event
# --------------------------------------------------------------------- #

def analyse_incoming_attack(target, attacker, attack_total: int,
                              ac_now: int, battle,
                              potential_reactors=None
                              ) -> ReactionPrompt:
    """Build the full reaction slate for an incoming attack."""
    prompt = ReactionPrompt(
        trigger_kind="incoming_attack",
        trigger_summary=(f"{attacker.name} → {target.name} "
                          f"(roll {attack_total} vs AC {ac_now})"),
    )
    reactors = potential_reactors
    if reactors is None:
        # The target themselves, plus their allies within 60 ft
        reactors = [target]
        if battle:
            for ally in battle.get_allies_of(target):
                if battle.get_distance(target, ally) * 5 <= 60:
                    reactors.append(ally)
    for r in reactors:
        # Target's own Shield reaction
        if r is target:
            opt = _shield_option(r, attacker, attack_total, ac_now,
                                    battle)
            if opt:
                prompt.options.append(opt)
        # Bard ally's Cutting Words
        if r is not target:
            opt = _cutting_words_option(r, attacker, target,
                                           attack_total, ac_now, battle)
            if opt:
                prompt.options.append(opt)
    return prompt


def analyse_enemy_spell(caster, spell, spell_level: int, battle,
                          potential_reactors=None) -> ReactionPrompt:
    """Build the full reaction slate when an enemy starts casting."""
    spell_name = spell.name if spell else "(unknown spell)"
    prompt = ReactionPrompt(
        trigger_kind="enemy_cast",
        trigger_summary=f"{caster.name} casts {spell_name} (lvl "
                         f"{spell_level})",
    )
    if potential_reactors is None and battle:
        potential_reactors = [
            r for r in battle.get_enemies_of(caster)
            if battle.get_distance(r, caster) * 5 <= 60
        ]
    for r in (potential_reactors or []):
        opt = _counterspell_option(r, caster, spell, spell_level,
                                       battle)
        if opt:
            prompt.options.append(opt)
    return prompt


def analyse_incoming_damage(target, attacker, damage: int,
                               damage_type: str, battle
                               ) -> ReactionPrompt:
    """Build the reaction slate when ``target`` is about to take
    ``damage`` of the given type."""
    prompt = ReactionPrompt(
        trigger_kind="incoming_damage",
        trigger_summary=(f"{target.name} takes {damage} {damage_type}"
                          f" from {attacker.name}"),
    )
    opt = _absorb_elements_option(target, attacker, damage,
                                     damage_type, battle)
    if opt:
        prompt.options.append(opt)
    opt = _hellish_rebuke_option(target, attacker, damage, battle)
    if opt:
        prompt.options.append(opt)
    return prompt
