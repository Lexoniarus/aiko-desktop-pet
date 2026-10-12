"""Options and actions allowed to the standalone settings popover."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True, slots=True)
class SettingsSnapshot:
    scale: int
    options: tuple[tuple[str, bool], ...]

    def value(self, key: str) -> bool:
        for name, value in self.options:
            if name == key:
                return value
        raise KeyError(key)


@dataclass(frozen=True, slots=True)
class SettingsActions:
    open_status: Callable[[], None]
    toggle_scale: Callable[[], None]
    set_option: Callable[[str, bool], None]
    forget_rhythm: Callable[[], None]
    reset_toolbar: Callable[[], None]
    center: Callable[[], None]
    quit: Callable[[], None]
    closed: Callable[[], None]
