"""Cancellable reveal/draw pacing for the separately owned game and views."""

from __future__ import annotations

from collections.abc import Callable

from ...games.blackjack import Blackjack, Phase, Table
from ...games.contracts import SessionSummary
from ..view_models.game_models import HandView, project_dealer_hand
from .rock_paper_scissors_dialogue import GameDialogue


class BlackjackSequence:
    RESULT_PAUSE_MS = 2800

    def __init__(
        self, *, schedule: Callable[[int, Callable[[], None]], str],
        cancel: Callable[[str], None], present: Callable[[Table, SessionSummary], None],
        hand: Callable[[HandView, bool], None], say: Callable[[str, int], None],
        animate: Callable[[str], None], dialogue: Callable[[str], str] | None = None,
        game: Blackjack | None = None,
    ) -> None:
        self.game = game if game is not None else Blackjack()
        self._schedule, self._cancel = schedule, cancel
        self._present, self._hand = present, hand
        self._say, self._animate = say, animate
        self._dialogue = dialogue if dialogue is not None else GameDialogue().choose
        self._closed = False
        self._revealing = False
        self.pending_timer: str | None = None

    def greet(self) -> None:
        if self._closed:
            return
        self._say(self._dialogue("game_blackjack_greeting"), 2800)
        self._publish()
        self._continue()

    def _publish(self, flip: bool = False) -> None:
        table = self.game.table
        self._hand(project_dealer_hand(table), flip)
        self._present(table, self.game.score)

    def hit(self) -> None:
        if (self._closed or self.pending_timer
                or self.game.table.phase is not Phase.PLAYER):
            return
        self.game.hit()
        self._publish()
        self._continue()

    def stand(self) -> None:
        if (self._closed or self.pending_timer
                or self.game.table.phase is not Phase.PLAYER):
            return
        self.game.stand()
        self._publish()
        self._continue()

    def _continue(self) -> None:
        if self.game.table.phase is not Phase.PLAYER:
            self._revealing = True
            self.pending_timer = self._schedule(500, self.advance)

    def advance(self) -> None:
        if self._closed or self.pending_timer is None:
            return
        self._cancel(self.pending_timer)
        self.pending_timer = None
        if self.game.table.result is not None:
            self.game.next_round()
            self._publish()
            self._continue()
            return
        if self._revealing:
            self._revealing = False
            self.game.reveal_dealer()
            self._publish(flip=True)
            self.pending_timer = self._schedule(550, self.advance)
            return
        if self.game.table.phase is Phase.DEALER:
            self.game.dealer_step()
        if self.game.table.phase is Phase.RESULT:
            self.game.settle()
            self._publish()
            result = self.game.table.result
            event = {
                "win": "game_round_player_win", "loss": "game_round_aiko_win",
                "draw": "game_round_draw",
            }
            assert result is not None
            clip = {"win": "failed", "loss": "jumping", "draw": "waving"}[result]
            self._animate(clip)
            self._say(self._dialogue(event[result]), self.RESULT_PAUSE_MS)
            self.pending_timer = self._schedule(self.RESULT_PAUSE_MS, self.advance)
        else:
            self._publish()
            self.pending_timer = self._schedule(600, self.advance)

    def close(self) -> SessionSummary:
        if not self._closed:
            self._closed = True
            if self.pending_timer is not None:
                self._cancel(self.pending_timer)
                self.pending_timer = None
            self._hand(HandView(), False)
            self.game.cancel()
        return self.game.score
