"""Daily sleep/nap clock and bounded catch-up simulation for Aiko.

The persisted PetState implements PetTimeline; this module owns state evolution
without importing Tkinter, the save repository, or computer activity providers.
"""

from __future__ import annotations

import math
from typing import Protocol

from .routine import TimeContext, context_at

MAX_CATCHUP_SECONDS = 8 * 60 * 60
SIMULATION_STEP_SECONDS = 300
# Live telemetry is never projected across a restart/suspend or offline gap.
MAX_LIVE_EFFORT_SECONDS = 30.0


class PetTimeline(Protocol):
    """The clock's mutable state surface, implemented by PetState."""

    sleeping: bool
    sleep_origin: str
    nap_until: float
    auto_sleep_night: str
    auto_nap_day: str
    updated_at: float
    meals_date: str
    meals_today: list[str]

    def _roll_meals(self, context: TimeContext) -> None: ...

    def _apply_clock(
        self,
        context: TimeContext,
        *,
        allow_bedtime: bool = True,
        allow_nap: bool = False,
        interrupt_nap: bool = False,
        effort: float | None = None,
    ) -> None: ...

    def _decay(
        self, hours: float, context: TimeContext | None,
        effort: float | None = None,
    ) -> None: ...


def apply_daily_routine(
    record: PetTimeline,
    context: TimeContext,
    *,
    allow_bedtime: bool = True,
    allow_nap: bool = False,
    interrupt_nap: bool = False,
    effort: float | None = None,
) -> None:
    record._roll_meals(context)
    stamp = context.local.timestamp()
    if record.sleep_origin == "nap" and (
        stamp >= record.nap_until or interrupt_nap
    ):
        record.sleeping = False
        record.sleep_origin = ""
        record.nap_until = 0.0
    if not allow_bedtime and record.sleep_origin == "routine":
        # Aiko cannot remain automatically asleep during real computer work.
        record.sleeping = False
        record.sleep_origin = ""
        record.auto_sleep_night = ""
    if context.night and allow_bedtime:
        if record.sleep_origin == "nap":
            record.sleep_origin = "routine"
            record.nap_until = 0.0
            record.auto_sleep_night = context.night_key
        if record.auto_sleep_night != context.night_key:
            record.auto_sleep_night = context.night_key
            if not record.sleeping:
                record.sleeping = True
                record.sleep_origin = "routine"
    elif record.sleeping and record.sleep_origin == "routine":
        record.sleeping = False
        record.sleep_origin = ""
    elif (not context.night and allow_nap and not record.sleeping
          and record.auto_nap_day != context.day_key):
        record.sleeping = True
        record.sleep_origin = "nap"
        record.nap_until = stamp + 45 * 60
        record.auto_nap_day = context.day_key

def advance_pet_time(
    record: PetTimeline,
    now: float,
    *,
    auto_routine: bool = False,
    allow_bedtime: bool | None = None,
    allow_nap: bool = False,
    interrupt_nap: bool = False,
    effort: float | None = None,
) -> None:
    """Catch up at most eight hours, including local day/night transitions.

    For old saves, plain time decay stays available. With a routine enabled,
    simulate the most recent eight hours in short intervals so time offline
    overnight does not behave like eight waking hours.
    """
    if not math.isfinite(now):
        return
    elapsed = max(0.0, min(MAX_CATCHUP_SECONDS, now - record.updated_at))
    if (type(effort) not in (int, float) or not math.isfinite(effort)
            or not 0.0 <= effort <= 1.0):
        effort = None
    known_since = now - min(elapsed, MAX_LIVE_EFFORT_SECONDS)
    if not auto_routine:
        if effort is None:
            record._decay(elapsed / 3600.0, None)
        else:
            unseen_seconds = max(0.0, known_since - (now - elapsed))
            record._decay(unseen_seconds / 3600.0, None)
            record._decay((now - known_since) / 3600.0, None, effort)
        record._roll_meals(context_at(now))
    else:
        cursor = now - elapsed
        while cursor < now:
            next_cursor = min(now, cursor + SIMULATION_STEP_SECONDS)
            if effort is not None and cursor < known_since < next_cursor:
                next_cursor = known_since
            context = context_at((cursor + next_cursor) / 2)
            record._apply_clock(
                context, allow_bedtime=allow_bedtime is not False,
                allow_nap=allow_nap, interrupt_nap=interrupt_nap,
            )
            record._decay(
                (next_cursor - cursor) / 3600, context,
                effort if cursor >= known_since else None,
            )
            cursor = next_cursor
        record._apply_clock(
            context_at(now), allow_bedtime=allow_bedtime is not False,
            allow_nap=allow_nap,
        )
    record.updated_at = now
