from data.models import CreatureStats, AbilityScores, Action, Feature, SpellInfo
from data.spells import get_spell

monsters = [
    # ------------------------------------------------------------------ #
    # CR 17 – Adult Red Dragon                                            #
    # ------------------------------------------------------------------ #
    CreatureStats(name="Adult Red Dragon", size="Huge", creature_type="Dragon",
        armor_class=19, hit_points=256, hit_dice="19d12+114", speed=40, fly_speed=80, climb_speed=40,
        abilities=AbilityScores(strength=27,dexterity=10,constitution=23,intelligence=16,wisdom=13,charisma=21),
        actions=[
            Action("Multiattack","Bite + 2 Claws",0,"",0,"",reach=10,is_multiattack=True,
                   multiattack_count=3,multiattack_targets=["Bite","Claw","Claw"]),
            Action("Bite","Melee",13,"2d10",8,"piercing",reach=10),
            Action("Claw","Melee",13,"2d6",8,"slashing"),
            Action("Tail","Melee",13,"2d8",8,"bludgeoning",reach=15),
            Action("Fire Breath","Cone 60ft DC 21 DEX half",0,"18d6",0,"fire",range=60,aoe_radius=60,aoe_shape="cone",condition_dc=21,condition_save="Dexterity"),
            Action("Magma Eruption","Lair Action: 20ft radius point",0,"6d6",0,"fire",range=120,action_type="lair",aoe_radius=20,aoe_shape="sphere",condition_dc=15,condition_save="Dexterity"),
        ],
        saving_throws={"Dexterity":6,"Constitution":12,"Wisdom":7,"Charisma":11},
        skills={"Perception":13,"Stealth":6},
        damage_immunities=["fire"],
        features=[
            Feature("Legendary Resistance","3/day auto-succeed","legendary_resist",uses_per_day=3),
            Feature("Fire Breath","Recharge 5-6: 60ft cone 18d6 fire DC 21 DEX half",recharge="5-6"),
            Feature("Frightful Presence","120ft DC 19 WIS or Frightened 1 min"),
        ],
        legendary_action_count=3,
        legendary_resistance_count=3,
        challenge_rating=17.0, xp=18000, proficiency_bonus=6),

    # ------------------------------------------------------------------ #
    # CR 17 – Death Knight                                                #
    # ------------------------------------------------------------------ #
    CreatureStats(name="Death Knight", size="Medium", creature_type="Undead",
        armor_class=20, hit_points=180, hit_dice="19d8+95", speed=30,
        abilities=AbilityScores(strength=20,dexterity=11,constitution=20,intelligence=12,wisdom=16,charisma=18),
        actions=[
            Action("Multiattack","x3 Longsword",0,"",0,"",range=5,is_multiattack=True,
                   multiattack_count=3,multiattack_targets=["Longsword","Longsword","Longsword"]),
            Action("Longsword","Melee",11,"1d8+5","slashing"),
        ],
        saving_throws={"Dexterity":6,"Wisdom":9,"Charisma":10},
        skills={},
        damage_immunities=["necrotic","poison"],
        condition_immunities=["Exhaustion","Frightened","Poisoned"],
        spellcasting_ability="Charisma", spell_save_dc=18, spell_attack_bonus=10,
        spell_slots={"1st":4,"2nd":3,"3rd":3,"4th":3,"5th":1},
        spells_known=[
            get_spell("Animate Dead"),
            get_spell("Banishment"),
            get_spell("Command"),
            get_spell("Dispel Magic"),
            get_spell("Hold Person"),
            get_spell("Magic Weapon", description="Weapon +3"),
            get_spell("Thunderwave"),
        ],
        features=[
            Feature("Legendary Resistance","3/day","legendary_resist",uses_per_day=3),
            Feature("Magic Resistance","Adv on saves vs spells"),
            Feature("Marshal Undead","Undead within 60ft have Adv on attack rolls"),
        ],
        legendary_action_count=3,
        legendary_resistance_count=3,
        challenge_rating=17.0, xp=18000, proficiency_bonus=6),

    # ------------------------------------------------------------------ #
    # CR 20 – Pit Fiend                                                   #
    # ------------------------------------------------------------------ #
    CreatureStats(name="Pit Fiend", size="Large", creature_type="Fiend",
        armor_class=19, hit_points=300, hit_dice="24d10+168", speed=30, fly_speed=60,
        abilities=AbilityScores(strength=26,dexterity=14,constitution=24,intelligence=22,wisdom=18,charisma=24),
        actions=[
            Action("Multiattack","Bite + Claw + Mace + Tail",0,"",0,"",reach=10,is_multiattack=True,
                   multiattack_count=4,multiattack_targets=["Bite","Claw","Mace","Tail"]),
            Action("Bite","Melee",14,"4d6",8,"piercing",applies_condition="Poisoned",condition_dc=21,condition_save="Constitution"),
            Action("Claw","Melee",14,"2d8",8,"slashing"),
            Action("Mace","Melee",14,"2d6+8","bludgeoning"),
            Action("Tail","Melee",14,"2d8+8","bludgeoning",reach=10),
        ],
        saving_throws={"Dexterity":8,"Constitution":13,"Wisdom":10},
        skills={"Deception":13,"Insight":10},
        damage_resistances=["cold","bludgeoning piercing slashing (non-magical, non-silvered)"],
        damage_immunities=["fire","poison"],
        condition_immunities=["Poisoned"],
        features=[
            Feature("Legendary Resistance","3/day","legendary_resist",uses_per_day=3),
            Feature("Magic Resistance","Adv on saves vs spells"),
            Feature("Magic Weapons","Weapon attacks are magical"),
            Feature("Aura of Fear","Creatures within 20ft DC 21 WIS or Frightened",
                    aura_radius=20, save_dc=21, save_ability="Wisdom", applies_condition="Frightened"),
        ],
        legendary_action_count=3,
        legendary_resistance_count=3,
        challenge_rating=20.0, xp=25000, proficiency_bonus=6),

    # ------------------------------------------------------------------ #
    # CR 21 – Lich                                                        #
    # ------------------------------------------------------------------ #
    CreatureStats(name="Lich", size="Medium", creature_type="Undead",
        armor_class=17, hit_points=135, hit_dice="18d8+54", speed=30,
        abilities=AbilityScores(strength=11,dexterity=16,constitution=16,intelligence=20,wisdom=14,charisma=16),
        actions=[
            Action("Paralyzing Touch","Melee",7,"3d6","cold",applies_condition="Paralyzed",
                   condition_save="Constitution",condition_dc=18),
        ],
        saving_throws={"Constitution":10,"Intelligence":12,"Wisdom":9},
        skills={"Arcana":19,"History":12,"Insight":9,"Perception":9},
        damage_resistances=["cold","lightning","necrotic"],
        damage_immunities=["poison","bludgeoning piercing slashing (non-magic)"],
        condition_immunities=["Charmed","Exhaustion","Frightened","Paralyzed","Poisoned"],
        spellcasting_ability="Intelligence", spell_save_dc=20, spell_attack_bonus=12,
        spell_slots={"1st":4,"2nd":3,"3rd":3,"4th":3,"5th":3,"6th":1,"7th":1,"8th":1,"9th":1},
        spells_known=[
            get_spell("Fireball"),
            get_spell("Lightning Bolt"),
            get_spell("Disintegrate"),
            get_spell("Power Word Kill"),
            get_spell("Finger of Death"),
            get_spell("Hold Monster"),
            get_spell("Counterspell"),
            get_spell("Cone of Cold"),
        ],
        cantrips=[
            get_spell("Mage Hand"),
            get_spell("Ray of Frost", attack_bonus_fixed=12),
        ],
        features=[
            Feature("Legendary Resistance","3/day","legendary_resist",uses_per_day=3),
            Feature("Magic Resistance","Adv on saves vs spells"),
            Feature("Rejuvenation","Reforms body after 1d10 days if phylactery intact"),
            Feature("Spellcasting","INT based, 20 DC, +12 attack"),
            Feature("Turn Immunity","Immune to turn undead effects"),
        ],
        legendary_action_count=3,
        legendary_resistance_count=3,
        challenge_rating=21.0, xp=33000, proficiency_bonus=7),

    # ------------------------------------------------------------------ #
    # CR 24 – Ancient Red Dragon                                          #
    # ------------------------------------------------------------------ #
    CreatureStats(name="Ancient Red Dragon", size="Gargantuan", creature_type="Dragon",
        armor_class=22, hit_points=546, hit_dice="28d20+252", speed=40, fly_speed=80, climb_speed=40,
        abilities=AbilityScores(strength=30,dexterity=10,constitution=29,intelligence=18,wisdom=15,charisma=23),
        actions=[
            Action("Multiattack","Frightful Presence then Bite + 2 Claws",0,"",0,"",reach=15,is_multiattack=True,
                   multiattack_count=3,multiattack_targets=["Bite","Claw","Claw"]),
            Action("Bite","Melee",17,"4d6+10","piercing",reach=15),
            Action("Claw","Melee",17,"4d6+10","slashing"),
            Action("Tail","Melee",17,"2d8+10","bludgeoning",reach=20),
            Action("Fire Breath","Cone 90ft DC 24 DEX half",0,"26d6",0,"fire",range=90,aoe_radius=90,aoe_shape="cone",condition_dc=24,condition_save="Dexterity"),
        ],
        saving_throws={"Dexterity":7,"Constitution":16,"Wisdom":9,"Charisma":13},
        skills={"Perception":16,"Stealth":7},
        damage_immunities=["fire"],
        features=[
            Feature("Legendary Resistance","3/day","legendary_resist",uses_per_day=3),
            Feature("Fire Breath","Recharge 5-6: 90ft cone 26d6 fire DC 24 DEX half",recharge="5-6"),
            Feature("Frightful Presence","120ft DC 21 WIS or Frightened 1 min"),
        ],
        legendary_action_count=3,
        legendary_resistance_count=3,
        challenge_rating=24.0, xp=62000, proficiency_bonus=7),
]
