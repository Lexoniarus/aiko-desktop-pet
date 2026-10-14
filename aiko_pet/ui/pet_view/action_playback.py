"""Own the current visual action and its timed completion deadline.

Sprite rendering is delegated to the existing pet-view renderer. This class
does not alter pet needs, choose dialogue, or schedule Tk frame callbacks.
"""

from __future__ import annotations

import time
from typing import Callable

from ...pet.animation.character import CharacterCatalog


class ActionPlayback:
    """Coordinate an authored animation action with one mutable deadline."""

    def __init__(
        self, assets: CharacterCatalog, *,
        begin: Callable[[str, float], None],
        cancel: Callable[[float], None],
    ) -> None:
        self._assets = assets
        self._begin = begin
        self._cancel = cancel
        self.state = "idle"
        self.until = 0.0

    def start(
        self, state: str, duration: float, *, started_at: float | None = None,
    ) -> None:
        now = time.monotonic() if started_at is None else started_at
        clip = self._assets.clips[state]
        if not clip.loop:
            duration = clip.duration_seconds
        self.state = state
        self.until = now + duration
        self._begin(state, now)

    def cancel_at(self, now: float) -> None:
        self.until = now
        self._cancel(now)

    def extend(self, deadline: float) -> None:
        self.until = max(self.until, deadline)
