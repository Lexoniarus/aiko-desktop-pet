"""Deterministic, sequential minigame dialogue without a UI dependency.

The entire interaction is one presentation timeline: Aiko speaks to the
existing character bubble, and the separate game view supplies only input.
"""

from __future__ import annotations

from typing import Callable

from ..games.rock_paper_scissors import (
    Move, RockPaperScissors, Round, Score,
)
from .rock_paper_scissors_text_de import (
    countdown_line, hands_line, outcome_line, score_line, welcome_line,
)

TimerCallback = Callable[[], None]
ScheduleTimer = Callable[[int, TimerCallback], str]
CancelTimer = Callable[[str], None]
Say = Callable[[str, int], None]
SetBusy = Callable[[bool], None]


class RockPaperScissorsSequence:
    """Own the 1→2→3→hands→reaction→score timeline and its cancellation."""

    COUNT_MS = 850
    HANDS_MS = 2300
    REACTION_MS = 2400
    SCORE_MS = 3300

    def __init__(
        self, *, schedule: ScheduleTimer, cancel: CancelTimer,
        say: Say, set_busy: SetBusy,
    ) -> None:
        self._schedule = schedule
        self._cancel = cancel
        self._say = say
        self._set_busy = set_busy
        self._game = RockPaperScissors()
        self._timer: str | None = None
        self._phase = 0
        self._result: Round | None = None
        self._closed = False

    @property
    def score(self) -> Score:
        return self._game.score

    @property
    def busy(self) -> bool:
        return self._phase != 0

    @property
    def pending_timer(self) -> str | None:
        return self._timer

    def greet(self) -> None:
        if not self._closed:
            self._say(welcome_line(), 4500)

    def choose(self, move: Move) -> None:
        """Freeze both hands; do not mutate the score until after 'Drei'."""
        if self._closed or self.busy:
            return
        self._game.begin(move)
        self._set_busy(True)
        self._phase = 1
        self._emit(countdown_line(1), self.COUNT_MS)

    def _emit(self, phrase: str, duration_ms: int) -> None:
        self._say(phrase, duration_ms)
        self._timer = self._schedule(duration_ms, self.advance)

    def advance(self) -> None:
        """Advance one and only one ordered speech cue."""
        if self._timer is not None:
            self._cancel(self._timer)
            self._timer = None
        if self._closed:
            return
        if self._phase == 1:
            self._phase = 2
            self._emit(countdown_line(2), self.COUNT_MS)
        elif self._phase == 2:
            self._phase = 3
            self._emit(countdown_line(3), self.COUNT_MS)
        elif self._phase == 3:
            self._result = self._game.reveal()
            self._phase = 4
            self._emit(hands_line(self._result), self.HANDS_MS)
        elif self._phase == 4 and self._result is not None:
            self._phase = 5
            self._emit(outcome_line(self._result), self.REACTION_MS)
        elif self._phase == 5:
            self._phase = 6
            self._emit(score_line(self._game.score), self.SCORE_MS)
        elif self._phase == 6:
            self._phase = 0
            self._result = None
            self._set_busy(False)

    def close(self) -> None:
        """Never let a queued game line speak after the player exits."""
        if self._closed:
            return
        self._closed = True
        if self._timer is not None:
            self._cancel(self._timer)
            self._timer = None
        self._game.cancel()
        self._phase = 0
        self._result = None
