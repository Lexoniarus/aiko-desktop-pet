"""Aiko's overall mood is a smoothed consequence, not another care need.

Needs and lived workload can affect mood. Mood never modifies enjoyment,
nutrition, energy, affection, social need, friendship or game scoring.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .balance import BALANCE
from .value_rules import clamp_need_value


@dataclass(frozen=True, slots=True)
class MoodBalance:
    """Editable, named contributions to Aiko's aggregate emotional state."""

    fun_weight: float = BALANCE.number("mood", "fun_weight")
    satiety_weight: float = BALANCE.number("mood", "satiety_weight")
    energy_weight: float = BALANCE.number("mood", "energy_weight")
    social_weight: float = BALANCE.number("mood", "social_weight")
    affection_weight: float = BALANCE.number("mood", "affection_weight")
    friendship_bonus_per_point_above_start: float = BALANCE.number(
        "mood", "friendship_bonus_per_point_above_start"
    )
    initial_friendship_points: float = BALANCE.number(
        "mood", "initial_friendship_points"
    )
    critical_need_threshold: float = BALANCE.number("mood", "critical_need_threshold")
    critical_need_penalty_per_missing_point: float = BALANCE.number(
        "mood", "critical_need_penalty_per_missing_point"
    )
    workload_mood_penalty_at_full_intensity: float = BALANCE.number(
        "mood", "workload_mood_penalty_at_full_intensity"
    )
    awake_mood_adjustment_speed_per_hour: float = BALANCE.number(
        "mood", "awake_mood_adjustment_speed_per_hour"
    )
    sleeping_mood_adjustment_speed_per_hour: float = BALANCE.number(
        "mood", "sleeping_mood_adjustment_speed_per_hour"
    )
    immediate_care_alignment_fraction: float = BALANCE.number(
        "mood", "immediate_care_alignment_fraction"
    )
    immediate_experience_impact_fraction: float = BALANCE.number(
        "mood", "immediate_experience_impact_fraction"
    )
    maximum_immediate_experience_points: float = BALANCE.number(
        "mood", "maximum_immediate_experience_points"
    )


MOOD_BALANCE = MoodBalance()


@dataclass(frozen=True, slots=True)
class MoodFactors:
    """The actual needs, friendship and workload, never the current mood."""

    satiety: float
    energy: float
    fun: float
    social: float
    affection: float
    friendship: float = BALANCE.number("initial", "friendship")
    workload_intensity: float = 0.0


def calculate_mood_target(factors: MoodFactors) -> float:
    """Combine needs and critical shortages, without feedback into needs."""
    balance = MOOD_BALANCE
    target = (
        factors.fun * balance.fun_weight
        + factors.satiety * balance.satiety_weight
        + factors.energy * balance.energy_weight
        + factors.social * balance.social_weight
        + factors.affection * balance.affection_weight
    )
    target += (
        max(
            0.0,
            factors.friendship - balance.initial_friendship_points,
        )
        * balance.friendship_bonus_per_point_above_start
    )
    lowest_need = min(
        factors.fun,
        factors.satiety,
        factors.energy,
        factors.social,
        factors.affection,
    )
    target -= (
        max(
            0.0,
            balance.critical_need_threshold - lowest_need,
        )
        * balance.critical_need_penalty_per_missing_point
    )
    target -= (
        max(0.0, min(1.0, factors.workload_intensity))
        * balance.workload_mood_penalty_at_full_intensity
    )
    return clamp_need_value(target)


def advance_mood(
    current_mood: float,
    target_mood: float,
    hours: float,
    *,
    sleeping: bool,
) -> float:
    """Approach the overall state smoothly instead of applying flat decay."""
    if not math.isfinite(hours) or hours <= 0:
        return clamp_need_value(current_mood)
    speed = (
        MOOD_BALANCE.sleeping_mood_adjustment_speed_per_hour
        if sleeping
        else MOOD_BALANCE.awake_mood_adjustment_speed_per_hour
    )
    progress = 1.0 - math.exp(-speed * hours)
    return clamp_need_value(
        current_mood + (target_mood - current_mood) * progress,
    )


def reflect_care_in_mood(
    current_mood: float,
    target_mood: float,
    *,
    experience_points: float = 0.0,
) -> float:
    """Small immediate response to care; the ordinary target later prevails."""
    balance = MOOD_BALANCE
    experience = max(
        -balance.maximum_immediate_experience_points,
        min(balance.maximum_immediate_experience_points, experience_points),
    )
    return clamp_need_value(
        current_mood
        + (target_mood - current_mood) * balance.immediate_care_alignment_fraction
        + experience * balance.immediate_experience_impact_fraction
    )
