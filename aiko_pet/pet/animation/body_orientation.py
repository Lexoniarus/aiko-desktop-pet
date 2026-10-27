"""Whole-body turning steps for gaze; independent of desktop locomotion.

Three-quarter poses orient a stationary pet. They never advance her world
position or replace the distinct profile walking/running clips.
"""

from __future__ import annotations

from ..mind.cursor_behaviour import BodyIntent
from .animation import SpriteSelection

TURN_STEP_SECONDS = 0.14


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

    @property
    def motion_ready(self) -> bool:
        return self._motion and self.phase == 8

    def orient_for_motion(self, now: float, direction: int) -> SpriteSelection:
        """Turn through existing whole poses before translating the body."""
        self._motion = True
        if self.phase == 0:
            self.side = direction
        if now >= self._next_step_at - 1e-6:
            self.phase += 1 if self.side == direction else -1
            self.phase = max(0, min(8, self.phase))
            self._next_step_at = now + TURN_STEP_SECONDS
        label = "right" if self.side == 1 else "left"
        return SpriteSelection(f"body-orient-{label}", self.phase)

    def select(
        self, now: float, choice: SpriteSelection, *,
        intent: BodyIntent = "front", side: int = 0,
    ) -> SpriteSelection:
        """Execute an owner's explicit pose; head sectors never initiate turns."""
        direction = choice.fixed_frame if choice.animation == "look" else None
        self._motion = False
        if choice.animation not in ("idle", "look"):
            self.reset()
            return choice
        target = side if intent != "front" and side in (-1, 1) else 0
        limit = 8 if intent == "profile" else 4
        self._target = target
        if self.phase == 0:
            if not target:
                self.side = 0
                return choice
            self.side = target
            self._look_direction = 4 if target == 1 else 12
            self.phase = 1
            self._next_step_at = now + TURN_STEP_SECONDS
        elif now >= self._next_step_at - 1e-6:
            destination = limit if target == self.side else 0
            self.phase += (destination > self.phase) - (destination < self.phase)
            self._next_step_at = now + TURN_STEP_SECONDS
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
