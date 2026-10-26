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
from .walk_runtime import WalkDriver


@dataclass(frozen=True, slots=True)
class PointerRuntimePorts:
    """Native pointer input and host geometry without importing Tk."""

    sample: Callable[[], tuple[int, int, int]]
    game_mode: Callable[[], bool]
    eyes: Callable[[], tuple[float, float]]
    on_motion: Callable[[float, int, float], None]
    scale: Callable[[], int] = lambda: 1
    activity: Callable[[], CursorActivityContext] = CursorActivityContext


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

    def begin_behaviour(self, now: float) -> None:
        if self._behaviour is not None:
            self._behaviour.begin_frame(now, self._ports.activity())

    def admit_behaviour(self, now: float) -> None:
        if self._behaviour is not None and self._walk is not None:
            self._walk.apply_cursor_intent(
                self._behaviour.admit_motion(self._ports.activity(), now),
                now,
            )

    def motion_allowed(self) -> bool:
        return (
            self._behaviour is not None
            and self._behaviour.admit_motion(
                self._ports.activity(),
                time.monotonic(),
            )
            is not None
        )

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
