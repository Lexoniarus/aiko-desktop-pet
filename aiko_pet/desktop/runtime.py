"""Bounded, deterministic desktop update scheduler.

Owns Tk timer IDs and update ordering. Each stage is supplied by a narrow
protocol; no pet state, sprite or browser transport is imported.
"""

from __future__ import annotations

import time
from typing import Callable, Protocol

TICK_MILLISECONDS = 140


class TickStages(Protocol):
    _closed: bool

    def _greet_on_start(self) -> None: ...

    def _advance_pet_lifecycle(
        self, now: float, wall_time: float,
    ) -> None: ...

    def _refresh_taskbar_track(self, now: float) -> None: ...

    def _poll_desktop_click(self) -> None: ...

    def _refresh_hover(self, now: float) -> None: ...

    def _react_to_computer(self, now: float) -> None: ...

    def _observe_pointer(self, now: float) -> tuple[int, int]: ...

    def _render_current_sprite(
        self, now: float, elapsed: float, pointer: tuple[int, int],
    ) -> None: ...

    def _maybe_show_idle_emote(self, now: float) -> None: ...

    def _maybe_speak_spontaneously(self, now: float) -> None: ...

    def _present_pending_notification(self, now: float) -> None: ...

    def _refresh_overlays_and_autosave(self, now: float) -> None: ...


class DesktopRuntime:
    """Advance each phase once; never own or modify domain/application state."""

    def __init__(
        self,
        stages: TickStages,
        *,
        schedule: Callable[[int, Callable[[], None]], str],
        cancel: Callable[[str], None],
        monotonic: Callable[[], float] = time.monotonic,
        wall_time: Callable[[], float] = time.time,
    ) -> None:
        self._stages = stages
        self._schedule = schedule
        self._cancel = cancel
        self._monotonic = monotonic
        self._wall_time = wall_time
        self.last_tick = monotonic()
        self.scheduled_tick: str | None = None
        self.scheduled_greeting: str | None = None

    def start(self) -> None:
        """Start desktop timers after all components have been assembled."""
        if self._stages._closed:
            return
        if self.scheduled_tick is not None:
            return
        self.scheduled_greeting = self._schedule(
            460, self._stages._greet_on_start,
        )
        self.scheduled_tick = self._schedule(
            TICK_MILLISECONDS, self._stages._tick,
        )

    def tick(self) -> None:
        """Preserve original phase ordering and manual-test timer cancellation."""
        if self._stages._closed:
            return
        if self.scheduled_tick is not None:
            self._cancel(self.scheduled_tick)
            self.scheduled_tick = None
        now = self._monotonic()
        elapsed = max(0.0, min(0.5, now - self.last_tick))
        self.last_tick = now
        timestamp = self._wall_time()
        stages = self._stages
        stages._advance_pet_lifecycle(now, timestamp)
        stages._refresh_taskbar_track(now)
        stages._poll_desktop_click()
        stages._refresh_hover(now)
        stages._react_to_computer(now)
        pointer = stages._observe_pointer(now)
        stages._render_current_sprite(now, elapsed, pointer)
        stages._maybe_show_idle_emote(now)
        stages._maybe_speak_spontaneously(now)
        stages._present_pending_notification(now)
        stages._refresh_overlays_and_autosave(now)
        if not stages._closed:
            self.scheduled_tick = self._schedule(
                TICK_MILLISECONDS, stages._tick,
            )

    def stop(self) -> None:
        """Cancel both startup and update timers once, including on shutdown."""
        for scheduled in (self.scheduled_tick, self.scheduled_greeting):
            if scheduled is not None:
                self._cancel(scheduled)
        self.scheduled_tick = None
        self.scheduled_greeting = None
