"""Execute horizontal motion, while delegating random choices to a planner."""

from __future__ import annotations

from .contracts import WalkConditions, WalkStep
from .random_walk import RandomWalkPlanner


class WalkController:
    """Own remaining travel, subpixel motion and safe interruptions."""

    def __init__(self, *, next_walk_at: float = 0.0) -> None:
        self.random_walk = RandomWalkPlanner(next_walk_at=next_walk_at)
        self.remaining_distance = 0.0
        self._residual = 0.0
        self._requested = 0.0
        self._blocked = False
        self._quiet = False

    @property
    def next_walk_at(self) -> float:
        """Expose existing departure timing while its planner owns the value."""
        return self.random_walk.next_walk_at

    def pause(self, now: float) -> None:
        """Begin a complete rest interval at the actual end of a walk."""
        self.remaining_distance = 0.0
        self._residual = 0.0
        self.random_walk.pause(now, quiet_period=self._quiet)

    def interrupt(self) -> None:
        """Resume with a full pause after the blocking activity ends."""
        self.remaining_distance = 0.0
        self._residual = 0.0
        self._blocked = True

    def plan_step(self, conditions: WalkConditions) -> WalkStep | None:
        """Prepare one step, respecting work, hover, sleep and energy."""
        now = conditions.now
        self._quiet = conditions.quiet_period
        if (
            conditions.attention_active and self.remaining_distance == 0
            and conditions.auto_walk and not conditions.sleeping
            and not conditions.toolbar_visible
            and not (conditions.observing_computer and conditions.computer_busy)
        ):
            # Brief cursor attention postpones departure, not the entire rest.
            return None
        if (
            (conditions.observing_computer and conditions.computer_busy)
            or not conditions.auto_walk
            or conditions.sleeping
            or conditions.attention_active
            or conditions.toolbar_visible
        ):
            self.interrupt()
            return None
        if self._blocked:
            self._blocked = False
            self.pause(now)
            return None

        if self.remaining_distance == 0 and now >= self.next_walk_at:
            departure = self.random_walk.plan_departure(conditions)
            if departure is not None:
                self.remaining_distance = departure

        if self.remaining_distance == 0:
            return None
        direction = 1 if self.remaining_distance > 0 else -1
        pixels = direction * min(
            abs(self.remaining_distance),
            max(0.0, conditions.speed_pixels_per_second * conditions.elapsed_seconds),
        )
        if conditions.elapsed_seconds > 0:
            pixels += self._residual
        self._requested = pixels
        animation = "running-right" if direction > 0 else "running-left"
        return WalkStep(pixels=pixels, animation=animation)

    def record_displacement(
        self, moved_pixels: float, *, now: float, blocked: bool = False,
    ) -> bool:
        """Consume actual clamped movement; return true when walking stops."""
        self.remaining_distance -= moved_pixels
        self._residual = self._requested - moved_pixels
        if blocked or abs(self.remaining_distance) < 1:
            self.pause(now)
            return True
        return False
