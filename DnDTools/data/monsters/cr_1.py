from data.models import CreatureStats, AbilityScores, Action

# D&D 5e SRD CR 1 Monsters

monsters = [
    CreatureStats(
        name="Bugbear",
        size="Medium",
        type="Humanoid",
        armor_class=16, # Hide armor + shield
        hit_points=27,
        speed=30,
        abilities=AbilityScores(strength=15, dexterity=14, constitution=13, intelligence=8, wisdom=11, charisma=9),
        actions=[
            Action("Morningstar", "Melee Weapon Attack", attack_bonus=4, damage_dice="2d8", damage_bonus=2),
            Action("Javelin", "Melee or Ranged Weapon Attack", attack_bonus=4, damage_dice="1d6", damage_bonus=2, range=30)
        ],
        challenge_rating=1.0,
        xp=200,
        skills={"Stealth": 6, "Survival": 2},
        saving_throws={}
    ),
    CreatureStats(
        name="Dire Wolf",
        size="Large",
        type="Beast",
        armor_class=14, # Natural armor
        hit_points=37,
        speed=50,
        abilities=AbilityScores(strength=17, dexterity=15, constitution=15, intelligence=3, wisdom=12, charisma=7),
        actions=[
            Action("Bite", "Melee Weapon Attack", attack_bonus=5, damage_dice="2d6", damage_bonus=3)
        ],
        challenge_rating=1.0,
        xp=200,
        skills={"Perception": 3, "Stealth": 4},
        saving_throws={}
    ),
    CreatureStats(
        name="Ghoul",
        size="Medium",
        type="Undead",
        armor_class=12,
        hit_points=22,
        speed=30,
        abilities=AbilityScores(strength=13, dexterity=15, constitution=10, intelligence=7, wisdom=10, charisma=6),
        actions=[
            Action("Claws", "Melee Weapon Attack", attack_bonus=4, damage_dice="2d4", damage_bonus=2)
        ],
        challenge_rating=1.0,
        xp=200,
        condition_immunities=["Charmed", "Exhaustion", "Poisoned"],
        saving_throws={}
    )
]