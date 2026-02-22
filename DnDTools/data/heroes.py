from data.models import CreatureStats, AbilityScores, Action

# Määritellään sankarit, joita pelaaja voi valita tiimiinsä
hero_list = [
    CreatureStats(
        name="Sir Paladin",
        hit_points=45,
        armor_class=18,
        speed=30,
        abilities=AbilityScores(strength=16, constitution=14, charisma=14),
        actions=[Action("Longsword", "Melee", 5, "1d8", 3)],
        spell_slots={"1st": 3}
    ),
    CreatureStats(
        name="Elven Wizard",
        hit_points=28,
        armor_class=12,
        speed=30,
        abilities=AbilityScores(intelligence=18, dexterity=14, constitution=12),
        actions=[Action("Firebolt", "Ranged", 5, "1d10", 0, range=120)],
        spell_slots={"1st": 4, "2nd": 3, "3rd": 2}
    ),
    CreatureStats(
        name="Dwarven Cleric",
        hit_points=38,
        armor_class=18,
        speed=25,
        abilities=AbilityScores(wisdom=16, strength=14, constitution=14),
        actions=[Action("Warhammer", "Melee", 4, "1d8", 2)],
        spell_slots={"1st": 4, "2nd": 2}
    ),
    CreatureStats(
        name="Rogue Shadow",
        hit_points=32,
        armor_class=15,
        speed=30,
        abilities=AbilityScores(dexterity=18, constitution=12, intelligence=12),
        actions=[Action("Dagger", "Melee", 6, "1d4", 4)],
        spell_slots={}
    )
]