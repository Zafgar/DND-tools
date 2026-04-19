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


def _combine_dice(base: str, extra: str) -> str:
    """Concatenate two dice expressions with '+'. Handles empty strings gracefully."""
    base = (base or "").strip()
    extra = (extra or "").strip()
    if not base:
        return extra
    if not extra:
        return base
    return f"{base}+{extra}"


def _scale_dice_by_count(dice: str, count: int) -> str:
    """Multiply the die count of each 'NdM' term in dice by `count`.
    E.g. '1d6+2' with count=3 -> '3d6+2'. Flat bonuses are preserved once."""
    if not dice or count <= 0:
        return dice
    if count == 1:
        return dice
    parts = [p.strip() for p in dice.replace("-", "+-").split("+") if p.strip()]
    scaled = []
    for p in parts:
        if "d" in p:
            n, m = p.split("d", 1)
            try:
                n_i = int(n) if n else 1
            except ValueError:
                scaled.append(p)
                continue
            scaled.append(f"{n_i * count}d{m}")
        else:
            scaled.append(p)
    return "+".join(scaled).replace("+-", "-")


def _get_spell_damage_dice(spell, entity, slot_used: int = 0) -> str:
    """Effective damage dice for a spell.

    - Cantrips scale by caster level (PHB p.201).
    - Leveled spells with damage_scaling scale by (slot_used - spell.level).
      If slot_used is 0 (unknown), the base spell level is assumed (no upcast bonus).
    """
    base = spell.damage_dice
    if spell.level == 0 and base:
        return scale_cantrip_dice(base, _get_effective_caster_level(entity))
    if base and spell.damage_scaling and slot_used and slot_used > spell.level:
        extra_slots = slot_used - spell.level
        scaling_dice = _scale_dice_by_count(spell.damage_scaling, extra_slots)
        return _combine_dice(base, scaling_dice)
    return base


def _get_spell_heals_dice(spell, slot_used: int = 0) -> str:
    """Effective healing dice for a spell, applying upcast scaling.
    Healing spells store extra healing-per-slot in `damage_scaling` field (reused)."""
    base = spell.heals
    if base and spell.damage_scaling and slot_used and slot_used > spell.level:
        extra_slots = slot_used - spell.level
        scaling_dice = _scale_dice_by_count(spell.damage_scaling, extra_slots)
        return _combine_dice(base, scaling_dice)
    return base
