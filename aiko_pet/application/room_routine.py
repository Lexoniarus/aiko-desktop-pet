"""Aiko's fixed room sleep window, independent of learned computer activity."""

from __future__ import annotations

from ..pet.mind.adaptive import AdaptiveRoutine
from ..pet.sleep import SleepContext


class RoomRoutine(AdaptiveRoutine):
    """Reuse contact/history contracts without sampling or training a rhythm."""

    def sleep_context(self, *, observed: bool = False) -> SleepContext:
        # An explicit initial profile, rather than imported desktop learning.
        # Meal slots and physical recovery retain the canonical pet policies.
        return SleepContext(start_minute=23 * 60, end_minute=8 * 60)
