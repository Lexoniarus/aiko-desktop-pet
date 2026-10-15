"""Rolling food-workload evidence from actual inputs and measured hardware.

Keep only one-minute aggregate buckets, never keyboard identities, text,
application titles, click positions, or a raw input-event history.
"""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass

from ..pet.balance import BALANCE
from ..pet.food import FoodActivity


@dataclass(frozen=True, slots=True)
class FoodActivityBalance:
    """Adjust these observation knobs without touching the hunger rules."""

    short_window_minutes: float = BALANCE.number(
        "food_activity", "short_window_minutes"
    )
    long_window_minutes: float = BALANCE.number("food_activity", "long_window_minutes")
    short_window_weight: float = BALANCE.number("food_activity", "short_window_weight")
    max_sample_gap_seconds: float = BALANCE.number(
        "food_activity", "max_sample_gap_seconds"
    )
    last_input_is_recent_seconds: float = BALANCE.number(
        "food_activity", "last_input_is_recent_seconds"
    )
    meaningful_mouse_move_pixels: float = BALANCE.number(
        "food_activity", "meaningful_mouse_move_pixels"
    )
    inferred_keyboard_or_wheel_activity: float = BALANCE.number(
        "food_activity", "inferred_keyboard_or_wheel_activity"
    )
    bucket_seconds: int = BALANCE.integer("food_activity", "bucket_seconds")
    recalculate_summary_after_seconds: float = BALANCE.number(
        "food_activity", "recalculate_summary_after_seconds"
    )


ACTIVITY_BALANCE = FoodActivityBalance()


@dataclass(slots=True)
class ActivityBucket:
    """Elapsed time and weighted activity in a short anonymous interval."""

    index: int
    observed_seconds: float = 0.0
    user_active_seconds: float = 0.0
    hardware_work_seconds: float = 0.0


class FoodActivityHistory:
    """Observe input presence and hardware load without hooks or raw logging."""

    def __init__(self) -> None:
        self._buckets: deque[ActivityBucket] = deque()
        self._previous_sample_at: float | None = None
        self._previous_pointer: tuple[int, int] | None = None
        self._previous_buttons: tuple[bool, bool] | None = None
        self._cached_summary = FoodActivity()
        self._last_summary_at = float("-inf")

    def observe(
        self,
        *,
        now: float,
        pointer: tuple[int, int] | None,
        input_idle_seconds: float | None,
        mouse_buttons_down: tuple[bool, bool] | None,
        measured_hardware_load: float | None,
    ) -> None:
        """Attribute load only to time that was actually sampled."""
        previous_time = self._previous_sample_at
        self._previous_sample_at = now
        if not math.isfinite(now):
            return
        delta = 0.0 if previous_time is None else now - previous_time
        meaningful_motion = False
        if pointer is not None and self._previous_pointer is not None:
            dx = abs(pointer[0] - self._previous_pointer[0])
            dy = abs(pointer[1] - self._previous_pointer[1])
            meaningful_motion = dx + dy >= ACTIVITY_BALANCE.meaningful_mouse_move_pixels
        self._previous_pointer = pointer
        clicked = False
        if mouse_buttons_down is not None and self._previous_buttons is not None:
            clicked = any(
                down and not previous
                for down, previous in zip(
                    mouse_buttons_down,
                    self._previous_buttons,
                )
            )
        self._previous_buttons = mouse_buttons_down
        if not 0.0 < delta <= ACTIVITY_BALANCE.max_sample_gap_seconds:
            self._remove_expired(now)
            return
        recent_input = (
            input_idle_seconds is not None
            and math.isfinite(input_idle_seconds)
            and 0.0
            <= input_idle_seconds
            <= ACTIVITY_BALANCE.last_input_is_recent_seconds
        )
        input_strength = (
            1.0
            if meaningful_motion or clicked
            else (
                ACTIVITY_BALANCE.inferred_keyboard_or_wheel_activity
                if recent_input
                else 0.0
            )
        )
        hardware = (
            max(0.0, min(1.0, measured_hardware_load))
            if measured_hardware_load is not None
            and math.isfinite(measured_hardware_load)
            else 0.0
        )
        index = int(now // ACTIVITY_BALANCE.bucket_seconds)
        if not self._buckets or self._buckets[-1].index != index:
            self._buckets.append(ActivityBucket(index))
        bucket = self._buckets[-1]
        bucket.observed_seconds += delta
        bucket.user_active_seconds += delta * input_strength
        bucket.hardware_work_seconds += delta * hardware
        self._remove_expired(now)

    def _remove_expired(self, now: float) -> None:
        cutoff = (
            now - ACTIVITY_BALANCE.long_window_minutes * 60.0
        ) // ACTIVITY_BALANCE.bucket_seconds
        while self._buckets and self._buckets[0].index < cutoff:
            self._buckets.popleft()

    def _average(self, now: float, window_minutes: float) -> FoodActivity:
        cutoff = now - window_minutes * 60.0
        observed = 0.0
        user = 0.0
        hardware = 0.0
        for bucket in self._buckets:
            if (bucket.index + 1) * ACTIVITY_BALANCE.bucket_seconds < cutoff:
                continue
            observed += bucket.observed_seconds
            user += bucket.user_active_seconds
            hardware += bucket.hardware_work_seconds
        if observed <= 0:
            return FoodActivity()
        return FoodActivity(
            hardware_load=min(1.0, hardware / observed),
            user_input_activity=min(1.0, user / observed),
        )

    def current_food_activity(self, now: float) -> FoodActivity:
        """Blend current activity and the last hour of observed intervals."""
        if now - self._last_summary_at < (
            ACTIVITY_BALANCE.recalculate_summary_after_seconds
        ):
            return self._cached_summary
        self._last_summary_at = now
        self._remove_expired(now)
        recent = self._average(now, ACTIVITY_BALANCE.short_window_minutes)
        hour = self._average(now, ACTIVITY_BALANCE.long_window_minutes)
        recent_weight = ACTIVITY_BALANCE.short_window_weight
        self._cached_summary = FoodActivity(
            hardware_load=(
                recent_weight * recent.hardware_load
                + (1.0 - recent_weight) * hour.hardware_load
            ),
            user_input_activity=(
                recent_weight * recent.user_input_activity
                + (1.0 - recent_weight) * hour.user_input_activity
            ),
        )
        return self._cached_summary
