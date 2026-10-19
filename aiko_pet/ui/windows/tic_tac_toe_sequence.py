"""Cancellable turn pacing; board truth belongs to the game session."""

from __future__ import annotations

from collections.abc import Callable

from ...games.contracts import SessionSummary
from ...games.tic_tac_toe import Board, TicTacToe
from .rock_paper_scissors_dialogue import GameDialogue


class TicTacToeSequence:
    def __init__(
        self, *, schedule: Callable[[int, Callable[[], None]], str],
        cancel: Callable[[str], None], present: Callable[[Board, SessionSummary], None],
        say: Callable[[str, int], None], animate: Callable[[str], None],
        dialogue: Callable[[str], str] | None = None,
        game: TicTacToe | None = None,
    ) -> None:
        self.game = game if game is not None else TicTacToe()
        self._schedule, self._cancel = schedule, cancel
        self._present, self._say, self._animate = present, say, animate
        self._dialogue = dialogue if dialogue is not None else GameDialogue().choose
        self.pending_timer: str | None = None
        self._closed = False

    def greet(self) -> None:
        self._say(self._dialogue("game_ttt_greeting"), 2800)
        self._present(self.game.board, self.game.score)

    def choose(self, cell: int) -> None:
        if self._closed or self.pending_timer is not None:
            return
        self.game.play(cell)
        self._after_move()

    def _after_move(self) -> None:
        board = self.game.board
        if board.winner is not None:
            self.game.settle()
            event = {
                "X": "game_round_player_win", "O": "game_round_aiko_win",
                "": "game_round_draw",
            }
            self._animate({"X": "failed", "O": "jumping", "": "waving"}[board.winner])
            self._say(self._dialogue(event[board.winner]), 2800)
        elif board.turn == "O":
            self.pending_timer = self._schedule(650, self.advance)
        self._present(board, self.game.score)

    def advance(self) -> None:
        if self._closed or self.pending_timer is None:
            return
        self._cancel(self.pending_timer)
        self.pending_timer = None
        self.game.aiko_move()
        self._after_move()

    def next_round(self) -> None:
        if not self._closed:
            self.game.next_round()
            self._after_move()

    def close(self) -> SessionSummary:
        if not self._closed:
            self._closed = True
            if self.pending_timer is not None:
                self._cancel(self.pending_timer)
                self.pending_timer = None
            self.game.cancel()
        return self.game.score
