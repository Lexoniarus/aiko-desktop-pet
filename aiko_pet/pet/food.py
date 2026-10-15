"""Food-only hunger, digestion and meal variety rules.

Transition rules stay in Python; balance values, nutrition profiles and menu
order live in validated JSON catalogues. No Tk, desktop or dialogue is imported.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace

from .balance import BALANCE
from .food_catalog import (
    DEFAULT_CATALOG,
)
from .food_catalog import (
    FoodCategory as FoodCategory,
)
from .food_catalog import (
    FoodId as FoodId,
)
from .food_catalog import (
    FoodProfile as FoodProfile,
)
from .value_rules import bounded_number, clamp_need_value


@dataclass(frozen=True, slots=True)
class FoodBalance:
    """Hours, minutes and 0..1 rates make gameplay tuning readable."""

    awake_hunger_points_per_hour: float = BALANCE.number(
        "food", "awake_hunger_points_per_hour"
    )
    sleeping_hunger_points_per_hour: float = BALANCE.number(
        "food", "sleeping_hunger_points_per_hour"
    )
    maximum_hardware_hunger_bonus: float = BALANCE.number(
        "food", "maximum_hardware_hunger_bonus"
    )
    maximum_user_input_hunger_bonus: float = BALANCE.number(
        "food", "maximum_user_input_hunger_bonus"
    )
    maximum_combined_activity_bonus: float = BALANCE.number(
        "food", "maximum_combined_activity_bonus"
    )
    awake_hours_before_hunger_accelerates: float = BALANCE.number(
        "food", "awake_hours_before_hunger_accelerates"
    )
    additional_hunger_fraction_per_hour_without_food: float = BALANCE.number(
        "food", "additional_hunger_fraction_per_hour_without_food"
    )
    maximum_long_fast_hunger_bonus: float = BALANCE.number(
        "food", "maximum_long_fast_hunger_bonus"
    )
    maximum_digest_hunger_reduction: float = BALANCE.number(
        "food", "maximum_digest_hunger_reduction"
    )
    digest_minutes_for_full_hunger_reduction: float = BALANCE.number(
        "food", "digest_minutes_for_full_hunger_reduction"
    )
    maximum_digest_reserve_minutes: float = BALANCE.number(
        "food", "maximum_digest_reserve_minutes"
    )
    digestion_speedup_from_activity: float = BALANCE.number(
        "food", "digestion_speedup_from_activity"
    )
    digestion_speed_during_sleep: float = BALANCE.number(
        "food", "digestion_speed_during_sleep"
    )
    internal_simulation_step_minutes: float = BALANCE.number(
        "food", "internal_simulation_step_minutes"
    )
    consecutive_repeats_before_dislike: int = BALANCE.integer(
        "food", "consecutive_repeats_before_dislike"
    )
    repeated_food_mood_penalty: float = BALANCE.number(
        "food", "repeated_food_mood_penalty"
    )
    maximum_recent_foods: int = BALANCE.integer("food", "maximum_recent_foods")
    too_full_to_eat_threshold: float = BALANCE.number(
        "food", "too_full_to_eat_threshold"
    )


FOOD_BALANCE = FoodBalance()


FOOD_CATALOG = DEFAULT_CATALOG.foods
DEFAULT_FOOD_ID: FoodId = DEFAULT_CATALOG.default_food_id
FOOD_MENU_ORDER = DEFAULT_CATALOG.menu_order


@dataclass(frozen=True, slots=True)
class FoodActivity:
    """Observed work, never guessed task identity or unseen user activity."""

    hardware_load: float = 0.0
    user_input_activity: float = 0.0


@dataclass(frozen=True, slots=True)
class FoodState:
    """Session-progressing nutrition values, independent of storage format."""

    remaining_digest_minutes: float = 0.0
    awake_hours_since_last_food: float = 0.0
    awake_hours_since_main_meal: float = 0.0
    recent_food_ids: tuple[FoodId, ...] = ()

    @property
    def last_food_id(self) -> FoodId | None:
        return self.recent_food_ids[-1] if self.recent_food_ids else None


@dataclass(frozen=True, slots=True)
class FoodIntake:
    """One food selection's immediate, atomic domain outcome."""

    accepted: bool
    satiety: float
    mood_change: float
    food: FoodState
    repetitive: bool


@dataclass(frozen=True, slots=True)
class FoodProgress:
    """Both hunger and the remaining digestive effect after elapsed time."""

    satiety: float
    food: FoodState


def is_repeated_food(food: FoodState, food_id: FoodId) -> bool:
    """Dislike starts after consecutive identical servings, not one repeat."""
    threshold = FOOD_BALANCE.consecutive_repeats_before_dislike
    return len(food.recent_food_ids) >= threshold and all(
        item == food_id for item in food.recent_food_ids[-threshold:]
    )


def eat_food(
    food: FoodState,
    current_satiety: float,
    food_id: FoodId,
) -> FoodIntake:
    """Add satiety and digest reserve; a snack does not count as a full meal."""
    profile = FOOD_CATALOG[food_id]
    if current_satiety >= FOOD_BALANCE.too_full_to_eat_threshold:
        return FoodIntake(False, current_satiety, 0.0, food, False)
    repetitive = is_repeated_food(food, food_id)
    history = (*food.recent_food_ids, food_id)
    updated = replace(
        food,
        remaining_digest_minutes=min(
            FOOD_BALANCE.maximum_digest_reserve_minutes,
            food.remaining_digest_minutes + profile.digest_reserve_minutes,
        ),
        awake_hours_since_last_food=0.0,
        awake_hours_since_main_meal=(
            0.0 if profile.category == "meal" else food.awake_hours_since_main_meal
        ),
        recent_food_ids=history[-FOOD_BALANCE.maximum_recent_foods :],
    )
    mood_change = profile.normal_mood_bonus - (
        FOOD_BALANCE.repeated_food_mood_penalty if repetitive else 0.0
    )
    return FoodIntake(
        accepted=True,
        satiety=clamp_need_value(
            current_satiety + profile.instant_satiety_points,
        ),
        mood_change=mood_change,
        food=updated,
        repetitive=repetitive,
    )


def hunger_activity_multiplier(activity: FoodActivity) -> float:
    """CPU/GPU/RAM work and real user inputs each add bounded hunger."""
    hardware = bounded_number(activity.hardware_load, 0.0, 1.0)
    user = bounded_number(activity.user_input_activity, 0.0, 1.0)
    bonus = min(
        FOOD_BALANCE.maximum_combined_activity_bonus,
        hardware * FOOD_BALANCE.maximum_hardware_hunger_bonus
        + user * FOOD_BALANCE.maximum_user_input_hunger_bonus,
    )
    return 1.0 + bonus


def hunger_after_long_food_break(awake_hours_since_food: float) -> float:
    """Late hunger increases gently and stops increasing at a fixed cap."""
    overdue = max(
        0.0,
        awake_hours_since_food - FOOD_BALANCE.awake_hours_before_hunger_accelerates,
    )
    return 1.0 + min(
        FOOD_BALANCE.maximum_long_fast_hunger_bonus,
        overdue * FOOD_BALANCE.additional_hunger_fraction_per_hour_without_food,
    )


def digestion_hunger_multiplier(remaining_minutes: float) -> float:
    """Nutrition slows decay progressively until the reserve is exhausted."""
    fullness = min(
        1.0,
        max(0.0, remaining_minutes)
        / FOOD_BALANCE.digest_minutes_for_full_hunger_reduction,
    )
    return 1.0 - FOOD_BALANCE.maximum_digest_hunger_reduction * fullness


def advance_food(
    food: FoodState,
    satiety: float,
    hours: float,
    *,
    sleeping: bool,
    activity: FoodActivity | None = None,
) -> FoodProgress:
    """Integrate digestion and hunger in five-minute steps, not once per tick.

    All input time comes from the host's *active session clock*. This method
    never computes the gap from wall timestamps after a program restart.
    """
    if not math.isfinite(hours) or hours <= 0.0:
        return FoodProgress(satiety, food)
    observed = activity if activity is not None else FoodActivity()
    activity_multiplier = hunger_activity_multiplier(observed)
    remainder = hours
    result = food
    hunger = satiety
    step_limit = FOOD_BALANCE.internal_simulation_step_minutes / 60.0
    while remainder > 1e-9:
        step = min(step_limit, remainder)
        if sleeping:
            rate = FOOD_BALANCE.sleeping_hunger_points_per_hour
            digestion_speed = FOOD_BALANCE.digestion_speed_during_sleep
            result = replace(
                result,
                remaining_digest_minutes=max(
                    0.0,
                    result.remaining_digest_minutes - step * 60.0 * digestion_speed,
                ),
            )
        else:
            rate = (
                FOOD_BALANCE.awake_hunger_points_per_hour
                * activity_multiplier
                * hunger_after_long_food_break(
                    result.awake_hours_since_last_food,
                )
                * digestion_hunger_multiplier(
                    result.remaining_digest_minutes,
                )
            )
            digestion_speed = 1.0 + FOOD_BALANCE.digestion_speedup_from_activity * (
                activity_multiplier - 1.0
            )
            result = replace(
                result,
                remaining_digest_minutes=max(
                    0.0,
                    result.remaining_digest_minutes - step * 60.0 * digestion_speed,
                ),
                awake_hours_since_last_food=(result.awake_hours_since_last_food + step),
                awake_hours_since_main_meal=(result.awake_hours_since_main_meal + step),
            )
        hunger = clamp_need_value(hunger - step * rate)
        remainder -= step
    return FoodProgress(hunger, result)
