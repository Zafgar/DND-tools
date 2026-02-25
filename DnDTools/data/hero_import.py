"""
Hero Import/Export – JSON-based system for importing and exporting player characters.
Supports importing from JSON files and exporting existing heroes for sharing.
"""
import json
import os
import copy
from typing import List, Optional
from data.models import (
    CreatureStats, AbilityScores, Action, SpellInfo, Feature,
    RacialTrait, Item
)


def export_hero(hero: CreatureStats) -> dict:
    """Export a CreatureStats hero to a JSON-serializable dictionary."""
    return {
        "name": hero.name,
        "size": hero.size,
        "creature_type": hero.creature_type,
        "native_plane": hero.native_plane,
        "alignment": hero.alignment,
        "armor_class": hero.armor_class,
        "armor_type": hero.armor_type,
        "hit_points": hero.hit_points,
        "hit_dice": hero.hit_dice,
        "speed": hero.speed,
        "fly_speed": hero.fly_speed,
        "swim_speed": hero.swim_speed,
        "climb_speed": hero.climb_speed,
        "burrow_speed": hero.burrow_speed,
        "abilities": {
            "strength": hero.abilities.strength,
            "dexterity": hero.abilities.dexterity,
            "constitution": hero.abilities.constitution,
            "intelligence": hero.abilities.intelligence,
            "wisdom": hero.abilities.wisdom,
            "charisma": hero.abilities.charisma,
        },
        "saving_throws": hero.saving_throws,
        "skills": hero.skills,
        "damage_immunities": hero.damage_immunities,
        "damage_resistances": hero.damage_resistances,
        "damage_vulnerabilities": hero.damage_vulnerabilities,
        "condition_immunities": hero.condition_immunities,
        "senses": hero.senses,
        "languages": hero.languages,
        "challenge_rating": hero.challenge_rating,
        "xp": hero.xp,
        "proficiency_bonus": hero.proficiency_bonus,
        "character_class": hero.character_class,
        "character_level": hero.character_level,
        "race": hero.race,
        "subclass": hero.subclass,
        # Resource pools
        "ki_points": hero.ki_points,
        "sorcery_points": hero.sorcery_points,
        "lay_on_hands_pool": hero.lay_on_hands_pool,
        "rage_count": hero.rage_count,
        "bardic_inspiration_dice": hero.bardic_inspiration_dice,
        "bardic_inspiration_count": hero.bardic_inspiration_count,
        "base_ac_unarmored": hero.base_ac_unarmored,
        # Spellcasting
        "spellcasting_ability": hero.spellcasting_ability,
        "spell_save_dc": hero.spell_save_dc,
        "spell_attack_bonus": hero.spell_attack_bonus,
        "spell_slots": hero.spell_slots,
        "legendary_action_count": hero.legendary_action_count,
        "legendary_resistance_count": hero.legendary_resistance_count,
        # Complex fields
        "actions": [_export_action(a) for a in hero.actions],
        "bonus_actions": [_export_action(a) for a in hero.bonus_actions],
        "reactions": [_export_action(a) for a in hero.reactions],
        "spells_known": [_export_spell(s) for s in hero.spells_known],
        "cantrips": [_export_spell(s) for s in hero.cantrips],
        "features": [_export_feature(f) for f in hero.features],
        "racial_traits": [_export_racial_trait(r) for r in hero.racial_traits],
        "items": [_export_item(i) for i in hero.items],
    }


def _export_action(action: Action) -> dict:
    return {
        "name": action.name,
        "description": action.description,
        "attack_bonus": action.attack_bonus,
        "damage_dice": action.damage_dice,
        "damage_bonus": action.damage_bonus,
        "damage_type": action.damage_type,
        "range": action.range,
        "action_type": action.action_type,
        "is_multiattack": action.is_multiattack,
        "multiattack_count": action.multiattack_count,
        "multiattack_targets": action.multiattack_targets,
        "reach": action.reach,
        "applies_condition": action.applies_condition,
        "condition_save": action.condition_save,
        "condition_dc": action.condition_dc,
        "aoe_radius": action.aoe_radius,
        "aoe_shape": action.aoe_shape,
    }


def _export_spell(spell: SpellInfo) -> dict:
    return {
        "name": spell.name,
        "level": spell.level,
        "school": spell.school,
        "action_type": spell.action_type,
        "range": spell.range,
        "aoe_radius": spell.aoe_radius,
        "aoe_shape": spell.aoe_shape,
        "damage_dice": spell.damage_dice,
        "damage_type": spell.damage_type,
        "damage_scaling": spell.damage_scaling,
        "save_ability": spell.save_ability,
        "save_dc_fixed": spell.save_dc_fixed,
        "attack_bonus_fixed": spell.attack_bonus_fixed,
        "applies_condition": spell.applies_condition,
        "condition_on_save": spell.condition_on_save,
        "repeat_save": spell.repeat_save,
        "heals": spell.heals,
        "targets": spell.targets,
        "concentration": spell.concentration,
        "duration": spell.duration,
        "description": spell.description,
        "half_on_save": spell.half_on_save,
        "summon_name": spell.summon_name,
        "summon_hp": spell.summon_hp,
        "summon_ac": spell.summon_ac,
        "summon_damage_dice": spell.summon_damage_dice,
        "summon_damage_type": spell.summon_damage_type,
        "summon_attack_bonus": spell.summon_attack_bonus,
        "summon_duration_rounds": spell.summon_duration_rounds,
        "bonus_damage_dice": spell.bonus_damage_dice,
        "bonus_damage_type": spell.bonus_damage_type,
    }


def _export_feature(feat: Feature) -> dict:
    return {
        "name": feat.name,
        "description": feat.description,
        "feature_type": feat.feature_type,
        "uses_per_day": feat.uses_per_day,
        "legendary_cost": feat.legendary_cost,
        "recharge": feat.recharge,
        "aura_radius": feat.aura_radius,
        "save_dc": feat.save_dc,
        "save_ability": feat.save_ability,
        "applies_condition": feat.applies_condition,
        "damage_dice": feat.damage_dice,
        "damage_type": feat.damage_type,
        "mechanic": feat.mechanic,
        "mechanic_value": feat.mechanic_value,
        "short_rest_recharge": feat.short_rest_recharge,
    }


def _export_racial_trait(trait: RacialTrait) -> dict:
    return {
        "name": trait.name,
        "description": trait.description,
        "mechanic": trait.mechanic,
        "mechanic_value": trait.mechanic_value,
        "uses_per_day": trait.uses_per_day,
        "damage_dice": trait.damage_dice,
        "damage_type": trait.damage_type,
        "save_dc": trait.save_dc,
        "save_ability": trait.save_ability,
    }


def _export_item(item: Item) -> dict:
    return {
        "name": item.name,
        "item_type": item.item_type,
        "uses": item.uses,
        "description": item.description,
        "heals": item.heals,
        "damage_dice": item.damage_dice,
        "applies_condition": item.applies_condition,
        "buff": item.buff,
    }


# ------------------------------------------------------------------ #
# Import                                                               #
# ------------------------------------------------------------------ #

def import_hero(data: dict) -> CreatureStats:
    """Import a hero from a dictionary (parsed JSON)."""
    abilities_data = data.get("abilities", {})
    abilities = AbilityScores(
        strength=abilities_data.get("strength", 10),
        dexterity=abilities_data.get("dexterity", 10),
        constitution=abilities_data.get("constitution", 10),
        intelligence=abilities_data.get("intelligence", 10),
        wisdom=abilities_data.get("wisdom", 10),
        charisma=abilities_data.get("charisma", 10),
    )

    hero = CreatureStats(
        name=data.get("name", "Imported Hero"),
        size=data.get("size", "Medium"),
        creature_type=data.get("creature_type", "Humanoid"),
        native_plane=data.get("native_plane", "Material Plane"),
        alignment=data.get("alignment", "Neutral"),
        armor_class=data.get("armor_class", 10),
        armor_type=data.get("armor_type", ""),
        hit_points=data.get("hit_points", 10),
        hit_dice=data.get("hit_dice", ""),
        speed=data.get("speed", 30),
        fly_speed=data.get("fly_speed", 0),
        swim_speed=data.get("swim_speed", 0),
        climb_speed=data.get("climb_speed", 0),
        burrow_speed=data.get("burrow_speed", 0),
        abilities=abilities,
        saving_throws=data.get("saving_throws", {}),
        skills=data.get("skills", {}),
        damage_immunities=data.get("damage_immunities", []),
        damage_resistances=data.get("damage_resistances", []),
        damage_vulnerabilities=data.get("damage_vulnerabilities", []),
        condition_immunities=data.get("condition_immunities", []),
        senses=data.get("senses", ""),
        languages=data.get("languages", ""),
        challenge_rating=data.get("challenge_rating", 0.0),
        xp=data.get("xp", 0),
        proficiency_bonus=data.get("proficiency_bonus", 2),
        character_class=data.get("character_class", ""),
        character_level=data.get("character_level", 0),
        race=data.get("race", ""),
        subclass=data.get("subclass", ""),
        ki_points=data.get("ki_points", 0),
        sorcery_points=data.get("sorcery_points", 0),
        lay_on_hands_pool=data.get("lay_on_hands_pool", 0),
        rage_count=data.get("rage_count", 0),
        bardic_inspiration_dice=data.get("bardic_inspiration_dice", ""),
        bardic_inspiration_count=data.get("bardic_inspiration_count", 0),
        base_ac_unarmored=data.get("base_ac_unarmored", False),
        spellcasting_ability=data.get("spellcasting_ability", ""),
        spell_save_dc=data.get("spell_save_dc", 0),
        spell_attack_bonus=data.get("spell_attack_bonus", 0),
        spell_slots=data.get("spell_slots", {}),
        legendary_action_count=data.get("legendary_action_count", 0),
        legendary_resistance_count=data.get("legendary_resistance_count", 0),
        actions=[_import_action(a) for a in data.get("actions", [])],
        bonus_actions=[_import_action(a) for a in data.get("bonus_actions", [])],
        reactions=[_import_action(a) for a in data.get("reactions", [])],
        spells_known=[_import_spell(s) for s in data.get("spells_known", [])],
        cantrips=[_import_spell(s) for s in data.get("cantrips", [])],
        features=[_import_feature(f) for f in data.get("features", [])],
        racial_traits=[_import_racial_trait(r) for r in data.get("racial_traits", [])],
        items=[_import_item(i) for i in data.get("items", [])],
    )
    return hero


def _import_action(data: dict) -> Action:
    return Action(
        name=data.get("name", "Attack"),
        description=data.get("description", ""),
        attack_bonus=data.get("attack_bonus", 0),
        damage_dice=data.get("damage_dice", "1d4"),
        damage_bonus=data.get("damage_bonus", 0),
        damage_type=data.get("damage_type", "bludgeoning"),
        range=data.get("range", 5),
        action_type=data.get("action_type", "action"),
        is_multiattack=data.get("is_multiattack", False),
        multiattack_count=data.get("multiattack_count", 1),
        multiattack_targets=data.get("multiattack_targets", []),
        reach=data.get("reach", 5),
        applies_condition=data.get("applies_condition", ""),
        condition_save=data.get("condition_save", ""),
        condition_dc=data.get("condition_dc", 0),
        aoe_radius=data.get("aoe_radius", 0),
        aoe_shape=data.get("aoe_shape", ""),
    )


def _import_spell(data: dict) -> SpellInfo:
    return SpellInfo(
        name=data.get("name", "Spell"),
        level=data.get("level", 0),
        school=data.get("school", "Evocation"),
        action_type=data.get("action_type", "action"),
        range=data.get("range", 60),
        aoe_radius=data.get("aoe_radius", 0),
        aoe_shape=data.get("aoe_shape", ""),
        damage_dice=data.get("damage_dice", ""),
        damage_type=data.get("damage_type", "fire"),
        damage_scaling=data.get("damage_scaling", ""),
        save_ability=data.get("save_ability", ""),
        save_dc_fixed=data.get("save_dc_fixed", 0),
        attack_bonus_fixed=data.get("attack_bonus_fixed", 0),
        applies_condition=data.get("applies_condition", ""),
        condition_on_save=data.get("condition_on_save", False),
        repeat_save=data.get("repeat_save", True),
        heals=data.get("heals", ""),
        targets=data.get("targets", "single"),
        concentration=data.get("concentration", False),
        duration=data.get("duration", ""),
        description=data.get("description", ""),
        half_on_save=data.get("half_on_save", True),
        summon_name=data.get("summon_name", ""),
        summon_hp=data.get("summon_hp", 0),
        summon_ac=data.get("summon_ac", 10),
        summon_damage_dice=data.get("summon_damage_dice", ""),
        summon_damage_type=data.get("summon_damage_type", ""),
        summon_attack_bonus=data.get("summon_attack_bonus", 0),
        summon_duration_rounds=data.get("summon_duration_rounds", 10),
        bonus_damage_dice=data.get("bonus_damage_dice", ""),
        bonus_damage_type=data.get("bonus_damage_type", ""),
    )


def _import_feature(data: dict) -> Feature:
    return Feature(
        name=data.get("name", "Feature"),
        description=data.get("description", ""),
        feature_type=data.get("feature_type", "passive"),
        uses_per_day=data.get("uses_per_day", -1),
        legendary_cost=data.get("legendary_cost", 1),
        recharge=data.get("recharge", ""),
        aura_radius=data.get("aura_radius", 0),
        save_dc=data.get("save_dc", 0),
        save_ability=data.get("save_ability", ""),
        applies_condition=data.get("applies_condition", ""),
        damage_dice=data.get("damage_dice", ""),
        damage_type=data.get("damage_type", ""),
        mechanic=data.get("mechanic", ""),
        mechanic_value=data.get("mechanic_value", ""),
        short_rest_recharge=data.get("short_rest_recharge", False),
    )


def _import_racial_trait(data: dict) -> RacialTrait:
    return RacialTrait(
        name=data.get("name", "Trait"),
        description=data.get("description", ""),
        mechanic=data.get("mechanic", ""),
        mechanic_value=data.get("mechanic_value", ""),
        uses_per_day=data.get("uses_per_day", -1),
        damage_dice=data.get("damage_dice", ""),
        damage_type=data.get("damage_type", ""),
        save_dc=data.get("save_dc", 0),
        save_ability=data.get("save_ability", ""),
    )


def _import_item(data: dict) -> Item:
    return Item(
        name=data.get("name", "Item"),
        item_type=data.get("item_type", "potion"),
        uses=data.get("uses", 1),
        description=data.get("description", ""),
        heals=data.get("heals", ""),
        damage_dice=data.get("damage_dice", ""),
        applies_condition=data.get("applies_condition", ""),
        buff=data.get("buff", ""),
    )


# ------------------------------------------------------------------ #
# File I/O                                                             #
# ------------------------------------------------------------------ #

def export_hero_to_file(hero: CreatureStats, filepath: str):
    """Export hero to a JSON file."""
    data = export_hero(hero)
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)


def import_hero_from_file(filepath: str) -> CreatureStats:
    """Import a hero from a JSON file."""
    with open(filepath) as f:
        data = json.load(f)
    return import_hero(data)


def import_heroes_from_file(filepath: str) -> List[CreatureStats]:
    """Import multiple heroes from a JSON file (supports both single and array)."""
    with open(filepath) as f:
        data = json.load(f)
    if isinstance(data, list):
        return [import_hero(h) for h in data]
    return [import_hero(data)]


def export_heroes_to_file(heroes: List[CreatureStats], filepath: str):
    """Export multiple heroes to a JSON file."""
    data = [export_hero(h) for h in heroes]
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)
