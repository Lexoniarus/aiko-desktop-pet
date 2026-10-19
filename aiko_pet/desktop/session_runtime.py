"""Own desktop-session lifecycle coordination and refresh/save ordering.

The shell supplies a few UI effect ports. Application time progression,
presentation refreshes and persistence run through their existing owners.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable

from ..application.activity import ActivityCoordinator
from ..infrastructure.active_time import active_uptime_seconds, elapsed_uptime_seconds
from ..pet.routine import TimeContext
from .attention_runtime import DesktopAttentionRuntime
from .maintenance import DesktopMaintenance
from .persistence import DesktopPersistence


@dataclass(frozen=True, slots=True)
class SessionRuntimePorts:
    """Host effects deliberately kept outside application/domain services."""

    context: Callable[[], TimeContext]
    set_context: Callable[[TimeContext], None]
    toolbar_visible: Callable[[], bool]
    refresh_toolbar: Callable[[], None]
    refresh_status: Callable[[], None]
    refresh_settings: Callable[[], None]
    save: Callable[[], None]


class DesktopSessionRuntime:
    """Coordinate tick-level lifecycle, overlays and durable state writes."""

    def __init__(
        self, *, activity: ActivityCoordinator,
        attention: DesktopAttentionRuntime, maintenance: DesktopMaintenance,
        persistence: DesktopPersistence, ports: SessionRuntimePorts,
    ) -> None:
        self._activity = activity
        self._attention = attention
        self._maintenance = maintenance
        self._persistence = persistence
        self._ports = ports
        self._uptime_pair = (elapsed_uptime_seconds(), active_uptime_seconds())

    def advance_lifecycle(self, now: float, wall_time: float) -> None:
        """Advance pet time before presentation, with the same prior context."""
        previous_elapsed, previous_active = self._uptime_pair
        elapsed, active = elapsed_uptime_seconds(), active_uptime_seconds()
        self._uptime_pair = elapsed, active
        if all(value is not None for value in (
            previous_elapsed, previous_active, elapsed, active,
        )):
            assert previous_elapsed is not None and previous_active is not None
            assert elapsed is not None and active is not None
            if elapsed >= previous_elapsed and active >= previous_active:
                unavailable = elapsed - previous_elapsed - (active - previous_active)
                if unavailable >= 5:
                    self._activity.note_unavailable(unavailable)
        progress = self._activity.advance_lifecycle(
            now, wall_time, self._ports.context(),
        )
        self._ports.set_context(progress.context)
        self._attention.handle_time_progress(progress, now)

    def refresh(self, now: float) -> None:
        """Refresh mapped windows and maintain autosave cadence."""
        if self._ports.toolbar_visible():
            self._ports.refresh_toolbar()
        self._ports.refresh_status()
        self._ports.refresh_settings()
        self._maintenance.refresh_stack(now)
        if self._persistence.due(now):
            self._ports.save()

    def advance_and_save(self) -> OSError | None:
        """Advance measured state exactly once before the persistence write."""
        self._activity.advance_state(time.time())
        return self._persistence.save()
