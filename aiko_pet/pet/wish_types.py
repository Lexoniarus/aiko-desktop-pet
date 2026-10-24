"""Shared immutable wish areas and target meaning, without progress or rewards."""

from dataclasses import dataclass
from enum import StrEnum


class WishArea(StrEnum):
    FOOD = "food"
    GAMES = "games"
    SOCIAL = "social"
    AFFECTION = "affection"


class WishTargetKind(StrEnum):
    FOOD = "food"
    GAME = "game"
    SOCIAL = "social"
    CARE = "care"


class WishTargetMode(StrEnum):
    EXACT = "exact"
    ANY = "any"
    EXCLUDE = "exclude"


@dataclass(frozen=True, slots=True)
class WishTarget:
    """A fixed target meaning, independent of the activity eventually chosen."""

    kind: WishTargetKind
    mode: WishTargetMode
    target_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.kind, WishTargetKind) or not isinstance(
            self.mode,
            WishTargetMode,
        ):
            raise ValueError("Wish target requires typed kind and mode")
        if self.mode == WishTargetMode.ANY:
            if self.target_id is not None:
                raise ValueError("Free-choice wish cannot bind a concrete target")
        elif not isinstance(self.target_id, str) or not self.target_id:
            raise ValueError("Concrete/excluded wish requires a reference target")

    def matches(self, kind: WishTargetKind, target_id: str) -> bool:
        """Match a validated activity identity within the same target kind."""
        if kind != self.kind or not target_id:
            return False
        if self.mode == WishTargetMode.ANY:
            return True
        if self.mode == WishTargetMode.EXCLUDE:
            return target_id != self.target_id
        return target_id == self.target_id


class WishId(StrEnum):
    FOOD = "food"
    AVOID_FOOD = "avoid_food"
    PLAY_GAME = "play_game"
    WIN_ROUND = "win_round"
    AVOID_ROUND_LOSS = "avoid_round_loss"
    WIN_OVERALL = "win_overall"
    AVOID_OVERALL_LOSS = "avoid_overall_loss"
    PLAY_ANY_GAME = "play_any_game"
    PLAY_OTHER_GAME = "play_other_game"
    REMATCH_GAME = "rematch_game"
    COMEBACK_GAME = "comeback_game"
    SOCIAL_ANY = "social_any"
    CHAT = "chat"
    SINGLE = "single"
    TWO_PARTS = "twopart"
    FACT = "fact"
    PET = "pet"


class WishObjective(StrEnum):
    """Stable goal meanings, independent of a catalogue ID's current wording."""

    FOOD_INTAKE = "food_intake"
    FOOD_HANDOVER = "food_handover"
    ACTIVITY = "activity"
    SESSION_ROUNDS = "session_rounds"
    TOTAL_ROUNDS = "total_rounds"
    RETRY_WIN = "retry_win"
    NEXT_WIN = "next_win"
    NEXT_NON_LOSS = "next_non_loss"
    BLOCK_MAJORITY = "block_majority"
    TOTAL_WINS = "total_wins"
    BLOCK_NON_LOSS = "block_non_loss"


@dataclass(frozen=True, slots=True)
class WishGoal:
    objective: WishObjective
    required_count: int
