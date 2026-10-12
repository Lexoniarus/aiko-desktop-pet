"""Read-only status panel data and its explicitly permitted actions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True, slots=True)
class StatusSnapshot:
    today: str
    next_event: str
    hint: str
    emotion: str
    sleep_label: str
    hardware_line: str
    activity_line: str
    needs: tuple[tuple[str, float], ...]
    friendship_level: int

    def need_value(self, key: str) -> float:
        for name, value in self.needs:
            if key == name:
                return value
        raise KeyError(key)


@dataclass(frozen=True, slots=True)
class StatusActions:
    interact: Callable[[str], None]
    quit: Callable[[], None]
    closed: Callable[[], None]
