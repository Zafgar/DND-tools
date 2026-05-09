"""Campaign in-game calendar helpers.

Pure logic, no pygame. Tracks in-game day/month/year + time-of-day
cycle. The DM advances time via:

  * ``advance_time_of_day(campaign)`` — dawn → day → dusk → night
    → next day's dawn.
  * ``advance_days(campaign, n)`` — fast-forward N days, also rolling
    months / years (PHB Forgotten-Realms-style 30-day months by
    default; configurable via ``DAYS_PER_MONTH`` / ``MONTHS_PER_YEAR``).
"""
from __future__ import annotations

from typing import List, Tuple

from data.campaign import Campaign


TIME_OF_DAY_CYCLE = ("dawn", "day", "dusk", "night")
DAYS_PER_MONTH = 30
MONTHS_PER_YEAR = 12

# Month names default to a generic Forgotten-Realms-ish ladder. The
# DM can override per-campaign by calling ``set_month_names``.
_DEFAULT_MONTHS = (
    "Hammer", "Alturiak", "Ches", "Tarsakh", "Mirtul", "Kythorn",
    "Flamerule", "Eleasis", "Eleint", "Marpenoth", "Uktar", "Nightal",
)
_MONTH_NAMES = list(_DEFAULT_MONTHS)


def set_month_names(names: List[str]) -> None:
    """Override the month-name list (length must match
    ``MONTHS_PER_YEAR``)."""
    if len(names) != MONTHS_PER_YEAR:
        raise ValueError(
            f"need exactly {MONTHS_PER_YEAR} month names"
        )
    _MONTH_NAMES[:] = names


def month_name(month: int) -> str:
    idx = max(1, min(MONTHS_PER_YEAR, int(month))) - 1
    return _MONTH_NAMES[idx]


# --------------------------------------------------------------------- #
# Time-of-day
# --------------------------------------------------------------------- #
def time_of_day_step(current: str) -> Tuple[str, bool]:
    """Return ``(next_time_of_day, rolled_to_new_day)``.
    ``rolled_to_new_day`` is True when night → dawn."""
    cur = (current or "day").lower()
    if cur not in TIME_OF_DAY_CYCLE:
        cur = "day"
    idx = TIME_OF_DAY_CYCLE.index(cur)
    next_idx = (idx + 1) % len(TIME_OF_DAY_CYCLE)
    rolled = next_idx == 0   # we wrapped past night → dawn
    return TIME_OF_DAY_CYCLE[next_idx], rolled


def advance_time_of_day(campaign: Campaign) -> dict:
    """Tick the time-of-day forward; if it rolls past night, advance
    the calendar by one day. Returns ``{time_of_day, rolled, day,
    month, year}``."""
    next_tod, rolled = time_of_day_step(campaign.time_of_day)
    campaign.time_of_day = next_tod
    if rolled:
        advance_days(campaign, 1)
    return {
        "time_of_day": campaign.time_of_day,
        "rolled": rolled,
        "day": campaign.in_game_day,
        "month": campaign.in_game_month,
        "year": campaign.in_game_year,
    }


def advance_days(campaign: Campaign, n: int = 1) -> dict:
    """Fast-forward ``n`` days. Adjusts month / year on overflow."""
    if n <= 0:
        return {
            "day": campaign.in_game_day,
            "month": campaign.in_game_month,
            "year": campaign.in_game_year,
        }
    day = int(campaign.in_game_day) + int(n)
    month = int(campaign.in_game_month)
    year = int(campaign.in_game_year)
    while day > DAYS_PER_MONTH:
        day -= DAYS_PER_MONTH
        month += 1
        if month > MONTHS_PER_YEAR:
            month = 1
            year += 1
    campaign.in_game_day = day
    campaign.in_game_month = month
    campaign.in_game_year = year
    return {"day": day, "month": month, "year": year}


def set_calendar(campaign: Campaign, *, day: int = None,
                   month: int = None, year: int = None,
                   time_of_day: str = None) -> None:
    """Direct setter for arbitrary jumps (e.g. session boundary)."""
    if day is not None:
        campaign.in_game_day = max(1, min(DAYS_PER_MONTH, int(day)))
    if month is not None:
        campaign.in_game_month = max(1, min(MONTHS_PER_YEAR,
                                              int(month)))
    if year is not None:
        campaign.in_game_year = max(1, int(year))
    if time_of_day is not None:
        campaign.time_of_day = (time_of_day if time_of_day in
                                  TIME_OF_DAY_CYCLE else "day")


def format_date(campaign: Campaign) -> str:
    """Compact date string ('5th of Mirtul, 1492 — day')."""
    suf = _ordinal_suffix(campaign.in_game_day)
    return (f"{campaign.in_game_day}{suf} of "
            f"{month_name(campaign.in_game_month)}, "
            f"{campaign.in_game_year} — {campaign.time_of_day}")


def _ordinal_suffix(n: int) -> str:
    if 11 <= (n % 100) <= 13:
        return "th"
    return {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
