"""Standalone utility functions used by the Tactical AI."""
from engine.dice import scale_cantrip_dice


def _get_effective_caster_level(entity) -> int:
    """Get effective caster level for cantrip scaling.
    Player heroes use character_level, monsters use CR (rounded up, min 1)."""
    if entity.stats.character_level > 0:
        return entity.stats.character_level
    # Monsters: use CR as effective level for cantrip scaling
    cr = entity.stats.challenge_rating
    return max(1, int(cr)) if cr > 0 else 1


def _get_spell_damage_dice(spell, entity, cast_level: int = 0) -> str:
    """Get the effective damage dice for a spell at a given cast level.

    - Cantrips scale by caster level (PHB p.201).
    - Leveled damage spells: if ``cast_level`` > ``spell.level``, append the
      extra scaling dice. Uses ``spell.damage_scaling`` when set, otherwise
      falls back to the spell's first dice clause (e.g. "8d6" -> "+1d6/slot").
    """
    if spell.level == 0 and spell.damage_dice:
        return scale_cantrip_dice(spell.damage_dice, _get_effective_caster_level(entity))
    base = spell.damage_dice
    if not base or cast_level <= spell.level:
        return base
    extra_slots = cast_level - spell.level
    scaling = spell.damage_scaling
    if not scaling:
        # Fallback: most SRD damage spells add 1 of the base die per slot.
        # Parse the leading "NdM" from the base dice string.
        import re
        m = re.match(r"(\d+)d(\d+)", base)
        if not m:
            return base
        die = int(m.group(2))
        scaling = f"1d{die}"
    return f"{base}+{extra_slots}{scaling[1:] if scaling.startswith('1') else scaling}"


def _best_cast_level_for_damage(spell, entity) -> int:
    """Pick the highest available spell slot up to level 9 that is at least
    ``spell.level``. Used for upcasting damage spells.
    Returns 0 if no slot is available.
    """
    if spell.level == 0:
        return 0
    # Prefer the highest slot available to maximise scaling, but don't
    # burn 9th-level slots on 1st-level spells. Cap at base level + 2
    # unless the entity is swimming in slots.
    highest = entity.get_highest_slot()
    if highest < spell.level:
        return 0
    cap = min(9, spell.level + 2)
    best = 0
    for lvl in range(spell.level, cap + 1):
        if entity.has_spell_slot(lvl):
            # prefer the lowest slot that can cast it; upcasting is only
            # selected if the extra dice are worth more than slot economy.
            if best == 0:
                best = lvl
    return best or spell.level
