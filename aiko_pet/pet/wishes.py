"""Immutable wish definitions and aggregate-owned inner wish progress."""

from dataclasses import dataclass
from enum import StrEnum

from .moodlets import MoodletId


class WishId(StrEnum):
    FOOD = "food"
    PLAY_GAME = "play_game"
    WIN_ROUND = "win_round"
    AVOID_ROUND_LOSS = "avoid_round_loss"
    WIN_OVERALL = "win_overall"
    AVOID_OVERALL_LOSS = "avoid_overall_loss"
    CHAT = "chat"
    SINGLE = "single"
    TWO_PARTS = "twopart"
    FACT = "fact"
    PET = "pet"


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


@dataclass(frozen=True, slots=True)
class WishDefinition:
    """Supported targets and a fulfillment outcome; no deadlines or progress."""

    id: WishId
    area: WishArea
    target_kind: WishTargetKind
    targets: tuple[str, ...]
    fulfillment_moodlet: MoodletId
    fulfillment_level: int
    round_count: int

    @property
    def label_key(self) -> str:
        return f"wish.{self.id}.label"

    @property
    def description_key(self) -> str:
        return f"wish.{self.id}.description"


@dataclass(frozen=True, slots=True)
class GameWishProgress:
    """Only the bounded objective block, never a board, deck or session score.

    Completed round identities support duplicate detection. A session token
    distinguishes the shared-play objective's single-session progress.
    """

    round_ids: tuple[str, ...] = ()
    wins: int = 0
    losses: int = 0
    session_id: str | None = None


@dataclass(frozen=True, slots=True)
class ActiveWish:
    instance_id: int
    definition_id: WishId
    target_id: str
    created_at: float
    expires_at: float
    expressed_at: float | None = None
    game: GameWishProgress = GameWishProgress()


@dataclass(frozen=True, slots=True)
class WishState:
    """Stable identities and bounded pacing evidence survive removed wishes.

    Removing a fulfilled/ended wish retires its identity; an event for that
    identity cannot find an active wish again after a save/reload. Relationship
    amounts still belong to the existing friendship history, not this record.
    """

    next_instance_id: int = 1
    active: tuple[ActiveWish, ...] = ()
    last_created_by_area: tuple[tuple[WishArea, float], ...] = ()
    last_expressed_at: float | None = None

    @property
    def last_created_at(self) -> float | None:
        return max((stamp for _, stamp in self.last_created_by_area), default=None)
