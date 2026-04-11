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
                         save_ability="Wisdom", applies_condition="Prone", description="Command target to grovel (Prone)", repeat_save=False),

    "Eldritch Blast": SpellInfo("Eldritch Blast", level=0, action_type="action", range=120, targets="single",
                                damage_dice="1d10", damage_type="force", description="Beam of crackling energy"),
    
    "Fire Bolt": SpellInfo("Fire Bolt", level=0, action_type="action", range=120, targets="single",
                           damage_dice="1d10", damage_type="fire", damage_scaling="1d10"),
    
    "Guidance": SpellInfo("Guidance", level=0, action_type="action", range=0, targets="touch",
                          concentration=True, duration="1 minute",
                          description="Target adds +1d4 to one ability check."),

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
    
    "Resistance": SpellInfo("Resistance", level=0, action_type="action", range=0, targets="touch",
                            concentration=True, duration="1 minute",
                            description="Target adds +1d4 to one saving throw."),

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
                          save_ability="Strength", applies_condition="Restrained", concentration=True, duration="1 minute", targets="aoe",
                          creates_terrain="entangle"),

    "Fog Cloud": SpellInfo("Fog Cloud", level=1, action_type="action", range=120, aoe_radius=20, aoe_shape="sphere",
                           targets="aoe", concentration=True, duration="1 hour",
                           creates_terrain="fog_cloud",
                           description="Heavily obscured area. Blocks line of sight."),
    
    "Guiding Bolt": SpellInfo("Guiding Bolt", level=1, action_type="action", range=120, targets="single",
                              damage_dice="4d6", damage_type="radiant", description="Next attack vs target has Adv",
                              applies_condition="Guiding Bolt", duration="2 rounds"),
    
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

    "Darkness": SpellInfo("Darkness", level=2, action_type="action", range=60, aoe_radius=15, aoe_shape="sphere",
                          targets="aoe", concentration=True, duration="10 minutes",
                          creates_terrain="darkness",
                          description="Magical darkness. Heavily obscured. Blocks darkvision."),
    
    "Hold Person": SpellInfo("Hold Person", level=2, action_type="action", range=60, targets="single",
                             save_ability="Wisdom", applies_condition="Paralyzed", concentration=True, duration="1 minute"),
    
    "Invisibility": SpellInfo("Invisibility", level=2, action_type="action", range=0, targets="single",
                              applies_condition="Invisible", concentration=True, duration="1 hour"),
    
    "Lesser Restoration": SpellInfo("Lesser Restoration", level=2, action_type="action", range=0, targets="touch",
                                    description="End disease or condition: blinded, deafened, paralyzed, poisoned"),

    "Misty Step": SpellInfo("Misty Step", level=2, action_type="bonus", range=0, targets="self",
                            description="Teleport 30ft"),
    
    "Scorching Ray": SpellInfo("Scorching Ray", level=2, action_type="action", range=120, targets="single",
                               damage_dice="6d6", damage_type="fire", description="3 rays, 2d6 each (Simulated as one 6d6 hit for AI)"),
    
    "Shatter": SpellInfo("Shatter", level=2, action_type="action", range=60, aoe_radius=10, aoe_shape="sphere",
                         damage_dice="3d8", damage_type="thunder", save_ability="Constitution", half_on_save=True, targets="aoe"),

    "Silence": SpellInfo("Silence", level=2, action_type="action", range=120, aoe_radius=20, aoe_shape="sphere",
                         targets="aoe", concentration=True, duration="10 minutes", ritual=True,
                         creates_terrain="silence",
                         description="No sound. Prevents spells with verbal (V) components."),

    "Spike Growth": SpellInfo("Spike Growth", level=2, action_type="action", range=150, aoe_radius=20, aoe_shape="sphere",
                              damage_dice="2d4", damage_type="piercing", targets="aoe",
                              concentration=True, duration="10 minutes",
                              creates_terrain="spike_growth",
                              description="Difficult terrain. 2d4 piercing per 5ft moved through."),

    "Spiritual Weapon": SpellInfo("Spiritual Weapon", level=2, action_type="bonus", range=60, targets="single",
                                  damage_dice="1d8+4", damage_type="force", duration="1 minute",
                                  description="Summon spectral weapon. Bonus action melee spell attack each turn.",
                                  summon_name="Spiritual Weapon", summon_hp=0, summon_ac=99,
                                  summon_damage_dice="1d8", summon_damage_type="force",
                                  summon_attack_bonus=0, summon_duration_rounds=10),
    
    "Web": SpellInfo("Web", level=2, action_type="action", range=60, aoe_radius=20, aoe_shape="cube",
                     save_ability="Dexterity", applies_condition="Restrained", concentration=True, duration="1 hour", targets="aoe",
                     creates_terrain="web"),

    "Heat Metal": SpellInfo("Heat Metal", level=2, action_type="action", range=60, targets="single",
                            damage_dice="2d8", damage_type="fire", concentration=True, duration="1 minute",
                            description="Target holding/wearing metal takes damage. Disadvantage on attacks/checks."),

    "Moonbeam": SpellInfo("Moonbeam", level=2, action_type="action", range=120, aoe_radius=5, aoe_shape="cylinder",
                          damage_dice="2d10", damage_type="radiant", save_ability="Constitution", half_on_save=True,
                          targets="aoe", concentration=True, duration="1 minute",
                          creates_terrain="moonbeam"),

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

    "Hypnotic Pattern": SpellInfo("Hypnotic Pattern", level=3, action_type="action", range=120,
                                  aoe_radius=30, aoe_shape="cube", save_ability="Wisdom",
                                  applies_condition="Charmed", concentration=True, duration="1 minute",
                                  targets="aoe", half_on_save=False,
                                  description="Charmed (Incapacitated + speed 0) on failed WIS save. "
                                  "Ends when creature takes damage or is shaken awake."),

    "Lightning Bolt": SpellInfo("Lightning Bolt", level=3, action_type="action", range=100, aoe_radius=100, aoe_shape="line",
                                damage_dice="8d6", damage_type="lightning", save_ability="Dexterity", half_on_save=True, targets="aoe"),

    "Slow": SpellInfo("Slow", level=3, action_type="action", range=120,
                      aoe_radius=40, aoe_shape="cube", save_ability="Wisdom",
                      applies_condition="Slowed", concentration=True, duration="1 minute",
                      targets="aoe", half_on_save=False,
                      description="Up to 6 creatures: speed halved, -2 AC & DEX saves, "
                      "can't use more than one action + bonus action per turn."),
    
    "Revivify": SpellInfo("Revivify", level=3, action_type="action", range=0, targets="single",
                          description="Return dead to life with 1 HP (within 1 min)"),
    
    "Sleet Storm": SpellInfo("Sleet Storm", level=3, action_type="action", range=150, aoe_radius=40, aoe_shape="sphere",
                            targets="aoe", save_ability="Dexterity", applies_condition="Prone",
                            concentration=True, duration="1 minute",
                            creates_terrain="sleet_storm",
                            description="Difficult terrain. Heavily obscured. DEX save or fall prone."),

    "Spirit Guardians": SpellInfo("Spirit Guardians", level=3, action_type="action", range=0, aoe_radius=15, aoe_shape="sphere",
                                  damage_dice="3d8", damage_type="radiant", save_ability="Wisdom", half_on_save=True, targets="aoe",
                                  concentration=True, duration="10 minutes",
                                  creates_terrain="spirit_guardians"),

    "Stinking Cloud": SpellInfo("Stinking Cloud", level=3, action_type="action", range=90, aoe_radius=20, aoe_shape="sphere",
                                targets="aoe", save_ability="Constitution", applies_condition="Poisoned",
                                concentration=True, duration="1 minute",
                                creates_terrain="stinking_cloud",
                                description="Heavily obscured. CON save or spend action retching (Poisoned)."),
    
    "Vampiric Touch": SpellInfo("Vampiric Touch", level=3, action_type="action", range=5, targets="single",
                                damage_dice="3d6", damage_type="necrotic", concentration=True, duration="1 minute",
                                description="Heal half damage dealt"),

    # --- LEVEL 4 ---
    "Banishment": SpellInfo("Banishment", level=4, school="Abjuration", action_type="action", range=60, targets="single",
                            save_ability="Charisma", applies_condition="Banished", concentration=True, duration="1 minute", repeat_save=False,
                            description="Banishes creature to another plane. Target is Incapacitated."),

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
                              concentration=True, duration="1 minute",
                              creates_terrain="wall_fire"),

    # --- LEVEL 5 ---
    "Cloudkill": SpellInfo("Cloudkill", level=5, action_type="action", range=120, aoe_radius=20, aoe_shape="sphere",
                           damage_dice="5d8", damage_type="poison", save_ability="Constitution", half_on_save=True, targets="aoe",
                           concentration=True, duration="10 minutes",
                           creates_terrain="cloudkill"),
    
    "Cone of Cold": SpellInfo("Cone of Cold", level=5, action_type="action", range=60, aoe_radius=60, aoe_shape="cone",
                              damage_dice="8d8", damage_type="cold", save_ability="Constitution", half_on_save=True, targets="aoe"),
    
    "Flame Strike": SpellInfo("Flame Strike", level=5, action_type="action", range=60, aoe_radius=10, aoe_shape="cylinder",
                              damage_dice="4d6+4d6", damage_type="fire", save_ability="Dexterity", half_on_save=True, targets="aoe"),
    
    "Hold Monster": SpellInfo("Hold Monster", level=5, action_type="action", range=90, targets="single",
                              save_ability="Wisdom", applies_condition="Paralyzed", concentration=True, duration="1 minute"),
    
    "Mass Cure Wounds": SpellInfo("Mass Cure Wounds", level=5, action_type="action", range=60, heals="3d8+4", targets="aoe",
                                  aoe_radius=30, aoe_shape="sphere",
                                  description="Heal up to 6 creatures"),

    "Mass Healing Word": SpellInfo("Mass Healing Word", level=3, action_type="bonus", range=60,
                                   heals="1d4+4", targets="aoe", aoe_radius=60, aoe_shape="sphere",
                                   description="Bonus action: heal up to 6 creatures within 60ft. "
                                   "+1d4 healing per slot above 3rd."),

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

    "Wall of Thorns": SpellInfo("Wall of Thorns", level=6, action_type="action", range=120, aoe_radius=60, aoe_shape="line",
                                damage_dice="7d8", damage_type="piercing", save_ability="Dexterity", half_on_save=True,
                                targets="aoe", concentration=True, duration="10 minutes",
                                creates_terrain="wall_thorns",
                                description="Thorny wall. 7d8 piercing on enter/through (DEX save). Difficult terrain."),

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

    # ============================================================
    # XANATHAR'S GUIDE TO EVERYTHING (XGtE) SPELLS
    # ============================================================

    # --- CANTRIPS (XGtE) ---
    "Toll the Dead": SpellInfo("Toll the Dead", level=0, action_type="action", range=60, targets="single",
                               damage_dice="1d8", damage_type="necrotic", save_ability="Wisdom", half_on_save=False,
                               description="1d12 if target is missing HP. Scales at 5th/11th/17th."),

    "Primal Savagery": SpellInfo("Primal Savagery", level=0, action_type="action", range=5, targets="single",
                                 damage_dice="1d10", damage_type="acid",
                                 description="Teeth/nails become natural weapons. Scales at 5th/11th/17th."),

    "Sword Burst": SpellInfo("Sword Burst", level=0, action_type="action", range=5, aoe_radius=5, aoe_shape="sphere",
                             damage_dice="1d6", damage_type="force", save_ability="Dexterity", half_on_save=False,
                             targets="aoe", description="Spectral blades sweep around you. Scales."),

    "Word of Radiance": SpellInfo("Word of Radiance", level=0, action_type="action", range=5, aoe_radius=5,
                                  aoe_shape="sphere", damage_dice="1d6", damage_type="radiant",
                                  save_ability="Constitution", half_on_save=False, targets="aoe",
                                  description="Divine word burns nearby creatures. Cleric cantrip."),

    "Infestation": SpellInfo("Infestation", level=0, action_type="action", range=30, targets="single",
                             damage_dice="1d6", damage_type="poison", save_ability="Constitution", half_on_save=False,
                             description="On fail: target moves 5ft random direction."),

    # --- LEVEL 1 (XGtE) ---
    "Absorb Elements": SpellInfo("Absorb Elements", level=1, action_type="reaction", range=0, targets="self",
                                 description="Reaction to acid/cold/fire/lightning/thunder damage. Resistance until "
                                 "start of next turn. Next melee hit deals +1d6 of that type."),

    "Catapult": SpellInfo("Catapult", level=1, action_type="action", range=60, targets="single",
                          damage_dice="3d8", damage_type="bludgeoning", save_ability="Dexterity", half_on_save=False,
                          description="Hurl object 5lb. +1d8/slot above 1st."),

    "Chaos Bolt": SpellInfo("Chaos Bolt", level=1, action_type="action", range=120, targets="single",
                            damage_dice="2d8+1d6", damage_type="varies",
                            description="Random damage type. If d8s match, bolt leaps to new target."),

    "Earth Tremor": SpellInfo("Earth Tremor", level=1, action_type="action", range=0, aoe_radius=10, aoe_shape="sphere",
                              damage_dice="1d6", damage_type="bludgeoning", save_ability="Dexterity",
                              half_on_save=False, targets="aoe",
                              description="Ground shakes. On fail: prone + difficult terrain."),

    "Ice Knife": SpellInfo("Ice Knife", level=1, action_type="action", range=60, targets="single",
                           damage_dice="1d10+2d6", damage_type="cold",
                           description="Ranged attack for 1d10 piercing + 5ft AoE 2d6 cold (DEX save)."),

    "Zephyr Strike": SpellInfo("Zephyr Strike", level=1, action_type="bonus", range=0, targets="self",
                               concentration=True, duration="1 minute",
                               description="No OA for duration. Once: advantage on weapon attack + 1d8 force + 30ft speed."),

    "Armor of Agathys": SpellInfo("Armor of Agathys", level=1, action_type="action", range=0, targets="self",
                                  duration="1 hour",
                                  description="Gain 5 temp HP. While temp HP remains, melee attacker takes 5 cold damage. "
                                  "+5 temp HP and +5 damage per slot above 1st."),

    # --- LEVEL 2 (XGtE) ---
    "Aganazzar's Scorcher": SpellInfo("Aganazzar's Scorcher", level=2, action_type="action", range=30,
                                      aoe_radius=30, aoe_shape="line", damage_dice="3d8", damage_type="fire",
                                      save_ability="Dexterity", half_on_save=True, targets="aoe",
                                      description="30ft line of fire. +1d8/slot above 2nd."),

    "Dragon's Breath": SpellInfo("Dragon's Breath", level=2, action_type="bonus", range=0, targets="single",
                                 concentration=True, duration="1 minute",
                                 damage_dice="3d6", damage_type="fire", save_ability="Dexterity", half_on_save=True,
                                 description="Touch. Target can use action to exhale 15ft cone. Choose type."),

    "Healing Spirit": SpellInfo("Healing Spirit", level=2, action_type="bonus", range=60, targets="aoe",
                                concentration=True, duration="1 minute",
                                heals="1d6", description="Create spirit in 5ft cube. Heals 1d6 when creature enters/starts turn. "
                                "Max uses = 1+casting mod."),

    "Mind Spike": SpellInfo("Mind Spike", level=2, action_type="action", range=60, targets="single",
                            damage_dice="3d8", damage_type="psychic", save_ability="Wisdom", half_on_save=True,
                            concentration=True, duration="1 hour",
                            description="On fail: you know target's location for duration. +1d8/slot above 2nd."),

    "Shadow Blade": SpellInfo("Shadow Blade", level=2, action_type="bonus", range=0, targets="self",
                              concentration=True, duration="1 minute",
                              damage_dice="2d8", damage_type="psychic",
                              description="Create blade: simple melee, finesse, light, thrown 20/60. "
                              "Advantage in dim light/darkness. 3d8 at 3rd-4th, 4d8 at 5th-6th, 5d8 at 7th+."),

    # --- LEVEL 3 (XGtE) ---
    "Erupting Earth": SpellInfo("Erupting Earth", level=3, action_type="action", range=120,
                                aoe_radius=20, aoe_shape="cube", damage_dice="3d12", damage_type="bludgeoning",
                                save_ability="Dexterity", half_on_save=True, targets="aoe",
                                description="Ground erupts. Area becomes difficult terrain. +1d12/slot above 3rd."),

    "Life Transference": SpellInfo("Life Transference", level=3, action_type="action", range=30, targets="single",
                                   damage_dice="4d8", damage_type="necrotic",
                                   heals="0", description="Take 4d8 necrotic (can't reduce). "
                                   "Target heals 2x damage taken. +1d8/slot above 3rd."),

    "Thunder Step": SpellInfo("Thunder Step", level=3, action_type="action", range=90, targets="self",
                              damage_dice="3d10", damage_type="thunder", save_ability="Constitution",
                              half_on_save=True,
                              description="Teleport 90ft. Each creature within 10ft of origin makes save. "
                              "Can bring one willing creature. +1d10/slot above 3rd."),

    "Enemies Abound": SpellInfo("Enemies Abound", level=3, action_type="action", range=120, targets="single",
                                save_ability="Intelligence", concentration=True, duration="1 minute",
                                description="On fail: target perceives all creatures as enemies. "
                                "Attacks nearest creature randomly. Repeat save on damage."),

    "Catnap": SpellInfo("Catnap", level=3, action_type="action", range=30, targets="aoe",
                        description="Up to 3 willing creatures fall unconscious for 10 minutes. "
                        "They gain benefits of a short rest. +1 creature/slot above 3rd."),

    # --- LEVEL 4 (XGtE) ---
    "Shadow of Moil": SpellInfo("Shadow of Moil", level=4, action_type="action", range=0, targets="self",
                                concentration=True, duration="1 minute",
                                description="Darkness shrouds you: heavily obscured to others. "
                                "Resistance to radiant. When hit by attack within 10ft, attacker takes 2d8 necrotic."),

    "Sickening Radiance": SpellInfo("Sickening Radiance", level=4, action_type="action", range=120,
                                    aoe_radius=30, aoe_shape="sphere", damage_dice="4d10", damage_type="radiant",
                                    save_ability="Constitution", half_on_save=False, targets="aoe",
                                    concentration=True, duration="10 minutes",
                                    applies_condition="Exhaustion",
                                    description="On fail: 4d10 radiant + 1 exhaustion + emit dim light. "
                                    "Invisible creatures revealed."),

    "Vitriolic Sphere": SpellInfo("Vitriolic Sphere", level=4, action_type="action", range=150,
                                  aoe_radius=20, aoe_shape="sphere", damage_dice="10d4+5d4", damage_type="acid",
                                  save_ability="Dexterity", half_on_save=True, targets="aoe",
                                  description="10d4 acid + 5d4 acid at end of target's next turn on fail."),

    "Storm Sphere": SpellInfo("Storm Sphere", level=4, action_type="action", range=150,
                              aoe_radius=20, aoe_shape="sphere", damage_dice="2d6", damage_type="bludgeoning",
                              save_ability="Strength", half_on_save=True, targets="aoe",
                              concentration=True, duration="1 minute",
                              description="Difficult terrain in sphere. Bonus action: 4d6 lightning bolt from center."),

    "Elemental Bane": SpellInfo("Elemental Bane", level=4, action_type="action", range=90, targets="single",
                                save_ability="Constitution", concentration=True, duration="1 minute",
                                description="On fail: target loses resistance to chosen damage type. "
                                "Takes +2d6 of that type when hit."),

    # --- LEVEL 5 (XGtE) ---
    "Enervation": SpellInfo("Enervation", level=5, action_type="action", range=60, targets="single",
                            damage_dice="4d8", damage_type="necrotic", save_ability="Dexterity",
                            half_on_save=True, concentration=True, duration="1 minute",
                            description="On fail: 4d8 necrotic + heal half. Action each turn to continue."),

    "Holy Weapon": SpellInfo("Holy Weapon", level=5, action_type="bonus", range=0, targets="single",
                             concentration=True, duration="1 hour",
                             description="Weapon deals +2d8 radiant. Dismiss: 30ft AoE, "
                             "4d8 radiant (CON save, half on save) + Blinded for 1 min."),

    "Immolation": SpellInfo("Immolation", level=5, action_type="action", range=90, targets="single",
                            damage_dice="8d6", damage_type="fire", save_ability="Dexterity", half_on_save=True,
                            concentration=True, duration="1 minute",
                            description="On fail: 8d6 fire and on fire. 4d6 at start of each turn. "
                            "Repeat save each turn."),

    "Steel Wind Strike": SpellInfo("Steel Wind Strike", level=5, action_type="action", range=30, targets="aoe",
                                   damage_dice="6d10", damage_type="force",
                                   description="Melee spell attack vs up to 5 creatures within 30ft. "
                                   "6d10 force each on hit. Teleport to within 5ft of one target."),

    "Synaptic Static": SpellInfo("Synaptic Static", level=5, action_type="action", range=120,
                                 aoe_radius=20, aoe_shape="sphere", damage_dice="8d6", damage_type="psychic",
                                 save_ability="Intelligence", half_on_save=True, targets="aoe",
                                 description="On fail: -1d6 to attack rolls, ability checks, "
                                 "and concentration saves for 1 minute. INT save at end of turns."),

    "Wall of Light": SpellInfo("Wall of Light", level=5, action_type="action", range=120,
                               aoe_radius=60, aoe_shape="line", damage_dice="4d8", damage_type="radiant",
                               save_ability="Constitution", half_on_save=True, targets="aoe",
                               concentration=True, duration="10 minutes",
                               description="60x5x10ft wall. Creatures in wall: 4d8 radiant + Blinded. "
                               "Action: 4d8 radiant ranged spell attack from wall."),

    "Danse Macabre": SpellInfo("Danse Macabre", level=5, action_type="action", range=60, targets="aoe",
                               concentration=True, duration="1 hour",
                               description="Animate up to 5 Small/Medium corpses as zombies/skeletons. "
                               "They obey your mental commands. +2 creatures/slot above 5th."),

    # ============================================================
    # TASHA'S CAULDRON OF EVERYTHING (TCoE) SPELLS
    # ============================================================

    # --- CANTRIPS (TCoE) ---
    "Booming Blade": SpellInfo("Booming Blade", level=0, action_type="action", range=5, targets="single",
                               damage_dice="0", damage_type="thunder",
                               description="Melee weapon attack as part of spell. If target willingly "
                               "moves before your next turn: 1d8 thunder (2d8 at 5th, 3d8 at 11th, 4d8 at 17th)."),

    "Green-Flame Blade": SpellInfo("Green-Flame Blade", level=0, action_type="action", range=5, targets="single",
                                   damage_dice="0", damage_type="fire",
                                   description="Melee weapon attack. Fire leaps to adjacent creature: "
                                   "spellcasting mod fire. At 5th: +1d8 melee + 1d8+mod leap. Scales."),

    "Lightning Lure": SpellInfo("Lightning Lure", level=0, action_type="action", range=15, targets="single",
                                damage_dice="1d8", damage_type="lightning", save_ability="Strength",
                                half_on_save=False,
                                description="Pull target 10ft toward you. If pulled within 5ft: 1d8 lightning."),

    "Mind Sliver": SpellInfo("Mind Sliver", level=0, action_type="action", range=60, targets="single",
                             damage_dice="1d6", damage_type="psychic", save_ability="Intelligence",
                             half_on_save=False,
                             description="On fail: -1d4 from next saving throw before end of your next turn. Scales."),

    # --- LEVEL 1 (TCoE) ---
    "Silvery Barbs": SpellInfo("Silvery Barbs", level=1, action_type="reaction", range=60, targets="single",
                               description="Reaction: when creature within 60ft succeeds on attack/check/save, "
                               "force reroll (must use lower). Then choose an ally within 60ft: advantage on "
                               "next attack/check/save within 1 round."),

    "Tasha's Caustic Brew": SpellInfo("Tasha's Caustic Brew", level=1, action_type="action", range=0,
                                      aoe_radius=30, aoe_shape="line", damage_dice="2d4", damage_type="acid",
                                      save_ability="Dexterity", half_on_save=False, targets="aoe",
                                      concentration=True, duration="1 minute",
                                      description="30ft line. On fail: Blinded and 2d4 acid at start of each turn. "
                                      "Action to wipe off. +2d4/slot above 1st."),

    # --- LEVEL 2 (TCoE) ---
    "Tasha's Mind Whip": SpellInfo("Tasha's Mind Whip", level=2, action_type="action", range=90, targets="single",
                                   damage_dice="3d6", damage_type="psychic", save_ability="Intelligence",
                                   half_on_save=True,
                                   description="On fail: only one of action/bonus/movement on next turn, "
                                   "no reactions until end of next turn. +1 target/slot above 2nd."),

    "Kinetic Jaunt": SpellInfo("Kinetic Jaunt", level=2, action_type="bonus", range=0, targets="self",
                               concentration=True, duration="1 minute",
                               description="+10ft speed, no OA, move through creatures. "
                               "Occupied space is not difficult terrain."),

    "Wither and Bloom": SpellInfo("Wither and Bloom", level=2, action_type="action", range=60,
                                  aoe_radius=10, aoe_shape="sphere", damage_dice="2d6", damage_type="necrotic",
                                  save_ability="Constitution", half_on_save=True, targets="aoe",
                                  description="Enemies take 2d6 necrotic. One ally in area can spend a Hit Die "
                                  "to heal (roll die + spellcasting mod). +1d6/slot above 2nd."),

    # --- LEVEL 3 (TCoE) ---
    "Intellect Fortress": SpellInfo("Intellect Fortress", level=3, action_type="action", range=30, targets="single",
                                    concentration=True, duration="1 hour",
                                    description="Resistance to psychic damage. Advantage on INT/WIS/CHA saves. "
                                    "+1 creature/slot above 3rd."),

    "Spirit Shroud": SpellInfo("Spirit Shroud", level=3, action_type="bonus", range=0, targets="self",
                               concentration=True, duration="1 minute",
                               description="Attacks deal +1d8 radiant/necrotic/cold within 10ft. "
                               "Creatures hit can't regain HP until start of your next turn. "
                               "Enemies that start within 10ft: -10ft speed. +1d8/2 slots above 3rd."),

    "Summon Shadowspawn": SpellInfo("Summon Shadowspawn", level=3, action_type="action", range=90, targets="single",
                                    concentration=True, duration="1 hour",
                                    summon_name="Shadow Spirit", summon_hp=35, summon_ac=12,
                                    summon_damage_dice="1d12", summon_damage_type="psychic",
                                    summon_attack_bonus=5, summon_duration_rounds=100,
                                    description="Summon shadow spirit: Fury (adv after damage), "
                                    "Despair (frighten AoE), Fear (AoE dash away). +1 AC & +10 HP/slot above 3rd."),

    # --- LEVEL 4 (TCoE) ---
    "Summon Aberration": SpellInfo("Summon Aberration", level=4, action_type="action", range=90, targets="single",
                                   concentration=True, duration="1 hour",
                                   summon_name="Aberrant Spirit", summon_hp=40, summon_ac=11,
                                   summon_damage_dice="1d8+3", summon_damage_type="psychic",
                                   summon_attack_bonus=6, summon_duration_rounds=100,
                                   description="Beholderkin (ranged 1d8+3+2d8 psychic), "
                                   "Slaad (regen 5/turn), Star Spawn (psychic AoE). +1 AC & +10 HP/slot."),

    "Summon Construct": SpellInfo("Summon Construct", level=4, action_type="action", range=90, targets="single",
                                  concentration=True, duration="1 hour",
                                  summon_name="Construct Spirit", summon_hp=40, summon_ac=13,
                                  summon_damage_dice="1d8+4", summon_damage_type="bludgeoning",
                                  summon_attack_bonus=7, summon_duration_rounds=100,
                                  description="Clay (reduce damage by 1d4 reaction), Metal (Heated Body 1d4 fire), "
                                  "Stone (+2d6 on charge). +1 AC & +10 HP/slot above 4th."),

    # --- LEVEL 5 (TCoE) ---
    "Summon Draconic Spirit": SpellInfo("Summon Draconic Spirit", level=5, action_type="action", range=60,
                                        targets="single", concentration=True, duration="1 hour",
                                        summon_name="Draconic Spirit", summon_hp=50, summon_ac=14,
                                        summon_damage_dice="1d6+4", summon_damage_type="varies",
                                        summon_attack_bonus=8, summon_duration_rounds=100,
                                        description="Summon dragon: fly 60ft, multiattack (bite+claw), "
                                        "30ft cone breath 2d6 of chosen type (DEX save). Resistance to type. "
                                        "+10 HP and +1d6 breath/slot above 5th."),
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