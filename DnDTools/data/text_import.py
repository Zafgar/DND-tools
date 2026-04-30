"""Bulk text importer — turn a DM's `.md` / `.txt` notes into
Campaign world data in one shot.

The format is a forgiving Markdown-ish dialect:

    ## Locations
    - Arenhold (town): Port-city on Greysea, trade hub.
        Tags: coast, merchants
    - Vardun Keep (fort): Crumbling wall, goblin probes.
        Tags: ruins, military
    - Silverbough Forest (wilderness): Fey-touched.

    ## NPCs
    - Lady Mira Vardun (Castellan, Vardun Keep): Stern but fair.
        Tags: noble
    - Harbourmaster Jolan Ves (Harbourmaster, Arenhold): Tracks every ship.
    - Captain Arys Tarn (Captain @ Tarn Trading House): Ruthless merchant.

    ## Quests
    - Goblin Investigation: Find the goblin source near Vardun Keep.

Rules:
  * ``##`` (or single ``#``) starts a section: ``Locations`` /
    ``NPCs`` / ``Quests`` / ``Notes`` (case-insensitive).
  * ``-`` (or ``*``) starts an entry. Continuation lines belong to
    the previous entry.
  * ``Name (qualifier): description`` — qualifier is loctype for
    locations, "occupation" or "occupation, location" or
    "occupation @ faction" for NPCs.
  * ``Tags:`` line on its own (or any continuation line starting
    "Tags:") becomes ``tags``.

Pure logic; no pygame. The importer is idempotent — re-importing
the same text on top of an already-populated World only updates
existing entries by name, never duplicates.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from data.world import World, Location, NPC, Quest, generate_id


# --------------------------------------------------------------------- #
# Section detection
# --------------------------------------------------------------------- #
_SECTION_KEYS = {
    "locations":  "locations",
    "places":     "locations",
    "cities":     "locations",
    "settlements":"locations",
    "kingdoms":   "locations",
    "regions":    "locations",
    "npcs":       "npcs",
    "characters": "npcs",
    "people":     "npcs",
    "actors":     "npcs",
    "quests":     "quests",
    "missions":   "quests",
    "hooks":      "quests",
    "notes":      "notes",
    "lore":       "notes",
}

_HEADING_RE = re.compile(r"^\s{0,3}#{1,3}\s+(.+?)\s*#*\s*$")
_BULLET_RE  = re.compile(r"^\s*[-*•]\s+(.+?)\s*$")
_PAREN_RE   = re.compile(r"^\s*([^()]+?)\s*\(([^)]+)\)\s*(?::\s*(.+))?$")
_PLAIN_RE   = re.compile(r"^\s*([^:]+?)\s*:\s*(.+)\s*$")


# --------------------------------------------------------------------- #
# Result containers
# --------------------------------------------------------------------- #
@dataclass
class ImportReport:
    locations_created: int = 0
    locations_updated: int = 0
    npcs_created: int = 0
    npcs_updated: int = 0
    quests_created: int = 0
    quests_updated: int = 0
    notes_added: int = 0
    skipped_lines: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def total_changes(self) -> int:
        return (self.locations_created + self.locations_updated
                + self.npcs_created + self.npcs_updated
                + self.quests_created + self.quests_updated
                + self.notes_added)

    def summary(self) -> str:
        bits = []
        if self.locations_created or self.locations_updated:
            bits.append(f"{self.locations_created}+ "
                         f"{self.locations_updated}~ locations")
        if self.npcs_created or self.npcs_updated:
            bits.append(f"{self.npcs_created}+ "
                         f"{self.npcs_updated}~ NPCs")
        if self.quests_created or self.quests_updated:
            bits.append(f"{self.quests_created}+ "
                         f"{self.quests_updated}~ quests")
        if self.notes_added:
            bits.append(f"{self.notes_added}+ notes")
        if self.warnings:
            bits.append(f"{len(self.warnings)} warning(s)")
        return ", ".join(bits) if bits else "no changes"


@dataclass
class _RawEntry:
    name: str
    qualifier: str = ""
    description: str = ""
    tags: List[str] = field(default_factory=list)
    raw_lines: List[str] = field(default_factory=list)


# --------------------------------------------------------------------- #
# Tokeniser
# --------------------------------------------------------------------- #
def _detect_section(text: str) -> Optional[str]:
    key = re.sub(r"[^a-z]+", "", text.lower())
    for k, kind in _SECTION_KEYS.items():
        if key == k or key.startswith(k):
            return kind
    return None


def _tokenize(text: str) -> Dict[str, List[_RawEntry]]:
    """Walk the text once and group bullet entries by section."""
    sections: Dict[str, List[_RawEntry]] = {
        "locations": [], "npcs": [], "quests": [], "notes": [],
    }
    current_section: Optional[str] = None
    current_entry: Optional[_RawEntry] = None

    def _commit_entry():
        nonlocal current_entry
        if current_entry is not None and current_section is not None:
            sections[current_section].append(current_entry)
        current_entry = None

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            _commit_entry()
            continue
        # Heading?
        m = _HEADING_RE.match(line)
        if m:
            _commit_entry()
            current_section = _detect_section(m.group(1))
            continue
        # Bullet (entry start)?
        m = _BULLET_RE.match(line)
        if m and current_section is not None:
            _commit_entry()
            entry_text = m.group(1)
            paren = _PAREN_RE.match(entry_text)
            if paren:
                name = paren.group(1).strip()
                qualifier = paren.group(2).strip()
                desc = (paren.group(3) or "").strip()
            else:
                plain = _PLAIN_RE.match(entry_text)
                if plain:
                    name = plain.group(1).strip()
                    qualifier = ""
                    desc = plain.group(2).strip()
                else:
                    name = entry_text.strip()
                    qualifier = ""
                    desc = ""
            current_entry = _RawEntry(name=name,
                                        qualifier=qualifier,
                                        description=desc,
                                        raw_lines=[line])
            continue
        # Continuation line on current entry?
        if current_entry is not None:
            stripped = line.strip()
            if stripped.lower().startswith("tags:"):
                tag_str = stripped.split(":", 1)[1]
                current_entry.tags.extend(
                    t.strip() for t in tag_str.split(",")
                    if t.strip()
                )
            else:
                # Append to description with a space
                if current_entry.description:
                    current_entry.description += " " + stripped
                else:
                    current_entry.description = stripped
            current_entry.raw_lines.append(line)
            continue
        # Otherwise: notes section can absorb stray paragraphs
        if current_section == "notes":
            sections["notes"].append(_RawEntry(name="",
                                                  description=line.strip()))

    _commit_entry()
    return sections


# --------------------------------------------------------------------- #
# Type inference
# --------------------------------------------------------------------- #
_LOC_TYPE_KEYWORDS = (
    # Order matters: more-specific keywords first so "Capital city"
    # resolves to "capital", not "city".
    "capital", "kingdom", "country", "wilderness", "stronghold",
    "outpost", "hamlet", "dungeon", "tavern",
    "city", "town", "village", "fort", "region",
    "cave", "temple", "shop",
)


def _infer_location_type(qualifier: str) -> str:
    q = qualifier.lower().strip()
    for kw in _LOC_TYPE_KEYWORDS:
        if kw in q:
            return kw
    return "region"


def _split_npc_qualifier(qualifier: str) -> Tuple[str, str, str]:
    """Parse 'Castellan, Vardun Keep' or 'Captain @ Tarn Trading House'
    into (occupation, location_hint, faction)."""
    if "@" in qualifier:
        occ, fac = qualifier.split("@", 1)
        return occ.strip(), "", fac.strip()
    if "," in qualifier:
        occ, loc = qualifier.split(",", 1)
        return occ.strip(), loc.strip(), ""
    return qualifier.strip(), "", ""


def _find_location_by_name(world: World, name: str) -> Optional[Location]:
    if not name:
        return None
    key = name.strip().lower()
    for loc in world.locations.values():
        if loc.name.lower() == key:
            return loc
    return None


def _find_npc_by_name(world: World, name: str) -> Optional[NPC]:
    if not name:
        return None
    key = name.strip().lower()
    for npc in world.npcs.values():
        if npc.name.lower() == key:
            return npc
    return None


def _find_quest_by_name(world: World, name: str) -> Optional[Quest]:
    if not name:
        return None
    key = name.strip().lower()
    for q in world.quests.values():
        if q.name.lower() == key:
            return q
    return None


# --------------------------------------------------------------------- #
# Apply
# --------------------------------------------------------------------- #
def _apply_locations(world: World, entries: List[_RawEntry],
                       report: ImportReport):
    for e in entries:
        if not e.name:
            report.skipped_lines.extend(e.raw_lines)
            continue
        existing = _find_location_by_name(world, e.name)
        kind = _infer_location_type(e.qualifier)
        if existing is None:
            new_id = generate_id(world, prefix="loc")
            world.locations[new_id] = Location(
                id=new_id, name=e.name,
                location_type=kind,
                description=e.description,
                tags=list(e.tags),
            )
            report.locations_created += 1
        else:
            if e.qualifier:
                existing.location_type = kind
            if e.description:
                existing.description = e.description
            if e.tags:
                # Merge tags (preserve existing, add new)
                merged = list(existing.tags)
                for t in e.tags:
                    if t not in merged:
                        merged.append(t)
                existing.tags = merged
            report.locations_updated += 1


def _apply_npcs(world: World, entries: List[_RawEntry],
                  report: ImportReport):
    for e in entries:
        if not e.name:
            report.skipped_lines.extend(e.raw_lines)
            continue
        occupation, loc_hint, faction = _split_npc_qualifier(e.qualifier)
        existing = _find_npc_by_name(world, e.name)
        # Best-effort link by name
        loc_id = ""
        if loc_hint:
            loc = _find_location_by_name(world, loc_hint)
            if loc is not None:
                loc_id = loc.id
            else:
                report.warnings.append(
                    f"NPC {e.name!r}: location hint "
                    f"{loc_hint!r} not found"
                )
        if existing is None:
            new_id = generate_id(world, prefix="npc")
            world.npcs[new_id] = NPC(
                id=new_id, name=e.name,
                occupation=occupation,
                faction=faction,
                location_id=loc_id,
                notes=e.description,
                tags=list(e.tags),
            )
            report.npcs_created += 1
        else:
            if occupation:
                existing.occupation = occupation
            if faction:
                existing.faction = faction
            if loc_id:
                existing.location_id = loc_id
            if e.description:
                existing.notes = e.description
            if e.tags:
                merged = list(existing.tags)
                for t in e.tags:
                    if t not in merged:
                        merged.append(t)
                existing.tags = merged
            report.npcs_updated += 1


def _apply_quests(world: World, entries: List[_RawEntry],
                    report: ImportReport):
    for e in entries:
        if not e.name:
            continue
        existing = _find_quest_by_name(world, e.name)
        if existing is None:
            new_id = generate_id(world, prefix="qst")
            world.quests[new_id] = Quest(
                id=new_id, name=e.name,
                description=e.description,
            )
            report.quests_created += 1
        else:
            if e.description:
                existing.description = e.description
            report.quests_updated += 1


def _apply_notes(world: World, entries: List[_RawEntry],
                   report: ImportReport):
    """Notes go into the World's description (legacy data has no
    dedicated note bucket on World; we append)."""
    if not entries:
        return
    block = []
    for e in entries:
        if e.name and e.description:
            block.append(f"{e.name}: {e.description}")
        elif e.description:
            block.append(e.description)
    if block:
        joined = "\n".join(block)
        if world.description:
            world.description = world.description.rstrip() + "\n\n" + joined
        else:
            world.description = joined
        report.notes_added += len(block)


# --------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------- #
def import_text(world: World, text: str) -> ImportReport:
    """Parse ``text`` and merge its content into ``world``. Returns a
    structured report describing what was added or updated."""
    report = ImportReport()
    sections = _tokenize(text or "")
    _apply_locations(world, sections["locations"], report)
    # Apply NPCs after locations so location hints can resolve.
    _apply_npcs(world, sections["npcs"], report)
    _apply_quests(world, sections["quests"], report)
    _apply_notes(world, sections["notes"], report)
    return report


def import_file(world: World, path: str,
                  encoding: str = "utf-8") -> ImportReport:
    """Read ``path`` and feed it through :func:`import_text`. Raises
    on file errors so callers can show a helpful message."""
    with open(path, encoding=encoding) as f:
        return import_text(world, f.read())
