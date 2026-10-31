"""Read-only object-use decisions, separate from curiosity and consumption."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal

from ..balance import BALANCE
from ..food import FOOD_BALANCE
from ..food_wishes import food_wish_permission
from ..state import PetState
from ..wish_catalog import WISH_CATALOG
from .object_knowledge import ObjectKnowledge


class ObjectUseContext(Enum):
    """Why use is considered, independently of who supplies the care."""

    SUPPLY = "supply"
    OFFER = "offer"
    CONTINUING_WISH = "continuing_wish"


@dataclass(frozen=True, slots=True)
class ObjectUseDecision:
    consume: bool
    reason: Literal[
        "hungry", "low_energy", "not_needed", "unrecognized", "unavailable", "read"
    ]
    read: bool = False

    @property
    def use(self) -> bool:
        return self.consume or self.read


def decide_object_use(
    known: ObjectKnowledge | None,
    state: PetState,
    context: ObjectUseContext = ObjectUseContext.SUPPLY,
) -> ObjectUseDecision:
    if known is None or known.identity is None or known.kind is None:
        return ObjectUseDecision(False, "unrecognized")
    if state.sleeping:
        return ObjectUseDecision(False, "unavailable")
    if known.kind == "book":
        return ObjectUseDecision(False, "not_needed")
    drink = known.kind == "drink"
    if drink and state.sleep_episode.care_break:
        return ObjectUseDecision(False, "not_needed")
    level = state.energy if drink else state.satiety
    if state.sleep_episode.care_break and level >= BALANCE.number(
        "sleep", "food_target"
    ):
        return ObjectUseDecision(False, "not_needed")
    if not drink:
        permission = food_wish_permission(
            state.wishes,
            known.identity,
            elapsed=state.lived_seconds,
            definitions=WISH_CATALOG.definitions,
            object_id=known.instance_id,
            personal=context != ObjectUseContext.SUPPLY,
        )
        if permission.excluded:
            return ObjectUseDecision(False, "not_needed")
        if permission.requested:
            return ObjectUseDecision(True, "hungry")
    capacity = 100 if drink else FOOD_BALANCE.too_full_to_eat_threshold
    threshold = (
        capacity
        if context != ObjectUseContext.SUPPLY
        else BALANCE.number(
            "object_behavior",
            "seek_drink_energy" if drink else "seek_food_satiety",
        )
    )
    wanted = level < capacity and (
        context != ObjectUseContext.SUPPLY or level <= threshold
    )
    return ObjectUseDecision(
        wanted, ("low_energy" if drink else "hungry") if wanted else "not_needed"
    )
