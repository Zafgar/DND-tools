import random
import re


def _parse_dice(dice_str: str):
    """Parse a full D&D notation string into ([(sign, count, sides), …],
    flat_modifier). Supports multiple dice terms and flats, e.g.
    '2d8+4d6+3', '1d10', '1d6-1', '10'. Unknown text yields ([], 0)."""
    if not dice_str:
        return [], 0
    s = str(dice_str).strip().replace(" ", "").lower()
    if not s:
        return [], 0
    dice_terms = []
    flat = 0
    # Split into signed tokens: 2d8, +4d6, -1, +3 …
    for tok in re.findall(r"[+-]?[^+-]+", s):
        sign = -1 if tok[0] == "-" else 1
        body = tok.lstrip("+-")
        if not body:
            continue
        if "d" in body:
            n_str, _, sides_str = body.partition("d")
            try:
                n = int(n_str) if n_str else 1
                sides = int(sides_str)
            except ValueError:
                continue
            dice_terms.append((sign, n, sides))
        else:
            try:
                flat += sign * int(body)
            except ValueError:
                continue
    return dice_terms, flat


def roll_dice(dice_str: str) -> int:
    """Roll dice from a D&D notation string like '2d6+3', '2d8+4d6', '10'."""
    terms, flat = _parse_dice(dice_str)
    if not terms and flat == 0:
        return 0
    total = flat
    for sign, n, sides in terms:
        total += sign * sum(random.randint(1, sides) for _ in range(n))
    return max(0, total)


def roll_dice_critical(dice_str: str) -> int:
    """Critical hit: double the dice count of every dice term (flat
    modifiers are added once, not doubled). Handles multi-term strings."""
    terms, flat = _parse_dice(dice_str)
    if not terms and flat == 0:
        return 0
    total = flat
    for sign, n, sides in terms:
        total += sign * sum(random.randint(1, sides) for _ in range(n * 2))
    return max(0, total)

def roll_d20(advantage: bool = False, disadvantage: bool = False) -> tuple[int, str]:
    """Roll 1d20, returning (result, roll_description)."""
    r1 = random.randint(1, 20)
    if advantage and not disadvantage:
        r2 = random.randint(1, 20)
        return max(r1, r2), f"({r1},{r2}) Adv"
    elif disadvantage and not advantage:
        r2 = random.randint(1, 20)
        return min(r1, r2), f"({r1},{r2}) Dis"
    return r1, str(r1)

def roll_attack(attack_bonus: int, advantage: bool = False, disadvantage: bool = False) -> tuple[int, int, bool, bool, str]:
    """Roll attack, returns (total, nat_roll, is_crit, is_fumble, roll_str)."""
    nat, roll_str = roll_d20(advantage, disadvantage)
    return nat + attack_bonus, nat, nat == 20, nat == 1, roll_str

def scale_cantrip_dice(damage_dice: str, caster_level: int) -> str:
    """Scale cantrip damage dice based on caster level (PHB p.201).
    Level 1-4: 1 die, 5-10: 2 dice, 11-16: 3 dice, 17+: 4 dice.
    For monsters, pass CR as caster_level."""
    if not damage_dice or caster_level <= 0:
        return damage_dice
    match = re.match(r"(\d+)d(\d+)([\+\-]\d+)?", str(damage_dice))
    if not match:
        return damage_dice
    base_dice = int(match.group(1))
    sides = int(match.group(2))
    modifier = match.group(3) or ""
    if caster_level >= 17:
        multiplier = 4
    elif caster_level >= 11:
        multiplier = 3
    elif caster_level >= 5:
        multiplier = 2
    else:
        multiplier = 1
    # Only scale if base is 1 die (standard cantrip pattern)
    # Cantrips like Eldritch Blast with multiple beams are handled separately
    if base_dice == 1:
        return f"{multiplier}d{sides}{modifier}"
    return damage_dice


def average_damage(dice_str: str) -> float:
    """Average of a full dice expression (handles multi-term strings) for
    AI evaluation, e.g. '2d8+4d6' → 9 + 14 = 23."""
    terms, flat = _parse_dice(dice_str)
    if not terms and flat == 0:
        # Allow bare floats/ints the parser skipped (e.g. "7.5").
        try:
            return float(dice_str)
        except (ValueError, TypeError):
            return 0.0
    avg = float(flat)
    for sign, n, sides in terms:
        avg += sign * n * (sides + 1) / 2.0
    return avg
