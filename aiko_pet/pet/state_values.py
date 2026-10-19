"""Immutable, complete PetState checkpoint and prepared consumption result.

The checkpoint is a value, not another live pet. Collection histories are tuples
so neither callers nor recovery paths can mutate a captured state in place.
"""

from __future__ import annotations

from dataclasses import dataclass

from .care_result import CareResult
from .food import FoodState
from .friendship_history import FriendshipHistory
from .sleep import SleepEpisode


@dataclass(frozen=True, slots=True)
class PetValues:
    """All persisted pet fields, independent of live mutable collections."""

    satiety: float
    mood: float
    energy: float
    social: float
    affection: float
    friendship: float
    friendship_day: str
    friendship_gained_today: float
    care_types_today: tuple[str, ...]
    care_last_rewards: tuple[tuple[str, float], ...]
    sleeping: bool
    updated_at: float
    meals_date: str
    meals_today: tuple[str, ...]
    sleep_origin: str
    auto_sleep_night: str
    nap_until: float
    auto_nap_day: str
    food: FoodState
    fun: float
    lived_seconds: float = 0.0
    relationship: FriendshipHistory = FriendshipHistory()
    sleep_episode: SleepEpisode = SleepEpisode()


@dataclass(frozen=True, slots=True)
class PreparedItemConsumption:
    """Accepted canonical care result and complete proposed pet checkpoint."""

    checkpoint: PetValues
    result: CareResult
