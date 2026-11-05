"""Quiet room outings and native idle poses, without care or object ownership."""

from __future__ import annotations

import math
import random

from ..pet.animation.ambient import AmbientDirector
from ..pet.state import PetState
from ..world.room import RoomGeometry, RoomPoint
from .room_locomotion import RoomLocomotion


class RoomLeisure:
    def __init__(self, rng: random.Random, *, rest_cycle: float) -> None:
        self.rng, self.rest_cycle = rng, rest_cycle
        self.director = AmbientDirector(
            0,
            between=rng.uniform,
            direction=rng.choice,
            body_poses=True,
        )
        self.next_outing = 10.0
        self._blink_until: float | None = None

    def destination(self, now: float, position: RoomPoint) -> RoomPoint | None:
        if now < self.next_outing:
            return None
        candidates = [
            anchor.position
            for anchor in RoomGeometry.anchors
            if abs(RoomGeometry.delta(position.x, anchor.position.x)) >= 160
        ]
        if not candidates:
            return None
        nearby = sorted(
            candidates, key=lambda point: abs(RoomGeometry.delta(position.x, point.x))
        )[:3]
        target = RoomGeometry.accessible(self.rng.choice(nearby))
        distance = RoomGeometry.delta(position.x, target.x)
        if abs(distance) > 650:
            distance = math.copysign(self.rng.uniform(400, 650), distance)
            target = RoomPoint(
                (position.x + distance) % RoomGeometry.width, target.depth
            )
        self.next_outing = float("inf")
        return target

    def arrived(self, now: float, side: int) -> None:
        self.next_outing = now + self.rng.uniform(25, 50)
        self.director.finish_outing(now, side)

    def suspend(self, now: float, *, cancel_outing: bool = False) -> None:
        self.director.suspend(now)
        self._blink_until = None
        if cancel_outing:
            self.next_outing = now + self.rng.uniform(20, 45)

    def pose(self, now: float, state: PetState, locomotion: RoomLocomotion) -> None:
        if self._blink_until is not None and now >= self._blink_until:
            self.director.finish_blink(now)
            self._blink_until = None
        intent = self.director.select_passive_animation(
            now,
            gaze_direction=None,
            observing_computer=False,
            computer_busy=False,
            energy=state.energy,
            mood=state.mood,
            satiety=state.satiety,
        )
        if self.director.blinking and self._blink_until is None:
            self._blink_until = now + self.rest_cycle
        locomotion.idle(now, intent)
        if intent.side and locomotion.orientation.phase == 4:
            self.director.note_body_settled(now, intent.side)
