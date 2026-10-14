"""Connect pure pet walking to desktop placement through narrow ports.

This adapter owns the walking controller and converts read-only pet/session
values into movement conditions. It never selects a dialogue or Tk sprite.
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Callable, Protocol

from ...pet.animation.character import FRAME_WIDTH
from ...pet.movement import WalkConditions, WalkController
from ...pet.movement.contracts import HorizontalTrack


class BusyReading(Protocol):
    def is_busy(self) -> bool: ...


class ActivityReadings(Protocol):
    def latest(self) -> BusyReading: ...


class FocusState(Protocol):
    @property
    def focused(self) -> bool: ...

    @property
    def quiet(self) -> bool: ...


class FocusReadings(Protocol):
    @property
    def current(self) -> FocusState | None: ...


class WalkSettings(Protocol):
    x: int | None
    scale: int
    auto_walk: bool
    observe_computer: bool


class WalkNeeds(Protocol):
    energy: float
    sleeping: bool


@dataclass(frozen=True, slots=True)
class WalkDriverPorts:
    """Host capabilities granted to the pet's walking adapter."""

    track: Callable[[], HorizontalTrack]
    toolbar_visible: Callable[[], bool]
    place_x: Callable[[float], None]
    walk_finished: Callable[[float], None]


class WalkDriver:
    """Own movement execution, with no widget or window lifecycle methods."""

    def __init__(
        self, *, state: WalkNeeds, settings: WalkSettings,
        adaptive: FocusReadings, monitor: ActivityReadings,
        ports: WalkDriverPorts, walk_cycle_seconds: float,
    ) -> None:
        self.state = state
        self.settings = settings
        self.adaptive = adaptive
        self.monitor = monitor
        self.ports = ports
        self.walk_cycle_seconds = walk_cycle_seconds
        self.movement = WalkController(
            next_walk_at=time.monotonic() + random.uniform(60.0, 180.0),
        )

    def set_auto_walk(self, enabled: bool, now: float) -> None:
        self.settings.auto_walk = bool(enabled)
        self.movement.interrupt()
        self.movement.pause(now)

    def step(
        self, now: float, elapsed: float, *,
        game_mode: bool, attention_active: bool,
    ) -> str | None:
        """Plan motion and apply only actual bounded desktop displacement."""
        if game_mode:
            return None
        observed = self.adaptive.current
        busy = (
            observed.focused if observed is not None
            else self.monitor.latest().is_busy()
        )
        step = self.movement.plan_step(WalkConditions(
            now=now,
            elapsed_seconds=elapsed,
            speed_pixels_per_second=(
                68 * self.settings.scale / self.walk_cycle_seconds
            ),
            stride_pixels=68 * self.settings.scale,
            x=self.settings.x or 0,
            track=self.ports.track(),
            sprite_width=FRAME_WIDTH * self.settings.scale,
            energy=self.state.energy,
            auto_walk=self.settings.auto_walk,
            sleeping=self.state.sleeping,
            attention_active=attention_active,
            toolbar_visible=self.ports.toolbar_visible(),
            observing_computer=self.settings.observe_computer,
            computer_busy=busy,
            quiet_period=bool(observed is not None and observed.quiet),
        ))
        if step is None:
            return None
        if step.pixels == 0:
            return step.animation
        old_x = self.settings.x or 0
        self.ports.place_x(old_x + step.pixels)
        delta = (self.settings.x or 0) - old_x
        track = self.ports.track()
        blocked = (
            (step.pixels < 0 and (self.settings.x or 0) <= track.left)
            or (step.pixels > 0 and (self.settings.x or 0)
                >= track.right - FRAME_WIDTH * self.settings.scale)
        )
        if self.movement.record_displacement(delta, now=now, blocked=blocked):
            self.ports.walk_finished(now)
        return step.animation
