"""Bounded interaction evidence and immutable facts; no dispatcher or clock."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class InteractionMemory:
    poke_boundary_at: float | None = None
    petting_boundary_at: float | None = None
    petting_refused_until: float = 0.0


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


InteractionEvent = Poked | PettingAttempted | BoundaryCommunicated
