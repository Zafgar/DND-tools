"""
Battle Statistics Tracker – records every combat event for post-battle analysis.
Tracks damage dealt/received, spells cast, conditions applied, spell slots used,
healing done, kills, and per-entity breakdowns.
"""
import copy
import json
from dataclasses import dataclass, field
from typing import List, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from engine.entities import Entity


@dataclass
class DamageEvent:
    """One instance of damage dealt or healing done."""
    round: int
    source_name: str
    target_name: str
    amount: int
    damage_type: str
    source_ability: str = ""       # Spell name, action name, feature name
    is_critical: bool = False
    is_aoe: bool = False
    was_resisted: bool = False     # Half damage from resistance
    was_saved: bool = False        # Half damage from save


@dataclass
class SpellEvent:
    """One spell cast during combat."""
    round: int
    caster_name: str
    spell_name: str
    slot_level: int                 # 0 = cantrip
    targets: List[str] = field(default_factory=list)
    total_damage: int = 0
    total_healing: int = 0
    applied_condition: str = ""


@dataclass
class ConditionEvent:
    """A condition applied or removed."""
    round: int
    target_name: str
    condition: str
    applied_by: str = ""
    duration_rounds: int = 0        # How long it lasted (filled on removal)
    event_type: str = "applied"     # "applied" or "removed"


@dataclass
class HealEvent:
    """One healing event."""
    round: int
    source_name: str
    target_name: str
    amount: int
    source_ability: str = ""


@dataclass
class DeathEvent:
    """Entity death or stabilization."""
    round: int
    entity_name: str
    event_type: str = "death"       # "death", "stabilized", "revived"
    killed_by: str = ""


@dataclass
class EntityCombatStats:
    """Aggregated statistics for a single entity across the battle."""
    name: str
    is_player: bool = False
    starting_hp: int = 0
    ending_hp: int = 0
    max_hp: int = 0
    total_damage_dealt: int = 0
    total_damage_taken: int = 0
    total_healing_done: int = 0
    total_healing_received: int = 0
    kills: int = 0
    times_downed: int = 0
    attacks_made: int = 0
    attacks_hit: int = 0
    critical_hits: int = 0
    critical_misses: int = 0
    spells_cast: int = 0
    spell_slots_used: Dict[int, int] = field(default_factory=dict)  # level -> count
    conditions_applied: int = 0
    conditions_suffered: int = 0
    saving_throws_made: int = 0
    saving_throws_passed: int = 0
    death_saves_made: int = 0
    death_saves_passed: int = 0
    damage_by_type: Dict[str, int] = field(default_factory=dict)
    damage_by_ability: Dict[str, int] = field(default_factory=dict)
    damage_taken_by_type: Dict[str, int] = field(default_factory=dict)
    movement_total_ft: float = 0.0
    rounds_active: int = 0          # Rounds entity was alive/conscious


class BattleStatisticsTracker:
    """Collects all combat events and provides aggregated statistics."""

    def __init__(self):
        self.damage_events: List[DamageEvent] = []
        self.spell_events: List[SpellEvent] = []
        self.condition_events: List[ConditionEvent] = []
        self.heal_events: List[HealEvent] = []
        self.death_events: List[DeathEvent] = []
        self.entity_stats: Dict[str, EntityCombatStats] = {}
        self.combat_start_time: int = 0       # Round when combat started
        self.combat_end_round: int = 0
        self.total_rounds: int = 0
        self.winner: str = ""                  # "players" or "enemies"
        self._initial_states: Dict[str, dict] = {}  # name -> snapshot

    def register_entity(self, entity: "Entity"):
        """Register an entity at combat start to track initial state."""
        stats = EntityCombatStats(
            name=entity.name,
            is_player=entity.is_player,
            starting_hp=entity.hp,
            ending_hp=entity.hp,
            max_hp=entity.max_hp,
        )
        self.entity_stats[entity.name] = stats
        self._initial_states[entity.name] = {
            "hp": entity.hp,
            "max_hp": entity.max_hp,
            "spell_slots": copy.deepcopy(entity.spell_slots),
            "ki_points": entity.ki_points_left,
            "sorcery_points": entity.sorcery_points_left,
            "lay_on_hands": entity.lay_on_hands_left,
            "rages_left": entity.rages_left,
            "bardic_inspiration": entity.bardic_inspiration_left,
            "feature_uses": copy.deepcopy(entity.feature_uses),
        }

    def _ensure_entity(self, name: str, is_player: bool = False):
        if name not in self.entity_stats:
            self.entity_stats[name] = EntityCombatStats(name=name, is_player=is_player)

    # ------------------------------------------------------------------ #
    # Event Recording                                                      #
    # ------------------------------------------------------------------ #

    def record_damage(self, round_num: int, source_name: str, target_name: str,
                      amount: int, damage_type: str, ability_name: str = "",
                      is_critical: bool = False, is_aoe: bool = False,
                      was_resisted: bool = False, was_saved: bool = False,
                      source_is_player: bool = False, target_is_player: bool = False):
        """Record a damage event."""
        event = DamageEvent(
            round=round_num, source_name=source_name, target_name=target_name,
            amount=amount, damage_type=damage_type, source_ability=ability_name,
            is_critical=is_critical, is_aoe=is_aoe,
            was_resisted=was_resisted, was_saved=was_saved,
        )
        self.damage_events.append(event)

        self._ensure_entity(source_name, source_is_player)
        self._ensure_entity(target_name, target_is_player)

        src = self.entity_stats[source_name]
        src.total_damage_dealt += amount
        src.damage_by_type[damage_type] = src.damage_by_type.get(damage_type, 0) + amount
        src.damage_by_ability[ability_name] = src.damage_by_ability.get(ability_name, 0) + amount

        tgt = self.entity_stats[target_name]
        tgt.total_damage_taken += amount
        tgt.damage_taken_by_type[damage_type] = tgt.damage_taken_by_type.get(damage_type, 0) + amount

    def record_attack(self, round_num: int, attacker_name: str, is_hit: bool,
                      is_critical: bool = False, is_fumble: bool = False,
                      attacker_is_player: bool = False):
        """Record an attack roll (hit/miss/crit)."""
        self._ensure_entity(attacker_name, attacker_is_player)
        stats = self.entity_stats[attacker_name]
        stats.attacks_made += 1
        if is_hit:
            stats.attacks_hit += 1
        if is_critical:
            stats.critical_hits += 1
        if is_fumble:
            stats.critical_misses += 1

    def record_spell(self, round_num: int, caster_name: str, spell_name: str,
                     slot_level: int, targets: List[str] = None,
                     total_damage: int = 0, total_healing: int = 0,
                     applied_condition: str = "",
                     caster_is_player: bool = False):
        """Record a spell cast."""
        event = SpellEvent(
            round=round_num, caster_name=caster_name, spell_name=spell_name,
            slot_level=slot_level, targets=targets or [],
            total_damage=total_damage, total_healing=total_healing,
            applied_condition=applied_condition,
        )
        self.spell_events.append(event)

        self._ensure_entity(caster_name, caster_is_player)
        stats = self.entity_stats[caster_name]
        stats.spells_cast += 1
        if slot_level > 0:
            stats.spell_slots_used[slot_level] = stats.spell_slots_used.get(slot_level, 0) + 1

    def record_heal(self, round_num: int, source_name: str, target_name: str,
                    amount: int, ability_name: str = "",
                    source_is_player: bool = False, target_is_player: bool = False):
        """Record a healing event."""
        event = HealEvent(
            round=round_num, source_name=source_name, target_name=target_name,
            amount=amount, source_ability=ability_name,
        )
        self.heal_events.append(event)

        self._ensure_entity(source_name, source_is_player)
        self._ensure_entity(target_name, target_is_player)
        self.entity_stats[source_name].total_healing_done += amount
        self.entity_stats[target_name].total_healing_received += amount

    def record_condition(self, round_num: int, target_name: str, condition: str,
                         applied_by: str = "", event_type: str = "applied",
                         target_is_player: bool = False, applier_is_player: bool = False):
        """Record a condition applied or removed."""
        event = ConditionEvent(
            round=round_num, target_name=target_name, condition=condition,
            applied_by=applied_by, event_type=event_type,
        )
        self.condition_events.append(event)

        self._ensure_entity(target_name, target_is_player)
        if event_type == "applied":
            self.entity_stats[target_name].conditions_suffered += 1
            if applied_by:
                self._ensure_entity(applied_by, applier_is_player)
                self.entity_stats[applied_by].conditions_applied += 1

    def record_saving_throw(self, round_num: int, entity_name: str,
                            passed: bool, is_death_save: bool = False,
                            entity_is_player: bool = False):
        """Record a saving throw result."""
        self._ensure_entity(entity_name, entity_is_player)
        stats = self.entity_stats[entity_name]
        if is_death_save:
            stats.death_saves_made += 1
            if passed:
                stats.death_saves_passed += 1
        else:
            stats.saving_throws_made += 1
            if passed:
                stats.saving_throws_passed += 1

    def record_kill(self, round_num: int, killer_name: str, target_name: str,
                    killer_is_player: bool = False, target_is_player: bool = False):
        """Record a kill."""
        self._ensure_entity(killer_name, killer_is_player)
        self.entity_stats[killer_name].kills += 1

        event = DeathEvent(
            round=round_num, entity_name=target_name,
            event_type="death", killed_by=killer_name,
        )
        self.death_events.append(event)

    def record_downed(self, round_num: int, entity_name: str,
                      entity_is_player: bool = False):
        """Record when an entity is knocked to 0 HP."""
        self._ensure_entity(entity_name, entity_is_player)
        self.entity_stats[entity_name].times_downed += 1

    def record_movement(self, entity_name: str, distance_ft: float,
                        entity_is_player: bool = False):
        """Record movement distance."""
        self._ensure_entity(entity_name, entity_is_player)
        self.entity_stats[entity_name].movement_total_ft += distance_ft

    def record_round_active(self, entity_name: str, entity_is_player: bool = False):
        """Record that entity was active (alive) during a round."""
        self._ensure_entity(entity_name, entity_is_player)
        self.entity_stats[entity_name].rounds_active += 1

    # ------------------------------------------------------------------ #
    # Finalize                                                             #
    # ------------------------------------------------------------------ #

    def finalize(self, entities: list, total_rounds: int, winner: str):
        """Finalize statistics at combat end."""
        self.total_rounds = total_rounds
        self.combat_end_round = total_rounds
        self.winner = winner
        for entity in entities:
            if entity.name in self.entity_stats:
                self.entity_stats[entity.name].ending_hp = entity.hp

    # ------------------------------------------------------------------ #
    # Resource Usage Summary                                               #
    # ------------------------------------------------------------------ #

    def get_resource_usage(self, entity_name: str) -> dict:
        """Get resource usage summary for an entity (comparing start vs current)."""
        initial = self._initial_states.get(entity_name, {})
        if not initial:
            return {}

        result = {}
        # Spell slots
        initial_slots = initial.get("spell_slots", {})
        if initial_slots:
            slots_used = {}
            for key, count in initial_slots.items():
                # We track in spell_events, but also can compare initial snapshot
                used = self.entity_stats.get(entity_name, EntityCombatStats(name=entity_name))
                slots_used[key] = count  # initial count
            result["initial_spell_slots"] = initial_slots

        # Other resources
        for resource, label in [
            ("ki_points", "Ki Points"),
            ("sorcery_points", "Sorcery Points"),
            ("lay_on_hands", "Lay on Hands HP"),
            ("rages_left", "Rages"),
            ("bardic_inspiration", "Bardic Inspiration"),
        ]:
            if initial.get(resource, 0) > 0:
                result[label] = {"initial": initial[resource]}

        return result

    # ------------------------------------------------------------------ #
    # Serialization                                                        #
    # ------------------------------------------------------------------ #

    def to_dict(self) -> dict:
        """Serialize all stats to a dictionary for saving."""
        return {
            "total_rounds": self.total_rounds,
            "winner": self.winner,
            "damage_events": [
                {
                    "round": e.round, "source": e.source_name, "target": e.target_name,
                    "amount": e.amount, "type": e.damage_type, "ability": e.source_ability,
                    "crit": e.is_critical, "aoe": e.is_aoe,
                } for e in self.damage_events
            ],
            "spell_events": [
                {
                    "round": e.round, "caster": e.caster_name, "spell": e.spell_name,
                    "slot": e.slot_level, "targets": e.targets,
                    "damage": e.total_damage, "healing": e.total_healing,
                    "condition": e.applied_condition,
                } for e in self.spell_events
            ],
            "heal_events": [
                {
                    "round": e.round, "source": e.source_name, "target": e.target_name,
                    "amount": e.amount, "ability": e.source_ability,
                } for e in self.heal_events
            ],
            "condition_events": [
                {
                    "round": e.round, "target": e.target_name, "condition": e.condition,
                    "applied_by": e.applied_by, "type": e.event_type,
                } for e in self.condition_events
            ],
            "death_events": [
                {
                    "round": e.round, "entity": e.entity_name,
                    "type": e.event_type, "killed_by": e.killed_by,
                } for e in self.death_events
            ],
            "entity_stats": {
                name: {
                    "name": s.name, "is_player": s.is_player,
                    "starting_hp": s.starting_hp, "ending_hp": s.ending_hp,
                    "max_hp": s.max_hp,
                    "damage_dealt": s.total_damage_dealt,
                    "damage_taken": s.total_damage_taken,
                    "healing_done": s.total_healing_done,
                    "healing_received": s.total_healing_received,
                    "kills": s.kills, "times_downed": s.times_downed,
                    "attacks_made": s.attacks_made, "attacks_hit": s.attacks_hit,
                    "critical_hits": s.critical_hits,
                    "spells_cast": s.spells_cast,
                    "spell_slots_used": s.spell_slots_used,
                    "conditions_applied": s.conditions_applied,
                    "conditions_suffered": s.conditions_suffered,
                    "saving_throws": f"{s.saving_throws_passed}/{s.saving_throws_made}",
                    "death_saves": f"{s.death_saves_passed}/{s.death_saves_made}",
                    "damage_by_type": s.damage_by_type,
                    "damage_by_ability": s.damage_by_ability,
                    "movement_ft": s.movement_total_ft,
                    "rounds_active": s.rounds_active,
                    "hit_rate": f"{s.attacks_hit}/{s.attacks_made}" if s.attacks_made > 0 else "N/A",
                } for name, s in self.entity_stats.items()
            },
            "initial_states": self._initial_states,
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)
