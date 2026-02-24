from data.models import CreatureStats, AbilityScores, Action, Feature

monsters = [
    CreatureStats(name="Bandit", size="Medium", creature_type="Humanoid",
        armor_class=12, hit_points=11, hit_dice="2d8+2", speed=30,
        abilities=AbilityScores(strength=11,dexterity=12,constitution=12,intelligence=10,wisdom=10,charisma=10),
        actions=[Action("Scimitar","Melee",3,"1d6",1,"slashing",range=5),
                 Action("Hand Crossbow","Ranged",3,"1d6",1,"piercing",range=30)],
        challenge_rating=0.125, xp=25, proficiency_bonus=2),

    CreatureStats(name="Cultist", size="Medium", creature_type="Humanoid",
        armor_class=12, hit_points=9, hit_dice="2d8", speed=30,
        abilities=AbilityScores(strength=11,dexterity=12,constitution=10,intelligence=10,wisdom=11,charisma=10),
        actions=[Action("Scimitar","Melee",3,"1d6",1,"slashing")],
        features=[Feature("Dark Devotion","Adv on saves vs frightened/charmed")],
        challenge_rating=0.125, xp=25, proficiency_bonus=2),

    CreatureStats(name="Guard", size="Medium", creature_type="Humanoid",
        armor_class=16, hit_points=11, hit_dice="2d8+2", speed=30,
        abilities=AbilityScores(strength=13,dexterity=12,constitution=12,intelligence=10,wisdom=11,charisma=10),
        actions=[Action("Spear","Melee/Ranged",3,"1d6",1,"piercing",range=5)],
        skills={"Perception":2},
        challenge_rating=0.125, xp=25, proficiency_bonus=2),

    CreatureStats(name="Kobold", size="Small", creature_type="Humanoid",
        armor_class=12, hit_points=5, hit_dice="2d6-2", speed=30,
        abilities=AbilityScores(strength=7,dexterity=15,constitution=9,intelligence=8,wisdom=7,charisma=8),
        actions=[Action("Dagger","Melee",4,"1d4",2,"piercing"),
                 Action("Sling","Ranged",4,"1d4",2,"bludgeoning",range=30)],
        features=[Feature("Pack Tactics","Adv on attack when ally adjacent to target"),
                  Feature("Sunlight Sensitivity","Disadv on attacks in sunlight")],
        condition_immunities=[],
        challenge_rating=0.125, xp=25, proficiency_bonus=2),
]
