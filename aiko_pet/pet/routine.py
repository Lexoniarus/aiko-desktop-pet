"""Local day/week context for a chibi desktop companion, not a school schedule.

The time is read from the operating system.  These are optional, gently
structured habits: Aiko does not leave the desktop or have obligations.
"""

from __future__ import annotations

from collections.abc import Collection
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from .content import GERMAN_TEXT

# (start minute since midnight, period, label, optional meal)
WEEKDAY_SLOTS = (
    (0, "night", "Nachtruhe", None),
    (7 * 60 + 30, "breakfast", "Frühstückszeit", "breakfast"),
    (9 * 60, "quiet", "Ruhiger Vormittag", None),
    (12 * 60 + 30, "lunch", "Mittagszeit", "lunch"),
    (14 * 60, "free", "Eigene Zeit", None),
    (18 * 60 + 30, "dinner", "Abendessen", "dinner"),
    (20 * 60, "evening", "Gemütlicher Abend", None),
    (23 * 60 + 30, "night", "Nachtruhe", None),
)
WEEKEND_SLOTS = (
    (0, "night", "Nachtruhe", None),
    (9 * 60, "breakfast", "Langsamer Morgen", "breakfast"),
    (11 * 60 + 30, "free", "Eigene Zeit", None),
    (13 * 60 + 30, "lunch", "Mittagszeit", "lunch"),
    (15 * 60, "free", "Eigene Zeit", None),
    (19 * 60 + 30, "dinner", "Abendessen", "dinner"),
    (21 * 60, "evening", "Ruhiger Abend", None),
)
SUNDAY_SLOTS = WEEKEND_SLOTS + (
    (23 * 60 + 30, "night", "Nachtruhe", None),
)

MEAL_NAMES = {
    period: GERMAN_TEXT.format(f"meal.{period}")
    for period in ("breakfast", "lunch", "dinner")
}


def slots_for_day(day: date) -> tuple[tuple[int, str, str, str | None], ...]:
    if day.weekday() == 6:
        return SUNDAY_SLOTS
    if day.weekday() == 5:
        return WEEKEND_SLOTS
    return WEEKDAY_SLOTS


@dataclass(frozen=True)
class TimeContext:
    """Time and day snapshot; no narrative/world or school references."""

    local: datetime
    period: str
    activity: str
    meal: str | None
    next_activity: str
    next_time: str

    @property
    def day_key(self) -> str:
        return self.local.date().isoformat()

    @property
    def weekend(self) -> bool:
        return self.local.weekday() >= 5

    @property
    def night(self) -> bool:
        return self.period == "night"

    @property
    def night_key(self) -> str:
        """One stable key for each overnight stretch, including midnight."""
        day = self.local.date()
        if self.night and self.local.hour < 12:
            day -= timedelta(days=1)
        return day.isoformat()


def due_meal(
    context: TimeContext, *, meals_date: str, meals_today: Collection[str],
) -> str | None:
    """Identify a current meal not yet recorded in this day's pet history."""
    if context.meal is not None and (
        context.day_key != meals_date or context.meal not in meals_today
    ):
        return context.meal
    return None


def context_at(timestamp: float) -> TimeContext:
    """Use local wall time, including weekday/DST from the operating system."""
    local = datetime.fromtimestamp(timestamp).astimezone()
    day = local.date()
    slots = slots_for_day(day)
    minute = local.hour * 60 + local.minute
    index = max(i for i, slot in enumerate(slots) if slot[0] <= minute)
    _start, period, activity, meal = slots[index]

    future = [(day, slot) for slot in slots[index + 1 :]]
    tomorrow = day + timedelta(days=1)
    future.extend((tomorrow, slot) for slot in slots_for_day(tomorrow))
    _next_day, next_slot = next(
        (day_of_slot, slot) for day_of_slot, slot in future if slot[1] != period
    )
    next_minute, _next_period, next_activity, _next_meal = next_slot
    return TimeContext(
        local=local,
        period=period,
        activity=activity,
        meal=meal,
        next_activity=next_activity,
        next_time=f"{next_minute // 60:02d}:{next_minute % 60:02d}",
    )
