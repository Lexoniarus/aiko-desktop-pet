"""Tk-independent adapter from application snapshots to desktop views.

Keeps mutable PetState and monitoring objects outside all Tk widgets. The
actual language and geometry belong to the presentation boundary.
"""

from __future__ import annotations

import time
from typing import Callable

from ...pet.mind.adaptive import AdaptiveRoutine
from ...application.ports import ComputerReadings
from ...application.read_snapshot import snapshot_pet
from ...application.settings import PetSettings
from ...pet.mind import PetMind
from ...pet.state import PetState
from ...pet.routine import TimeContext
from ...telemetry import ComputerSnapshot
from .contracts import (
    HoverAnchor, HoverSnapshot, SettingsSnapshot, StatusSnapshot,
)
from .projections import project_hover, project_settings, project_status


class DesktopPresentation:
    """Map domain snapshots to the three desktop windows on the owner thread."""

    def __init__(
        self, state: PetState, settings: PetSettings, mind: PetMind,
        adaptive: AdaptiveRoutine, monitor: ComputerReadings,
        *, context: Callable[[], TimeContext],
        sprite_size: Callable[[], tuple[int, int]],
    ) -> None:
        self._state = state
        self._settings = settings
        self._mind = mind
        self._adaptive = adaptive
        self._monitor = monitor
        self._context = context
        self._sprite_size = sprite_size

    def hover(self) -> HoverSnapshot:
        return project_hover(
            snapshot_pet(self._state),
            self._context(), self._monitor.latest(),
            observe_computer=self._settings.observe_computer,
        )

    def status(self) -> StatusSnapshot:
        computer = (
            self._monitor.latest()
            if self._settings.observe_computer else ComputerSnapshot()
        )
        now = time.monotonic()
        return project_status(
            snapshot_pet(self._state), self._context(),
            self._mind.emotion(self._state, now),
            self._adaptive.current, computer,
            observe_computer=self._settings.observe_computer,
        )

    def settings_view(self) -> SettingsSnapshot:
        return project_settings(self._settings)

    def anchor(self) -> HoverAnchor:
        width, height = self._sprite_size()
        return HoverAnchor(
            x=self._settings.x or 0, y=self._settings.y or 0,
            width=width, height=height,
            pinned_x=self._settings.toolbar_x,
            pinned_y=self._settings.toolbar_y,
        )
