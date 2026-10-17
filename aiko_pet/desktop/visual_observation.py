"""Observe native gaze geometry and cached workload for pet animation.

The Tk sprite never samples hardware or maintains cursor direction history.
Desktop observations become immutable inputs for pure animation policies.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from ..pet.animation.animation import PassiveObservation
from ..pet.animation.gaze import gaze_sector


class VisualSettings(Protocol):
    @property
    def scale(self) -> int: ...

    @property
    def follow_cursor(self) -> bool: ...

    @property
    def observe_computer(self) -> bool: ...


class BusyReading(Protocol):
    def is_busy(self) -> bool: ...


class WorkloadReadings(Protocol):
    def latest(self) -> BusyReading: ...


class DesktopVisualObservation:
    """Resolve one gaze sector and defer CPU observations during cursor gaze."""

    def __init__(
        self, *, settings: VisualSettings, monitor: WorkloadReadings,
        eyes: Callable[[], tuple[float, float]],
    ) -> None:
        self._settings = settings
        self._monitor = monitor
        self._eyes = eyes
        self._sector: int | None = None
        self.object_target: tuple[float, float] | None = None

    @property
    def sector(self) -> int | None:
        return self._sector

    def reset(self) -> None:
        """Clear gaze hysteresis on game, scale or cursor-setting changes."""
        self._sector = None

    def gaze_direction(
        self, pointer: tuple[int, int], *, game_mode: bool = False,
    ) -> int | None:
        """Resolve cursor gaze without entering Tk or reading the monitor."""
        if game_mode or (
            not self._settings.follow_cursor and self.object_target is None
        ):
            self.reset()
            return None
        eyes_x, eyes_y = self._eyes()
        target = self.object_target or pointer
        self._sector = gaze_sector(
            eyes_x, eyes_y, *target,
            scale=self._settings.scale, previous=self._sector,
        )
        return self._sector

    def observe(
        self, now: float, pointer: tuple[int, int],
        last_pointer_move: float, game_mode: bool,
    ) -> PassiveObservation:
        """Return passive inputs; preserve gaze precedence over hardware."""
        if self.object_target is not None or now - last_pointer_move < 4.0:
            direction = self.gaze_direction(pointer, game_mode=game_mode)
        else:
            self.reset()
            direction = None
        busy = (
            self._monitor.latest().is_busy()
            if not game_mode and direction is None
            and self._settings.observe_computer else False
        )
        return PassiveObservation(direction, busy)
