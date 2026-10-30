"""One cancellable turn/drop/reaction timeline; search runs away from Tk."""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import Executor, Future, ThreadPoolExecutor
from dataclasses import dataclass
from threading import Event
from uuid import uuid4

from ...games.connect_four import Board, ConnectFourSession, Move, choose_column
from ...games.contracts import GameId, GameRoundEvent, SessionSummary
from ..common.game_pacing import GAME_PACING
from .game_commentary import GameCommentary
from .rock_paper_scissors_dialogue import GameDialogue


@dataclass(frozen=True, slots=True)
class Drop:
    cell: int
    player: int
    fraction: float


class ConnectFourSequence:
    def __init__(
        self,
        *,
        schedule: Callable[[int, Callable[[], None]], str],
        cancel: Callable[[str], None],
        present: Callable[[Board, SessionSummary, bool, Drop | None], None],
        say: Callable[[str, int], None],
        animate: Callable[[str], None],
        emote: Callable[[str, int], None],
        dialogue: Callable[[str], str] | None = None,
        round_event: Callable[[GameRoundEvent], None] = lambda _event: None,
        express_event: Callable[[str], None] = lambda _event: None,
        game: ConnectFourSession | None = None,
        executor: Executor | None = None,
        throw: Callable[[Move, Callable[[], None]], None] | None = None,
        interrupt: Callable[[], None] = lambda: None,
        look: Callable[[int | None], None] = lambda _: None,
    ) -> None:
        self.game = game if game is not None else ConnectFourSession()
        self._express_event = express_event
        self._schedule, self._cancel, self._present = schedule, cancel, present
        self._say, self._animate, self._emote = say, animate, emote
        self._dialogue = dialogue if dialogue is not None else GameDialogue().choose
        self._round_event = round_event
        self._executor = executor or ThreadPoolExecutor(
            max_workers=1,
            thread_name_prefix="aiko-connect-four",
        )
        self._cancelled = Event()
        self._future: Future[int] | None = None
        self._session_id = uuid4().hex
        self._generation = 0
        self._closed = False
        self._started = False
        self._busy = True
        self._last_comment = -6
        self.pending_timer: str | None = None
        self._throw = throw
        self._interrupt, self._look = interrupt, look
        self._comments = GameCommentary(
            schedule=schedule, cancel=cancel, say=say, emote=emote,
            dialogue=self._dialogue, express=express_event,
        )

    @property
    def busy(self) -> bool:
        return self._busy

    def _show(self, drop: Drop | None = None) -> None:
        self._present(self.game.board, self.game.score, self._busy, drop)

    def _later(self, milliseconds: int, callback: Callable[[], None]) -> None:
        self._generation += 1
        if self.pending_timer is not None:
            self._cancel(self.pending_timer)
        generation = self._generation

        def run() -> None:
            if not self._closed and generation == self._generation:
                self.pending_timer = None
                callback()

        self.pending_timer = self._schedule(milliseconds, run)

    def _react(
        self,
        event: str,
        then: Callable[[], None],
        *,
        animation: str = "idle",
        emote: str | None = None,
    ) -> None:
        if self.game.board.turn == 1 and self.game.board.winner is None:
            self._comments.event(event, emote)
            self._ready()
            return
        self._busy = True
        self._show()
        self._animate(animation)
        text = self._dialogue(event)
        duration = GAME_PACING.text_ms(text)

        def speak() -> None:
            self._express_event(event)
            self._say(text, duration)
            self._later(duration, then)

        if emote is not None:
            self._emote(emote, GAME_PACING.emote_ms)
            self._later(GAME_PACING.emote_ms, speak)
        else:
            speak()

    def greet(self) -> None:
        if self._started or self._closed:
            return
        self._started = True
        self._begin_round()
        if self.game.board.turn == 1:
            # The welcome is presentation, not an unresolved player move.
            # Keep its reading time without discarding the player's first click.
            text = self._dialogue("game_c4_greeting")
            self._express_event("game_c4_greeting")
            self._say(text, GAME_PACING.text_ms(text))
            self._turn()
        else:
            self._react("game_c4_greeting", self._turn)

    def _begin_round(self) -> None:
        self._round_event(
            GameRoundEvent(
                GameId.CONNECT_FOUR,
                self._session_id,
                self.game.score.games + 1,
            )
        )

    def choose(self, column: int) -> None:
        if (
            self._closed
            or self._busy
            or self.game.board.turn != 1
            or type(column) is not int
            or column not in self.game.board.legal_columns
            or self.game.board.winner is not None
        ):
            return
        self._comments.cancel()
        self._interrupt()
        self._drop(self.game.play(column))

    def _drop(self, move: Move, frame: int = 0) -> None:
        self._busy = True
        if frame < 6:
            self._show(Drop(move.cell, move.player, frame / 6))
            self._later(30, lambda: self._drop(move, frame + 1))
            return
        self._show()
        if self.game.board.winner is not None:
            self.game.settle()
            winner = self.game.board.winner
            self._round_event(
                GameRoundEvent(
                    GameId.CONNECT_FOUR,
                    self._session_id,
                    self.game.score.games,
                    "win" if winner == 1 else "loss" if winner == 2 else "draw",
                )
            )
            self._react(
                {1: "game_c4_player_win", 2: "game_c4_aiko_win", 0: "game_c4_draw"}[
                    winner
                ],
                self._ready,
                animation="jumping"
                if winner == 2
                else "idle",
                emote="star" if winner == 2 else "faceSad" if winner == 1 else None,
            )
            return
        count = sum(value != 0 for value in self.game.board.cells)
        if move.blocked_win and count - self._last_comment >= 6:
            self._last_comment = count
            self._react(
                "game_c4_block" if move.player == 2 else "game_c4_blocked",
                self._turn,
                emote="idea" if move.player == 2 else "question",
            )
        else:
            self._turn()

    def _ready(self) -> None:
        self._busy = False
        self._animate("idle")
        self._show()

    def _turn(self) -> None:
        if self._closed:
            return
        if self.game.board.turn == 1:
            self._ready()
        else:
            self._busy = True
            self._look(24)
            self._show()
            self._future = self._executor.submit(
                choose_column,
                self.game.board,
                self._cancelled,
            )
            snapshot = self.game.board
            self._later(650, lambda: self._poll(snapshot))

    def _poll(self, snapshot: Board) -> None:
        future = self._future
        if self._closed or self.game.board is not snapshot or future is None:
            return
        if not future.done():
            self._later(20, lambda: self._poll(snapshot))
            return
        self._future = None
        column = future.result()
        move = self.game.play(column, 2)
        if self._throw is None:
            self._drop(move)
        else:
            self._show(Drop(move.cell, move.player, -1))
            self._throw(move, lambda: self._drop(move, 6) if not self._closed else None)

    def next_round(self) -> None:
        if self._closed or self._busy or self.game.board.winner is None:
            return
        self.game.next_round()
        self._last_comment = -6
        self._begin_round()
        self._turn()

    def close(self) -> SessionSummary:
        if not self._closed:
            self._closed = True
            self._comments.cancel()
            self._look(None)
            self._generation += 1
            self._cancelled.set()
            if self.pending_timer is not None:
                self._cancel(self.pending_timer)
                self.pending_timer = None
            if self._future is not None:
                self._future.cancel()
                self._future = None
            self._executor.shutdown(wait=False, cancel_futures=True)
            self.game.cancel()
        return self.game.score
