"""Typed commands accepted by Aiko's application layer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias, cast

from ..pet.care_result import CARE_ACTIONS, CareAction
from ..pet.food import FOOD_CATALOG, FoodId
from .events import IncomingNotification


@dataclass(frozen=True, slots=True)
class CareCommand:
    """An intentional local care action, never an untrusted API event."""

    action: CareAction
    food_id: FoodId | None = None

    def __post_init__(self) -> None:
        if self.action not in CARE_ACTIONS:
            raise ValueError(f"Unsupported care action: {self.action}")
        if self.food_id is not None and (
            self.action != "feed" or self.food_id not in FOOD_CATALOG
        ):
            raise ValueError("Invalid food selection for care action")

    @classmethod
    def from_action(
        cls, action: str, *, food_id: FoodId | None = None,
    ) -> CareCommand:
        """Check a UI string before converting it to a typed care command."""
        if action not in CARE_ACTIONS:
            raise ValueError(f"Unsupported care action: {action}")
        return cls(cast(CareAction, action), food_id=food_id)


@dataclass(frozen=True, slots=True)
class NotificationCommand:
    """An already validated, authorized notification from an adapter."""

    notification: IncomingNotification


ApplicationCommand: TypeAlias = CareCommand | NotificationCommand
