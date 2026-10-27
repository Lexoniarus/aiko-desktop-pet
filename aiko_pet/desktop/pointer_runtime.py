"""Connect OS pointer samples to pet observation and current event handlers."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable

from ..application.cursor_behaviour import (
    CursorActivityContext,
    CursorBehaviourCoordinator,
)
from ..application.cursor_observation import CursorObservation
from ..pet.interaction_events import CursorExperience
from .geometry import sprite_access_contains
from .walk_runtime import WalkDriver


@dataclass(frozen=True, slots=True)
class PointerRuntimePorts:
    """Native pointer input and host geometry without importing Tk."""

    sample: Callable[[], tuple[int, int, int]]
    game_mode: Callable[[], bool]
    eyes: Callable[[], tuple[float, float]]
    on_motion: Callable[[float, int, float], None]
    on_experience: Callable[[CursorExperience], None] = lambda _event: None
    scale: Callable[[], int] = lambda: 1
    menu_engaged: Callable[[], bool] = lambda: False
    foreground_active: Callable[[], bool] = lambda: False
    world_protected: Callable[[], bool] = lambda: False
    sprite_origin: Callable[[], tuple[int, int] | None] = lambda: None
    pointer_inside: Callable[[int, int], bool] = lambda _x, _y: False


class PointerRuntime:
    """Sample once, update the pet's history and forward changed motion."""

    def __init__(
        self,
        observer: CursorObservation,
        ports: PointerRuntimePorts,
        behaviour: CursorBehaviourCoordinator | None = None,
        walk: WalkDriver | None = None,
    ) -> None:
        self._observer = observer
        self._ports = ports
        self._behaviour, self._walk = behaviour, walk
        self._access_claimed = False

    def access_contains(self, x: int, y: int) -> bool:
        origin = self._ports.sprite_origin()
        return (origin is not None and sprite_access_contains(
            (x, y), origin, self._ports.scale(),
        ))

    def claim_access(self, point: tuple[int, int] | None = None) -> None:
        """An admitted native entry/click takes control immediately between ticks."""
        self._access_claimed = True
        now = time.monotonic()
        if self._behaviour is not None:
            self._behaviour.claim_access(now)
        if self._walk is not None:
            self._walk.clear_cursor_request(now)

    def control_active(self) -> bool:
        """Pure current admission read; no policy evaluation or contact side effects."""
        if self._ports.menu_engaged():
            return True
        x, y, _width = self._ports.sample()
        inside = self.access_contains(x, y) or self._ports.pointer_inside(x, y)
        return inside and (self._access_claimed or self.allow_hover())

    def begin_behaviour(self, now: float) -> None:
        x, y, _width = self._ports.sample()
        inside = self.access_contains(x, y) or self._ports.pointer_inside(x, y)
        if not inside and not self._ports.menu_engaged():
            self._access_claimed = False
        elif self.control_active() and not self._access_claimed:
            self.claim_access((x, y))
        if self._behaviour is not None:
            self._behaviour.begin_frame(now, self.activity())
            if self._behaviour.feedback is not None:
                self._ports.on_experience(self._behaviour.feedback)

    def admit_behaviour(self, now: float) -> None:
        if self._behaviour is not None and self._walk is not None:
            self._walk.apply_cursor_intent(
                self._behaviour.admit_motion(self.activity(), now),
                now,
            )

    def motion_allowed(self) -> bool:
        return (
            self._behaviour is not None
            and self._behaviour.admit_motion(
                self.activity(),
                time.monotonic(),
            )
            is not None
        )

    def activity(self) -> CursorActivityContext:
        return CursorActivityContext(
            game_open=self._ports.game_mode(),
            menu_engaged=self._ports.menu_engaged(),
            foreground_active=self._ports.foreground_active(),
            world_protected=self._ports.world_protected(),
            direct_contact=self.control_active(),
        )

    def allow_hover(self) -> bool:
        x, y, _width = self._ports.sample()
        return self._observer.classify_contact(
            (x, y),
            pet_moved_at=self._walk.last_placement_at
            if self._walk is not None
            else -1000,
        )

    def reset(self) -> None:
        self._access_claimed = False
        self._observer.attention.reset()
        if self._behaviour is not None:
            self._behaviour.reset()
        if self._walk is not None:
            self._walk.clear_cursor_request()

    def snapshot_pointer(self) -> tuple[int, int]:
        current = self._observer.current
        if 0 <= time.monotonic() - current.sampled_at <= 0.3:
            return current.pointer
        x, y, _width = self._ports.sample()
        return x, y

    def observe(self, now: float) -> tuple[int, int]:
        x, y, screen_width = self._ports.sample()
        pointer = x, y
        result = self._observer.observe(
            pointer,
            now,
            game_mode=self._ports.game_mode(),
            eyes=self._ports.eyes(),
            screen_width=screen_width,
            scale=self._ports.scale(),
        )
        motion = result.motion
        if motion is not None:
            self._ports.on_motion(motion.distance, motion.screen_width, motion.now)
        return pointer
