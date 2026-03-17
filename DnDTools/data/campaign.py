"""
Campaign Management System - Data model and persistence.
Campaigns hold a party of heroes, encounters, areas, notes, and settings.
JSON-based save/load using the generic serialization system.
"""
import json
import os
import time
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from data.models import CreatureStats, Item
from data.serialization import serialize, deserialize


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
    # World reference (world.py World object saved inline)
    world_data: dict = field(default_factory=dict)  # Serialized World for persistence
    # Settings
    settings: Dict = field(default_factory=lambda: {
        "variant_healing_potions": True,   # Potions as bonus action
        "variant_encumbrance": False,
        "flanking_advantage": False,
    })


def _timestamp():
    return time.strftime("%Y-%m-%d %H:%M:%S")


# ============================================================================
# SERIALIZATION (now uses generic serialize/deserialize)
# ============================================================================

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
        "party": [serialize(m) for m in campaign.party],
        "time_of_day": campaign.time_of_day,
        "current_area": campaign.current_area,
        "session_number": campaign.session_number,
        "encounters": [serialize(e) for e in campaign.encounters],
        "areas": [serialize(a) for a in campaign.areas],
        "notes": [serialize(n) for n in campaign.notes],
        "world_data": campaign.world_data,
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
        party=[deserialize(PartyMember, m) for m in data.get("party", [])],
        time_of_day=data.get("time_of_day", "day"),
        current_area=data.get("current_area", ""),
        session_number=data.get("session_number", 1),
        encounters=[deserialize(CampaignEncounter, e) for e in data.get("encounters", [])],
        areas=[deserialize(CampaignArea, a) for a in data.get("areas", [])],
        notes=[deserialize(CampaignNote, n) for n in data.get("notes", [])],
        world_data=data.get("world_data", {}),
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
