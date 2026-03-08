import random
import re

def roll_dice(dice_str: str) -> int:
    """Roll dice from a D&D notation string like '2d6+3', '1d8-1', '10'."""
    if not dice_str:
        return 0
    dice_str = str(dice_str).strip()
    match = re.match(r"(\d+)d(\d+)([\+\-]\d+)?", dice_str)
    if not match:
        try:
            return int(dice_str)
        except ValueError:
            return 0
    num_dice = int(match.group(1))
    num_sides = int(match.group(2))
    modifier_str = match.group(3)
    total = sum(random.randint(1, num_sides) for _ in range(num_dice))
    if modifier_str:
        total += int(modifier_str)
    return max(0, total)

def roll_dice_critical(dice_str: str) -> int:
    """Critical hit: double the dice (add extra dice, not doubled total)."""
    if not dice_str:
        return 0
    match = re.match(r"(\d+)d(\d+)([\+\-]\d+)?", str(dice_str))
    if not match:
        try:
            return int(dice_str)
        except ValueError:
            return 0
    num_dice = int(match.group(1))
    num_sides = int(match.group(2))
    modifier_str = match.group(3)
    # Double dice for critical hit
    total = sum(random.randint(1, num_sides) for _ in range(num_dice * 2))
    if modifier_str:
        total += int(modifier_str)
    return max(0, total)

def roll_d20(advantage: bool = False, disadvantage: bool = False):
    """Roll 1d20, returning (result, roll_description)."""
    r1 = random.randint(1, 20)
    if advantage and not disadvantage:
        r2 = random.randint(1, 20)
        return max(r1, r2), f"({r1},{r2}) Adv"
    elif disadvantage and not advantage:
        r2 = random.randint(1, 20)
        return min(r1, r2), f"({r1},{r2}) Dis"
    return r1, str(r1)

def roll_attack(attack_bonus: int, advantage: bool = False, disadvantage: bool = False):
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
    """Calculate average damage for AI evaluation."""
    if not dice_str:
        return 0.0
    match = re.match(r"(\d+)d(\d+)([\+\-]\d+)?", str(dice_str))
    if not match:
        try:
            return float(dice_str)
        except ValueError:
            return 0.0
    num_dice = int(match.group(1))
    num_sides = int(match.group(2))
    modifier = int(match.group(3)) if match.group(3) else 0
    return num_dice * (num_sides + 1) / 2 + modifier
