"""Short-lived cursor attention history, without any desktop dependencies."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

from ..balance import BALANCE

MotionBand = Literal["still", "slow", "normal", "fast", "very_fast"]


@dataclass(frozen=True, slots=True)
class CursorAttentionSnapshot:
    """Immutable clock values used when rendering one frame."""

    last_pointer_move: float
    attention_until: float


@dataclass(frozen=True, slots=True)
class CursorPerception:
    """Normalized local evidence; velocity excludes the pet's own motion."""

    sampled_at: float = -100.0
    pointer: tuple[int, int] = (0, 0)
    distance: float = float("inf")
    speed: float = 0.0
    closing_speed: float = 0.0
    stationary_seconds: float = 0.0
    side: int = 0
    reachable: bool = False
    valid: bool = False

    @property
    def motion_band(self) -> MotionBand:
        """Normalized measurement only; interest and feelings belong to policy."""
        if self.stationary_seconds >= BALANCE.number(
            "cursor_behaviour", "stationary_override_seconds",
        ):
            return "still"
        if self.speed < BALANCE.number("cursor_behaviour", "slow_speed"):
            return "slow"
        if self.speed < BALANCE.number("cursor_behaviour", "attention_fast_speed"):
            return "normal"
        if self.speed < BALANCE.number("cursor_behaviour", "very_fast_speed"):
            return "fast"
        return "very_fast"


@dataclass(slots=True)
class CursorAttention:
    """Track pointer changes and the original brief walk-attention window."""

    previous_pointer: tuple[int, int] | None = None
    last_pointer_move: float = -100.0
    last_attention: float = -100.0
    attention_until: float = -100.0
    sampled_at: float = -100.0
    velocity: tuple[float, float] = (0.0, 0.0)
    stationary_since: float = -100.0
    steady_origin: tuple[int, int] | None = None
    sample_width: float = 192.0
    valid: bool = False

    def reset(self) -> None:
        """Forget cursor history on game-mode transitions."""
        self.previous_pointer = None
        self.last_pointer_move = -100.0
        self.last_attention = -100.0
        self.attention_until = -100.0
        self.sampled_at = -100.0
        self.velocity = (0.0, 0.0)
        self.stationary_since = -100.0
        self.steady_origin = None
        self.valid = False

    def snapshot(self) -> CursorAttentionSnapshot:
        """Read the current attention window without exposing mutable state."""
        return CursorAttentionSnapshot(
            last_pointer_move=self.last_pointer_move,
            attention_until=self.attention_until,
        )

    def observe(
        self,
        pointer: tuple[int, int],
        now: float,
        *,
        game_mode: bool = False,
        width: float = 192.0,
    ) -> bool:
        """Observe pointer motion; keep game-mode readings as baselines."""
        previous = self.previous_pointer
        dt = now - self.sampled_at
        self.valid = (
            previous is not None
            and 0 < dt <= 1.5
            and width == self.sample_width
            and not game_mode
        )
        if self.valid and previous is not None:
            alpha = 1 - math.exp(-dt / BALANCE.number(
                "cursor_behaviour", "velocity_filter_seconds",
            ))
            vx, vy = self.velocity
            self.velocity = (
                vx + alpha * ((pointer[0] - previous[0]) / dt - vx),
                vy + alpha * ((pointer[1] - previous[1]) / dt - vy),
            )
        else:
            self.velocity = (0.0, 0.0)
            self.steady_origin = pointer
            self.stationary_since = now
        if self.steady_origin is None or math.dist(pointer, self.steady_origin) > max(
            1.0, width * 0.012
        ):
            self.steady_origin = pointer
            self.stationary_since = now
        self.sampled_at, self.sample_width = now, width
        self.previous_pointer = pointer
        if game_mode or previous is None or pointer == previous:
            return False
        self.last_pointer_move = now
        if now - self.last_attention >= BALANCE.number(
            "cursor", "attention_interval_seconds"
        ):
            self.last_attention = now
            self.attention_until = now + BALANCE.number(
                "cursor", "attention_hold_seconds"
            )
        return True
