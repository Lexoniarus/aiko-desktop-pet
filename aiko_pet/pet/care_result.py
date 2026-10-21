"""Language-neutral effects of one care decision, shared by all consumers."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Literal, TypeAlias

from .food_catalog import FoodId

CareAction: TypeAlias = Literal[
    "feed", "play", "pet", "talk", "energy_drink", "sleep",
]
CARE_ACTIONS: frozenset[str] = frozenset(
    ("feed", "play", "pet", "talk", "energy_drink", "sleep"),
)


class CareEffect(StrEnum):
    FOOD_SATISFIED = "food_satisfied"
    FOOD_REPEAT = "food_repeat"
    FOOD_MEAL = "food_meal"
    FOOD_SNACK = "food_snack"
    PLAY_TIRED = "play_tired"
    PLAY_REQUESTED = "play_requested"
    DRINK_SATISFIED = "drink_satisfied"
    DRINK_CONSUMED = "drink_consumed"
    CONVERSATION = "conversation"
    AFFECTION = "affection"
    AFFECTION_ENOUGH = "affection_enough"
    AFFECTION_ENOUGH_FIRM = "affection_enough_firm"
    AFFECTION_REFUSED = "affection_refused"
    AFFECTION_BOUNDARY_IGNORED = "affection_boundary_ignored"
    SLEEP_STARTED = "sleep_started"
    SLEEP_ENDED = "sleep_ended"


@dataclass(frozen=True, slots=True)
class CareResult:
    """Actual care effect; no text, rendering or storage representation."""

    action: CareAction
    effect: CareEffect
    food_id: FoodId | None = None
    meal_id: str | None = None

    @property
    def affection_accepted(self) -> bool:
        return self.effect in (
            CareEffect.AFFECTION, CareEffect.AFFECTION_ENOUGH,
            CareEffect.AFFECTION_ENOUGH_FIRM,
        )

    @property
    def affection_refused(self) -> bool:
        return self.effect in (
            CareEffect.AFFECTION_REFUSED, CareEffect.AFFECTION_BOUNDARY_IGNORED,
        )

    @property
    def food_consumed(self) -> bool:
        return self.effect in (
            CareEffect.FOOD_REPEAT, CareEffect.FOOD_MEAL, CareEffect.FOOD_SNACK,
        )

    @property
    def consumed_item_id(self) -> str | None:
        if self.food_consumed:
            return self.food_id
        if self.effect == CareEffect.DRINK_CONSUMED:
            return "energy_drink"
        return None
