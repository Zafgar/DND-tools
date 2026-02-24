# D&D 5e 2014 Conditions with mechanical effects

CONDITIONS = {
    "Blinded": "Fail sight checks. Attacks Disadvantage. Attacks against Advantage.",
    "Charmed": "Cannot attack charmer. Charmer has Advantage on social checks.",
    "Deafened": "Fail hearing-based checks.",
    "Exhaustion": "Cumulative: 1=Disadv checks, 2=Half speed, 3=Disadv attack/saves, 4=Half max HP, 5=Speed 0, 6=Death.",
    "Frightened": "Disadvantage on checks/attacks while source visible. Cannot move closer to source.",
    "Grappled": "Speed 0. Ends when grappler incapacitated or moved out of reach.",
    "Incapacitated": "No actions or reactions.",
    "Invisible": "Advantage on attacks. Attacks against have Disadvantage.",
    "Paralyzed": "Incapacitated. Fail STR/DEX saves. Attacks against Advantage. Hits within 5ft are Critical.",
    "Petrified": "Incapacitated. Resistance to all damage. Immune to poison/disease.",
    "Poisoned": "Disadvantage on attack rolls and ability checks.",
    "Prone": "Crawl only (half speed). Melee attacks against Advantage. Ranged attacks against Disadvantage.",
    "Restrained": "Speed 0. Attacks against Advantage. Attacks Disadvantage. Disadvantage on DEX saves.",
    "Stunned": "Incapacitated. Fail STR/DEX saves. Attacks against Advantage.",
    "Unconscious": "Incapacitated. Drop items. Fail STR/DEX saves. Attacks against Advantage. Hits within 5ft are Critical.",
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
        "crawl_only": True,
        "attacked_advantage_melee": True,
        "attacked_disadvantage_ranged": True,
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
