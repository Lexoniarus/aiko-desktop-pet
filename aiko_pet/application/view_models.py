"""Immutable application read contracts independent of desktop presentation.

An external status-query adapter can later map a deliberate subset of these
models without depending on Tkinter widgets or exposing mutable PetState.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class HoverSnapshot:
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
    x: int
    y: int
    width: int
    height: int
    pinned_x: int | None
    pinned_y: int | None


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
class SettingsSnapshot:
    scale: int
    options: tuple[tuple[str, bool], ...]

    def value(self, key: str) -> bool:
        for name, value in self.options:
            if name == key:
                return value
        raise KeyError(key)
