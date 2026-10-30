"""Cancellable turn pacing; board truth belongs to the game session."""

from __future__ import annotations

from collections.abc import Callable
from uuid import uuid4

from ...games.contracts import GameId, GameRoundEvent, SessionSummary
from ...games.tic_tac_toe import Board, TicTacToe
from ...games.tic_tac_toe_analysis import read_board
from .game_commentary import GameCommentary
from .rock_paper_scissors_dialogue import GameDialogue


class TicTacToeSequence:
    def __init__(
        self, *, schedule: Callable[[int, Callable[[], None]], str],
        cancel: Callable[[str], None], present: Callable[[Board, SessionSummary], None],
        say: Callable[[str, int], None], animate: Callable[[str], None],
        dialogue: Callable[[str], str] | None = None,
        round_event: Callable[[GameRoundEvent], None] = lambda _event: None,
        express_event: Callable[[str], None] = lambda _event: None,
        game: TicTacToe | None = None,
        emote: Callable[[str, int], None] = lambda *_: None,
        look: Callable[[int | None], None] = lambda _: None,
    ) -> None:
        self.game = game if game is not None else TicTacToe()
        self._schedule, self._cancel = schedule, cancel
        self._present, self._say, self._animate = present, say, animate
        self._dialogue = dialogue if dialogue is not None else GameDialogue().choose
        self.pending_timer: str | None = None
        self._closed = False
        self._session_id = uuid4().hex
        self._round_event = round_event
        self._express_event = express_event
        self._look = look
        self._commentary = GameCommentary(
            schedule=schedule, cancel=cancel, say=say, emote=emote,
            dialogue=self._dialogue, express=express_event,
        )

    def greet(self) -> None:
        self._round_event(GameRoundEvent(
            GameId.TIC_TAC_TOE, self._session_id, self.game.score.games + 1,
        ))
        text = self._dialogue("game_ttt_greeting")
        self._express_event("game_ttt_greeting")
        self._say(text, 2800)
        self._present(self.game.board, self.game.score)

    def choose(self, cell: int) -> None:
        if self._closed or self.pending_timer is not None:
            return
        self._commentary.cancel()
        self.game.play(cell)
        self._after_move()

    def _after_move(self) -> None:
        board = self.game.board
        if board.winner is not None:
            self.game.settle()
            self._round_event(GameRoundEvent(
                GameId.TIC_TAC_TOE, self._session_id, self.game.score.games,
                "win" if board.winner == "X" else
                "loss" if board.winner == "O" else "draw",
            ))
            event = {
                "X": "game_ttt_player_win", "O": "game_ttt_aiko_win",
                "": "game_ttt_draw",
            }
            if board.winner == "O":
                self._animate("jumping")
            self._look(None)
            self._commentary.event(event[board.winner], "question" if
                                   board.winner == "" else "star" if
                                   board.winner == "O" else "drops")
        elif board.turn == "O":
            reading = read_board(board)
            self._look(reading.target)
            self._commentary.event(reading.event)
            self.pending_timer = self._schedule(1400, self.advance)
        self._present(board, self.game.score)

    def advance(self) -> None:
        if self._closed or self.pending_timer is None:
            return
        self._cancel(self.pending_timer)
        self.pending_timer = None
        before = self.game.board
        self.game.aiko_move()
        self._after_move()
        if self.game.board.winner is None:
            reading = read_board(self.game.board, before)
            self._look(reading.target)
            self._commentary.event(reading.event, "drops" if
                                   reading.event == "game_ttt_mistake" else "question")
            self._commentary.later(1800, lambda: self._look(None))

    def next_round(self) -> None:
        if not self._closed:
            self._commentary.cancel()
            self.game.next_round()
            self._round_event(GameRoundEvent(
                GameId.TIC_TAC_TOE, self._session_id, self.game.score.games + 1,
            ))
            self._after_move()

    def close(self) -> SessionSummary:
        if not self._closed:
            self._closed = True
            self._commentary.cancel()
            self._look(None)
            if self.pending_timer is not None:
                self._cancel(self.pending_timer)
                self.pending_timer = None
            self.game.cancel()
        return self.game.score
