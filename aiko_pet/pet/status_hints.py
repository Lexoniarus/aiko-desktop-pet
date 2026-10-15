"""Character-neutral mood hint keys and their priority order.

PetState and immutable read snapshots use the same pure policy. This module
contains no localized sentences, Tkinter or presentation dependencies.
"""

from __future__ import annotations

from collections.abc import Sequence
from enum import StrEnum
from typing import Protocol

from .balance import BALANCE
from .routine import TimeContext


class MoodHint(StrEnum):
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


class MoodHintState(Protocol):
    """Only read-only need values shared by PetState and PetReadSnapshot."""

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


def choose_mood_hint(
    pet: MoodHintState,
    context: TimeContext | None = None,
) -> MoodHint:
    """Choose one semantic hint, preserving existing need/time precedence."""
    if pet.sleeping:
        return (
            MoodHint.SLEEP_NIGHT
            if context is not None and context.night
            else MoodHint.SLEEP_REST
        )
    if pet.satiety < BALANCE.integer("status", "low_need"):
        return MoodHint.HUNGRY
    if pet.energy < BALANCE.integer("status", "low_need"):
        return MoodHint.TIRED
    if pet.social < BALANCE.integer("status", "low_need"):
        return MoodHint.LONELY
    if pet.affection < BALANCE.integer("status", "low_need"):
        return MoodHint.NEEDS_AFFECTION
    if pet.fun < BALANCE.integer("status", "low_need"):
        return MoodHint.BORED
    if context is not None:
        if context.meal and context.meal not in pet.meals_today:
            return MoodHint.MEAL_TIME
        if context.weekend:
            return MoodHint.WEEKEND
        if context.night:
            return MoodHint.LATE_NIGHT
        if context.period == "evening":
            return MoodHint.EVENING
    if min(
        pet.satiety,
        pet.mood,
        pet.energy,
        pet.social,
        pet.affection,
    ) > BALANCE.integer("status", "happy_average"):
        return MoodHint.GOOD_DAY
    return MoodHint.CONTENT
