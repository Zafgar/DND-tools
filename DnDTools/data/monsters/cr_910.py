from data.models import CreatureStats, AbilityScores, Action, Feature, SpellInfo
from data.spells import get_spell

monsters = [
    # ------------------------------------------------------------------ #
    # CR 9 – Bone Devil (Osyluth)                                        #
    # ------------------------------------------------------------------ #
    CreatureStats(name="Bone Devil", size="Large", creature_type="Fiend",
        armor_class=19, hit_points=142, hit_dice="15d10+60", speed=40, fly_speed=40,
        native_plane="Nine Hells",
        abilities=AbilityScores(strength=18,dexterity=16,constitution=18,intelligence=13,wisdom=14,charisma=16),
        actions=[
            Action("Multiattack","Claw + Sting",0,"",0,"",range=5,is_multiattack=True,
                   multiattack_count=2,multiattack_targets=["Claw","Sting"]),
            Action("Claw","Melee",8,"1d8",4,"slashing"),
            Action("Sting","Melee",8,"2d8",4,"piercing",
                   applies_condition="Poisoned",condition_dc=14,condition_save="Constitution"),
        ],
        saving_throws={"Intelligence":5,"Wisdom":6,"Charisma":7},
        damage_resistances=["cold","bludgeoning piercing slashing (non-magic)"],
        damage_immunities=["fire","poison"],
        condition_immunities=["Poisoned"],
        features=[
            Feature("Devil's Sight","Magical darkness doesn't impede darkvision"),
            Feature("Magic Resistance","Adv on saves vs spells"),
        ],
        challenge_rating=9.0, xp=5000, proficiency_bonus=4),

    # ------------------------------------------------------------------ #
    # CR 9 – Clay Golem                                                  #
    # ------------------------------------------------------------------ #
    CreatureStats(name="Clay Golem", size="Large", creature_type="Construct",
        armor_class=14, hit_points=133, hit_dice="14d10+56", speed=20,
        abilities=AbilityScores(strength=20,dexterity=9,constitution=18,intelligence=3,wisdom=8,charisma=1),
        actions=[
            Action("Multiattack","x2 Slam",0,"",0,"",range=5,is_multiattack=True,
                   multiattack_count=2,multiattack_targets=["Slam","Slam"]),
            Action("Slam","Melee",8,"2d10",5,"bludgeoning"),
            Action("Haste","Recharge 5-6: +2 slam attacks",8,"2d10",5,"bludgeoning",
                   is_multiattack=True,multiattack_count=2,multiattack_targets=["Slam","Slam"]),
        ],
        damage_immunities=["acid","poison","psychic","bludgeoning piercing slashing (non-magic non-adamantine)"],
        condition_immunities=["Charmed","Exhaustion","Frightened","Paralyzed","Petrified","Poisoned"],
        features=[
            Feature("Haste","Recharge 5-6: Until end of next turn, +2 bonus slam attacks",recharge="5-6"),
            Feature("Immutable Form","Immune to any spell/effect that would alter its form"),
            Feature("Acid Absorption","Whenever subjected to acid damage, takes no damage and regains HP equal to acid damage dealt"),
            Feature("Magic Resistance","Adv on saves vs spells"),
            Feature("Magic Weapons","Weapon attacks are magical",mechanic="magic_weapons"),
        ],
        challenge_rating=9.0, xp=5000, proficiency_bonus=4),

    # ------------------------------------------------------------------ #
    # CR 9 – Treant                                                      #
    # ------------------------------------------------------------------ #
    CreatureStats(name="Treant", size="Huge", creature_type="Plant",
        armor_class=16, hit_points=138, hit_dice="12d12+60", speed=30,
        abilities=AbilityScores(strength=23,dexterity=8,constitution=21,intelligence=12,wisdom=16,charisma=12),
        actions=[
            Action("Multiattack","x2 Slam",0,"",0,"",range=5,is_multiattack=True,
                   multiattack_count=2,multiattack_targets=["Slam","Slam"]),
            Action("Slam","Melee",10,"3d6",6,"bludgeoning",reach=10),
            Action("Rock","Ranged",10,"4d10",6,"bludgeoning",range=60),
        ],
        damage_resistances=["bludgeoning","piercing"],
        damage_vulnerabilities=["fire"],
        features=[
            Feature("False Appearance","While motionless, indistinguishable from normal tree"),
            Feature("Siege Monster","Double damage to objects and structures"),
        ],
        challenge_rating=9.0, xp=5000, proficiency_bonus=4),

    # ------------------------------------------------------------------ #
    # CR 10 – Aboleth (with Lair Actions)                                #
    # ------------------------------------------------------------------ #
    CreatureStats(name="Aboleth", size="Large", creature_type="Aberration",
        armor_class=17, hit_points=135, hit_dice="18d10+36", speed=10, swim_speed=40,
        abilities=AbilityScores(strength=21,dexterity=9,constitution=15,intelligence=18,wisdom=15,charisma=18),
        actions=[
            Action("Multiattack","x3 Tentacle",0,"",0,"",range=5,is_multiattack=True,
                   multiattack_count=3,multiattack_targets=["Tentacle","Tentacle","Tentacle"]),
            Action("Tentacle","Melee",9,"2d6",5,"bludgeoning",reach=10),
            Action("Tail","Melee",9,"3d6",5,"bludgeoning",reach=10),
            Action("Enslave","60ft DC 14 WIS or Charmed. Charmed creature obeys telepathic commands.",
                   0,"",0,"",range=60,applies_condition="Charmed",
                   condition_dc=14,condition_save="Wisdom"),
            # Lair Actions
            Action("Phantasmal Force","Lair: DC 14 WIS or Frightened until next lair action",
                   0,"",0,"psychic",range=120,action_type="lair",
                   applies_condition="Frightened",condition_dc=14,condition_save="Wisdom"),
            Action("Psychic Drain","Lair: 20ft radius DC 14 INT or 2d6 psychic",
                   0,"2d6",0,"psychic",range=90,action_type="lair",
                   aoe_radius=20,aoe_shape="sphere",condition_dc=14,condition_save="Intelligence"),
            Action("Slimy Pool","Lair: 10ft radius water becomes slime, DC 14 CON or Poisoned",
                   0,"",0,"",range=90,action_type="lair",aoe_radius=10,aoe_shape="sphere",
                   applies_condition="Poisoned",condition_dc=14,condition_save="Constitution"),
            # Legendary Actions
            Action("Detect","Aboleth makes a Wisdom (Perception) check.",0,"",0,"",
                   range=0,action_type="legendary"),
            Action("Tail Swipe","Melee",9,"3d6+5","bludgeoning",reach=10,action_type="legendary"),
            Action("Psychic Drain","One creature DC 14 INT or 3d6 psychic",0,"3d6",0,"psychic",
                   range=60,action_type="legendary",condition_dc=14,condition_save="Intelligence"),
        ],
        saving_throws={"Constitution":6,"Intelligence":8,"Wisdom":6},
        skills={"History":12,"Perception":10},
        senses="darkvision 120 ft.",
        features=[
            Feature("Amphibious","Can breathe air and water"),
            Feature("Mucous Cloud","Creature that touches aboleth or hits with melee within 5ft must "
                    "DC 14 CON or be diseased for 1d4 hours",
                    damage_type="poison",save_dc=14,save_ability="Constitution"),
            Feature("Probing Telepathy","120ft telepathy, knows creature's greatest desires"),
            Feature("Legendary Resistance","3/day auto-succeed on failed save","legendary_resist",uses_per_day=3),
            Feature("Detect","Legendary Action (1 cost)",feature_type="legendary",legendary_cost=1),
            Feature("Tail Swipe","Legendary Action (1 cost)",feature_type="legendary",legendary_cost=1),
            Feature("Psychic Drain","Legendary Action (2 cost)",feature_type="legendary",legendary_cost=2),
        ],
        legendary_action_count=3,
        legendary_resistance_count=3,
        challenge_rating=10.0, xp=5900, proficiency_bonus=4),

    # ------------------------------------------------------------------ #
    # CR 10 – Young Red Dragon (with Lair Actions)                       #
    # ------------------------------------------------------------------ #
    CreatureStats(name="Young Red Dragon", size="Large", creature_type="Dragon",
        armor_class=18, hit_points=178, hit_dice="17d10+85", speed=40, climb_speed=40, fly_speed=80,
        abilities=AbilityScores(strength=23,dexterity=10,constitution=21,intelligence=14,wisdom=11,charisma=19),
        actions=[
            Action("Multiattack","Bite + 2 Claws",0,"",0,"",reach=10,is_multiattack=True,
                   multiattack_count=3,multiattack_targets=["Bite","Claw","Claw"]),
            Action("Bite","Melee",10,"2d10",6,"piercing",reach=10),
            Action("Claw","Melee",10,"2d6",6,"slashing"),
            Action("Fire Breath","30ft cone DC 17 DEX half",0,"16d6",0,"fire",range=30,
                   aoe_radius=30,aoe_shape="cone",condition_dc=17,condition_save="Dexterity"),
            # Lair Actions
            Action("Volcanic Vent","Lair: 10ft radius eruption",0,"3d6",0,"fire",range=120,
                   action_type="lair",aoe_radius=10,aoe_shape="sphere",
                   condition_dc=15,condition_save="Dexterity"),
            Action("Tremor","Lair: 20ft radius DC 15 DEX or Prone",0,"",0,"",range=120,
                   action_type="lair",aoe_radius=20,aoe_shape="sphere",
                   applies_condition="Prone",condition_dc=15,condition_save="Dexterity"),
        ],
        saving_throws={"Dexterity":4,"Constitution":9,"Wisdom":4,"Charisma":8},
        skills={"Perception":8,"Stealth":4},
        damage_immunities=["fire"],
        features=[
            Feature("Fire Breath","Recharge 5-6: 30ft cone 16d6 fire DC 17 DEX half",recharge="5-6"),
        ],
        challenge_rating=10.0, xp=5900, proficiency_bonus=4),

    # ------------------------------------------------------------------ #
    # CR 10 – Guardian Naga (with Spellcasting)                          #
    # ------------------------------------------------------------------ #
    CreatureStats(name="Guardian Naga", size="Large", creature_type="Monstrosity",
        armor_class=18, hit_points=127, hit_dice="15d10+45", speed=40,
        abilities=AbilityScores(strength=19,dexterity=18,constitution=16,intelligence=16,wisdom=19,charisma=18),
        actions=[
            Action("Bite","Melee",8,"1d8",4,"piercing",
                   applies_condition="Poisoned",condition_dc=15,condition_save="Constitution"),
            Action("Spit Poison","Ranged 15ft: DC 15 CON or 10d8 poison",0,"10d8",0,"poison",
                   range=15,condition_dc=15,condition_save="Constitution"),
        ],
        saving_throws={"Dexterity":8,"Constitution":7,"Intelligence":7,"Wisdom":8,"Charisma":8},
        damage_immunities=["poison"],
        condition_immunities=["Charmed","Poisoned"],
        spellcasting_ability="Wisdom", spell_save_dc=16, spell_attack_bonus=8,
        spell_slots={"1st":4,"2nd":3,"3rd":3,"4th":3,"5th":2,"6th":1},
        spells_known=[
            get_spell("Cure Wounds"),
            get_spell("Shield of Faith"),
            get_spell("Hold Person"),
            get_spell("Flame Strike"),
            get_spell("Banishment"),
            get_spell("Bless"),
        ],
        cantrips=[
            get_spell("Sacred Flame"),
        ],
        features=[
            Feature("Rejuvenation","If killed, returns to life in 1d6 days with all HP"),
        ],
        challenge_rating=10.0, xp=5900, proficiency_bonus=4),

    # ------------------------------------------------------------------ #
    # CR 10 – Stone Golem                                                #
    # ------------------------------------------------------------------ #
    CreatureStats(name="Stone Golem", size="Large", creature_type="Construct",
        armor_class=17, hit_points=178, hit_dice="17d10+85", speed=30,
        abilities=AbilityScores(strength=22,dexterity=9,constitution=20,intelligence=3,wisdom=11,charisma=1),
        actions=[
            Action("Multiattack","x2 Slam",0,"",0,"",range=5,is_multiattack=True,
                   multiattack_count=2,multiattack_targets=["Slam","Slam"]),
            Action("Slam","Melee",10,"3d8",6,"bludgeoning"),
            Action("Slow","10ft radius DC 17 WIS or Slowed for 1 minute",0,"",0,"",range=0,
                   aoe_radius=10,aoe_shape="sphere",applies_condition="Slowed",
                   condition_dc=17,condition_save="Wisdom"),
        ],
        damage_immunities=["poison","psychic","bludgeoning piercing slashing (non-magic non-adamantine)"],
        condition_immunities=["Charmed","Exhaustion","Frightened","Paralyzed","Petrified","Poisoned"],
        features=[
            Feature("Slow","Recharge 5-6: 10ft DC 17 WIS or speed halved, -2 AC, no reactions, "
                    "only 1 attack per turn, can't use bonus action",recharge="5-6"),
            Feature("Immutable Form","Immune to any spell/effect that would alter its form"),
            Feature("Magic Resistance","Adv on saves vs spells"),
            Feature("Magic Weapons","Weapon attacks are magical",mechanic="magic_weapons"),
        ],
        challenge_rating=10.0, xp=5900, proficiency_bonus=4),

    # ------------------------------------------------------------------ #
    # CR 10 – Deva (Angel)                                               #
    # ------------------------------------------------------------------ #
    CreatureStats(name="Deva", size="Medium", creature_type="Celestial",
        armor_class=17, hit_points=136, hit_dice="16d8+64", speed=30, fly_speed=90,
        abilities=AbilityScores(strength=18,dexterity=18,constitution=18,intelligence=17,wisdom=20,charisma=20),
        actions=[
            Action("Multiattack","x2 Mace",0,"",0,"",range=5,is_multiattack=True,
                   multiattack_count=2,multiattack_targets=["Mace","Mace"]),
            Action("Mace","Melee",8,"1d6+4","bludgeoning"),
        ],
        saving_throws={"Wisdom":9,"Charisma":9},
        skills={"Insight":9,"Perception":9},
        damage_resistances=["radiant","bludgeoning piercing slashing (non-magic)"],
        condition_immunities=["Charmed","Exhaustion","Frightened"],
        spellcasting_ability="Charisma", spell_save_dc=17, spell_attack_bonus=9,
        spell_slots={"1st":4,"2nd":3,"3rd":3,"4th":1},
        spells_known=[
            get_spell("Cure Wounds"),
            get_spell("Lesser Restoration"),
            get_spell("Dispel Magic"),
            get_spell("Flame Strike"),
        ],
        features=[
            Feature("Angelic Weapons","Weapon attacks deal extra 4d8 radiant damage (included in Mace)"),
            Feature("Magic Resistance","Adv on saves vs spells"),
            Feature("Magic Weapons","Weapon attacks are magical",mechanic="magic_weapons"),
            Feature("Healing Touch","3/day: touch to heal 20 HP and remove conditions",uses_per_day=3),
        ],
        challenge_rating=10.0, xp=5900, proficiency_bonus=4),
]
