"""Immutable definitions, geometry and objective World read values."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum


def _finite_nonnegative(value: float, name: str) -> None:
    if isinstance(value, bool) or not math.isfinite(value) or value < 0:
        raise ValueError(f"{name} must be finite and nonnegative")


@dataclass(frozen=True, slots=True)
class WorldPosition:
    """Support anchor in logical units; height is positive above the ground."""

    x: float
    height: float

    def __post_init__(self) -> None:
        _finite_nonnegative(self.x, "x")
        _finite_nonnegative(self.height, "height")


@dataclass(frozen=True, slots=True)
class ObjectFootprint:
    """Horizontal extents relative to the support anchor, not a hand grip."""

    left: float
    right: float

    def __post_init__(self) -> None:
        _finite_nonnegative(self.left, "left extent")
        _finite_nonnegative(self.right, "right extent")


@dataclass(frozen=True, slots=True)
class WorldSurface:
    """One logical ground interval and the supported space above it."""

    width: float
    height: float

    def __post_init__(self) -> None:
        _finite_nonnegative(self.width, "surface width")
        _finite_nonnegative(self.height, "surface height")
        if self.width == 0 or self.height == 0:
            raise ValueError("Surface dimensions must be positive")

    def contains(self, position: WorldPosition, footprint: ObjectFootprint) -> bool:
        return (
            footprint.left <= position.x <= self.width - footprint.right
            and position.height <= self.height
        )


class ObjectInteraction(StrEnum):
    EAT = "eat"
    DRINK = "drink"


@dataclass(frozen=True, slots=True)
class ObjectDefinition:
    """References to existing food/asset identities, without nutrition or copy."""

    definition_id: str
    asset_id: str
    food_id: str | None = None
    interactions: frozenset[ObjectInteraction] = frozenset()

    def __post_init__(self) -> None:
        for key in (self.definition_id, self.asset_id):
            if not key or not key.isidentifier():
                raise ValueError("Object and asset IDs must be identifiers")
        if self.food_id is not None and not self.food_id.isidentifier():
            raise ValueError("Food ID must be an identifier")
        if not isinstance(self.interactions, frozenset) or any(
            not isinstance(value, ObjectInteraction) for value in self.interactions
        ):
            raise ValueError("Interactions must be immutable typed capabilities")
        if (ObjectInteraction.EAT in self.interactions) != (self.food_id is not None):
            raise ValueError("An edible definition must reference a food ID")
        if ObjectInteraction.DRINK in self.interactions and self.food_id is not None:
            raise ValueError("A drink must not pretend to be a food")


class ObjectState(StrEnum):
    USER_HELD = "user_held"
    FALLING = "falling"
    RESTING = "resting"
    PET_HELD = "pet_held"
    CONSUMED = "consumed"
    REMOVED = "removed"


@dataclass(frozen=True, slots=True)
class WorldObjectSnapshot:
    """One objective instance; hidden knowledge filtering belongs elsewhere."""

    instance_id: str
    definition_id: str
    revision: int
    state: ObjectState
    position: WorldPosition | None
    footprint: ObjectFootprint
    fall_speed: float = 0.0


@dataclass(frozen=True, slots=True)
class WorldSnapshot:
    """Stable collection, including terminal identities, with no live mappings."""

    surface: WorldSurface
    revision: int
    definitions: tuple[ObjectDefinition, ...]
    objects: tuple[WorldObjectSnapshot, ...]
