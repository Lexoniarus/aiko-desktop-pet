"""Character-neutral status advice keys and their priority order.

PetState and immutable read snapshots use the same pure policy. This module
contains no localized sentences, Tkinter or presentation dependencies.
"""

from __future__ import annotations

from collections.abc import Sequence
from enum import StrEnum
from typing import Protocol

from .balance import BALANCE
from .routine import TimeContext


class StatusHint(StrEnum):
    """Meaning of the currently most helpful status line, not its wording."""

    SLEEP_NIGHT = "sleep_night"
    SLEEP_REST = "sleep_rest"
    HUNGRY = "hungry"
    TIRED = "tired"
    LONELY = "lonely"
    NEEDS_AFFECTION = "needs_affection"
    BORED = "bored"
    MEAL_TIME = "meal_time"
    WEEKEND = "weekend"
    LATE_NIGHT = "late_night"
    EVENING = "evening"
    GOOD_DAY = "good_day"
    CONTENT = "content"


class StatusHintValues(Protocol):
    """Need, numeric mood and lifecycle reads; not an emotional-state model."""

    @property
    def sleeping(self) -> bool: ...

    @property
    def satiety(self) -> float: ...

    @property
    def energy(self) -> float: ...

    @property
    def social(self) -> float: ...

    @property
    def affection(self) -> float: ...

    @property
    def fun(self) -> float: ...

    @property
    def mood(self) -> float: ...

    @property
    def meals_today(self) -> Sequence[str]: ...


def choose_status_hint(
    pet: StatusHintValues,
    context: TimeContext | None = None,
) -> StatusHint:
    """Choose one semantic hint, preserving existing need/time precedence."""
    if pet.sleeping:
        return (
            StatusHint.SLEEP_NIGHT
            if context is not None and context.night
            else StatusHint.SLEEP_REST
        )
    if pet.satiety < BALANCE.integer("status", "low_need"):
        return StatusHint.HUNGRY
    if pet.energy < BALANCE.integer("status", "low_need"):
        return StatusHint.TIRED
    if pet.social < BALANCE.integer("status", "low_need"):
        return StatusHint.LONELY
    if pet.affection < BALANCE.integer("status", "low_need"):
        return StatusHint.NEEDS_AFFECTION
    if pet.fun < BALANCE.integer("status", "low_need"):
        return StatusHint.BORED
    if context is not None:
        if context.meal and context.meal not in pet.meals_today:
            return StatusHint.MEAL_TIME
        if context.weekend:
            return StatusHint.WEEKEND
        if context.night:
            return StatusHint.LATE_NIGHT
        if context.period == "evening":
            return StatusHint.EVENING
    if min(
        pet.satiety,
        pet.mood,
        pet.energy,
        pet.social,
        pet.affection,
    ) > BALANCE.integer("status", "happy_average"):
        return StatusHint.GOOD_DAY
    return StatusHint.CONTENT
