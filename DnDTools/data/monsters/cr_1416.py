from data.models import CreatureStats, AbilityScores, Action, Feature, SpellInfo
from data.spells import get_spell

monsters = [
    # ------------------------------------------------------------------ #
    # CR 14 – Adult Copper Dragon                                         #
    # ------------------------------------------------------------------ #
    CreatureStats(name="Adult Copper Dragon", size="Huge", creature_type="Dragon",
        armor_class=18, hit_points=184, hit_dice="16d12+80", speed=40, fly_speed=80, climb_speed=40,
        abilities=AbilityScores(strength=23, dexterity=12, constitution=21, intelligence=18, wisdom=15, charisma=17),
        actions=[
            Action("Multiattack", "Bite + 2 Claws", 0, "", 0, "", reach=10, is_multiattack=True,
                   multiattack_count=3, multiattack_targets=["Bite", "Claw", "Claw"]),
            Action("Bite", "Melee", 11, "2d10", 6, "piercing", reach=10),
            Action("Claw", "Melee", 11, "2d6", 6, "slashing"),
            Action("Tail", "Melee", 11, "2d8", 6, "bludgeoning", reach=15),
            Action("Acid Breath", "60ft line DC 18 DEX half", 0, "12d8", 0, "acid",
                   range=60, aoe_radius=60, aoe_shape="line", condition_dc=18, condition_save="Dexterity"),
            Action("Slowing Breath", "60ft cone DC 18 CON or speed halved", 0, "", 0, "",
                   range=60, aoe_radius=60, aoe_shape="cone", condition_dc=18, condition_save="Constitution"),
            # Legendary Actions
            Action("Tail Attack", "Melee", 11, "2d8+6", 0, "bludgeoning", reach=15, action_type="legendary"),
            Action("Wing Attack", "AoE 10ft + Fly", 0, "2d6+6", 0, "bludgeoning", range=0,
                   action_type="legendary", aoe_radius=10, aoe_shape="sphere",
                   condition_dc=19, condition_save="Dexterity", applies_condition="Prone"),
        ],
        saving_throws={"Dexterity": 6, "Constitution": 10, "Wisdom": 7, "Charisma": 8},
        skills={"Deception": 8, "Perception": 12, "Stealth": 6},
        damage_immunities=["acid"],
        features=[
            Feature("Legendary Resistance", "3/day auto-succeed", "legendary_resist", uses_per_day=3),
            Feature("Acid Breath", "Recharge 5-6: 60ft line 12d8 acid DC 18 DEX half", recharge="5-6"),
            Feature("Frightful Presence", "120ft DC 16 WIS or Frightened 1 min"),
            Feature("Tail Attack", "Legendary Action (1 cost)", feature_type="legendary", legendary_cost=1),
            Feature("Wing Attack", "Legendary Action (2 cost)", feature_type="legendary", legendary_cost=2),
        ],
        legendary_action_count=3,
        legendary_resistance_count=3,
        challenge_rating=14.0, xp=11500, proficiency_bonus=5),

    # ------------------------------------------------------------------ #
    # CR 14 – Adult Black Dragon                                          #
    # ------------------------------------------------------------------ #
    CreatureStats(name="Adult Black Dragon", size="Huge", creature_type="Dragon",
        armor_class=19, hit_points=195, hit_dice="17d12+85", speed=40, fly_speed=80, swim_speed=40,
        abilities=AbilityScores(strength=23, dexterity=14, constitution=21, intelligence=14, wisdom=13, charisma=17),
        actions=[
            Action("Multiattack", "Bite + 2 Claws", 0, "", 0, "", reach=10, is_multiattack=True,
                   multiattack_count=3, multiattack_targets=["Bite", "Claw", "Claw"]),
            Action("Bite", "Melee", 11, "2d10", 6, "piercing", reach=10),
            Action("Claw", "Melee", 11, "2d6", 6, "slashing"),
            Action("Tail", "Melee", 11, "2d8", 6, "bludgeoning", reach=15),
            Action("Acid Breath", "60ft line DC 18 DEX half", 0, "12d8", 0, "acid",
                   range=60, aoe_radius=60, aoe_shape="line", condition_dc=18, condition_save="Dexterity"),
            # Legendary Actions
            Action("Tail Attack", "Melee", 11, "2d8+6", 0, "bludgeoning", reach=15, action_type="legendary"),
            Action("Wing Attack", "AoE 10ft + Fly", 0, "2d6+6", 0, "bludgeoning", range=0,
                   action_type="legendary", aoe_radius=10, aoe_shape="sphere",
                   condition_dc=19, condition_save="Dexterity", applies_condition="Prone"),
        ],
        saving_throws={"Dexterity": 7, "Constitution": 10, "Wisdom": 6, "Charisma": 8},
        skills={"Perception": 11, "Stealth": 7},
        damage_immunities=["acid"],
        features=[
            Feature("Legendary Resistance", "3/day auto-succeed", "legendary_resist", uses_per_day=3),
            Feature("Acid Breath", "Recharge 5-6: 60ft line 12d8 acid DC 18 DEX half", recharge="5-6"),
            Feature("Frightful Presence", "120ft DC 16 WIS or Frightened 1 min"),
            Feature("Amphibious", "Can breathe air and water"),
            Feature("Tail Attack", "Legendary Action (1 cost)", feature_type="legendary", legendary_cost=1),
            Feature("Wing Attack", "Legendary Action (2 cost)", feature_type="legendary", legendary_cost=2),
        ],
        legendary_action_count=3,
        legendary_resistance_count=3,
        challenge_rating=14.0, xp=11500, proficiency_bonus=5),

    # ------------------------------------------------------------------ #
    # CR 14 – Adult Green Dragon                                          #
    # ------------------------------------------------------------------ #
    CreatureStats(name="Adult Green Dragon", size="Huge", creature_type="Dragon",
        armor_class=19, hit_points=207, hit_dice="18d12+90", speed=40, fly_speed=80, swim_speed=40,
        abilities=AbilityScores(strength=23, dexterity=12, constitution=21, intelligence=18, wisdom=15, charisma=17),
        actions=[
            Action("Multiattack", "Bite + 2 Claws", 0, "", 0, "", reach=10, is_multiattack=True,
                   multiattack_count=3, multiattack_targets=["Bite", "Claw", "Claw"]),
            Action("Bite", "Melee", 11, "2d10", 6, "piercing", reach=10),
            Action("Claw", "Melee", 11, "2d6", 6, "slashing"),
            Action("Tail", "Melee", 11, "2d8", 6, "bludgeoning", reach=15),
            Action("Poison Breath", "60ft cone DC 18 CON half", 0, "12d6", 0, "poison",
                   range=60, aoe_radius=60, aoe_shape="cone", condition_dc=18, condition_save="Constitution"),
            # Legendary Actions
            Action("Tail Attack", "Melee", 11, "2d8+6", 0, "bludgeoning", reach=15, action_type="legendary"),
            Action("Wing Attack", "AoE 10ft + Fly", 0, "2d6+6", 0, "bludgeoning", range=0,
                   action_type="legendary", aoe_radius=10, aoe_shape="sphere",
                   condition_dc=19, condition_save="Dexterity", applies_condition="Prone"),
        ],
        saving_throws={"Dexterity": 6, "Constitution": 10, "Wisdom": 7, "Charisma": 8},
        skills={"Deception": 8, "Insight": 7, "Perception": 12, "Persuasion": 8, "Stealth": 6},
        damage_immunities=["poison"],
        condition_immunities=["Poisoned"],
        features=[
            Feature("Legendary Resistance", "3/day auto-succeed", "legendary_resist", uses_per_day=3),
            Feature("Poison Breath", "Recharge 5-6: 60ft cone 12d6 poison DC 18 CON half", recharge="5-6"),
            Feature("Frightful Presence", "120ft DC 16 WIS or Frightened 1 min"),
            Feature("Amphibious", "Can breathe air and water"),
            Feature("Tail Attack", "Legendary Action (1 cost)", feature_type="legendary", legendary_cost=1),
            Feature("Wing Attack", "Legendary Action (2 cost)", feature_type="legendary", legendary_cost=2),
        ],
        legendary_action_count=3,
        legendary_resistance_count=3,
        challenge_rating=14.0, xp=11500, proficiency_bonus=5),

    # ------------------------------------------------------------------ #
    # CR 15 – Adult Bronze Dragon                                         #
    # ------------------------------------------------------------------ #
    CreatureStats(name="Adult Bronze Dragon", size="Huge", creature_type="Dragon",
        armor_class=19, hit_points=212, hit_dice="17d12+102", speed=40, fly_speed=80, swim_speed=40,
        abilities=AbilityScores(strength=25, dexterity=10, constitution=23, intelligence=16, wisdom=15, charisma=19),
        actions=[
            Action("Multiattack", "Bite + 2 Claws", 0, "", 0, "", reach=10, is_multiattack=True,
                   multiattack_count=3, multiattack_targets=["Bite", "Claw", "Claw"]),
            Action("Bite", "Melee", 12, "2d10", 7, "piercing", reach=10),
            Action("Claw", "Melee", 12, "2d6", 7, "slashing"),
            Action("Tail", "Melee", 12, "2d8", 7, "bludgeoning", reach=15),
            Action("Lightning Breath", "90ft line DC 19 DEX half", 0, "14d10", 0, "lightning",
                   range=90, aoe_radius=90, aoe_shape="line", condition_dc=19, condition_save="Dexterity"),
            Action("Repulsion Breath", "30ft cone DC 19 STR or pushed 60ft", 0, "", 0, "",
                   range=30, aoe_radius=30, aoe_shape="cone", condition_dc=19, condition_save="Strength"),
            # Legendary Actions
            Action("Tail Attack", "Melee", 12, "2d8+7", 0, "bludgeoning", reach=15, action_type="legendary"),
            Action("Wing Attack", "AoE 10ft + Fly", 0, "2d6+7", 0, "bludgeoning", range=0,
                   action_type="legendary", aoe_radius=10, aoe_shape="sphere",
                   condition_dc=20, condition_save="Dexterity", applies_condition="Prone"),
        ],
        saving_throws={"Dexterity": 5, "Constitution": 11, "Wisdom": 7, "Charisma": 9},
        skills={"Insight": 7, "Perception": 12, "Stealth": 5},
        damage_immunities=["lightning"],
        features=[
            Feature("Legendary Resistance", "3/day auto-succeed", "legendary_resist", uses_per_day=3),
            Feature("Lightning Breath", "Recharge 5-6: 90ft line 14d10 lightning DC 19 DEX half", recharge="5-6"),
            Feature("Frightful Presence", "120ft DC 17 WIS or Frightened 1 min"),
            Feature("Amphibious", "Can breathe air and water"),
            Feature("Tail Attack", "Legendary Action (1 cost)", feature_type="legendary", legendary_cost=1),
            Feature("Wing Attack", "Legendary Action (2 cost)", feature_type="legendary", legendary_cost=2),
        ],
        legendary_action_count=3,
        legendary_resistance_count=3,
        challenge_rating=15.0, xp=13000, proficiency_bonus=5),

    # ------------------------------------------------------------------ #
    # CR 15 – Purple Worm                                                 #
    # ------------------------------------------------------------------ #
    CreatureStats(name="Purple Worm", size="Gargantuan", creature_type="Monstrosity",
        armor_class=18, hit_points=247, hit_dice="15d20+90", speed=50, burrow_speed=30,
        abilities=AbilityScores(strength=28, dexterity=7, constitution=22, intelligence=1, wisdom=8, charisma=4),
        actions=[
            Action("Multiattack", "Bite + Tail Stinger", 0, "", 0, "", reach=10, is_multiattack=True,
                   multiattack_count=2, multiattack_targets=["Bite", "Tail Stinger"]),
            Action("Bite", "Melee", 14, "3d8", 9, "piercing", reach=10),
            Action("Tail Stinger", "Melee", 14, "3d6", 9, "piercing", reach=10,
                   applies_condition="Poisoned", condition_dc=19, condition_save="Constitution"),
        ],
        saving_throws={"Constitution": 11, "Wisdom": 4},
        skills={},
        senses="blindsight 30 ft., tremorsense 60 ft.",
        features=[
            Feature("Tunneler", "Burrow through solid rock at half speed, leaving 10ft tunnel"),
        ],
        challenge_rating=15.0, xp=13000, proficiency_bonus=5),

    # ------------------------------------------------------------------ #
    # CR 15 – Mummy Lord                                                  #
    # ------------------------------------------------------------------ #
    CreatureStats(name="Mummy Lord", size="Medium", creature_type="Undead",
        armor_class=17, hit_points=97, hit_dice="13d8+39", speed=20,
        abilities=AbilityScores(strength=18, dexterity=10, constitution=17, intelligence=11, wisdom=18, charisma=16),
        actions=[
            Action("Multiattack", "Dreadful Glare + Rotting Fist", 0, "", 0, "", range=5, is_multiattack=True,
                   multiattack_count=2, multiattack_targets=["Rotting Fist", "Rotting Fist"]),
            Action("Rotting Fist", "Melee", 9, "3d6", 4, "bludgeoning",
                   applies_condition="Cursed", condition_dc=16, condition_save="Constitution"),
            Action("Dreadful Glare", "60ft DC 16 WIS or Frightened + Paralyzed", 0, "", 0, "",
                   range=60, applies_condition="Frightened", condition_dc=16, condition_save="Wisdom"),
            # Legendary Actions
            Action("Blasphemous Word", "DC 16 CON or Stunned until end of next turn", 0, "", 0, "",
                   range=10, action_type="legendary", applies_condition="Stunned",
                   condition_dc=16, condition_save="Constitution"),
            Action("Channel Negative Energy", "60ft: up to 6 undead regain 1d6 HP", 0, "1d6", 0, "necrotic",
                   range=60, action_type="legendary"),
            Action("Whirlwind of Sand", "AoE blind + 2d8 bludgeoning", 0, "2d8", 0, "bludgeoning",
                   range=0, action_type="legendary", aoe_radius=10, aoe_shape="sphere",
                   applies_condition="Blinded", condition_dc=16, condition_save="Constitution"),
        ],
        saving_throws={"Constitution": 8, "Intelligence": 5, "Wisdom": 9, "Charisma": 8},
        skills={"History": 5, "Religion": 5},
        damage_vulnerabilities=["fire"],
        damage_immunities=["necrotic", "poison", "bludgeoning piercing slashing (non-magic)"],
        condition_immunities=["Charmed", "Exhaustion", "Frightened", "Paralyzed", "Poisoned"],
        spellcasting_ability="Wisdom", spell_save_dc=17, spell_attack_bonus=9,
        spell_slots={"1st": 4, "2nd": 3, "3rd": 3, "4th": 3, "5th": 2, "6th": 1},
        spells_known=[
            get_spell("Animate Dead"),
            get_spell("Dispel Magic"),
            get_spell("Hold Person"),
            get_spell("Contagion") if "Contagion" in dir() else get_spell("Inflict Wounds"),
            get_spell("Harm") if "Harm" in dir() else get_spell("Finger of Death"),
        ],
        cantrips=[get_spell("Sacred Flame")],
        features=[
            Feature("Legendary Resistance", "3/day auto-succeed", "legendary_resist", uses_per_day=3),
            Feature("Magic Resistance", "Adv on saves vs spells"),
            Feature("Rejuvenation", "Reforms after destruction unless heart destroyed"),
            Feature("Blasphemous Word", "Legendary Action (1 cost)", feature_type="legendary", legendary_cost=1),
            Feature("Channel Negative Energy", "Legendary Action (2 cost)", feature_type="legendary", legendary_cost=2),
            Feature("Whirlwind of Sand", "Legendary Action (3 cost)", feature_type="legendary", legendary_cost=3),
        ],
        legendary_action_count=3,
        legendary_resistance_count=3,
        challenge_rating=15.0, xp=13000, proficiency_bonus=5),

    # ------------------------------------------------------------------ #
    # CR 15 – Adult Brass Dragon                                          #
    # ------------------------------------------------------------------ #
    CreatureStats(name="Adult Brass Dragon", size="Huge", creature_type="Dragon",
        armor_class=18, hit_points=172, hit_dice="15d12+75", speed=40, fly_speed=80, burrow_speed=30,
        abilities=AbilityScores(strength=23, dexterity=10, constitution=21, intelligence=14, wisdom=13, charisma=17),
        actions=[
            Action("Multiattack", "Bite + 2 Claws", 0, "", 0, "", reach=10, is_multiattack=True,
                   multiattack_count=3, multiattack_targets=["Bite", "Claw", "Claw"]),
            Action("Bite", "Melee", 11, "2d10", 6, "piercing", reach=10),
            Action("Claw", "Melee", 11, "2d6", 6, "slashing"),
            Action("Tail", "Melee", 11, "2d8", 6, "bludgeoning", reach=15),
            Action("Fire Breath", "60ft line DC 18 DEX half", 0, "13d6", 0, "fire",
                   range=60, aoe_radius=60, aoe_shape="line", condition_dc=18, condition_save="Dexterity"),
            Action("Sleep Breath", "60ft cone DC 18 CON or Unconscious 10 min", 0, "", 0, "",
                   range=60, aoe_radius=60, aoe_shape="cone",
                   applies_condition="Unconscious", condition_dc=18, condition_save="Constitution"),
            # Legendary Actions
            Action("Tail Attack", "Melee", 11, "2d8+6", 0, "bludgeoning", reach=15, action_type="legendary"),
            Action("Wing Attack", "AoE 10ft + Fly", 0, "2d6+6", 0, "bludgeoning", range=0,
                   action_type="legendary", aoe_radius=10, aoe_shape="sphere",
                   condition_dc=19, condition_save="Dexterity", applies_condition="Prone"),
        ],
        saving_throws={"Dexterity": 5, "Constitution": 10, "Wisdom": 6, "Charisma": 8},
        skills={"History": 7, "Perception": 11, "Persuasion": 8, "Stealth": 5},
        damage_immunities=["fire"],
        features=[
            Feature("Legendary Resistance", "3/day auto-succeed", "legendary_resist", uses_per_day=3),
            Feature("Fire Breath", "Recharge 5-6: 60ft line 13d6 fire DC 18 DEX half", recharge="5-6"),
            Feature("Frightful Presence", "120ft DC 16 WIS or Frightened 1 min"),
            Feature("Tail Attack", "Legendary Action (1 cost)", feature_type="legendary", legendary_cost=1),
            Feature("Wing Attack", "Legendary Action (2 cost)", feature_type="legendary", legendary_cost=2),
        ],
        legendary_action_count=3,
        legendary_resistance_count=3,
        challenge_rating=15.0, xp=13000, proficiency_bonus=5),

    # ------------------------------------------------------------------ #
    # CR 16 – Iron Golem                                                  #
    # ------------------------------------------------------------------ #
    CreatureStats(name="Iron Golem", size="Large", creature_type="Construct",
        armor_class=20, hit_points=210, hit_dice="20d10+100", speed=30,
        abilities=AbilityScores(strength=24, dexterity=9, constitution=20, intelligence=3, wisdom=11, charisma=1),
        actions=[
            Action("Multiattack", "x2 Slam", 0, "", 0, "", range=5, is_multiattack=True,
                   multiattack_count=2, multiattack_targets=["Slam", "Slam"]),
            Action("Slam", "Melee", 13, "3d8", 7, "bludgeoning"),
            Action("Sword", "Melee", 13, "3d10", 7, "slashing", reach=10),
            Action("Poison Breath", "15ft cone DC 19 CON or 10d8 poison", 0, "10d8", 0, "poison",
                   range=15, aoe_radius=15, aoe_shape="cone", condition_dc=19, condition_save="Constitution",
                   applies_condition="Poisoned"),
        ],
        damage_immunities=["fire", "poison", "psychic", "bludgeoning piercing slashing (non-magic non-adamantine)"],
        condition_immunities=["Charmed", "Exhaustion", "Frightened", "Paralyzed", "Petrified", "Poisoned"],
        features=[
            Feature("Fire Absorption", "Fire damage heals the golem instead"),
            Feature("Magic Resistance", "Adv on saves vs spells"),
            Feature("Magic Weapons", "Weapon attacks are magical", mechanic="magic_weapons"),
            Feature("Immutable Form", "Immune to form-altering spells"),
            Feature("Poison Breath", "Recharge 5-6: 15ft cone 10d8 poison DC 19 CON", recharge="5-6"),
        ],
        challenge_rating=16.0, xp=15000, proficiency_bonus=5),

    # ------------------------------------------------------------------ #
    # CR 16 – Marilith                                                    #
    # ------------------------------------------------------------------ #
    CreatureStats(name="Marilith", size="Large", creature_type="Fiend",
        armor_class=18, hit_points=189, hit_dice="18d10+90", speed=40,
        native_plane="Abyss",
        abilities=AbilityScores(strength=18, dexterity=20, constitution=20, intelligence=18, wisdom=16, charisma=20),
        actions=[
            Action("Multiattack", "x6 Longsword + Tail", 0, "", 0, "", range=5, is_multiattack=True,
                   multiattack_count=7, multiattack_targets=["Longsword", "Longsword", "Longsword",
                                                              "Longsword", "Longsword", "Longsword", "Tail"]),
            Action("Longsword", "Melee", 9, "2d8", 4, "slashing"),
            Action("Tail", "Melee", 9, "2d10", 4, "bludgeoning", reach=10,
                   applies_condition="Grappled", condition_dc=19, condition_save="Strength"),
        ],
        reactions=[
            Action("Parry", "Reaction: +5 AC against one melee attack", action_type="reaction"),
        ],
        saving_throws={"Strength": 9, "Constitution": 10, "Wisdom": 8, "Charisma": 10},
        skills={},
        damage_resistances=["cold", "fire", "lightning", "bludgeoning piercing slashing (non-magic)"],
        damage_immunities=["poison"],
        condition_immunities=["Poisoned"],
        features=[
            Feature("Magic Resistance", "Adv on saves vs spells"),
            Feature("Magic Weapons", "Weapon attacks are magical", mechanic="magic_weapons"),
            Feature("Reactive", "Can take one reaction on every creature's turn"),
        ],
        challenge_rating=16.0, xp=15000, proficiency_bonus=5),

    # ------------------------------------------------------------------ #
    # CR 16 – Planetar                                                    #
    # ------------------------------------------------------------------ #
    CreatureStats(name="Planetar", size="Large", creature_type="Celestial",
        armor_class=19, hit_points=200, hit_dice="16d10+112", speed=40, fly_speed=120,
        abilities=AbilityScores(strength=24, dexterity=20, constitution=24, intelligence=19, wisdom=22, charisma=25),
        actions=[
            Action("Multiattack", "x2 Greatsword", 0, "", 0, "", range=5, is_multiattack=True,
                   multiattack_count=2, multiattack_targets=["Greatsword", "Greatsword"]),
            Action("Greatsword", "Melee", 12, "4d6+7", 0, "slashing"),
        ],
        saving_throws={"Constitution": 12, "Wisdom": 11, "Charisma": 12},
        skills={"Perception": 11},
        damage_resistances=["radiant", "bludgeoning piercing slashing (non-magic)"],
        condition_immunities=["Charmed", "Exhaustion", "Frightened"],
        spellcasting_ability="Charisma", spell_save_dc=20, spell_attack_bonus=12,
        spells_known=[
            get_spell("Dispel Magic"),
            get_spell("Flame Strike"),
            get_spell("Banishment"),
            get_spell("Mass Cure Wounds"),
        ],
        features=[
            Feature("Magic Resistance", "Adv on saves vs spells"),
            Feature("Magic Weapons", "Weapon attacks are magical + 5d8 radiant", mechanic="magic_weapons"),
            Feature("Divine Awareness", "Knows if it hears a lie"),
            Feature("Angelic Weapons", "Weapon attacks deal +5d8 radiant damage"),
            Feature("Healing Touch", "4/day: touch heals 30 HP + cures conditions",
                    feature_type="class", uses_per_day=4),
        ],
        challenge_rating=16.0, xp=15000, proficiency_bonus=5),

    # ------------------------------------------------------------------ #
    # CR 14 – Beholder Zombie                                             #
    # ------------------------------------------------------------------ #
    CreatureStats(name="Beholder Zombie", size="Large", creature_type="Undead",
        armor_class=15, hit_points=93, hit_dice="11d10+33", speed=0, fly_speed=20,
        abilities=AbilityScores(strength=10, dexterity=8, constitution=16, intelligence=3, wisdom=8, charisma=5),
        actions=[
            Action("Bite", "Melee", 3, "4d6", 0, "piercing"),
            Action("Eye Ray", "Ranged DC 16 DEX or 9d8 necrotic", 0, "9d8", 0, "necrotic",
                   range=60, condition_dc=16, condition_save="Dexterity"),
        ],
        damage_immunities=["poison"],
        condition_immunities=["Poisoned", "Prone"],
        features=[
            Feature("Undead Fortitude", "On 0 HP (non-radiant/crit): CON save DC 5+damage to stay at 1 HP"),
        ],
        challenge_rating=14.0, xp=11500, proficiency_bonus=5),

    # ------------------------------------------------------------------ #
    # CR 15 – Vampire Spellcaster                                         #
    # ------------------------------------------------------------------ #
    CreatureStats(name="Vampire Spellcaster", size="Medium", creature_type="Undead",
        armor_class=16, hit_points=144, hit_dice="17d8+68", speed=30,
        abilities=AbilityScores(strength=18, dexterity=18, constitution=18, intelligence=17, wisdom=15, charisma=18),
        actions=[
            Action("Multiattack", "x2 Claws or Longsword", 0, "", 0, "", range=5, is_multiattack=True,
                   multiattack_count=2, multiattack_targets=["Claws", "Claws"]),
            Action("Claws", "Melee", 9, "2d4", 4, "slashing"),
            Action("Bite", "Melee", 9, "1d6+4", 0, "piercing"),
            # Legendary Actions
            Action("Unarmed Strike", "Melee", 9, "1d8+4", 0, "bludgeoning", action_type="legendary"),
            Action("Bite", "Melee", 9, "1d6+4", 0, "piercing", action_type="legendary"),
        ],
        saving_throws={"Dexterity": 9, "Wisdom": 7, "Charisma": 9},
        skills={"Perception": 7, "Stealth": 9, "Arcana": 8},
        damage_resistances=["necrotic", "bludgeoning piercing slashing (non-magical, non-silvered)"],
        condition_immunities=["Exhaustion"],
        spellcasting_ability="Intelligence", spell_save_dc=17, spell_attack_bonus=9,
        spell_slots={"1st": 4, "2nd": 3, "3rd": 3, "4th": 3, "5th": 2},
        spells_known=[
            get_spell("Fireball"),
            get_spell("Hold Person"),
            get_spell("Counterspell"),
            get_spell("Lightning Bolt"),
            get_spell("Cone of Cold"),
            get_spell("Misty Step"),
        ],
        cantrips=[
            get_spell("Fire Bolt", attack_bonus_fixed=9),
            get_spell("Ray of Frost", attack_bonus_fixed=9),
        ],
        features=[
            Feature("Legendary Resistance", "3/day auto-succeed", "legendary_resist", uses_per_day=3),
            Feature("Regeneration", "Regen 20 HP at start of turn unless in sunlight/running water",
                    mechanic="regeneration", mechanic_value="20"),
            Feature("Magic Resistance", "Adv on saves vs spells"),
            Feature("Misty Escape", "On 0 HP, turn to mist and fly 20ft to coffin"),
            Feature("Unarmed Strike", "Legendary Action (1 cost)", feature_type="legendary", legendary_cost=1),
            Feature("Bite", "Legendary Action (2 cost)", feature_type="legendary", legendary_cost=2),
        ],
        legendary_action_count=3,
        legendary_resistance_count=3,
        challenge_rating=15.0, xp=13000, proficiency_bonus=5),

    # ------------------------------------------------------------------ #
    # CR 16 – Adult Blue Dragon (without lair)                            #
    # ------------------------------------------------------------------ #
    CreatureStats(name="Adult Silver Dragon", size="Huge", creature_type="Dragon",
        armor_class=19, hit_points=243, hit_dice="18d12+126", speed=40, fly_speed=80,
        abilities=AbilityScores(strength=27, dexterity=10, constitution=25, intelligence=16, wisdom=13, charisma=21),
        actions=[
            Action("Multiattack", "Bite + 2 Claws", 0, "", 0, "", reach=10, is_multiattack=True,
                   multiattack_count=3, multiattack_targets=["Bite", "Claw", "Claw"]),
            Action("Bite", "Melee", 13, "2d10", 8, "piercing", reach=10),
            Action("Claw", "Melee", 13, "2d6", 8, "slashing"),
            Action("Tail", "Melee", 13, "2d8", 8, "bludgeoning", reach=15),
            Action("Cold Breath", "60ft cone DC 20 CON half", 0, "13d8", 0, "cold",
                   range=60, aoe_radius=60, aoe_shape="cone", condition_dc=20, condition_save="Constitution"),
            Action("Paralyzing Breath", "60ft cone DC 20 CON or Paralyzed", 0, "", 0, "",
                   range=60, aoe_radius=60, aoe_shape="cone",
                   applies_condition="Paralyzed", condition_dc=20, condition_save="Constitution"),
            # Legendary Actions
            Action("Tail Attack", "Melee", 13, "2d8+8", 0, "bludgeoning", reach=15, action_type="legendary"),
            Action("Wing Attack", "AoE 10ft + Fly", 0, "2d6+8", 0, "bludgeoning", range=0,
                   action_type="legendary", aoe_radius=10, aoe_shape="sphere",
                   condition_dc=21, condition_save="Dexterity", applies_condition="Prone"),
        ],
        saving_throws={"Dexterity": 5, "Constitution": 12, "Wisdom": 6, "Charisma": 10},
        skills={"Arcana": 8, "History": 8, "Perception": 11, "Stealth": 5},
        damage_immunities=["cold"],
        features=[
            Feature("Legendary Resistance", "3/day auto-succeed", "legendary_resist", uses_per_day=3),
            Feature("Cold Breath", "Recharge 5-6: 60ft cone 13d8 cold DC 20 CON half", recharge="5-6"),
            Feature("Frightful Presence", "120ft DC 18 WIS or Frightened 1 min"),
            Feature("Tail Attack", "Legendary Action (1 cost)", feature_type="legendary", legendary_cost=1),
            Feature("Wing Attack", "Legendary Action (2 cost)", feature_type="legendary", legendary_cost=2),
        ],
        legendary_action_count=3,
        legendary_resistance_count=3,
        challenge_rating=16.0, xp=15000, proficiency_bonus=5),

    # ------------------------------------------------------------------ #
    # CR 14 – Fire Giant                                                  #
    # ------------------------------------------------------------------ #
    CreatureStats(name="Fire Giant", size="Huge", creature_type="Giant",
        armor_class=18, hit_points=162, hit_dice="13d12+78", speed=30,
        abilities=AbilityScores(strength=25, dexterity=9, constitution=23, intelligence=10, wisdom=14, charisma=13),
        actions=[
            Action("Multiattack", "x2 Greatsword", 0, "", 0, "", reach=10, is_multiattack=True,
                   multiattack_count=2, multiattack_targets=["Greatsword", "Greatsword"]),
            Action("Greatsword", "Melee", 11, "6d6", 7, "slashing", reach=10),
            Action("Rock", "Ranged", 11, "4d10", 7, "bludgeoning", range=60),
        ],
        saving_throws={"Dexterity": 3, "Constitution": 10, "Charisma": 5},
        skills={"Athletics": 11, "Perception": 6},
        damage_immunities=["fire"],
        features=[],
        challenge_rating=14.0, xp=11500, proficiency_bonus=5),

    # ------------------------------------------------------------------ #
    # CR 16 – Phoenix (Homebrew-balanced Elemental)                       #
    # Tests: fire aura, regeneration, death explosion                     #
    # ------------------------------------------------------------------ #
    CreatureStats(name="Phoenix", size="Gargantuan", creature_type="Elemental",
        armor_class=18, hit_points=175, hit_dice="14d20+28", speed=20, fly_speed=120,
        abilities=AbilityScores(strength=19, dexterity=26, constitution=14, intelligence=2, wisdom=21, charisma=18),
        actions=[
            Action("Multiattack", "x2 Talon", 0, "", 0, "", range=5, is_multiattack=True,
                   multiattack_count=2, multiattack_targets=["Talon", "Talon"]),
            Action("Talon", "Melee", 13, "2d6", 8, "fire"),
            Action("Immolating Gaze", "60ft DC 19 DEX or 8d6 fire", 0, "8d6", 0, "fire",
                   range=60, condition_dc=19, condition_save="Dexterity"),
        ],
        damage_resistances=["bludgeoning piercing slashing (non-magic)"],
        damage_immunities=["fire", "poison"],
        condition_immunities=["Exhaustion", "Grappled", "Paralyzed", "Petrified", "Poisoned",
                             "Prone", "Restrained", "Stunned"],
        features=[
            Feature("Fire Aura", "Creatures within 5ft or touching take 2d6 fire",
                    aura_radius=5, damage_dice="2d6", damage_type="fire"),
            Feature("Regeneration", "Regen 10 HP at start of turn unless took cold damage",
                    mechanic="regeneration", mechanic_value="10"),
            Feature("Death Burst", "On death: 20ft radius DC 20 DEX or 12d6 fire"),
            Feature("Flyby", "Doesn't provoke opportunity attacks when flying"),
            Feature("Illumination", "Sheds bright light 60ft, dim 60ft"),
        ],
        challenge_rating=16.0, xp=15000, proficiency_bonus=5),
]
