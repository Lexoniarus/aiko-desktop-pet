"""Local workload and daily-rhythm coordination without Tk or view imports."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable

from ..personality.adaptive import AdaptiveRoutine, Observation
from ..personality.mind import AikoMind
from ..personality.workload_events import WorkloadEventDetector
from ..personality.catalog import Reaction
from ..pet.state import PetState
from ..pet.routine import TimeContext, context_at
from .settings import PetSettings
from ..telemetry import workload_intensity
from .ports import ComputerObservation


@dataclass(frozen=True, slots=True)
class ActivityCallbacks:
    """No access to GUI internals: only specific side effects are injected."""

    read_idle_seconds: Callable[[], float | None]
    start_review: Callable[[float], None]
    react: Callable[[Reaction, int], None]
    action_until: Callable[[], float]
    last_spoken: Callable[[], float]


@dataclass(frozen=True, slots=True)
class TimeProgress:
    context: TimeContext
    period_changed: bool
    sleep_changed: bool


class ActivityCoordinator:
    """Own coarse sampling, sleep permissions and deferred work dialogue."""

    def __init__(
        self, state: PetState, settings: PetSettings,
        mind: AikoMind, adaptive: AdaptiveRoutine,
        voice: WorkloadEventDetector, monitor: ComputerObservation,
        callbacks: ActivityCallbacks,
    ) -> None:
        self.state = state
        self.settings = settings
        self.mind = mind
        self.adaptive = adaptive
        self.workload_events = voice
        self.monitor = monitor
        self.callbacks = callbacks
        self.last_hardware_sample = 0.0
        self.last_adaptive_sample = 0.0
        self.pending_computer_line: tuple[str, float] | None = None

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

    def interrupt_nap(self) -> bool:
        behaviour = self.adaptive.current
        return bool(
            self.settings.observe_computer and behaviour is not None
            and behaviour.should_wake
        )

    def allow_nap(self) -> bool:
        behaviour = self.adaptive.current
        return bool(
            self.settings.observe_computer and behaviour is not None
            and behaviour.can_nap
        )

    def allow_bedtime(self) -> bool | None:
        behaviour = self.adaptive.current
        if not self.settings.observe_computer or behaviour is None:
            return None
        return behaviour.can_sleep

    def live_effort(self) -> float | None:
        """Never project a stale hardware sample into unseen time."""
        if not self.settings.observe_computer:
            return None
        reading = self.monitor.latest()
        age = time.monotonic() - reading.measured_at
        if not 0 <= age <= 18:
            return None
        return workload_intensity(reading)

    def observe_adaptive(self, now: float, stamp: float) -> None:
        if not self.settings.observe_computer:
            return
        sample = self.monitor.latest()
        if sample.measured_at <= self.last_adaptive_sample:
            return
        if sample.measured_at <= 0 or now - sample.measured_at > 25:
            return
        self.last_adaptive_sample = sample.measured_at
        behaviour = self.adaptive.observe(
            Observation(
                wall_time=stamp,
                effort=workload_intensity(sample),
                idle_seconds=self.callbacks.read_idle_seconds(),
                uptime_hours=sample.uptime_hours,
            ),
            now, energy=self.state.energy, sleeping=self.state.sleeping,
            manual_sleep=self.state.sleep_origin == "manual",
            learn=self.settings.learn_rhythm,
        )
        self.mind.set_situation(behaviour, now=now)

    def advance_state(self, wall_time: float) -> None:
        """Apply time and current workload without recording new observations."""
        self.state.advance(
            wall_time, auto_routine=self.settings.auto_routine,
            allow_bedtime=self.allow_bedtime(),
            allow_nap=self.allow_nap(),
            interrupt_nap=self.interrupt_nap(),
            effort=self.live_effort(),
        )

    def advance_lifecycle(
        self, now: float, wall_time: float, previous: TimeContext,
    ) -> TimeProgress:
        """Apply observed activity before time, preserving sleep transitions."""
        was_sleeping = self.state.sleeping
        previous_period = (previous.day_key, previous.period)
        self.observe_adaptive(now, wall_time)
        self.advance_state(wall_time)
        context = context_at(wall_time)
        return TimeProgress(
            context=context,
            period_changed=(
                (context.day_key, context.period) != previous_period
            ),
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
            if (
                event and self.settings.spontaneous_talk
                and not self.state.sleeping
            ):
                self.pending_computer_line = (event, now)
                if now >= self.callbacks.action_until():
                    self.callbacks.start_review(now)
        if self.pending_computer_line is None:
            return
        event, observed_at = self.pending_computer_line
        if (
            now - observed_at > 25
            or not self.settings.spontaneous_talk
            or self.state.sleeping
        ):
            self.pending_computer_line = None
        elif (
            now >= self.callbacks.action_until()
            and now - self.callbacks.last_spoken() >= 7
        ):
            reaction = self.mind.computer_event(
                event, self.state, context, now,
            )
            self.pending_computer_line = None
            if reaction is not None:
                self.callbacks.react(reaction, 3400)
                self.workload_events.last_voice_at = now
