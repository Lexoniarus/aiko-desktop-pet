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

    @property
    def identity(self) -> str:
        return f"{self.session_id}:{self.number}"
