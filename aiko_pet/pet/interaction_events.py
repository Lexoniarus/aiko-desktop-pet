"""Bounded interaction evidence and immutable facts; no dispatcher or clock."""

from dataclasses import dataclass


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


InteractionEvent = Poked | PettingAttempted | BoundaryCommunicated | FoodConsumed
