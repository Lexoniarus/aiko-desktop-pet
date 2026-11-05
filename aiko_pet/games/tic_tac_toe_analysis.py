"""Read public board tactics for comments, independently of move selection."""

from dataclasses import dataclass
from functools import lru_cache

from .tic_tac_toe import LINES, Board


def winning_moves(cells: tuple[str, ...], mark: str) -> tuple[int, ...]:
    return tuple(i for i, value in enumerate(cells) if not value and any(
        i in line and all(j == i or cells[j] == mark for j in line) for line in LINES
    ))


@lru_cache(maxsize=16000)
def evaluate(cells: tuple[str, ...], turn: str) -> int:
    for mark in ("X", "O"):
        if any(all(cells[i] == mark for i in line) for line in LINES):
            return 1 if mark == "O" else -1
    values = [evaluate(cells[:i] + (turn,) + cells[i + 1:],
                       "X" if turn == "O" else "O")
              for i, cell in enumerate(cells) if not cell]
    return (max(values) if turn == "O" else min(values)) if values else 0


@dataclass(frozen=True, slots=True)
class BoardReading:
    event: str
    target: int | None


def read_board(board: Board, before: Board | None = None) -> BoardReading:
    if before and evaluate(board.cells, "X") < evaluate(before.cells, "O"):
        event = ("game_ttt_mistake" if evaluate(board.cells, "X") < 0 else
                 "game_ttt_mistake_draw")
        return BoardReading(event, next(
            (i for i in range(9) if before.cells[i] != board.cells[i]), None,
        ))
    own, other = winning_moves(board.cells, "O"), winning_moves(board.cells, "X")
    if board.turn == "O" and own:
        return BoardReading("game_ttt_finish", own[0])
    if other:
        return BoardReading("game_ttt_block" if board.turn == "O" else
                            "game_ttt_player_threat", other[0])
    if len(own) > 1:
        return BoardReading("game_ttt_fork", own[0])
    if own:
        return BoardReading("game_ttt_threat", own[0])
    value = evaluate(board.cells, board.turn)
    if value:
        return BoardReading("game_ttt_forced_aiko" if value > 0 else
                            "game_ttt_forced_player", 4)
    return BoardReading("game_ttt_balanced", 4)
