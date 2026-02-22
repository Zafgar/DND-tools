from dataclasses import dataclass, field
from typing import List, Optional, Dict

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
class SpellInfo:
    name: str
    level: int = 0                    # 0 = cantrip
    school: str = "Evocation"
    action_type: str = "action"       # action, bonus, reaction
    range: int = 60
    aoe_radius: int = 0               # ft radius (0 = single target)
    aoe_shape: str = ""               # sphere, cone, line, cube
    damage_dice: str = ""             # e.g. "8d6"
    damage_type: str = "fire"
    damage_scaling: str = ""          # extra dice per slot above base, e.g. "1d6"
    save_ability: str = ""            # "Dexterity" etc
    save_dc_fixed: int = 0            # 0 = compute from caster
    attack_bonus_fixed: int = 0       # 0 = compute from caster
    applies_condition: str = ""       # condition on hit/fail
    condition_on_save: bool = False   # if True, condition applies even on save
    heals: str = ""                   # healing dice e.g. "2d4+2"
    targets: str = "single"          # single, aoe, self, all_allies
    concentration: bool = False
    duration: str = ""                # "1 minute", "1 hour"
    description: str = ""
    half_on_save: bool = True         # AoE spells usually deal half on save

@dataclass
class Action:
    name: str
    description: str = ""
    attack_bonus: int = 0
    damage_dice: str = "1d4"
    damage_bonus: int = 0
    damage_type: str = "bludgeoning"
    range: int = 5
    action_type: str = "action"       # action, bonus, reaction, legendary, free
    is_multiattack: bool = False
    multiattack_count: int = 1
    multiattack_targets: List[str] = field(default_factory=list)  # names of sub-actions
    reach: int = 5                    # melee reach in ft
    applies_condition: str = ""
    condition_save: str = ""          # "STR", "DEX" etc for condition save
    condition_dc: int = 0

@dataclass
class Feature:
    name: str
    description: str = ""
    feature_type: str = "passive"     # passive, legendary, lair, reaction, trait
    uses_per_day: int = -1            # -1 = unlimited/passive
    legendary_cost: int = 1           # cost in legendary actions
    recharge: str = ""                # "5-6", "short rest", "long rest"

@dataclass
class Item:
    name: str
    item_type: str = "potion"         # potion, scroll, wand, weapon, misc
    uses: int = 1
    description: str = ""
    heals: str = ""
    damage_dice: str = ""
    applies_condition: str = ""
    buff: str = ""                    # e.g. "resistance:fire"

@dataclass
class CreatureStats:
    name: str
    size: str = "Medium"
    creature_type: str = "Humanoid"
    alignment: str = "Neutral"
    armor_class: int = 10
    armor_type: str = ""
    hit_points: int = 10
    hit_dice: str = ""                # e.g. "5d8+10"
    speed: int = 30
    fly_speed: int = 0
    swim_speed: int = 0
    climb_speed: int = 0
    burrow_speed: int = 0
    abilities: AbilityScores = field(default_factory=AbilityScores)
    saving_throws: Dict[str, int] = field(default_factory=dict)
    skills: Dict[str, int] = field(default_factory=dict)
    damage_immunities: List[str] = field(default_factory=list)
    damage_resistances: List[str] = field(default_factory=list)
    damage_vulnerabilities: List[str] = field(default_factory=list)
    condition_immunities: List[str] = field(default_factory=list)
    senses: str = ""
    languages: str = ""
    challenge_rating: float = 0.0
    xp: int = 0
    proficiency_bonus: int = 2
    # Actions
    actions: List[Action] = field(default_factory=list)
    bonus_actions: List[Action] = field(default_factory=list)
    reactions: List[Action] = field(default_factory=list)
    # Spellcasting
    spellcasting_ability: str = ""    # "Intelligence", "Wisdom", "Charisma"
    spell_save_dc: int = 0
    spell_attack_bonus: int = 0
    spell_slots: Dict[str, int] = field(default_factory=dict)
    spells_known: List[SpellInfo] = field(default_factory=list)
    cantrips: List[SpellInfo] = field(default_factory=list)
    # Traits and special abilities
    features: List[Feature] = field(default_factory=list)
    legendary_action_count: int = 0
    legendary_resistance_count: int = 0
    # Items
    items: List[Item] = field(default_factory=list)
