"""Read-only object-use decisions, separate from curiosity and consumption."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from ..balance import BALANCE
from ..consumption import ConsumptionOrigin
from ..food import FOOD_BALANCE
from ..state import PetState
from .object_perception import ObjectObservation


@dataclass(frozen=True, slots=True)
class ObjectUseDecision:
    consume: bool
    reason: Literal["hungry", "low_energy", "not_needed", "unrecognized", "unavailable"]


def decide_object_use(
    known: ObjectObservation | None, state: PetState,
    origin: ConsumptionOrigin = ConsumptionOrigin.AUTONOMOUS,
) -> ObjectUseDecision:
    if known is None or known.identity is None or known.kind is None:
        return ObjectUseDecision(False, "unrecognized")
    if state.sleeping:
        return ObjectUseDecision(False, "unavailable")
    drink = known.kind == "drink"
    level = state.energy if drink else state.satiety
    capacity = 100 if drink else FOOD_BALANCE.too_full_to_eat_threshold
    threshold = capacity if origin == ConsumptionOrigin.HANDOVER else BALANCE.number(
        "object_behavior", "seek_drink_energy" if drink else "seek_food_satiety",
    )
    wanted = level < capacity and (
        origin == ConsumptionOrigin.HANDOVER or level <= threshold
    )
    return ObjectUseDecision(wanted, ("low_energy" if drink else "hungry")
                             if wanted else "not_needed")
