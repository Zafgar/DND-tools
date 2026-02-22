from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class AbilityScores:
    strength: int = 10
    dexterity: int = 10
    constitution: int = 10
    intelligence: int = 10
    wisdom: int = 10
    charisma: int = 10

    def get_mod(self, score_name: str) -> int:
        score = getattr(self, score_name.lower())
        return (score - 10) // 2

@dataclass
class Action:
    name: str
    description: str
    attack_bonus: int = 0
    damage_dice: str = "1d4"
    damage_bonus: int = 0
    range: int = 5
    action_type: str = "action" # action, bonus, reaction, legendary

@dataclass
class CreatureStats:
    """
    Tämä luokka sisältää kaiken datan, jota D&D 5e olento tarvitsee.
    Tämä vastaa JSON-tiedoston rakennetta tulevaisuudessa.
    """
    name: str
    size: str = "Medium"
    type: str = "Humanoid"
    alignment: str = "Neutral"
    armor_class: int = 10
    hit_points: int = 10
    speed: int = 30
    abilities: AbilityScores = field(default_factory=AbilityScores)
    actions: List[Action] = field(default_factory=list)
    challenge_rating: float = 0.0
    xp: int = 0
    condition_immunities: List[str] = field(default_factory=list)
    spell_slots: dict = field(default_factory=dict) # Esim. {"1st": 4, "2nd": 2}
    skills: dict = field(default_factory=dict) # Esim. {"Athletics": 5, "Stealth": 6}
    saving_throws: dict = field(default_factory=dict) # Esim. {"Dexterity": 4}