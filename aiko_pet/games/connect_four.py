"""Transient Connect Four rules and a bounded, cancellable local opponent."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from secrets import randbelow
from threading import Event

from .contracts import GameId, SessionSummary

ROWS, COLUMNS = 6, 7
SEARCH_DEPTH = 4
SEARCH_NODE_LIMIT = 5000
ORDER = (3, 2, 4, 1, 5, 0, 6)
WINDOWS = tuple(
    tuple((row + step * dr) * COLUMNS + column + step * dc for step in range(4))
    for row in range(ROWS)
    for column in range(COLUMNS)
    for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1))
    if 0 <= row + 3 * dr < ROWS and 0 <= column + 3 * dc < COLUMNS
)


@dataclass(frozen=True, slots=True)
class Board:
    cells: tuple[int, ...] = (0,) * (ROWS * COLUMNS)
    turn: int = 1
    winner: int | None = None  # 1 player, 2 Aiko, 0 draw.
    winning_cells: tuple[int, ...] = ()

    @property
    def legal_columns(self) -> tuple[int, ...]:
        return tuple(c for c in ORDER if not self.cells[c])


@dataclass(frozen=True, slots=True)
class Move:
    cell: int
    player: int
    blocked_win: bool


def landing_cell(cells: tuple[int, ...], column: int) -> int | None:
    if type(column) is not int or not 0 <= column < COLUMNS:
        return None
    return next(
        (
            r * COLUMNS + column
            for r in range(ROWS - 1, -1, -1)
            if not cells[r * COLUMNS + column]
        ),
        None,
    )


def winning_cells(cells: tuple[int, ...], cell: int) -> tuple[int, ...]:
    player = cells[cell]
    found: set[int] = set()
    if player:
        for window in WINDOWS:
            if cell in window and all(cells[i] == player for i in window):
                found.update(window)
    return tuple(sorted(found))


def dropped(cells: tuple[int, ...], column: int, player: int) -> tuple[int, ...]:
    cell = landing_cell(cells, column)
    if cell is None:
        raise ValueError("Column is full or invalid")
    return cells[:cell] + (player,) + cells[cell + 1 :]


def winning_columns(cells: tuple[int, ...], player: int) -> tuple[int, ...]:
    return tuple(
        column
        for column in ORDER
        if (cell := landing_cell(cells, column)) is not None
        and winning_cells(dropped(cells, column, player), cell)
    )


def _evaluate(cells: tuple[int, ...]) -> int:
    score = 3 * sum(
        1 if cells[r * COLUMNS + 3] == 2 else -1 if cells[r * COLUMNS + 3] == 1 else 0
        for r in range(ROWS)
    )
    for window in WINDOWS:
        own = sum(cells[i] == 2 for i in window)
        other = sum(cells[i] == 1 for i in window)
        if not other:
            score += (0, 1, 7, 35, 10000)[own]
        if not own:
            score -= (0, 1, 8, 40, 10000)[other]
    return score


def choose_column(
    board: Board,
    cancelled: Event,
    *,
    random_index: Callable[[int], int] = randbelow,
) -> int:
    """Search only this immutable snapshot; never touch Tk or the live session."""
    if board.turn != 2 or board.winner is not None:
        raise ValueError("Not Aiko's turn")
    legal = board.legal_columns
    if not legal:
        raise ValueError("No legal move")
    wins = winning_columns(board.cells, 2)
    threats = winning_columns(board.cells, 1)
    safe = tuple(c for c in legal if not winning_columns(dropped(board.cells, c, 2), 1))
    candidates = wins or safe or threats or legal
    nodes = 0

    def search(
        cells: tuple[int, ...],
        turn: int,
        depth: int,
        alpha: int,
        beta: int,
        last_cell: int,
    ) -> int:
        nonlocal nodes
        nodes += 1
        if cancelled.is_set():
            raise InterruptedError("Opponent search cancelled")
        if winning_cells(cells, last_cell):
            return (100000 + depth) * (1 if cells[last_cell] == 2 else -1)
        columns = tuple(c for c in ORDER if not cells[c])
        if not columns:
            return 0
        if depth == 0 or nodes >= SEARCH_NODE_LIMIT:
            return _evaluate(cells)
        value = -1000000 if turn == 2 else 1000000
        for column in columns:
            cell = landing_cell(cells, column)
            assert cell is not None
            result = search(
                dropped(cells, column, turn), 3 - turn, depth - 1, alpha, beta, cell
            )
            if turn == 2:
                value = max(value, result)
                alpha = max(alpha, value)
            else:
                value = min(value, result)
                beta = min(beta, value)
            if beta <= alpha:
                break
        return value

    scores: dict[int, int] = {}
    for column in candidates:
        cell = landing_cell(board.cells, column)
        assert cell is not None
        scores[column] = search(
            dropped(board.cells, column, 2),
            1,
            SEARCH_DEPTH - 1,
            -1000000,
            1000000,
            cell,
        )
    best = max(scores.values())
    moves = tuple(c for c in candidates if scores[c] == best)
    index = random_index(len(moves))
    if not 0 <= index < len(moves):
        raise ValueError("Invalid random choice")
    return moves[index]


class ConnectFourSession:
    def __init__(self) -> None:
        self._board = Board()
        self._score = SessionSummary(GameId.CONNECT_FOUR)
        self._starter = 1
        self._settled = False
        self._closed = False

    @property
    def board(self) -> Board:
        return self._board

    @property
    def score(self) -> SessionSummary:
        return self._score

    def play(self, column: int, player: int = 1) -> Move:
        board = self._board
        if (
            self._closed
            or board.winner is not None
            or type(player) is not int
            or player != board.turn
        ):
            raise ValueError("Move is not legal")
        cell = landing_cell(board.cells, column)
        if cell is None:
            raise ValueError("Move is not legal")
        blocked = column in winning_columns(board.cells, 3 - player)
        cells = dropped(board.cells, column, player)
        line = winning_cells(cells, cell)
        winner = player if line else (0 if all(cells) else None)
        self._board = Board(cells, 3 - player, winner, line)
        return Move(cell, player, blocked)

    def settle(self) -> None:
        if self._closed or self._settled or self._board.winner is None:
            raise ValueError("No new result to settle")
        winner = self._board.winner
        self._score = replace(
            self._score,
            wins=self._score.wins + (winner == 1),
            losses=self._score.losses + (winner == 2),
            draws=self._score.draws + (winner == 0),
        )
        self._settled = True

    def next_round(self) -> None:
        if self._closed or not self._settled:
            raise ValueError("Finish the current round first")
        self._starter = 3 - self._starter
        self._board = Board(turn=self._starter)
        self._settled = False

    def cancel(self) -> None:
        self._closed = True
