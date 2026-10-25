"""Small immutable contracts shared by transient minigame sessions."""

from dataclasses import dataclass
from enum import Enum
from typing import Literal

RoundOutcome = Literal["win", "loss", "draw"]
GameResult = Literal["win", "loss", "draw", "completed"]


class GameId(str, Enum):
    ROCK_PAPER_SCISSORS = "rock_paper_scissors"
    TIC_TAC_TOE = "tic_tac_toe"
    BLACKJACK = "blackjack"
    CONNECT_FOUR = "connect_four"
    MASTERMIND = "mastermind"
    QUIZ = "quiz"


class RockPaperScissorsMove(str, Enum):
    ROCK = "rock"
    PAPER = "paper"
    SCISSORS = "scissors"


RPS_WINNING_MOVES = frozenset({
    (RockPaperScissorsMove.ROCK, RockPaperScissorsMove.SCISSORS),
    (RockPaperScissorsMove.PAPER, RockPaperScissorsMove.ROCK),
    (RockPaperScissorsMove.SCISSORS, RockPaperScissorsMove.PAPER),
})


@dataclass(frozen=True, slots=True)
class RockPaperScissorsDetails:
    """Actual hands of one revealed event, independent of wishes and scores."""

    player_move: RockPaperScissorsMove
    aiko_move: RockPaperScissorsMove

    def __post_init__(self) -> None:
        if (not isinstance(self.player_move, RockPaperScissorsMove)
                or not isinstance(self.aiko_move, RockPaperScissorsMove)):
            raise ValueError("Rock Paper Scissors details require typed moves")

    @property
    def player_outcome(self) -> RoundOutcome:
        if self.player_move == self.aiko_move:
            return "draw"
        return (
            "win" if (self.player_move, self.aiko_move) in RPS_WINNING_MOVES else "loss"
        )

    @property
    def aiko_outcome(self) -> RoundOutcome:
        result = self.player_outcome
        return "loss" if result == "win" else "win" if result == "loss" else "draw"


@dataclass(frozen=True, slots=True)
class SessionSummary:
    """Completed units from the player's perspective; never persisted."""

    game_id: GameId
    wins: int = 0
    losses: int = 0
    draws: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.game_id, GameId) or any(
            type(value) is not int or value < 0
            for value in (self.wins, self.losses, self.draws)
        ):
            raise ValueError("Invalid game session summary")
        if self.game_id is GameId.QUIZ and self.games:
            raise ValueError("Quiz completion is not a competitive score")

    @property
    def games(self) -> int:
        return self.wins + self.losses + self.draws


@dataclass(frozen=True, slots=True)
class GameRoundEvent:
    """Actual start (outcome None) or settled result, from the player's view."""

    game_id: GameId
    session_id: str
    number: int
    outcome: GameResult | None = None
    details: RockPaperScissorsDetails | None = None

    def __post_init__(self) -> None:
        if (not isinstance(self.game_id, GameId)
                or not isinstance(self.session_id, str)
                or not 1 <= len(self.session_id) <= 64
                or type(self.number) is not int or not 1 <= self.number < 2**63
                or self.outcome not in (None, "win", "loss", "draw", "completed")
                or self.outcome == "completed" and self.game_id is not GameId.QUIZ
                or self.game_id is GameId.QUIZ
                and self.outcome not in (None, "completed")):
            raise ValueError("Invalid game round evidence")
        if self.details is not None and (
            not isinstance(self.details, RockPaperScissorsDetails)
            or self.game_id is not GameId.ROCK_PAPER_SCISSORS
            or self.outcome != self.details.player_outcome
        ):
            raise ValueError("Game result details must match a revealed RPS outcome")

    @property
    def identity(self) -> str:
        return f"{self.session_id}:{self.number}"
