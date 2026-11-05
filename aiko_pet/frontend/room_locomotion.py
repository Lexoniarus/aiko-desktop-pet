"""Present room travel with the desktop's authored turns and walking banks."""

from __future__ import annotations

import math

from ..pet.animation.ambient import AmbientIntent
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
        side = (1 if dx > 0 else -1) if abs(dx) > 1 else (self.orientation.side or 1)
        if self.orientation.side not in (0, side):
            self.orientation.reset()
        label = "right" if side > 0 else "left"
        if dy > max(1, abs(dx) * 1.5):
            # The approved forward-facing quarter body is a stance/turn pose,
            # not a baked forward step cycle. Keep that distinction explicit.
            gaze = 4 if side > 0 else 12
            self.selection = self.orientation.select_gaze_stance(
                now,
                SpriteSelection("look", gaze),
                intent="three_quarter",
                side=side,
            )
            return True
        turn = self.orientation.orient_for_motion(now, side, responsive=True)
        if not self.orientation.motion_ready:
            self.selection = turn
            return False
        self.selection = SpriteSelection(f"body-step-{label}-profil")
        return True

    def rest(self, now: float, look: tuple[float, float] | None = None) -> None:
        choice = SpriteSelection("idle")
        if look is not None and math.hypot(*look) > 0.1:
            sector = round(math.degrees(math.atan2(look[0], -look[1])) / 22.5) % 16
            choice = SpriteSelection("look", sector)
            side = 1 if look[0] > 0.1 else -1 if look[0] < -0.1 else 0
            self.selection = self.orientation.select_gaze_stance(
                now,
                choice,
                intent="three_quarter" if side else "front",
                side=side,
            )
        else:
            self.selection = self.orientation.select(now, choice)
        if self.selection.animation == "idle":
            self.selection = SpriteSelection("rest-neutral")

    def idle(self, now: float, intent: AmbientIntent) -> None:
        self.selection = self.orientation.select(
            now,
            intent.sprite,
            intent=intent.body,
            side=intent.side,
        )
        if self.selection.animation == "idle":
            self.selection = SpriteSelection("rest-neutral", intent.sprite.fixed_frame)

    @property
    def gaze(self) -> tuple[float, float] | None:
        selection = self.selection
        sector = selection.fixed_frame
        if sector is None:
            return None
        if selection.animation == "body-look-left":
            sector = sector + 7 if sector else 0
        elif selection.animation not in ("look", "body-look-right"):
            return None
        angle = sector * math.pi / 8
        return math.sin(angle), math.cos(angle)
