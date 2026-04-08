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


def _get_spell_damage_dice(spell, entity) -> str:
    """Get the effective damage dice for a spell, scaling cantrips by caster level."""
    if spell.level == 0 and spell.damage_dice:
        return scale_cantrip_dice(spell.damage_dice, _get_effective_caster_level(entity))
    return spell.damage_dice
