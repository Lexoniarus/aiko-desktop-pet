"""Read-only object-use decisions, separate from curiosity and consumption."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal

from ..balance import BALANCE
from ..food import FOOD_BALANCE
from ..state import PetState
from .object_knowledge import ObjectKnowledge


class ObjectUseContext(Enum):
    """Why use is considered, independently of who supplies the care."""

    SUPPLY = "supply"
    OFFER = "offer"
    CONTINUING_WISH = "continuing_wish"


@dataclass(frozen=True, slots=True)
class ObjectUseDecision:
    consume: bool
    reason: Literal["hungry", "low_energy", "not_needed", "unrecognized", "unavailable"]


def decide_object_use(
    known: ObjectKnowledge | None, state: PetState,
    context: ObjectUseContext = ObjectUseContext.SUPPLY,
) -> ObjectUseDecision:
    if known is None or known.identity is None or known.kind is None:
        return ObjectUseDecision(False, "unrecognized")
    if state.sleeping:
        return ObjectUseDecision(False, "unavailable")
    drink = known.kind == "drink"
    level = state.energy if drink else state.satiety
    capacity = 100 if drink else FOOD_BALANCE.too_full_to_eat_threshold
    threshold = capacity if context != ObjectUseContext.SUPPLY else BALANCE.number(
        "object_behavior", "seek_drink_energy" if drink else "seek_food_satiety",
    )
    wanted = level < capacity and (
        context != ObjectUseContext.SUPPLY or level <= threshold
    )
    return ObjectUseDecision(wanted, ("low_energy" if drink else "hungry")
                             if wanted else "not_needed")
