"""Pure daily-routine and bounded-time planning for the pet aggregate.

Policies calculate transitions and time steps; PetState owns every mutation.
Old module-level functions remain callable as public PetState method adapters.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Protocol

from .routine import TimeContext, context_at

MAX_CATCHUP_SECONDS = 8 * 60 * 60
SIMULATION_STEP_SECONDS = 300
# Live telemetry is never projected across a restart/suspend or offline gap.
MAX_LIVE_EFFORT_SECONDS = 30.0


class RoutineValues(Protocol):
    sleeping: bool
    sleep_origin: str
    nap_until: float
    auto_sleep_night: str
    auto_nap_day: str


@dataclass(frozen=True, slots=True)
class RoutineTransition:
    """Calculated sleep/routine fields, without changing the input pet."""

    sleeping: bool
    sleep_origin: str
    nap_until: float
    auto_sleep_night: str
    auto_nap_day: str


@dataclass(frozen=True, slots=True)
class SimulationStep:
    """One bounded interval and the workload actually known for that interval."""

    hours: float
    context: TimeContext | None
    effort: float | None


def calculate_daily_routine(
    record: RoutineValues,
    context: TimeContext,
    *,
    allow_bedtime: bool = True,
    allow_nap: bool = False,
    interrupt_nap: bool = False,
    effort: float | None = None,
) -> RoutineTransition:
    """Apply the established sleep priority to local values, without writes."""
    sleeping = record.sleeping
    origin = record.sleep_origin
    nap_until = record.nap_until
    night = record.auto_sleep_night
    nap_day = record.auto_nap_day
    stamp = context.local.timestamp()
    if origin == "nap" and (stamp >= nap_until or interrupt_nap):
        sleeping = False
        origin = ""
        nap_until = 0.0
    if not allow_bedtime and origin == "routine":
        sleeping = False
        origin = ""
        night = ""
    if context.night and allow_bedtime:
        if origin == "nap":
            origin = "routine"
            nap_until = 0.0
            night = context.night_key
        if night != context.night_key:
            night = context.night_key
            if not sleeping:
                sleeping = True
                origin = "routine"
    elif sleeping and origin == "routine":
        sleeping = False
        origin = ""
    elif (
        not context.night and allow_nap and not sleeping
        and nap_day != context.day_key
    ):
        sleeping = True
        origin = "nap"
        nap_until = stamp + 45 * 60
        nap_day = context.day_key
    return RoutineTransition(
        sleeping=sleeping,
        sleep_origin=origin,
        nap_until=nap_until,
        auto_sleep_night=night,
        auto_nap_day=nap_day,
    )


def plan_pet_time(
    updated_at: float,
    now: float,
    *,
    auto_routine: bool = False,
    effort: float | None = None,
) -> tuple[SimulationStep, ...] | None:
    """Plan the old bounded catch-up, never projecting stale telemetry."""
    if not math.isfinite(now):
        return None
    elapsed = max(0.0, min(MAX_CATCHUP_SECONDS, now - updated_at))
    if type(effort) not in (int, float):
        effort = None
    elif effort is not None and (
        not math.isfinite(effort) or not 0.0 <= effort <= 1.0
    ):
        effort = None
    known_since = now - min(elapsed, MAX_LIVE_EFFORT_SECONDS)
    if not auto_routine:
        if effort is None:
            return (SimulationStep(elapsed / 3600.0, None, None),)
        unseen_seconds = max(0.0, known_since - (now - elapsed))
        return (
            SimulationStep(unseen_seconds / 3600.0, None, None),
            SimulationStep((now - known_since) / 3600.0, None, effort),
        )
    steps: list[SimulationStep] = []
    cursor = now - elapsed
    while cursor < now:
        next_cursor = min(now, cursor + SIMULATION_STEP_SECONDS)
        if effort is not None and cursor < known_since < next_cursor:
            next_cursor = known_since
        steps.append(SimulationStep(
            hours=(next_cursor - cursor) / 3600.0,
            context=context_at((cursor + next_cursor) / 2),
            effort=effort if cursor >= known_since else None,
        ))
        cursor = next_cursor
    return tuple(steps)


class PetTimeline(Protocol):
    """Public aggregate operation for legacy module-level compatibility."""

    def advance(
        self,
        now: float,
        *,
        auto_routine: bool = False,
        allow_bedtime: bool | None = None,
        allow_nap: bool = False,
        interrupt_nap: bool = False,
        effort: float | None = None,
    ) -> None: ...


class RoutineActor(Protocol):
    def update_daily_routine(
        self,
        context: TimeContext,
        *,
        allow_bedtime: bool = True,
        allow_nap: bool = False,
        interrupt_nap: bool = False,
        effort: float | None = None,
    ) -> None: ...


def apply_daily_routine(
    record: RoutineActor,
    context: TimeContext,
    *,
    allow_bedtime: bool = True,
    allow_nap: bool = False,
    interrupt_nap: bool = False,
    effort: float | None = None,
) -> None:
    """Legacy adapter to the aggregate's explicit calendar operation."""
    record.update_daily_routine(
        context, allow_bedtime=allow_bedtime,
        allow_nap=allow_nap, interrupt_nap=interrupt_nap, effort=effort,
    )


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
    """Legacy adapter; the aggregate now executes its own planned steps."""
    record.advance(
        now, auto_routine=auto_routine, allow_bedtime=allow_bedtime,
        allow_nap=allow_nap, interrupt_nap=interrupt_nap, effort=effort,
    )
