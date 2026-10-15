"""Random walking departure and rest policy, independent of motion execution."""

from __future__ import annotations

import random

from ..balance import BALANCE
from .contracts import WalkConditions


class RandomWalkPlanner:
    """Own random walk timing and choose one bounded departure at a time."""

    def __init__(self, *, next_walk_at: float = 0.0) -> None:
        self.next_walk_at = next_walk_at

    def pause(self, now: float, *, quiet_period: bool) -> None:
        """Schedule rest from the moment a walk ended or became blocked."""
        self.next_walk_at = now + random.uniform(
            BALANCE.integer(
                "walk",
                "quiet_pause_min_seconds" if quiet_period else "pause_min_seconds",
            ),
            BALANCE.integer("walk", "pause_max_seconds"),
        )

    def plan_departure(self, conditions: WalkConditions) -> float | None:
        """Choose an allowed random stride; leave movement execution to caller."""
        if conditions.now < self.next_walk_at:
            return None
        if conditions.energy < BALANCE.integer("walk", "minimum_energy"):
            self.pause(conditions.now, quiet_period=conditions.quiet_period)
            return None

        limit = conditions.track.right - conditions.sprite_width
        if conditions.x <= conditions.track.left + BALANCE.integer(
            "walk", "edge_margin_pixels"
        ):
            direction = 1
        elif conditions.x >= limit - BALANCE.integer("walk", "edge_margin_pixels"):
            direction = -1
        else:
            direction = random.choice((-1, 1))
        self.next_walk_at = float("inf")
        return (
            direction
            * random.randint(
                BALANCE.integer("walk", "minimum_cycles"),
                BALANCE.integer("walk", "maximum_cycles"),
            )
            * conditions.stride_pixels
        )
