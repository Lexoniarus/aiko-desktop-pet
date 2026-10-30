"""Fingerduell: actual arm markers own countdown and exactly-once reveal."""

from __future__ import annotations

from collections.abc import Callable
from uuid import uuid4

from ...games.contracts import GameId, GameRoundEvent
from ...games.rock_paper_scissors import Move, Outcome, RockPaperScissors, Round, Score
from ..common.game_pacing import GAME_PACING
from .game_presentation import GamePresentation
from .rock_paper_scissors_dialogue import GameDialogue, countdown_line, outcome_event


class RockPaperScissorsSequence:
    CYCLE_MS = 900
    REACTION_EMOTE_MS = GAME_PACING.emote_ms

    def __init__(
        self, *, schedule: Callable[[int, Callable[[], None]], str],
        cancel: Callable[[str], None], say: Callable[[str, int], None],
        show_emote: Callable[[str, int], None],
        show_aiko_hand: Callable[[Move, int], None],
        reveal_player: Callable[[Move, Score], None],
        animate: Callable[[str], None], set_busy: Callable[[bool], None],
        dialogue: Callable[[str], str] | None = None,
        round_event: Callable[[GameRoundEvent], None] = lambda _: None,
        express_event: Callable[[str], None] = lambda _: None,
        presentation: GamePresentation | None = None,
        clear_hand: Callable[[], None] = lambda: None,
    ) -> None:
        self._schedule, self._cancel = schedule, cancel
        self._say, self._show_emote = say, show_emote
        self._show_aiko_hand, self._reveal_player = show_aiko_hand, reveal_player
        self._animate, self._set_busy = animate, set_busy
        self._dialogue = dialogue or GameDialogue().choose
        self._round_event, self._express_event = round_event, express_event
        self._presentation, self._clear_hand = presentation, clear_hand
        self._game = RockPaperScissors()
        self._session_id = uuid4().hex
        self._timer: str | None = None
        self._next: Callable[[], None] | None = None
        self._generation = 0
        self._closed = False
        self._result: Round | None = None

    @property
    def score(self) -> Score:
        return self._game.score

    @property
    def busy(self) -> bool:
        return self._game.pending

    @property
    def pending_timer(self) -> str | None:
        return self._timer

    def _invalidate(self) -> int:
        self._generation += 1
        self._next = None
        if self._timer is not None:
            self._cancel(self._timer)
            self._timer = None
        if self._presentation is not None:
            self._presentation.cancel()
            self._presentation.look(None)
        return self._generation

    def _later(self, ms: int, callback: Callable[[], None], generation: int) -> None:
        def run() -> None:
            if not self._closed and generation == self._generation:
                self._timer = None
                self._next = None
                callback()
        self._next = run
        self._timer = self._schedule(ms, run)

    def greet(self) -> None:
        if not self._closed and not self.busy:
            self._animate("waving-greeting")
            phrase = self._dialogue("game_greeting")
            self._express_event("game_greeting")
            self._say(phrase, GAME_PACING.text_ms(phrase))

    def choose(self, move: Move) -> None:
        if self._closed or self.busy:
            return
        generation = self._invalidate()
        self._clear_hand()
        self._result = None
        self._game.begin(move)
        self._round_event(GameRoundEvent(
            GameId.ROCK_PAPER_SCISSORS, self._session_id, self.score.games + 1,
        ))
        self._set_busy(True)
        self._cycle(1, generation)

    def _cycle(self, number: int, generation: int) -> None:
        def marker(index: int) -> None:
            if self._closed or generation != self._generation or index != 4:
                return
            self._say(countdown_line(number), self.CYCLE_MS)
            if number == 3 and self._game.pending:
                result = self._game.reveal()
                self._result = result
                self._round_event(GameRoundEvent(
                    GameId.ROCK_PAPER_SCISSORS, self._session_id, self.score.games,
                    result.outcome.value, result.details,
                ))
                self._reveal_player(result.player, self.score)
                self._show_aiko_hand(result.aiko, 0)
                self._set_busy(False)

        def done() -> None:
            if self._closed or generation != self._generation:
                return
            if number < 3:
                self._cycle(number + 1, generation)
            else:
                self._react(generation)

        if self._presentation is not None:
            self._presentation.action("attack", self.CYCLE_MS, marker, done)
        else:
            # Standalone view/test adapter has no character, only phase deadlines.
            def forward() -> None:
                marker(4)
                self._later(450, done, generation)
            self._later(450, forward, generation)

    def _react(self, generation: int) -> None:
        result = self._result
        if result is None:
            return
        if result.outcome is Outcome.LOSS:
            self._animate("jumping")
        emote = {Outcome.WIN: "drops", Outcome.LOSS: "star",
                 Outcome.DRAW: "question"}[result.outcome]
        self._show_emote(emote, self.REACTION_EMOTE_MS)

        def speak() -> None:
            phrase = self._dialogue(outcome_event(result))
            self._express_event(outcome_event(result))
            self._say(phrase, GAME_PACING.text_ms(phrase))

        self._later(self.REACTION_EMOTE_MS, speak, generation)

    def advance(self) -> None:
        """Advance only the optional character-free adapter's current callback."""
        callback = self._next
        if callback is not None:
            if self._timer is not None:
                self._cancel(self._timer)
            callback()

    def close(self) -> None:
        if not self._closed:
            self._closed = True
            self._invalidate()
            self._game.cancel()
            self._clear_hand()
