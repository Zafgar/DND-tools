from data.models import CreatureStats, AbilityScores, Action, Feature, SpellInfo

monsters = [
    # ------------------------------------------------------------------ #
    # CR 13 – Vampire                                                     #
    # ------------------------------------------------------------------ #
    CreatureStats(name="Vampire", size="Medium", creature_type="Undead",
        armor_class=16, hit_points=144, hit_dice="17d8+68", speed=30,
        abilities=AbilityScores(strength=18,dexterity=18,constitution=18,intelligence=17,wisdom=15,charisma=18),
        actions=[Action("Multiattack","x2 Claws or Longsword",0,"",0,"",range=5,is_multiattack=True,
                        multiattack_count=2,multiattack_targets=["Claws","Claws"]),
                 Action("Claws","Melee",9,"2d4",4,"slashing"),
                 Action("Bite","Melee",9,"1d6+4","piercing"),
                 Action("Longsword","Melee",9,"1d8",4,"slashing"),
                 # Legendary Actions
                 Action("Unarmed Strike","Melee",9,"1d8+4","bludgeoning",action_type="legendary"),
                 Action("Bite","Melee",9,"1d6+4","piercing",action_type="legendary")],
        saving_throws={"Dexterity":9,"Wisdom":7,"Charisma":9},
        skills={"Perception":7,"Stealth":9},
        damage_resistances=["necrotic","bludgeoning piercing slashing (non-magical, non-silvered)"],
        condition_immunities=["Exhaustion"],
        spellcasting_ability="Charisma", spell_save_dc=17, spell_attack_bonus=9,
        features=[Feature("Legendary Resistance","3/day: auto-succeed on failed save","legendary_resist",uses_per_day=3),
                  Feature("Regeneration","Regen 20 HP at start of turn unless in sunlight/running water",
                          mechanic="regeneration", mechanic_value="20"),
                  Feature("Children of the Night","Summon 2d4 bats/rats as action"),
                  Feature("Unarmed Movement","Move up walls and ceilings"),
                  Feature("Misty Escape","On 0 HP, turn to mist and fly 20ft to coffin"),
                  Feature("Unarmed Strike","Legendary Action (1 cost)",feature_type="legendary",legendary_cost=1),
                  Feature("Bite","Legendary Action (2 cost)",feature_type="legendary",legendary_cost=2)],
        legendary_action_count=3,
        legendary_resistance_count=3,
        challenge_rating=13.0, xp=10000, proficiency_bonus=5),

    # ------------------------------------------------------------------ #
    # CR 13 – Beholder                                                    #
    # ------------------------------------------------------------------ #
    CreatureStats(name="Beholder", size="Large", creature_type="Aberration",
        armor_class=18, hit_points=180, hit_dice="19d10+76", speed=0, fly_speed=20,
        abilities=AbilityScores(strength=10,dexterity=14,constitution=18,intelligence=17,wisdom=15,charisma=17),
        actions=[Action("Bite","Melee",5,"4d6","piercing"),
                 Action("Eye Rays","Use 3 random rays on up to 3 targets in 120ft",0,"",0,"",range=120)],
        saving_throws={"Intelligence":8,"Wisdom":7,"Charisma":8},
        skills={"Perception":12},
        condition_immunities=["Prone"],
        features=[Feature("Antimagic Cone","Central eye creates 150ft antimagic cone"),
                  Feature("Eye Rays","Roll d10 for random ray each turn: 1=Charm, 2=Paralyze, 3=Fear, 4=Slow, 5=Exhaust, 6=Disintegrate, 7=Petrify, 8=Shrink, 9=Sleep, 10=Death"),
                  Feature("Legendary Resistance","3/day auto-succeed on failed save","legendary_resist",uses_per_day=3)],
        legendary_action_count=3,
        legendary_resistance_count=3,
        challenge_rating=13.0, xp=10000, proficiency_bonus=5),

    # ------------------------------------------------------------------ #
    # CR 13 – Storm Giant                                                 #
    # ------------------------------------------------------------------ #
    CreatureStats(name="Storm Giant", size="Huge", creature_type="Giant",
        armor_class=16, hit_points=230, hit_dice="20d12+100", speed=50, swim_speed=50, fly_speed=0,
        abilities=AbilityScores(strength=29,dexterity=14,constitution=20,intelligence=16,wisdom=18,charisma=18),
        actions=[Action("Multiattack","x2 Greatsword",0,"",0,"",reach=10,is_multiattack=True,
                        multiattack_count=2,multiattack_targets=["Greatsword","Greatsword"]),
                 Action("Greatsword","Melee",14,"6d6",9,"slashing",reach=10),
                 Action("Rock","Ranged",14,"4d12",9,"bludgeoning",range=60),
                 Action("Lightning Strike","60ft line DC 17 DEX save 12d8 lightning",0,"12d8",0,"lightning",range=60,aoe_radius=60,aoe_shape="line",condition_dc=17,condition_save="Dexterity")],
        saving_throws={"Strength":14,"Constitution":10,"Wisdom":9,"Charisma":9},
        skills={"Arcana":8,"Athletics":14,"History":8,"Perception":9},
        damage_immunities=["cold","lightning","thunder"],
        features=[Feature("Amphibious","Breathe air and water"),
                  Feature("Legendary Resistance","3/day","legendary_resist",uses_per_day=3)],
        legendary_action_count=3,
        legendary_resistance_count=3,
        challenge_rating=13.0, xp=10000, proficiency_bonus=5),

    # ------------------------------------------------------------------ #
    # CR 13 – Rakshasa                                                    #
    # ------------------------------------------------------------------ #
    CreatureStats(name="Rakshasa", size="Medium", creature_type="Fiend",
        armor_class=16, hit_points=110, hit_dice="13d8+52", speed=40,
        abilities=AbilityScores(strength=14,dexterity=17,constitution=18,intelligence=13,wisdom=16,charisma=20),
        actions=[
            Action("Multiattack","x2 Claws",0,"",0,"",range=5,is_multiattack=True,
                   multiattack_count=2,multiattack_targets=["Claw","Claw"]),
            Action("Claw","Melee",7,"2d6",2,"slashing",
                   applies_condition="Cursed",condition_dc=18,condition_save="Wisdom"),
        ],
        damage_vulnerabilities=["piercing (magic from good-aligned)"],
        damage_immunities=["bludgeoning piercing slashing (non-magic)"],
        features=[
            Feature("Limited Magic Immunity","Can't be affected or detected by spells of 6th level or lower unless it wishes to be"),
            Feature("Innate Spellcasting","DC 18. At will: Detect Thoughts, Disguise Self, Mage Hand, Minor Illusion. 3/day each: Charm Person, Detect Magic, Invisibility, Major Image, Suggestion. 1/day each: Dominate Person, Fly, Plane Shift, True Seeing"),
        ],
        challenge_rating=13.0, xp=10000, proficiency_bonus=5),

    # ------------------------------------------------------------------ #
    # CR 13 – Adult White Dragon                                          #
    # ------------------------------------------------------------------ #
    CreatureStats(name="Adult White Dragon", size="Huge", creature_type="Dragon",
        armor_class=18, hit_points=200, hit_dice="16d12+96", speed=40, burrow_speed=30, fly_speed=80, swim_speed=40,
        abilities=AbilityScores(strength=22,dexterity=10,constitution=22,intelligence=8,wisdom=12,charisma=12),
        actions=[
            Action("Multiattack","Bite + 2 Claws",0,"",0,"",reach=10,is_multiattack=True,
                   multiattack_count=3,multiattack_targets=["Bite","Claw","Claw"]),
            Action("Bite","Melee",11,"2d10",6,"piercing",reach=10),
            Action("Claw","Melee",11,"2d6",6,"slashing"),
            Action("Tail","Melee",11,"2d8",6,"bludgeoning",reach=15),
            Action("Cold Breath","60ft cone DC 19 CON half",0,"12d8",0,"cold",
                   range=60,aoe_radius=60,aoe_shape="cone",condition_dc=19,condition_save="Constitution"),
            # Legendary Actions
            Action("Tail Attack","Melee",11,"2d8+6","bludgeoning",reach=15,action_type="legendary"),
            Action("Wing Attack","AoE 10ft + Fly",0,"2d6+6",0,"bludgeoning",range=0,action_type="legendary",aoe_radius=10,aoe_shape="sphere",condition_dc=19,condition_save="Dexterity",applies_condition="Prone"),
        ],
        damage_immunities=["cold"],
        features=[
            Feature("Legendary Resistance","3/day auto-succeed on failed save","legendary_resist",uses_per_day=3),
            Feature("Cold Breath","Recharge 5-6: 60ft cone 12d8 cold DC 19 CON half",recharge="5-6"),
            Feature("Frightful Presence","120ft DC 14 WIS or Frightened 1 min"),
            Feature("Tail Attack","Legendary Action (1 cost)",feature_type="legendary",legendary_cost=1),
            Feature("Wing Attack","Legendary Action (2 cost)",feature_type="legendary",legendary_cost=2),
        ],
        legendary_action_count=3,
        legendary_resistance_count=3,
        challenge_rating=13.0, xp=10000, proficiency_bonus=5),

    # ------------------------------------------------------------------ #
    # CR 13 – Nalfeshnee                                                  #
    # ------------------------------------------------------------------ #
    CreatureStats(name="Nalfeshnee", size="Large", creature_type="Fiend",
        armor_class=18, hit_points=184, hit_dice="16d10+96", speed=20, fly_speed=30,
        abilities=AbilityScores(strength=21,dexterity=10,constitution=22,intelligence=19,wisdom=12,charisma=15),
        actions=[
            Action("Multiattack","Bite + Claws",0,"",0,"",range=5,is_multiattack=True,
                   multiattack_count=2,multiattack_targets=["Bite","Claws"]),
            Action("Bite","Melee",10,"5d10",5,"piercing"),
            Action("Claws","Melee",10,"3d6",5,"slashing"),
            Action("Horror Nimbus","60ft radius DC 15 WIS or Frightened",0,"",0,"",
                   range=60,aoe_radius=60,aoe_shape="sphere",
                   applies_condition="Frightened",condition_dc=15,condition_save="Wisdom"),
        ],
        damage_resistances=["cold","fire","lightning","bludgeoning piercing slashing (non-magic)"],
        damage_immunities=["poison"],
        condition_immunities=["Poisoned"],
        features=[
            Feature("Horror Nimbus","Recharge 5-6: 60ft DC 15 WIS or Frightened",recharge="5-6"),
            Feature("Teleport","Magically teleport up to 120ft to unoccupied space"),
            Feature("Magic Resistance","Adv on saves vs spells"),
        ],
        challenge_rating=13.0, xp=10000, proficiency_bonus=5),
]
