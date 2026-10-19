"""Need-derived mood target and real-time response, without feedback loops."""

from __future__ import annotations

import math
from dataclasses import dataclass

from .balance import BALANCE
from .value_rules import clamp_need_value


@dataclass(frozen=True, slots=True)
class NeedMoodAnchor:
    threshold: float
    deduction: float
    target_limit: float
    decline_points_per_minute: float


@dataclass(frozen=True, slots=True)
class MoodBalance:
    need_weight: float = BALANCE.number("mood", "need_weight")
    recovery_points_per_minute: float = BALANCE.number(
        "mood", "recovery_points_per_minute",
    )
    anchors: tuple[NeedMoodAnchor, ...] = tuple(
        NeedMoodAnchor(
            BALANCE.number("mood", f"{name}_need_threshold"),
            BALANCE.number("mood", f"{name}_need_deduction"),
            BALANCE.number("mood", f"{name}_need_target_limit"),
            BALANCE.number("mood", f"{name}_decline_points_per_minute"),
        )
        for name in ("zero", "critical", "low", "healthy")
    )


MOOD_BALANCE = MoodBalance()


@dataclass(frozen=True, slots=True)
class MoodFactors:
    """Only actual needs contribute; relationship and hardware are separate."""

    satiety: float
    energy: float
    fun: float
    social: float
    affection: float

    @property
    def needs(self) -> tuple[float, ...]:
        return tuple(clamp_need_value(value) for value in (
            self.satiety, self.energy, self.fun, self.social, self.affection,
        ))


def need_mood_factors(value: float) -> NeedMoodAnchor:
    """Interpolate shortage impact continuously between the JSON anchors."""
    value = clamp_need_value(value)
    anchors = MOOD_BALANCE.anchors
    if value <= anchors[0].threshold:
        return anchors[0]
    for low, high in zip(anchors, anchors[1:]):
        if value <= high.threshold:
            progress = (value - low.threshold) / (high.threshold - low.threshold)
            return NeedMoodAnchor(
                value,
                low.deduction + progress * (high.deduction - low.deduction),
                low.target_limit + progress * (high.target_limit - low.target_limit),
                low.decline_points_per_minute + progress * (
                    high.decline_points_per_minute - low.decline_points_per_minute
                ),
            )
    return anchors[-1]


def calculate_mood_target(factors: MoodFactors) -> float:
    """Sum deficits and respect the strongest limit; never duplicate Moodlets."""
    needs = factors.needs
    impacts = tuple(need_mood_factors(value) for value in needs)
    target = sum(needs) * MOOD_BALANCE.need_weight - sum(
        impact.deduction for impact in impacts
    )
    return max(0.0, min(target, *(impact.target_limit for impact in impacts)))


def advance_mood(
    current_mood: float, target_mood: float, hours: float, *, lowest_need: float,
) -> float:
    """Approach a constant target at bounded points/minute, without overshoot.

    The need policy subdivides changing needs chronologically. No care action,
    sleep flag or hardware sample causes an independent instant mood change.
    """
    current = clamp_need_value(current_mood)
    target = clamp_need_value(target_mood)
    if not math.isfinite(hours) or hours <= 0:
        return current
    if target >= current:
        return min(
            target,
            current + hours * 60 * MOOD_BALANCE.recovery_points_per_minute,
        )
    rate = need_mood_factors(lowest_need).decline_points_per_minute
    return max(target, current - hours * 60 * rate)
