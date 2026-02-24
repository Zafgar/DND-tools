from data.models import SpellInfo
import copy

# D&D 5e SRD Combat Spell Library
# Includes damage, healing, buffs, and control spells supported by the engine.

_spells = {
    # --- CANTRIPS ---
    "Acid Splash": SpellInfo("Acid Splash", level=0, action_type="action", range=60, targets="single",
                             damage_dice="1d6", damage_type="acid", save_ability="Dexterity", half_on_save=False,
                             description="Acid damage to target (scaling)"),
    
    "Chill Touch": SpellInfo("Chill Touch", level=0, action_type="action", range=120, targets="single",
                             damage_dice="1d8", damage_type="necrotic", description="Prevents healing until next turn"),
    
    "Command": SpellInfo("Command", level=1, action_type="action", range=60, targets="single",
                         save_ability="Wisdom", applies_condition="Prone", description="Command target to grovel (Prone)"),

    "Eldritch Blast": SpellInfo("Eldritch Blast", level=0, action_type="action", range=120, targets="single",
                                damage_dice="1d10", damage_type="force", description="Beam of crackling energy"),
    
    "Fire Bolt": SpellInfo("Fire Bolt", level=0, action_type="action", range=120, targets="single",
                           damage_dice="1d10", damage_type="fire", damage_scaling="1d10"),
    
    "Poison Spray": SpellInfo("Poison Spray", level=0, action_type="action", range=10, targets="single",
                              damage_dice="1d12", damage_type="poison", save_ability="Constitution", half_on_save=False),
    
    "Mage Hand": SpellInfo("Mage Hand", level=0, action_type="action", range=30, targets="single",
                           description="Move objects 30ft"),

    "Mind Blast": SpellInfo("Mind Blast", level=0, action_type="action", range=60, aoe_radius=60, aoe_shape="cone",
                            damage_dice="5d8", damage_type="psychic", save_ability="Intelligence", applies_condition="Stunned",
                            half_on_save=False, targets="aoe"),

    "Ray of Frost": SpellInfo("Ray of Frost", level=0, action_type="action", range=60, targets="single",
                              damage_dice="1d8", damage_type="cold", description="Reduces speed by 10ft"),
    
    "Sacred Flame": SpellInfo("Sacred Flame", level=0, action_type="action", range=60, targets="single",
                              damage_dice="1d8", damage_type="radiant", save_ability="Dexterity", half_on_save=False),
    
    "Shocking Grasp": SpellInfo("Shocking Grasp", level=0, action_type="action", range=5, targets="single",
                                damage_dice="1d8", damage_type="lightning", description="Advantage if target in metal armor"),
    
    "Vicious Mockery": SpellInfo("Vicious Mockery", level=0, action_type="action", range=60, targets="single",
                                 damage_dice="1d4", damage_type="psychic", save_ability="Wisdom", half_on_save=False,
                                 description="Target has Disadvantage on next attack"),

    # --- LEVEL 1 ---
    "Burning Hands": SpellInfo("Burning Hands", level=1, action_type="action", range=15, aoe_radius=15, aoe_shape="cone",
                               damage_dice="3d6", damage_type="fire", save_ability="Dexterity", half_on_save=True, targets="aoe"),
    
    "Animate Dead": SpellInfo("Animate Dead", level=3, action_type="action", range=10, targets="single",
                              description="Create undead servant"),

    "Bless": SpellInfo("Bless", level=1, action_type="action", range=30, targets="aoe", concentration=True, duration="1 minute",
                       description="+1d4 to attacks/saves for 3 targets"),
    
    "Chromatic Orb": SpellInfo("Chromatic Orb", level=1, action_type="action", range=90, targets="single",
                               damage_dice="3d8", damage_type="acid", description="Choose acid, cold, fire, lightning, poison, thunder"),
    
    "Cure Wounds": SpellInfo("Cure Wounds", level=1, action_type="action", range=5, heals="1d8+4", targets="single",
                             description="Heals 1d8 + mod"),
    
    "Divine Favor": SpellInfo("Divine Favor", level=1, action_type="bonus", range=0, targets="self", concentration=True, duration="1 minute",
                              description="Weapon attacks deal +1d4 radiant"),
    
    "Entangle": SpellInfo("Entangle", level=1, action_type="action", range=90, aoe_radius=20, aoe_shape="cube",
                          save_ability="Strength", applies_condition="Restrained", concentration=True, duration="1 minute", targets="aoe"),
    
    "Guiding Bolt": SpellInfo("Guiding Bolt", level=1, action_type="action", range=120, targets="single",
                              damage_dice="4d6", damage_type="radiant", description="Next attack vs target has Adv"),
    
    "Hail of Thorns": SpellInfo("Hail of Thorns", level=1, action_type="bonus", range=0, targets="self", concentration=True,
                                damage_dice="1d10", damage_type="piercing", description="Next hit explodes 5ft radius"),
    
    "Healing Word": SpellInfo("Healing Word", level=1, action_type="bonus", range=60, heals="1d4+4", targets="single",
                              description="Bonus action heal"),
    
    "Hellish Rebuke": SpellInfo("Hellish Rebuke", level=1, action_type="reaction", range=60, targets="single",
                                damage_dice="2d10", damage_type="fire", save_ability="Dexterity", half_on_save=True,
                                description="Reaction when damaged"),

    "Hex": SpellInfo("Hex", level=1, action_type="bonus", range=90, targets="single", concentration=True, duration="1 hour",
                     description="Extra 1d6 necrotic on hits vs hexed target. Disadvantage on one ability check.",
                     bonus_damage_dice="1d6", bonus_damage_type="necrotic"),

    "Faerie Fire": SpellInfo("Faerie Fire", level=1, action_type="action", range=60, aoe_radius=20, aoe_shape="cube",
                             save_ability="Dexterity", applies_condition="Outlined", concentration=True, duration="1 minute",
                             targets="aoe", half_on_save=False,
                             description="Outlined creatures grant Advantage on attacks. No invisibility."),

    "Heroism": SpellInfo("Heroism", level=1, action_type="action", range=0, targets="single", concentration=True,
                         duration="1 minute", description="Target immune to Frightened, gains temp HP = CHA mod each turn"),

    "Dissonant Whispers": SpellInfo("Dissonant Whispers", level=1, action_type="action", range=60, targets="single",
                                    damage_dice="3d6", damage_type="psychic", save_ability="Wisdom", half_on_save=True,
                                    description="Target uses reaction to move away on fail"),

    "Tasha's Hideous Laughter": SpellInfo("Tasha's Hideous Laughter", level=1, action_type="action", range=30,
                                          targets="single", save_ability="Wisdom", applies_condition="Incapacitated",
                                          concentration=True, duration="1 minute",
                                          description="Target falls prone and is incapacitated, laughing"),
    
    "Hunter's Mark": SpellInfo("Hunter's Mark", level=1, action_type="bonus", range=90, targets="single", concentration=True, duration="1 hour",
                               description="Extra 1d6 dmg on weapon hits vs marked target",
                               bonus_damage_dice="1d6", bonus_damage_type=""),
    
    "Inflict Wounds": SpellInfo("Inflict Wounds", level=1, action_type="action", range=5, targets="single",
                                damage_dice="3d10", damage_type="necrotic"),
    
    "Mage Armor": SpellInfo("Mage Armor", level=1, action_type="action", range=0, targets="self", duration="8 hours",
                            description="AC becomes 13 + Dex"),
    
    "Magic Weapon": SpellInfo("Magic Weapon", level=2, action_type="bonus", range=0, targets="self", concentration=True,
                              duration="1 hour", description="Weapon becomes magical +1"),

    "Magic Missile": SpellInfo("Magic Missile", level=1, action_type="action", range=120, targets="single",
                               damage_dice="3d4+3", damage_type="force", description="Auto-hit 3 missiles (1d4+1 each)"),
    
    "Shield": SpellInfo("Shield", level=1, action_type="reaction", range=0, targets="self", duration="1 round",
                        description="+5 AC until start of next turn"),
    
    "Shield of Faith": SpellInfo("Shield of Faith", level=1, action_type="bonus", range=60, targets="single", concentration=True, duration="10 minutes",
                                 description="+2 AC"),
    
    "Thunderwave": SpellInfo("Thunderwave", level=1, action_type="action", range=0, aoe_radius=15, aoe_shape="cube",
                             damage_dice="2d8", damage_type="thunder", save_ability="Constitution", half_on_save=True, targets="aoe",
                             description="Push 10ft on fail"),

    # --- LEVEL 2 ---
    "Blindness/Deafness": SpellInfo("Blindness/Deafness", level=2, action_type="action", range=30, targets="single",
                                    save_ability="Constitution", applies_condition="Blinded", duration="1 minute"),
    
    "Hold Person": SpellInfo("Hold Person", level=2, action_type="action", range=60, targets="single",
                             save_ability="Wisdom", applies_condition="Paralyzed", concentration=True, duration="1 minute"),
    
    "Invisibility": SpellInfo("Invisibility", level=2, action_type="action", range=0, targets="single",
                              applies_condition="Invisible", concentration=True, duration="1 hour"),
    
    "Misty Step": SpellInfo("Misty Step", level=2, action_type="bonus", range=0, targets="self",
                            description="Teleport 30ft"),
    
    "Scorching Ray": SpellInfo("Scorching Ray", level=2, action_type="action", range=120, targets="single",
                               damage_dice="6d6", damage_type="fire", description="3 rays, 2d6 each (Simulated as one 6d6 hit for AI)"),
    
    "Shatter": SpellInfo("Shatter", level=2, action_type="action", range=60, aoe_radius=10, aoe_shape="sphere",
                         damage_dice="3d8", damage_type="thunder", save_ability="Constitution", half_on_save=True, targets="aoe"),
    
    "Spiritual Weapon": SpellInfo("Spiritual Weapon", level=2, action_type="bonus", range=60, targets="single",
                                  damage_dice="1d8+4", damage_type="force", duration="1 minute",
                                  description="Summon spectral weapon. Bonus action melee spell attack each turn.",
                                  summon_name="Spiritual Weapon", summon_hp=0, summon_ac=99,
                                  summon_damage_dice="1d8", summon_damage_type="force",
                                  summon_attack_bonus=0, summon_duration_rounds=10),
    
    "Web": SpellInfo("Web", level=2, action_type="action", range=60, aoe_radius=20, aoe_shape="cube",
                     save_ability="Dexterity", applies_condition="Restrained", concentration=True, duration="1 hour", targets="aoe"),

    "Heat Metal": SpellInfo("Heat Metal", level=2, action_type="action", range=60, targets="single",
                            damage_dice="2d8", damage_type="fire", concentration=True, duration="1 minute",
                            description="Target holding/wearing metal takes damage. Disadvantage on attacks/checks."),

    "Moonbeam": SpellInfo("Moonbeam", level=2, action_type="action", range=120, aoe_radius=5, aoe_shape="cylinder",
                          damage_dice="2d10", damage_type="radiant", save_ability="Constitution", half_on_save=True,
                          targets="aoe", concentration=True, duration="1 minute"),

    "Silence": SpellInfo("Silence", level=2, action_type="action", range=120, aoe_radius=20, aoe_shape="sphere",
                         targets="aoe", concentration=True, duration="10 minutes",
                         description="No sound in area. Prevents verbal spellcasting."),

    "Mirror Image": SpellInfo("Mirror Image", level=2, action_type="action", range=0, targets="self",
                              duration="1 minute", description="3 illusory duplicates. AC 10+DEX. Destroyed on hit."),

    "Enhance Ability": SpellInfo("Enhance Ability", level=2, action_type="action", range=0, targets="single",
                                 concentration=True, duration="1 hour",
                                 description="Grant advantage on one ability's checks. Bear=STR, etc."),

    # --- LEVEL 3 ---
    "Call Lightning": SpellInfo("Call Lightning", level=3, action_type="action", range=120, aoe_radius=5, aoe_shape="sphere",
                                damage_dice="3d10", damage_type="lightning", save_ability="Dexterity", half_on_save=True, targets="aoe",
                                concentration=True, duration="10 minutes"),
    
    "Conjure Animals": SpellInfo("Conjure Animals", level=3, action_type="action", range=60, targets="aoe",
                                 concentration=True, duration="1 hour",
                                 description="Summon fey spirits as beasts (DM chooses). CR varies by count."),

    "Counterspell": SpellInfo("Counterspell", level=3, action_type="reaction", range=60, targets="single",
                              description="Interrupt a spell cast"),
    
    "Dispel Magic": SpellInfo("Dispel Magic", level=3, action_type="action", range=120, targets="single",
                              description="End spells on target"),
    
    "Fear": SpellInfo("Fear", level=3, action_type="action", range=0, aoe_radius=30, aoe_shape="cone",
                      save_ability="Wisdom", applies_condition="Frightened", concentration=True, duration="1 minute", targets="aoe"),
    
    "Fireball": SpellInfo("Fireball", level=3, action_type="action", range=150, aoe_radius=20, aoe_shape="sphere",
                          damage_dice="8d6", damage_type="fire", save_ability="Dexterity", half_on_save=True, targets="aoe"),
    
    "Fly": SpellInfo("Fly", level=3, action_type="action", range=0, targets="single", concentration=True, duration="10 minutes",
                     description="Target gains 60ft fly speed"),
    
    "Haste": SpellInfo("Haste", level=3, action_type="action", range=30, targets="single", concentration=True, duration="1 minute",
                       description="Double speed, +2 AC, extra action"),
    
    "Lightning Bolt": SpellInfo("Lightning Bolt", level=3, action_type="action", range=100, aoe_radius=100, aoe_shape="line",
                                damage_dice="8d6", damage_type="lightning", save_ability="Dexterity", half_on_save=True, targets="aoe"),
    
    "Revivify": SpellInfo("Revivify", level=3, action_type="action", range=0, targets="single",
                          description="Return dead to life with 1 HP (within 1 min)"),
    
    "Spirit Guardians": SpellInfo("Spirit Guardians", level=3, action_type="action", range=0, aoe_radius=15, aoe_shape="sphere",
                                  damage_dice="3d8", damage_type="radiant", save_ability="Wisdom", half_on_save=True, targets="aoe",
                                  concentration=True, duration="10 minutes"),
    
    "Vampiric Touch": SpellInfo("Vampiric Touch", level=3, action_type="action", range=5, targets="single",
                                damage_dice="3d6", damage_type="necrotic", concentration=True, duration="1 minute",
                                description="Heal half damage dealt"),

    # --- LEVEL 4 ---
    "Banishment": SpellInfo("Banishment", level=4, action_type="action", range=60, targets="single",
                            save_ability="Charisma", applies_condition="Incapacitated", concentration=True, duration="1 minute"),

    "Blight": SpellInfo("Blight", level=4, action_type="action", range=30, targets="single",
                        damage_dice="8d8", damage_type="necrotic", save_ability="Constitution", half_on_save=True),
    
    "Dimension Door": SpellInfo("Dimension Door", level=4, action_type="action", range=500, targets="self",
                                description="Teleport 500ft"),
    
    "Greater Invisibility": SpellInfo("Greater Invisibility", level=4, action_type="action", range=0, targets="single",
                                      applies_condition="Invisible", concentration=True, duration="1 minute",
                                      description="Does not break on attack"),
    
    "Ice Storm": SpellInfo("Ice Storm", level=4, action_type="action", range=300, aoe_radius=20, aoe_shape="cylinder",
                           damage_dice="2d8+4d6", damage_type="cold", save_ability="Dexterity", half_on_save=True, targets="aoe"),
    
    "Wall of Fire": SpellInfo("Wall of Fire", level=4, action_type="action", range=120, aoe_radius=60, aoe_shape="line",
                              damage_dice="5d8", damage_type="fire", save_ability="Dexterity", half_on_save=True, targets="aoe",
                              concentration=True, duration="1 minute"),

    # --- LEVEL 5 ---
    "Cloudkill": SpellInfo("Cloudkill", level=5, action_type="action", range=120, aoe_radius=20, aoe_shape="sphere",
                           damage_dice="5d8", damage_type="poison", save_ability="Constitution", half_on_save=True, targets="aoe",
                           concentration=True, duration="10 minutes"),
    
    "Cone of Cold": SpellInfo("Cone of Cold", level=5, action_type="action", range=60, aoe_radius=60, aoe_shape="cone",
                              damage_dice="8d8", damage_type="cold", save_ability="Constitution", half_on_save=True, targets="aoe"),
    
    "Flame Strike": SpellInfo("Flame Strike", level=5, action_type="action", range=60, aoe_radius=10, aoe_shape="cylinder",
                              damage_dice="4d6+4d6", damage_type="fire", save_ability="Dexterity", half_on_save=True, targets="aoe"),
    
    "Hold Monster": SpellInfo("Hold Monster", level=5, action_type="action", range=90, targets="single",
                              save_ability="Wisdom", applies_condition="Paralyzed", concentration=True, duration="1 minute"),
    
    "Mass Cure Wounds": SpellInfo("Mass Cure Wounds", level=5, action_type="action", range=60, heals="3d8+4", targets="aoe",
                                  description="Heal up to 6 creatures"),

    # --- LEVEL 6 ---
    "Chain Lightning": SpellInfo("Chain Lightning", level=6, action_type="action", range=150, targets="single",
                                 damage_dice="10d8", damage_type="lightning", save_ability="Dexterity", half_on_save=True,
                                 description="Arcs to 3 other targets"),
    
    "Disintegrate": SpellInfo("Disintegrate", level=6, action_type="action", range=60, targets="single",
                              damage_dice="10d6+40", damage_type="force", save_ability="Dexterity", half_on_save=False,
                              description="Dusts target on 0 HP"),
    
    "Sunbeam": SpellInfo("Sunbeam", level=6, action_type="action", range=0, aoe_radius=60, aoe_shape="line",
                         damage_dice="6d8", damage_type="radiant", save_ability="Constitution", half_on_save=True, targets="aoe",
                         concentration=True, duration="1 minute", applies_condition="Blinded"),

    # --- LEVEL 7 ---
    "Finger of Death": SpellInfo("Finger of Death", level=7, action_type="action", range=60, targets="single",
                                 damage_dice="7d8+30", damage_type="necrotic", save_ability="Constitution", half_on_save=True),
    
    "Plane Shift": SpellInfo("Plane Shift", level=7, action_type="action", range=0, targets="self",
                             description="Teleport to another plane"),

    "Fire Storm": SpellInfo("Fire Storm", level=7, action_type="action", range=150, aoe_radius=20, aoe_shape="cube",
                            damage_dice="7d10", damage_type="fire", save_ability="Dexterity", half_on_save=True, targets="aoe"),

    # --- LEVEL 8 ---
    "Dominate Monster": SpellInfo("Dominate Monster", level=8, action_type="action", range=60, targets="single",
                                  save_ability="Wisdom", applies_condition="Charmed", concentration=True, duration="1 hour"),

    "Power Word Stun": SpellInfo("Power Word Stun", level=8, action_type="action", range=60, targets="single",
                                 description="Stuns target with < 150 HP (no save initially)", applies_condition="Stunned"),
    
    "Sunburst": SpellInfo("Sunburst", level=8, action_type="action", range=150, aoe_radius=60, aoe_shape="sphere",
                          damage_dice="12d6", damage_type="radiant", save_ability="Constitution", half_on_save=True, targets="aoe",
                          applies_condition="Blinded"),

    # --- LEVEL 9 ---
    "Meteor Swarm": SpellInfo("Meteor Swarm", level=9, action_type="action", range=1000, aoe_radius=40, aoe_shape="sphere",
                              damage_dice="20d6+20d6", damage_type="fire", save_ability="Dexterity", half_on_save=True, targets="aoe"),
    
    "Power Word Kill": SpellInfo("Power Word Kill", level=9, action_type="action", range=60, targets="single",
                                 description="Instantly kills target with < 100 HP"),
    
    "Time Stop": SpellInfo("Time Stop", level=9, action_type="action", range=0, targets="self",
                           description="Take 1d4+1 turns in a row"),
}

def get_spell(name: str, **overrides) -> SpellInfo:
    """
    Returns a copy of the spell from the library.
    You can override fields like 'attack_bonus_fixed' or 'save_dc_fixed' here.
    """
    if name not in _spells:
        # Return a placeholder if not found to prevent crashes
        return SpellInfo(name=name, description="Unknown spell")
    
    spell = copy.deepcopy(_spells[name])
    
    for key, value in overrides.items():
        if hasattr(spell, key):
            setattr(spell, key, value)
            
    return spell