"""Battle serialization – save/load helpers extracted from BattleSystem.

These are standalone functions that operate on a BattleSystem instance so the
main module stays smaller.  BattleSystem delegates to them:
    get_state_dict(battle) -> dict
    save_state(battle, filepath)
    restore_state(battle, data)
    battle_from_save(filepath, log_callback) -> BattleSystem
"""
import json
import os
import copy
from typing import Callable


def get_state_dict(battle) -> dict:
    """Serialize full combat state to a dictionary."""
    data = {
        "combat_started": battle.combat_started,
        "round": battle.round,
        "current_plane": battle.current_plane,
        "turn_index": battle.turn_index,
        "entities": [],
        "terrain": [t.to_dict() for t in battle.terrain],
        "weather": battle.weather,
        "lair_enabled": battle.lair_enabled,
        "background_image_path": getattr(battle, "background_image_path", ""),
        "background_alpha": getattr(battle, "background_alpha", 200),
        "background_world_cells_w": getattr(battle, "background_world_cells_w", 40),
        "background_world_cells_h": getattr(battle, "background_world_cells_h", 40),
        "background_offset_x": getattr(battle, "background_offset_x", 0),
        "background_offset_y": getattr(battle, "background_offset_y", 0),
        "ceiling_ft": getattr(battle, "ceiling_ft", 0),
    }
    for e in battle.entities:
        ent_data = {
            "name": e.name,
            "base_name": e.stats.name,
            "is_player": e.is_player,
            "grid_x": e.grid_x,
            "grid_y": e.grid_y,
            "hp": e.hp,
            "max_hp": e.max_hp,
            "temp_hp": e.temp_hp,
            "initiative": e.initiative,
            "conditions": list(e.conditions),
            "condition_metadata": copy.deepcopy(e.condition_metadata),
            "spell_slots": copy.deepcopy(e.spell_slots),
            "legendary_resistances_left": e.legendary_resistances_left,
            "legendary_actions_left": e.legendary_actions_left,
            "exhaustion": e.exhaustion,
            "feature_uses": copy.deepcopy(e.feature_uses),
            "action_used": e.action_used,
            "bonus_action_used": e.bonus_action_used,
            "reaction_used": e.reaction_used,
            "movement_left": e.movement_left,
            "concentrating_on": e.concentrating_on.name if e.concentrating_on else None,
            "death_save_successes": e.death_save_successes,
            "death_save_failures": e.death_save_failures,
            "is_stable": e.is_stable,
            "is_lair": e.is_lair,
            "lair_owner_name": e.lair_owner.name if e.lair_owner else None,
            "last_lair_action": e.last_lair_action,
            "active_effects": copy.deepcopy(e.active_effects),
            "notes": e.notes,
            "rage_active": e.rage_active,
            "rage_rounds": e.rage_rounds,
            "rages_left": e.rages_left,
            "ki_points_left": e.ki_points_left,
            "sorcery_points_left": e.sorcery_points_left,
            "lay_on_hands_left": e.lay_on_hands_left,
            "bardic_inspiration_left": e.bardic_inspiration_left,
            "is_summon": e.is_summon,
            "summon_rounds_left": e.summon_rounds_left,
            "summon_spell_name": e.summon_spell_name,
            "summon_owner_name": e.summon_owner.name if e.summon_owner else None,
            "marked_target_name": e.marked_target.name if e.marked_target else None,
            "death_save_history": e.death_save_history,
            "is_surprised": e.is_surprised,
            "grappling_names": [g.name for g in e.grappling] if e.grappling else [],
            "grappled_by_name": e.grappled_by.name if e.grappled_by else None,
            "condition_sources": {k: v.name for k, v in e.condition_sources.items()} if e.condition_sources else {},
            "elevation": e.elevation,
            "is_flying": e.is_flying,
            "is_climbing": e.is_climbing,
            "actor_id": getattr(e, "actor_id", ""),
        }
        data["entities"].append(ent_data)
    return data


def save_state(battle, filepath: str):
    """Serialize full combat state to JSON file."""
    data = get_state_dict(battle)
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)


def _restore_entity_fields(e, ent_data):
    """Apply saved fields to an Entity instance."""
    e.hp = ent_data["hp"]
    e.max_hp = ent_data["max_hp"]
    e.temp_hp = ent_data["temp_hp"]
    e.initiative = ent_data["initiative"]
    e.conditions = set(ent_data["conditions"])
    e.condition_metadata = ent_data.get("condition_metadata", {})
    e.spell_slots = ent_data["spell_slots"]
    e.legendary_resistances_left = ent_data["legendary_resistances_left"]
    e.legendary_actions_left = ent_data["legendary_actions_left"]
    e.exhaustion = ent_data["exhaustion"]
    e.feature_uses = ent_data["feature_uses"]
    e.action_used = ent_data["action_used"]
    e.bonus_action_used = ent_data["bonus_action_used"]
    e.reaction_used = ent_data["reaction_used"]
    e.movement_left = ent_data["movement_left"]
    e.death_save_successes = ent_data["death_save_successes"]
    e.death_save_failures = ent_data["death_save_failures"]
    e.is_stable = ent_data["is_stable"]
    e.is_lair = ent_data.get("is_lair", False)
    e.last_lair_action = ent_data.get("last_lair_action", "")
    e.active_effects = ent_data.get("active_effects", {})
    e.notes = ent_data.get("notes", "")
    e.is_surprised = ent_data.get("is_surprised", False)
    e.rage_active = ent_data.get("rage_active", False)
    e.rage_rounds = ent_data.get("rage_rounds", 0)
    e.rages_left = ent_data.get("rages_left", e.stats.rage_count)
    e.ki_points_left = ent_data.get("ki_points_left", e.stats.ki_points)
    e.sorcery_points_left = ent_data.get("sorcery_points_left", e.stats.sorcery_points)
    e.lay_on_hands_left = ent_data.get("lay_on_hands_left", e.stats.lay_on_hands_pool)
    e.bardic_inspiration_left = ent_data.get("bardic_inspiration_left", e.stats.bardic_inspiration_count)
    e.is_summon = ent_data.get("is_summon", False)
    e.summon_rounds_left = ent_data.get("summon_rounds_left", 0)
    e.summon_spell_name = ent_data.get("summon_spell_name", "")
    e.death_save_history = ent_data.get("death_save_history", [])
    e.elevation = ent_data.get("elevation", 0)
    e.is_flying = ent_data.get("is_flying", False)
    e.is_climbing = ent_data.get("is_climbing", False)
    e.actor_id = ent_data.get("actor_id", "")


def _resolve_stats(ent_data, hero_map, heroes):
    """Find the CreatureStats for a saved entity."""
    from data.library import library
    base_name = ent_data.get("base_name", ent_data["name"])
    stats = None

    if ent_data["is_player"]:
        stats = copy.deepcopy(hero_map.get(base_name))
        if stats is None:
            for h in heroes:
                if h.name in base_name or base_name in h.name:
                    stats = copy.deepcopy(h)
                    break
    else:
        if ent_data.get("is_lair"):
            from data.models import CreatureStats
            stats = CreatureStats(name="Lair Action", hit_points=1, speed=0, challenge_rating=0)
        else:
            try:
                stats = library.get_monster(base_name)
            except ValueError:
                stripped = base_name.rsplit(" ", 1)[0]
                try:
                    stats = library.get_monster(stripped)
                except ValueError:
                    pass
    return stats, base_name


def _link_entity_refs(entities, data):
    """Restore cross-entity references (lair owners, summons, grapple, etc.)."""
    entity_by_name = {e.name: e for e in entities}
    for ent_data in data["entities"]:
        ent = entity_by_name.get(ent_data["name"])
        if ent is None:
            continue

        owner_name = ent_data.get("lair_owner_name")
        if owner_name:
            ent.lair_owner = entity_by_name.get(owner_name)

        summon_owner_name = ent_data.get("summon_owner_name")
        if summon_owner_name:
            ent.summon_owner = entity_by_name.get(summon_owner_name)

        marked_name = ent_data.get("marked_target_name")
        if marked_name:
            ent.marked_target = entity_by_name.get(marked_name)

        grappled_by_name = ent_data.get("grappled_by_name")
        if grappled_by_name:
            grappler = entity_by_name.get(grappled_by_name)
            if grappler:
                ent.grappled_by = grappler

        for gname in ent_data.get("grappling_names", []):
            target = entity_by_name.get(gname)
            if target:
                ent.grappling.append(target)

        for cond, source_name in ent_data.get("condition_sources", {}).items():
            source = entity_by_name.get(source_name)
            if source:
                ent.condition_sources[cond] = source


def _restore_concentration(e, ent_data, stats):
    """Restore concentration spell reference."""
    conc_name = ent_data.get("concentrating_on")
    if conc_name:
        for sp in list(stats.spells_known) + list(stats.cantrips):
            if sp.name == conc_name:
                e.concentrating_on = sp
                break


def restore_state(battle, data: dict):
    """Restore state from dictionary onto an existing BattleSystem."""
    from data.heroes import hero_list as heroes
    from engine.terrain import TerrainObject
    from engine.entities import Entity

    battle.round = data.get("round", 1)
    battle.combat_started = data.get("combat_started", True)
    battle.current_plane = data.get("current_plane", "Material Plane")
    battle.turn_index = data.get("turn_index", 0)
    battle.weather = data.get("weather", "Clear")
    battle.background_image_path = data.get("background_image_path", "")
    battle.background_alpha = data.get("background_alpha", 200)
    battle.background_world_cells_w = data.get("background_world_cells_w", 40)
    battle.background_world_cells_h = data.get("background_world_cells_h", 40)
    battle.background_offset_x = data.get("background_offset_x", 0)
    battle.background_offset_y = data.get("background_offset_y", 0)
    battle.ceiling_ft = data.get("ceiling_ft", 0)
    battle.terrain = [TerrainObject.from_dict(t) for t in data.get("terrain", [])]
    battle.entities = []
    battle.pending_reactions = []
    battle.legendary_queue = []

    hero_map = {h.name: h for h in heroes}

    for ent_data in data["entities"]:
        stats, base_name = _resolve_stats(ent_data, hero_map, heroes)
        if stats is None:
            from data.models import CreatureStats
            stats = CreatureStats(name=ent_data["name"], hit_points=ent_data["max_hp"])
        stats.name = ent_data["name"]
        e = Entity(stats, ent_data["grid_x"], ent_data["grid_y"], ent_data["is_player"])
        _restore_entity_fields(e, ent_data)
        _restore_concentration(e, ent_data, stats)
        battle.entities.append(e)

    _link_entity_refs(battle.entities, data)


def battle_from_save(filepath: str, log_callback: Callable[[str], None]):
    """Reconstruct a BattleSystem from a saved JSON file."""
    from data.heroes import hero_list as heroes
    from engine.terrain import TerrainObject
    from engine.entities import Entity
    from engine.ai import TacticalAI
    from engine.battle_stats import BattleStatisticsTracker
    from engine.dm_advisor import DMAdvisor
    from engine.win_probability import WinProbabilityCalculator

    # Import BattleSystem lazily to avoid circular import
    from engine.battle import BattleSystem

    with open(filepath) as f:
        data = json.load(f)

    sys_obj = object.__new__(BattleSystem)
    sys_obj.grid_size = 60
    sys_obj.entities = []
    sys_obj.log = log_callback
    sys_obj.round = data.get("round", 1)
    sys_obj.combat_started = data.get("combat_started", True)
    sys_obj.current_plane = data.get("current_plane", "Material Plane")
    sys_obj.turn_index = data.get("turn_index", 0)
    sys_obj.ai = TacticalAI()
    sys_obj.terrain = []
    sys_obj.weather = data.get("weather", "Clear")
    sys_obj.background_image_path = data.get("background_image_path", "")
    sys_obj.background_alpha = data.get("background_alpha", 200)
    sys_obj.background_world_cells_w = data.get("background_world_cells_w", 40)
    sys_obj.background_world_cells_h = data.get("background_world_cells_h", 40)
    sys_obj.background_offset_x = data.get("background_offset_x", 0)
    sys_obj.background_offset_y = data.get("background_offset_y", 0)
    sys_obj.ceiling_ft = data.get("ceiling_ft", 0)
    sys_obj.pending_reactions = []
    sys_obj.legendary_queue = []
    sys_obj.lair_enabled = data.get("lair_enabled", False)

    hero_map = {h.name: h for h in heroes}

    for ent_data in data["entities"]:
        stats, base_name = _resolve_stats(ent_data, hero_map, heroes)
        if stats is None:
            log_callback(f"[LOAD] Could not find stats for '{base_name}', skipping.")
            continue
        stats.name = ent_data["name"]
        e = Entity(stats, ent_data["grid_x"], ent_data["grid_y"], ent_data["is_player"])
        _restore_entity_fields(e, ent_data)
        _restore_concentration(e, ent_data, stats)
        sys_obj.entities.append(e)

    _link_entity_refs(sys_obj.entities, data)

    sys_obj.turn_index = min(sys_obj.turn_index, max(0, len(sys_obj.entities) - 1))
    sys_obj.terrain = [TerrainObject.from_dict(t) for t in data.get("terrain", [])]
    sys_obj.stats_tracker = BattleStatisticsTracker()
    sys_obj.dm_advisor = DMAdvisor()
    sys_obj.win_calculator = WinProbabilityCalculator()
    sys_obj._last_damage_source = ""

    log_callback(f"=== ENCOUNTER LOADED (Round {sys_obj.round}) ===")
    return sys_obj
