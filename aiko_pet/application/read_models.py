"""Read-only models for the three desktop utility windows.

This adapter owns no Tk widgets, network listeners or persistence operations.
It reads current local domain objects only when a window requests a snapshot.
"""

from __future__ import annotations

import time
from typing import Callable, Protocol

from ..adaptive import AdaptiveRoutine
from ..dialogue import AikoMind
from ..domain import PetState
from ..routine import TimeContext
from ..storage import PetSettings
from ..system_activity import ComputerSnapshot
from .view_models import (
    HoverAnchor, HoverSnapshot, SettingsSnapshot, StatusSnapshot,
)
from .hover_projection import project_hover
from .settings_projection import project_settings
from .status_projection import project_status


class CachedComputerReadings(Protocol):
    def latest(self) -> ComputerSnapshot: ...


class DesktopViewSource:
    """Snapshot the live pet before data crosses into Tk utility windows."""

    def __init__(
        self, state: PetState, settings: PetSettings, mind: AikoMind,
        adaptive: AdaptiveRoutine, monitor: CachedComputerReadings,
        *, context: Callable[[], TimeContext],
        sprite_size: Callable[[], tuple[int, int]],
    ) -> None:
        self.state = state
        self.settings = settings
        self.mind = mind
        self.adaptive = adaptive
        self.monitor = monitor
        self._context = context
        self._sprite_size = sprite_size

    def hover(self) -> HoverSnapshot:
        return project_hover(
            self.state, self._context(), self.monitor.latest(),
            observe_computer=self.settings.observe_computer,
        )

    def status(self) -> StatusSnapshot:
        from ..system_activity import ComputerSnapshot

        reading = (
            self.monitor.latest()
            if self.settings.observe_computer else ComputerSnapshot()
        )
        return project_status(
            self.state, self._context(), self.mind,
            self.adaptive.current, reading,
            observe_computer=self.settings.observe_computer,
            now=time.monotonic(),
        )

    def settings_view(self) -> SettingsSnapshot:
        return project_settings(self.settings)

    def anchor(self) -> HoverAnchor:
        width, height = self._sprite_size()
        return HoverAnchor(
            x=self.settings.x or 0, y=self.settings.y or 0,
            width=width, height=height,
            pinned_x=self.settings.toolbar_x,
            pinned_y=self.settings.toolbar_y,
        )
