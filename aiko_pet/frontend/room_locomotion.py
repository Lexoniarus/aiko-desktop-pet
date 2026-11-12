"""Start room travel and present the stationary turns and gaze poses."""

from __future__ import annotations

import math

from ..pet.animation.ambient import AmbientIntent
from ..pet.animation.animation import SpriteSelection
from ..pet.animation.body_orientation import BodyOrientation
from ..world.room import RoomPoint

ROOM_WALK_ANIMATION = "room-walk"


class RoomLocomotion:
    # The native step covers 16 logical pixels in 620 ms. Room artwork displays
    # the 156-logical-pixel visible figure at 100 room units, without skating.
    speed = 16 / 0.62 * 100 / 156

    def __init__(self) -> None:
        self.orientation = BodyOrientation()
        self.selection = SpriteSelection("rest-neutral")

    def walk(self, now: float, start: RoomPoint, end: RoomPoint) -> bool:
        if self.selection.animation == ROOM_WALK_ANIMATION:
            return True
        if start.x != end.x:
            side = 1 if end.x > start.x else -1
            if self.orientation.side not in (0, side):
                self.orientation.reset()
            turn = self.orientation.orient_for_motion(now, side, responsive=True)
            if not self.orientation.motion_ready:
                self.selection = turn
                return False
        else:
            self.orientation.reset()
        # The camera chooses the clip from the direction of the displayed segment.
        self.selection = SpriteSelection(ROOM_WALK_ANIMATION)
        return True

    def stop_walk(self) -> None:
        if (
            self.selection.animation == ROOM_WALK_ANIMATION
            or self.selection.animation.startswith("body-orient-")
        ):
            self.orientation.reset()
            self.selection = SpriteSelection("rest-neutral")

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

    def idle(
        self, now: float, intent: AmbientIntent, *, face_player: bool = False,
    ) -> None:
        if face_player:
            self.orientation.reset()
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
