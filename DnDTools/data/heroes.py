from data.models import CreatureStats, AbilityScores, Action, Feature, SpellInfo, Item
from data.spells import get_spell

# Pre-built heroes for quick setup. DM can customize HP/AC manually.
hero_list = [
    # ---- FIGHTER (lvl 10) ----
    CreatureStats(
        name="Veteran Fighter",
        hit_points=94, armor_class=18, speed=30, hit_dice="10d10+30",
        abilities=AbilityScores(strength=18,dexterity=14,constitution=16,intelligence=10,wisdom=12,charisma=10),
        actions=[
            Action("Multiattack","3 attacks (Action Surge: 4)",0,"",0,"",range=5,is_multiattack=True,
                   multiattack_count=3,multiattack_targets=["Longsword","Longsword","Longsword"]),
            Action("Longsword","Melee",8,"1d8",4,"slashing"),
            Action("Shield Bash","Melee",8,"1d4",4,"bludgeoning",applies_condition="Prone",condition_dc=16,condition_save="Strength"),
        ],
        features=[
            Feature("Action Surge","Extra action 1/rest",uses_per_day=1),
            Feature("Second Wind","Bonus heal 1d10+10",uses_per_day=1),
            Feature("Indomitable","Re-roll failed save 2/day",uses_per_day=2),
        ],
        saving_throws={"Strength":8,"Constitution":7},
        skills={"Athletics":8,"Intimidation":4,"Perception":5},
        challenge_rating=5.0, proficiency_bonus=4,
    ),

    # ---- PALADIN (lvl 10) ----
    CreatureStats(
        name="Holy Paladin",
        hit_points=85, armor_class=20, speed=30, hit_dice="10d10+20",
        abilities=AbilityScores(strength=18,dexterity=10,constitution=14,intelligence=10,wisdom=12,charisma=18),
        actions=[
            Action("Multiattack","2 attacks",0,"",0,"",range=5,is_multiattack=True,
                   multiattack_count=2,multiattack_targets=["Longsword","Longsword"]),
            Action("Longsword","Melee",8,"1d8",4,"slashing"),
            Action("Divine Smite","Add 2d8 radiant on hit (uses slot)",8,"1d8+4","slashing"),
        ],
        bonus_actions=[
            Action("Lay on Hands (5HP)",description="Restore 5 HP",action_type="bonus", damage_dice=""),
        ],
        spellcasting_ability="Charisma", spell_save_dc=16, spell_attack_bonus=8,
        spell_slots={"1st":4,"2nd":3,"3rd":2},
        spells_known=[
            get_spell("Bless"),
            get_spell("Divine Favor"),
            get_spell("Shield of Faith"),
            get_spell("Cure Wounds"),
            get_spell("Revivify"),
        ],
        features=[
            Feature("Aura of Protection","Allies within 10ft add +4 to saves"),
            Feature("Aura of Courage","Allies within 10ft immune to Frightened"),
            Feature("Divine Smite","Expend spell slot for +2d8 radiant per level on hit"),
            Feature("Lay on Hands","HP pool: 50 HP to heal as action",uses_per_day=1),
        ],
        saving_throws={"Wisdom":8,"Charisma":8},
        skills={"Athletics":8,"Insight":5,"Persuasion":8},
        challenge_rating=5.0, proficiency_bonus=4,
    ),

    # ---- WIZARD (lvl 10) ----
    CreatureStats(
        name="Arcane Wizard",
        hit_points=52, armor_class=13, speed=30, hit_dice="10d6+10",
        abilities=AbilityScores(strength=8,dexterity=16,constitution=12,intelligence=20,wisdom=14,charisma=10),
        actions=[
            Action("Quarterstaff","Melee",3,"1d6-1","bludgeoning"),
        ],
        spellcasting_ability="Intelligence", spell_save_dc=17, spell_attack_bonus=9,
        spell_slots={"1st":4,"2nd":3,"3rd":3,"4th":3,"5th":2},
        spells_known=[
            get_spell("Fireball"),
            get_spell("Cone of Cold"),
            get_spell("Hold Person"),
            get_spell("Lightning Bolt"),
            get_spell("Magic Missile"),
            get_spell("Shield"),
            get_spell("Counterspell"),
            get_spell("Misty Step"),
            get_spell("Banishment"),
            get_spell("Wall of Fire"),
        ],
        cantrips=[
            get_spell("Fire Bolt", attack_bonus_fixed=9),
            get_spell("Chill Touch", attack_bonus_fixed=9),
            get_spell("Ray of Frost", attack_bonus_fixed=9),
            get_spell("Shocking Grasp", attack_bonus_fixed=9),
        ],
        features=[
            Feature("Arcane Recovery","Short rest: recover 5 levels of spell slots",uses_per_day=1),
            Feature("Spell Mastery","Can cast 2 chosen spells at will"),
        ],
        saving_throws={"Intelligence":9,"Wisdom":6},
        skills={"Arcana":13,"History":9,"Investigation":9},
        challenge_rating=5.0, proficiency_bonus=4,
    ),

    # ---- CLERIC (lvl 10) ----
    CreatureStats(
        name="War Cleric",
        hit_points=76, armor_class=18, speed=30, hit_dice="10d8+20",
        abilities=AbilityScores(strength=14,dexterity=10,constitution=14,intelligence=10,wisdom=18,charisma=14),
        actions=[
            Action("Multiattack","2 attacks (with War Priest feature)",0,"",0,"",range=5,is_multiattack=True,
                   multiattack_count=2,multiattack_targets=["Warhammer","Warhammer"]),
            Action("Warhammer","Melee",6,"1d8",2,"bludgeoning"),
        ],
        bonus_actions=[
            Action("War Priest Strike",description="Bonus weapon attack",action_type="bonus",
                   attack_bonus=6,damage_dice="1d8",damage_bonus=2,damage_type="bludgeoning"),
        ],
        spellcasting_ability="Wisdom", spell_save_dc=16, spell_attack_bonus=8,
        spell_slots={"1st":4,"2nd":3,"3rd":3,"4th":3,"5th":2},
        spells_known=[
            get_spell("Cure Wounds"),
            get_spell("Mass Cure Wounds"),
            get_spell("Healing Word"),
            get_spell("Guiding Bolt", attack_bonus_fixed=8),
            get_spell("Sacred Flame"),
            get_spell("Spirit Guardians"),
            get_spell("Banishment"),
            get_spell("Hold Person"),
            get_spell("Spiritual Weapon"),
            get_spell("Flame Strike"),
        ],
        features=[
            Feature("Channel Divinity: Turn Undead","Turn undead within 30ft",uses_per_day=2),
            Feature("War Priest","Bonus weapon attack after using Attack action",uses_per_day=4),
            Feature("Divine Intervention","Call on deity for help",uses_per_day=1),
        ],
        saving_throws={"Wisdom":8,"Charisma":6},
        skills={"Insight":8,"Medicine":8,"Persuasion":6},
        challenge_rating=5.0, proficiency_bonus=4,
    ),

    # ---- ROGUE (lvl 10) ----
    CreatureStats(
        name="Shadow Rogue",
        hit_points=66, armor_class=16, speed=30, hit_dice="10d8+20",
        abilities=AbilityScores(strength=10,dexterity=20,constitution=14,intelligence=14,wisdom=12,charisma=12),
        actions=[
            Action("Multiattack","2 attacks",0,"",0,"",range=5,is_multiattack=True,
                   multiattack_count=2,multiattack_targets=["Rapier","Rapier"]),
            Action("Rapier","Melee",9,"1d8",5,"piercing"),
            Action("Hand Crossbow","Ranged",9,"1d6",5,"piercing",range=30),
        ],
        features=[
            Feature("Sneak Attack","5d6 extra dmg when Adv or ally adjacent"),
            Feature("Cunning Action","Dash/Disengage/Hide as bonus action"),
            Feature("Uncanny Dodge","Use reaction to halve attack damage"),
            Feature("Evasion","No damage on successful DEX save, half if fail"),
        ],
        saving_throws={"Dexterity":9,"Intelligence":6},
        skills={"Acrobatics":9,"Deception":5,"Perception":9,"Sleight of Hand":9,"Stealth":13},
        challenge_rating=5.0, proficiency_bonus=4,
    ),

    # ---- RANGER (lvl 10) ----
    CreatureStats(
        name="Elven Ranger",
        hit_points=74, armor_class=16, speed=35, hit_dice="10d10+10",
        abilities=AbilityScores(strength=12,dexterity=18,constitution=13,intelligence=12,wisdom=16,charisma=11),
        actions=[
            Action("Multiattack","3 Longbow or 2 Shortsword",0,"",0,"",range=150,is_multiattack=True,
                   multiattack_count=3,multiattack_targets=["Longbow","Longbow","Longbow"]),
            Action("Longbow","Ranged",8,"1d8",4,"piercing",range=150),
            Action("Shortsword","Melee",8,"1d6",4,"piercing"),
        ],
        spellcasting_ability="Wisdom", spell_save_dc=15, spell_attack_bonus=7,
        spell_slots={"1st":4,"2nd":3,"3rd":2},
        spells_known=[
            get_spell("Hunter's Mark"),
            get_spell("Hail of Thorns"),
            get_spell("Cure Wounds"),
        ],
        features=[
            Feature("Colossus Slayer","Extra 1d8 on hits vs damaged creatures"),
            Feature("Extra Attack","3 attacks"),
            Feature("Foe Slayer","Add WIS mod to attack or damage vs favored enemy"),
            Feature("Volley","Ranged attack vs all creatures in 10ft radius"),
        ],
        saving_throws={"Strength":5,"Dexterity":8},
        skills={"Animal Handling":7,"Nature":5,"Perception":11,"Stealth":8,"Survival":11},
        challenge_rating=5.0, proficiency_bonus=4,
    ),
]
