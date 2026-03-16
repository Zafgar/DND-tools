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
    repeat_save: bool = True          # if True, target repeats save at end of turn
    heals: str = ""                   # healing dice e.g. "2d4+2"
    targets: str = "single"          # single, aoe, self, all_allies
    concentration: bool = False
    duration: str = ""                # "1 minute", "1 hour"
    description: str = ""
    half_on_save: bool = True         # AoE spells usually deal half on save
    ritual: bool = False              # PHB p.201: can cast as ritual (10 min extra, no slot)
    components: str = ""              # "V", "V,S", "V,S,M" — for future Silence/Subtle checks
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
    # Terrain creation: spawns persistent terrain on the battlefield
    creates_terrain: str = ""         # terrain_type key from TERRAIN_TYPES (e.g. "darkness", "spike_growth")
    # Innate spellcasting: cast without using spell slots
    innate: bool = False              # True = innate (doesn't consume slot)
    innate_uses_per_day: int = -1     # -1 = at will, >0 = X/day

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
    properties: List[str] = field(default_factory=list)  # weapon: "light","finesse","heavy","reach","thrown","versatile","two-handed","loading"
    long_range: int = 0               # long range in ft (normal range = self.range)

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
    # Phase mechanic: behavior change at HP thresholds
    phase_trigger_hp_pct: float = 0.0 # e.g. 0.5 = triggers at 50% HP
    phase_description: str = ""       # What happens when phase triggers

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
    item_type: str = "potion"         # weapon, armor, shield, potion, scroll, wand,
                                      # wondrous, ring, amulet, cloak, boots, gloves,
                                      # belt, helm, misc
    uses: int = -1                    # -1 = unlimited (equipment), >0 = consumable
    description: str = ""
    heals: str = ""
    damage_dice: str = ""
    applies_condition: str = ""
    buff: str = ""                    # e.g. "resistance:fire"
    # Equipment fields (PHB Ch.5)
    equipped: bool = False            # True = currently worn/wielded
    slot: str = ""                    # "main_hand", "off_hand", "armor", "shield",
                                      # "helm", "cloak", "amulet", "ring1", "ring2",
                                      # "gloves", "boots", "belt"
    requires_attunement: bool = False
    attuned: bool = False
    rarity: str = "common"            # common, uncommon, rare, very_rare, legendary, artifact
    # Armor fields
    base_ac: int = 0                  # Base AC for armor (e.g. 14 for scale mail)
    ac_bonus: int = 0                 # +X bonus (magic armor/shield, Ring of Protection)
    max_dex_bonus: int = -1           # -1 = unlimited, 0 = no DEX, 2 = medium armor
    armor_category: str = ""          # "light", "medium", "heavy", "shield"
    stealth_disadvantage: bool = False
    strength_required: int = 0        # Min STR for heavy armor (PHB p.145)
    # Weapon fields
    weapon_damage_dice: str = ""      # e.g. "1d8" for longsword
    weapon_damage_type: str = ""      # slashing, piercing, bludgeoning
    weapon_properties: List[str] = field(default_factory=list)  # finesse, light, heavy, etc.
    weapon_range: int = 5             # Normal range in feet
    weapon_long_range: int = 0        # Long range (thrown/ranged)
    weapon_bonus: int = 0             # +X magic weapon bonus (to hit AND damage)
    weapon_category: str = ""         # "simple_melee", "martial_melee", "simple_ranged", "martial_ranged"
    # Magic item effects
    stat_bonuses: Dict[str, int] = field(default_factory=dict)  # e.g. {"strength": 19} for Gauntlets
    save_bonuses: Dict[str, int] = field(default_factory=dict)  # e.g. {"all": 1} for Cloak of Protection
    skill_bonuses: Dict[str, int] = field(default_factory=dict) # e.g. {"Perception": 5} for Eyes of the Eagle
    damage_resistances: List[str] = field(default_factory=list)  # resistances granted
    damage_immunities: List[str] = field(default_factory=list)   # immunities granted
    condition_immunities: List[str] = field(default_factory=list) # e.g. ["Frightened"]
    extra_damage_dice: str = ""       # e.g. "1d6" for Flame Tongue
    extra_damage_type: str = ""       # e.g. "fire" for Flame Tongue
    charges: int = 0                  # Magic item charges (wands, staves)
    max_charges: int = 0
    spell_granted: str = ""           # Spell the item can cast
    speed_bonus: int = 0              # e.g. +10 for Boots of Speed
    is_magical: bool = False          # True = overcomes nonmagical resistance

@dataclass
class CreatureStats:
    name: str
    size: str = "Medium"
    creature_type: str = "Humanoid"
    native_plane: str = "Material Plane"
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
    # Items & Equipment
    items: List[Item] = field(default_factory=list)      # All items (inventory)
    # Hero-specific fields
    # Multiclass support
    multiclass: Dict[str, int] = field(default_factory=dict)  # e.g. {"Fighter": 5, "Wizard": 3}
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
