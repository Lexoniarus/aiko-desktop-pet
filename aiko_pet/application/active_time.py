"""Consume active session intervals exactly once, independent of wall time."""

from __future__ import annotations

import math
from typing import Callable


class ActiveSessionClock:
    """The supplied uptime reader excludes system suspend and hibernation."""

    def __init__(self, reader: Callable[[], float | None]) -> None:
        self._reader = reader
        self._anchor = self._sample()

    def _sample(self) -> float | None:
        value = self._reader()
        return value if value is not None and math.isfinite(value) else None

    def consume(self) -> float:
        """Reset after unavailable/backward readings rather than invent time."""
        previous, current = self._anchor, self._sample()
        self._anchor = current
        if previous is None or current is None:
            return 0.0
        return max(0.0, current - previous)
