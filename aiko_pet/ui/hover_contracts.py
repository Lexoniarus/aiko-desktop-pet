"""Read-only data and callbacks for an independent hover panel."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True, slots=True)
class HoverSnapshot:
    """The values a hover panel may see, without direct access to PetState."""

    header: str
    sleep_label: str
    feed_label: str
    needs: tuple[tuple[str, float], ...]
    friendship_level: int
    hardware_line: str
    workload_line: str

    def need_value(self, key: str) -> float:
        for name, value in self.needs:
            if name == key:
                return value
        raise KeyError(key)


@dataclass(frozen=True, slots=True)
class HoverAnchor:
    """Sprite geometry and optional saved hover-window position."""

    x: int
    y: int
    width: int
    height: int
    pinned_x: int | None
    pinned_y: int | None


@dataclass(frozen=True, slots=True)
class HoverActions:
    """Precisely the actions that the application grants to its hover view."""

    interact: Callable[[str], None]
    open_status: Callable[[], None]
    open_settings: Callable[[int, int], None]
    save_position: Callable[[int | None, int | None], None]
    move_speech: Callable[[], None]
    restore_stack: Callable[[], bool]
