"""Race / population demographics for settlements + biome-driven
default suggestions.

A campaign Location can hold a :class:`Demographics` block that
breaks down its population by D&D race. The breakdown is a dict
(race name → percentage 0..100). The remaining percentage rolls up
into ``other_pct``.

Adjacent helper: ``suggest_demographics(biome)`` returns a sensible
default distribution for common biome tags ("forest", "underdark",
"plains", "swamp", …). UI can show the suggestion when the DM picks
a region type and let them tweak from there.

Pure logic, no pygame.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


# Canonical PHB races plus a few classic monstrous races. The DM
# can use any string; this list is just for picker presets.
COMMON_RACES = (
    "Human", "Elf", "Half-Elf", "Dwarf", "Halfling", "Gnome",
    "Half-Orc", "Tiefling", "Dragonborn",
    "Orc", "Goblin", "Hobgoblin", "Kobold", "Gnoll",
    "Drow", "Duergar", "Svirfneblin", "Mind Flayer",
    "Lizardfolk", "Tabaxi", "Tortle",
    "Genasi", "Aasimar", "Firbolg", "Triton",
)


# Biome tag → race-name → pct. Numbers sum to <= 100 leaving room
# for ``other_pct`` to absorb the long tail.
_BIOME_DEFAULTS: Dict[str, Dict[str, int]] = {
    "human_heartland": {
        "Human": 80, "Half-Elf": 6, "Halfling": 5,
        "Dwarf": 3, "Gnome": 2, "Elf": 2,
    },
    "forest": {
        "Elf": 55, "Half-Elf": 15, "Human": 15,
        "Halfling": 8, "Firbolg": 3,
    },
    "highland": {
        "Dwarf": 60, "Human": 20, "Gnome": 8, "Halfling": 5,
    },
    "swamp": {
        "Lizardfolk": 55, "Human": 15, "Tortle": 8, "Bullywug": 10,
    },
    "desert": {
        "Human": 50, "Tiefling": 12, "Half-Orc": 10,
        "Tabaxi": 8, "Genasi": 5,
    },
    "tundra": {
        "Human": 35, "Dwarf": 25, "Half-Orc": 10, "Goliath": 15,
    },
    "underdark": {
        "Drow": 35, "Duergar": 25, "Svirfneblin": 15,
        "Mind Flayer": 3, "Kobold": 8,
    },
    "coast": {
        "Human": 45, "Triton": 10, "Half-Elf": 12,
        "Halfling": 8, "Dwarf": 5, "Tabaxi": 5,
    },
    "plains": {
        "Human": 60, "Half-Elf": 10, "Halfling": 12,
        "Dwarf": 8, "Gnome": 4,
    },
    "mountain": {
        "Dwarf": 55, "Human": 20, "Half-Orc": 10,
        "Gnome": 5, "Goliath": 5,
    },
    "frontier": {
        "Human": 40, "Half-Orc": 15, "Dwarf": 12,
        "Halfling": 10, "Elf": 5, "Tiefling": 5,
    },
    # Orcish heartland — useful for villainous strongholds
    "orcish": {
        "Orc": 65, "Half-Orc": 15, "Goblin": 10, "Hobgoblin": 5,
    },
    "feywild_touched": {
        "Elf": 50, "Half-Elf": 15, "Halfling": 8,
        "Firbolg": 5, "Satyr": 5, "Human": 10,
    },
    # Cosmopolitan capital
    "cosmopolitan": {
        "Human": 35, "Half-Elf": 12, "Halfling": 10,
        "Dwarf": 10, "Elf": 8, "Gnome": 6, "Tiefling": 6,
        "Half-Orc": 5, "Dragonborn": 4,
    },
}


@dataclass
class Demographics:
    """Population breakdown for one settlement / region."""
    total_population: int = 0
    by_race: Dict[str, int] = field(default_factory=dict)  # name → pct
    biome: str = ""           # tag from _BIOME_DEFAULTS or DM-chosen
    notes: str = ""

    def normalised(self) -> Dict[str, int]:
        """Return ``by_race`` with sum clamped <= 100; the rest is
        labelled 'Other'."""
        total = sum(max(0, int(v)) for v in self.by_race.values())
        out = dict(self.by_race)
        if total < 100:
            out["Other"] = 100 - total
        return out

    def population_by_race(self) -> Dict[str, int]:
        """Approx headcount per race (using total_population and pct)."""
        breakdown = self.normalised()
        return {
            race: int(round(self.total_population * pct / 100.0))
            for race, pct in breakdown.items()
        }

    def majority_race(self) -> str:
        """The single largest racial group, or '' when empty."""
        if not self.by_race:
            return ""
        return max(self.by_race, key=lambda r: self.by_race[r])


# --------------------------------------------------------------------- #
# Suggestion API
# --------------------------------------------------------------------- #
def suggest_demographics(biome: str,
                            total_population: int = 0) -> Demographics:
    """Pick a default breakdown for ``biome``. Falls back to the
    cosmopolitan mix when the biome is unknown."""
    key = (biome or "").strip().lower()
    table = _BIOME_DEFAULTS.get(key) or _BIOME_DEFAULTS["cosmopolitan"]
    return Demographics(
        total_population=int(max(0, total_population)),
        by_race=dict(table),
        biome=key,
    )


def known_biomes() -> List[str]:
    return list(_BIOME_DEFAULTS.keys())


def biome_for_location_type(location_type: str) -> str:
    """Map a Location.location_type string to a biome tag — used
    when the DM hasn't picked one explicitly."""
    key = (location_type or "").lower()
    mapping = {
        "city":       "cosmopolitan",
        "capital":    "cosmopolitan",
        "town":       "human_heartland",
        "village":    "plains",
        "fort":       "frontier",
        "wilderness": "forest",
        "dungeon":    "underdark",
        "cave":       "underdark",
        "region":     "plains",
    }
    return mapping.get(key, "plains")
