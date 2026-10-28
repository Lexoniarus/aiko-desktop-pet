"""Small autonomous gestures while Aiko is genuinely idle.

An idle blink is a complete eight-frame animation, followed by a neutral
resting pose. Brief independent gaze choices use the existing sixteen static
directional sprites without hijacking mouse tracking or dialogue scheduling.
"""

from __future__ import annotations

import random
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from ..balance import BALANCE
from ..mind.cursor_behaviour import BodyIntent
from .animation import SpriteSelection, choose_passive_animation

_DIRECTIONS = (2, 3, 4, 12, 13, 14)
# Repeating positions make the one-pixel sway gentler and less busy.
# Eight phases still form a 3.36-second cycle at 420 ms per phase.
_SWAY_OFFSETS = (0, 0, 1, 1, 0, 0, -1, -1)
_SWAY_STEP_SECONDS = BALANCE.number("ambient", "sway_step_seconds")
_BLINK_GAP_SECONDS = (
    BALANCE.number("ambient", "blink_gap_minimum_seconds"),
    BALANCE.number("ambient", "blink_gap_maximum_seconds"),
)


@dataclass(frozen=True, slots=True)
class AmbientIntent:
    """One passive pose request, without movement or an independent action owner."""

    sprite: SpriteSelection
    body: BodyIntent = "front"
    side: int = 0


class AmbientDirector:
    """Pure policy for blink gaps, quiet poses and occasional self-glances."""

    def __init__(
        self,
        started_at: float,
        *,
        between: Callable[[float, float], float] = random.uniform,
        direction: Callable[[Sequence[int]], int] = random.choice,
        body_poses: bool = False,
    ) -> None:
        self._between = between
        self._direction = direction
        self._body_poses = body_poses
        self._glance_count = 0
        self._glance_side = 0
        self._body_settled = False
        self._body_hold_seconds = 0.0
        self._next_head_at = float("inf")
        self.outing_side = 0
        self._outing_until = started_at
        self._blink_active = False
        self._motion_started_at = started_at
        self._glance_frame: int | None = None
        self._glance_until = started_at
        self.next_blink_at = started_at + self._between(*_BLINK_GAP_SECONDS)
        self.next_glance_at = started_at + self._between(
            BALANCE.number("ambient", "glance_gap_minimum_seconds"),
            BALANCE.number("ambient", "glance_gap_maximum_seconds"),
        )

    def finish_outing(self, now: float, side: int) -> None:
        """A small outing ends with a quiet stand before the ordered front return."""
        self.outing_side = side
        self._outing_until = now + self._between(1, 2)

    @property
    def blinking(self) -> bool:
        return self._blink_active

    def suspend(self, now: float, *, keep_pose_motion: bool = False) -> None:
        """Yield to attention without repeatedly postponing a pending glance."""
        self.outing_side = 0
        if not keep_pose_motion:
            self._motion_started_at = now
        self._blink_active = False
        # An interrupted glance is consumed, not resumed as a stale held pose.
        # A merely pending glance keeps its due time and waits for free Idle.
        if self._glance_frame is not None:
            self.next_glance_at = now + self._between(
                BALANCE.number("ambient", "glance_gap_minimum_seconds"),
                BALANCE.number("ambient", "glance_gap_maximum_seconds"),
            )
        self._glance_frame = None
        self._glance_side = 0
        self._body_settled = False
        self._next_head_at = float("inf")
        self._glance_until = now
        self.next_blink_at = now + self._between(*_BLINK_GAP_SECONDS)

    def motion_offset(self, now: float) -> int:
        """Head sway relative to the selected pose, not the whole character."""
        elapsed = max(0.0, now - self._motion_started_at)
        step = int(elapsed / _SWAY_STEP_SECONDS) % len(_SWAY_OFFSETS)
        return _SWAY_OFFSETS[step]

    def choose(self, now: float) -> SpriteSelection:
        """Return one stable look pose, active blink or neutral idle rest."""
        if self.outing_side:
            if now < self._outing_until:
                return SpriteSelection("look", 4 if self.outing_side > 0 else 12)
            self.outing_side = 0
        if self._blink_active:
            return SpriteSelection("idle")

        if self._glance_frame is not None:
            if (now < self._glance_until
                    or self._glance_side and not self._body_settled):
                if now >= self._next_head_at:
                    directions = (2, 3, 4) if self._glance_side > 0 else (12, 13, 14)
                    options = tuple(n for n in directions if n != self._glance_frame)
                    self._glance_frame = self._direction(options)
                    if self._glance_frame not in options:
                        raise ValueError("Invalid autonomous body glance direction")
                    self._next_head_at = float("inf")
                return SpriteSelection("look", fixed_frame=self._glance_frame)
            self._glance_frame = None
            self._glance_side = 0
            self.next_glance_at = now + self._between(
                BALANCE.number("ambient", "glance_gap_minimum_seconds"),
                BALANCE.number("ambient", "glance_gap_maximum_seconds"),
            )

        if now >= self.next_glance_at:
            index = self._direction(_DIRECTIONS)
            if index not in _DIRECTIONS:
                raise ValueError("Invalid autonomous glance direction")
            self._glance_frame = index
            self._glance_count += 1
            self._glance_side = (
                (1 if index < 8 else -1)
                if self._body_poses and self._glance_count % BALANCE.integer(
                    "ambient", "body_glance_every",
                ) == 0 else 0
            )
            self._body_settled = False
            self._body_hold_seconds = self._between(
                BALANCE.number("ambient", "body_hold_minimum_seconds"
                               if self._glance_side else "glance_hold_minimum_seconds"),
                BALANCE.number("ambient", "body_hold_maximum_seconds"
                               if self._glance_side else "glance_hold_maximum_seconds"),
            )
            self._glance_until = now + self._body_hold_seconds
            return SpriteSelection("look", fixed_frame=index)

        if now >= self.next_blink_at:
            self._blink_active = True
            return SpriteSelection("idle")
        return SpriteSelection("idle", fixed_frame=0)

    def note_body_settled(self, now: float, side: int) -> None:
        """Start the quiet hold only after the renderer reaches the chosen pose."""
        if self._glance_side == side and side and not self._body_settled:
            self._body_settled = True
            self._glance_until = now + self._body_hold_seconds
            self._next_head_at = now + self._body_hold_seconds / 2

    def select_passive_animation(
        self,
        now: float,
        *,
        gaze_direction: int | None,
        observing_computer: bool,
        computer_busy: bool,
        energy: float,
        mood: float,
        satiety: float,
        forward_gaze: bool = False,
    ) -> AmbientIntent:
        """Choose the passive pose and preserve ambient timing on gaze."""
        choice = choose_passive_animation(
            gaze_direction=gaze_direction,
            observing_computer=observing_computer,
            computer_busy=computer_busy,
            energy=energy,
            mood=mood,
            satiety=satiety,
            forward_gaze=forward_gaze,
        )
        if choice.animation == "idle" and choice.fixed_frame is None:
            return AmbientIntent(
                self.choose(now),
                "three_quarter" if self._glance_side else "front", self._glance_side,
            )
        self.suspend(
            now,
            keep_pose_motion=(
                forward_gaze
                or choice.animation == "look" and choice.fixed_frame is not None
            ),
        )
        return AmbientIntent(choice)

    def finish_blink(self, now: float) -> None:
        """A full eight-frame blink ended; do not immediately repeat it."""
        if self._blink_active:
            self._blink_active = False
            self.next_blink_at = now + self._between(*_BLINK_GAP_SECONDS)
