"""Classic 5e monsters the catalogue was missing.

Every creature here exists for one of two reasons.

Most of them fill a silhouette in ``states/creature_art.py`` that had
nothing to draw: the bird, bat, aquatic, crustacean, centaur, dinosaur
and hydra shapes were written for monsters the library did not yet
contain, so at the table they were art with no monster behind them.

The rest round out the low end of the encounter tables, where a DM
building a random fight had almost nothing between CR 1/8 and CR 2 that
was not a humanoid with a sword.

All stat blocks follow the 2014 rules (SRD 5.1, CC-BY-4.0).
"""
from data.models import CreatureStats, AbilityScores, Action, Feature


def _keen_sight():
    return Feature("Keen Sight",
                   "Advantage on Perception checks that rely on sight")


monsters = [
    # ----------------------------------------------------------------- #
    # Birds
    # ----------------------------------------------------------------- #
    CreatureStats(name="Giant Eagle", size="Large", creature_type="Beast",
        armor_class=13, hit_points=26, hit_dice="4d10+4", speed=10,
        fly_speed=80,
        abilities=AbilityScores(strength=16, dexterity=17, constitution=13,
                                intelligence=8, wisdom=14, charisma=10),
        actions=[Action("Multiattack", "Beak + Talons", 0, "", 0, "",
                        range=5, is_multiattack=True, multiattack_count=2,
                        multiattack_targets=["Beak", "Talons"]),
                 Action("Beak", "Melee", 5, "1d6", 3, "piercing"),
                 Action("Talons", "Melee", 5, "2d6", 3, "slashing")],
        skills={"Perception": 4},
        features=[_keen_sight()],
        challenge_rating=1.0, xp=200, proficiency_bonus=2),

    CreatureStats(name="Roc", size="Gargantuan", creature_type="Monstrosity",
        armor_class=15, hit_points=248, hit_dice="16d20+80", speed=20,
        fly_speed=120,
        abilities=AbilityScores(strength=28, dexterity=10, constitution=20,
                                intelligence=3, wisdom=10, charisma=9),
        actions=[Action("Multiattack", "Beak + Talons", 0, "", 0, "",
                        range=10, is_multiattack=True, multiattack_count=2,
                        multiattack_targets=["Beak", "Talons"]),
                 Action("Beak", "Melee", 13, "4d8", 9, "piercing", reach=10),
                 Action("Talons", "Melee", 13, "4d6", 9, "slashing",
                        reach=5, applies_condition="Grappled",
                        condition_save="Strength", condition_dc=19)],
        saving_throws={"Dexterity": 4, "Constitution": 9, "Wisdom": 4,
                       "Charisma": 3},
        skills={"Perception": 4},
        features=[_keen_sight()],
        challenge_rating=11.0, xp=7200, proficiency_bonus=4),

    CreatureStats(name="Harpy", size="Medium", creature_type="Monstrosity",
        armor_class=11, hit_points=38, hit_dice="7d8+7", speed=20,
        fly_speed=40,
        abilities=AbilityScores(strength=12, dexterity=13, constitution=12,
                                intelligence=7, wisdom=10, charisma=13),
        actions=[Action("Multiattack", "Claws + Club", 0, "", 0, "",
                        range=5, is_multiattack=True, multiattack_count=2,
                        multiattack_targets=["Claws", "Club"]),
                 Action("Claws", "Melee", 3, "2d4", 1, "slashing"),
                 Action("Club", "Melee", 3, "1d4", 1, "bludgeoning"),
                 Action("Luring Song", "Song", 0, "0", 0, "", range=300,
                        applies_condition="Charmed",
                        condition_save="Wisdom", condition_dc=11)],
        features=[Feature("Luring Song",
                          "Every creature within 300 ft that can hear the "
                          "song makes a DC 11 WIS save or is Charmed and "
                          "drawn toward the harpy",
                          save_dc=11, save_ability="Wisdom",
                          applies_condition="Charmed")],
        challenge_rating=1.0, xp=200, proficiency_bonus=2),

    # ----------------------------------------------------------------- #
    # Bats
    # ----------------------------------------------------------------- #
    CreatureStats(name="Giant Bat", size="Large", creature_type="Beast",
        armor_class=13, hit_points=22, hit_dice="4d10", speed=10,
        fly_speed=60,
        abilities=AbilityScores(strength=15, dexterity=16, constitution=11,
                                intelligence=2, wisdom=12, charisma=6),
        actions=[Action("Bite", "Melee", 4, "1d6", 3, "piercing")],
        features=[Feature("Echolocation",
                          "Cannot use blindsight while deafened"),
                  Feature("Keen Hearing",
                          "Advantage on Perception checks that rely on "
                          "hearing")],
        challenge_rating=0.25, xp=50, proficiency_bonus=2),

    # ----------------------------------------------------------------- #
    # Aquatic
    # ----------------------------------------------------------------- #
    CreatureStats(name="Hunter Shark", size="Large", creature_type="Beast",
        armor_class=12, hit_points=45, hit_dice="6d10+12", speed=0,
        swim_speed=40,
        abilities=AbilityScores(strength=18, dexterity=13, constitution=15,
                                intelligence=1, wisdom=10, charisma=4),
        actions=[Action("Bite", "Melee", 6, "3d6", 4, "piercing")],
        skills={"Perception": 2},
        features=[Feature("Blood Frenzy",
                          "Advantage on attacks against any creature that "
                          "is not at full hit points"),
                  Feature("Water Breathing",
                          "Can breathe only underwater",
                          mechanic="water_breathing")],
        challenge_rating=2.0, xp=450, proficiency_bonus=2),

    CreatureStats(name="Sahuagin", size="Medium", creature_type="Humanoid",
        armor_class=12, hit_points=22, hit_dice="4d8+4", speed=30,
        swim_speed=40,
        abilities=AbilityScores(strength=13, dexterity=11, constitution=12,
                                intelligence=12, wisdom=13, charisma=9),
        actions=[Action("Multiattack", "Bite + Claws", 0, "", 0, "",
                        range=5, is_multiattack=True, multiattack_count=2,
                        multiattack_targets=["Bite", "Claws"]),
                 Action("Bite", "Melee", 3, "1d4", 1, "piercing"),
                 Action("Claws", "Melee", 3, "1d4", 1, "slashing"),
                 Action("Spear", "Melee", 3, "1d6", 1, "piercing",
                        properties=["thrown", "versatile"], range=20,
                        long_range=60)],
        skills={"Perception": 5},
        features=[Feature("Blood Frenzy",
                          "Advantage on attacks against any creature that "
                          "is not at full hit points"),
                  Feature("Limited Amphibiousness",
                          "Can breathe air and water, but must be "
                          "submerged once every 4 hours",
                          mechanic="amphibious"),
                  Feature("Shark Telepathy",
                          "Can magically command any shark within 120 ft")],
        challenge_rating=0.5, xp=100, proficiency_bonus=2),

    CreatureStats(name="Merrow", size="Large", creature_type="Monstrosity",
        armor_class=13, hit_points=45, hit_dice="6d10+12", speed=10,
        swim_speed=40,
        abilities=AbilityScores(strength=18, dexterity=10, constitution=15,
                                intelligence=8, wisdom=10, charisma=9),
        actions=[Action("Multiattack", "Bite + Claws or Harpoon", 0, "", 0,
                        "", range=5, is_multiattack=True,
                        multiattack_count=2,
                        multiattack_targets=["Bite", "Claws"]),
                 Action("Bite", "Melee", 6, "1d8", 4, "piercing"),
                 Action("Claws", "Melee", 6, "2d4", 4, "slashing"),
                 Action("Harpoon", "Ranged", 6, "2d6", 4, "piercing",
                        range=20, long_range=60,
                        applies_condition="Grappled",
                        condition_save="Strength", condition_dc=14)],
        features=[Feature("Amphibious", "Can breathe air and water",
                          mechanic="amphibious")],
        challenge_rating=2.0, xp=450, proficiency_bonus=2),

    # ----------------------------------------------------------------- #
    # Crustaceans
    # ----------------------------------------------------------------- #
    CreatureStats(name="Giant Crab", size="Medium", creature_type="Beast",
        armor_class=15, hit_points=13, hit_dice="3d8", speed=30,
        swim_speed=30,
        abilities=AbilityScores(strength=13, dexterity=15, constitution=11,
                                intelligence=1, wisdom=9, charisma=3),
        actions=[Action("Claw", "Melee", 3, "1d6", 1, "bludgeoning",
                        applies_condition="Grappled",
                        condition_save="Strength", condition_dc=11)],
        skills={"Stealth": 4},
        features=[Feature("Amphibious", "Can breathe air and water",
                          mechanic="amphibious")],
        challenge_rating=0.125, xp=25, proficiency_bonus=2),

    CreatureStats(name="Chuul", size="Large", creature_type="Aberration",
        armor_class=16, hit_points=93, hit_dice="11d10+33", speed=30,
        swim_speed=30,
        abilities=AbilityScores(strength=19, dexterity=10, constitution=16,
                                intelligence=5, wisdom=11, charisma=5),
        actions=[Action("Multiattack", "Two pincers", 0, "", 0, "",
                        range=10, is_multiattack=True, multiattack_count=2,
                        multiattack_targets=["Pincer"]),
                 Action("Pincer", "Melee", 6, "2d6", 4, "bludgeoning",
                        reach=10, applies_condition="Grappled",
                        condition_save="Strength", condition_dc=14),
                 Action("Tentacles", "Melee", 0, "0", 0, "", range=5,
                        applies_condition="Paralyzed",
                        condition_save="Constitution", condition_dc=13)],
        skills={"Perception": 4},
        damage_immunities=["poison"],
        condition_immunities=["Poisoned"],
        features=[Feature("Amphibious", "Can breathe air and water",
                          mechanic="amphibious"),
                  Feature("Sense Magic",
                          "Senses magic within 120 ft at will")],
        challenge_rating=4.0, xp=1100, proficiency_bonus=2),

    # ----------------------------------------------------------------- #
    # Centaur
    # ----------------------------------------------------------------- #
    CreatureStats(name="Centaur", size="Large", creature_type="Monstrosity",
        armor_class=12, hit_points=45, hit_dice="6d10+12", speed=50,
        abilities=AbilityScores(strength=18, dexterity=14, constitution=14,
                                intelligence=9, wisdom=13, charisma=11),
        actions=[Action("Multiattack", "Pike + Hooves, or two Longbows", 0,
                        "", 0, "", range=10, is_multiattack=True,
                        multiattack_count=2,
                        multiattack_targets=["Pike", "Hooves"]),
                 Action("Pike", "Melee", 6, "1d10", 4, "piercing", reach=10),
                 Action("Hooves", "Melee", 6, "2d6", 4, "bludgeoning"),
                 Action("Longbow", "Ranged", 4, "1d8", 2, "piercing",
                        range=150, long_range=600)],
        skills={"Athletics": 6, "Perception": 3, "Survival": 3},
        features=[Feature("Charge",
                          "If it moves 30 ft straight toward a target and "
                          "hits with a pike, the target takes an extra 3d6 "
                          "piercing damage",
                          damage_dice="3d6", damage_type="piercing")],
        challenge_rating=2.0, xp=450, proficiency_bonus=2),

    # ----------------------------------------------------------------- #
    # Dinosaurs
    # ----------------------------------------------------------------- #
    CreatureStats(name="Tyrannosaurus Rex", size="Huge",
        creature_type="Beast",
        armor_class=13, hit_points=136, hit_dice="13d12+52", speed=50,
        abilities=AbilityScores(strength=25, dexterity=10, constitution=19,
                                intelligence=2, wisdom=12, charisma=9),
        actions=[Action("Multiattack", "Bite + Tail", 0, "", 0, "",
                        range=10, is_multiattack=True, multiattack_count=2,
                        multiattack_targets=["Bite", "Tail"]),
                 Action("Bite", "Melee", 10, "4d12", 7, "piercing",
                        reach=10, applies_condition="Grappled",
                        condition_save="Strength", condition_dc=17),
                 Action("Tail", "Melee", 10, "3d8", 7, "bludgeoning",
                        reach=10)],
        skills={"Perception": 4},
        features=[Feature("Bite and Hold",
                          "A Medium or smaller creature bitten is Grappled "
                          "(escape DC 17) and the rex can bite nothing else")],
        challenge_rating=8.0, xp=3900, proficiency_bonus=3),

    CreatureStats(name="Velociraptor", size="Small", creature_type="Beast",
        armor_class=13, hit_points=10, hit_dice="3d6", speed=30,
        abilities=AbilityScores(strength=6, dexterity=14, constitution=10,
                                intelligence=4, wisdom=12, charisma=6),
        actions=[Action("Multiattack", "Bite + Claws", 0, "", 0, "",
                        range=5, is_multiattack=True, multiattack_count=2,
                        multiattack_targets=["Bite", "Claws"]),
                 Action("Bite", "Melee", 4, "1d6", 2, "piercing"),
                 Action("Claws", "Melee", 4, "1d4", 2, "slashing")],
        skills={"Perception": 3, "Stealth": 4},
        features=[Feature("Pack Tactics",
                          "Advantage on attacks when an ally is within 5 ft "
                          "of the target",
                          mechanic="pack_tactics")],
        challenge_rating=0.25, xp=50, proficiency_bonus=2),

    # ----------------------------------------------------------------- #
    # Lycanthropes
    # ----------------------------------------------------------------- #
    CreatureStats(name="Wererat", size="Medium", creature_type="Humanoid",
        armor_class=12, hit_points=33, hit_dice="6d8+6", speed=30,
        abilities=AbilityScores(strength=10, dexterity=15, constitution=12,
                                intelligence=11, wisdom=10, charisma=8),
        actions=[Action("Multiattack", "Two attacks", 0, "", 0, "",
                        range=5, is_multiattack=True, multiattack_count=2,
                        multiattack_targets=["Bite", "Shortsword"]),
                 Action("Bite", "Melee", 4, "1d4", 2, "piercing"),
                 Action("Shortsword", "Melee", 4, "1d6", 2, "piercing"),
                 Action("Hand Crossbow", "Ranged", 4, "1d6", 2, "piercing",
                        range=30, long_range=120)],
        skills={"Perception": 2, "Stealth": 4},
        damage_immunities=[
            "bludgeoning piercing slashing from non-silvered"],
        features=[Feature("Shapechanger",
                          "Can shift between rat, hybrid and humanoid form"),
                  Feature("Keen Smell",
                          "Advantage on Perception checks that rely on "
                          "smell")],
        challenge_rating=2.0, xp=450, proficiency_bonus=2),

    CreatureStats(name="Weretiger", size="Medium", creature_type="Humanoid",
        armor_class=12, hit_points=120, hit_dice="16d8+48", speed=30,
        abilities=AbilityScores(strength=17, dexterity=15, constitution=16,
                                intelligence=10, wisdom=13, charisma=11),
        actions=[Action("Multiattack", "Two claws or two scimitars", 0, "",
                        0, "", range=5, is_multiattack=True,
                        multiattack_count=2,
                        multiattack_targets=["Claw", "Claw"]),
                 Action("Bite", "Melee", 5, "1d10", 3, "piercing"),
                 Action("Claw", "Melee", 5, "1d8", 3, "slashing"),
                 Action("Scimitar", "Melee", 5, "1d6", 3, "slashing"),
                 Action("Longbow", "Ranged", 4, "1d8", 2, "piercing",
                        range=150, long_range=600)],
        skills={"Perception": 5, "Stealth": 4},
        damage_immunities=[
            "bludgeoning piercing slashing from non-silvered"],
        features=[Feature("Shapechanger",
                          "Can shift between tiger, hybrid and humanoid "
                          "form"),
                  Feature("Keen Hearing and Smell",
                          "Advantage on Perception checks that rely on "
                          "hearing or smell"),
                  Feature("Pounce",
                          "If it moves 15 ft straight toward a target and "
                          "hits with a claw, the target makes a DC 14 STR "
                          "save or falls Prone",
                          save_dc=14, save_ability="Strength",
                          applies_condition="Prone")],
        challenge_rating=4.0, xp=1100, proficiency_bonus=2),

    # ----------------------------------------------------------------- #
    # Goblinoids and other small folk
    # ----------------------------------------------------------------- #
    CreatureStats(name="Hobgoblin Captain", size="Medium",
        creature_type="Humanoid",
        armor_class=17, hit_points=39, hit_dice="6d8+12", speed=30,
        abilities=AbilityScores(strength=15, dexterity=14, constitution=14,
                                intelligence=12, wisdom=10, charisma=13),
        actions=[Action("Multiattack", "Two greatsword attacks", 0, "", 0,
                        "", range=5, is_multiattack=True,
                        multiattack_count=2,
                        multiattack_targets=["Greatsword"]),
                 Action("Greatsword", "Melee", 4, "2d6", 2, "slashing"),
                 Action("Javelin", "Ranged", 4, "1d6", 2, "piercing",
                        range=30, long_range=120)],
        features=[Feature("Martial Advantage",
                          "Once per turn deals an extra 2d6 damage to a "
                          "creature within 5 ft of an ally",
                          damage_dice="2d6")],
        challenge_rating=3.0, xp=700, proficiency_bonus=2),

    CreatureStats(name="Xvart", size="Small", creature_type="Humanoid",
        armor_class=13, hit_points=7, hit_dice="2d6", speed=30,
        abilities=AbilityScores(strength=8, dexterity=14, constitution=10,
                                intelligence=8, wisdom=7, charisma=7),
        actions=[Action("Shortsword", "Melee", 4, "1d6", 2, "piercing"),
                 Action("Sling", "Ranged", 4, "1d4", 2, "bludgeoning",
                        range=30, long_range=120)],
        skills={"Stealth": 4},
        features=[Feature("Overbearing Pack",
                          "Advantage on Shove checks when an ally is "
                          "within 5 ft of the target",
                          mechanic="pack_tactics"),
                  Feature("Raxivort's Tongue",
                          "Can speak with bats and rats")],
        challenge_rating=0.125, xp=25, proficiency_bonus=2),

    # ----------------------------------------------------------------- #
    # Armoured soldiery
    # ----------------------------------------------------------------- #
    CreatureStats(name="Knight", size="Medium", creature_type="Humanoid",
        armor_class=18, hit_points=52, hit_dice="8d8+16", speed=30,
        abilities=AbilityScores(strength=16, dexterity=11, constitution=14,
                                intelligence=11, wisdom=11, charisma=15),
        actions=[Action("Multiattack", "Two greatsword attacks", 0, "", 0,
                        "", range=5, is_multiattack=True,
                        multiattack_count=2,
                        multiattack_targets=["Greatsword"]),
                 Action("Greatsword", "Melee", 5, "2d6", 3, "slashing"),
                 Action("Heavy Crossbow", "Ranged", 2, "1d10", 0,
                        "piercing", range=100, long_range=400),
                 Action("Leadership", "Rally", 0, "0", 0, "", range=30,
                        action_type="bonus")],
        saving_throws={"Constitution": 4, "Wisdom": 2},
        features=[Feature("Brave",
                          "Advantage on saving throws against being "
                          "Frightened"),
                  Feature("Leadership",
                          "Bonus action: one ally within 30 ft that can "
                          "hear the knight adds 1d4 to an attack roll or "
                          "save (recharges after a short rest)",
                          feature_type="bonus", recharge="short rest",
                          uses_per_day=1)],
        challenge_rating=3.0, xp=700, proficiency_bonus=2),

    CreatureStats(name="Gladiator", size="Medium", creature_type="Humanoid",
        armor_class=16, hit_points=112, hit_dice="15d8+45", speed=30,
        abilities=AbilityScores(strength=18, dexterity=15, constitution=16,
                                intelligence=10, wisdom=12, charisma=15),
        actions=[Action("Multiattack", "Three melee attacks", 0, "", 0, "",
                        range=5, is_multiattack=True, multiattack_count=3,
                        multiattack_targets=["Spear"]),
                 Action("Spear", "Melee", 7, "1d6", 4, "piercing",
                        properties=["thrown", "versatile"], range=20,
                        long_range=60),
                 Action("Shield Bash", "Melee", 7, "2d4", 4, "bludgeoning",
                        applies_condition="Prone",
                        condition_save="Strength", condition_dc=15)],
        saving_throws={"Strength": 7, "Dexterity": 5, "Constitution": 6},
        skills={"Athletics": 10, "Intimidation": 5},
        features=[Feature("Brave",
                          "Advantage on saving throws against being "
                          "Frightened"),
                  Feature("Parry",
                          "Reaction: add 3 to AC against one melee attack "
                          "it can see",
                          feature_type="reaction")],
        challenge_rating=5.0, xp=1800, proficiency_bonus=3),

    # ----------------------------------------------------------------- #
    # Casters
    # ----------------------------------------------------------------- #
    CreatureStats(name="Priest", size="Medium", creature_type="Humanoid",
        armor_class=13, hit_points=27, hit_dice="5d8+5", speed=25,
        abilities=AbilityScores(strength=10, dexterity=10, constitution=12,
                                intelligence=13, wisdom=16, charisma=13),
        actions=[Action("Mace", "Melee", 2, "1d6", 0, "bludgeoning")],
        skills={"Medicine": 7, "Persuasion": 3, "Religion": 5},
        spellcasting_ability="Wisdom",
        spell_save_dc=13, spell_attack_bonus=5,
        cantrip_names=["Sacred Flame", "Guidance"],
        spell_names=["Bless", "Cure Wounds", "Sanctuary",
                     "Lesser Restoration", "Spiritual Weapon"],
        spell_slots={"1st": 4, "2nd": 3},
        features=[Feature("Divine Eminence",
                          "Bonus action: expend a spell slot to add 3d6 "
                          "radiant damage to the next melee hit",
                          feature_type="bonus", damage_dice="3d6",
                          damage_type="radiant")],
        challenge_rating=2.0, xp=450, proficiency_bonus=2),

    CreatureStats(name="Necromancer", size="Medium",
        creature_type="Humanoid",
        armor_class=12, hit_points=66, hit_dice="12d8+12", speed=30,
        abilities=AbilityScores(strength=9, dexterity=14, constitution=12,
                                intelligence=17, wisdom=12, charisma=11),
        actions=[Action("Dagger", "Melee", 5, "1d4", 2, "piercing",
                        properties=["finesse", "thrown"], range=20,
                        long_range=60)],
        saving_throws={"Intelligence": 6, "Wisdom": 4},
        skills={"Arcana": 6, "History": 6},
        spellcasting_ability="Intelligence",
        spell_save_dc=14, spell_attack_bonus=6,
        cantrip_names=["Chill Touch", "Mage Hand", "Ray of Frost"],
        spell_names=["Mage Armor", "Blindness/Deafness", "Web",
                     "Animate Dead", "Vampiric Touch", "Blight",
                     "Cloudkill"],
        spell_slots={"1st": 4, "2nd": 3, "3rd": 3, "4th": 3, "5th": 1},
        features=[Feature("Grim Harvest",
                          "Once per turn, killing a creature with a spell "
                          "heals the necromancer for twice the spell's "
                          "level in hit points")],
        challenge_rating=9.0, xp=5000, proficiency_bonus=4),
]
