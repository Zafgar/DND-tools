import random
import re

def roll_dice(dice_str: str) -> int:
    """
    Heittää noppaa D&D-muotoisen merkkijonon perusteella (esim. "2d6+3").
    Tukee muotoja:
    - XdY: Heitä X kappaletta Y-sivuista noppaa.
    - XdY+Z: Lisää Z tulokseen.
    - XdY-Z: Vähennä Z tuloksesta.
    """
    match = re.match(r"(\d+)d(\d+)([\+\-]\d+)?", dice_str)
    
    if not match:
        # Käsittelee yksinkertaiset luvut, kuten "5"
        if dice_str.isdigit():
            return int(dice_str)
        raise ValueError(f"Invalid dice string format: '{dice_str}'")

    num_dice = int(match.group(1))
    num_sides = int(match.group(2))
    modifier_str = match.group(3)

    total = 0
    for _ in range(num_dice):
        total += random.randint(1, num_sides)

    if modifier_str:
        total += int(modifier_str)

    return max(0, total) # Varmistetaan, ettei tulos ole negatiivinen
