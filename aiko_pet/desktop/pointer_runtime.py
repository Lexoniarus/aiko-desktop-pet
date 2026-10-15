"""Connect OS pointer samples to pet observation and current event handlers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from ..application.cursor_observation import CursorObservation


@dataclass(frozen=True, slots=True)
class PointerRuntimePorts:
    """Native pointer input and host geometry without importing Tk."""

    sample: Callable[[], tuple[int, int, int]]
    game_mode: Callable[[], bool]
    eyes: Callable[[], tuple[float, float]]
    on_motion: Callable[[float, int, float], None]


class PointerRuntime:
    """Sample once, update the pet's history and forward changed motion."""

    def __init__(
        self, observer: CursorObservation, ports: PointerRuntimePorts,
    ) -> None:
        self._observer = observer
        self._ports = ports

    def observe(self, now: float) -> tuple[int, int]:
        x, y, screen_width = self._ports.sample()
        pointer = x, y
        motion = self._observer.observe(
            pointer, now, game_mode=self._ports.game_mode(),
            eyes=self._ports.eyes(), screen_width=screen_width,
        )
        if motion is not None:
            self._ports.on_motion(motion.distance, motion.screen_width, motion.now)
        return pointer
