"""Whole-body turning steps for gaze; independent of desktop locomotion.

Three-quarter poses orient a stationary pet. They never advance her world
position or replace the distinct profile walking/running clips.
"""

from __future__ import annotations

import math

from ..mind.cursor_behaviour import BodyIntent
from .animation import SpriteSelection
from .gaze import sector_for_angle

TURN_STEP_SECONDS = 0.14
REACTIVE_TURN_STEP_SECONDS = 0.07


def body_look_index(side: int, direction: int) -> int:
    """Map compatible head directions onto one baked body pose bank."""
    if side == 1 and 0 <= direction <= 8:
        return direction
    if side == -1 and direction in (0, *range(8, 16)):
        return 0 if direction == 0 else direction - 7
    raise ValueError("Head direction conflicts with body orientation")


class BodyOrientation:
    """Present every turning step, returning through frontal on side changes."""

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.side = 0
        self.phase = 0
        self._target = 0
        self._next_step_at = 0.0
        self._look_direction = 0
        self._motion = False
        self._gaze_motion = False
        self._limit = 4

    @property
    def motion_ready(self) -> bool:
        return self._motion and self.phase == 8

    def next_delay_ms(self, now: float) -> int | None:
        """One existing frame timer may refresh an unfinished responsive turn."""
        destination = self._limit if self._target and self._target == self.side else 0
        if self.phase == destination and not (self.phase == 0 and self._target):
            return None
        return max(1, math.ceil((self._next_step_at - now) * 1000 - 1e-6))

    def constrain_direction(
        self, direction: tuple[float, float],
    ) -> tuple[float, float]:
        """Read actual pose compatibility, also used by subjective World sight."""
        if self.phase == 0:
            return direction
        sector = sector_for_angle(
            math.degrees(math.atan2(direction[0], direction[1])) % 360,
            self._look_direction,
        )
        if self.phase == 4 and self.supports_gaze(sector):
            return direction
        if self.phase == 4 or self._gaze_motion:
            angle = self._look_direction * math.pi / 8
            return (math.sin(angle), math.cos(angle))
        return (float(self.side), 0.0)

    def supports_gaze(self, direction: int | None) -> bool:
        if self.phase == 0:
            return True
        if direction is None:
            return False
        if self._gaze_motion and self.phase == 8:
            return 2 <= direction <= 6 if self.side == 1 else 10 <= direction <= 14
        return self.phase == 4 and (
            0 <= direction <= 8 if self.side == 1
            else direction == 0 or 8 <= direction <= 15
        )

    def orient_for_gaze_motion(self, now: float, direction: int) -> SpriteSelection:
        """Use existing compatible head banks; motion begins after a quarter pose."""
        side = 1 if 2 <= direction <= 6 else -1
        self._motion = self._gaze_motion = True
        self._target, self._limit = side, 8
        self._look_direction = direction
        self.side = side
        if self.phase == 0:
            self.phase = 4
            self._next_step_at = now + REACTIVE_TURN_STEP_SECONDS
        elif now >= self._next_step_at - 1e-6:
            self.phase = 8
        label = "right" if side == 1 else "left"
        return SpriteSelection(f"body-look-{label}", body_look_index(side, direction))

    def orient_for_motion(
        self, now: float, direction: int, *, responsive: bool = False,
    ) -> SpriteSelection:
        """Turn through existing whole poses before translating the body."""
        self._motion = True
        self._target, self._limit = direction, 8
        if self.phase == 0:
            self.side = direction
        if now >= self._next_step_at - 1e-6:
            self.phase += 1 if self.side == direction else -1
            self.phase = max(0, min(8, self.phase))
            self._next_step_at = now + (
                REACTIVE_TURN_STEP_SECONDS if responsive else TURN_STEP_SECONDS
            )
        label = "right" if self.side == 1 else "left"
        return SpriteSelection(f"body-orient-{label}", self.phase)

    def select_gaze_stance(
        self, now: float, choice: SpriteSelection, *, intent: BodyIntent, side: int,
    ) -> SpriteSelection:
        """Hold a compatible baked head without replaying fixed-head turn art.

        Emotional cursor gaze uses the same compact quarter pose as departure.
        Returning from a moving profile keeps that side instead of resetting to
        front. An incompatible or centered gaze restores frontal immediately.
        """
        direction = choice.fixed_frame if choice.animation == "look" else None
        compatible = direction is not None and side in (-1, 1) and (
            0 <= direction <= 8 if side == 1
            else direction == 0 or 8 <= direction <= 15
        )
        if intent == "front" or not compatible or direction is None:
            self.reset()
            return choice
        if self.phase != 4 or self.side != side:
            self._next_step_at = now + REACTIVE_TURN_STEP_SECONDS
        self.side, self.phase = side, 4
        self._target, self._limit = side, 4
        self._look_direction = direction
        self._motion = self._gaze_motion = False
        label = "right" if side == 1 else "left"
        return SpriteSelection(f"body-look-{label}", body_look_index(side, direction))

    def select(
        self, now: float, choice: SpriteSelection, *,
        intent: BodyIntent = "front", side: int = 0,
        responsive: bool = False,
    ) -> SpriteSelection:
        """Execute an owner's explicit pose; head sectors never initiate turns."""
        if self._gaze_motion:
            self.reset()
        direction = choice.fixed_frame if choice.animation == "look" else None
        interval = REACTIVE_TURN_STEP_SECONDS if responsive else TURN_STEP_SECONDS
        self._motion = False
        if choice.animation not in ("idle", "look"):
            self.reset()
            return choice
        target = side if intent != "front" and side in (-1, 1) else 0
        limit = 8 if intent == "profile" else 4
        self._target = target
        self._limit = limit
        if self.phase == 0:
            if not target:
                self.side = 0
                return choice
            self.side = target
            self._look_direction = 4 if target == 1 else 12
            self.phase = 1
            self._next_step_at = now + interval
        elif now >= self._next_step_at - 1e-6:
            destination = limit if target == self.side else 0
            self.phase += (destination > self.phase) - (destination < self.phase)
            self._next_step_at = now + interval
        if self.phase == 0:
            self.side = 0
            return choice
        label = "right" if self.side == 1 else "left"
        compatible = direction is not None and (
            0 <= direction <= 8 if self.side == 1
            else direction == 0 or 8 <= direction <= 15
        )
        if compatible and direction is not None:
            self._look_direction = direction
        if self.phase == 4 and target == self.side and limit == 4:
            return SpriteSelection(f"body-look-{label}",
                                   body_look_index(self.side, self._look_direction))
        family = "body-orient" if self.phase > 4 else "body-turn"
        return SpriteSelection(f"{family}-{label}", self.phase)
