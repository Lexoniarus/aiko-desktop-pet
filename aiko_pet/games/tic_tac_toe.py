"""One transient board session and a deliberately small local opponent."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from secrets import randbelow

from .contracts import GameId, SessionSummary

LINES = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6),
)


@dataclass(frozen=True, slots=True)
class Board:
    cells: tuple[str, ...]
    turn: str
    winner: str | None = None  # X, O, or empty string for a draw.
    winning_line: tuple[int, ...] = ()


class TicTacToe:
    def __init__(self, *, random_index: Callable[[int], int] = randbelow) -> None:
        self._random_index = random_index
        self._starter = "X"
        self._board = Board(("",) * 9, "X")
        self._score = SessionSummary(GameId.TIC_TAC_TOE)
        self._settled = False
        self._closed = False

    @property
    def board(self) -> Board:
        return self._board

    @property
    def score(self) -> SessionSummary:
        return self._score

    def play(self, cell: int, mark: str = "X") -> None:
        board = self._board
        if (self._closed or board.winner is not None or mark != board.turn
                or type(cell) is not int or not 0 <= cell < 9 or board.cells[cell]):
            raise ValueError("Move is not legal")
        cells = list(board.cells)
        cells[cell] = mark
        line = next((line for line in LINES if all(cells[i] == mark for i in line)), ())
        winner = mark if line else ("" if all(cells) else None)
        self._board = Board(tuple(cells), "O" if mark == "X" else "X", winner, line)

    def aiko_move(self) -> None:
        board = self._board
        if self._closed or board.turn != "O" or board.winner is not None:
            raise ValueError("Not Aiko's turn")
        empty = tuple(i for i, value in enumerate(board.cells) if not value)
        for mark in ("O", "X"):
            moves = tuple(i for i in empty if any(
                i in line and all(j == i or board.cells[j] == mark for j in line)
                for line in LINES
            ))
            if moves:
                self.play(self._choose(moves), "O")
                return
        for preferred in ((4,), (0, 2, 6, 8), (1, 3, 5, 7)):
            moves = tuple(i for i in preferred if i in empty)
            if moves:
                self.play(self._choose(moves), "O")
                return

    def _choose(self, moves: tuple[int, ...]) -> int:
        index = self._random_index(len(moves))
        if not 0 <= index < len(moves):
            raise ValueError("Invalid random choice")
        return moves[index]

    def settle(self) -> None:
        if self._closed or self._settled or self._board.winner is None:
            raise ValueError("No new result to settle")
        winner = self._board.winner
        self._score = replace(
            self._score, wins=self._score.wins + (winner == "X"),
            losses=self._score.losses + (winner == "O"),
            draws=self._score.draws + (winner == ""),
        )
        self._settled = True

    def next_round(self) -> None:
        if self._closed or not self._settled:
            raise ValueError("Finish the current round first")
        self._starter = "O" if self._starter == "X" else "X"
        self._board = Board(("",) * 9, self._starter)
        self._settled = False

    def cancel(self) -> None:
        self._closed = True
