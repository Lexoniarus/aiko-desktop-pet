"""Immutable contracts for Tk-facing presentation and hover geometry.

These values are disconnected from mutable pet state and contain no widgets.
Application read models remain semantic; this is a presentation boundary.
"""

from __future__ import annotations

from dataclasses import dataclass

from ...application.read_snapshot import MoodletRead, WishRead
from ...application.settings import SettingKey
from ...pet.emotions import EmotionalComposition
from ...pet.needs import NeedCondition


@dataclass(frozen=True, slots=True)
class MoodletView:
    value: MoodletRead
    label: str
    description: str


@dataclass(frozen=True, slots=True)
class WishView:
    value: WishRead
    label: str
    description: str
    target_label: str
    restriction_label: str


@dataclass(frozen=True, slots=True)
class EmotionalSnapshot:
    composition: EmotionalComposition
    state_label: str
    need_conditions: frozenset[NeedCondition] = frozenset()
    moodlets: tuple[MoodletView, ...] = ()
    wishes: tuple[WishView, ...] = ()


@dataclass(frozen=True, slots=True)
class HoverSnapshot:
    header: str
    sleep_label: str
    feed_label: str
    status_values: tuple[tuple[str, float], ...]
    friendship_level: int
    hardware_line: str
    workload_line: str
    emotional: EmotionalSnapshot
    food_line: str = ""
    wellbeing_line: str = ""

    def status_value(self, key: str) -> float:
        for name, value in self.status_values:
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
    sleep_label: str
    hardware_line: str
    activity_line: str
    status_values: tuple[tuple[str, float], ...]
    friendship_level: int
    emotional: EmotionalSnapshot
    objects_line: str = ""
    wellbeing_line: str = ""
    relationship_line: str = ""
    sleep_context_line: str = ""
    contact_line: str = ""

    @property
    def emotional_state_label(self) -> str:
        return self.emotional.state_label

    def status_value(self, key: str) -> float:
        for name, value in self.status_values:
            if key == name:
                return value
        raise KeyError(key)


@dataclass(frozen=True, slots=True)
class SettingsSnapshot:
    scale: int
    options: tuple[tuple[SettingKey, bool], ...]

    def value(self, key: str) -> bool:
        for name, value in self.options:
            if name == key:
                return value
        raise KeyError(key)
