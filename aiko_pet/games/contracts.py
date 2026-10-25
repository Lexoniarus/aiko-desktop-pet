"""Small immutable contracts shared by transient minigame sessions."""

from dataclasses import dataclass
from enum import Enum
from typing import Literal, TypeAlias

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
    def game_id(self) -> GameId:
        return GameId.ROCK_PAPER_SCISSORS

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


class BlackjackDecisionReason(str, Enum):
    AIKO_BUST = "aiko_bust"
    PLAYER_BUST = "player_bust"
    AIKO_BLACKJACK = "aiko_blackjack"
    PLAYER_BLACKJACK = "player_blackjack"
    BOTH_BLACKJACK = "both_blackjack"
    HIGHER_TOTAL = "higher_total"
    EQUAL_TOTAL = "equal_total"


@dataclass(frozen=True, slots=True)
class BlackjackDetails:
    """Actual totals and the decision made by Blackjack's settled rules."""

    player_total: int
    aiko_total: int
    reason: BlackjackDecisionReason

    def __post_init__(self) -> None:
        if (type(self.player_total) is not int or type(self.aiko_total) is not int
                or not 4 <= self.player_total <= 30
                or not 4 <= self.aiko_total <= 26
                or not isinstance(self.reason, BlackjackDecisionReason)):
            raise ValueError("Invalid Blackjack totals or decision reason")
        player, aiko = self.player_total, self.aiko_total
        valid = {
            BlackjackDecisionReason.AIKO_BUST: aiko > 21 and player <= 21,
            BlackjackDecisionReason.PLAYER_BUST: player > 21 and aiko < 21,
            BlackjackDecisionReason.AIKO_BLACKJACK: aiko == 21 and player < 21,
            BlackjackDecisionReason.PLAYER_BLACKJACK: player == 21 and aiko < 21,
            BlackjackDecisionReason.BOTH_BLACKJACK: player == aiko == 21,
            BlackjackDecisionReason.HIGHER_TOTAL: (
                player <= 21 and 17 <= aiko <= 21 and player != aiko
            ),
            BlackjackDecisionReason.EQUAL_TOTAL: player == aiko and 17 <= aiko <= 21,
        }
        if not valid[self.reason]:
            raise ValueError("Blackjack totals contradict the decision reason")

    @property
    def game_id(self) -> GameId:
        return GameId.BLACKJACK

    @property
    def player_outcome(self) -> RoundOutcome:
        if self.reason in (
            BlackjackDecisionReason.AIKO_BUST, BlackjackDecisionReason.PLAYER_BLACKJACK,
        ):
            return "win"
        if self.reason in (
            BlackjackDecisionReason.PLAYER_BUST, BlackjackDecisionReason.AIKO_BLACKJACK,
        ):
            return "loss"
        if self.reason in (
            BlackjackDecisionReason.BOTH_BLACKJACK, BlackjackDecisionReason.EQUAL_TOTAL,
        ):
            return "draw"
        return "win" if self.player_total > self.aiko_total else "loss"

    @property
    def aiko_outcome(self) -> RoundOutcome:
        result = self.player_outcome
        return "loss" if result == "win" else "win" if result == "loss" else "draw"


GameResultDetails: TypeAlias = RockPaperScissorsDetails | BlackjackDetails


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
    details: GameResultDetails | None = None

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
            not isinstance(self.details, (RockPaperScissorsDetails, BlackjackDetails))
            or self.game_id is not self.details.game_id
            or self.outcome != self.details.player_outcome
        ):
            raise ValueError("Game result details must match the actual game outcome")

    @property
    def identity(self) -> str:
        return f"{self.session_id}:{self.number}"
