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
    # Summon support
    summon_name: str = ""             # If set, spawns a token (e.g. "Spiritual Weapon")
    summon_hp: int = 0                # HP of summoned creature (0 = object/no HP)
    summon_ac: int = 10
    summon_damage_dice: str = ""      # Damage the summon deals
    summon_damage_type: str = ""
    summon_attack_bonus: int = 0
    summon_duration_rounds: int = 10  # How long summon lasts
    # Bonus damage on weapon hits (e.g. Hunter's Mark 1d6)
    bonus_damage_dice: str = ""
    bonus_damage_type: str = ""

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
    aoe_radius: int = 0
    aoe_shape: str = ""               # "cone", "sphere", "line", "cube"

@dataclass
class Feature:
    name: str
    description: str = ""
    feature_type: str = "passive"     # passive, legendary, lair, reaction, trait, class, racial
    uses_per_day: int = -1            # -1 = unlimited/passive
    legendary_cost: int = 1           # cost in legendary actions
    recharge: str = ""                # "5-6", "short rest", "long rest"
    # Aura / Turn Start Trigger fields
    aura_radius: int = 0
    save_dc: int = 0
    save_ability: str = ""            # "Constitution", "Wisdom", etc.
    applies_condition: str = ""
    damage_dice: str = ""
    damage_type: str = ""
    # Class mechanic fields
    mechanic: str = ""                # Key for AI behavior: "rage", "sneak_attack",
                                      # "divine_smite", "hunters_mark", "colossus_slayer",
                                      # "second_wind", "action_surge", "lay_on_hands",
                                      # "cunning_action", "uncanny_dodge", "evasion",
                                      # "wild_shape", "ki", "bardic_inspiration",
                                      # "metamagic", "eldritch_invocation",
                                      # "channel_divinity", "rage_damage", "reckless_attack",
                                      # "danger_sense", "feral_instinct", "brutal_critical",
                                      # "flurry_of_blows", "patient_defense", "step_of_wind",
                                      # "stunning_strike", "deflect_missiles",
                                      # "favored_enemy", "natural_explorer",
                                      # "fighting_style", "extra_attack"
    mechanic_value: str = ""          # Extra data: dice "5d6", HP pool "50", etc.
    short_rest_recharge: bool = False # Recharges on short rest

@dataclass
class RacialTrait:
    name: str
    description: str = ""
    mechanic: str = ""                # "darkvision", "fey_ancestry", "lucky",
                                      # "relentless_endurance", "savage_attacks",
                                      # "breath_weapon", "stonecunning",
                                      # "halfling_nimbleness", "brave",
                                      # "trance", "mask_of_wild",
                                      # "dwarven_resilience", "hellish_rebuke",
                                      # "infernal_legacy", "draconic_ancestry"
    mechanic_value: str = ""          # e.g. "fire" for draconic ancestry
    uses_per_day: int = -1            # -1 = passive
    damage_dice: str = ""
    damage_type: str = ""
    save_dc: int = 0
    save_ability: str = ""

@dataclass
class SummonTemplate:
    """Template for summoned creatures/objects (Spiritual Weapon, Animate Dead, etc.)"""
    name: str
    hp: int = 0                       # 0 = untargetable object
    ac: int = 10
    speed: int = 20
    fly_speed: int = 0
    attack_bonus: int = 0
    damage_dice: str = ""
    damage_type: str = "force"
    damage_bonus: int = 0
    action_type: str = "bonus"        # bonus for spiritual weapon, action for others
    range: int = 5
    duration_rounds: int = 10
    is_object: bool = True            # True = can't be targeted by most attacks
    owner_side: str = "player"        # "player" or "enemy"

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
    # Hero-specific fields
    character_class: str = ""         # "Fighter", "Wizard", "Barbarian", etc.
    character_level: int = 0          # 0 = NPC/monster
    race: str = ""                    # "Human", "Elf", "Dwarf", etc.
    subclass: str = ""                # "Champion", "Evocation", "Totem Warrior", etc.
    racial_traits: List[RacialTrait] = field(default_factory=list)
    # Resource pools
    ki_points: int = 0               # Monk
    sorcery_points: int = 0          # Sorcerer
    lay_on_hands_pool: int = 0       # Paladin
    rage_count: int = 0              # Barbarian
    bardic_inspiration_dice: str = "" # Bard: "1d8", "1d10", etc.
    bardic_inspiration_count: int = 0
    # Base AC for unarmored defense calculations
    base_ac_unarmored: bool = False   # True = uses unarmored defense formula
