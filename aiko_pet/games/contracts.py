"""Small immutable contracts shared by transient minigame sessions."""

from dataclasses import dataclass
from enum import Enum


class GameId(str, Enum):
    ROCK_PAPER_SCISSORS = "rock_paper_scissors"
    TIC_TAC_TOE = "tic_tac_toe"
    BLACKJACK = "blackjack"


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

    @property
    def games(self) -> int:
        return self.wins + self.losses + self.draws
