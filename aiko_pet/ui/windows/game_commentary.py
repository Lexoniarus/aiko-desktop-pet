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
        self._event: str | None = None
        self._duration = 0
        self._pending_emote: str | None = None
        self._text_showing = False

    def cancel(self) -> None:
        self.active = False
        self._event = None
        self._pending_emote = None
        self._text_showing = False
        self._generation += 1
        for timer in self._timers:
            self._cancel(timer)
        self._timers.clear()

    def later(self, ms: int, action: Callable[[], None]) -> None:
        generation = self._generation

        token = ""

        def run() -> None:
            if generation == self._generation and token in self._timers:
                self._timers.remove(token)
                action()
        token = self._schedule(ms, run)
        self._timers.append(token)

    def event(self, event: str, emote: str | None = None) -> int:
        if self.active and self._text_showing and self._event == event:
            self._pending_emote = emote or self._pending_emote
            return self._duration
        self.cancel()
        text = self._dialogue(event)
        duration = GAME_PACING.text_ms(text)
        self.active = self._text_showing = True
        self._event, self._duration, self._pending_emote = event, duration, emote
        self._express(event)
        self._say(text, duration)

        def finish() -> None:
            self.active = False

        def text_finished() -> None:
            self._text_showing = False
            if self._pending_emote is not None:
                self._emote(self._pending_emote, GAME_PACING.emote_ms)
                self.later(GAME_PACING.emote_ms, finish)
            else:
                finish()
        self.later(duration, text_finished)
        return duration
