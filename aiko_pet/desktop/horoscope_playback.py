"""Read a frozen entry while the object interaction owns Aiko's hands."""

import logging
from dataclasses import replace
from typing import Callable

from ..application.horoscope_coordinator import HoroscopeCoordinator
from ..ui.pet_view.reaction_player import ReactionPlayer


class HoroscopePlayback:
    def __init__(
        self,
        content: HoroscopeCoordinator,
        player: ReactionPlayer,
        pose: Callable[[str], None],
        *,
        schedule: Callable[[int, Callable[[], None]], str],
        cancel_timer: Callable[[str], None],
        unavailable: Callable[[], None] = lambda: None,
    ) -> None:
        self._content, self._player, self._pose = content, player, pose
        self._schedule, self._cancel_timer = schedule, cancel_timer
        self._unavailable = unavailable
        self._book: str | None = None
        self._timer: str | None = None
        self._finished: Callable[[bool], None] | None = None
        self._generation = 0

    @property
    def active(self) -> bool:
        return self._book is not None

    def _finish(self, success: bool) -> None:
        self._generation += 1
        if self._timer is not None:
            self._cancel_timer(self._timer)
            self._timer = None
        self._book = None
        finished, self._finished = self._finished, None
        self._pose("carry_closed")
        if finished is not None:
            finished(success)

    def stop(self) -> None:
        if self.active:
            self._content.pause()
            self._player.cancel()
            if self.active:
                self._finish(False)

    def expire(self, book: str) -> None:
        if self._book == book:
            self.stop()

    def start(self, book: str, finished: Callable[[bool], None]) -> bool:
        if self.active:
            return False
        try:
            day = self._content.start(book)
        except (ImportError, OSError, ValueError, ArithmeticError):
            logging.getLogger(__name__).warning(
                "Local book reading unavailable", exc_info=True
            )
            self._unavailable()
            return False
        if day is None or day.reading is None:
            self._unavailable()
            return False
        offset, generation = day.index, self._content.generation
        reaction = replace(
            day.reading.reaction, beats=day.reading.reaction.beats[offset:]
        )
        self._player.cancel()
        self._book, self._finished = book, finished
        self._generation += 1
        visual_generation = self._generation
        self._pose("half_open")

        def complete(success: bool) -> None:
            if visual_generation != self._generation:
                return
            if not success:
                self._finish(False)
                return
            self._pose("half_open")
            self._timer = self._schedule(300, lambda: self._finish(True))

        def read() -> None:
            self._timer = None
            if visual_generation != self._generation:
                return
            self._pose("open_reading")
            self._player.play(
                reaction,
                animate=False,
                on_progress=lambda index: self._content.advance(
                    book, generation, offset + index
                ),
                on_complete=complete,
            )

        self._timer = self._schedule(300, read)
        return True
