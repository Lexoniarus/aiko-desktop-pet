"""Bounded interaction evidence and immutable facts; no dispatcher or clock."""

import math
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True, slots=True)
class FoodRepetitionMemory:
    food_id: str | None = None
    intakes: tuple[float, ...] = ()
    request_pending: bool = False
    requested_at: float | None = None
    ignored_portions: int = 0


@dataclass(frozen=True, slots=True)
class InteractionMemory:
    poke_boundary_at: float | None = None
    petting_boundary_at: float | None = None
    petting_refused_until: float = 0.0
    food: FoodRepetitionMemory = FoodRepetitionMemory()
    petting_excess_attempts: int = 0
    petting_last_excess_at: float | None = None


@dataclass(frozen=True, slots=True)
class Poked:
    continuing_burst: bool


@dataclass(frozen=True, slots=True)
class PettingAttempted:
    affection: float
    friendship_level: int


@dataclass(frozen=True, slots=True)
class BoundaryCommunicated:
    kind: str


@dataclass(frozen=True, slots=True)
class FoodConsumed:
    food_id: str
    personal: bool


@dataclass(frozen=True, slots=True)
class WithholdingObserved:
    reinforce: bool = True
    repeated_take: bool = False


@dataclass(frozen=True, slots=True)
class WithholdingEnded:
    pass


@dataclass(frozen=True, slots=True)
class ArrangementDisrupted:
    attributed: bool = False


@dataclass(frozen=True, slots=True)
class SocialCompletion:
    """Admitted category/wish and actual sequence identity carried through playback.

    Application admissions provide a sequence ID and elapsed start. Older direct
    value callers may omit both; no history is fabricated for those values.
    """

    category: str
    wish_instance_id: int | None = None
    sequence_id: str | None = None
    started_at: float | None = None

    def __post_init__(self) -> None:
        if (self.category not in ("chat", "single", "twopart", "fact")
                or self.wish_instance_id is not None
                and (type(self.wish_instance_id) is not int
                     or self.wish_instance_id < 1)):
            raise ValueError("Invalid social completion evidence")
        if (self.sequence_id is None) != (self.started_at is None):
            raise ValueError("Social admission identity requires its elapsed start")
        if self.sequence_id is not None and (
            not isinstance(self.sequence_id, str)
            or not 1 <= len(self.sequence_id) <= 120
        ):
            raise ValueError("Invalid social sequence identity")
        if self.started_at is not None and (
            type(self.started_at) not in (int, float)
            or not math.isfinite(self.started_at) or self.started_at < 0
        ):
            raise ValueError("Invalid social admission time")

    @property
    def kind(self) -> Literal["chat", "social"]:
        return "chat" if self.category == "chat" else "social"


@dataclass(frozen=True, slots=True)
class HelpfulInteraction:
    kind: Literal["chat", "social", "petting", "play", "meal"]
    arrangement_ready: bool = False


InteractionEvent = (
    Poked | PettingAttempted | BoundaryCommunicated | FoodConsumed
    | WithholdingObserved | WithholdingEnded | ArrangementDisrupted
    | HelpfulInteraction
)
