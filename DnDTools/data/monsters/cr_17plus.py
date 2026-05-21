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
            # Legendary Actions
            Action("Tail Attack","Melee",17,"2d8+10","bludgeoning",reach=20,action_type="legendary"),
            Action("Wing Attack","AoE 10ft + Fly",0,"2d6+10",0,"bludgeoning",range=0,action_type="legendary",
                   aoe_radius=10,aoe_shape="sphere",condition_dc=25,condition_save="Dexterity",applies_condition="Prone"),
        ],
        saving_throws={"Dexterity":6,"Constitution":12,"Wisdom":7,"Charisma":11},
        skills={"Perception":13,"Stealth":6},
        damage_immunities=["fire"],
        features=[
            Feature("Legendary Resistance","3/day auto-succeed","legendary_resist",uses_per_day=3),
            Feature("Fire Breath","Recharge 5-6: 60ft cone 18d6 fire DC 21 DEX half",recharge="5-6"),
            Feature("Frightful Presence","120ft DC 19 WIS or Frightened 1 min"),
            Feature("Tail Attack","Legendary Action (1 cost)",feature_type="legendary",legendary_cost=1),
            Feature("Wing Attack","Legendary Action (2 cost): Damage + Prone + Fly half speed",feature_type="legendary",legendary_cost=2),
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
        armor_class=19, hit_points=300, hit_dice="24d10+168", speed=30, fly_speed=60, native_plane="Nine Hells",
        abilities=AbilityScores(strength=26,dexterity=14,constitution=24,intelligence=22,wisdom=18,charisma=24),
        actions=[
            Action("Multiattack","Bite + Claw + Mace + Tail",0,"",0,"",reach=10,is_multiattack=True,
                   multiattack_count=4,multiattack_targets=["Bite","Claw","Mace","Tail"]),
            Action("Bite","Melee",14,"4d6",8,"piercing",applies_condition="Poisoned",condition_dc=21,condition_save="Constitution"),
            Action("Claw","Melee",14,"2d8",8,"slashing",reach=10),
            Action("Mace","Melee",14,"2d6+8","bludgeoning",reach=10),
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
            # Legendary Actions
            Action("Cantrip","Cast Ray of Frost",12,"4d8",0,"cold",range=60,action_type="legendary"),
            Action("Paralyzing Touch","Melee",7,"3d6","cold",applies_condition="Paralyzed",condition_save="Constitution",condition_dc=18,action_type="legendary"),
            Action("Frightening Gaze","Fix gaze on one creature. DC 20 WIS or Frightened.",0,"",0,"",range=10,action_type="legendary",applies_condition="Frightened",condition_dc=20,condition_save="Wisdom"),
            Action("Disrupt Life","Each non-undead within 20ft DC 18 CON or 6d6 necrotic",0,"6d6",0,"necrotic",range=0,action_type="legendary",aoe_radius=20,aoe_shape="sphere",condition_dc=18,condition_save="Constitution"),
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
            Feature("Cantrip","Legendary Action (1 cost)",feature_type="legendary",legendary_cost=1),
            Feature("Paralyzing Touch","Legendary Action (2 cost)",feature_type="legendary",legendary_cost=2),
            Feature("Frightening Gaze","Legendary Action (2 cost)",feature_type="legendary",legendary_cost=2),
            Feature("Disrupt Life","Legendary Action (3 cost)",feature_type="legendary",legendary_cost=3),
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
            Action("Claw","Melee",17,"4d6+10","slashing",reach=10),
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

    # ------------------------------------------------------------------ #
    # CR 17 – Dracolich (Adult Blue)                                     #
    # Undead dragon with lair actions. Tests: legendary + lair + immunities
    # ------------------------------------------------------------------ #
    CreatureStats(name="Dracolich", size="Huge", creature_type="Undead",
        armor_class=19, hit_points=225, hit_dice="18d12+108", speed=40, fly_speed=80, burrow_speed=30,
        abilities=AbilityScores(strength=25,dexterity=10,constitution=23,intelligence=16,wisdom=15,charisma=19),
        actions=[
            Action("Multiattack","Bite + 2 Claws",0,"",0,"",reach=10,is_multiattack=True,
                   multiattack_count=3,multiattack_targets=["Bite","Claw","Claw"]),
            Action("Bite","Melee",12,"2d10+7","piercing",reach=10),
            Action("Claw","Melee",12,"2d6+7","slashing"),
            Action("Tail","Melee",12,"2d8+7","bludgeoning",reach=15),
            Action("Lightning Breath","90ft line DC 20 DEX half",0,"16d10",0,"lightning",
                   range=90,aoe_radius=90,aoe_shape="line",condition_dc=20,condition_save="Dexterity"),
            # Lair Actions
            Action("Sand Sinkhole","Lair: 20ft radius DC 15 DEX or Restrained by sand",
                   0,"",0,"",range=120,action_type="lair",aoe_radius=20,aoe_shape="sphere",
                   applies_condition="Restrained",condition_dc=15,condition_save="Dexterity"),
            Action("Static Discharge","Lair: 15ft radius lightning burst",0,"4d6",0,"lightning",
                   range=120,action_type="lair",aoe_radius=15,aoe_shape="sphere",
                   condition_dc=15,condition_save="Dexterity"),
            Action("Necrotic Miasma","Lair: 20ft radius DC 15 CON or 3d6 necrotic + no healing",
                   0,"3d6",0,"necrotic",range=90,action_type="lair",aoe_radius=20,aoe_shape="sphere",
                   condition_dc=15,condition_save="Constitution"),
            # Legendary Actions
            Action("Tail Attack","Melee",12,"2d8+7","bludgeoning",reach=15,action_type="legendary"),
            Action("Wing Attack","AoE 10ft + Fly",0,"2d6+7",0,"bludgeoning",range=0,
                   action_type="legendary",aoe_radius=10,aoe_shape="sphere",
                   condition_dc=20,condition_save="Dexterity",applies_condition="Prone"),
        ],
        saving_throws={"Dexterity":5,"Constitution":11,"Wisdom":7,"Charisma":9},
        skills={"Perception":12,"Stealth":5},
        damage_immunities=["lightning","poison","necrotic"],
        damage_resistances=["bludgeoning piercing slashing (non-magic)"],
        condition_immunities=["Charmed","Exhaustion","Frightened","Paralyzed","Poisoned"],
        features=[
            Feature("Legendary Resistance","3/day auto-succeed","legendary_resist",uses_per_day=3),
            Feature("Lightning Breath","Recharge 5-6: 90ft line 16d10 lightning DC 20 DEX half",recharge="5-6"),
            Feature("Magic Resistance","Adv on saves vs spells"),
            Feature("Frightful Presence","120ft DC 18 WIS or Frightened 1 min"),
            Feature("Turn Resistance","Adv on saves vs Turn Undead"),
            Feature("Tail Attack","Legendary Action (1 cost)",feature_type="legendary",legendary_cost=1),
            Feature("Wing Attack","Legendary Action (2 cost)",feature_type="legendary",legendary_cost=2),
        ],
        legendary_action_count=3,
        legendary_resistance_count=3,
        challenge_rating=17.0, xp=18000, proficiency_bonus=6),

    # ------------------------------------------------------------------ #
    # CR 17 – Adult Blue Dragon (with Lair Actions)                      #
    # Tests: lair actions, breath weapon, legendary actions                #
    # ------------------------------------------------------------------ #
    CreatureStats(name="Adult Blue Dragon", size="Huge", creature_type="Dragon",
        armor_class=19, hit_points=225, hit_dice="18d12+108", speed=40, fly_speed=80, burrow_speed=30,
        abilities=AbilityScores(strength=25,dexterity=10,constitution=23,intelligence=16,wisdom=15,charisma=19),
        actions=[
            Action("Multiattack","Bite + 2 Claws",0,"",0,"",reach=10,is_multiattack=True,
                   multiattack_count=3,multiattack_targets=["Bite","Claw","Claw"]),
            Action("Bite","Melee",12,"2d10",7,"piercing",reach=10),
            Action("Claw","Melee",12,"2d6",7,"slashing"),
            Action("Tail","Melee",12,"2d8",7,"bludgeoning",reach=15),
            Action("Lightning Breath","90ft line DC 19 DEX half",0,"12d10",0,"lightning",
                   range=90,aoe_radius=90,aoe_shape="line",condition_dc=19,condition_save="Dexterity"),
            # Lair Actions
            Action("Thunderclap","Lair: 20ft radius DC 15 CON or Stunned until next lair action",
                   0,"",0,"thunder",range=120,action_type="lair",aoe_radius=20,aoe_shape="sphere",
                   applies_condition="Stunned",condition_dc=15,condition_save="Constitution"),
            Action("Sand Wall","Lair: 15ft line wall blocks LOS and movement",
                   0,"",0,"",range=120,action_type="lair",aoe_radius=15,aoe_shape="line"),
            # Legendary Actions
            Action("Tail Attack","Melee",12,"2d8+7","bludgeoning",reach=15,action_type="legendary"),
            Action("Wing Attack","AoE 10ft + Fly",0,"2d6+7",0,"bludgeoning",range=0,
                   action_type="legendary",aoe_radius=10,aoe_shape="sphere",
                   condition_dc=20,condition_save="Dexterity",applies_condition="Prone"),
        ],
        saving_throws={"Dexterity":5,"Constitution":11,"Wisdom":7,"Charisma":9},
        skills={"Perception":12,"Stealth":5},
        damage_immunities=["lightning"],
        features=[
            Feature("Legendary Resistance","3/day auto-succeed","legendary_resist",uses_per_day=3),
            Feature("Lightning Breath","Recharge 5-6: 90ft line 12d10 lightning DC 19 DEX half",recharge="5-6"),
            Feature("Frightful Presence","120ft DC 17 WIS or Frightened 1 min"),
            Feature("Tail Attack","Legendary Action (1 cost)",feature_type="legendary",legendary_cost=1),
            Feature("Wing Attack","Legendary Action (2 cost)",feature_type="legendary",legendary_cost=2),
        ],
        legendary_action_count=3,
        legendary_resistance_count=3,
        challenge_rating=17.0, xp=18000, proficiency_bonus=6),

    # ------------------------------------------------------------------ #
    # CR 20 – Ancient White Dragon (with Lair Actions)                   #
    # Tests: lair actions with conditions, legendary + breath weapon      #
    # ------------------------------------------------------------------ #
    CreatureStats(name="Ancient White Dragon", size="Gargantuan", creature_type="Dragon",
        armor_class=20, hit_points=333, hit_dice="18d20+144", speed=40, fly_speed=80, swim_speed=40, burrow_speed=40,
        abilities=AbilityScores(strength=26,dexterity=10,constitution=26,intelligence=10,wisdom=13,charisma=14),
        actions=[
            Action("Multiattack","Frightful Presence + Bite + 2 Claws",0,"",0,"",reach=15,is_multiattack=True,
                   multiattack_count=3,multiattack_targets=["Bite","Claw","Claw"]),
            Action("Bite","Melee",14,"2d10+8","piercing",reach=15),
            Action("Claw","Melee",14,"2d6+8","slashing",reach=10),
            Action("Tail","Melee",14,"2d8+8","bludgeoning",reach=20),
            Action("Cold Breath","90ft cone DC 22 CON half",0,"16d8",0,"cold",
                   range=90,aoe_radius=90,aoe_shape="cone",condition_dc=22,condition_save="Constitution"),
            # Lair Actions
            Action("Freezing Fog","Lair: 20ft radius DC 15 CON or Blinded until next lair action",
                   0,"",0,"cold",range=120,action_type="lair",aoe_radius=20,aoe_shape="sphere",
                   applies_condition="Blinded",condition_dc=15,condition_save="Constitution"),
            Action("Ice Spikes","Lair: 15ft radius 3d6 piercing + difficult terrain",
                   0,"3d6",0,"piercing",range=120,action_type="lair",aoe_radius=15,aoe_shape="sphere",
                   condition_dc=15,condition_save="Dexterity"),
            Action("Icy Gale","Lair: 30ft line DC 15 STR or pushed 15ft + Prone",
                   0,"2d6",0,"cold",range=30,action_type="lair",aoe_radius=30,aoe_shape="line",
                   applies_condition="Prone",condition_dc=15,condition_save="Strength"),
            # Legendary Actions
            Action("Tail Attack","Melee",14,"2d8+8","bludgeoning",reach=20,action_type="legendary"),
            Action("Wing Attack","AoE 15ft + Fly",0,"2d6+8",0,"bludgeoning",range=0,
                   action_type="legendary",aoe_radius=15,aoe_shape="sphere",
                   condition_dc=22,condition_save="Dexterity",applies_condition="Prone"),
        ],
        saving_throws={"Dexterity":6,"Constitution":14,"Wisdom":7,"Charisma":8},
        skills={"Perception":13,"Stealth":6},
        damage_immunities=["cold"],
        features=[
            Feature("Legendary Resistance","3/day","legendary_resist",uses_per_day=3),
            Feature("Cold Breath","Recharge 5-6: 90ft cone 16d8 cold DC 22 CON half",recharge="5-6"),
            Feature("Frightful Presence","120ft DC 16 WIS or Frightened 1 min"),
            Feature("Ice Walk","Move across icy surfaces without ability check, difficult terrain (ice/snow) costs no extra movement"),
            Feature("Tail Attack","Legendary Action (1 cost)",feature_type="legendary",legendary_cost=1),
            Feature("Wing Attack","Legendary Action (2 cost)",feature_type="legendary",legendary_cost=2),
        ],
        legendary_action_count=3,
        legendary_resistance_count=3,
        challenge_rating=20.0, xp=25000, proficiency_bonus=6),

    # ------------------------------------------------------------------ #
    # CR 21 – Death Tyrant (Undead Beholder with Lair Actions)           #
    # Tests: legendary + lair + eye rays + conditions                     #
    # ------------------------------------------------------------------ #
    CreatureStats(name="Death Tyrant", size="Large", creature_type="Undead",
        armor_class=19, hit_points=187, hit_dice="25d10+50", speed=0, fly_speed=20,
        abilities=AbilityScores(strength=10,dexterity=14,constitution=14,intelligence=19,wisdom=15,charisma=19),
        actions=[
            Action("Bite","Melee",5,"4d6","piercing"),
            Action("Eye Rays","3 random rays on up to 3 targets within 120ft",0,"",0,"",range=120),
            Action("Charm Ray","DC 17 WIS or Charmed for 1 hour",0,"",0,"",range=120,
                   applies_condition="Charmed",condition_dc=17,condition_save="Wisdom"),
            Action("Fear Ray","DC 17 WIS or Frightened for 1 minute",0,"",0,"",range=120,
                   applies_condition="Frightened",condition_dc=17,condition_save="Wisdom"),
            Action("Paralyzing Ray","DC 17 CON or Paralyzed for 1 minute",0,"",0,"",range=120,
                   applies_condition="Paralyzed",condition_dc=17,condition_save="Constitution"),
            Action("Enervation Ray","Ranged",0,"8d8",0,"necrotic",range=120,
                   condition_dc=17,condition_save="Constitution"),
            Action("Disintegration Ray","DC 17 DEX or 10d8 force. 0 HP = disintegrated.",0,"10d8",0,"force",
                   range=120,condition_dc=17,condition_save="Dexterity"),
            # Lair Actions
            Action("Negative Energy Cone","Lair: 50ft cone. Creatures at 0 HP die. Others DC 15 CON or 3d6 necrotic.",
                   0,"3d6",0,"necrotic",range=50,action_type="lair",aoe_radius=50,aoe_shape="cone",
                   condition_dc=15,condition_save="Constitution"),
            Action("Telekinetic Slam","Lair: DC 15 STR or creature dragged 25ft + 2d6 bludgeoning",
                   0,"2d6",0,"bludgeoning",range=120,action_type="lair",
                   condition_dc=15,condition_save="Strength"),
            Action("Slippery Ground","Lair: 10ft area becomes slippery, DC 15 DEX or Prone",
                   0,"",0,"",range=120,action_type="lair",aoe_radius=10,aoe_shape="sphere",
                   applies_condition="Prone",condition_dc=15,condition_save="Dexterity"),
            # Legendary Actions
            Action("Eye Ray","Use one random eye ray",0,"",0,"",range=120,action_type="legendary"),
        ],
        saving_throws={"Strength":5,"Constitution":7,"Intelligence":9,"Wisdom":7,"Charisma":9},
        skills={"Perception":12},
        damage_immunities=["poison"],
        condition_immunities=["Charmed","Exhaustion","Paralyzed","Petrified","Poisoned","Prone"],
        features=[
            Feature("Legendary Resistance","3/day auto-succeed on failed save","legendary_resist",uses_per_day=3),
            Feature("Negative Energy Cone","60ft cone: dead creatures rise as zombies under Death Tyrant's control"),
            Feature("Antimagic Cone","Central eye creates 150ft antimagic cone forward"),
            Feature("Eye Ray","Legendary Action (1 cost)",feature_type="legendary",legendary_cost=1),
        ],
        legendary_action_count=3,
        legendary_resistance_count=3,
        challenge_rating=21.0, xp=33000, proficiency_bonus=7),

    # ------------------------------------------------------------------ #
    # CR 23 – Kraken (with Lair Actions)                                 #
    # Tests: massive HP, lair mechanics, grapple, legendary actions       #
    # ------------------------------------------------------------------ #
    CreatureStats(name="Kraken", size="Gargantuan", creature_type="Monstrosity",
        armor_class=18, hit_points=472, hit_dice="27d20+189", speed=20, swim_speed=60,
        abilities=AbilityScores(strength=30,dexterity=11,constitution=25,intelligence=22,wisdom=18,charisma=20),
        actions=[
            Action("Multiattack","x3 Tentacle or x2 Tentacle + Fling",0,"",0,"",reach=30,is_multiattack=True,
                   multiattack_count=3,multiattack_targets=["Tentacle","Tentacle","Tentacle"]),
            Action("Bite","Melee",17,"3d8+10","piercing",reach=5),
            Action("Tentacle","Melee",17,"3d6+10","bludgeoning",reach=30,
                   applies_condition="Grappled",condition_dc=18,condition_save="Strength"),
            Action("Fling","Throw grappled creature 60ft. DC 18 STR or 3d6+10 bludgeoning on landing.",
                   0,"3d6",10,"bludgeoning",range=60,condition_dc=18,condition_save="Strength",
                   applies_condition="Prone"),
            Action("Lightning Storm","120ft radius: up to 3 bolts, DC 23 DEX or 4d10 lightning each",
                   0,"4d10",0,"lightning",range=120,aoe_radius=120,aoe_shape="sphere",
                   condition_dc=23,condition_save="Dexterity"),
            # Lair Actions
            Action("Strong Current","Lair: DC 18 STR or pushed 60ft + Prone",0,"",0,"",
                   range=120,action_type="lair",aoe_radius=30,aoe_shape="sphere",
                   applies_condition="Prone",condition_dc=18,condition_save="Strength"),
            Action("Tidal Wave","Lair: 30ft line 4d10 bludgeoning + DC 18 STR or Prone",
                   0,"4d10",0,"bludgeoning",range=120,action_type="lair",aoe_radius=30,aoe_shape="line",
                   applies_condition="Prone",condition_dc=18,condition_save="Strength"),
            Action("Whirlpool","Lair: 25ft radius DC 18 STR or Restrained and 2d8 bludgeoning per round",
                   0,"2d8",0,"bludgeoning",range=120,action_type="lair",aoe_radius=25,aoe_shape="sphere",
                   applies_condition="Restrained",condition_dc=18,condition_save="Strength"),
            # Legendary Actions
            Action("Tentacle Attack","One tentacle attack",17,"3d6+10","bludgeoning",reach=30,
                   action_type="legendary",applies_condition="Grappled",condition_dc=18,condition_save="Strength"),
            Action("Lightning Storm","1 bolt 4d10 lightning",0,"4d10",0,"lightning",
                   range=120,action_type="legendary",condition_dc=23,condition_save="Dexterity"),
            Action("Ink Cloud","Creates 60ft cloud of ink (Blinded in area)",0,"",0,"",
                   range=0,action_type="legendary",aoe_radius=60,aoe_shape="sphere",
                   applies_condition="Blinded",condition_dc=23,condition_save="Constitution"),
        ],
        saving_throws={"Strength":17,"Dexterity":7,"Constitution":14,"Intelligence":13,"Wisdom":11},
        skills={"Perception":14},
        damage_immunities=["lightning","bludgeoning piercing slashing (non-magic)"],
        condition_immunities=["Frightened","Paralyzed"],
        features=[
            Feature("Legendary Resistance","3/day","legendary_resist",uses_per_day=3),
            Feature("Siege Monster","Double damage to objects and structures"),
            Feature("Freedom of Movement","Cannot be restrained, escape non-magical restraints with 5ft movement"),
            Feature("Lightning Storm","Recharge 5-6: 3 bolts 4d10 lightning each DC 23 DEX half",recharge="5-6"),
            Feature("Tentacle Attack","Legendary Action (1 cost)",feature_type="legendary",legendary_cost=1),
            Feature("Lightning Storm","Legendary Action (2 cost)",feature_type="legendary",legendary_cost=2),
            Feature("Ink Cloud","Legendary Action (3 cost): 60ft radius blindness",feature_type="legendary",legendary_cost=3),
        ],
        legendary_action_count=3,
        legendary_resistance_count=3,
        challenge_rating=23.0, xp=50000, proficiency_bonus=7),

    # ------------------------------------------------------------------ #
    # CR 22 – Ancient Black Dragon (with Lair Actions)                   #
    # Tests: acid breath, water lair, legendary + frightful presence      #
    # ------------------------------------------------------------------ #
    CreatureStats(name="Ancient Black Dragon", size="Gargantuan", creature_type="Dragon",
        armor_class=22, hit_points=367, hit_dice="21d20+147", speed=40, fly_speed=80, swim_speed=40,
        abilities=AbilityScores(strength=27,dexterity=14,constitution=25,intelligence=16,wisdom=15,charisma=19),
        actions=[
            Action("Multiattack","Frightful Presence + Bite + 2 Claws",0,"",0,"",reach=15,is_multiattack=True,
                   multiattack_count=3,multiattack_targets=["Bite","Claw","Claw"]),
            Action("Bite","Melee",15,"2d10+8","piercing",reach=15),
            Action("Claw","Melee",15,"2d6+8","slashing",reach=10),
            Action("Tail","Melee",15,"2d8+8","bludgeoning",reach=20),
            Action("Acid Breath","90ft line DC 22 DEX half",0,"15d8",0,"acid",
                   range=90,aoe_radius=90,aoe_shape="line",condition_dc=22,condition_save="Dexterity"),
            # Lair Actions
            Action("Insect Swarm","Lair: 20ft radius 3d6 piercing + DC 15 CON or Poisoned",
                   0,"3d6",0,"piercing",range=120,action_type="lair",aoe_radius=20,aoe_shape="sphere",
                   applies_condition="Poisoned",condition_dc=15,condition_save="Constitution"),
            Action("Grasping Mire","Lair: 20ft radius DC 15 STR or Restrained by mud",
                   0,"",0,"",range=120,action_type="lair",aoe_radius=20,aoe_shape="sphere",
                   applies_condition="Restrained",condition_dc=15,condition_save="Strength"),
            Action("Darkness","Lair: 20ft radius magical darkness (Blinded)",0,"",0,"",
                   range=120,action_type="lair",aoe_radius=20,aoe_shape="sphere",
                   applies_condition="Blinded",condition_dc=0),
            # Legendary Actions
            Action("Tail Attack","Melee",15,"2d8+8","bludgeoning",reach=20,action_type="legendary"),
            Action("Wing Attack","AoE 15ft + Fly",0,"2d6+8",0,"bludgeoning",range=0,
                   action_type="legendary",aoe_radius=15,aoe_shape="sphere",
                   condition_dc=23,condition_save="Dexterity",applies_condition="Prone"),
        ],
        saving_throws={"Dexterity":9,"Constitution":14,"Wisdom":9,"Charisma":11},
        skills={"Perception":15,"Stealth":9},
        damage_immunities=["acid"],
        features=[
            Feature("Legendary Resistance","3/day","legendary_resist",uses_per_day=3),
            Feature("Acid Breath","Recharge 5-6: 90ft line 15d8 acid DC 22 DEX half",recharge="5-6"),
            Feature("Frightful Presence","120ft DC 19 WIS or Frightened 1 min"),
            Feature("Amphibious","Can breathe air and water"),
            Feature("Tail Attack","Legendary Action (1 cost)",feature_type="legendary",legendary_cost=1),
            Feature("Wing Attack","Legendary Action (2 cost)",feature_type="legendary",legendary_cost=2),
        ],
        legendary_action_count=3,
        legendary_resistance_count=3,
        challenge_rating=22.0, xp=41000, proficiency_bonus=7),

    # ------------------------------------------------------------------ #
    # CR 18 – Demilich (with Lair Actions)                               #
    # Tests: tiny size, life drain, howl, lair, legendary                  #
    # ------------------------------------------------------------------ #
    CreatureStats(name="Demilich", size="Tiny", creature_type="Undead",
        armor_class=20, hit_points=80, hit_dice="20d4", speed=0, fly_speed=30,
        abilities=AbilityScores(strength=1,dexterity=20,constitution=10,intelligence=20,wisdom=17,charisma=20),
        actions=[
            Action("Howl","Recharge 5-6: 30ft radius DC 15 CON or drop to 0 HP",0,"10d6",0,"necrotic",
                   range=0,aoe_radius=30,aoe_shape="sphere",condition_dc=15,condition_save="Constitution"),
            Action("Life Drain","Ranged: DC 19 CON or 6d6 necrotic, max HP reduced",
                   0,"6d6",0,"necrotic",range=10,condition_dc=19,condition_save="Constitution"),
            # Lair Actions
            Action("Skull Vortex","Lair: 10ft radius DC 15 DEX or 3d6 necrotic + pushed 10ft",
                   0,"3d6",0,"necrotic",range=120,action_type="lair",aoe_radius=10,aoe_shape="sphere",
                   condition_dc=15,condition_save="Dexterity"),
            Action("Antimagic Zone","Lair: 15ft radius antimagic field until next lair action",
                   0,"",0,"",range=120,action_type="lair",aoe_radius=15,aoe_shape="sphere"),
            Action("Soul Siphon","Lair: DC 15 CHA or 2d8 necrotic + Frightened until next lair action",
                   0,"2d8",0,"necrotic",range=120,action_type="lair",
                   applies_condition="Frightened",condition_dc=15,condition_save="Charisma"),
            # Legendary Actions
            Action("Flight","Move up to half flying speed",0,"",0,"",range=0,action_type="legendary"),
            Action("Cloud of Dust","10ft sphere of blinding dust. DC 15 CON or Blinded for 1 min.",
                   0,"",0,"",range=0,action_type="legendary",aoe_radius=10,aoe_shape="sphere",
                   applies_condition="Blinded",condition_dc=15,condition_save="Constitution"),
            Action("Energy Drain","DC 19 CON: 6d6 necrotic, max HP reduced by amount dealt.",
                   0,"6d6",0,"necrotic",range=10,action_type="legendary",
                   condition_dc=19,condition_save="Constitution"),
            Action("Vile Curse","DC 19 CHA or cursed. Disadvantage on attacks and saves.",
                   0,"",0,"",range=30,action_type="legendary",
                   applies_condition="Cursed",condition_dc=19,condition_save="Charisma"),
        ],
        saving_throws={"Constitution":6,"Intelligence":11,"Wisdom":9,"Charisma":11},
        damage_resistances=["bludgeoning piercing slashing (magic)"],
        damage_immunities=["necrotic","poison","psychic","bludgeoning piercing slashing (non-magic)"],
        condition_immunities=["Charmed","Deafened","Exhaustion","Frightened","Paralyzed",
                             "Petrified","Poisoned","Prone","Stunned"],
        features=[
            Feature("Legendary Resistance","5/day auto-succeed on failed save","legendary_resist",uses_per_day=5),
            Feature("Avoidance","If subjected to effect with half damage on save, takes no damage on success, half on fail"),
            Feature("Turn Immunity","Immune to effects that turn undead"),
            Feature("Howl","Recharge 5-6: 30ft DC 15 CON or drop to 0 HP",recharge="5-6"),
            Feature("Flight","Legendary Action (1 cost)",feature_type="legendary",legendary_cost=1),
            Feature("Cloud of Dust","Legendary Action (2 cost)",feature_type="legendary",legendary_cost=2),
            Feature("Energy Drain","Legendary Action (2 cost)",feature_type="legendary",legendary_cost=2),
            Feature("Vile Curse","Legendary Action (3 cost)",feature_type="legendary",legendary_cost=3),
        ],
        legendary_action_count=5,
        legendary_resistance_count=5,
        challenge_rating=18.0, xp=20000, proficiency_bonus=6,
        lore=("All that remains of a lich whose phylactery was "
              "destroyed but whose mind clings to undeath. A "
              "demilich is a desiccated skull set with gems where "
              "its eyes once were — each gem the trapped soul of a "
              "previous victim."),
        tactics=("Opens with Howl to instantly drop low-HP PCs. "
                  "Stays 30+ ft up via Flight; Energy Drain on "
                  "clustered targets. Avoidance means Fireball does "
                  "nothing on a successful save. Saves LR for "
                  "Polymorph / Banishment / Disintegrate."),
        loot_table=("Phylactery (must be destroyed permanently). "
                     "6-8 soul gems (1500 gp each, each trapping "
                     "an NPC who can be restored). Spell components "
                     "worth 3000 gp."),
        habitat="Forgotten crypts, Acererak-style tombs",
        sources="MM p.48"),

    # ------------------------------------------------------------------ #
    # CR 19 – Balor (with Lair Actions)                                  #
    # Tests: fire aura, massive melee, lair, death explosion              #
    # ------------------------------------------------------------------ #
    CreatureStats(name="Balor", size="Huge", creature_type="Fiend",
        armor_class=19, hit_points=262, hit_dice="21d12+126", speed=40, fly_speed=80,
        native_plane="Abyss",
        abilities=AbilityScores(strength=26,dexterity=15,constitution=22,intelligence=20,wisdom=16,charisma=22),
        actions=[
            Action("Multiattack","Longsword + Whip",0,"",0,"",reach=10,is_multiattack=True,
                   multiattack_count=2,multiattack_targets=["Longsword","Whip"]),
            Action("Longsword","Melee",14,"3d8+8","slashing",reach=10),
            Action("Whip","Melee",14,"2d6+8","slashing",reach=30),
            # Lair Actions
            Action("Demonic Gate","Lair: Summon 1d4 dretches or 1 shadow demon",
                   0,"",0,"",range=60,action_type="lair"),
            Action("Flame Rift","Lair: 20ft radius 4d6 fire eruption from ground",
                   0,"4d6",0,"fire",range=120,action_type="lair",aoe_radius=20,aoe_shape="sphere",
                   condition_dc=18,condition_save="Dexterity"),
            Action("Abyssal Corruption","Lair: DC 18 CHA or Frightened + 2d6 psychic",
                   0,"2d6",0,"psychic",range=120,action_type="lair",
                   applies_condition="Frightened",condition_dc=18,condition_save="Charisma"),
            # Legendary Actions
            Action("Teleport","Teleport up to 120ft to unoccupied space",0,"",0,"",
                   range=120,action_type="legendary"),
            Action("Fire Aura","Each creature within 10ft takes 3d6 fire",0,"3d6",0,"fire",
                   range=0,action_type="legendary",aoe_radius=10,aoe_shape="sphere"),
        ],
        saving_throws={"Strength":14,"Constitution":12,"Wisdom":9,"Charisma":12},
        skills={"Perception":9,"Intimidation":12},
        damage_resistances=["cold","lightning","bludgeoning piercing slashing (non-magic)"],
        damage_immunities=["fire","poison"],
        condition_immunities=["Poisoned"],
        features=[
            Feature("Legendary Resistance","3/day","legendary_resist",uses_per_day=3),
            Feature("Magic Resistance","Adv on saves vs spells"),
            Feature("Magic Weapons","Weapon attacks are magical",mechanic="magic_weapons"),
            Feature("Death Throes","When killed, explodes: 20ft radius DC 20 DEX or 14d6 fire half on save"),
            Feature("Fire Aura","Creatures starting turn within 5ft or touching take 3d6 fire",
                    aura_radius=5, damage_dice="3d6", damage_type="fire"),
            Feature("Teleport","Legendary Action (1 cost)",feature_type="legendary",legendary_cost=1),
            Feature("Fire Aura","Legendary Action (2 cost)",feature_type="legendary",legendary_cost=2),
        ],
        legendary_action_count=3,
        legendary_resistance_count=3,
        challenge_rating=19.0, xp=22000, proficiency_bonus=6),

    # ------------------------------------------------------------------ #
    # CR 30 — Tarrasque (MM p.286) — earth-shaker, no LR but huge HP &  #
    # legendary actions; immune to most casting via Reflective Carapace #
    # ------------------------------------------------------------------ #
    CreatureStats(name="Tarrasque", size="Gargantuan",
        creature_type="Monstrosity",
        armor_class=25, hit_points=676, hit_dice="33d20+330",
        speed=40,
        abilities=AbilityScores(strength=30, dexterity=11,
                                  constitution=30, intelligence=3,
                                  wisdom=11, charisma=11),
        actions=[
            Action("Multiattack", "Bite + 2 Claws + Tail + Horns",
                    0, "", 0, "", reach=15, is_multiattack=True,
                    multiattack_count=5,
                    multiattack_targets=["Bite", "Claw", "Claw",
                                          "Tail", "Horns"]),
            Action("Bite", "Melee", 19, "4d12+10", 0, "piercing",
                    reach=10,
                    applies_condition="Grappled",
                    condition_dc=20, condition_save="Strength"),
            Action("Claw", "Melee", 19, "4d8+10", 0, "slashing",
                    reach=15),
            Action("Horns", "Melee", 19, "4d10+10", 0, "piercing",
                    reach=10),
            Action("Tail", "Melee", 19, "4d6+10", 0, "bludgeoning",
                    reach=20,
                    applies_condition="Prone",
                    condition_dc=20, condition_save="Strength"),
            Action("Swallow",
                    "Replaces Bite on a grappled Large or smaller. "
                    "Target takes 6d6 acid each turn inside, escape "
                    "DC 20 STR.",
                    0, "6d6", 0, "acid"),
            # Legendary actions
            Action("Move", "Half movement",
                    0, "", 0, "", action_type="legendary"),
            Action("Chomp", "Bite attack (legendary, 2 cost)",
                    19, "4d12+10", 0, "piercing",
                    reach=10, action_type="legendary"),
            Action("Tail Sweep",
                    "Tail attack (legendary, 2 cost)",
                    19, "4d6+10", 0, "bludgeoning",
                    reach=20, action_type="legendary"),
        ],
        saving_throws={"Intelligence": 5, "Wisdom": 9, "Charisma": 9},
        damage_resistances=[
            "bludgeoning piercing slashing (non-magic)"
        ],
        damage_immunities=["fire", "poison"],
        condition_immunities=["Charmed", "Frightened", "Paralyzed",
                                "Poisoned"],
        features=[
            Feature("Legendary Resistance",
                     "3/day automatic save success",
                     "legendary_resist", uses_per_day=3),
            Feature("Magic Resistance",
                     "Advantage on saves against spells and other "
                     "magical effects."),
            Feature("Reflective Carapace",
                     "Any time the tarrasque is targeted by a magic "
                     "missile spell, line, or ray, roll d6. On 1-5 "
                     "the tarrasque is unaffected. On 6 the spell "
                     "reflects back on the caster, using its DC."),
            Feature("Siege Monster",
                     "Doubles damage to objects and structures."),
            Feature("Move", "Legendary Action (1 cost): move up to "
                              "half its speed",
                     feature_type="legendary", legendary_cost=1),
            Feature("Chomp",
                     "Legendary Action (2 cost): make one Bite "
                     "attack or use Swallow",
                     feature_type="legendary", legendary_cost=2),
            Feature("Tail Sweep",
                     "Legendary Action (2 cost): make one Tail "
                     "attack",
                     feature_type="legendary", legendary_cost=2),
        ],
        legendary_action_count=3,
        legendary_resistance_count=3,
        challenge_rating=30.0, xp=155000, proficiency_bonus=9,
        lore=("The Tarrasque is the deadliest land creature ever "
              "known — a hibernating apocalypse. Said to be one "
              "of a kind. When it wakes, kingdoms fall. Its "
              "carapace reflects magic missiles back at casters."),
        tactics=("Walks toward the largest threat. Bites it, then "
                  "uses Swallow. Tail Sweep AoE legendary clears "
                  "skirmishers. Reflective Carapace makes single-"
                  "target line/ray spells worse than useless. "
                  "Tank-and-spank doesn't work — must kite or "
                  "find magical solutions (Wish, Power Word Kill, "
                  "etc.)."),
        loot_table=("Tarrasque hide (artifact armor crafting). "
                     "Tarrasque heart (Wish-component analogue, "
                     "100,000+ gp). No traditional hoard."),
        habitat="Deep underground (hibernates millennia)",
        sources="MM p.286"),

    # ------------------------------------------------------------------ #
    # CR 21 — Solar (MM p.18) — top-tier angelic boss                   #
    # ------------------------------------------------------------------ #
    CreatureStats(name="Solar", size="Large", creature_type="Celestial",
        armor_class=21, hit_points=243, hit_dice="18d10+144",
        speed=50, fly_speed=150,
        abilities=AbilityScores(strength=26, dexterity=22,
                                  constitution=26, intelligence=25,
                                  wisdom=25, charisma=30),
        actions=[
            Action("Multiattack", "x2 Slaying Longsword",
                    0, "", 0, "", reach=10, is_multiattack=True,
                    multiattack_count=2,
                    multiattack_targets=["Slaying Longsword",
                                          "Slaying Longsword"]),
            Action("Slaying Longsword",
                    "Melee +15, 1d8+8 slashing + 6d8 radiant",
                    15, "1d8", 8, "slashing", reach=10),
            Action("Slaying Bow",
                    "Ranged +13, 2d6+8 piercing + 6d8 radiant. "
                    "If target is below 100 HP, save DC 15 CON or "
                    "be reduced to 0 HP.",
                    13, "2d6", 8, "piercing",
                    range=150, long_range=600,
                    condition_dc=15, condition_save="Constitution"),
            Action("Flying Sword",
                    "Detached blade with own actions, attack +15",
                    15, "1d8", 8, "slashing", range=120),
            Action("Healing Touch",
                    "4/day touch heals 40 HP and removes one disease/"
                    "poison/charm/frightened.",
                    0, "40", 0, "healing", range=0),
            Action("Searing Burst",
                    "Legendary Action (2 cost): 10-ft radius, all "
                    "creatures DC 23 DEX save or 14d6 fire half.",
                    0, "14d6", 0, "fire", range=120,
                    aoe_radius=10, aoe_shape="sphere",
                    action_type="legendary",
                    condition_dc=23, condition_save="Dexterity"),
            Action("Blinding Gaze",
                    "Legendary Action (1 cost): single target DC 15 "
                    "CON save or be Blinded until end of next turn.",
                    0, "", 0, "", range=120,
                    action_type="legendary",
                    applies_condition="Blinded",
                    condition_dc=15, condition_save="Constitution"),
        ],
        saving_throws={"Intelligence": 14, "Wisdom": 14,
                         "Charisma": 17},
        damage_resistances=[
            "radiant", "bludgeoning piercing slashing (non-magic)"
        ],
        damage_immunities=["necrotic", "poison"],
        condition_immunities=["Charmed", "Exhaustion", "Frightened",
                                "Poisoned"],
        features=[
            Feature("Legendary Resistance",
                     "3/day automatic save success",
                     "legendary_resist", uses_per_day=3),
            Feature("Angelic Weapons",
                     "Solar's weapon attacks are magical; melee "
                     "deals an extra 6d8 radiant, ranged extra 6d8."),
            Feature("Divine Awareness",
                     "Knows when it hears a lie."),
            Feature("Innate Spellcasting",
                     "At will: detect evil and good, invisibility; "
                     "3/day: blade barrier, dispel evil and good, "
                     "resurrection, commune, control weather; "
                     "1/day: holy aura."),
            Feature("Magic Resistance",
                     "Advantage on saves against spells."),
            Feature("Searing Burst",
                     "Legendary Action (2 cost)",
                     feature_type="legendary", legendary_cost=2),
            Feature("Blinding Gaze",
                     "Legendary Action (1 cost)",
                     feature_type="legendary", legendary_cost=1),
        ],
        legendary_action_count=3,
        legendary_resistance_count=3,
        challenge_rating=21.0, xp=33000, proficiency_bonus=7,
        lore=("Solars are the highest order of angels, agents of "
              "the gods of good. Each is a being of pure righteousness "
              "armed with a slaying longsword and bow that can banish "
              "or kill the unworthy with a glance."),
        tactics=("Opens with a Slaying Bow shot at a low-HP enemy. "
                  "Uses Healing Touch on dying allies. Detaches its "
                  "Flying Sword to threaten ranged casters while it "
                  "melees a tank. Legendary Searing Burst when "
                  "surrounded."),
        loot_table=("Treasure Hoard 17+. Always carries a +3 "
                     "longsword (its slaying blade often disappears "
                     "on death), holy gemstones (4d6 × 1000 gp), and "
                     "a divine token tied to its patron deity."),
        habitat="Upper Planes (Celestia, Elysium, Arborea)",
        sources="MM p.18"),

    # ------------------------------------------------------------------ #
    # CR 20 — Ancient Brass Dragon (MM p.104)                          #
    # ------------------------------------------------------------------ #
    CreatureStats(name="Ancient Brass Dragon", size="Gargantuan",
        creature_type="Dragon",
        armor_class=20, hit_points=297, hit_dice="17d20+119",
        speed=40, fly_speed=80, burrow_speed=40,
        abilities=AbilityScores(strength=27, dexterity=10,
                                  constitution=25, intelligence=16,
                                  wisdom=15, charisma=19),
        actions=[
            Action("Multiattack", "Bite + 2 Claws",
                    0, "", 0, "", reach=15, is_multiattack=True,
                    multiattack_count=3,
                    multiattack_targets=["Bite","Claw","Claw"]),
            Action("Bite", "Melee", 14, "2d10+8", 0, "piercing",
                    reach=15),
            Action("Claw", "Melee", 14, "2d6+8", 0, "slashing",
                    reach=10),
            Action("Tail", "Melee", 14, "2d8+8", 0, "bludgeoning",
                    reach=20),
            Action("Fire Breath",
                    "90-ft line, DC 21 DEX save, 16d6 fire half",
                    0, "16d6", 0, "fire", range=90,
                    aoe_radius=90, aoe_shape="line",
                    condition_dc=21, condition_save="Dexterity"),
            Action("Sleep Breath",
                    "90-ft line, DC 21 CON save or fall asleep 10 min",
                    0, "", 0, "", range=90,
                    aoe_radius=90, aoe_shape="line",
                    applies_condition="Unconscious",
                    condition_dc=21, condition_save="Constitution"),
            # Legendary
            Action("Tail Attack", "Legendary (1)", 14, "2d8+8", 0,
                    "bludgeoning", reach=20, action_type="legendary"),
            Action("Wing Attack",
                    "Legendary (2): 15-ft radius, DC 22 DEX or "
                    "2d6+8 bludgeoning + Prone; dragon flies "
                    "half speed",
                    0, "2d6", 8, "bludgeoning",
                    action_type="legendary",
                    aoe_radius=15, aoe_shape="sphere",
                    condition_dc=22, condition_save="Dexterity",
                    applies_condition="Prone"),
        ],
        saving_throws={"Dexterity": 6, "Constitution": 13,
                         "Wisdom": 8, "Charisma": 10},
        skills={"Perception": 14, "Persuasion": 10, "Stealth": 6},
        damage_immunities=["fire"],
        features=[
            Feature("Legendary Resistance", "3/day",
                     "legendary_resist", uses_per_day=3),
            Feature("Frightful Presence",
                     "120-ft, DC 18 WIS or Frightened 1 min"),
            Feature("Fire Breath", "Recharge 5-6", recharge="5-6"),
            Feature("Sleep Breath", "Recharge 5-6", recharge="5-6"),
            Feature("Tail Attack", "Legendary 1",
                     feature_type="legendary", legendary_cost=1),
            Feature("Wing Attack", "Legendary 2",
                     feature_type="legendary", legendary_cost=2),
        ],
        legendary_action_count=3, legendary_resistance_count=3,
        challenge_rating=20.0, xp=25000, proficiency_bonus=7,
        lore=("Brass dragons are the most talkative of the metallic "
              "kin — they will literally chat a party to death if "
              "permitted. Vain, friendly when respected, prone to "
              "lengthy monologues about their own cleverness."),
        tactics=("Opens conversation, not combat. If pushed, Sleep "
                  "Breath the most threatening melee threat, then "
                  "fly out of reach and Fire Breath. Always keeps a "
                  "Legendary Wing Attack for escape if HP drops "
                  "below 100."),
        loot_table=("Treasure Hoard 17+ (desert). Hoard contains "
                     "many oddities collected from \"interesting "
                     "conversationalists\" rather than pure gold."),
        habitat="Hot deserts, sandy wastes",
        sources="MM p.104"),

    # ------------------------------------------------------------------ #
    # CR 22 — Ancient Bronze Dragon (MM p.108)                         #
    # ------------------------------------------------------------------ #
    CreatureStats(name="Ancient Bronze Dragon", size="Gargantuan",
        creature_type="Dragon",
        armor_class=22, hit_points=444, hit_dice="24d20+192",
        speed=40, fly_speed=80, swim_speed=40,
        abilities=AbilityScores(strength=29, dexterity=10,
                                  constitution=27, intelligence=18,
                                  wisdom=17, charisma=21),
        actions=[
            Action("Multiattack", "Bite + 2 Claws",
                    0, "", 0, "", reach=15, is_multiattack=True,
                    multiattack_count=3,
                    multiattack_targets=["Bite","Claw","Claw"]),
            Action("Bite", "Melee", 16, "2d10+9", 0, "piercing",
                    reach=15),
            Action("Claw", "Melee", 16, "2d6+9", 0, "slashing",
                    reach=10),
            Action("Tail", "Melee", 16, "2d8+9", 0, "bludgeoning",
                    reach=20),
            Action("Lightning Breath",
                    "120-ft line, DC 23 DEX, 16d10 lightning half",
                    0, "16d10", 0, "lightning", range=120,
                    aoe_radius=120, aoe_shape="line",
                    condition_dc=23, condition_save="Dexterity"),
            Action("Repulsion Breath",
                    "30-ft cone, DC 23 STR or pushed 60 ft",
                    0, "", 0, "", range=30,
                    aoe_radius=30, aoe_shape="cone",
                    condition_dc=23, condition_save="Strength"),
            # Legendary
            Action("Tail Attack", "Legendary (1)", 16, "2d8+9", 0,
                    "bludgeoning", reach=20, action_type="legendary"),
            Action("Wing Attack",
                    "Legendary (2): 15-ft radius DC 24 DEX or "
                    "2d6+9 + Prone",
                    0, "2d6", 9, "bludgeoning",
                    action_type="legendary",
                    aoe_radius=15, aoe_shape="sphere",
                    condition_dc=24, condition_save="Dexterity",
                    applies_condition="Prone"),
        ],
        saving_throws={"Dexterity": 7, "Constitution": 15,
                         "Wisdom": 10, "Charisma": 12},
        damage_immunities=["lightning"],
        features=[
            Feature("Legendary Resistance", "3/day",
                     "legendary_resist", uses_per_day=3),
            Feature("Amphibious", "Breathes air and water",
                     mechanic="amphibious"),
            Feature("Frightful Presence",
                     "120-ft, DC 20 WIS or Frightened"),
            Feature("Lightning Breath", "Recharge 5-6", recharge="5-6"),
            Feature("Repulsion Breath", "Recharge 5-6", recharge="5-6"),
            Feature("Tail Attack", "Legendary 1",
                     feature_type="legendary", legendary_cost=1),
            Feature("Wing Attack", "Legendary 2",
                     feature_type="legendary", legendary_cost=2),
        ],
        legendary_action_count=3, legendary_resistance_count=3,
        challenge_rating=22.0, xp=41000, proficiency_bonus=7,
        lore=("Bronze dragons are coastal champions of justice — "
              "they take the form of friendly sailors to gauge a "
              "ship's crew before deciding whether to help or sink "
              "it. They hate slavers and pirate fleets with a "
              "particular passion."),
        tactics=("Opens with Repulsion Breath to scatter the party "
                  "into the water. Follows up with Lightning Breath "
                  "down the line where PCs landed. Legendary Tail "
                  "Attacks on swimming PCs."),
        loot_table=("Treasure Hoard 17+. Frequently includes lost "
                     "naval relics, magical compasses, salvaged "
                     "magic items from shipwrecks."),
        habitat="Coastal seas, lagoons",
        sources="MM p.108"),

    # ------------------------------------------------------------------ #
    # CR 21 — Ancient Copper Dragon (MM p.112)                         #
    # ------------------------------------------------------------------ #
    CreatureStats(name="Ancient Copper Dragon", size="Gargantuan",
        creature_type="Dragon",
        armor_class=21, hit_points=350, hit_dice="20d20+140",
        speed=40, fly_speed=80, climb_speed=40,
        abilities=AbilityScores(strength=27, dexterity=12,
                                  constitution=25, intelligence=20,
                                  wisdom=17, charisma=19),
        actions=[
            Action("Multiattack", "Bite + 2 Claws",
                    0, "", 0, "", reach=15, is_multiattack=True,
                    multiattack_count=3,
                    multiattack_targets=["Bite","Claw","Claw"]),
            Action("Bite", "Melee", 15, "2d10+8", 0, "piercing",
                    reach=15),
            Action("Claw", "Melee", 15, "2d6+8", 0, "slashing",
                    reach=10),
            Action("Tail", "Melee", 15, "2d8+8", 0, "bludgeoning",
                    reach=20),
            Action("Acid Breath",
                    "90-ft line, DC 22 DEX, 16d8 acid half",
                    0, "16d8", 0, "acid", range=90,
                    aoe_radius=90, aoe_shape="line",
                    condition_dc=22, condition_save="Dexterity"),
            Action("Slowing Breath",
                    "90-ft cone, DC 22 CON or speed halved & "
                    "1 attack/turn",
                    0, "", 0, "", range=90,
                    aoe_radius=90, aoe_shape="cone",
                    applies_condition="Slowed",
                    condition_dc=22, condition_save="Constitution"),
            Action("Tail Attack", "Legendary (1)", 15, "2d8+8", 0,
                    "bludgeoning", reach=20, action_type="legendary"),
            Action("Wing Attack",
                    "Legendary (2): 15-ft radius DC 23 DEX or "
                    "2d6+8 + Prone",
                    0, "2d6", 8, "bludgeoning",
                    action_type="legendary",
                    aoe_radius=15, aoe_shape="sphere",
                    condition_dc=23, condition_save="Dexterity",
                    applies_condition="Prone"),
        ],
        saving_throws={"Dexterity": 8, "Constitution": 14,
                         "Wisdom": 10, "Charisma": 11},
        damage_immunities=["acid"],
        features=[
            Feature("Legendary Resistance", "3/day",
                     "legendary_resist", uses_per_day=3),
            Feature("Frightful Presence",
                     "120-ft, DC 19 WIS or Frightened"),
            Feature("Acid Breath", "Recharge 5-6", recharge="5-6"),
            Feature("Slowing Breath", "Recharge 5-6", recharge="5-6"),
            Feature("Tail Attack", "Legendary 1",
                     feature_type="legendary", legendary_cost=1),
            Feature("Wing Attack", "Legendary 2",
                     feature_type="legendary", legendary_cost=2),
        ],
        legendary_action_count=3, legendary_resistance_count=3,
        challenge_rating=21.0, xp=33000, proficiency_bonus=7,
        lore=("Copper dragons are tricksters and lovers of riddles. "
              "Their hoards are pranks given form: cursed copper "
              "coins, joke magic items, riddle-locks. They respect "
              "those who can outwit them."),
        tactics=("Slowing Breath on melee threats, then kites with "
                  "Acid Breath. Uses cliffs and verticality — drops "
                  "rocks via Legendary Tail Attacks. Often laughs."),
        loot_table=("Treasure Hoard 17+. ~30% items are cursed or "
                     "prank items (Bag of Beans, Cloak of Poisonous-"
                     "ness disguised, etc.)."),
        habitat="Rocky hills, cliffs",
        sources="MM p.112"),

    # ------------------------------------------------------------------ #
    # CR 24 — Ancient Gold Dragon (MM p.115)                           #
    # ------------------------------------------------------------------ #
    CreatureStats(name="Ancient Gold Dragon", size="Gargantuan",
        creature_type="Dragon",
        armor_class=22, hit_points=546, hit_dice="28d20+252",
        speed=40, fly_speed=80, swim_speed=40,
        abilities=AbilityScores(strength=30, dexterity=14,
                                  constitution=29, intelligence=18,
                                  wisdom=17, charisma=28),
        actions=[
            Action("Multiattack", "Frightful Presence + Bite + 2 Claws",
                    0, "", 0, "", reach=15, is_multiattack=True,
                    multiattack_count=3,
                    multiattack_targets=["Bite","Claw","Claw"]),
            Action("Bite", "Melee", 17, "2d10+10", 0, "piercing",
                    reach=15),
            Action("Claw", "Melee", 17, "2d6+10", 0, "slashing",
                    reach=10),
            Action("Tail", "Melee", 17, "2d8+10", 0, "bludgeoning",
                    reach=20),
            Action("Fire Breath",
                    "90-ft cone, DC 24 DEX, 22d6 fire half",
                    0, "22d6", 0, "fire", range=90,
                    aoe_radius=90, aoe_shape="cone",
                    condition_dc=24, condition_save="Dexterity"),
            Action("Weakening Breath",
                    "90-ft cone, DC 24 STR or disadvantage on STR "
                    "checks, attacks & saves for 1 min",
                    0, "", 0, "", range=90,
                    aoe_radius=90, aoe_shape="cone",
                    condition_dc=24, condition_save="Strength"),
            Action("Tail Attack", "Legendary (1)", 17, "2d8+10", 0,
                    "bludgeoning", reach=20, action_type="legendary"),
            Action("Wing Attack",
                    "Legendary (2): 15-ft radius DC 25 DEX or "
                    "2d6+10 + Prone",
                    0, "2d6", 10, "bludgeoning",
                    action_type="legendary",
                    aoe_radius=15, aoe_shape="sphere",
                    condition_dc=25, condition_save="Dexterity",
                    applies_condition="Prone"),
        ],
        saving_throws={"Dexterity": 9, "Constitution": 16,
                         "Wisdom": 10, "Charisma": 16},
        damage_immunities=["fire"],
        features=[
            Feature("Legendary Resistance", "3/day",
                     "legendary_resist", uses_per_day=3),
            Feature("Amphibious", "Breathes air and water",
                     mechanic="amphibious"),
            Feature("Frightful Presence",
                     "120-ft, DC 24 WIS or Frightened"),
            Feature("Fire Breath", "Recharge 5-6", recharge="5-6"),
            Feature("Weakening Breath", "Recharge 5-6",
                     recharge="5-6"),
            Feature("Tail Attack", "Legendary 1",
                     feature_type="legendary", legendary_cost=1),
            Feature("Wing Attack", "Legendary 2",
                     feature_type="legendary", legendary_cost=2),
        ],
        legendary_action_count=3, legendary_resistance_count=3,
        challenge_rating=24.0, xp=62000, proficiency_bonus=7,
        lore=("Gold dragons are the king of the metallic dragons — "
              "wise, regal champions of order. They often live "
              "among the mortal nobility in shape-changed form, "
              "guiding kingdoms toward justice."),
        tactics=("Opens with Frightful Presence to lock the party "
                  "into Frightened. Weakening Breath on the heaviest "
                  "hitters. Fire Breath the back rank. Wing Attack "
                  "to reposition and force Prone saves."),
        loot_table=("Treasure Hoard 17+. Almost always a +2 weapon "
                     "or armor, royal regalia (3000+ gp), and "
                     "tomes/scrolls of high-level divine magic."),
        habitat="Royal courts, sky temples",
        sources="MM p.115"),

    # ------------------------------------------------------------------ #
    # CR 22 — Ancient Green Dragon (MM p.94)                           #
    # ------------------------------------------------------------------ #
    CreatureStats(name="Ancient Green Dragon", size="Gargantuan",
        creature_type="Dragon",
        armor_class=21, hit_points=385, hit_dice="22d20+154",
        speed=40, fly_speed=80, swim_speed=40,
        abilities=AbilityScores(strength=27, dexterity=12,
                                  constitution=25, intelligence=20,
                                  wisdom=17, charisma=19),
        actions=[
            Action("Multiattack", "Bite + 2 Claws",
                    0, "", 0, "", reach=15, is_multiattack=True,
                    multiattack_count=3,
                    multiattack_targets=["Bite","Claw","Claw"]),
            Action("Bite", "Melee", 15, "2d10+8", 0, "piercing",
                    reach=15),
            Action("Claw", "Melee", 15, "4d6+8", 0, "slashing",
                    reach=10),
            Action("Tail", "Melee", 15, "2d8+8", 0, "bludgeoning",
                    reach=20),
            Action("Poison Breath",
                    "90-ft cone, DC 22 CON, 22d6 poison half",
                    0, "22d6", 0, "poison", range=90,
                    aoe_radius=90, aoe_shape="cone",
                    condition_dc=22, condition_save="Constitution"),
            Action("Tail Attack", "Legendary (1)", 15, "2d8+8", 0,
                    "bludgeoning", reach=20, action_type="legendary"),
            Action("Wing Attack",
                    "Legendary (2): 15-ft radius DC 23 DEX or "
                    "2d6+8 + Prone",
                    0, "2d6", 8, "bludgeoning",
                    action_type="legendary",
                    aoe_radius=15, aoe_shape="sphere",
                    condition_dc=23, condition_save="Dexterity",
                    applies_condition="Prone"),
        ],
        saving_throws={"Dexterity": 8, "Constitution": 14,
                         "Wisdom": 10, "Charisma": 11},
        damage_immunities=["poison"],
        condition_immunities=["Poisoned"],
        features=[
            Feature("Legendary Resistance", "3/day",
                     "legendary_resist", uses_per_day=3),
            Feature("Amphibious", "Breathes air and water",
                     mechanic="amphibious"),
            Feature("Frightful Presence",
                     "120-ft, DC 19 WIS or Frightened"),
            Feature("Poison Breath", "Recharge 5-6", recharge="5-6"),
            Feature("Tail Attack", "Legendary 1",
                     feature_type="legendary", legendary_cost=1),
            Feature("Wing Attack", "Legendary 2",
                     feature_type="legendary", legendary_cost=2),
        ],
        legendary_action_count=3, legendary_resistance_count=3,
        challenge_rating=22.0, xp=41000, proficiency_bonus=7,
        lore=("Green dragons are deceitful manipulators who corrupt "
              "the forests they inhabit. They prefer to dominate "
              "lesser creatures into serving as informants and "
              "spies rather than fight openly."),
        tactics=("Avoids direct fights — manipulates other forest "
                  "creatures to weaken the party first. When "
                  "cornered, Poison Breath the cluster, then flies "
                  "while spamming Tail Attack legendaries."),
        loot_table=("Treasure Hoard 17+. Hoard often includes magical"
                     " items poisoned or cursed; bribes from "
                     "subordinate creatures."),
        habitat="Old-growth forests",
        sources="MM p.94"),

    # ------------------------------------------------------------------ #
    # CR 23 — Ancient Blue Dragon (MM p.91)                            #
    # ------------------------------------------------------------------ #
    CreatureStats(name="Ancient Blue Dragon", size="Gargantuan",
        creature_type="Dragon",
        armor_class=22, hit_points=481, hit_dice="26d20+208",
        speed=40, fly_speed=80, burrow_speed=40,
        abilities=AbilityScores(strength=29, dexterity=10,
                                  constitution=27, intelligence=18,
                                  wisdom=17, charisma=21),
        actions=[
            Action("Multiattack", "Bite + 2 Claws",
                    0, "", 0, "", reach=15, is_multiattack=True,
                    multiattack_count=3,
                    multiattack_targets=["Bite","Claw","Claw"]),
            Action("Bite", "Melee", 16, "2d10+9", 0, "piercing",
                    reach=15),
            Action("Claw", "Melee", 16, "4d6+9", 0, "slashing",
                    reach=10),
            Action("Tail", "Melee", 16, "2d8+9", 0, "bludgeoning",
                    reach=20),
            Action("Lightning Breath",
                    "120-ft line, DC 23 DEX, 16d10 lightning half",
                    0, "16d10", 0, "lightning", range=120,
                    aoe_radius=120, aoe_shape="line",
                    condition_dc=23, condition_save="Dexterity"),
            Action("Tail Attack", "Legendary (1)", 16, "2d8+9", 0,
                    "bludgeoning", reach=20, action_type="legendary"),
            Action("Wing Attack",
                    "Legendary (2): 15-ft radius DC 24 DEX or "
                    "2d6+9 + Prone",
                    0, "2d6", 9, "bludgeoning",
                    action_type="legendary",
                    aoe_radius=15, aoe_shape="sphere",
                    condition_dc=24, condition_save="Dexterity",
                    applies_condition="Prone"),
        ],
        saving_throws={"Dexterity": 7, "Constitution": 15,
                         "Wisdom": 10, "Charisma": 12},
        damage_immunities=["lightning"],
        features=[
            Feature("Legendary Resistance", "3/day",
                     "legendary_resist", uses_per_day=3),
            Feature("Frightful Presence",
                     "120-ft, DC 20 WIS or Frightened"),
            Feature("Lightning Breath", "Recharge 5-6",
                     recharge="5-6"),
            Feature("Tail Attack", "Legendary 1",
                     feature_type="legendary", legendary_cost=1),
            Feature("Wing Attack", "Legendary 2",
                     feature_type="legendary", legendary_cost=2),
        ],
        legendary_action_count=3, legendary_resistance_count=3,
        challenge_rating=23.0, xp=50000, proficiency_bonus=7,
        lore=("Blue dragons are vain, scheming desert tyrants. "
              "They surround themselves with smaller blue dragons "
              "and kobold cults, ruling miles of sand from "
              "buried-treasure thrones."),
        tactics=("Burrows underground to ambush. Lightning Breath "
                  "straight down a line at the party. Frightful "
                  "Presence to lock down spellcasters. Aerial "
                  "harassment with Tail Attacks."),
        loot_table=("Treasure Hoard 17+. Frequently magical desert "
                     "regalia, sand-buried artifacts, kobold-cult "
                     "offerings."),
        habitat="Sandy deserts, dunes",
        sources="MM p.91"),

    # ------------------------------------------------------------------ #
    # CR 23 — Ancient Silver Dragon (MM p.118)                         #
    # ------------------------------------------------------------------ #
    CreatureStats(name="Ancient Silver Dragon", size="Gargantuan",
        creature_type="Dragon",
        armor_class=22, hit_points=487, hit_dice="25d20+225",
        speed=40, fly_speed=80,
        abilities=AbilityScores(strength=30, dexterity=10,
                                  constitution=29, intelligence=18,
                                  wisdom=15, charisma=23),
        actions=[
            Action("Multiattack", "Bite + 2 Claws",
                    0, "", 0, "", reach=15, is_multiattack=True,
                    multiattack_count=3,
                    multiattack_targets=["Bite","Claw","Claw"]),
            Action("Bite", "Melee", 17, "2d10+10", 0, "piercing",
                    reach=15),
            Action("Claw", "Melee", 17, "2d6+10", 0, "slashing",
                    reach=10),
            Action("Tail", "Melee", 17, "2d8+10", 0, "bludgeoning",
                    reach=20),
            Action("Cold Breath",
                    "90-ft cone, DC 24 CON, 17d8 cold half",
                    0, "17d8", 0, "cold", range=90,
                    aoe_radius=90, aoe_shape="cone",
                    condition_dc=24, condition_save="Constitution"),
            Action("Paralyzing Breath",
                    "90-ft cone, DC 24 CON or Paralyzed 1 min",
                    0, "", 0, "", range=90,
                    aoe_radius=90, aoe_shape="cone",
                    applies_condition="Paralyzed",
                    condition_dc=24, condition_save="Constitution"),
            Action("Tail Attack", "Legendary (1)", 17, "2d8+10", 0,
                    "bludgeoning", reach=20, action_type="legendary"),
            Action("Wing Attack",
                    "Legendary (2): 15-ft radius DC 25 DEX or "
                    "2d6+10 + Prone",
                    0, "2d6", 10, "bludgeoning",
                    action_type="legendary",
                    aoe_radius=15, aoe_shape="sphere",
                    condition_dc=25, condition_save="Dexterity",
                    applies_condition="Prone"),
        ],
        saving_throws={"Dexterity": 7, "Constitution": 16,
                         "Wisdom": 9, "Charisma": 13},
        damage_immunities=["cold"],
        features=[
            Feature("Legendary Resistance", "3/day",
                     "legendary_resist", uses_per_day=3),
            Feature("Frightful Presence",
                     "120-ft, DC 21 WIS or Frightened"),
            Feature("Cold Breath", "Recharge 5-6", recharge="5-6"),
            Feature("Paralyzing Breath", "Recharge 5-6",
                     recharge="5-6"),
            Feature("Tail Attack", "Legendary 1",
                     feature_type="legendary", legendary_cost=1),
            Feature("Wing Attack", "Legendary 2",
                     feature_type="legendary", legendary_cost=2),
        ],
        legendary_action_count=3, legendary_resistance_count=3,
        challenge_rating=23.0, xp=50000, proficiency_bonus=7,
        lore=("Silver dragons love human society and often spend "
              "decades living among mortals in disguise. They are "
              "gentle but determined foes of evil."),
        tactics=("Paralyzing Breath the most dangerous PC and let "
                  "allies coup-de-grace them. Cold Breath the rest. "
                  "Holds Wing Attack for repositioning, not as a "
                  "damage tool."),
        loot_table=("Treasure Hoard 17+. Library of mortal "
                     "memorabilia: portraits, journals, magic items "
                     "befriended-mortals left behind."),
        habitat="Mountain peaks, cloud lairs",
        sources="MM p.118"),

    # ------------------------------------------------------------------ #
    # CR 23 — Empyrean (MM p.130) — titan, child of a deity            #
    # ------------------------------------------------------------------ #
    CreatureStats(name="Empyrean", size="Huge", creature_type="Celestial",
        armor_class=22, hit_points=313, hit_dice="19d12+190",
        speed=50, swim_speed=50,
        abilities=AbilityScores(strength=30, dexterity=21,
                                  constitution=30, intelligence=21,
                                  wisdom=22, charisma=27),
        actions=[
            Action("Multiattack", "x2 Maul or x2 Bolt",
                    0, "", 0, "", reach=10, is_multiattack=True,
                    multiattack_count=2,
                    multiattack_targets=["Maul","Maul"]),
            Action("Maul",
                    "Melee +17, 5d10+10 bludgeoning, target STR DC 24"
                    " or knocked Prone",
                    17, "5d10", 10, "bludgeoning", reach=10,
                    applies_condition="Prone",
                    condition_dc=24, condition_save="Strength"),
            Action("Bolt",
                    "Ranged +12, 10d6+5 lightning",
                    12, "10d6", 5, "lightning",
                    range=120, long_range=480),
            Action("Living Lightning",
                    "Legendary (3 cost): becomes a lightning bolt, "
                    "moves up to 120 ft, every creature in line DC "
                    "24 DEX or 10d6 lightning",
                    0, "10d6", 0, "lightning", range=120,
                    action_type="legendary",
                    aoe_radius=120, aoe_shape="line",
                    condition_dc=24, condition_save="Dexterity"),
            Action("Trembling Strike",
                    "Legendary (1 cost): Maul attack",
                    17, "5d10", 10, "bludgeoning",
                    reach=10, action_type="legendary"),
        ],
        saving_throws={"Strength": 17, "Wisdom": 13,
                         "Charisma": 15},
        skills={"Insight": 13, "Perception": 13},
        damage_resistances=[
            "bludgeoning piercing slashing (non-magic)"
        ],
        condition_immunities=["Charmed", "Frightened"],
        features=[
            Feature("Magic Weapons",
                     "Empyrean weapon attacks are magical.",
                     mechanic="magic_weapons"),
            Feature("Innate Spellcasting",
                     "At will: commune, dispel evil and good, "
                     "wind walk; 3/day: bestow curse, control "
                     "weather, insect plague; 1/day: earthquake."),
            Feature("Legendary Resistance", "3/day",
                     "legendary_resist", uses_per_day=3),
            Feature("Trembling Strike", "Legendary 1",
                     feature_type="legendary", legendary_cost=1),
            Feature("Living Lightning", "Legendary 3",
                     feature_type="legendary", legendary_cost=3),
        ],
        legendary_action_count=3, legendary_resistance_count=3,
        challenge_rating=23.0, xp=50000, proficiency_bonus=7,
        lore=("Empyreans are demigods — half-mortal children of "
              "the gods. A good one champions mortals against "
              "tyrants; a fallen one carves a kingdom of its own "
              "across continents."),
        tactics=("Opens at range with Bolt + Trembling Strike "
                  "legendary on the heavy hitter. When 3+ PCs "
                  "are aligned, becomes Living Lightning and "
                  "drives the line through them. Insect plague "
                  "to chase low-HP backline."),
        loot_table=("Cult-of-an-empyrean treasure hoard plus a "
                     "demigod's relic (a Tier-4 boon, an "
                     "artifact-tier weapon, or a strand of "
                     "Empyrean's hair worth 50,000 gp)."),
        habitat="Mount Olympus, Carceri (fallen)",
        sources="MM p.130"),

    # ------------------------------------------------------------------ #
    # CR 26 — Demogorgon (MM p.144) — Prince of Demons                 #
    # ------------------------------------------------------------------ #
    CreatureStats(name="Demogorgon", size="Huge", creature_type="Fiend",
        armor_class=22, hit_points=406, hit_dice="28d12+224",
        speed=50, swim_speed=50,
        abilities=AbilityScores(strength=29, dexterity=14,
                                  constitution=26, intelligence=20,
                                  wisdom=17, charisma=25),
        actions=[
            Action("Multiattack", "x2 Tentacle attacks",
                    0, "", 0, "", reach=10, is_multiattack=True,
                    multiattack_count=2,
                    multiattack_targets=["Tentacle","Tentacle"]),
            Action("Tentacle",
                    "Melee +14, 3d6+9 bludgeoning + 7d6 force, "
                    "target CON DC 23 or take 28 more force",
                    14, "3d6", 9, "bludgeoning", reach=10,
                    condition_dc=23, condition_save="Constitution"),
            Action("Gaze",
                    "Random target within 120 ft suffers one of: "
                    "Beguiling, Insanity, or Hypnotic. Save DC 19 "
                    "WIS / CHA / WIS respectively.",
                    0, "", 0, "psychic", range=120,
                    condition_dc=19, condition_save="Wisdom",
                    applies_condition="Frightened"),
            Action("Tentacle", "Legendary (1)", 14, "3d6+9",
                    0, "bludgeoning",
                    reach=10, action_type="legendary"),
            Action("Gaze", "Legendary (2)", 0, "", 0, "psychic",
                    range=120, action_type="legendary",
                    condition_dc=19, condition_save="Wisdom",
                    applies_condition="Frightened"),
        ],
        saving_throws={"Strength": 16, "Constitution": 15,
                         "Wisdom": 10, "Charisma": 14},
        damage_resistances=["cold", "fire", "lightning"],
        damage_immunities=[
            "poison",
            "bludgeoning piercing slashing (non-magic)",
        ],
        condition_immunities=["Charmed", "Exhaustion",
                                "Frightened", "Poisoned"],
        features=[
            Feature("Legendary Resistance", "3/day",
                     "legendary_resist", uses_per_day=3),
            Feature("Magic Resistance",
                     "Advantage on saves against spells and "
                     "magical effects."),
            Feature("Magic Weapons",
                     "Tentacle attacks are magical.",
                     mechanic="magic_weapons"),
            Feature("Two Heads",
                     "Advantage on saves against being Blinded, "
                     "Charmed, Deafened, Frightened, Stunned, "
                     "Unconscious."),
            Feature("Innate Spellcasting",
                     "At will: detect magic, major image; 3/day "
                     "each: fear, telekinesis; 1/day each: feeble"
                     "mind, project image."),
            Feature("Tentacle Strike", "Legendary 1",
                     feature_type="legendary", legendary_cost=1),
            Feature("Gaze", "Legendary 2",
                     feature_type="legendary", legendary_cost=2),
        ],
        legendary_action_count=3, legendary_resistance_count=3,
        challenge_rating=26.0, xp=90000, proficiency_bonus=8,
        lore=("Prince of Demons. The Sibilant Beast. Two heads, "
              "two minds locked in eternal hatred of each other "
              "and of all creation. Even other demon lords fear "
              "Demogorgon's madness-inducing gaze."),
        tactics=("Opens with Gaze on the highest-CHA save target "
                  "(spread the insanity). Tentacles the front-line "
                  "for raw damage. Gaze Legendary between turns to "
                  "keep multiple PCs insane simultaneously."),
        loot_table=("Demon-lord scale (artifact tier). Ichor of "
                     "Demogorgon (25,000 gp per vial, used in "
                     "abyssal rituals). Plus normal abyssal hoard."),
        habitat="Abyss, Layer 88 — the Gaping Maw",
        sources="MM p.144"),

    # ------------------------------------------------------------------ #
    # CR 26 — Orcus (MM p.151) — Prince of Undeath                     #
    # ------------------------------------------------------------------ #
    CreatureStats(name="Orcus", size="Large", creature_type="Fiend",
        armor_class=17, hit_points=405, hit_dice="30d10+240",
        speed=40, fly_speed=60,
        abilities=AbilityScores(strength=27, dexterity=14,
                                  constitution=27, intelligence=20,
                                  wisdom=19, charisma=25),
        actions=[
            Action("Multiattack", "x3: Wand of Orcus or x2 Tail",
                    0, "", 0, "", reach=10, is_multiattack=True,
                    multiattack_count=3,
                    multiattack_targets=["Wand of Orcus",
                                          "Wand of Orcus",
                                          "Wand of Orcus"]),
            Action("Wand of Orcus",
                    "Melee +14, 3d12+8 bludgeoning + 4d12 necrotic",
                    14, "3d12", 8, "bludgeoning", reach=10),
            Action("Tail",
                    "Melee +14, 3d6+8 piercing, target CON DC 22 "
                    "or 4d6 necrotic and max HP reduced",
                    14, "3d6", 8, "piercing", reach=10,
                    condition_dc=22, condition_save="Constitution"),
            Action("Animate Dead",
                    "1/day: animate up to 15 ghouls or 7 wights "
                    "from corpses within 60 ft.",
                    0, "", 0, "", range=60),
            Action("Necrotic Bolt",
                    "Ranged +14, 3d10 necrotic; target dies on 0 HP"
                    " and rises as zombie under Orcus's control",
                    14, "3d10", 0, "necrotic", range=120),
            Action("Wand Attack", "Legendary (1)",
                    14, "3d12", 8, "bludgeoning",
                    reach=10, action_type="legendary"),
            Action("Charge", "Legendary (2): fly 30 ft and Wand",
                    14, "3d12", 8, "bludgeoning",
                    reach=10, action_type="legendary"),
        ],
        saving_throws={"Constitution": 16, "Wisdom": 12,
                         "Charisma": 15},
        damage_resistances=["cold", "fire", "lightning"],
        damage_immunities=[
            "necrotic", "poison",
            "bludgeoning piercing slashing (non-magic)",
        ],
        condition_immunities=["Charmed", "Exhaustion",
                                "Frightened", "Poisoned"],
        features=[
            Feature("Legendary Resistance", "3/day",
                     "legendary_resist", uses_per_day=3),
            Feature("Magic Resistance",
                     "Advantage on saves against spells."),
            Feature("Master of Undeath",
                     "Adv on saves to maintain control of undead. "
                     "Undead within 100 ft can't be turned."),
            Feature("Innate Spellcasting",
                     "At will: detect magic; 3/day each: animate "
                     "dead, blight, circle of death."),
            Feature("Wand Attack", "Legendary 1",
                     feature_type="legendary", legendary_cost=1),
            Feature("Charge", "Legendary 2",
                     feature_type="legendary", legendary_cost=2),
        ],
        legendary_action_count=3, legendary_resistance_count=3,
        challenge_rating=26.0, xp=90000, proficiency_bonus=8,
        lore=("Prince of Undeath. The Blood Lord. Demon lord of "
              "death and the undead, wielder of the dreaded Wand "
              "of Orcus — a skull-tipped artifact that slays the "
              "living with a touch and animates them as servants."),
        tactics=("Animate Dead on round 1 — turn fallen NPCs against "
                  "the party. Necrotic Bolt the squishies. Wand "
                  "Multiattack on the tank, with Charge Legendary "
                  "to gap-close between turns. Saves LR for "
                  "Banishment / Polymorph specifically."),
        loot_table=("Wand of Orcus (artifact, 50,000+ gp). Skull-"
                     "throne fragments. Undead-lord boons (Lichdom "
                     "ritual scrolls)."),
        habitat="Abyss, Thanatos (Layer 113)",
        sources="MM p.151"),
]
