"""Connect pure pet walking to desktop placement through narrow ports.

This adapter owns the walking controller and converts read-only pet/session
values into movement conditions. It never selects a dialogue or Tk sprite.
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Callable, Protocol

from ..pet.animation.character import FRAME_WIDTH
from ..pet.balance import BALANCE
from ..pet.mind.cursor_behaviour import CursorIntent
from ..pet.movement import WalkConditions, WalkController
from ..pet.movement.contracts import (
    HorizontalTrack,
    MotionCompletion,
    MotionRequest,
    MotionStopReason,
    WalkStep,
)


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
    """Mutable settings capabilities used to plan host movement."""

    @property
    def x(self) -> int | None: ...

    @x.setter
    def x(self, value: int | None) -> None: ...

    @property
    def scale(self) -> int: ...

    @scale.setter
    def scale(self, value: int) -> None: ...

    @property
    def auto_walk(self) -> bool: ...

    @auto_walk.setter
    def auto_walk(self, value: bool) -> None: ...

    @property
    def observe_computer(self) -> bool: ...

    @observe_computer.setter
    def observe_computer(self, value: bool) -> None: ...


class WalkNeeds(Protocol):
    @property
    def energy(self) -> float: ...

    @property
    def sleeping(self) -> bool: ...


@dataclass(frozen=True, slots=True)
class WalkDriverPorts:
    """Host capabilities granted to the pet's walking adapter."""

    track: Callable[[], HorizontalTrack]
    menu_engaged: Callable[[], bool]
    place_x: Callable[[float], None]
    committed_goal: Callable[[], bool] = lambda: False
    cursor_allowed: Callable[[], bool] = lambda: False
    cursor_finished: Callable[[MotionCompletion], None] = lambda _result: None
    idle_steps: Callable[[], bool] = lambda: False
    hard_access: Callable[[], bool] = lambda: False


class WalkDriver:
    """Own movement execution, with no widget or window lifecycle methods."""

    def __init__(
        self,
        *,
        state: WalkNeeds,
        settings: WalkSettings,
        adaptive: FocusReadings,
        monitor: ActivityReadings,
        ports: WalkDriverPorts,
        walk_cycle_seconds: float,
    ) -> None:
        self.state = state
        self.settings = settings
        self.adaptive = adaptive
        self.monitor = monitor
        self.ports = ports
        self.walk_cycle_seconds = walk_cycle_seconds
        self.last_placement_at = -1000.0
        self.movement = WalkController(
            next_walk_at=time.monotonic()
            + random.uniform(
                BALANCE.number("cursor_behaviour", "idle_step_minimum_seconds"),
                BALANCE.number("cursor_behaviour", "idle_step_maximum_seconds"),
            ),
        )

    def set_auto_walk(self, enabled: bool, now: float) -> None:
        self.settings.auto_walk = bool(enabled)
        self.movement.interrupt()
        self.movement.pause(now)

    def set_world_goal(self, x: float | None) -> None:
        self.movement.set_goal(x)

    def clear_cursor_request(
        self,
        now: float | None = None,
        *,
        reason: MotionStopReason = "cancelled",
    ) -> None:
        old = self.movement.request("cursor")
        self.movement.release_request("cursor")
        if old is not None:
            self.ports.cursor_finished(
                MotionCompletion(
                    "cursor",
                    old.token,
                    time.monotonic() if now is None else now,
                    reason,
                )
            )

    def apply_cursor_intent(self, intent: CursorIntent | None, now: float) -> None:
        if intent is None:
            self.clear_cursor_request(now)
            return
        old = self.movement.request("cursor")
        if old is not None and old.token == intent.token:
            return
        steps = intent.steps if intent.reaction == "approach" else 1
        amount = steps * BALANCE.number(
            "cursor_behaviour",
            "flight_width_multiplier"
            if intent.reaction == "flee"
            else "step_width_fraction",
        )
        width = FRAME_WIDTH * self.settings.scale
        x = self.settings.x or 0
        track = self.ports.track()
        target = max(
            track.left,
            min(
                round(x + intent.side * width * amount),
                max(track.left, track.right - width),
            ),
        )
        if target == x:
            self.ports.cursor_finished(
                MotionCompletion(
                    "cursor",
                    intent.token,
                    now,
                    "blocked",
                )
            )
            return
        self.submit_cursor_intent(
            MotionRequest(
                "cursor",
                intent.token,
                target,
                "run" if intent.reaction == "flee" else "step",
                intent.until,
                movement_seconds=BALANCE.number("cursor_behaviour", "flight_seconds")
                if intent.reaction == "flee"
                else float("inf"),
                step_pixels=width
                * BALANCE.number("cursor_behaviour", "step_width_fraction")
                if intent.reaction != "flee"
                else 0,
            )
        )

    def submit_cursor_intent(self, request: MotionRequest) -> None:
        self.movement.replace_request("cursor", request)

    def step(
        self,
        now: float,
        elapsed: float,
        *,
        game_mode: bool,
        attention_active: bool,
    ) -> WalkStep | None:
        """Plan motion and apply only actual bounded desktop displacement."""
        if game_mode:
            return None
        if self.ports.hard_access() or self.ports.menu_engaged():
            self.clear_cursor_request(now)
            self.movement.random_walk.pause(now, quiet_period=False)
            if self.movement.goal_x is None and self.movement.source == "idle":
                self.movement.interrupt()
            return None
        if not self.ports.cursor_allowed():
            self.clear_cursor_request(now)
        observed = self.adaptive.current
        committed = self.movement.goal_x is not None and self.ports.committed_goal()
        busy = (
            observed.focused
            if observed is not None
            else self.monitor.latest().is_busy()
        )
        step = self.movement.plan_step(
            WalkConditions(
                now=now,
                elapsed_seconds=elapsed,
                speed_pixels_per_second=(
                    (
                        16 / 0.62
                        if self.movement.kind == "step"
                        else BALANCE.integer("walk", "stride_pixels_at_scale_one")
                        / self.walk_cycle_seconds
                    )
                    * self.settings.scale
                ),
                stride_pixels=BALANCE.integer("walk", "stride_pixels_at_scale_one")
                * self.settings.scale,
                x=self.settings.x or 0,
                track=self.ports.track(),
                sprite_width=FRAME_WIDTH * self.settings.scale,
                energy=self.state.energy,
                auto_walk=self.settings.auto_walk,
                sleeping=self.state.sleeping,
                attention_active=attention_active and not committed,
                menu_engaged=self.ports.menu_engaged() and not committed,
                observing_computer=self.settings.observe_computer,
                computer_busy=busy,
                quiet_period=bool(observed is not None and observed.quiet),
                small_idle_steps=self.ports.idle_steps(),
            )
        )
        if step is None:
            return None
        if step.pixels == 0:
            return step
        source = self.movement.source
        old_x = self.settings.x or 0
        self.ports.place_x(old_x + step.pixels)
        delta = (self.settings.x or 0) - old_x
        if delta:
            self.last_placement_at = now
        track = self.ports.track()
        blocked = (step.pixels < 0 and (self.settings.x or 0) <= track.left) or (
            step.pixels > 0
            and (self.settings.x or 0)
            >= track.right - FRAME_WIDTH * self.settings.scale
        )
        if self.movement.record_displacement(delta, now=now, blocked=blocked):
            if source == "cursor":
                self.clear_cursor_request(now, reason=self.movement.completion_reason)
            # Autonomous and cursor steps deliberately carry no spoken completion.
        return step
