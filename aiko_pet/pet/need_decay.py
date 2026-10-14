"""Pure need-decay rules; the pet aggregate owns applying their results."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .food import FoodActivity, FoodProgress, FoodState, advance_food
from .fun import advance_fun
from .mood import MoodFactors, advance_mood, calculate_mood_target
from .routine import TimeContext
from .value_rules import clamp_need_value


class NeedValues(Protocol):
    """Required current values, readable without a concrete PetState."""

    sleeping: bool
    satiety: float
    mood: float
    energy: float
    social: float
    affection: float


@dataclass(frozen=True, slots=True)
class NeedLevels:
    """Calculated next values, not a mutable reference to the pet."""

    satiety: float
    mood: float
    energy: float
    social: float
    affection: float


def calculate_need_decay(
    record: NeedValues,
    hours: float,
    context: TimeContext | None,
    effort: float | None = None, *,
    food_activity: FoodActivity | None = None,
    food_progress: FoodProgress | None = None,
) -> NeedLevels:
    """Compute all needs while delegating hunger to the food policy."""
    progress = food_progress if food_progress is not None else advance_food(
        getattr(record, "food", FoodState()), record.satiety, hours,
        sleeping=record.sleeping,
        activity=(
            food_activity if food_activity is not None
            else FoodActivity(hardware_load=effort or 0.0)
        ),
    )
    if record.sleeping:
        energy = clamp_need_value(record.energy + hours * 22.0)
        social = clamp_need_value(record.social - hours * 0.35)
        affection = clamp_need_value(record.affection - hours * 0.25)
        intensity = 0.0
    else:
        # Verified CPU/GPU work adds strain; fun itself is independent.
        intensity = 0.0 if effort is None else max(
            0.0, min(1.0, (effort - 0.15) / 0.85),
        )
        energy = clamp_need_value(record.energy - hours * (
            6.0 + 2.8 * intensity
        ))
        social = clamp_need_value(record.social - hours * (
            8.0 + 0.35 * intensity
        ))
        affection = clamp_need_value(record.affection - hours * 6.0)
    next_fun = advance_fun(
        getattr(record, "fun", 75.0), hours, sleeping=record.sleeping,
    )
    target = calculate_mood_target(MoodFactors(
        satiety=progress.satiety, energy=energy, fun=next_fun,
        social=social, affection=affection,
        friendship=getattr(record, "friendship", 15.0),
        workload_intensity=intensity,
    ))
    return NeedLevels(
        satiety=progress.satiety,
        mood=advance_mood(
            record.mood, target, hours, sleeping=record.sleeping,
        ),
        energy=energy, social=social, affection=affection,
    )


def apply_need_decay(
    record: NeedValues, hours: float,
    context: TimeContext | None, effort: float | None = None,
) -> None:
    """Legacy mutable-record adapter; PetState applies calculations itself."""
    food = getattr(record, "food", None)
    food_progress = (
        advance_food(
            food, record.satiety, hours, sleeping=record.sleeping,
            activity=FoodActivity(hardware_load=effort or 0.0),
        )
        if isinstance(food, FoodState) else None
    )
    next_values = calculate_need_decay(
        record, hours, context, effort, food_progress=food_progress,
    )
    record.satiety = next_values.satiety
    if food_progress is not None:
        setattr(record, "food", food_progress.food)
    record.mood = next_values.mood
    record.energy = next_values.energy
    record.social = next_values.social
    record.affection = next_values.affection
    if hasattr(record, "fun"):
        setattr(record, "fun", advance_fun(
            getattr(record, "fun"), hours, sleeping=record.sleeping,
        ))
