"""Schedule Aiko's character-led Rock–Paper–Scissors reaction beats.

The player hand and transient counters belong to the input panel. Aiko's own
hand, emotes and outcome reaction belong to the established character bubble.
No Tk dependency lives here, and every pending cue is cancellable.
"""

from __future__ import annotations

from collections.abc import Callable

from ..games.rock_paper_scissors import (
    Move, Outcome, RockPaperScissors, Round, Score,
)
from .rock_paper_scissors_text_de import (
    countdown_line, outcome_line, welcome_line,
)

ScheduleTimer = Callable[[int, Callable[[], None]], str]
CancelTimer = Callable[[str], None]
DisplayText = Callable[[str, int], None]
DisplayEmote = Callable[[str, int], None]
DisplayAikoHand = Callable[[Move, int], None]
RevealPlayer = Callable[[Move, Score], None]
PlayAnimation = Callable[[str], None]
SetBusy = Callable[[bool], None]

_REACTION_ASSETS: dict[Outcome, tuple[str, str]] = {
    Outcome.WIN: ("failed", "drops"),
    Outcome.LOSS: ("jumping", "star"),
    Outcome.DRAW: ("waving", "question"),
}


class RockPaperScissorsSequence:
    """Own the 1→2→3→reveal→emote→result timeline and its cancellation."""

    COUNT_MS = 800
    EXCITEMENT_MS = 700
    HAND_MS = 2300
    REACTION_EMOTE_MS = 850
    REACTION_MS = 2800

    def __init__(
        self, *, schedule: ScheduleTimer, cancel: CancelTimer,
        say: DisplayText, show_emote: DisplayEmote,
        show_aiko_hand: DisplayAikoHand,
        reveal_player: RevealPlayer,
        animate: PlayAnimation, set_busy: SetBusy,
    ) -> None:
        self._schedule = schedule
        self._cancel = cancel
        self._say = say
        self._show_emote = show_emote
        self._show_aiko_hand = show_aiko_hand
        self._reveal_player = reveal_player
        self._animate = animate
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
            self._animate("waving")
            self._say(welcome_line(self.score.games), 4300)

    def choose(self, move: Move) -> None:
        if self._closed or self.busy:
            return
        self._game.begin(move)
        self._set_busy(True)
        self._phase = 1
        self._emit_text(countdown_line(1), self.COUNT_MS)

    def _emit_text(self, phrase: str, duration_ms: int) -> None:
        self._say(phrase, duration_ms)
        self._timer = self._schedule(duration_ms, self.advance)

    def _emit_emote(self, name: str, duration_ms: int) -> None:
        self._show_emote(name, duration_ms)
        self._timer = self._schedule(duration_ms, self.advance)

    def advance(self) -> None:
        if self._timer is not None:
            self._cancel(self._timer)
            self._timer = None
        if self._closed:
            return
        if self._phase == 1:
            self._phase = 2
            self._emit_text(countdown_line(2), self.COUNT_MS)
        elif self._phase == 2:
            self._phase = 3
            self._emit_text(countdown_line(3), self.COUNT_MS)
        elif self._phase == 3:
            self._phase = 4
            self._emit_emote("exclamation", self.EXCITEMENT_MS)
        elif self._phase == 4:
            result = self._game.reveal()
            self._result = result
            self._phase = 5
            # Both views reveal at the same instant, in their own owners.
            self._reveal_player(result.player, self._game.score)
            self._show_aiko_hand(result.aiko, self.HAND_MS)
            self._timer = self._schedule(self.HAND_MS, self.advance)
        elif self._phase == 5 and self._result is not None:
            self._phase = 6
            clip, emote = _REACTION_ASSETS[self._result.outcome]
            self._animate(clip)
            self._emit_emote(emote, self.REACTION_EMOTE_MS)
        elif self._phase == 6 and self._result is not None:
            self._phase = 7
            self._emit_text(
                outcome_line(self._result, self.score.games),
                self.REACTION_MS,
            )
        elif self._phase == 7:
            self._phase = 0
            self._result = None
            self._set_busy(False)

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        if self._timer is not None:
            self._cancel(self._timer)
            self._timer = None
        self._game.cancel()
        self._phase = 0
        self._result = None
