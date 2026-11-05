"""Present room travel with the desktop's authored turns and walking banks."""

from __future__ import annotations

import math

from ..pet.animation.animation import SpriteSelection
from ..pet.animation.body_orientation import BodyOrientation
from ..world.room import RoomGeometry, RoomPoint


class RoomLocomotion:
    # The native step covers 16 logical pixels in 620 ms. Room artwork displays
    # the 156-logical-pixel visible figure at 400 world units, without skating.
    speed = 16 / 0.62 * 400 / 156

    def __init__(self) -> None:
        self.orientation = BodyOrientation()
        self.selection = SpriteSelection("rest-neutral")

    def walk(self, now: float, start: RoomPoint, end: RoomPoint) -> bool:
        dx = RoomGeometry.delta(start.x, end.x)
        dy = (end.depth - start.depth) * 475
        side = 1 if dx >= 0 else -1
        # These are the existing compatible three-quarter head/step variants;
        # no new back-facing artwork or mirrored character is fabricated.
        slope = dy / max(1, abs(dx))
        gaze = (
            2
            if slope < -0.7
            else 3
            if slope < -0.12
            else 6
            if slope > 0.7
            else 5
            if slope > 0.12
            else 4
        )
        if side < 0:
            gaze = 16 - gaze
        if self.orientation.side not in (0, side):
            self.orientation.reset()
        turn = self.orientation.orient_for_gaze_motion(now, gaze)
        if not self.orientation.motion_ready:
            self.selection = turn
            return False
        label = "right" if side > 0 else "left"
        self.selection = SpriteSelection(f"body-step-{label}-{gaze:02}")
        return True

    def rest(self, now: float, look: tuple[float, float] | None = None) -> None:
        choice = SpriteSelection("idle")
        if look is not None and math.hypot(*look) > 0.1:
            sector = round(math.degrees(math.atan2(look[0], -look[1])) / 22.5) % 16
            choice = SpriteSelection("look", sector)
        self.selection = self.orientation.select(now, choice)
        if self.selection.animation == "idle":
            self.selection = SpriteSelection("rest-neutral")
