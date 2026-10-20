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
from .mood import NeedMoodFactors, advance_mood, calculate_mood_target
from .moodlet_catalog import MOODLET_CATALOG
from .moodlets import (
    MoodletState,
    PoorCareParameters,
    advance_moodlets,
    calculate_moodlet_contributions,
    next_moodlet_boundary,
)
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

    @property
    def moodlets(self) -> MoodletState: ...

    @property
    def lived_seconds(self) -> float: ...


@dataclass(frozen=True, slots=True)
class PetProgress:
    """Transient calculation result; not another pet aggregate or save record."""

    needs: NeedLevels
    mood: float
    food: FoodState
    moodlets: MoodletState
    relationship: FriendshipProgress | None = None


def _advance_needs(
    before: NeedLevels, food: FoodState, hours: float, *, sleeping: bool,
    activity: FoodActivity, rates: tuple[float, float, float],
) -> tuple[NeedLevels, FoodState]:
    progress = advance_food(food, before.satiety, hours, sleeping=sleeping,
                            activity=activity)
    energy, social, affection = rates
    return NeedLevels(
        progress.satiety, clamp_need_value(before.energy + hours * energy),
        advance_fun(before.fun, hours, sleeping=sleeping),
        clamp_need_value(before.social - hours * social),
        clamp_need_value(before.affection - hours * affection),
    ), progress.food


def _recovery_crossing(
    state: MoodletState, before: NeedLevels, after: NeedLevels, seconds: float,
) -> float:
    """Split existing numeric steps at actual recovery-threshold crossings."""
    if not state.active:
        return seconds
    threshold = BALANCE.number("moodlets", "recovery_need_threshold")
    boundary = seconds
    for episode in state.active:
        parameters = MOODLET_CATALOG.definitions[episode.definition_id].parameters
        if not isinstance(parameters, PoorCareParameters):
            continue
        low, high = (float(getattr(needs, parameters.need))
                     for needs in (before, after))
        if min(low, high) < threshold < max(low, high):
            boundary = min(boundary, seconds * (threshold - low) / (high - low))
    return boundary


def calculate_pet_progression(
    record: ProgressionValues,
    hours: float,
    effort: float | None = None,
    *,
    food_activity: FoodActivity | None = None,
    relationship: FriendshipProgress | None = None,
    observed: bool = True,
) -> PetProgress:
    """Integrate changing needs and mood without mutating the input aggregate.

    The existing time plan supplies routine/observation boundaries. This policy
    only integrates their numeric effects, using bounded temporary storage and
    the same calculation path for live, closed-app and suspended time.
    """
    satiety, energy = record.satiety, record.energy
    social, affection = record.social, record.affection
    mood, fun, food = record.mood, record.fun, record.food
    moodlets, elapsed = record.moodlets, record.lived_seconds
    definitions = MOODLET_CATALOG.definitions
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
        before_needs = NeedLevels(satiety, energy, fun, social, affection)
        seconds = min(remaining, step_limit)
        if moodlets.active:
            moodlets = advance_moodlets(
                moodlets, 0, elapsed=elapsed, before=before_needs, after=before_needs,
                definitions=definitions, observed=observed,
            )
            seconds = min(seconds, next_moodlet_boundary(
                moodlets, elapsed=elapsed, definitions=definitions,
            ))
        after_needs, next_food = _advance_needs(
            before_needs, food, seconds / 3600, sleeping=record.sleeping,
            activity=activity, rates=(energy_rate, social_rate, affection_rate),
        )
        crossing = _recovery_crossing(moodlets, before_needs, after_needs, seconds)
        if crossing < seconds:
            seconds = crossing
            after_needs, next_food = _advance_needs(
                before_needs, food, seconds / 3600, sleeping=record.sleeping,
                activity=activity, rates=(energy_rate, social_rate, affection_rate),
            )
        step_hours = seconds / 3600
        before = (satiety, energy, fun, social, affection)
        satiety, energy, fun = after_needs.satiety, after_needs.energy, after_needs.fun
        social, affection, food = after_needs.social, after_needs.affection, next_food
        target = calculate_mood_target(NeedMoodFactors(
            satiety=satiety, energy=energy, fun=fun,
            social=social, affection=affection,
        ), calculate_moodlet_contributions(moodlets, definitions=definitions))
        mood = advance_mood(
            mood, target, step_hours,
            lowest_need=min(satiety, energy, fun, social, affection),
        )
        if relationship is not None:
            relationship = advance_friendship(
                relationship, seconds, before,
                (satiety, energy, fun, social, affection), sleeping=record.sleeping,
            )
        if moodlets.active:
            moodlets = advance_moodlets(
                moodlets, seconds, elapsed=elapsed, before=before_needs,
                after=after_needs, definitions=definitions, observed=observed,
            )
        elapsed += seconds
        remaining -= seconds
    return PetProgress(
        NeedLevels(satiety, energy, fun, social, affection), mood, food,
        moodlets, relationship,
    )
