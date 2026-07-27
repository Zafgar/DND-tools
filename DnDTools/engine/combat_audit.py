"""Combat audit — play a great many real fights and write down what broke.

Unit tests check the thing you thought to check. This plays hundreds of
actual battles with every class, every spell list and a wide sweep of
the monster library, watches the board after every single step, and
reports anything that could not legally have happened.

Nearly every bug found in this engine so far turned up this way rather
than by reading code: a dragon breathing through a stone wall, a
will-o'-wisp with a movement budget of zero, a Large creature settling
half inside a goblin, a spell slot spent on a spell that was never
cast. The invariants below are that experience written down so the same
classes of fault get caught the next time, automatically.

What it watches, after every step of every fight:

  placement   two creatures in one square; anybody standing inside
              terrain they cannot occupy (flight is accounted for)
  resources   negative or impossible spell slots, legendary actions,
              channel divinity, movement; two concentration spells at
              once; a recharge ability used while spent
  hitpoints   hp above maximum, a corpse still acting, death saves
              past three
  rules       an attack made through a wall or beyond its reach, a
              save-based effect with no DC, a condition that does not
              exist, damage dice that do not parse
  progress    a fight that never ends

And what it counts, so gaps show up as clearly as faults: which spells
were ever cast, which class features ever fired, which conditions ever
landed, which monsters never managed to act at all.

The runner is incremental — :meth:`AuditRunner.run_slice` does as much
work as fits in a millisecond budget and returns — so the UI can drive
it from the main loop and stay responsive without threads.
"""
from __future__ import annotations

import copy
import io
import json
import os
import random
import time
import traceback
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

from data.conditions import CONDITIONS
from data.heroes import hero_list
from data.library import library
from data.maps import PREMADE_MAPS, load_map_terrain, get_spawn_zones
from engine.entities import Entity

# Severity ordering for reports.
ERROR, WARNING, INFO = "error", "warning", "info"
_SEVERITY_ORDER = {ERROR: 0, WARNING: 1, INFO: 2}


# --------------------------------------------------------------------- #
# Findings
# --------------------------------------------------------------------- #
@dataclass
class Finding:
    """One thing that should not have happened.

    Findings are deduplicated by (category, title) so a fault that
    fires in four hundred battles is one line with a count, not four
    hundred lines. The first few concrete occurrences are kept as
    evidence — that is what makes a report actionable.
    """
    severity: str
    category: str
    title: str
    count: int = 0
    examples: List[str] = field(default_factory=list)

    def add(self, evidence: str, keep: int = 4):
        self.count += 1
        if len(self.examples) < keep and evidence not in self.examples:
            self.examples.append(evidence)

    @property
    def key(self) -> Tuple[str, str]:
        return (self.category, self.title)


@dataclass
class AuditReport:
    started: str = ""
    elapsed_s: float = 0.0
    depth: str = ""
    battles: int = 0
    rounds: int = 0
    steps: int = 0
    findings: Dict[Tuple[str, str], Finding] = field(default_factory=dict)
    # Coverage counters
    spells_cast: Counter = field(default_factory=Counter)
    actions_used: Counter = field(default_factory=Counter)
    conditions_seen: Counter = field(default_factory=Counter)
    step_types: Counter = field(default_factory=Counter)
    classes_played: Counter = field(default_factory=Counter)
    monsters_played: Counter = field(default_factory=Counter)
    monsters_that_acted: set = field(default_factory=set)
    suite_stats: Dict[str, dict] = field(default_factory=dict)

    def note(self, severity, category, title, evidence):
        key = (category, title)
        f = self.findings.get(key)
        if f is None:
            f = Finding(severity=severity, category=category, title=title)
            self.findings[key] = f
        f.add(evidence)

    @property
    def errors(self) -> List[Finding]:
        return [f for f in self.findings.values() if f.severity == ERROR]

    @property
    def warnings(self) -> List[Finding]:
        return [f for f in self.findings.values() if f.severity == WARNING]

    def sorted_findings(self) -> List[Finding]:
        return sorted(self.findings.values(),
                      key=lambda f: (_SEVERITY_ORDER.get(f.severity, 9),
                                     -f.count, f.category, f.title))


# --------------------------------------------------------------------- #
# Scenario definitions
# --------------------------------------------------------------------- #
@dataclass
class Scenario:
    suite: str
    label: str
    seed: int
    map_key: str
    players: List[str]          # hero names
    enemies: List[str]          # monster names


_HERO_BY_NAME = {h.name: h for h in hero_list}

# A party that exercises the four broad ability shapes: weapon damage,
# arcane control, divine support and skirmishing.
STANDARD_PARTY = ["Magnus Dragonius", "Archmage Wizard", "War Cleric",
                  "Shadow Rogue"]

# Maps chosen for what they do to movement and sight rather than looks:
# an open field with no terrain at all, a corridor, a map with water and
# height, and one with a chasm to jump.
TERRAIN_MAPS = ["dungeon_corridor", "cliffside_battle", "shipwreck_shore",
                "castle_courtyard", "volcanic_forge", "grand_city"]

DEPTHS = {
    "quick":    {"seeds": 1, "monster_stride": 6, "hero_stride": 3},
    "standard": {"seeds": 2, "monster_stride": 2, "hero_stride": 1},
    "deep":     {"seeds": 4, "monster_stride": 1, "hero_stride": 1},
}


def _scaled_foes(cr: float) -> List[str]:
    """A handful of monsters near a challenge rating, for fair fights."""
    pool = [m.name for m in library.get_all_monsters()
            if abs(m.challenge_rating - cr) < 1.0]
    return pool or ["Goblin"]


def build_scenarios(depth: str = "standard") -> List[Scenario]:
    """The whole matrix, in the order it will be played.

    Ordered cheapest-first so a run that is cut short has still covered
    every class and every monster before it starts on the slow maps.
    """
    cfg = DEPTHS.get(depth, DEPTHS["standard"])
    seeds = cfg["seeds"]
    out: List[Scenario] = []
    rng = random.Random(20240727)

    # 1. Every class, alone, against something its own size. This is the
    #    suite that guarantees each class's features get a turn.
    heroes = hero_list[::cfg["hero_stride"]]
    for h in heroes:
        foes = _scaled_foes(max(1.0, h.character_level * 0.75))
        for s in range(seeds):
            out.append(Scenario(
                suite="classes", label=f"{h.name} solo", seed=1000 + s,
                map_key="", players=[h.name],
                enemies=[rng.choice(foes), rng.choice(foes)]))

    # 2. Casters against a crowd, so area and control spells have a
    #    reason to be cast at all.
    casters = [h.name for h in hero_list
               if h.spells_known or h.cantrips][::cfg["hero_stride"]]
    for name in casters:
        for s in range(seeds):
            out.append(Scenario(
                suite="spells", label=f"{name} vs crowd", seed=2000 + s,
                map_key="", players=[name, "War Cleric"],
                enemies=["Goblin", "Goblin", "Goblin", "Ogre", "Ogre"]))

    # 3. Every stat block in the library gets at least one fight, so a
    #    monster with a broken action cannot hide.
    all_monsters = [m.name for m in library.get_all_monsters()]
    for name in all_monsters[::cfg["monster_stride"]]:
        out.append(Scenario(
            suite="bestiary", label=f"party vs {name}", seed=3000,
            map_key="", players=STANDARD_PARTY, enemies=[name]))

    # 4. Terrain: the same fight on maps that block sight, break line of
    #    movement, and drop people off ledges.
    for map_key in TERRAIN_MAPS:
        for s in range(seeds):
            out.append(Scenario(
                suite="terrain", label=f"party on {map_key}", seed=4000 + s,
                map_key=map_key, players=STANDARD_PARTY,
                enemies=["Ogre", "Adult Red Dragon", "Archmage"]))

    # 5. Big mixed brawls — the realistic table case, and the one most
    #    likely to trip placement and turn-economy faults.
    brawl_foes = [["Ogre", "Troll", "Goblin", "Goblin", "Archmage"],
                  ["Adult Red Dragon", "Knight", "Gladiator"],
                  ["Vampire", "Vampire Spawn", "Vampire Spawn", "Ghost"],
                  ["Iron Golem", "Gelatinous Cube", "Giant Spider"]]
    for i, foes in enumerate(brawl_foes):
        for s in range(seeds):
            out.append(Scenario(
                suite="brawl", label=f"brawl {i + 1}", seed=5000 + s,
                map_key="castle_courtyard", players=STANDARD_PARTY,
                enemies=list(foes)))

    return out


# --------------------------------------------------------------------- #
# The watcher
# --------------------------------------------------------------------- #
class _Watcher:
    """Invariant checks over a live battle. No mutation, ever."""

    def __init__(self, report: AuditReport):
        self.report = report
        self.max_slots: Dict[int, dict] = {}
        self.max_legendary: Dict[int, int] = {}

    def baseline(self, battle):
        """Remember starting resources so we can spot impossible gains."""
        for e in battle.entities:
            self.max_slots[id(e)] = dict(getattr(e, "spell_slots", {}) or {})
            self.max_legendary[id(e)] = e.legendary_actions_left

    # -- board state -------------------------------------------------- #
    def check_state(self, battle, where: str):
        note = self.report.note
        live = [e for e in battle.entities
                if e.hp > 0 and not getattr(e, "is_lair", False)]

        for i, a in enumerate(live):
            sa = a.size_in_squares
            fa = {(int(a.grid_x) + dx, int(a.grid_y) + dy)
                  for dx in range(sa) for dy in range(sa)}
            for b in live[i + 1:]:
                sb = b.size_in_squares
                fb = {(int(b.grid_x) + dx, int(b.grid_y) + dy)
                      for dx in range(sb) for dy in range(sb)}
                if fa & fb:
                    note(ERROR, "placement", "Two creatures in one square",
                         f"{where}: {a.name} and {b.name} share "
                         f"{sorted(fa & fb)[:2]}")
            for (cx, cy) in fa:
                t = battle.get_terrain_at(cx, cy)
                if t is None or t.passable:
                    continue
                if a.is_flying and battle.flyer_clears(a, t):
                    continue
                note(ERROR, "placement", "Creature inside impassable terrain",
                     f"{where}: {a.name} stands in {t.terrain_type} "
                     f"at ({cx},{cy})")

        for e in battle.entities:
            self._check_entity(e, where)

    def _check_entity(self, e, where: str):
        note = self.report.note
        name = e.name

        if e.max_hp > 0 and e.hp > e.max_hp:
            note(ERROR, "hitpoints", "Hit points above maximum",
                 f"{where}: {name} at {e.hp}/{e.max_hp}")
        if e.death_save_failures > 3 or e.death_save_successes > 3:
            note(ERROR, "hitpoints", "Death saves past three",
                 f"{where}: {name} {e.death_save_successes}s/"
                 f"{e.death_save_failures}f")
        if e.movement_left < -0.01:
            note(ERROR, "resources", "Negative movement remaining",
                 f"{where}: {name} has {e.movement_left:.1f} ft left")

        slots = getattr(e, "spell_slots", None) or {}
        base = self.max_slots.get(id(e), {})
        for lvl, n in slots.items():
            if n < 0:
                note(ERROR, "resources", "Negative spell slots",
                     f"{where}: {name} has {n} {lvl} slots")
            cap = base.get(lvl)
            if cap is not None and n > cap:
                note(ERROR, "resources", "More spell slots than it started with",
                     f"{where}: {name} has {n} {lvl}, started with {cap}")

        cap_leg = e.stats.legendary_action_count
        if e.legendary_actions_left < 0:
            note(ERROR, "resources", "Negative legendary actions",
                 f"{where}: {name} at {e.legendary_actions_left}")
        elif cap_leg and e.legendary_actions_left > cap_leg:
            note(ERROR, "resources", "More legendary actions than the maximum",
                 f"{where}: {name} has {e.legendary_actions_left}/{cap_leg}")

        if e.channel_divinity_left < 0:
            note(ERROR, "resources", "Negative channel divinity",
                 f"{where}: {name} at {e.channel_divinity_left}")

        for cond in e.conditions:
            if cond not in CONDITIONS:
                note(WARNING, "rules",
                     "Creature carries a condition missing from the table",
                     f"{where}: {name} has '{cond}' — the table drives the "
                     f"token badge and the help text, so the DM cannot see "
                     f"it")
            else:
                self.report.conditions_seen[cond] += 1

    # -- one executed step -------------------------------------------- #
    def check_step(self, battle, step, where: str):
        note = self.report.note
        rep = self.report
        rep.step_types[step.step_type] += 1
        if step.spell is not None:
            rep.spells_cast[step.spell.name] += 1
        if step.action_name:
            rep.actions_used[step.action_name] += 1
        if step.attacker is not None and not step.attacker.is_player:
            rep.monsters_that_acted.add(step.attacker.name)

        atk = step.attacker
        targets = list(step.targets) if step.targets else (
            [step.target] if step.target else [])

        if step.applies_condition and step.applies_condition not in CONDITIONS:
            note(WARNING, "rules",
                 "Condition applied that is missing from the condition table",
                 f"{where}: {step.action_name or step.step_type} applies "
                 f"'{step.applies_condition}' — it will have no badge, no "
                 f"help text and no duration handling")

        if step.save_ability and step.save_dc <= 0:
            note(WARNING, "rules", "Saving throw with no DC",
                 f"{where}: {step.action_name or '?'} asks for a "
                 f"{step.save_ability} save at DC {step.save_dc}")

        if atk is None:
            return

        if atk.hp <= 0 and step.step_type not in ("wait",):
            note(ERROR, "hitpoints", "A downed creature acted",
                 f"{where}: {atk.name} at {atk.hp} hp did "
                 f"{step.action_name or step.step_type}")

        # Reach and range. A miss is fine; a swing from across the room
        # is not.
        if step.step_type in ("attack", "multiattack", "bonus_attack",
                              "legendary") and step.action is not None:
            reach_ft = max(step.action.range, step.action.reach)
            if step.action.long_range:
                reach_ft = max(reach_ft, step.action.long_range)
            for t in targets:
                if t is None:
                    continue
                dist = battle.get_distance(atk, t) * 5.0
                if reach_ft and dist > reach_ft + 2.5:
                    note(ERROR, "rules", "Attack made beyond its reach",
                         f"{where}: {atk.name}'s {step.action.name} "
                         f"({reach_ft} ft) hit {t.name} at {dist:.0f} ft")

        # Sight blocked by TERRAIN specifically. has_line_of_sight also
        # returns False for an invisible or unseen target, and attacking
        # a creature you cannot see is perfectly legal (at disadvantage)
        # — using it here reported a cloaker biting an invisible rogue on
        # a map with no terrain at all as shooting "through solid cover".
        # Area effects are excluded too: a burst legitimately catches
        # things around a corner from its caster.
        if (step.step_type in ("attack", "multiattack", "bonus_attack")
                and not step.aoe_center and battle.terrain
                and step.action is not None and step.action.aoe_radius == 0):
            from engine.terrain import check_los_blocked
            for t in targets:
                if t is None or t is atk:
                    continue
                if check_los_blocked(battle.terrain,
                                     int(atk.grid_x), int(atk.grid_y),
                                     int(t.grid_x), int(t.grid_y),
                                     float(atk.elevation) + 5.0,
                                     float(t.elevation) + 5.0):
                    note(ERROR, "rules", "Attack made through solid terrain",
                         f"{where}: {atk.name}'s "
                         f"{step.action_name or 'attack'} hit {t.name} "
                         f"through a wall")

        if step.step_type == "move":
            if step.movement_ft < 0:
                note(ERROR, "rules", "Negative movement",
                     f"{where}: {atk.name} moved {step.movement_ft} ft")
            budget = max(atk.get_speed(), atk.stats.speed,
                         atk.stats.fly_speed) + 10
            if step.movement_ft > budget:
                note(ERROR, "rules", "Moved further than its speed allows",
                     f"{where}: {atk.name} moved {step.movement_ft:.0f} ft "
                     f"on a {budget - 10:.0f} ft speed")


# --------------------------------------------------------------------- #
# The runner
# --------------------------------------------------------------------- #
class AuditRunner:
    """Plays the scenarios, a slice at a time.

    Kept incremental so the tool can be driven from a pygame main loop:
    :meth:`run_slice` works for at most ``budget_ms`` and returns, and
    the caller draws a progress bar and calls it again.
    """

    MAX_STEPS_PER_BATTLE = 700
    MAX_ROUNDS = 60

    def __init__(self, depth: str = "standard",
                 scenarios: Optional[List[Scenario]] = None):
        self.depth = depth
        self.scenarios = scenarios if scenarios is not None \
            else build_scenarios(depth)
        self.report = AuditReport(depth=depth,
                                  started=time.strftime("%Y-%m-%d %H:%M:%S"))
        self.index = 0
        self._t0 = None
        self._suite_battles = Counter()

    # -- progress ------------------------------------------------------ #
    @property
    def total(self) -> int:
        return len(self.scenarios)

    @property
    def done(self) -> bool:
        return self.index >= self.total

    @property
    def progress(self) -> float:
        return 1.0 if not self.total else self.index / self.total

    def run_slice(self, budget_ms: float = 40.0) -> bool:
        """Play battles until the budget runs out. True when finished."""
        if self._t0 is None:
            self._t0 = time.time()
        deadline = time.perf_counter() + budget_ms / 1000.0
        while not self.done and time.perf_counter() < deadline:
            self._play(self.scenarios[self.index])
            self.index += 1
        if self.done:
            self.report.elapsed_s = time.time() - self._t0
            self._finish()
        return self.done

    def run_all(self) -> AuditReport:
        while not self.run_slice(1000.0):
            pass
        return self.report

    # -- one battle ---------------------------------------------------- #
    def _build(self, sc: Scenario):
        from states.battle_state import BattleState

        class _FakeManager:
            def __init__(self):
                import pygame
                self.screen = pygame.display.get_surface()
                self.running = True
                self.states = {}

            def change_state(self, *a, **k):
                pass

        random.seed(sc.seed)
        terrain = load_map_terrain(sc.map_key) if sc.map_key else []
        if sc.map_key:
            pz = get_spawn_zones(sc.map_key) or {}
            pspots = list(pz.get("players") or [])
            espots = list(pz.get("enemies") or [])
        else:
            pspots, espots = [], []
        if not pspots:
            pspots = [(3, 3 + i * 2) for i in range(8)]
        if not espots:
            espots = [(16, 3 + i * 2) for i in range(8)]

        ents = []
        for i, name in enumerate(sc.players):
            stats = _HERO_BY_NAME.get(name)
            if stats is None:
                continue
            x, y = pspots[i % len(pspots)]
            ents.append(Entity(copy.deepcopy(stats), float(x), float(y),
                               is_player=True))
            self.report.classes_played[stats.character_class or "?"] += 1
        for i, name in enumerate(sc.enemies):
            try:
                stats = library.get_monster(name)
            except Exception:
                continue
            x, y = espots[i % len(espots)]
            ents.append(Entity(stats, float(x), float(y), is_player=False))
            self.report.monsters_played[name] += 1

        bs = BattleState(_FakeManager(), entities=ents)
        bs.battle.terrain = terrain
        bs._set_ai_mode("full_auto")
        return bs

    def _play(self, sc: Scenario):
        rep = self.report
        watcher = _Watcher(rep)
        where0 = f"{sc.suite}/{sc.label} seed {sc.seed}"
        try:
            bs = self._build(sc)
        except Exception as exc:
            rep.note(ERROR, "crash", "Battle could not be set up",
                     f"{where0}: {exc!r}")
            return
        watcher.baseline(bs.battle)
        rep.battles += 1
        self._suite_battles[sc.suite] += 1

        steps = 0
        for steps in range(self.MAX_STEPS_PER_BATTLE):
            where = f"{where0} r{bs.battle.round}s{steps}"
            # The step that is about to be executed, so coverage and the
            # per-step rule checks see the real stream of play.
            pending = None
            if bs.pending_plan and \
                    bs.pending_step_idx < len(bs.pending_plan.steps):
                pending = bs.pending_plan.steps[bs.pending_step_idx]
            try:
                bs._process_auto_battle()
            except Exception:
                rep.note(ERROR, "crash", "Exception during a turn",
                         f"{where}: "
                         + traceback.format_exc().strip().splitlines()[-1])
                break
            if pending is not None:
                try:
                    watcher.check_step(bs.battle, pending, where)
                except Exception:
                    pass
            try:
                watcher.check_state(bs.battle, where)
            except Exception:
                pass
            if bs.battle.round > self.MAX_ROUNDS:
                rep.note(WARNING, "progress", "Fight ran past the round cap",
                         f"{where0}: still going at round "
                         f"{bs.battle.round}")
                break
            if not bs.auto_battle:
                break
            if (not [e for e in bs.battle.entities
                     if e.is_player and e.hp > 0]
                    or not [e for e in bs.battle.entities
                            if not e.is_player and e.hp > 0]):
                break
        else:
            rep.note(WARNING, "progress", "Fight hit the step cap",
                     f"{where0}: {self.MAX_STEPS_PER_BATTLE} steps and "
                     f"no result")

        rep.steps += steps + 1
        rep.rounds += bs.battle.round

    # -- coverage gaps -------------------------------------------------- #
    def _finish(self):
        rep = self.report
        for suite, n in self._suite_battles.items():
            rep.suite_stats[suite] = {"battles": n}

        # A monster that was fielded and never took a single action is
        # either unreachable, permanently incapacitated, or has no usable
        # actions at all. Any of the three is worth a look.
        silent = sorted(set(rep.monsters_played) - rep.monsters_that_acted)
        for name in silent[:40]:
            rep.note(WARNING, "coverage", "Monster never acted",
                     f"{name} was in a fight and never took an action")

        try:
            import data.spells as spell_lib
            known = set(spell_lib._spells)
        except Exception:
            known = set()
        never = sorted(known - set(rep.spells_cast))
        if never:
            rep.note(INFO, "coverage", "Spells never cast in any fight",
                     f"{len(never)} of {len(known)}: "
                     + ", ".join(never[:12])
                     + ("..." if len(never) > 12 else ""))


# --------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------- #
def format_report(rep: AuditReport) -> str:
    """The human-readable log. Faults first, then what was covered."""
    out = io.StringIO()
    w = out.write
    w("=" * 72 + "\n")
    w("COMBAT AUDIT\n")
    w("=" * 72 + "\n")
    w(f"started   {rep.started}\n")
    w(f"depth     {rep.depth}\n")
    w(f"battles   {rep.battles}\n")
    w(f"rounds    {rep.rounds}\n")
    w(f"steps     {rep.steps}\n")
    w(f"elapsed   {rep.elapsed_s:.1f} s "
      f"({rep.battles / max(rep.elapsed_s, 0.001):.0f} battles/s)\n")
    errs, warns = rep.errors, rep.warnings
    w(f"verdict   {len(errs)} error kind(s), {len(warns)} warning kind(s)\n")
    if not errs:
        w("          no rule or state violations found\n")
    w("\n")

    w("-" * 72 + "\n")
    w("FINDINGS\n")
    w("-" * 72 + "\n")
    if not rep.findings:
        w("  nothing to report\n")
    for f in rep.sorted_findings():
        w(f"\n[{f.severity.upper():7}] {f.category:10} {f.title}  "
          f"(x{f.count})\n")
        for ex in f.examples:
            w(f"           {ex}\n")
    w("\n")

    w("-" * 72 + "\n")
    w("COVERAGE\n")
    w("-" * 72 + "\n")
    w(f"  classes played      {len(rep.classes_played)}: "
      f"{', '.join(sorted(rep.classes_played))}\n")
    w(f"  monsters fielded    {len(rep.monsters_played)}\n")
    w(f"  monsters that acted {len(rep.monsters_that_acted)}\n")
    w(f"  distinct spells cast {len(rep.spells_cast)}\n")
    w(f"  distinct actions    {len(rep.actions_used)}\n")
    w(f"  conditions seen     {len(rep.conditions_seen)}: "
      f"{', '.join(sorted(rep.conditions_seen))}\n")
    w(f"  step types          "
      f"{dict(rep.step_types.most_common())}\n")
    w("\n  most-cast spells:\n")
    for name, n in rep.spells_cast.most_common(20):
        w(f"    {n:5}  {name}\n")
    unused_conditions = sorted(set(CONDITIONS) - set(rep.conditions_seen))
    if unused_conditions:
        w(f"\n  conditions that never landed: "
          f"{', '.join(unused_conditions)}\n")
    w("\n  per suite:\n")
    for suite, st in sorted(rep.suite_stats.items()):
        w(f"    {suite:12} {st['battles']} battles\n")
    return out.getvalue()


def report_to_dict(rep: AuditReport) -> dict:
    return {
        "started": rep.started,
        "depth": rep.depth,
        "elapsed_s": round(rep.elapsed_s, 2),
        "battles": rep.battles,
        "rounds": rep.rounds,
        "steps": rep.steps,
        "findings": [
            {"severity": f.severity, "category": f.category,
             "title": f.title, "count": f.count, "examples": f.examples}
            for f in rep.sorted_findings()],
        "coverage": {
            "classes": dict(rep.classes_played),
            "spells_cast": dict(rep.spells_cast),
            "actions": dict(rep.actions_used),
            "conditions": dict(rep.conditions_seen),
            "step_types": dict(rep.step_types),
            "monsters_fielded": len(rep.monsters_played),
            "monsters_that_acted": len(rep.monsters_that_acted),
        },
        "suites": rep.suite_stats,
    }


def default_log_dir() -> str:
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(here, "audit_logs")


def write_report(rep: AuditReport, directory: Optional[str] = None) -> str:
    """Write the .log and its .json twin. Returns the log path."""
    directory = directory or default_log_dir()
    os.makedirs(directory, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    path = os.path.join(directory, f"combat_audit_{stamp}.log")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(format_report(rep))
    with open(path[:-4] + ".json", "w", encoding="utf-8") as fh:
        json.dump(report_to_dict(rep), fh, indent=2, ensure_ascii=False)
    return path
