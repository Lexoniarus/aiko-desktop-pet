"""Periodic desktop window maintenance with no domain or Tk dependencies."""

from __future__ import annotations

from typing import Callable

TRACK_REFRESH_SECONDS = 4.0
STACK_REFRESH_SECONDS = 1.5


class DesktopMaintenance:
    """Own frequency limits for taskbar discovery and native window layering."""

    def __init__(
        self,
        *,
        check_taskbar: Callable[[], bool],
        reposition: Callable[[], None],
        maintain_stack: Callable[[], object],
        started_at: float,
    ) -> None:
        self._check_taskbar = check_taskbar
        self._reposition = reposition
        self._maintain_stack = maintain_stack
        self.last_track_check = started_at
        self.last_stack_check = started_at

    def refresh_track(self, now: float) -> None:
        """Move the sprite only when actual primary taskbar bounds change."""
        if now - self.last_track_check < TRACK_REFRESH_SECONDS:
            return
        self.last_track_check = now
        if self._check_taskbar():
            self._reposition()

    def refresh_stack(self, now: float) -> None:
        """Avoid repeatedly raising all windows when layering is intact."""
        if now - self.last_stack_check < STACK_REFRESH_SECONDS:
            return
        self.last_stack_check = now
        self._maintain_stack()
