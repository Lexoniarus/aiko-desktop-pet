"""Game-independent enjoyment rules; no Tk, game engine or mood imports.

Tune the active-day need and each game's completed-unit rewards in balance.json.
Three to four short play sessions with two to three rounds each should
roughly balance a normal sixteen-hour awake day. No window-time rewards.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .balance import BALANCE
from .value_rules import clamp_need_value


@dataclass(frozen=True, slots=True)
class FunBalance:
    """Editable global enjoyment policy, using hours and need points."""

    awake_fun_loss_points_per_hour: float = BALANCE.number(
        "fun", "awake_fun_loss_points_per_hour"
    )
    sleeping_fun_loss_points_per_hour: float = BALANCE.number(
        "fun", "sleeping_fun_loss_points_per_hour"
    )
    full_reward_units_per_session: int = BALANCE.integer(
        "fun", "full_reward_units_per_session"
    )
    middle_reward_units_per_session: int = BALANCE.integer(
        "fun", "middle_reward_units_per_session"
    )
    middle_unit_reward_fraction: float = BALANCE.number(
        "fun", "middle_unit_reward_fraction"
    )
    late_unit_reward_fraction: float = BALANCE.number(
        "fun", "late_unit_reward_fraction"
    )
    maximum_fun_gain_per_session: float = BALANCE.number(
        "fun", "maximum_fun_gain_per_session"
    )
    high_fun_threshold: float = BALANCE.number("fun", "high_fun_threshold")
    reward_fraction_at_full_fun: float = BALANCE.number(
        "fun", "reward_fraction_at_full_fun"
    )


FUN_BALANCE = FunBalance()


@dataclass(frozen=True, slots=True)
class GameFunProfile:
    """Per-game meaning of one completed unit and of the game's outcomes."""

    base_fun_per_completed_unit: float
    successful_unit_bonus: float
    neutral_unit_bonus: float
    setback_unit_bonus: float
    energy_cost_per_completed_unit: float
    social_gain_per_completed_unit: float


GAME_FUN_PROFILES: dict[str, GameFunProfile] = {
    "rock_paper_scissors": GameFunProfile(
        base_fun_per_completed_unit=BALANCE.number(
            "game_rock_paper_scissors", "base_fun_per_completed_unit"
        ),
        successful_unit_bonus=BALANCE.number(
            "game_rock_paper_scissors", "successful_unit_bonus"
        ),
        neutral_unit_bonus=BALANCE.number(
            "game_rock_paper_scissors", "neutral_unit_bonus"
        ),
        setback_unit_bonus=BALANCE.number(
            "game_rock_paper_scissors", "setback_unit_bonus"
        ),
        energy_cost_per_completed_unit=BALANCE.number(
            "game_rock_paper_scissors", "energy_cost_per_completed_unit"
        ),
        social_gain_per_completed_unit=BALANCE.number(
            "game_rock_paper_scissors", "social_gain_per_completed_unit"
        ),
    ),
}


@dataclass(frozen=True, slots=True)
class GameExperience:
    """A neutral summary of completed game units, not a session history.

    A success or setback is interpreted from Aiko's perspective by each
    game's application adapter. Unclassified units still count as play.
    """

    game_id: str
    completed_units: int
    successful_units: int = 0
    neutral_units: int = 0
    setback_units: int = 0

    def __post_init__(self) -> None:
        counts = (
            self.completed_units,
            self.successful_units,
            self.neutral_units,
            self.setback_units,
        )
        if not self.game_id or any(
            type(number) is not int or number < 0 for number in counts
        ):
            raise ValueError("Game experience requires valid unit counts")
        if sum(counts[1:]) > self.completed_units:
            raise ValueError("Game outcomes exceed completed units")


@dataclass(frozen=True, slots=True)
class FunReward:
    """Pure result; the pet aggregate decides when to commit it."""

    fun_points: float
    energy_cost: float
    social_gain: float


def advance_fun(current_fun: float, hours: float, *, sleeping: bool) -> float:
    """Use only simulated active session time; sleeping cannot create boredom."""
    if not math.isfinite(hours) or hours <= 0:
        return clamp_need_value(current_fun)
    rate = (
        FUN_BALANCE.sleeping_fun_loss_points_per_hour
        if sleeping
        else FUN_BALANCE.awake_fun_loss_points_per_hour
    )
    return clamp_need_value(current_fun - hours * rate)


def completed_unit_reward_fraction(completed_units: int) -> float:
    """Diminish long sessions without storing results after their closure."""
    if completed_units <= 0:
        return 0.0
    balance = FUN_BALANCE
    full = min(completed_units, balance.full_reward_units_per_session)
    middle = max(
        0,
        min(completed_units, balance.middle_reward_units_per_session)
        - balance.full_reward_units_per_session,
    )
    late = max(0, completed_units - balance.middle_reward_units_per_session)
    weighted_units = (
        full
        + middle * balance.middle_unit_reward_fraction
        + late * balance.late_unit_reward_fraction
    )
    return weighted_units / completed_units


def satisfaction_reward_fraction(current_fun: float) -> float:
    """Already entertained Aiko gains less, without a game-history timer."""
    start = FUN_BALANCE.high_fun_threshold
    if current_fun <= start:
        return 1.0
    progress = min(1.0, (current_fun - start) / (100.0 - start))
    return 1.0 - progress * (1.0 - FUN_BALANCE.reward_fraction_at_full_fun)


def calculate_game_session_fun(
    experience: GameExperience,
    current_fun: float,
) -> FunReward:
    """Award actual completed play, never an open window or pending round."""
    if experience.completed_units == 0:
        return FunReward(0.0, 0.0, 0.0)
    profile = GAME_FUN_PROFILES[experience.game_id]
    points = (
        experience.completed_units * profile.base_fun_per_completed_unit
        + experience.successful_units * profile.successful_unit_bonus
        + experience.neutral_units * profile.neutral_unit_bonus
        + experience.setback_units * profile.setback_unit_bonus
    )
    points *= completed_unit_reward_fraction(experience.completed_units)
    points *= satisfaction_reward_fraction(current_fun)
    points = min(FUN_BALANCE.maximum_fun_gain_per_session, points)
    return FunReward(
        fun_points=max(0.0, points),
        energy_cost=(
            experience.completed_units * profile.energy_cost_per_completed_unit
        ),
        social_gain=(
            experience.completed_units * profile.social_gain_per_completed_unit
        ),
    )
