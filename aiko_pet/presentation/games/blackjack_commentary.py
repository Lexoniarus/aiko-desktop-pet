"""Bounded, interruptible casino speech with no game-continuation callbacks."""
from collections import deque
from collections.abc import Callable

from .pacing import GAME_PACING


class BlackjackCommentary:
    def __init__(
        self, *, schedule: Callable[[int, Callable[[], None]], str],
        cancel: Callable[[str], None], say: Callable[[str, int], None],
        emote: Callable[[str, int], None], express: Callable[[str], None],
        silence: Callable[[], None],
    ) -> None:
        self._schedule, self._cancel = schedule, cancel
        self._say, self._emote, self._express = say, emote, express
        self._silence = silence
        self._pending: deque[tuple[str, str, str | None]] = deque()
        self._timer: str | None = None
        self._generation = 0
        self.active = False

    def clear_pending(self) -> None:
        """A new hand discards unheard old cues but lets the current line finish."""
        self._pending.clear()

    def cue(self, event: str, text: str) -> None:
        self._pending.append((event, text, None))
        if not self.active:
            self._next()

    def result(self, event: str, text: str, aside: str) -> None:
        # Only the current cue plus this outcome may remain; no old reveal backlog.
        self._pending.clear()
        self._pending.extend(((event, text, None), ('game_bj_aside', aside, 'star')))
        if not self.active:
            self._next()

    def _later(self, ms: int, done: Callable[[], None]) -> None:
        generation = self._generation
        token = ''

        def run() -> None:
            if generation != self._generation or self._timer != token:
                return
            self._timer = None
            done()
        token = self._schedule(ms, run)
        self._timer = token

    def _next(self) -> None:
        self.active = bool(self._pending)
        if not self._pending:
            return
        event, text, emote = self._pending.popleft()
        self._express(event)
        duration = GAME_PACING.comment_text_ms(text)
        self._say(text, duration)

        def finish() -> None:
            if emote is None:
                self._next()
            else:
                self._emote(emote, GAME_PACING.emote_ms)
                self._later(GAME_PACING.emote_ms, self._next)
        self._later(duration, finish)

    def interrupt(self) -> None:
        self._generation += 1
        if self._timer is not None:
            self._cancel(self._timer)
            self._timer = None
        self._pending.clear()
        self.active = False
        self._silence()
