"""
Campaign ↔ Battle Bridge – Syncs state between Campaign and Battle.

After combat ends, this module updates the campaign's party members with:
- Current HP, temp HP
- Conditions
- Spell slots used
- Feature uses consumed
- Exhaustion levels
- Death save state
"""
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from engine.entities import Entity
    from data.campaign import Campaign, PartyMember


def sync_battle_results_to_campaign(
    campaign: "Campaign",
    battle_entities: List["Entity"],
):
    """After combat ends, update campaign party with battle results.

    Matches battle entities to campaign party members by name
    and syncs HP, conditions, spell slots, and resource usage.
    """
    from data.hero_import import export_hero

    for member in campaign.party:
        if not member.active or not member.hero_data:
            continue

        hero_name = member.hero_data.get("name", "")
        if not hero_name:
            continue

        # Find matching entity from battle
        entity = _find_entity_by_name(battle_entities, hero_name)
        if entity is None:
            continue

        # Sync HP state
        member.current_hp = max(0, entity.hp)
        member.temp_hp = entity.temp_hp

        # Sync conditions (exclude combat-only conditions)
        combat_only = {"Dodge", "Hasted", "Concentration"}
        member.conditions = [
            c for c in entity.conditions
            if c not in combat_only
        ]

        # Sync exhaustion
        member.exhaustion = getattr(entity, 'exhaustion', 0)

        # Sync death saves
        member.death_saves = {
            "success": getattr(entity, 'death_save_successes', 0),
            "failure": getattr(entity, 'death_save_failures', 0),
        }

        # Sync spell slot usage
        if entity.stats.spell_slots:
            used = {}
            for level_str, max_slots in entity.stats.spell_slots.items():
                current = entity.spell_slots.get(level_str, max_slots)
                used_count = max_slots - current
                if used_count > 0:
                    used[level_str] = used_count
            member.spell_slots_used = used

        # Sync feature uses (track what was used)
        used_features = {}
        for feat in entity.stats.features:
            if feat.uses_per_day > 0 and feat.name:
                remaining = entity.feature_uses.get(feat.name, feat.uses_per_day)
                used_count = feat.uses_per_day - remaining
                if used_count > 0:
                    used_features[feat.name] = used_count
        member.feature_uses_used = used_features

        # Update hero_data with any stat changes (e.g., gained items)
        member.hero_data = export_hero(entity.stats)


def _find_entity_by_name(entities: list, name: str) -> Optional["Entity"]:
    """Find entity by name, case-insensitive."""
    for entity in entities:
        if entity.is_player and entity.name.lower() == name.lower():
            return entity
    return None


def get_campaign_from_manager(manager) -> Optional["Campaign"]:
    """Get the active campaign from the GameManager, if any."""
    campaign_state = manager.states.get("CAMPAIGN")
    if campaign_state and hasattr(campaign_state, 'campaign'):
        return campaign_state.campaign
    return None
