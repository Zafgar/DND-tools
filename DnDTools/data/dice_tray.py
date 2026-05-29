"""Phase 45 — DM dice tray (pure logic).

The combat engine's :mod:`engine.dice` rolls *totals*. The DM-facing
dice tray needs the *breakdown* — which individual dice came up what,
whether advantage/disadvantage applied, the modifier, a label, and a
rolling history the widget can re-roll from.

Pure logic, no pygame. The widget in ``states/dice_tray_widget.py``
renders :class:`DiceRoll` objects this module produces.
"""
from __future__ import annotations

import random
import re
from dataclasses import dataclass, field
from typing import List, Optional


# A roll request like "2d6+3", "d20", "4d8-2", "3d6 + 1d4".
_TERM = re.compile(r"([+-]?)\s*(\d*)d(\d+)|([+-]?\s*\d+)", re.IGNORECASE)


@dataclass
class DieGroup:
    """One ``NdM`` term within a roll, with the individual results."""
    count: int
    sides: int
    rolls: List[int] = field(default_factory=list)
    sign: int = 1                      # +1 or -1

    @property
    def subtotal(self) -> int:
        return self.sign * sum(self.rolls)

    def label(self) -> str:
        s = "-" if self.sign < 0 else ""
        return f"{s}{self.count}d{self.sides}"


@dataclass
class DiceRoll:
    expression: str                     # the normalised expression
    groups: List[DieGroup] = field(default_factory=list)
    flat_modifier: int = 0
    total: int = 0
    label: str = ""                     # "Goblin attack", "Stealth", …
    mode: str = "normal"                # normal | advantage | disadvantage
    # For advantage/disadvantage on a single d20 we keep both rolls.
    adv_pair: Optional[tuple] = None    # (kept, discarded)
    timestamp: str = ""

    def breakdown(self) -> str:
        """Human-readable breakdown e.g. '2d6[4,5] +3 = 12'."""
        parts = []
        for g in self.groups:
            rolls_str = ",".join(str(r) for r in g.rolls)
            sign = "-" if g.sign < 0 else ("+" if parts else "")
            parts.append(f"{sign}{g.label().lstrip('-')}[{rolls_str}]")
        if self.flat_modifier:
            parts.append(f"{'+' if self.flat_modifier >= 0 else '-'}"
                          f"{abs(self.flat_modifier)}")
        body = " ".join(parts) if parts else "0"
        if self.adv_pair:
            kept, disc = self.adv_pair
            body += f"  ({self.mode}: kept {kept}, dropped {disc})"
        return f"{body} = {self.total}"


def _now() -> str:
    import time
    return time.strftime("%H:%M:%S")


def parse_expression(expr: str) -> tuple:
    """Parse '2d6+3' → ([(count, sides, sign)], flat_modifier).

    Bare integers become the flat modifier. Returns ([], 0) for junk.
    """
    expr = (expr or "").strip().lower().replace(" ", "")
    if not expr:
        return [], 0
    groups = []
    flat = 0
    for m in _TERM.finditer(expr):
        sign_str, count_str, sides_str, flat_str = m.groups()
        if sides_str:  # NdM term
            sign = -1 if sign_str == "-" else 1
            count = int(count_str) if count_str else 1
            groups.append((count, int(sides_str), sign))
        elif flat_str:
            flat += int(flat_str.replace(" ", ""))
    return groups, flat


def roll_expression(expr: str, *, label: str = "",
                      mode: str = "normal",
                      rng: Optional[random.Random] = None) -> DiceRoll:
    """Roll a dice expression and return a fully broken-down result.

    ``mode`` of "advantage"/"disadvantage" only applies to a single
    ``1d20`` (the canonical 5e case) — it rolls twice and keeps the
    higher/lower. For any other expression mode is ignored.
    """
    r = rng or random
    groups_spec, flat = parse_expression(expr)
    roll = DiceRoll(expression=expr or "", flat_modifier=flat,
                     label=label, mode=mode, timestamp=_now())

    # Advantage/disadvantage special-case: a lone d20.
    is_lone_d20 = (len(groups_spec) == 1
                    and groups_spec[0][0] == 1
                    and groups_spec[0][1] == 20
                    and groups_spec[0][2] == 1)
    if is_lone_d20 and mode in ("advantage", "disadvantage"):
        a, b = r.randint(1, 20), r.randint(1, 20)
        kept = max(a, b) if mode == "advantage" else min(a, b)
        disc = min(a, b) if mode == "advantage" else max(a, b)
        g = DieGroup(count=1, sides=20, rolls=[kept], sign=1)
        roll.groups.append(g)
        roll.adv_pair = (kept, disc)
        roll.total = kept + flat
        return roll

    for count, sides, sign in groups_spec:
        g = DieGroup(count=count, sides=sides, sign=sign)
        g.rolls = [r.randint(1, sides) for _ in range(count)]
        roll.groups.append(g)
    roll.total = sum(g.subtotal for g in roll.groups) + flat
    return roll


# --------------------------------------------------------------------- #
# History — the widget keeps a rolling log the DM can re-roll from
# --------------------------------------------------------------------- #

class DiceTray:
    """Holds recent rolls (most-recent first) plus the DM's quick
    buttons.  The UI widget wraps this."""
    MAX_HISTORY = 30

    QUICK_PRESETS = [
        ("d20", "d20"),
        ("Adv", "d20:advantage"),
        ("Dis", "d20:disadvantage"),
        ("d4", "1d4"),
        ("d6", "1d6"),
        ("d8", "1d8"),
        ("d10", "1d10"),
        ("d12", "1d12"),
        ("d100", "1d100"),
        ("2d6", "2d6"),
    ]

    def __init__(self, rng: Optional[random.Random] = None):
        self.history: List[DiceRoll] = []
        self._rng = rng

    def roll(self, expr: str, *, label: str = "",
              mode: str = "normal") -> DiceRoll:
        result = roll_expression(expr, label=label, mode=mode,
                                   rng=self._rng)
        self.history.insert(0, result)
        del self.history[self.MAX_HISTORY:]
        return result

    def roll_preset(self, preset_value: str,
                      label: str = "") -> DiceRoll:
        """A preset value can carry a mode: 'd20:advantage'."""
        if ":" in preset_value:
            expr, mode = preset_value.split(":", 1)
        else:
            expr, mode = preset_value, "normal"
        return self.roll(expr, label=label, mode=mode)

    def reroll_last(self) -> Optional[DiceRoll]:
        if not self.history:
            return None
        last = self.history[0]
        return self.roll(last.expression, label=last.label,
                          mode=last.mode)

    def clear(self) -> None:
        self.history.clear()
