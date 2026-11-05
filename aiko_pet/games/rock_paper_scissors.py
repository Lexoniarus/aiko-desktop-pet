"""One transient Schere–Stein–Papier session, without Tk or persistence."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from secrets import randbelow
from typing import Callable

from .contracts import (
    RPS_WINNING_MOVES,
    RockPaperScissorsDetails,
    RockPaperScissorsMove,
)

Move = RockPaperScissorsMove
WINNING_MOVES = RPS_WINNING_MOVES


class Outcome(str, Enum):
    WIN = "win"
    LOSS = "loss"
    DRAW = "draw"


MOVES: tuple[Move, ...] = (Move.ROCK, Move.PAPER, Move.SCISSORS)


@dataclass(frozen=True, slots=True)
class Round:
    """Result from the human player's perspective, hidden until reveal."""

    player: Move
    aiko: Move
    outcome: Outcome

    @property
    def details(self) -> RockPaperScissorsDetails:
        return RockPaperScissorsDetails(self.player, self.aiko)


@dataclass(frozen=True, slots=True)
class Score:
    wins: int = 0
    losses: int = 0
    draws: int = 0

    @property
    def games(self) -> int:
        return self.wins + self.losses + self.draws


class RockPaperScissors:
    """Choose Aiko's move at selection; score only after the countdown."""

    def __init__(
        self, *, random_index: Callable[[int], int] = randbelow,
    ) -> None:
        self._random_index = random_index
        self._pending: Round | None = None
        self._score = Score()

    @property
    def score(self) -> Score:
        return self._score

    @property
    def pending(self) -> bool:
        return self._pending is not None

    def begin(self, player: Move) -> None:
        if not isinstance(player, Move):
            raise ValueError("Unknown move")
        if self._pending is not None:
            raise RuntimeError("Round already in progress")
        index = self._random_index(len(MOVES))
        if not 0 <= index < len(MOVES):
            raise ValueError("Opponent returned an invalid move")
        aiko = MOVES[index]
        if player == aiko:
            outcome = Outcome.DRAW
        elif (player, aiko) in WINNING_MOVES:
            outcome = Outcome.WIN
        else:
            outcome = Outcome.LOSS
        self._pending = Round(player, aiko, outcome)

    def reveal(self) -> Round:
        if self._pending is None:
            raise RuntimeError("No round to reveal")
        result = self._pending
        self._pending = None
        score = self._score
        self._score = Score(
            wins=score.wins + (result.outcome is Outcome.WIN),
            losses=score.losses + (result.outcome is Outcome.LOSS),
            draws=score.draws + (result.outcome is Outcome.DRAW),
        )
        return result

    def cancel(self) -> None:
        """Abort a pending selection without counting an unplayed round."""
        self._pending = None
