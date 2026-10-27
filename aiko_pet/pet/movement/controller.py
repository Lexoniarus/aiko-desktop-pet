"""Execute horizontal motion, while delegating random choices to a planner."""

from __future__ import annotations

from dataclasses import replace

from ..balance import BALANCE
from .contracts import (
    MotionKind,
    MotionRequest,
    MotionSource,
    MotionStopReason,
    WalkConditions,
    WalkStep,
)
from .random_walk import RandomWalkPlanner

_PRIORITY: tuple[MotionSource, ...] = ("world", "cursor", "idle")


class WalkController:
    """Own remaining travel, subpixel motion and safe interruptions."""

    def __init__(self, *, next_walk_at: float = 0.0) -> None:
        self.random_walk = RandomWalkPlanner(next_walk_at=next_walk_at)
        self.remaining_distance = 0.0
        self._residual = 0.0
        self._requested = 0.0
        self._blocked = False
        self._quiet = False
        self._requests: dict[MotionSource, MotionRequest] = {}
        self._active: MotionRequest | None = None
        self._completed: dict[MotionSource, int] = {}
        self._progress: dict[MotionSource, tuple[int, float, float]] = {}
        self._planned_speed = 0.0
        self.completion_reason: MotionStopReason = "reached"

    @property
    def goal_x(self) -> float | None:
        request = self._requests.get("world")
        return request.target_x if request is not None else None

    @property
    def source(self) -> MotionSource:
        return self._active.source if self._active is not None else "idle"

    @property
    def kind(self) -> MotionKind:
        return self._active.kind if self._active is not None else self.random_walk.kind

    @property
    def token(self) -> int:
        return self._active.token if self._active is not None else 0

    def replace_request(self, source: MotionSource, request: MotionRequest) -> None:
        if source != request.source:
            raise ValueError("Movement request source mismatch")
        if source == "cursor" and request.token <= self._completed.get(source, -1):
            return
        if self._requests.get(source) == request:
            return
        previous = self._requests.get(source)
        if (source == "cursor" and previous is not None
                and previous.token == request.token):
            self.retarget(source, request.token, request.target_x)
            return
        if (
            self._requests.get(source) is None
            or self._requests[source].token != request.token
        ):
            self._progress[source] = (request.token, 0.0, 0.0)
        self._requests[source] = request
        if source != "cursor":
            self._completed.pop(source, None)

    def retarget(self, source: MotionSource, token: int, target_x: float) -> bool:
        """Only the selected point may change; consumed budgets remain authoritative."""
        old = self._requests.get(source)
        if old is None or old.token != token or self._completed.get(source) == token:
            return False
        updated = replace(old, target_x=target_x)
        self._requests[source] = updated
        if self._active == old:
            self._active = updated
        return True

    def release_request(self, source: MotionSource) -> None:
        old = self._requests.pop(source, None)
        self._progress.pop(source, None)
        if source == "cursor" and old is not None:
            self._completed[source] = max(old.token, self._completed.get(source, -1))
        elif source != "cursor":
            self._completed.pop(source, None)
        if self._active is not None and self._active.source == source:
            self._active = None
            self.remaining_distance = 0
            self._residual = 0

    def request(self, source: MotionSource) -> MotionRequest | None:
        return self._requests.get(source)

    def set_goal(self, x: float | None) -> None:
        if x == self.goal_x:
            return
        if x is None:
            self.release_request("world")
        else:
            self.replace_request("world", MotionRequest("world", 0, x))
            self.remaining_distance = 0
            self._residual = 0
            self._blocked = False

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
        request = next(
            (
                self._requests[source]
                for source in _PRIORITY
                if source in self._requests
                and now <= self._requests[source].until
                and self._completed.get(source) != self._requests[source].token
            ),
            None,
        )
        if request is not None:
            if request != self._active:
                self._residual = 0
                self._active = request
            self.remaining_distance = request.target_x - conditions.x
        elif self._active is not None:
            self._active = None
            self.remaining_distance = 0
        attending = conditions.attention_active and self.source != "cursor"
        has_goal = request is not None or self.goal_x is not None
        self._quiet = conditions.quiet_period
        if (
            attending
            and self.remaining_distance == 0
            and (conditions.auto_walk or has_goal)
            and not conditions.sleeping
            and not conditions.menu_engaged
            and not (conditions.observing_computer and conditions.computer_busy)
        ):
            # Brief cursor attention postpones departure, not the entire rest.
            return None
        if (
            (conditions.observing_computer and conditions.computer_busy)
            or (not conditions.auto_walk and self.goal_x is None)
            or conditions.sleeping
            or attending
            or conditions.menu_engaged
        ):
            self.interrupt()
            return None
        if self._blocked:
            self._blocked = False
            self.pause(now)
            if not has_goal:
                return None

        if request is not None:
            if conditions.energy < BALANCE.number("walk", "minimum_energy"):
                self.interrupt()
                return None
            self.remaining_distance = request.target_x - conditions.x
            if abs(self.remaining_distance) < 1:
                self.remaining_distance = 0
                return None

        if not has_goal and self.remaining_distance == 0 and now >= self.next_walk_at:
            departure = self.random_walk.plan_departure(conditions)
            if departure is not None:
                self.remaining_distance = departure

        if self.remaining_distance == 0:
            return None
        direction = 1 if self.remaining_distance > 0 else -1
        elapsed = conditions.elapsed_seconds
        boundary = abs(self.remaining_distance)
        budget_distance = float("inf")
        if request is not None:
            _, spent, travelled = self._progress[request.source]
            remaining_time = max(0, request.movement_seconds - spent)
            elapsed = min(elapsed, remaining_time)
            budget_distance = min(
                remaining_time * conditions.speed_pixels_per_second,
                max(0, request.distance_pixels - travelled),
            )
            boundary = min(boundary, budget_distance)
            if request.step_pixels > 0:
                within = travelled % request.step_pixels
                boundary = min(boundary, request.step_pixels - within)
        self._planned_speed = conditions.speed_pixels_per_second
        allowance = max(0.0, self._planned_speed * elapsed)
        pixels = direction * min(boundary, allowance)
        if elapsed > 0:
            pixels += self._residual
            pixels = direction * min(direction * pixels, boundary, budget_distance)
        self._requested = pixels
        return WalkStep(pixels=pixels, direction=direction, kind=self.kind)

    def record_displacement(
        self,
        moved_pixels: float,
        *,
        now: float,
        blocked: bool = False,
    ) -> bool:
        """Consume actual clamped movement; return true when walking stops."""
        self.remaining_distance -= moved_pixels
        self._residual = self._requested - moved_pixels
        exhausted = False
        if self._active is not None and moved_pixels:
            token, spent, travelled = self._progress[self._active.source]
            spent += abs(moved_pixels) / max(self._planned_speed, 1e-9)
            travelled += abs(moved_pixels)
            self._progress[self._active.source] = (token, spent, travelled)
            exhausted = (
                (self._active.movement_seconds - spent) * self._planned_speed < 1
                or self._active.distance_pixels - travelled < 1
            )
        if blocked or exhausted or abs(self.remaining_distance) < 1:
            self.completion_reason = (
                "blocked" if blocked else "budget" if exhausted else "reached"
            )
            if self._active is not None:
                self._completed[self._active.source] = self._active.token
            self.pause(now)
            return True
        return False
