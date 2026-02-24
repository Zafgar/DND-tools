"""
D&D 5e 2014 Player's Handbook Feats Database
All 42 feats from the 2014 PHB, with machine-readable mechanics for AI combat use.
"""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Feat:
    name: str
    description: str = ""
    prerequisite: str = ""          # e.g. "STR 13", "Spellcasting", "Elf", ""
    ability_increase: str = ""      # e.g. "STR+1", "DEX+1 or CON+1"
    mechanic: str = ""              # Machine-readable key for combat effects
    mechanic_value: str = ""
    combat_effect: str = ""         # Brief combat-relevant description


# ============================================================
# ALL 42 PLAYER'S HANDBOOK FEATS (2014)
# ============================================================

ALERT = Feat(
    name="Alert",
    description=(
        "Always on the lookout for danger, you gain the following benefits: "
        "You gain a +5 bonus to initiative. You can't be surprised while you "
        "are conscious. Other creatures don't gain advantage on attack rolls "
        "against you as a result of being unseen by you."
    ),
    prerequisite="",
    ability_increase="",
    mechanic="alert",
    mechanic_value="+5",
    combat_effect="+5 initiative, can't be surprised, hidden attackers don't get advantage",
)

ATHLETE = Feat(
    name="Athlete",
    description=(
        "You have undergone extensive physical training to gain the following "
        "benefits: Increase your Strength or Dexterity score by 1, to a maximum "
        "of 20. When you are prone, standing up uses only 5 feet of your "
        "movement. Climbing doesn't cost you extra movement. You can make a "
        "running long jump or a running high jump after moving only 5 feet on "
        "foot, rather than 10 feet."
    ),
    prerequisite="",
    ability_increase="STR+1 or DEX+1",
    mechanic="athlete",
    mechanic_value="",
    combat_effect="Stand from prone costs only 5 ft movement; climbing costs no extra movement",
)

ACTOR = Feat(
    name="Actor",
    description=(
        "Skilled at mimicry and dramatics, you gain the following benefits: "
        "Increase your Charisma score by 1, to a maximum of 20. You have "
        "advantage on Charisma (Deception) and Charisma (Performance) checks "
        "when trying to pass yourself off as a different person. You can mimic "
        "the speech of another person or the sounds made by other creatures. "
        "You must have heard the person speaking, or heard the creature make "
        "the sound, for at least 1 minute. A successful Wisdom (Insight) check "
        "contested by your Charisma (Deception) check allows a listener to "
        "determine that the effect is faked."
    ),
    prerequisite="",
    ability_increase="CHA+1",
    mechanic="actor",
    mechanic_value="",
    combat_effect="Advantage on Deception/Performance to impersonate; CHA+1",
)

CHARGER = Feat(
    name="Charger",
    description=(
        "When you use your action to Dash, you can use a bonus action to make "
        "one melee weapon attack or to shove a creature. If you move at least "
        "10 feet in a straight line immediately before taking this bonus action, "
        "you either gain a +5 bonus to the attack's damage roll (if you chose "
        "to make a melee attack and hit) or push the target up to 10 feet away "
        "from you (if you chose to shove and you succeed)."
    ),
    prerequisite="",
    ability_increase="",
    mechanic="charger",
    mechanic_value="+5",
    combat_effect="After Dash, bonus action melee attack at +5 damage or shove 10 ft",
)

CROSSBOW_EXPERT = Feat(
    name="Crossbow Expert",
    description=(
        "Thanks to extensive practice with the crossbow, you gain the following "
        "benefits: You ignore the loading quality of crossbows with which you "
        "are proficient. Being within 5 feet of a hostile creature doesn't "
        "impose disadvantage on your ranged attack rolls. When you use the "
        "Attack action and attack with a one-handed weapon, you can use a "
        "bonus action to attack with a hand crossbow you are holding."
    ),
    prerequisite="",
    ability_increase="",
    mechanic="crossbow_expert",
    mechanic_value="",
    combat_effect=(
        "Ignore crossbow loading; no disadvantage on ranged attacks within 5 ft; "
        "bonus action hand crossbow attack after one-handed Attack action"
    ),
)

DEFENSIVE_DUELIST = Feat(
    name="Defensive Duelist",
    description=(
        "When you are wielding a finesse weapon with which you are proficient "
        "and another creature hits you with a melee attack, you can use your "
        "reaction to add your proficiency bonus to your AC for that attack, "
        "potentially causing the attack to miss you."
    ),
    prerequisite="DEX 13",
    ability_increase="",
    mechanic="defensive_duelist",
    mechanic_value="proficiency_bonus",
    combat_effect="Reaction: add proficiency bonus to AC against one melee attack (requires finesse weapon)",
)

DUAL_WIELDER = Feat(
    name="Dual Wielder",
    description=(
        "You master fighting with two weapons, gaining the following benefits: "
        "You gain a +1 bonus to AC while you are wielding a separate melee "
        "weapon in each hand. You can use two-weapon fighting even when the "
        "one-handed melee weapons you are wielding aren't light. You can draw "
        "or stow two one-handed weapons when you would normally be able to "
        "draw or stow only one."
    ),
    prerequisite="",
    ability_increase="",
    mechanic="dual_wielder",
    mechanic_value="+1",
    combat_effect="+1 AC when dual wielding; can dual wield non-light one-handed weapons",
)

DUNGEON_DELVER = Feat(
    name="Dungeon Delver",
    description=(
        "Alert to the hidden traps and secret doors found in many dungeons, "
        "you gain the following benefits: You have advantage on Wisdom "
        "(Perception) and Intelligence (Investigation) checks made to detect "
        "the presence of secret doors. You have advantage on saving throws "
        "made to avoid or resist traps. You have resistance to the damage "
        "dealt by traps. You can search for traps while travelling at a "
        "normal pace, instead of only at a slow pace."
    ),
    prerequisite="",
    ability_increase="",
    mechanic="dungeon_delver",
    mechanic_value="",
    combat_effect="Advantage on saves vs traps; resistance to trap damage",
)

DURABLE = Feat(
    name="Durable",
    description=(
        "Hardy and resilient, you gain the following benefits: Increase your "
        "Constitution score by 1, to a maximum of 20. When you roll a Hit Die "
        "to regain hit points, the minimum number of hit points you regain "
        "from the roll equals twice your Constitution modifier (minimum of 2)."
    ),
    prerequisite="",
    ability_increase="CON+1",
    mechanic="durable",
    mechanic_value="",
    combat_effect="CON+1; minimum HP regained from Hit Dice = 2x CON modifier",
)

ELEMENTAL_ADEPT = Feat(
    name="Elemental Adept",
    description=(
        "When you gain this feat, choose one of the following damage types: "
        "acid, cold, fire, lightning, or thunder. Spells you cast ignore "
        "resistance to damage of the chosen type. In addition, when you roll "
        "damage for a spell you cast that deals damage of that type, you can "
        "treat any 1 on a damage die as a 2. You can select this feat multiple "
        "times. Each time you do so, you must choose a different damage type."
    ),
    prerequisite="Spellcasting",
    ability_increase="",
    mechanic="elemental_adept",
    mechanic_value="chosen_element",
    combat_effect="Spells ignore resistance to chosen element; treat 1s on damage dice as 2s",
)

GRAPPLER = Feat(
    name="Grappler",
    description=(
        "You've developed the skills necessary to hold your own in close-quarters "
        "grappling. You gain the following benefits: You have advantage on attack "
        "rolls against a creature you are grappling. You can use your action to "
        "try to pin a creature grappled by you. To do so, make another grapple "
        "check. If you succeed, you and the creature are both restrained until "
        "the grapple ends."
    ),
    prerequisite="STR 13",
    ability_increase="",
    mechanic="grappler",
    mechanic_value="",
    combat_effect="Advantage on attacks vs grappled target; can pin (restrain both) with action",
)

GREAT_WEAPON_MASTER = Feat(
    name="Great Weapon Master",
    description=(
        "You've learned to put the weight of a weapon to your advantage, "
        "letting its momentum empower your strikes. You gain the following "
        "benefits: On your turn, when you score a critical hit with a melee "
        "weapon or reduce a creature to 0 hit points with one, you can make "
        "one melee weapon attack as a bonus action. Before you make a melee "
        "attack with a heavy weapon that you are proficient with, you can "
        "choose to take a -5 penalty to the attack roll. If the attack hits, "
        "you add +10 to the attack's damage."
    ),
    prerequisite="",
    ability_increase="",
    mechanic="great_weapon_master",
    mechanic_value="-5/+10",
    combat_effect=(
        "Bonus action melee attack on crit or kill; "
        "opt -5 attack / +10 damage with heavy weapons"
    ),
)

HEALER = Feat(
    name="Healer",
    description=(
        "You are an able physician, allowing you to mend wounds quickly and "
        "get your allies back in the fight. You gain the following benefits: "
        "When you use a healer's kit to stabilize a dying creature, that "
        "creature also regains 1 hit point. As an action, you can spend one "
        "use of a healer's kit to tend to a creature and restore 1d6 + 4 hit "
        "points to it, plus additional hit points equal to the creature's "
        "maximum number of Hit Dice. The creature can't regain hit points "
        "from this feat again until it finishes a short or long rest."
    ),
    prerequisite="",
    ability_increase="",
    mechanic="healer",
    mechanic_value="1d6+4+HD",
    combat_effect="Action: heal 1d6+4+max HD with healer's kit (once per creature per rest)",
)

HEAVILY_ARMORED = Feat(
    name="Heavily Armored",
    description=(
        "You have trained to master the use of heavy armor, gaining the "
        "following benefits: Increase your Strength score by 1, to a maximum "
        "of 20. You gain proficiency with heavy armor."
    ),
    prerequisite="Medium Armor proficiency",
    ability_increase="STR+1",
    mechanic="heavily_armored",
    mechanic_value="",
    combat_effect="STR+1; gain heavy armor proficiency",
)

HEAVY_ARMOR_MASTER = Feat(
    name="Heavy Armor Master",
    description=(
        "You can use your armor to deflect strikes that would kill others. "
        "You gain the following benefits: Increase your Strength score by 1, "
        "to a maximum of 20. While you are wearing heavy armor, bludgeoning, "
        "piercing, and slashing damage that you take from nonmagical weapons "
        "is reduced by 3."
    ),
    prerequisite="Heavy Armor proficiency",
    ability_increase="STR+1",
    mechanic="heavy_armor_master",
    mechanic_value="3",
    combat_effect="STR+1; reduce nonmagical B/P/S damage by 3 while in heavy armor",
)

INSPIRING_LEADER = Feat(
    name="Inspiring Leader",
    description=(
        "You can spend 10 minutes inspiring your companions, shoring up their "
        "resolve to fight. When you do so, choose up to six friendly creatures "
        "(which can include yourself) within 30 feet of you who can see or "
        "hear you and who can understand you. Each creature gains temporary "
        "hit points equal to your level + your Charisma modifier. A creature "
        "can't gain temporary hit points from this feat again until it has "
        "finished a short or long rest."
    ),
    prerequisite="CHA 13",
    ability_increase="",
    mechanic="inspiring_leader",
    mechanic_value="level+CHA",
    combat_effect="Grant up to 6 allies temp HP = your level + CHA mod (once per rest)",
)

KEEN_MIND = Feat(
    name="Keen Mind",
    description=(
        "You have a mind that can track time, direction, and detail with "
        "uncanny precision. You gain the following benefits: Increase your "
        "Intelligence score by 1, to a maximum of 20. You always know which "
        "way is north. You always know the number of hours left before the "
        "next sunrise or sunset. You can accurately recall anything you have "
        "seen or heard within the past month."
    ),
    prerequisite="",
    ability_increase="INT+1",
    mechanic="keen_mind",
    mechanic_value="",
    combat_effect="INT+1; perfect recall of past month",
)

LIGHTLY_ARMORED = Feat(
    name="Lightly Armored",
    description=(
        "You have trained to master the use of light armor, gaining the "
        "following benefits: Increase your Strength or Dexterity score by 1, "
        "to a maximum of 20. You gain proficiency with light armor."
    ),
    prerequisite="",
    ability_increase="STR+1 or DEX+1",
    mechanic="lightly_armored",
    mechanic_value="",
    combat_effect="STR+1 or DEX+1; gain light armor proficiency",
)

LINGUIST = Feat(
    name="Linguist",
    description=(
        "You have studied languages and codes, gaining the following benefits: "
        "Increase your Intelligence score by 1, to a maximum of 20. You learn "
        "three languages of your choice. You can ably create written ciphers. "
        "Others can't decipher a code you create unless you teach them, they "
        "succeed on an Intelligence check (DC equal to your Intelligence score "
        "+ your proficiency bonus), or they use magic to decipher it."
    ),
    prerequisite="",
    ability_increase="INT+1",
    mechanic="linguist",
    mechanic_value="",
    combat_effect="INT+1; learn 3 languages; create unbreakable ciphers",
)

LUCKY = Feat(
    name="Lucky",
    description=(
        "You have inexplicable luck that seems to kick in at just the right "
        "moment. You have 3 luck points. Whenever you make an attack roll, an "
        "ability check, or a saving throw, you can spend one luck point to "
        "roll an additional d20. You can choose to spend one of your luck "
        "points after you roll the die, but before the outcome is determined. "
        "You choose which of the d20s is used for the attack roll, ability "
        "check, or saving throw. You can also spend one luck point when an "
        "attack roll is made against you. Roll a d20, and then choose whether "
        "the attack uses the attacker's roll or yours. If more than one "
        "creature spends a luck point to influence the outcome of a roll, the "
        "points cancel each other out; no additional dice are rolled. You "
        "regain your expended luck points when you finish a long rest."
    ),
    prerequisite="",
    ability_increase="",
    mechanic="lucky",
    mechanic_value="3",
    combat_effect="3/long rest: roll extra d20 on attack/check/save and choose which to use",
)

MAGE_SLAYER = Feat(
    name="Mage Slayer",
    description=(
        "You have practiced techniques useful in melee combat against "
        "spellcasters, gaining the following benefits: When a creature within "
        "5 feet of you casts a spell, you can use your reaction to make a "
        "melee weapon attack against that creature. When you damage a creature "
        "that is concentrating on a spell, that creature has disadvantage on "
        "the saving throw it makes to maintain its concentration. You have "
        "advantage on saving throws against spells cast by creatures within "
        "5 feet of you."
    ),
    prerequisite="",
    ability_increase="",
    mechanic="mage_slayer",
    mechanic_value="",
    combat_effect=(
        "Reaction melee attack when adjacent creature casts a spell; "
        "target has disadvantage on concentration saves from your damage; "
        "advantage on saves vs spells cast within 5 ft"
    ),
)

MAGIC_INITIATE = Feat(
    name="Magic Initiate",
    description=(
        "Choose a class: bard, cleric, druid, sorcerer, warlock, or wizard. "
        "You learn two cantrips of your choice from that class's spell list. "
        "In addition, choose one 1st-level spell from that same list. You "
        "learn that spell and can cast it at its lowest level. Once you cast "
        "it, you must finish a long rest before you can cast it again using "
        "this feat. Your spellcasting ability for these spells depends on the "
        "class you chose: Charisma for bard, sorcerer, or warlock; Wisdom for "
        "cleric or druid; or Intelligence for wizard."
    ),
    prerequisite="",
    ability_increase="",
    mechanic="magic_initiate",
    mechanic_value="2_cantrips+1_spell",
    combat_effect="Learn 2 cantrips and one 1st-level spell (1/long rest) from a chosen class",
)

MARTIAL_ADEPT = Feat(
    name="Martial Adept",
    description=(
        "You have martial training that allows you to perform special combat "
        "maneuvers. You gain the following benefits: You learn two maneuvers "
        "of your choice from among those available to the Battle Master "
        "archetype in the fighter class. If a maneuver you use requires your "
        "target to make a saving throw to resist the maneuver's effects, the "
        "saving throw DC equals 8 + your proficiency bonus + your Strength or "
        "Dexterity modifier (your choice). You gain one superiority die, which "
        "is a d6 (this die is added to any superiority dice you have from "
        "another source). This die is used to fuel your maneuvers. A "
        "superiority die is expended when you use it. You regain your expended "
        "superiority dice when you finish a short or long rest."
    ),
    prerequisite="",
    ability_increase="",
    mechanic="martial_adept",
    mechanic_value="1d6",
    combat_effect="Learn 2 Battle Master maneuvers; gain 1 superiority die (d6, short rest recharge)",
)

MEDIUM_ARMOR_MASTER = Feat(
    name="Medium Armor Master",
    description=(
        "You have practiced moving in medium armor to gain the following "
        "benefits: Wearing medium armor doesn't impose disadvantage on your "
        "Dexterity (Stealth) checks. When you wear medium armor, you can add "
        "3, rather than 2, to your AC if you have a Dexterity of 16 or higher."
    ),
    prerequisite="Medium Armor proficiency",
    ability_increase="",
    mechanic="medium_armor_master",
    mechanic_value="+3",
    combat_effect="No Stealth disadvantage in medium armor; max DEX bonus to AC becomes +3",
)

MOBILE = Feat(
    name="Mobile",
    description=(
        "You are exceptionally speedy and agile. You gain the following "
        "benefits: Your speed increases by 10 feet. When you use the Dash "
        "action, difficult terrain doesn't cost you extra movement on that "
        "turn. When you make a melee attack against a creature, you don't "
        "provoke opportunity attacks from that creature for the rest of the "
        "turn, whether you hit or not."
    ),
    prerequisite="",
    ability_increase="",
    mechanic="mobile",
    mechanic_value="+10",
    combat_effect="+10 ft speed; Dash ignores difficult terrain; no OA from creatures you melee",
)

MODERATELY_ARMORED = Feat(
    name="Moderately Armored",
    description=(
        "You have trained to master the use of medium armor and shields, "
        "gaining the following benefits: Increase your Strength or Dexterity "
        "score by 1, to a maximum of 20. You gain proficiency with medium "
        "armor and shields."
    ),
    prerequisite="Light Armor proficiency",
    ability_increase="STR+1 or DEX+1",
    mechanic="moderately_armored",
    mechanic_value="",
    combat_effect="STR+1 or DEX+1; gain medium armor and shield proficiency",
)

MOUNTED_COMBATANT = Feat(
    name="Mounted Combatant",
    description=(
        "You are a dangerous foe to face while mounted. While you are mounted "
        "and aren't incapacitated, you gain the following benefits: You have "
        "advantage on melee attack rolls against any unmounted creature that "
        "is smaller than your mount. You can force an attack targeted at your "
        "mount to target you instead. If your mount is subjected to an effect "
        "that allows it to make a Dexterity saving throw to take only half "
        "damage, it instead takes no damage if it succeeds on the saving "
        "throw, and only half damage if it fails."
    ),
    prerequisite="",
    ability_increase="",
    mechanic="mounted_combatant",
    mechanic_value="",
    combat_effect=(
        "Advantage on melee vs smaller unmounted creatures; redirect attacks "
        "from mount to self; mount gets evasion on DEX saves"
    ),
)

OBSERVANT = Feat(
    name="Observant",
    description=(
        "Quick to notice details of your environment, you gain the following "
        "benefits: Increase your Intelligence or Wisdom score by 1, to a "
        "maximum of 20. If you can see a creature's mouth while it is "
        "speaking a language you understand, you can interpret what it's "
        "saying by reading its lips. You have a +5 bonus to your passive "
        "Wisdom (Perception) and passive Intelligence (Investigation) scores."
    ),
    prerequisite="",
    ability_increase="INT+1 or WIS+1",
    mechanic="observant",
    mechanic_value="+5",
    combat_effect="INT+1 or WIS+1; +5 passive Perception and Investigation; lip reading",
)

POLEARM_MASTER = Feat(
    name="Polearm Master",
    description=(
        "You can keep your enemies at bay with reach weapons. You gain the "
        "following benefits: When you take the Attack action and attack with "
        "only a glaive, halberd, quarterstaff, or spear, you can use a bonus "
        "action to make a melee attack with the opposite end of the weapon. "
        "This attack uses the same ability modifier as the primary attack. "
        "The weapon's damage die for this attack is a d4, and the attack "
        "deals bludgeoning damage. While you are wielding a glaive, halberd, "
        "pike, quarterstaff, or spear, other creatures provoke an opportunity "
        "attack from you when they enter your reach."
    ),
    prerequisite="",
    ability_increase="",
    mechanic="polearm_master",
    mechanic_value="1d4",
    combat_effect=(
        "Bonus action d4 bludgeoning attack with polearm butt; "
        "OA when creatures enter your reach"
    ),
)

RESILIENT = Feat(
    name="Resilient",
    description=(
        "Choose one ability score. You gain the following benefits: Increase "
        "the chosen ability score by 1, to a maximum of 20. You gain "
        "proficiency in saving throws using the chosen ability."
    ),
    prerequisite="",
    ability_increase="chosen_ability+1",
    mechanic="resilient",
    mechanic_value="chosen_ability",
    combat_effect="Chosen ability +1 and gain saving throw proficiency in that ability",
)

RITUAL_CASTER = Feat(
    name="Ritual Caster",
    description=(
        "You have learned a number of spells that you can cast as rituals. "
        "These spells are written in a ritual book, which you must have in "
        "hand while casting one of them. When you choose this feat, you "
        "acquire a ritual book holding two 1st-level spells of your choice. "
        "Choose one of the following classes: bard, cleric, druid, sorcerer, "
        "warlock, or wizard. You must choose your spells from that class's "
        "spell list, and the spells you choose must have the ritual tag. The "
        "class you choose also determines your spellcasting ability for these "
        "spells: Charisma for bard, sorcerer, or warlock; Wisdom for cleric "
        "or druid; or Intelligence for wizard. If you come across a spell in "
        "written form, such as a magical spell scroll or a wizard's spellbook, "
        "you might be able to add it to your ritual book. The spell must be on "
        "the spell list for the class you chose, the spell's level can be no "
        "higher than half your level (rounded up), and it must have the ritual "
        "tag. The process of copying the spell into your ritual book takes 2 "
        "hours per level of the spell, and costs 50 gp per level."
    ),
    prerequisite="INT 13 or WIS 13",
    ability_increase="",
    mechanic="ritual_caster",
    mechanic_value="",
    combat_effect="Cast ritual spells from a ritual book; can copy new ritual spells found",
)

SAVAGE_ATTACKER = Feat(
    name="Savage Attacker",
    description=(
        "Once per turn when you roll damage for a melee weapon attack, you "
        "can reroll the weapon's damage dice and use either total."
    ),
    prerequisite="",
    ability_increase="",
    mechanic="savage_attacker",
    mechanic_value="",
    combat_effect="1/turn: reroll melee weapon damage dice and use either result",
)

SENTINEL = Feat(
    name="Sentinel",
    description=(
        "You have mastered techniques to take advantage of every drop in any "
        "enemy's guard, gaining the following benefits: When you hit a creature "
        "with an opportunity attack, the creature's speed becomes 0 for the "
        "rest of the turn. Creatures provoke opportunity attacks from you even "
        "if they take the Disengage action before leaving your reach. When a "
        "creature within 5 feet of you makes an attack against a target other "
        "than you (and that target doesn't have this feat), you can use your "
        "reaction to make a melee weapon attack against the attacking creature."
    ),
    prerequisite="",
    ability_increase="",
    mechanic="sentinel",
    mechanic_value="",
    combat_effect=(
        "OA sets target speed to 0; Disengage doesn't prevent your OA; "
        "reaction attack when adjacent creature attacks someone else"
    ),
)

SHARPSHOOTER = Feat(
    name="Sharpshooter",
    description=(
        "You have mastered ranged weapons and can make shots that others find "
        "impossible. You gain the following benefits: Attacking at long range "
        "doesn't impose disadvantage on your ranged weapon attack rolls. Your "
        "ranged weapon attacks ignore half cover and three-quarters cover. "
        "Before you make an attack with a ranged weapon that you are proficient "
        "with, you can choose to take a -5 penalty to the attack roll. If the "
        "attack hits, you add +10 to the attack's damage."
    ),
    prerequisite="",
    ability_increase="",
    mechanic="sharpshooter",
    mechanic_value="-5/+10",
    combat_effect=(
        "No disadvantage at long range; ignore half/three-quarters cover; "
        "opt -5 attack / +10 damage with ranged weapons"
    ),
)

SHIELD_MASTER = Feat(
    name="Shield Master",
    description=(
        "You use shields not just for protection but also for offense. You "
        "gain the following benefits while you are wielding a shield: If you "
        "take the Attack action on your turn, you can use a bonus action to "
        "try to shove a creature within 5 feet of you with your shield. If "
        "you aren't incapacitated, you can add your shield's AC bonus to any "
        "Dexterity saving throw you make against a spell or other harmful "
        "effect that targets only you. If you are subjected to an effect that "
        "allows you to make a Dexterity saving throw to take only half damage, "
        "you can use your reaction to take no damage if you succeed on the "
        "saving throw, interposing your shield between yourself and the source "
        "of the effect."
    ),
    prerequisite="",
    ability_increase="",
    mechanic="shield_master",
    mechanic_value="+2",
    combat_effect=(
        "Bonus action shove after Attack; add shield AC to DEX saves vs "
        "targeted effects; reaction for evasion on DEX save half-damage effects"
    ),
)

SKILLED = Feat(
    name="Skilled",
    description=(
        "You gain proficiency in any combination of three skills or tools of "
        "your choice."
    ),
    prerequisite="",
    ability_increase="",
    mechanic="skilled",
    mechanic_value="3",
    combat_effect="Gain 3 skill or tool proficiencies",
)

SKULKER = Feat(
    name="Skulker",
    description=(
        "You are expert at slinking through shadows. You gain the following "
        "benefits: You can try to hide when you are lightly obscured from the "
        "creature from which you are hiding. When you are hidden from a "
        "creature and miss it with a ranged weapon attack, making the attack "
        "doesn't reveal your position. Dim light doesn't impose disadvantage "
        "on your Wisdom (Perception) checks relying on sight."
    ),
    prerequisite="DEX 13",
    ability_increase="",
    mechanic="skulker",
    mechanic_value="",
    combat_effect=(
        "Hide when lightly obscured; missed ranged attacks don't reveal position; "
        "no Perception disadvantage in dim light"
    ),
)

SPELL_SNIPER = Feat(
    name="Spell Sniper",
    description=(
        "You have learned techniques to enhance your attacks with certain "
        "kinds of spells, gaining the following benefits: When you cast a "
        "spell that requires you to make an attack roll, the spell's range is "
        "doubled. Your ranged spell attacks ignore half cover and three-quarters "
        "cover. You learn one cantrip that requires an attack roll. Choose the "
        "cantrip from the bard, cleric, druid, sorcerer, warlock, or wizard "
        "spell list. Your spellcasting ability for this cantrip depends on "
        "the spell list you chose from: Charisma for bard, sorcerer, or "
        "warlock; Wisdom for cleric or druid; or Intelligence for wizard."
    ),
    prerequisite="Spellcasting",
    ability_increase="",
    mechanic="spell_sniper",
    mechanic_value="x2",
    combat_effect="Double range on attack-roll spells; ignore half/three-quarters cover; learn 1 attack cantrip",
)

TAVERN_BRAWLER = Feat(
    name="Tavern Brawler",
    description=(
        "Accustomed to rough-and-tumble fighting using whatever is at hand, "
        "you gain the following benefits: Increase your Strength or "
        "Constitution score by 1, to a maximum of 20. You are proficient with "
        "improvised weapons. Your unarmed strike uses a d4 for damage. When "
        "you hit a creature with an unarmed strike or an improvised weapon on "
        "your turn, you can use a bonus action to attempt to grapple the target."
    ),
    prerequisite="",
    ability_increase="STR+1 or CON+1",
    mechanic="tavern_brawler",
    mechanic_value="1d4",
    combat_effect=(
        "STR+1 or CON+1; proficient with improvised weapons; unarmed = d4; "
        "bonus action grapple after unarmed/improvised hit"
    ),
)

TOUGH = Feat(
    name="Tough",
    description=(
        "Your hit point maximum increases by an amount equal to twice your "
        "level when you gain this feat. Each time you gain a level thereafter, "
        "your hit point maximum increases by an additional 2 hit points."
    ),
    prerequisite="",
    ability_increase="",
    mechanic="tough",
    mechanic_value="2xLevel",
    combat_effect="HP maximum increases by 2 per character level",
)

WAR_CASTER = Feat(
    name="War Caster",
    description=(
        "You have practiced casting spells in the midst of combat, learning "
        "techniques that grant you the following benefits: You have advantage "
        "on Constitution saving throws that you make to maintain your "
        "concentration on a spell when you take damage. You can perform the "
        "somatic components of spells even when you have weapons or a shield "
        "in one or both hands. When a hostile creature's movement provokes an "
        "opportunity attack from you, you can use your reaction to cast a "
        "spell at the creature, rather than making an opportunity attack. The "
        "spell must have a casting time of 1 action and must target only that "
        "creature."
    ),
    prerequisite="Spellcasting",
    ability_increase="",
    mechanic="war_caster",
    mechanic_value="",
    combat_effect=(
        "Advantage on concentration saves; somatic components with full hands; "
        "cast spell as opportunity attack"
    ),
)

WEAPON_MASTER = Feat(
    name="Weapon Master",
    description=(
        "You have practiced extensively with a variety of weapons, gaining "
        "the following benefits: Increase your Strength or Dexterity score "
        "by 1, to a maximum of 20. You gain proficiency with four weapons "
        "of your choice. Each one must be a simple or a martial weapon."
    ),
    prerequisite="",
    ability_increase="STR+1 or DEX+1",
    mechanic="weapon_master",
    mechanic_value="4",
    combat_effect="STR+1 or DEX+1; gain proficiency with 4 weapons of choice",
)


# ============================================================
# MASTER LISTS AND LOOKUP HELPERS
# ============================================================

ALL_FEATS: List[Feat] = [
    ALERT,
    ATHLETE,
    ACTOR,
    CHARGER,
    CROSSBOW_EXPERT,
    DEFENSIVE_DUELIST,
    DUAL_WIELDER,
    DUNGEON_DELVER,
    DURABLE,
    ELEMENTAL_ADEPT,
    GRAPPLER,
    GREAT_WEAPON_MASTER,
    HEALER,
    HEAVILY_ARMORED,
    HEAVY_ARMOR_MASTER,
    INSPIRING_LEADER,
    KEEN_MIND,
    LIGHTLY_ARMORED,
    LINGUIST,
    LUCKY,
    MAGE_SLAYER,
    MAGIC_INITIATE,
    MARTIAL_ADEPT,
    MEDIUM_ARMOR_MASTER,
    MOBILE,
    MODERATELY_ARMORED,
    MOUNTED_COMBATANT,
    OBSERVANT,
    POLEARM_MASTER,
    RESILIENT,
    RITUAL_CASTER,
    SAVAGE_ATTACKER,
    SENTINEL,
    SHARPSHOOTER,
    SHIELD_MASTER,
    SKILLED,
    SKULKER,
    SPELL_SNIPER,
    TAVERN_BRAWLER,
    TOUGH,
    WAR_CASTER,
    WEAPON_MASTER,
]

FEATS_BY_NAME = {f.name: f for f in ALL_FEATS}


def get_feat(name: str) -> Optional[Feat]:
    """Look up a feat by exact name. Returns None if not found."""
    return FEATS_BY_NAME.get(name)


# ============================================================
# PREREQUISITE FILTERING
# ============================================================

# Classes that have spellcasting by default (at level 1 or 2)
_SPELLCASTING_CLASSES = {
    "Bard", "Cleric", "Druid", "Sorcerer", "Warlock", "Wizard",
    "Paladin", "Ranger",
}

# Default armor proficiencies by class
_LIGHT_ARMOR_CLASSES = {
    "Bard", "Cleric", "Druid", "Fighter", "Paladin", "Ranger",
    "Rogue", "Warlock",
}
_MEDIUM_ARMOR_CLASSES = {
    "Barbarian", "Cleric", "Druid", "Fighter", "Paladin", "Ranger",
}
_HEAVY_ARMOR_CLASSES = {
    "Fighter", "Paladin",
}

# Minimum spellcasting level by class (when the class first gains spellcasting)
_SPELLCASTING_LEVEL = {
    "Bard": 1, "Cleric": 1, "Druid": 1, "Sorcerer": 1,
    "Warlock": 1, "Wizard": 1, "Paladin": 2, "Ranger": 2,
    # Subclass casters (Eldritch Knight, Arcane Trickster) gain at 3
    "Fighter": 3, "Rogue": 3,
}


def _has_spellcasting(character_class: str, level: int) -> bool:
    """Check if a class has spellcasting at the given level."""
    min_lvl = _SPELLCASTING_LEVEL.get(character_class, 0)
    return min_lvl > 0 and level >= min_lvl


def _has_light_armor(character_class: str) -> bool:
    return character_class in _LIGHT_ARMOR_CLASSES


def _has_medium_armor(character_class: str) -> bool:
    return character_class in _MEDIUM_ARMOR_CLASSES


def _has_heavy_armor(character_class: str) -> bool:
    return character_class in _HEAVY_ARMOR_CLASSES


def _ability_score(abilities: Optional[dict], ability: str) -> int:
    """Get an ability score from an abilities dict. Defaults to 10."""
    if abilities is None:
        return 10
    # Support both full names and abbreviations
    _map = {
        "STR": "strength", "DEX": "dexterity", "CON": "constitution",
        "INT": "intelligence", "WIS": "wisdom", "CHA": "charisma",
        "strength": "strength", "dexterity": "dexterity",
        "constitution": "constitution", "intelligence": "intelligence",
        "wisdom": "wisdom", "charisma": "charisma",
    }
    key = _map.get(ability.upper(), _map.get(ability.lower(), ability.lower()))
    return abilities.get(key, abilities.get(ability, 10))


def _meets_prerequisite(
    feat: Feat,
    character_class: str,
    race: str,
    level: int,
    abilities: Optional[dict],
) -> bool:
    """Check whether a character meets the prerequisite for a feat."""
    prereq = feat.prerequisite
    if not prereq:
        return True

    prereq_lower = prereq.lower()

    # --- Ability score prerequisites ---
    # Patterns: "STR 13", "DEX 13", "CHA 13", "INT 13 or WIS 13"
    ability_abbrevs = {"str", "dex", "con", "int", "wis", "cha"}
    if " or " in prereq_lower:
        # e.g. "INT 13 or WIS 13"
        parts = prereq.split(" or ")
        met_any = False
        for part in parts:
            part = part.strip()
            tokens = part.split()
            if len(tokens) == 2 and tokens[0].upper()[:3].lower() in ability_abbrevs:
                try:
                    required = int(tokens[1])
                    if _ability_score(abilities, tokens[0]) >= required:
                        met_any = True
                except ValueError:
                    pass
        if met_any:
            return True
        # If none matched, fall through to return False only if it looks like
        # an ability score prereq
        if any(a in prereq_lower for a in ability_abbrevs):
            return False

    # Single ability score: "STR 13", "DEX 13", "CHA 13"
    tokens = prereq.split()
    if len(tokens) == 2 and tokens[0].upper()[:3].lower() in ability_abbrevs:
        try:
            required = int(tokens[1])
            return _ability_score(abilities, tokens[0]) >= required
        except ValueError:
            pass

    # --- Spellcasting prerequisite ---
    if "spellcasting" in prereq_lower:
        return _has_spellcasting(character_class, level)

    # --- Armor proficiency prerequisites ---
    if "heavy armor" in prereq_lower and "proficiency" in prereq_lower:
        return _has_heavy_armor(character_class)
    if "medium armor" in prereq_lower and "proficiency" in prereq_lower:
        return _has_medium_armor(character_class)
    if "light armor" in prereq_lower and "proficiency" in prereq_lower:
        return _has_light_armor(character_class)

    # --- Race prerequisites (e.g. "Elf") ---
    if race and prereq_lower in race.lower():
        return True

    # If we can't parse the prerequisite, be permissive and include the feat
    return True


def get_feats_available(
    character_class: str = "",
    race: str = "",
    level: int = 1,
    abilities: Optional[dict] = None,
) -> List[Feat]:
    """Return all feats whose prerequisites are met by the given character.

    Args:
        character_class: e.g. "Fighter", "Wizard", "Rogue"
        race: e.g. "Human", "High Elf", "Hill Dwarf"
        level: character level (1-20)
        abilities: dict mapping ability names/abbreviations to scores, e.g.
                   {"strength": 16, "dexterity": 14, "constitution": 12,
                    "intelligence": 10, "wisdom": 13, "charisma": 8}
                   Keys can be full names or abbreviations (STR, DEX, etc.).

    Returns:
        List of Feat objects whose prerequisites are satisfied.
    """
    return [
        feat for feat in ALL_FEATS
        if _meets_prerequisite(feat, character_class, race, level, abilities)
    ]
