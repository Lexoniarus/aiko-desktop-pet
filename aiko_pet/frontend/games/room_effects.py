"""Cancellable room presentation for the existing game timelines and artwork.

Only public cards/code and cosmetic props are projected. No game rules, World
objects, food consumption or pet rewards are owned by this adapter.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ...application.room_contracts import json_value
from ...games.connect_four import Move
from ...games.playing_cards import Card
from ..room_playback import RoomPlayback
from .pacing import GAME_PACING
from .ports import GamePresentation


class RoomGameEffects:
    def __init__(self, playback: RoomPlayback) -> None:
        self.playback = playback
        self._timers: set[str] = set()
        self._closed = False
        self._sequence = 0
        self._motion: dict[str, Any] | None = None
        self._started = 0.0
        self.held_item: str | None = None
        self.safe_frame = 0
        self.snack = False
        self.presentation = GamePresentation(
            action=playback.game_action,
            cancel=playback.stop_animation,
            look=lambda _point: None,
        )

    def later(self, milliseconds: int, done: Callable[[], None]) -> None:
        token = ""

        def run() -> None:
            self._timers.discard(token)
            if not self._closed:
                done()

        token = self.playback.schedule(milliseconds, run)
        self._timers.add(token)

    def motion(self, kind: str, duration: int, **data: Any) -> None:
        self._sequence += 1
        self._started = self.playback.now
        self._motion = dict(id=self._sequence, kind=kind, duration=duration, **data)

    def card(
        self, kind: str, card: Card | None, index: int, done: Callable[[], None]
    ) -> None:
        duration = (
            GAME_PACING.card_flight_ms
            if kind in ("player", "dealer")
            else GAME_PACING.card_gather_ms
            if kind == "gather"
            else GAME_PACING.card_shuffle_ms
        )
        self.motion(kind, duration, card=json_value(card), index=index)
        if kind == "shuffle":
            self.playback.game_action("attack", duration, lambda _: None, lambda: None)

        def landed() -> None:
            self._motion = None
            done()

        self.later(duration, landed)

    def throw(self, move: Move, done: Callable[[], None]) -> None:
        def release() -> None:
            self.held_item = None
            self.motion("chip", 1490, cell=move.cell, flight_duration=1240)

            def landed() -> None:
                self._motion = None
                done()

            self.later(1490, landed)

        def marker(index: int) -> None:
            if index == 3:
                self.held_item = "c4-red"
            if index == 5:
                self.later(30, release)

        self.playback.game_action(
            "pick_up", (180, 120, 120, 130, 110, 140, 140, 220), marker, lambda: None
        )

    def finale(self, _won: bool, done: Callable[[], None]) -> None:
        def opening(index: int) -> None:
            self.safe_frame = index
            self.snack = index == 32
            if index < 32:
                self.later(
                    round((index + 1) * 1560 / 32) - round(index * 1560 / 32),
                    lambda: opening(index + 1),
                )
            else:
                self.later(500, eat)

        def eat() -> None:
            self.snack = False
            self.held_item = "mm-donut"

            def complete() -> None:
                self.held_item = None
                done()

            self.playback.game_action("eat", None, lambda _: None, complete)

        opening(0)

    def snapshot(self) -> dict[str, Any]:
        motion = None
        if self._motion is not None:
            motion = {
                **self._motion,
                "fraction": min(
                    1.0,
                    (self.playback.now - self._started)
                    * 1000
                    / self._motion["duration"],
                ),
            }
        return dict(motion=motion, safe_frame=self.safe_frame, snack=self.snack)

    def close(self) -> None:
        self._closed = True
        for token in self._timers:
            self.playback.cancel_timer(token)
        self._timers.clear()
        self._motion = None
        self.held_item = None
        self.playback.stop_animation()
