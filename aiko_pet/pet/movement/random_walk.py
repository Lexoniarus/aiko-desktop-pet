"""Random walking departure and rest policy, independent of motion execution."""

from __future__ import annotations

import random

from ..balance import BALANCE
from .contracts import MotionKind, WalkConditions


class RandomWalkPlanner:
    """Own random walk timing and choose one bounded departure at a time."""

    def __init__(self, *, next_walk_at: float = 0.0) -> None:
        self.next_walk_at = next_walk_at
        self.kind: MotionKind = "run"

    def pause(self, now: float, *, quiet_period: bool) -> None:
        """Schedule rest from the moment a walk ended or became blocked."""
        self.next_walk_at = now + random.uniform(
            BALANCE.number("cursor_behaviour", "idle_step_minimum_seconds"),
            BALANCE.number("cursor_behaviour", "idle_step_maximum_seconds"),
        )

    def plan_departure(self, conditions: WalkConditions) -> float | None:
        """Choose an allowed random stride; leave movement execution to caller."""
        if conditions.now < self.next_walk_at:
            return None
        if not conditions.small_idle_steps:
            self.pause(conditions.now, quiet_period=conditions.quiet_period)
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
        self.kind = "step"
        count = 2 if random.random() < .2 else 1
        amount = count * conditions.sprite_width * BALANCE.number(
            "cursor_behaviour", "step_width_fraction",
        )
        room = (limit - conditions.x if direction > 0
                else conditions.x - conditions.track.left)
        return direction * min(amount, max(0, room))
