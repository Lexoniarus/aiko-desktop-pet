"""Pure daily-routine and streaming elapsed-time planning for the aggregate.

Policies calculate transitions and time steps; PetState owns every mutation.
"""

from __future__ import annotations

import math
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Protocol

from .balance import BALANCE
from .food import FoodActivity
from .routine import TimeContext, context_at

SIMULATION_STEP_SECONDS = BALANCE.integer("simulation", "step_seconds")
# Live telemetry is never projected across a restart/suspend or offline gap.
MAX_LIVE_EFFORT_SECONDS = BALANCE.number("simulation", "maximum_live_effort_seconds")


class RoutineValues(Protocol):
    """Read-only routine inputs for the pure transition policy."""

    @property
    def sleeping(self) -> bool: ...

    @property
    def sleep_origin(self) -> str: ...

    @property
    def nap_until(self) -> float: ...

    @property
    def auto_sleep_night(self) -> str: ...

    @property
    def auto_nap_day(self) -> str: ...


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
    food_activity: FoodActivity | None = None
    observed: bool = False


@dataclass(frozen=True, slots=True)
class TimePlan:
    """Full elapsed duration with constant-memory iteration, never an age cap."""

    now: float
    elapsed_seconds: float
    auto_routine: bool
    effort: float | None
    food_activity: FoodActivity | None

    def __iter__(self) -> Iterator[SimulationStep]:
        cursor = self.now - self.elapsed_seconds
        known_since = self.now - min(self.elapsed_seconds, MAX_LIVE_EFFORT_SECONDS)
        while cursor < self.now:
            if self.auto_routine:
                # Align the grid across calls instead of drifting after restart.
                boundary = (math.floor(cursor / SIMULATION_STEP_SECONDS) + 1)
                end = min(self.now, boundary * SIMULATION_STEP_SECONDS)
            else:
                end = self.now
            if cursor < known_since < end:
                end = known_since
            observed = cursor >= known_since
            yield SimulationStep(
                hours=(end - cursor) / 3600.0,
                context=context_at(cursor) if self.auto_routine else None,
                effort=self.effort if observed else None,
                food_activity=self.food_activity if observed else None,
                observed=observed,
            )
            cursor = end


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
        not context.night and allow_nap and not sleeping and nap_day != context.day_key
    ):
        sleeping = True
        origin = "nap"
        nap_until = stamp + BALANCE.integer("simulation", "nap_seconds")
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
    elapsed_seconds: float | None = None,
    food_activity: FoodActivity | None = None,
) -> TimePlan | None:
    """Plan all elapsed time; current observations cover only a recent tail."""
    if not math.isfinite(now):
        return None
    duration = now - updated_at if elapsed_seconds is None else elapsed_seconds
    if not math.isfinite(duration):
        return None
    elapsed = max(0.0, duration)
    if type(effort) not in (int, float):
        effort = None
    elif effort is not None and (not math.isfinite(effort) or not 0.0 <= effort <= 1.0):
        effort = None
    return TimePlan(now, elapsed, auto_routine, effort, food_activity)
