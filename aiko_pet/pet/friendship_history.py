"""Immutable elapsed-axis relationship evidence, owned within PetValues."""

from dataclasses import dataclass

NEED_NAMES = ("satiety", "energy", "fun", "social", "affection")
NeedDurations = tuple[float, float, float, float, float]
EMPTY_DURATIONS: NeedDurations = (0.0, 0.0, 0.0, 0.0, 0.0)


@dataclass(frozen=True, slots=True)
class RelationshipEvent:
    at: float
    kind: str
    amount: float


@dataclass(frozen=True, slots=True)
class CriticalBucket:
    start: float
    critical: NeedDurations = EMPTY_DURATIONS
    zero: NeedDurations = EMPTY_DURATIONS
    width: float = 60.0


@dataclass(frozen=True, slots=True)
class FriendshipHistory:
    """None baseline means legacy history is unavailable, not past care."""

    baseline: float | None = None
    last_contact: float | None = None
    rewards: tuple[RelationshipEvent, ...] = ()
    eligible: tuple[tuple[str, float], ...] = ()
    critical: tuple[CriticalBucket, ...] = ()
    penalties: tuple[RelationshipEvent, ...] = ()
    continuous_since: float | None = None


@dataclass(frozen=True, slots=True)
class FriendshipProgress:
    points: float
    history: FriendshipHistory
    elapsed: float
