"""AI Scoring Constants used by the Tactical AI."""

# Target scoring weights
KILL_POTENTIAL_BONUS = 50       # Bonus for killable targets
FOCUS_FIRE_WEIGHT = 40          # Max bonus for nearly-dead targets
THREAT_DPR_WEIGHT = 0.5         # Multiplier for enemy DPR contribution
SPELL_SLOT_THREAT = 2           # Per remaining spell slot
CONC_LEVEL_VALUE = 5            # Per spell level of concentration target
CONC_AOE_BONUS = 15             # Bonus for AoE concentration spells
CONC_CONDITION_BONUS = 10       # Bonus for debuff concentration spells
CONC_SUMMON_BONUS = 10          # Bonus for summon concentration spells
HEALER_PRIORITY_BONUS = 15      # Bonus for targeting healers
DISTANCE_PENALTY_WEIGHT = 2     # Per square distance penalty
AC_DIFFICULTY_WEIGHT = 0.5      # Per AC point above 12
MARK_TARGET_BONUS = 25          # Bonus for Hunter's Mark/Hex targets

# Grapple/shove scoring
GRAPPLE_SHOVE_COMBO_VALUE = 40  # Value of the grapple+prone combo

# Action scoring thresholds
DODGE_HP_THRESHOLD = 0.40       # Below this HP%, consider Dodge action
DODGE_CRITICAL_THRESHOLD = 0.25 # Below this HP%, Dodge with even 1 threat
HEAL_MELEE_THRESHOLD = 0.30     # Below this HP%, melee fighters self-heal
HEAL_RANGED_THRESHOLD = 0.35    # Below this HP%, ranged fighters self-heal
DISENGAGE_HP_LOW = 0.20         # Melee fighters disengage below this HP%
