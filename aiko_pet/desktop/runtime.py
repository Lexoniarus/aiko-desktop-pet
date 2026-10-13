"""Deterministic desktop scheduler driven by explicit, named phase ports.

The scheduler owns timer IDs and tick ordering, but receives no DesktopPet,
legacy private-method façade, UI widgets or domain state.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable

TICK_MILLISECONDS = 140


@dataclass(frozen=True, slots=True)
class DesktopTickPorts:
    """Capabilities needed by the desktop update scheduler, not an object API."""

    is_closed: Callable[[], bool]
    request_tick: Callable[[], None]
    greet: Callable[[], None]
    advance_lifecycle: Callable[[float, float], None]
    refresh_taskbar: Callable[[float], None]
    poll_desktop_clicks: Callable[[], None]
    refresh_hover: Callable[[float], None]
    observe_computer: Callable[[float], None]
    observe_pointer: Callable[[float], tuple[int, int]]
    render_character: Callable[[float, float, tuple[int, int]], None]
    show_idle_emote: Callable[[float], None]
    speak_spontaneously: Callable[[float], None]
    present_notification: Callable[[float], None]
    refresh_overlays_and_save: Callable[[float], None]


class DesktopRuntime:
    """Advance ordered phases once per tick and own all its Tk timer IDs."""

    def __init__(
        self,
        ports: DesktopTickPorts,
        *,
        schedule: Callable[[int, Callable[[], None]], str],
        cancel: Callable[[str], None],
        monotonic: Callable[[], float] = time.monotonic,
        wall_time: Callable[[], float] = time.time,
    ) -> None:
        self._ports = ports
        self._schedule = schedule
        self._cancel = cancel
        self._monotonic = monotonic
        self._wall_time = wall_time
        self.last_tick = monotonic()
        self.scheduled_tick: str | None = None
        self.scheduled_greeting: str | None = None

    def start(self) -> None:
        """Schedule the first tick and greeting only for an open desktop."""
        if self._ports.is_closed():
            return
        if self.scheduled_tick is not None:
            return
        self.scheduled_greeting = self._schedule(
            460, self._ports.greet,
        )
        self.scheduled_tick = self._schedule(
            TICK_MILLISECONDS, self._ports.request_tick,
        )

    def tick(self) -> None:
        """Preserve original stage order and bounded sprite delta time."""
        ports = self._ports
        if ports.is_closed():
            return
        if self.scheduled_tick is not None:
            self._cancel(self.scheduled_tick)
            self.scheduled_tick = None
        now = self._monotonic()
        elapsed = max(0.0, min(0.5, now - self.last_tick))
        self.last_tick = now
        timestamp = self._wall_time()
        ports.advance_lifecycle(now, timestamp)
        ports.refresh_taskbar(now)
        ports.poll_desktop_clicks()
        ports.refresh_hover(now)
        ports.observe_computer(now)
        pointer = ports.observe_pointer(now)
        ports.render_character(now, elapsed, pointer)
        ports.show_idle_emote(now)
        ports.speak_spontaneously(now)
        ports.present_notification(now)
        ports.refresh_overlays_and_save(now)
        if not ports.is_closed():
            self.scheduled_tick = self._schedule(
                TICK_MILLISECONDS, ports.request_tick,
            )

    def stop(self) -> None:
        """Cancel both timer families, including pending startup greeting."""
        for scheduled in (self.scheduled_tick, self.scheduled_greeting):
            if scheduled is not None:
                self._cancel(scheduled)
        self.scheduled_tick = None
        self.scheduled_greeting = None
