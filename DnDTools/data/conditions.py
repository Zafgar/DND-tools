# D&D 5e 2014 Conditions with mechanical effects (PHB Appendix A, p.290-292)

CONDITIONS = {
    "Blinded": (
        "A blinded creature can't see and automatically fails any ability check "
        "that requires sight. Attack rolls against the creature have advantage, "
        "and the creature's attack rolls have disadvantage."
    ),
    "Charmed": (
        "A charmed creature can't attack the charmer or target the charmer with "
        "harmful abilities or magical effects. The charmer has advantage on any "
        "ability check to interact socially with the creature."
    ),
    "Deafened": (
        "A deafened creature can't hear and automatically fails any ability check "
        "that requires hearing."
    ),
    "Exhaustion": (
        "Cumulative levels: 1=Disadvantage on ability checks, 2=Speed halved, "
        "3=Disadvantage on attack rolls and saving throws, 4=Hit point maximum halved, "
        "5=Speed reduced to 0, 6=Death."
    ),
    "Frightened": (
        "A frightened creature has disadvantage on ability checks and attack rolls "
        "while the source of its fear is within line of sight. The creature can't "
        "willingly move closer to the source of its fear."
    ),
    "Grappled": (
        "A grappled creature's speed becomes 0, and it can't benefit from any bonus "
        "to its speed. The condition ends if the grappler is incapacitated or if an "
        "effect removes the grappled creature from the reach of the grappler. "
        "KEY: A grappled+prone creature CANNOT stand up (speed is 0)."
    ),
    "Incapacitated": (
        "An incapacitated creature can't take actions or reactions."
    ),
    "Invisible": (
        "An invisible creature is impossible to see without the aid of magic or a "
        "special sense. The creature's location can be detected by noise or tracks. "
        "Attack rolls against the creature have disadvantage, and the creature's "
        "attack rolls have advantage."
    ),
    "Paralyzed": (
        "A paralyzed creature is incapacitated and can't move or speak. The creature "
        "automatically fails Strength and Dexterity saving throws. Attack rolls "
        "against the creature have advantage. Any attack that hits the creature is "
        "a critical hit if the attacker is within 5 feet."
    ),
    "Petrified": (
        "A petrified creature is transformed into a solid inanimate substance. It is "
        "incapacitated, can't move or speak, and is unaware of its surroundings. "
        "It has resistance to all damage, is immune to poison and disease. "
        "Attack rolls against have advantage. Fails STR/DEX saves."
    ),
    "Poisoned": (
        "A poisoned creature has disadvantage on attack rolls and ability checks."
    ),
    "Prone": (
        "A prone creature's only movement option is to crawl (half speed to move), "
        "unless it stands up and thereby ends the condition. Standing up costs half "
        "your speed (you CANNOT stand if speed is 0, e.g. while Grappled). "
        "The creature has disadvantage on attack rolls. An attack roll against the "
        "creature has advantage if the attacker is within 5 feet, otherwise "
        "disadvantage."
    ),
    "Restrained": (
        "A restrained creature's speed becomes 0, and it can't benefit from any "
        "bonus to its speed. Attack rolls against the creature have advantage, and "
        "the creature's attack rolls have disadvantage. The creature has disadvantage "
        "on Dexterity saving throws."
    ),
    "Stunned": (
        "A stunned creature is incapacitated, can't move, and can speak only "
        "falteringly. The creature automatically fails Strength and Dexterity "
        "saving throws. Attack rolls against the creature have advantage."
    ),
    "Unconscious": (
        "An unconscious creature is incapacitated, can't move or speak, and is "
        "unaware of its surroundings. The creature drops whatever it's holding "
        "and falls prone. The creature automatically fails Strength and Dexterity "
        "saving throws. Attack rolls against the creature have advantage. Any "
        "attack that hits the creature is a critical hit if the attacker is within "
        "5 feet of the creature."
    ),
}

# Mechanical effects used by the rules engine
CONDITION_EFFECTS = {
    "Blinded": {
        "attack_disadvantage": True,
        "attacked_advantage": True,
        "fail_sight_checks": True,
    },
    "Charmed": {
        "cannot_attack_source": True,
    },
    "Deafened": {
        "fail_hearing_checks": True,
    },
    "Exhaustion": {
        # Level tracked separately; handled case-by-case
    },
    "Frightened": {
        "attack_disadvantage": True,
        "check_disadvantage": True,
        "cannot_move_toward_source": True,
    },
    "Grappled": {
        "speed_zero": True,
        "prevents_prone_standup": True,  # Can't stand from Prone while speed is 0
    },
    "Incapacitated": {
        "no_actions": True,
        "no_reactions": True,
    },
    "Invisible": {
        "attack_advantage": True,
        "attacked_disadvantage": True,
    },
    "Paralyzed": {
        "incapacitated": True,
        "no_actions": True,
        "no_reactions": True,
        "fail_str_save": True,
        "fail_dex_save": True,
        "attacked_advantage": True,
        "auto_crit_melee": True,
        "speed_zero": True,
    },
    "Petrified": {
        "incapacitated": True,
        "no_actions": True,
        "no_reactions": True,
        "speed_zero": True,
        "resistance_all": True,
        "immune_poison": True,
        "immune_disease": True,
        "fail_str_save": True,
        "fail_dex_save": True,
        "attacked_advantage": True,
    },
    "Poisoned": {
        "attack_disadvantage": True,
        "check_disadvantage": True,
    },
    "Prone": {
        "crawl_only": True,              # Movement = crawling at half speed
        "attack_disadvantage": True,     # PHB: "The creature has disadvantage on attack rolls"
        "attacked_advantage_melee": True,
        "attacked_disadvantage_ranged": True,
        "standup_costs_half_speed": True, # Standing costs half movement speed
    },
    "Restrained": {
        "speed_zero": True,
        "attack_disadvantage": True,
        "attacked_advantage": True,
        "dex_save_disadvantage": True,
    },
    "Stunned": {
        "incapacitated": True,
        "no_actions": True,
        "no_reactions": True,
        "fail_str_save": True,
        "fail_dex_save": True,
        "attacked_advantage": True,
        "speed_zero": True,
    },
    "Unconscious": {
        "incapacitated": True,
        "no_actions": True,
        "no_reactions": True,
        "speed_zero": True,
        "fail_str_save": True,
        "fail_dex_save": True,
        "attacked_advantage": True,
        "auto_crit_melee": True,
    },
}

INCAPACITATING_CONDITIONS = {"Incapacitated", "Paralyzed", "Stunned", "Unconscious", "Petrified"}
SPEED_ZERO_CONDITIONS = {"Grappled", "Restrained", "Paralyzed", "Stunned", "Unconscious", "Petrified"}

# Conditions that prevent standing from Prone (because speed is 0)
PREVENTS_STANDUP_CONDITIONS = {"Grappled", "Restrained", "Paralyzed", "Stunned", "Unconscious", "Petrified"}

# Conditions that require a source entity for their effects (e.g. Frightened, Charmed)
SOURCE_DEPENDENT_CONDITIONS = {"Frightened", "Charmed"}
