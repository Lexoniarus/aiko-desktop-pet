"""Local workload and daily-rhythm coordination without Tk or view imports."""

from __future__ import annotations

import time
from dataclasses import dataclass, replace
from typing import Callable

from ..pet.balance import BALANCE
from ..pet.food import FoodActivity
from ..pet.mind import PetMind
from ..pet.mind.adaptive import AdaptiveRoutine
from ..pet.mind.adaptive_models import Observation
from ..pet.mind.catalog import Reaction
from ..pet.mind.workload_events import WorkloadEventDetector
from ..pet.routine import TimeContext, context_at
from ..pet.sleep import SleepContext
from ..pet.state import PetState
from ..telemetry import ComputerSnapshot, consumption_load, workload_intensity
from .active_time import (
    ActiveSessionClock,
    SessionInputs,
    TimeProgression,
    advance_session_time,
)
from .food_activity import FoodActivityHistory
from .ports import ComputerObservation
from .settings import PetSettings


@dataclass(frozen=True, slots=True)
class ActivityCallbacks:
    """No access to GUI internals: only specific side effects are injected."""

    read_idle_seconds: Callable[[], float | None]
    start_review: Callable[[float], None]
    react: Callable[[Reaction, int], None]
    action_until: Callable[[], float]
    last_spoken: Callable[[], float]
    read_pointer: Callable[[], tuple[int, int]] | None = None
    read_mouse_buttons: Callable[[], tuple[bool, bool] | None] | None = None
    defer_routine: Callable[[], bool] = lambda: False
    speech_busy: Callable[[], bool] = lambda: False


@dataclass(frozen=True, slots=True)
class TimeProgress:
    context: TimeContext
    period_changed: bool
    sleep_changed: bool


class ActivityCoordinator:
    """Own coarse sampling, sleep permissions and deferred work dialogue."""

    def __init__(
        self,
        state: PetState,
        settings: PetSettings,
        mind: PetMind,
        adaptive: AdaptiveRoutine,
        workload_events: WorkloadEventDetector,
        monitor: ComputerObservation,
        callbacks: ActivityCallbacks,
        *,
        clock: ActiveSessionClock,
        progression: TimeProgression | None = None,
    ) -> None:
        self.state = state
        self.settings = settings
        self.mind = mind
        self.adaptive = adaptive
        self.workload_events = workload_events
        self.monitor = monitor
        self.callbacks = callbacks
        self._clock = clock
        self._progression = progression
        self.last_hardware_sample = 0.0
        self.last_adaptive_sample = 0.0
        self.pending_computer_line: tuple[str, float] | None = None
        self.food_activity_history = FoodActivityHistory()
        self._unavailable_seconds = 0.0

    def set_observation_enabled(self, enabled: bool) -> None:
        """Stop or restart measured workload and clear old session readings."""
        self.settings.observe_computer = bool(enabled)
        self.monitor.set_enabled(self.settings.observe_computer)
        self.workload_events.reset_samples()
        self.last_hardware_sample = 0.0
        self.last_adaptive_sample = 0.0
        self.pending_computer_line = None
        if not enabled:
            self.mind.set_situation(None)
            self.food_activity_history = FoodActivityHistory()

    def note_unavailable(self, seconds: float) -> None:
        """Accept only host-measured suspension, never app closure as evidence."""
        self._unavailable_seconds = max(self._unavailable_seconds, seconds)

    def sleep_context(self) -> SleepContext:
        return replace(self.adaptive.sleep_context(observed=True),
                       blocked=(self.callbacks.defer_routine()
                                or time.monotonic() < self.callbacks.action_until()
                                or self.callbacks.speech_busy()))

    def should_interrupt_nap(self) -> bool:
        return self.sleep_context().active_seconds >= BALANCE.number(
            "sleep", "return_seconds",
        )

    def allow_nap(self) -> bool:
        context = self.sleep_context()
        return (not context.blocked and context.idle_seconds is not None
                and context.idle_seconds >= BALANCE.number("sleep", "quiet_seconds")
                and self.state.energy <= BALANCE.number("sleep", "nap_energy"))

    def allow_bedtime(self) -> bool | None:
        context = self.sleep_context()
        if context.blocked:
            return False
        return (context.idle_seconds >= BALANCE.number("sleep", "quiet_seconds")
                if context.idle_seconds is not None else None)

    def _live_reading(self) -> ComputerSnapshot | None:
        """Never project a stale hardware sample into unseen time."""
        if not self.settings.observe_computer:
            return None
        reading = self.monitor.latest()
        age = time.monotonic() - reading.measured_at
        if (
            not 0
            <= age
            <= BALANCE.integer("activity", "live_effort_maximum_age_seconds")
        ):
            return None
        return reading

    def live_effort(self) -> float | None:
        """Retain coarse observed workload for existing dialogue/routine policy."""
        reading = self._live_reading()
        return workload_intensity(reading) if reading is not None else None

    def live_consumption_load(self) -> float | None:
        """Only actual CPU/GPU utilization enters the smoothed need surcharge."""
        reading = self._live_reading()
        return consumption_load(reading) if reading is not None else None

    def session_inputs(
        self,
        wall_time: float,
        monotonic_time: float,
    ) -> SessionInputs:
        """Gather trusted activity context for care and completed games."""
        return SessionInputs(
            wall_time=wall_time,
            monotonic_time=monotonic_time,
            auto_routine=self.settings.auto_routine,
            allow_bedtime=None, allow_nap=False, interrupt_nap=False,
            effort=self.live_effort(),
            food_activity=self.observed_food_activity(),
            sleep_context=self.sleep_context(),
        )

    def observe_adaptive(self, now: float, stamp: float) -> None:
        if not self.settings.observe_computer:
            return
        sample = self.monitor.latest()
        if sample.measured_at <= self.last_adaptive_sample:
            return
        if sample.measured_at <= 0 or now - sample.measured_at > BALANCE.integer(
            "activity", "adaptive_sample_maximum_age_seconds"
        ):
            return
        self.last_adaptive_sample = sample.measured_at
        behaviour = self.adaptive.observe(
            Observation(
                wall_time=stamp,
                effort=workload_intensity(sample),
                idle_seconds=self.callbacks.read_idle_seconds(),
                uptime_hours=sample.uptime_hours,
            ),
            now,
            energy=self.state.energy,
            sleeping=self.state.sleeping,
            manual_sleep=self.state.sleep_origin == "manual",
            learn=self.settings.learn_rhythm,
        )
        self.mind.set_situation(behaviour, now=now)

    def observed_food_activity(self) -> FoodActivity:
        """Return recent measured work for a care command between ticks."""
        return self.food_activity_history.current_food_activity(time.monotonic())

    def advance_state(self, wall_time: float, *, force: bool = True) -> None:
        """Sample real input and workload before progressing pet hunger."""
        now = time.monotonic()
        self.adaptive.observe_input(
            wall=wall_time, monotonic=now,
            idle_seconds=self.callbacks.read_idle_seconds(),
            learn=self.settings.learn_rhythm,
            unavailable_seconds=self._unavailable_seconds,
        )
        self._unavailable_seconds = 0.0
        machine_load = self.live_consumption_load()
        self.food_activity_history.observe(
            now=now,
            pointer=(
                self.callbacks.read_pointer()
                if self.callbacks.read_pointer is not None
                else None
            ),
            input_idle_seconds=self.callbacks.read_idle_seconds(),
            mouse_buttons_down=(
                self.callbacks.read_mouse_buttons()
                if self.callbacks.read_mouse_buttons is not None
                else None
            ),
            measured_hardware_load=machine_load,
        )
        inputs = replace(self.session_inputs(wall_time, now), effort=machine_load)
        advance_session_time(
            self.state, self._clock, inputs, progression=self._progression,
            minimum_seconds=(0 if force else
                             BALANCE.number("simulation", "status_interval_seconds")),
        )

    def advance_lifecycle(
        self,
        now: float,
        wall_time: float,
        previous: TimeContext,
    ) -> TimeProgress:
        """Apply observed activity before time, preserving sleep transitions."""
        was_sleeping = self.state.sleeping
        previous_period = (previous.day_key, previous.period)
        self.observe_adaptive(now, wall_time)
        self.advance_state(wall_time, force=False)
        context = context_at(wall_time)
        return TimeProgress(
            context=context,
            period_changed=((context.day_key, context.period) != previous_period),
            sleep_changed=self.state.sleeping != was_sleeping,
        )

    def react_to_computer(self, now: float, context: TimeContext) -> None:
        """Queue new workload commentary without preempting care actions."""
        if not self.settings.observe_computer:
            self.pending_computer_line = None
            return
        sample = self.monitor.latest()
        if sample.measured_at > self.last_hardware_sample:
            self.last_hardware_sample = sample.measured_at
            event = self.workload_events.observe_change(sample, now)
            if event and self.settings.spontaneous_talk and not self.state.sleeping:
                self.pending_computer_line = (event, now)
                if (
                    now >= self.callbacks.action_until()
                    and not self.callbacks.speech_busy()
                ):
                    self.callbacks.start_review(now)
        if self.pending_computer_line is None:
            return
        event, observed_at = self.pending_computer_line
        if (
            now - observed_at
            > BALANCE.integer("activity", "pending_voice_maximum_age_seconds")
            or not self.settings.spontaneous_talk
            or self.state.sleeping
        ):
            self.pending_computer_line = None
        elif (
            now >= self.callbacks.action_until()
            and not self.callbacks.speech_busy()
            and now - self.callbacks.last_spoken()
            >= BALANCE.integer("activity", "voice_quiet_seconds")
        ):
            reaction = self.mind.select_computer_reaction(
                event,
                self.state,
                context,
                now,
            )
            self.pending_computer_line = None
            if reaction is not None:
                self.callbacks.react(
                    reaction, BALANCE.integer("activity", "voice_duration_ms")
                )
                self.workload_events.last_voice_at = now
