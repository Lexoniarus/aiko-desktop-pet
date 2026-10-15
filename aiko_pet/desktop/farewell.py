"""Non-blocking deliberate farewell before the desktop session terminates.

This coordinator owns the acknowledgement timeline, not Tk widgets, sprites,
simulation state, saved games or application shutdown implementation.
"""

from __future__ import annotations

from ..pet.content import GERMAN_TEXT

import math
from typing import Callable


class FarewellSequence:
    """Run one goodbye wave and bubble, then request the normal shutdown."""

    TEXT = GERMAN_TEXT.format("farewell.text")

    def __init__(
        self,
        *,
        schedule: Callable[[int, Callable[[], None]], str],
        cancel: Callable[[str], None],
        prepare: Callable[[], None],
        animate: Callable[[], None],
        say: Callable[[str, int], None],
        finish: Callable[[], None],
        seconds: float,
    ) -> None:
        if not math.isfinite(seconds) or seconds <= 0:
            raise ValueError("Farewell clip must have a positive duration")
        self._schedule = schedule
        self._cancel = cancel
        self._prepare = prepare
        self._animate = animate
        self._say = say
        self._finish = finish
        # Let the whole double wave finish; leave time to read the short line.
        self.duration_ms = max(2600, math.ceil(seconds * 1000) + 500)
        self._pending_timer: str | None = None
        self._active = False

    @property
    def active(self) -> bool:
        return self._active

    @property
    def pending_timer(self) -> str | None:
        return self._pending_timer

    def begin(self) -> None:
        """Accept only the first quit request while a farewell is running."""
        if self._active:
            return
        self._active = True
        try:
            self._prepare()
            self._animate()
            # Teardown removes the bubble; never let its own timer hide it first.
            self._say(self.TEXT, self.duration_ms + 500)
            self._pending_timer = self._schedule(
                self.duration_ms,
                self._complete,
            )
        except Exception:
            # Quitting must remain possible even if displaying goodbye fails.
            self._active = False
            self._finish()

    def _complete(self) -> None:
        self._pending_timer = None
        if not self._active:
            return
        self._active = False
        self._finish()

    def cancel(self) -> None:
        """Cancel a delayed exit when another shutdown path has already won."""
        self._active = False
        if self._pending_timer is not None:
            self._cancel(self._pending_timer)
            self._pending_timer = None
