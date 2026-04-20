"""
Tasha's Cauldron of Everything (TCE) — Optional Class Features.

Curated subset of the TCE "Optional Class Features" rules. Each entry is a
(class, min_level, Feature) tuple. The Hero Creator exposes them as player-
choosable toggles on the Features tab; chosen features are appended directly
into CreatureStats.features so they round-trip through existing save/load.

TCE, p.46-90. Optional means the DM can permit them per campaign; they
replace or augment a PHB feature but do not remove it from this data set.
"""
from data.models import Feature


# Each item: (class_name, min_level, Feature)
# Keep descriptions short — full text belongs in the printed rulebook.
TCE_OPTIONAL_FEATURES = [
    # ---- Barbarian ----
    ("Barbarian", 3, Feature(
        name="Primal Knowledge (TCE)",
        description="Gain proficiency in one Strength-/Dex-/Con-/Wis-based skill; use it with advantage while raging.",
        feature_type="class",
        mechanic="primal_knowledge",
    )),
    ("Barbarian", 7, Feature(
        name="Instinctive Pounce (TCE)",
        description="When you Rage on your turn, you can move up to half your speed as part of the same bonus action.",
        feature_type="class",
        mechanic="instinctive_pounce",
    )),

    # ---- Bard ----
    ("Bard", 1, Feature(
        name="Magical Inspiration (TCE)",
        description="Expended Bardic Inspiration die can instead boost a spell's healing or damage.",
        feature_type="class",
        mechanic="magical_inspiration",
    )),
    ("Bard", 4, Feature(
        name="Magical Secrets (Additional, TCE)",
        description="Treated as additional flexible spell access from the expanded list (roleplay gate).",
        feature_type="class",
        mechanic="magical_secrets_extra",
    )),

    # ---- Cleric ----
    ("Cleric", 2, Feature(
        name="Harness Divine Power (TCE)",
        description="Bonus action: expend a use of Channel Divinity to regain one spell slot up to half your proficiency bonus.",
        feature_type="class",
        mechanic="harness_divine_power",
        short_rest_recharge=True,
        uses_per_day=1,
    )),
    ("Cleric", 5, Feature(
        name="Cantrip Versatility (TCE)",
        description="On a long rest that follows an ASI, you may replace one cantrip you know with a new one from the cleric list.",
        feature_type="class",
        mechanic="cantrip_versatility",
    )),

    # ---- Druid ----
    ("Druid", 2, Feature(
        name="Wild Companion (TCE)",
        description="Expend a use of Wild Shape to cast Find Familiar (fey spirit) without components; lasts 1 hour.",
        feature_type="class",
        mechanic="wild_companion",
    )),

    # ---- Fighter ----
    ("Fighter", 2, Feature(
        name="Martial Versatility (TCE)",
        description="On a long rest after gaining a Fighter level that grants an ASI, you may replace a fighting style.",
        feature_type="class",
        mechanic="martial_versatility",
    )),

    # ---- Monk ----
    ("Monk", 2, Feature(
        name="Dedicated Weapon (TCE)",
        description="After a short/long rest, treat one simple or martial weapon without heavy/special as a monk weapon.",
        feature_type="class",
        mechanic="dedicated_weapon",
    )),
    ("Monk", 3, Feature(
        name="Ki-Fueled Attack (TCE)",
        description="If you spent 1+ ki on your turn, you can make one melee weapon / unarmed attack as a bonus action.",
        feature_type="class",
        mechanic="ki_fueled_attack",
    )),

    # ---- Paladin ----
    ("Paladin", 3, Feature(
        name="Harness Divine Power (TCE)",
        description="Bonus action: expend a use of Channel Divinity to regain one spell slot up to half your proficiency bonus.",
        feature_type="class",
        mechanic="harness_divine_power",
        short_rest_recharge=True,
        uses_per_day=1,
    )),
    ("Paladin", 5, Feature(
        name="Martial Versatility (TCE)",
        description="On a long rest after an ASI-granting paladin level, you may swap one of your fighting styles.",
        feature_type="class",
        mechanic="martial_versatility",
    )),

    # ---- Ranger ----
    ("Ranger", 1, Feature(
        name="Favored Foe (TCE)",
        description="Replace Favored Enemy. Bonus 1d4 damage (later 1d6, 1d8) to a marked target 1/turn, concentration, prof-bonus uses.",
        feature_type="class",
        mechanic="favored_foe",
        uses_per_day=2,  # scales with proficiency bonus at higher levels
    )),
    ("Ranger", 1, Feature(
        name="Deft Explorer (TCE)",
        description="Replace Natural Explorer. Gain Canny (expertise + 2 languages). Additional boons at 6 and 10.",
        feature_type="class",
        mechanic="deft_explorer",
    )),

    # ---- Rogue ----
    ("Rogue", 3, Feature(
        name="Steady Aim (TCE)",
        description="Bonus action: grant yourself advantage on your next attack this turn if you haven't moved.",
        feature_type="class",
        mechanic="steady_aim",
    )),

    # ---- Sorcerer ----
    ("Sorcerer", 1, Feature(
        name="Sorcerous Versatility (TCE)",
        description="When you gain a sorcerer ASI, replace one metamagic option or cantrip with another from your list.",
        feature_type="class",
        mechanic="sorcerous_versatility",
    )),
    ("Sorcerer", 3, Feature(
        name="Metamagic (Seeking Spell, TCE)",
        description="2 SP: when an attack spell misses, reroll the attack once and use the new roll.",
        feature_type="class",
        mechanic="metamagic",
        mechanic_value="seeking_spell",
    )),

    # ---- Warlock ----
    ("Warlock", 1, Feature(
        name="Eldritch Versatility (TCE)",
        description="After an ASI, replace one cantrip, Pact Boon, or Eldritch Invocation with an eligible alternative.",
        feature_type="class",
        mechanic="eldritch_versatility",
    )),
    ("Warlock", 2, Feature(
        name="Eldritch Invocation (Investment of the Chain Master, TCE)",
        description="Requires Pact of the Chain. Your familiar gains flying/swim speeds, temp HP, and a DC-based effect.",
        feature_type="class",
        mechanic="eldritch_invocation",
        mechanic_value="investment_chain_master",
    )),

    # ---- Wizard ----
    ("Wizard", 3, Feature(
        name="Cantrip Formulas (TCE)",
        description="When you finish a long rest, you can replace one cantrip you know with another from the wizard list.",
        feature_type="class",
        mechanic="cantrip_formulas",
    )),
]


def get_available_tce_features(char_class: str, level: int) -> list[Feature]:
    """Return all TCE optional class features available to this class at this level."""
    return [
        feat for cls, min_lvl, feat in TCE_OPTIONAL_FEATURES
        if cls == char_class and level >= min_lvl
    ]


def resolve_selected_tce_features(selected_names: list[str]) -> list[Feature]:
    """Map a flat list of chosen TCE feature names back to Feature objects.

    Names are matched case-insensitively against the 'name' field.
    Unknown names are silently ignored (safe for forward-compat saves)."""
    lookup = {feat.name.lower(): feat for _, _, feat in TCE_OPTIONAL_FEATURES}
    out = []
    for name in selected_names:
        feat = lookup.get(name.lower())
        if feat is not None:
            out.append(feat)
    return out
