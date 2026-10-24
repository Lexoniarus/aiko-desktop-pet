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
from .friendship_history import NEED_NAMES, FriendshipProgress
from .fun import advance_fun
from .long_term_moodlets import (
    advance_long_term,
    next_long_term_boundary,
    prepare_long_term,
)
from .mood import NeedMoodFactors, advance_mood, calculate_mood_target
from .moodlet_catalog import MOODLET_CATALOG
from .moodlets import (
    MoodletState,
    advance_moodlets,
    calculate_moodlet_contributions,
    next_moodlet_boundary,
)
from .needs import NeedLevels
from .poor_care import (
    next_poor_care_boundary,
    poor_care_at_capacity,
    prepare_poor_care,
    qualify_poor_care,
)
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


def _need_crossing(
    before: NeedLevels, after: NeedLevels, food: FoodState, seconds: float, *,
    sleeping: bool, activity: FoodActivity, rates: tuple[float, float, float],
) -> float:
    """Use canonical needs at zero, critical and recovery crossings.

    A clamped zero endpoint alone cannot show how much of a step was at zero.
    Only these rare crossings require root finding; there is no extra time loop.
    """
    if before == after:
        return seconds
    boundary = seconds
    for name in NEED_NAMES:
        low, high = float(getattr(before, name)), float(getattr(after, name))
        for threshold in (0.0, BALANCE.number("friendship", "critical_need"),
                          BALANCE.number("moodlets", "recovery_need_threshold")):
            if not (low < threshold <= high or high <= threshold < low):
                continue
            left, right = 0.0, seconds
            for _ in range(36):
                middle = (left + right) / 2
                at, _ = _advance_needs(before, food, middle / 3600, sleeping=sleeping,
                                       activity=activity, rates=rates)
                value = float(getattr(at, name))
                if (value > threshold if high < low else value < threshold):
                    left = middle
                else:
                    right = middle
            boundary = min(boundary, max(1e-7, right))
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
    endpoint = elapsed + remaining
    represented = False
    if remaining > 0:
        moodlets = prepare_long_term(moodlets, elapsed=elapsed)
    while remaining > 1e-9:
        before_needs = NeedLevels(satiety, energy, fun, social, affection)
        if relationship is not None and not represented:
            moodlets = prepare_poor_care(
                moodlets, relationship.history, elapsed=elapsed,
            )
        seconds = min(remaining, step_limit)
        seconds = min(seconds, next_long_term_boundary(moodlets, elapsed=elapsed))
        if moodlets.active and not represented:
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
        crossing = _need_crossing(
            before_needs, after_needs, food, seconds, sleeping=record.sleeping,
            activity=activity, rates=(energy_rate, social_rate, affection_rate),
        )
        if crossing < seconds:
            seconds = crossing
            after_needs, next_food = _advance_needs(
                before_needs, food, seconds / 3600, sleeping=record.sleeping,
                activity=activity, rates=(energy_rate, social_rate, affection_rate),
            )
        if relationship is not None and not represented:
            boundary = next_poor_care_boundary(
                moodlets, relationship.history, elapsed=elapsed, seconds=seconds,
                before=before_needs, after=after_needs, sleeping=record.sleeping,
            )
            if boundary < seconds:
                seconds = boundary
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
        ), calculate_moodlet_contributions(
            moodlets, definitions=definitions,
            long_term_policy=MOODLET_CATALOG.long_term_policy,
        ))
        mood_before = mood
        mood = advance_mood(
            mood, target, step_hours,
            lowest_need=min(satiety, energy, fun, social, affection),
        )
        if relationship is not None:
            relationship = advance_friendship(
                relationship, seconds, before,
                (satiety, energy, fun, social, affection), sleeping=record.sleeping,
                mood_before=mood_before, mood_after=mood, moodlets=moodlets,
            )
        if moodlets.active and not represented:
            moodlets = advance_moodlets(
                moodlets, seconds, elapsed=elapsed, before=before_needs,
                after=after_needs, definitions=definitions, observed=observed,
            )
        if relationship is not None and not represented:
            moodlets = qualify_poor_care(
                moodlets, relationship.history, elapsed=elapsed + seconds,
                before=before_needs, after=after_needs, sleeping=record.sleeping,
                definitions=definitions,
            )
            represented = poor_care_at_capacity(
                moodlets, after_needs, sleeping=record.sleeping,
                definitions=definitions,
            )
        if relationship is not None:
            moodlets = advance_long_term(
                moodlets, relationship.history, elapsed=elapsed + seconds,
                sleeping=record.sleeping,
            )
            represented = represented and poor_care_at_capacity(
                moodlets, after_needs, sleeping=record.sleeping,
                definitions=definitions,
            )
        elapsed += seconds
        remaining = max(0.0, endpoint - elapsed)
    return PetProgress(
        NeedLevels(satiety, energy, fun, social, affection), mood, food,
        moodlets, relationship,
    )
