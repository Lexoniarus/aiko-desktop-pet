"""Interruptible game comments; never acquire a gameplay input lock."""

from collections.abc import Callable

from ..common.game_pacing import GAME_PACING


class GameCommentary:
    def __init__(
        self, *, schedule: Callable[[int, Callable[[], None]], str],
        cancel: Callable[[str], None], say: Callable[[str, int], None],
        emote: Callable[[str, int], None], dialogue: Callable[[str], str],
        express: Callable[[str], None],
    ) -> None:
        self._schedule, self._cancel = schedule, cancel
        self._say, self._emote = say, emote
        self._dialogue, self._express = dialogue, express
        self._generation = 0
        self._timers: list[str] = []
        self.active = False

    def cancel(self) -> None:
        self.active = False
        self._generation += 1
        for timer in self._timers:
            self._cancel(timer)
        self._timers.clear()

    def later(self, ms: int, action: Callable[[], None]) -> None:
        generation = self._generation

        def run() -> None:
            if generation == self._generation:
                action()
        self._timers.append(self._schedule(ms, run))

    def event(self, event: str, emote: str | None = None) -> int:
        self.cancel()
        self.active = True
        text = self._dialogue(event)
        duration = GAME_PACING.text_ms(text)
        self._express(event)
        self._say(text, duration)
        if emote:
            def show() -> None:
                self._emote(emote, GAME_PACING.emote_ms)
                self.later(GAME_PACING.emote_ms, lambda: self._say(text, duration))
            self.later(duration, show)
        return duration
