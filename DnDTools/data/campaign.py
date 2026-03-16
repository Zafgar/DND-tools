"""
Campaign Management System - Data model and persistence.
Campaigns hold a party of heroes, encounters, areas, notes, and settings.
JSON-based save/load for full campaign state.
"""
import json
import os
import copy
import time
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from data.models import CreatureStats, Item
from data.hero_import import export_hero, import_hero_from_file
from data.items import get_item


CAMPAIGNS_DIR = os.path.join(os.path.dirname(__file__), "..", "campaigns")


@dataclass
class CampaignNote:
    """A note attached to a hero, encounter, or the campaign itself."""
    text: str = ""
    timestamp: str = ""
    category: str = "general"  # general, combat, lore, quest, loot


@dataclass
class EncounterSlot:
    """A creature slot in a pre-built encounter (name + count + side)."""
    creature_name: str = ""       # Name to look up in heroes or monster library
    count: int = 1
    side: str = "enemy"           # "enemy", "ally", "neutral"
    is_hero: bool = False         # True = look up in party/hero_list, False = monster library
    notes: str = ""


@dataclass
class CampaignEncounter:
    """A pre-built encounter within a campaign."""
    name: str = "New Encounter"
    description: str = ""
    area_name: str = ""           # Which area this encounter belongs to
    slots: List[EncounterSlot] = field(default_factory=list)
    loot_items: List[str] = field(default_factory=list)  # Item names from items.py
    notes: str = ""
    completed: bool = False
    difficulty_hint: str = ""     # "Easy", "Medium", "Hard", "Deadly"


@dataclass
class CampaignArea:
    """A named area/location within the campaign."""
    name: str = "New Area"
    description: str = ""
    environment: str = "outdoor"  # outdoor, indoor, underground, underwater
    lighting: str = "bright"      # bright, dim, darkness
    notes: str = ""
    encounter_names: List[str] = field(default_factory=list)


@dataclass
class PartyMember:
    """Wrapper for a hero in the campaign party with campaign-specific state."""
    hero_data: dict = field(default_factory=dict)  # Serialized CreatureStats
    notes: str = ""
    active: bool = True           # False = inactive/away from party
    current_hp: int = -1          # -1 = use hero's max HP
    temp_hp: int = 0
    conditions: List[str] = field(default_factory=list)
    spell_slots_used: Dict[str, int] = field(default_factory=dict)
    feature_uses_used: Dict[str, int] = field(default_factory=dict)
    exhaustion: int = 0
    death_saves: Dict[str, int] = field(default_factory=lambda: {"success": 0, "failure": 0})
    custom_items: List[str] = field(default_factory=list)  # Extra item names beyond class defaults


@dataclass
class Campaign:
    """Top-level campaign data."""
    name: str = "New Campaign"
    description: str = ""
    created: str = ""
    last_modified: str = ""
    # Party
    party: List[PartyMember] = field(default_factory=list)
    # World state
    time_of_day: str = "day"      # day, dawn, dusk, night
    current_area: str = ""
    session_number: int = 1
    # Encounters & Areas
    encounters: List[CampaignEncounter] = field(default_factory=list)
    areas: List[CampaignArea] = field(default_factory=list)
    # Campaign-level notes
    notes: List[CampaignNote] = field(default_factory=list)
    # Settings
    settings: Dict = field(default_factory=lambda: {
        "variant_healing_potions": True,   # Potions as bonus action
        "variant_encumbrance": False,
        "flanking_advantage": False,
    })


def _timestamp():
    return time.strftime("%Y-%m-%d %H:%M:%S")


# ============================================================================
# SERIALIZATION
# ============================================================================

def _serialize_note(note: CampaignNote) -> dict:
    return {"text": note.text, "timestamp": note.timestamp, "category": note.category}

def _deserialize_note(d: dict) -> CampaignNote:
    return CampaignNote(text=d.get("text", ""), timestamp=d.get("timestamp", ""),
                        category=d.get("category", "general"))

def _serialize_slot(slot: EncounterSlot) -> dict:
    return {
        "creature_name": slot.creature_name, "count": slot.count,
        "side": slot.side, "is_hero": slot.is_hero, "notes": slot.notes,
    }

def _deserialize_slot(d: dict) -> EncounterSlot:
    return EncounterSlot(**{k: d[k] for k in d if k in EncounterSlot.__dataclass_fields__})

def _serialize_encounter(enc: CampaignEncounter) -> dict:
    return {
        "name": enc.name, "description": enc.description, "area_name": enc.area_name,
        "slots": [_serialize_slot(s) for s in enc.slots],
        "loot_items": enc.loot_items, "notes": enc.notes,
        "completed": enc.completed, "difficulty_hint": enc.difficulty_hint,
    }

def _deserialize_encounter(d: dict) -> CampaignEncounter:
    return CampaignEncounter(
        name=d.get("name", ""), description=d.get("description", ""),
        area_name=d.get("area_name", ""),
        slots=[_deserialize_slot(s) for s in d.get("slots", [])],
        loot_items=d.get("loot_items", []), notes=d.get("notes", ""),
        completed=d.get("completed", False), difficulty_hint=d.get("difficulty_hint", ""),
    )

def _serialize_area(area: CampaignArea) -> dict:
    return {
        "name": area.name, "description": area.description,
        "environment": area.environment, "lighting": area.lighting,
        "notes": area.notes, "encounter_names": area.encounter_names,
    }

def _deserialize_area(d: dict) -> CampaignArea:
    return CampaignArea(
        name=d.get("name", ""), description=d.get("description", ""),
        environment=d.get("environment", "outdoor"), lighting=d.get("lighting", "bright"),
        notes=d.get("notes", ""), encounter_names=d.get("encounter_names", []),
    )

def _serialize_member(m: PartyMember) -> dict:
    return {
        "hero_data": m.hero_data, "notes": m.notes, "active": m.active,
        "current_hp": m.current_hp, "temp_hp": m.temp_hp,
        "conditions": m.conditions,
        "spell_slots_used": m.spell_slots_used,
        "feature_uses_used": m.feature_uses_used,
        "exhaustion": m.exhaustion, "death_saves": m.death_saves,
        "custom_items": m.custom_items,
    }

def _deserialize_member(d: dict) -> PartyMember:
    return PartyMember(
        hero_data=d.get("hero_data", {}), notes=d.get("notes", ""),
        active=d.get("active", True), current_hp=d.get("current_hp", -1),
        temp_hp=d.get("temp_hp", 0), conditions=d.get("conditions", []),
        spell_slots_used=d.get("spell_slots_used", {}),
        feature_uses_used=d.get("feature_uses_used", {}),
        exhaustion=d.get("exhaustion", 0),
        death_saves=d.get("death_saves", {"success": 0, "failure": 0}),
        custom_items=d.get("custom_items", []),
    )


def save_campaign(campaign: Campaign, filepath: str = ""):
    """Save campaign to JSON file."""
    if not filepath:
        os.makedirs(CAMPAIGNS_DIR, exist_ok=True)
        safe_name = "".join(c if c.isalnum() or c in " -_" else "_" for c in campaign.name)
        filepath = os.path.join(CAMPAIGNS_DIR, f"{safe_name}.json")

    campaign.last_modified = _timestamp()
    if not campaign.created:
        campaign.created = campaign.last_modified

    data = {
        "name": campaign.name,
        "description": campaign.description,
        "created": campaign.created,
        "last_modified": campaign.last_modified,
        "party": [_serialize_member(m) for m in campaign.party],
        "time_of_day": campaign.time_of_day,
        "current_area": campaign.current_area,
        "session_number": campaign.session_number,
        "encounters": [_serialize_encounter(e) for e in campaign.encounters],
        "areas": [_serialize_area(a) for a in campaign.areas],
        "notes": [_serialize_note(n) for n in campaign.notes],
        "settings": campaign.settings,
    }

    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)
    return filepath


def load_campaign(filepath: str) -> Campaign:
    """Load campaign from JSON file."""
    with open(filepath) as f:
        data = json.load(f)

    return Campaign(
        name=data.get("name", "Unnamed"),
        description=data.get("description", ""),
        created=data.get("created", ""),
        last_modified=data.get("last_modified", ""),
        party=[_deserialize_member(m) for m in data.get("party", [])],
        time_of_day=data.get("time_of_day", "day"),
        current_area=data.get("current_area", ""),
        session_number=data.get("session_number", 1),
        encounters=[_deserialize_encounter(e) for e in data.get("encounters", [])],
        areas=[_deserialize_area(a) for a in data.get("areas", [])],
        notes=[_deserialize_note(n) for n in data.get("notes", [])],
        settings=data.get("settings", {}),
    )


def list_campaigns() -> List[str]:
    """List all campaign files."""
    os.makedirs(CAMPAIGNS_DIR, exist_ok=True)
    return sorted([f for f in os.listdir(CAMPAIGNS_DIR) if f.endswith(".json")])


def delete_campaign(filepath: str):
    """Delete a campaign file."""
    if os.path.exists(filepath):
        os.remove(filepath)
