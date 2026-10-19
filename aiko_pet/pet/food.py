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
    maximum_digest_hunger_reduction: float = BALANCE.number(
        "food", "maximum_digest_hunger_reduction"
    )
    digest_minutes_for_full_hunger_reduction: float = BALANCE.number(
        "food", "digest_minutes_for_full_hunger_reduction"
    )
    maximum_digest_reserve_minutes: float = BALANCE.number(
        "food", "maximum_digest_reserve_minutes"
    )
    digestion_speed_during_sleep: float = BALANCE.number(
        "food", "digestion_speed_during_sleep"
    )
    consecutive_repeats_before_dislike: int = BALANCE.integer(
        "food", "consecutive_repeats_before_dislike"
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
        return FoodIntake(False, current_satiety, food, False)
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
    return FoodIntake(
        accepted=True,
        satiety=clamp_need_value(
            current_satiety + profile.instant_satiety_points,
        ),
        food=updated,
        repetitive=repetitive,
    )


def hardware_consumption_fraction(load: float) -> float:
    """Map smoothed CPU/GPU utilization above the common threshold to 0..1."""
    baseline = BALANCE.number("needs", "hardware_intensity_baseline")
    span = BALANCE.number("needs", "hardware_intensity_span")
    return max(0.0, min(1.0, (bounded_number(load, 0.0, 1.0) - baseline) / span))


def hunger_activity_multiplier(activity: FoodActivity) -> float:
    """Base hunger always applies; CPU/GPU and actual input add bounded costs."""
    hardware = hardware_consumption_fraction(activity.hardware_load)
    user = bounded_number(activity.user_input_activity, 0.0, 1.0)
    bonus = min(
        FOOD_BALANCE.maximum_combined_activity_bonus,
        hardware * FOOD_BALANCE.maximum_hardware_hunger_bonus
        + user * FOOD_BALANCE.maximum_user_input_hunger_bonus,
    )
    return 1.0 + bonus


def advance_food(
    food: FoodState,
    satiety: float,
    hours: float,
    *,
    sleeping: bool,
    activity: FoodActivity | None = None,
) -> FoodProgress:
    """Integrate the linear reserve fade exactly, independent of tick length.

    The aggregate supplies elapsed life time, including closed/standby time.
    This method never reads clocks or reconstructs observations itself.
    """
    if not math.isfinite(hours) or hours <= 0.0:
        return FoodProgress(satiety, food)
    observed = activity if activity is not None else FoodActivity()
    minutes = hours * 60.0
    reserve = max(0.0, food.remaining_digest_minutes)
    if sleeping:
        loss = hours * FOOD_BALANCE.sleeping_hunger_points_per_hour
        result = replace(food, remaining_digest_minutes=max(
            0.0, reserve - minutes * FOOD_BALANCE.digestion_speed_during_sleep,
        ))
    else:
        anchor = FOOD_BALANCE.digest_minutes_for_full_hunger_reduction
        full_minutes = min(minutes, max(0.0, reserve - anchor))
        fade_reserve = min(reserve, anchor)
        fade_minutes = min(minutes - full_minutes, fade_reserve)
        protected_minutes = full_minutes + (
            fade_reserve * fade_minutes - fade_minutes * fade_minutes / 2
        ) / anchor
        effective_hours = (
            minutes - FOOD_BALANCE.maximum_digest_hunger_reduction * protected_minutes
        ) / 60.0
        loss = (
            FOOD_BALANCE.awake_hunger_points_per_hour
            * hunger_activity_multiplier(observed) * effective_hours
        )
        result = replace(
            food, remaining_digest_minutes=max(0.0, reserve - minutes),
            awake_hours_since_last_food=food.awake_hours_since_last_food + hours,
            awake_hours_since_main_meal=food.awake_hours_since_main_meal + hours,
        )
    return FoodProgress(clamp_need_value(satiety - loss), result)
