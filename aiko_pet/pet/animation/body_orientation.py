"""Whole-body turning steps for gaze; independent of desktop locomotion.

Three-quarter poses orient a stationary pet. They never advance her world
position or replace the distinct profile walking/running clips.
"""

from __future__ import annotations

from .animation import SpriteSelection

TURN_DWELL_SECONDS = 1.2
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
        self._candidate = 0
        self._candidate_since = 0.0
        self._next_step_at = 0.0
        self._look_direction = 0

    def select(self, now: float, choice: SpriteSelection) -> SpriteSelection:
        """Follow sustained left/right attention, not the gaze's steepness."""
        direction = choice.fixed_frame if choice.animation == "look" else None
        if choice.animation not in ("idle", "look"):
            self.reset()
            return choice
        candidate = 0
        if direction is not None:
            if 1 <= direction <= 7:
                candidate = 1
            elif 9 <= direction <= 15:
                candidate = -1
        if candidate != self._candidate:
            self._candidate = candidate
            self._candidate_since = now
        if direction is None:
            # With no gaze, frontal is the normal resting body orientation.
            self._target = 0
        elif now - self._candidate_since >= TURN_DWELL_SECONDS - 1e-6:
            self._target = candidate
        if self.phase == 0:
            if self._target and self._target == candidate:
                self.side = self._target
                self.phase = 1
                self._next_step_at = now + TURN_STEP_SECONDS
            else:
                # A superseded pending turn must not start after returning.
                self._target = 0
                return choice
        elif now >= self._next_step_at - 1e-6:
            if self._target == self.side:
                self.phase = min(4, self.phase + 1)
            else:
                self.phase -= 1
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
        if self.phase == 4 and self._target == self.side and direction is not None:
            # Brief opposite-side flicks must not turn the body or attach an
            # impossible opposite-facing head before the dwell has elapsed.
            return SpriteSelection(
                f"body-look-{label}",
                body_look_index(self.side, self._look_direction),
            )
        return SpriteSelection(f"body-turn-{label}", self.phase)
