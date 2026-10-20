"""Pure chronological pet progression; PetState owns applying the result."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Protocol

from .balance import BALANCE
from .food import (
    FoodActivity,
    FoodState,
    advance_food,
    hardware_consumption_fraction,
)
from .friendship_decay import advance_friendship
from .friendship_history import FriendshipProgress
from .fun import advance_fun
from .mood import NeedMoodFactors, advance_mood, calculate_need_mood_target
from .needs import NeedLevels
from .value_rules import clamp_need_value


class ProgressionValues(Protocol):
    """Read-only numeric pet inputs; policies cannot write back to the pet."""

    @property
    def sleeping(self) -> bool: ...

    @property
    def satiety(self) -> float: ...

    @property
    def food(self) -> FoodState: ...

    @property
    def fun(self) -> float: ...

    @property
    def mood(self) -> float: ...

    @property
    def energy(self) -> float: ...

    @property
    def social(self) -> float: ...

    @property
    def affection(self) -> float: ...


@dataclass(frozen=True, slots=True)
class PetProgress:
    """Transient calculation result; not another pet aggregate or save record."""

    needs: NeedLevels
    mood: float
    food: FoodState
    relationship: FriendshipProgress | None = None


def calculate_pet_progression(
    record: ProgressionValues,
    hours: float,
    effort: float | None = None,
    *,
    food_activity: FoodActivity | None = None,
    relationship: FriendshipProgress | None = None,
) -> PetProgress:
    """Integrate changing needs and mood without mutating the input aggregate.

    The existing time plan supplies routine/observation boundaries. This policy
    only integrates their numeric effects, using bounded temporary storage and
    the same calculation path for live, closed-app and suspended time.
    """
    satiety, energy = record.satiety, record.energy
    social, affection = record.social, record.affection
    mood, fun, food = record.mood, record.fun, record.food
    activity = (
        food_activity if food_activity is not None
        else FoodActivity(hardware_load=effort or 0.0)
    )
    if record.sleeping:
        energy_rate = BALANCE.number("needs", "sleeping_energy_gain_per_hour")
        social_rate = BALANCE.number("needs", "sleeping_social_loss_per_hour")
        affection_rate = BALANCE.number("needs", "sleeping_affection_loss_per_hour")
    else:
        intensity = hardware_consumption_fraction(activity.hardware_load)
        energy_rate = -(
            BALANCE.number("needs", "awake_energy_loss_per_hour")
            + BALANCE.number("needs", "hardware_energy_loss_per_hour") * intensity
        )
        social_rate = BALANCE.number("needs", "awake_social_loss_per_hour")
        affection_rate = BALANCE.number("needs", "awake_affection_loss_per_hour")
    remaining = hours * 3600 if math.isfinite(hours) and hours > 0 else 0.0
    step_limit = BALANCE.number("simulation", "needs_step_seconds")
    while remaining > 1e-9:
        seconds = min(remaining, step_limit)
        step_hours = seconds / 3600
        before = (satiety, energy, fun, social, affection)
        progress = advance_food(
            food, satiety, step_hours, sleeping=record.sleeping, activity=activity,
        )
        satiety, food = progress.satiety, progress.food
        energy = clamp_need_value(energy + step_hours * energy_rate)
        social = clamp_need_value(social - step_hours * social_rate)
        affection = clamp_need_value(affection - step_hours * affection_rate)
        fun = advance_fun(fun, step_hours, sleeping=record.sleeping)
        target = calculate_need_mood_target(NeedMoodFactors(
            satiety=satiety, energy=energy, fun=fun,
            social=social, affection=affection,
        ))
        mood = advance_mood(
            mood, target, step_hours,
            lowest_need=min(satiety, energy, fun, social, affection),
        )
        if relationship is not None:
            relationship = advance_friendship(
                relationship, seconds, before,
                (satiety, energy, fun, social, affection), sleeping=record.sleeping,
            )
        remaining -= seconds
    return PetProgress(
        NeedLevels(satiety, energy, fun, social, affection), mood, food, relationship,
    )
