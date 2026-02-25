from data.models import CreatureStats, AbilityScores, Action, Feature

monsters = [
    # ------------------------------------------------------------------ #
    # CR 11 – Behir                                                       #
    # ------------------------------------------------------------------ #
    CreatureStats(name="Behir", size="Huge", creature_type="Monstrosity",
        armor_class=17, hit_points=168, hit_dice="16d12+64", speed=50, climb_speed=40,
        abilities=AbilityScores(strength=23,dexterity=16,constitution=18,intelligence=7,wisdom=14,charisma=12),
        actions=[
            Action("Multiattack","Bite + Constrict",0,"",0,"",range=5,is_multiattack=True,
                   multiattack_count=2,multiattack_targets=["Bite","Constrict"]),
            Action("Bite","Melee",10,"3d10",6,"piercing"),
            Action("Constrict","Melee",10,"2d10+6","bludgeoning",
                   applies_condition="Grappled",condition_dc=16,condition_save="Strength"),
            Action("Lightning Breath","20ft line DC 16 DEX half",0,"12d10",0,"lightning",
                   range=20,aoe_radius=20,aoe_shape="line",condition_dc=16,condition_save="Dexterity"),
        ],
        damage_immunities=["lightning"],
        features=[
            Feature("Lightning Breath","Recharge 5-6: 20ft line 12d10 lightning DC 16 DEX half",recharge="5-6"),
            Feature("Swallow","On bite hit vs grappled Medium or smaller, target is swallowed: blinded, restrained, 6d6 acid/turn"),
        ],
        challenge_rating=11.0, xp=7200, proficiency_bonus=4),

    # ------------------------------------------------------------------ #
    # CR 11 – Remorhaz                                                    #
    # ------------------------------------------------------------------ #
    CreatureStats(name="Remorhaz", size="Huge", creature_type="Monstrosity",
        armor_class=17, hit_points=195, hit_dice="17d12+85", speed=30, burrow_speed=20,
        abilities=AbilityScores(strength=24,dexterity=13,constitution=21,intelligence=4,wisdom=10,charisma=5),
        actions=[
            Action("Bite","Melee",11,"6d10",7,"piercing"),
        ],
        damage_immunities=["cold","fire"],
        features=[
            Feature("Heated Body","Creature that touches or hits with melee within 5ft takes 3d6 fire",
                    damage_dice="3d6",damage_type="fire"),
            Feature("Swallow","On bite hit, can swallow Medium or smaller grappled target: blinded, restrained, 6d6 acid/turn"),
        ],
        challenge_rating=11.0, xp=7200, proficiency_bonus=4),

    # ------------------------------------------------------------------ #
    # CR 11 – Efreeti                                                     #
    # ------------------------------------------------------------------ #
    CreatureStats(name="Efreeti", size="Large", creature_type="Elemental",
        armor_class=17, hit_points=200, hit_dice="16d10+112", speed=40, fly_speed=60,
        abilities=AbilityScores(strength=22,dexterity=12,constitution=24,intelligence=16,wisdom=15,charisma=16),
        actions=[
            Action("Multiattack","x2 Scimitar",0,"",0,"",range=5,is_multiattack=True,
                   multiattack_count=2,multiattack_targets=["Scimitar","Scimitar"]),
            Action("Scimitar","Melee",10,"2d6",6,"slashing"),
            Action("Hurl Flame","Ranged",7,"5d6",0,"fire",range=120),
        ],
        damage_immunities=["fire"],
        features=[
            Feature("Innate Spellcasting","DC 15. At will: Detect Magic. 3/day each: Conjure Elemental (fire only), Invisibility, Major Image, Gaseous Form. 1/day each: Plane Shift, Wall of Fire"),
        ],
        challenge_rating=11.0, xp=7200, proficiency_bonus=4),

    # ------------------------------------------------------------------ #
    # CR 11 – Horned Devil (Cornugon)                                     #
    # ------------------------------------------------------------------ #
    CreatureStats(name="Horned Devil", size="Large", creature_type="Fiend",
        armor_class=18, hit_points=178, hit_dice="17d10+85", speed=20, fly_speed=60,
        abilities=AbilityScores(strength=22,dexterity=17,constitution=21,intelligence=12,wisdom=16,charisma=17),
        actions=[
            Action("Multiattack","Fork + Tail",0,"",0,"",range=5,is_multiattack=True,
                   multiattack_count=2,multiattack_targets=["Fork","Tail"]),
            Action("Fork","Melee",10,"2d8",6,"piercing",reach=10),
            Action("Tail","Melee",10,"1d8",6,"piercing",
                   applies_condition="Infernal Wound",condition_dc=17,condition_save="Constitution"),
            Action("Hurl Flame","Ranged",7,"4d6",0,"fire",range=150),
        ],
        damage_resistances=["cold","bludgeoning piercing slashing (non-magic)"],
        damage_immunities=["fire","poison"],
        condition_immunities=["Poisoned"],
        features=[
            Feature("Devil's Sight","Magical darkness doesn't impede darkvision"),
            Feature("Magic Resistance","Adv on saves vs spells"),
            Feature("Infernal Wound","Tail hit: DC 17 CON or 3d6 bleed damage at start of each turn until healed"),
        ],
        challenge_rating=11.0, xp=7200, proficiency_bonus=4),

    # ------------------------------------------------------------------ #
    # CR 12 – Archmage                                                    #
    # ------------------------------------------------------------------ #
    CreatureStats(name="Archmage", size="Medium", creature_type="Humanoid",
        armor_class=12, hit_points=99, hit_dice="18d8+18", speed=30,
        abilities=AbilityScores(strength=10,dexterity=14,constitution=12,intelligence=20,wisdom=15,charisma=16),
        actions=[
            Action("Dagger","Melee",6,"1d4",2,"piercing"),
        ],
        spellcasting_ability="Intelligence", spell_save_dc=17, spell_attack_bonus=9,
        damage_resistances=["damage from spells"],
        features=[
            Feature("Magic Resistance","Adv on saves vs spells"),
            Feature("Spellcasting","INT DC 17 +9 attack. Cantrips: Fire Bolt. 1st: Mage Armor, Shield, Misty Step. 3rd: Counterspell, Fireball, Lightning Bolt. 4th: Banishment. 5th: Cone of Cold, Wall of Force. 9th: Time Stop, Meteor Swarm"),
        ],
        challenge_rating=12.0, xp=8400, proficiency_bonus=4),

    # ------------------------------------------------------------------ #
    # CR 14 – Adult Copper Dragon                                         #
    # ------------------------------------------------------------------ #
    CreatureStats(name="Adult Copper Dragon", size="Huge", creature_type="Dragon",
        armor_class=18, hit_points=184, hit_dice="16d12+80", speed=40, climb_speed=40, fly_speed=80,
        abilities=AbilityScores(strength=23,dexterity=12,constitution=21,intelligence=18,wisdom=15,charisma=17),
        actions=[
            Action("Multiattack","Bite + 2 Claws",0,"",0,"",reach=10,is_multiattack=True,
                   multiattack_count=3,multiattack_targets=["Bite","Claw","Claw"]),
            Action("Bite","Melee",11,"2d10",6,"piercing",reach=10),
            Action("Claw","Melee",11,"2d6",6,"slashing"),
            Action("Tail","Melee",11,"2d8",6,"bludgeoning",reach=15),
            Action("Acid Breath","60ft line DC 18 DEX half",0,"12d8",0,"acid",
                   range=60,aoe_radius=60,aoe_shape="line",condition_dc=18,condition_save="Dexterity"),
            Action("Slowing Breath","60ft cone DC 18 CON or speed halved 1 min",0,"",0,"",
                   range=60,aoe_radius=60,aoe_shape="cone",condition_dc=18,condition_save="Constitution",
                   applies_condition="Slowed"),
        ],
        damage_immunities=["acid"],
        features=[
            Feature("Legendary Resistance","3/day auto-succeed on failed save","legendary_resist",uses_per_day=3),
            Feature("Acid Breath","Recharge 5-6: 60ft line 12d8 acid DC 18 DEX half",recharge="5-6"),
            Feature("Slowing Breath","60ft cone DC 18 CON or speed halved 1 min"),
            Feature("Frightful Presence","120ft DC 16 WIS or Frightened 1 min"),
        ],
        legendary_action_count=3,
        legendary_resistance_count=3,
        challenge_rating=14.0, xp=11500, proficiency_bonus=5),

    # ------------------------------------------------------------------ #
    # CR 15 – Purple Worm                                                 #
    # ------------------------------------------------------------------ #
    CreatureStats(name="Purple Worm", size="Gargantuan", creature_type="Monstrosity",
        armor_class=18, hit_points=247, hit_dice="15d20+90", speed=50, burrow_speed=30,
        abilities=AbilityScores(strength=28,dexterity=7,constitution=22,intelligence=1,wisdom=8,charisma=4),
        actions=[
            Action("Multiattack","Bite + Tail Stinger",0,"",0,"",range=10,is_multiattack=True,
                   multiattack_count=2,multiattack_targets=["Bite","Tail Stinger"]),
            Action("Bite","Melee",14,"3d8",9,"piercing",reach=10,
                   applies_condition="Swallowed",condition_dc=19,condition_save="Dexterity"),
            Action("Tail Stinger","Melee",14,"3d6",9,"piercing",reach=10),
        ],
        features=[
            Feature("Tunneler","Can burrow through solid rock at half burrow speed, leaving 10ft tunnel"),
            Feature("Swallow","On bite hit DC 19 DEX or swallowed: blinded, restrained, 6d6 acid/turn"),
            Feature("Tail Stinger Poison","Tail hit deals extra 12d6 poison, DC 19 CON half"),
        ],
        challenge_rating=15.0, xp=13000, proficiency_bonus=5),
]
