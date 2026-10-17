"""Pure need-decay rules; the pet aggregate owns applying their results."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .balance import BALANCE
from .food import FoodActivity, FoodProgress, FoodState, advance_food
from .fun import advance_fun
from .mood import MoodFactors, advance_mood, calculate_mood_target
from .routine import TimeContext
from .value_rules import clamp_need_value


class NeedValues(Protocol):
    """Read-only need values; policies cannot write back to the pet."""

    @property
    def sleeping(self) -> bool: ...

    @property
    def satiety(self) -> float: ...

    @property
    def mood(self) -> float: ...

    @property
    def energy(self) -> float: ...

    @property
    def social(self) -> float: ...

    @property
    def affection(self) -> float: ...


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
    effort: float | None = None,
    *,
    food_activity: FoodActivity | None = None,
    food_progress: FoodProgress | None = None,
) -> NeedLevels:
    """Compute all needs while delegating hunger to the food policy."""
    progress = (
        food_progress
        if food_progress is not None
        else advance_food(
            getattr(record, "food", FoodState()),
            record.satiety,
            hours,
            sleeping=record.sleeping,
            activity=(
                food_activity
                if food_activity is not None
                else FoodActivity(hardware_load=effort or 0.0)
            ),
        )
    )
    if record.sleeping:
        energy = clamp_need_value(
            record.energy
            + hours * BALANCE.number("needs", "sleeping_energy_gain_per_hour")
        )
        social = clamp_need_value(
            record.social
            - hours * BALANCE.number("needs", "sleeping_social_loss_per_hour")
        )
        affection = clamp_need_value(
            record.affection
            - hours * BALANCE.number("needs", "sleeping_affection_loss_per_hour")
        )
        intensity = 0.0
    else:
        # Verified CPU/GPU work adds strain; fun itself is independent.
        intensity = (
            0.0
            if effort is None
            else max(
                0.0,
                min(
                    1.0,
                    (effort - BALANCE.number("needs", "hardware_intensity_baseline"))
                    / BALANCE.number("needs", "hardware_intensity_span"),
                ),
            )
        )
        energy = clamp_need_value(
            record.energy
            - hours
            * (
                BALANCE.number("needs", "awake_energy_loss_per_hour")
                + BALANCE.number("needs", "hardware_energy_loss_per_hour") * intensity
            )
        )
        social = clamp_need_value(
            record.social
            - hours
            * (
                BALANCE.number("needs", "awake_social_loss_per_hour")
                + BALANCE.number("needs", "hardware_social_loss_per_hour") * intensity
            )
        )
        affection = clamp_need_value(
            record.affection
            - hours * BALANCE.number("needs", "awake_affection_loss_per_hour")
        )
    next_fun = advance_fun(
        getattr(record, "fun", BALANCE.number("initial", "fun")),
        hours,
        sleeping=record.sleeping,
    )
    target = calculate_mood_target(
        MoodFactors(
            satiety=progress.satiety,
            energy=energy,
            fun=next_fun,
            social=social,
            affection=affection,
            friendship=getattr(
                record, "friendship", BALANCE.number("initial", "friendship")
            ),
            workload_intensity=intensity,
        )
    )
    return NeedLevels(
        satiety=progress.satiety,
        mood=advance_mood(
            record.mood,
            target,
            hours,
            sleeping=record.sleeping,
        ),
        energy=energy,
        social=social,
        affection=affection,
    )
