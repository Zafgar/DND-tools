"""
Battle Report Generator – creates a comprehensive text + JSON summary
when combat ends, covering all relevant statistics.
"""
import json
import os
from datetime import datetime
from typing import Dict, List, TYPE_CHECKING

if TYPE_CHECKING:
    from engine.battle_stats import BattleStatisticsTracker


def generate_battle_report(tracker: "BattleStatisticsTracker",
                           combat_log: List[str] = None) -> dict:
    """Generate a comprehensive battle report dictionary."""
    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": _build_summary(tracker),
        "combatants": _build_combatant_details(tracker),
        "damage_breakdown": _build_damage_breakdown(tracker),
        "spell_usage": _build_spell_usage(tracker),
        "healing_breakdown": _build_healing_breakdown(tracker),
        "conditions_timeline": _build_conditions_timeline(tracker),
        "death_events": _build_death_events(tracker),
        "resource_usage": _build_resource_usage(tracker),
        "round_by_round": _build_round_summary(tracker),
        "mvp": _calculate_mvp(tracker),
    }
    if combat_log:
        report["combat_log"] = combat_log
    return report


def _build_summary(tracker) -> dict:
    """Top-level battle summary."""
    player_stats = [s for s in tracker.entity_stats.values() if s.is_player]
    enemy_stats = [s for s in tracker.entity_stats.values() if not s.is_player]

    total_player_dmg = sum(s.total_damage_dealt for s in player_stats)
    total_enemy_dmg = sum(s.total_damage_dealt for s in enemy_stats)
    total_player_healing = sum(s.total_healing_done for s in player_stats)
    total_enemy_healing = sum(s.total_healing_done for s in enemy_stats)

    player_deaths = sum(1 for s in player_stats if s.ending_hp <= 0)
    enemy_deaths = sum(1 for s in enemy_stats if s.ending_hp <= 0)

    return {
        "winner": tracker.winner,
        "total_rounds": tracker.total_rounds,
        "player_count": len(player_stats),
        "enemy_count": len(enemy_stats),
        "total_player_damage_dealt": total_player_dmg,
        "total_enemy_damage_dealt": total_enemy_dmg,
        "total_player_healing": total_player_healing,
        "total_enemy_healing": total_enemy_healing,
        "player_casualties": player_deaths,
        "enemy_casualties": enemy_deaths,
        "avg_damage_per_round_players": round(total_player_dmg / max(1, tracker.total_rounds), 1),
        "avg_damage_per_round_enemies": round(total_enemy_dmg / max(1, tracker.total_rounds), 1),
    }


def _build_combatant_details(tracker) -> List[dict]:
    """Per-combatant statistics."""
    combatants = []
    for name, s in tracker.entity_stats.items():
        hit_rate = (s.attacks_hit / s.attacks_made * 100) if s.attacks_made > 0 else 0
        dpr = s.total_damage_dealt / max(1, s.rounds_active)
        entry = {
            "name": name,
            "side": "Player" if s.is_player else "Enemy",
            "hp_start": s.starting_hp,
            "hp_end": s.ending_hp,
            "hp_max": s.max_hp,
            "total_damage_dealt": s.total_damage_dealt,
            "total_damage_taken": s.total_damage_taken,
            "total_healing_done": s.total_healing_done,
            "total_healing_received": s.total_healing_received,
            "kills": s.kills,
            "times_downed": s.times_downed,
            "attacks_made": s.attacks_made,
            "attacks_hit": s.attacks_hit,
            "hit_rate_pct": round(hit_rate, 1),
            "critical_hits": s.critical_hits,
            "critical_misses": s.critical_misses,
            "spells_cast": s.spells_cast,
            "spell_slots_used": s.spell_slots_used,
            "conditions_applied": s.conditions_applied,
            "conditions_suffered": s.conditions_suffered,
            "saving_throws": f"{s.saving_throws_passed}/{s.saving_throws_made}",
            "death_saves": f"{s.death_saves_passed}/{s.death_saves_made}",
            "damage_per_round": round(dpr, 1),
            "damage_by_type": s.damage_by_type,
            "damage_by_ability": s.damage_by_ability,
            "damage_taken_by_type": s.damage_taken_by_type,
            "movement_total_ft": round(s.movement_total_ft, 0),
            "rounds_active": s.rounds_active,
        }
        combatants.append(entry)

    # Sort: players first, then by damage dealt descending
    combatants.sort(key=lambda c: (-int(c["side"] == "Player"), -c["total_damage_dealt"]))
    return combatants


def _build_damage_breakdown(tracker) -> dict:
    """Damage breakdown by type across all combatants."""
    by_type: Dict[str, int] = {}
    for event in tracker.damage_events:
        by_type[event.damage_type] = by_type.get(event.damage_type, 0) + event.amount

    top_hits = sorted(tracker.damage_events, key=lambda e: e.amount, reverse=True)[:10]
    return {
        "by_damage_type": by_type,
        "top_10_hits": [
            {
                "round": h.round, "source": h.source_name, "target": h.target_name,
                "amount": h.amount, "type": h.damage_type, "ability": h.source_ability,
                "critical": h.is_critical,
            } for h in top_hits
        ],
    }


def _build_spell_usage(tracker) -> dict:
    """Spell usage statistics."""
    spells_by_name: Dict[str, dict] = {}
    for event in tracker.spell_events:
        if event.spell_name not in spells_by_name:
            spells_by_name[event.spell_name] = {
                "name": event.spell_name,
                "times_cast": 0,
                "total_damage": 0,
                "total_healing": 0,
                "highest_slot": 0,
                "casters": set(),
            }
        entry = spells_by_name[event.spell_name]
        entry["times_cast"] += 1
        entry["total_damage"] += event.total_damage
        entry["total_healing"] += event.total_healing
        entry["highest_slot"] = max(entry["highest_slot"], event.slot_level)
        entry["casters"].add(event.caster_name)

    # Convert sets to lists for JSON
    spell_list = []
    for entry in spells_by_name.values():
        entry["casters"] = list(entry["casters"])
        spell_list.append(entry)
    spell_list.sort(key=lambda s: s["total_damage"] + s["total_healing"], reverse=True)

    total_slots = {}
    for event in tracker.spell_events:
        if event.slot_level > 0:
            total_slots[event.slot_level] = total_slots.get(event.slot_level, 0) + 1

    return {
        "spells": spell_list,
        "total_slots_used": total_slots,
        "total_spells_cast": len(tracker.spell_events),
        "total_cantrips": sum(1 for e in tracker.spell_events if e.slot_level == 0),
    }


def _build_healing_breakdown(tracker) -> dict:
    """Healing breakdown."""
    heals_by_source: Dict[str, int] = {}
    heals_by_ability: Dict[str, int] = {}
    for event in tracker.heal_events:
        heals_by_source[event.source_name] = heals_by_source.get(event.source_name, 0) + event.amount
        if event.source_ability:
            heals_by_ability[event.source_ability] = heals_by_ability.get(event.source_ability, 0) + event.amount

    return {
        "by_healer": heals_by_source,
        "by_ability": heals_by_ability,
        "total_healing": sum(e.amount for e in tracker.heal_events),
    }


def _build_conditions_timeline(tracker) -> List[dict]:
    """Conditions applied/removed over time."""
    return [
        {
            "round": e.round,
            "target": e.target_name,
            "condition": e.condition,
            "applied_by": e.applied_by,
            "event": e.event_type,
        } for e in tracker.condition_events
    ]


def _build_death_events(tracker) -> List[dict]:
    """Death/stabilization events."""
    return [
        {
            "round": e.round,
            "entity": e.entity_name,
            "type": e.event_type,
            "killed_by": e.killed_by,
        } for e in tracker.death_events
    ]


def _build_resource_usage(tracker) -> dict:
    """Resource usage comparison (start vs end) for all entities."""
    usage = {}
    for name, initial in tracker._initial_states.items():
        entity_usage = {}
        # Spell slots
        initial_slots = initial.get("spell_slots", {})
        if initial_slots:
            stats = tracker.entity_stats.get(name)
            slots_used = stats.spell_slots_used if stats else {}
            entity_usage["spell_slots"] = {
                "initial": initial_slots,
                "used": {str(k): v for k, v in slots_used.items()},
            }
        # Class resources
        for key, label in [
            ("ki_points", "Ki Points"),
            ("sorcery_points", "Sorcery Points"),
            ("lay_on_hands", "Lay on Hands"),
            ("rages_left", "Rages"),
            ("bardic_inspiration", "Bardic Inspiration"),
        ]:
            init_val = initial.get(key, 0)
            if init_val > 0:
                entity_usage[label] = {"initial": init_val}

        if entity_usage:
            usage[name] = entity_usage
    return usage


def _build_round_summary(tracker) -> List[dict]:
    """Per-round damage totals."""
    rounds: Dict[int, dict] = {}
    for event in tracker.damage_events:
        if event.round not in rounds:
            rounds[event.round] = {"round": event.round, "player_damage": 0,
                                   "enemy_damage": 0, "events": 0}
        r = rounds[event.round]
        r["events"] += 1
        src = tracker.entity_stats.get(event.source_name)
        if src and src.is_player:
            r["player_damage"] += event.amount
        else:
            r["enemy_damage"] += event.amount

    return sorted(rounds.values(), key=lambda r: r["round"])


def _calculate_mvp(tracker) -> dict:
    """Determine Most Valuable Player based on contribution."""
    player_stats = [s for s in tracker.entity_stats.values() if s.is_player]
    if not player_stats:
        return {"name": "N/A", "reason": "No players"}

    # Score: damage_dealt + healing_done*1.5 + kills*20 + conditions_applied*10
    def score(s):
        return (s.total_damage_dealt +
                s.total_healing_done * 1.5 +
                s.kills * 20 +
                s.conditions_applied * 10 -
                s.times_downed * 15)

    mvp = max(player_stats, key=score)
    return {
        "name": mvp.name,
        "damage_dealt": mvp.total_damage_dealt,
        "healing_done": mvp.total_healing_done,
        "kills": mvp.kills,
        "conditions_applied": mvp.conditions_applied,
        "score": round(score(mvp), 1),
    }


# ------------------------------------------------------------------ #
# Text Formatting                                                      #
# ------------------------------------------------------------------ #

def format_report_text(report: dict) -> str:
    """Format report as readable text for display or saving."""
    lines = []
    summary = report["summary"]

    lines.append("=" * 60)
    lines.append("         BATTLE REPORT")
    lines.append("=" * 60)
    lines.append(f"Winner: {'PLAYERS' if summary['winner'] == 'players' else 'ENEMIES'}")
    lines.append(f"Total Rounds: {summary['total_rounds']}")
    lines.append(f"Players: {summary['player_count']}  |  Enemies: {summary['enemy_count']}")
    lines.append(f"Player Casualties: {summary['player_casualties']}  |  Enemy Casualties: {summary['enemy_casualties']}")
    lines.append("")
    lines.append(f"Total Player Damage: {summary['total_player_damage_dealt']}  (avg {summary['avg_damage_per_round_players']}/round)")
    lines.append(f"Total Enemy Damage:  {summary['total_enemy_damage_dealt']}  (avg {summary['avg_damage_per_round_enemies']}/round)")
    lines.append(f"Total Player Healing: {summary['total_player_healing']}")
    lines.append("")

    # MVP
    mvp = report.get("mvp", {})
    if mvp.get("name") != "N/A":
        lines.append(f"MVP: {mvp['name']} (DMG:{mvp['damage_dealt']} HEAL:{mvp['healing_done']} KILLS:{mvp['kills']})")
    lines.append("")

    # Per-combatant
    lines.append("-" * 60)
    lines.append("COMBATANT DETAILS")
    lines.append("-" * 60)
    for c in report["combatants"]:
        side = c["side"]
        status = "ALIVE" if c["hp_end"] > 0 else "DEAD"
        lines.append(f"\n[{side}] {c['name']} ({status})")
        lines.append(f"  HP: {c['hp_start']} -> {c['hp_end']}/{c['hp_max']}")
        lines.append(f"  Damage Dealt: {c['total_damage_dealt']}  |  Taken: {c['total_damage_taken']}")
        lines.append(f"  DPR: {c['damage_per_round']}  |  Healing: Done {c['total_healing_done']} / Recv {c['total_healing_received']}")
        lines.append(f"  Attacks: {c['attacks_hit']}/{c['attacks_made']} ({c['hit_rate_pct']}%)  |  Crits: {c['critical_hits']}")
        lines.append(f"  Spells: {c['spells_cast']}  |  Kills: {c['kills']}  |  Downed: {c['times_downed']}")
        if c["damage_by_ability"]:
            top_abilities = sorted(c["damage_by_ability"].items(), key=lambda x: x[1], reverse=True)[:5]
            lines.append(f"  Top Abilities: " + ", ".join(f"{name}:{dmg}" for name, dmg in top_abilities))
        if c["spell_slots_used"]:
            slots_str = ", ".join(f"Lvl{k}:{v}" for k, v in sorted(c["spell_slots_used"].items()))
            lines.append(f"  Slots Used: {slots_str}")
        lines.append(f"  Conditions Applied: {c['conditions_applied']}  |  Suffered: {c['conditions_suffered']}")
        lines.append(f"  Saves: {c['saving_throws']}  |  Death Saves: {c['death_saves']}")

    # Spell Usage
    spells = report.get("spell_usage", {})
    if spells.get("spells"):
        lines.append("")
        lines.append("-" * 60)
        lines.append("SPELL USAGE")
        lines.append("-" * 60)
        for s in spells["spells"]:
            lines.append(f"  {s['name']}: Cast {s['times_cast']}x  DMG:{s['total_damage']}  HEAL:{s['total_healing']}")

    # Top Hits
    dmg_bd = report.get("damage_breakdown", {})
    top_hits = dmg_bd.get("top_10_hits", [])
    if top_hits:
        lines.append("")
        lines.append("-" * 60)
        lines.append("TOP 10 HITS")
        lines.append("-" * 60)
        for i, h in enumerate(top_hits, 1):
            crit_str = " [CRIT]" if h["critical"] else ""
            lines.append(f"  {i}. R{h['round']} {h['source']} -> {h['target']}: "
                         f"{h['amount']} {h['type']} ({h['ability']}){crit_str}")

    # Resource Usage
    resources = report.get("resource_usage", {})
    if resources:
        lines.append("")
        lines.append("-" * 60)
        lines.append("RESOURCE USAGE")
        lines.append("-" * 60)
        for name, usage in resources.items():
            lines.append(f"  {name}:")
            for resource, data in usage.items():
                if resource == "spell_slots":
                    init = data["initial"]
                    used = data["used"]
                    for slot_key, init_count in sorted(init.items()):
                        used_count = used.get(slot_key.replace("st", "").replace("nd", "").replace("rd", "").replace("th", ""), 0)
                        if init_count > 0:
                            lines.append(f"    {slot_key}: {init_count} -> used {used_count}")
                else:
                    lines.append(f"    {resource}: started with {data['initial']}")

    # Conditions Timeline
    conditions = report.get("conditions_timeline", [])
    if conditions:
        lines.append("")
        lines.append("-" * 60)
        lines.append("CONDITIONS TIMELINE")
        lines.append("-" * 60)
        for c in conditions:
            lines.append(f"  R{c['round']} {c['target']}: {c['condition']} {c['event']} "
                         f"{'by ' + c['applied_by'] if c['applied_by'] else ''}")

    lines.append("")
    lines.append("=" * 60)
    lines.append(f"Report generated: {report.get('timestamp', 'N/A')}")
    lines.append("=" * 60)

    return "\n".join(lines)


def save_report(report: dict, filepath: str):
    """Save report as JSON file."""
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(report, f, indent=2, default=str)


def save_report_text(report: dict, filepath: str):
    """Save report as readable text file."""
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    text = format_report_text(report)
    with open(filepath, "w") as f:
        f.write(text)
