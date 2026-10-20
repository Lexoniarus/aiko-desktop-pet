"""Immutable Moodlet definitions and aggregate-owned episode values.

Emotional directions describe individual impressions, not the derived overall
emotional state. None of these values owns a timer or mutable pet collection.
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Literal


class MoodletId(StrEnum):
    FOOD_FULFILLED = "food_fulfilled"
    SHARED_PLAY = "shared_play"
    PRIDE = "pride"
    RELIEF = "relief"
    CONNECTION = "connection"
    CHEERFUL = "cheerful"
    ENTHUSIASTIC = "enthusiastic"
    SECURE = "secure"
    POKING = "poking"
    CROWDED = "crowded"
    FOOD_MONOTONY = "food_monotony"
    WITHHELD = "withheld"
    DISRUPTED = "disrupted"
    HUNGER_WORN = "hunger_worn"
    EXHAUSTION_IRRITATED = "exhaustion_irritated"
    UNSTIMULATED = "unstimulated"
    LONELY = "lonely"
    MISSING_CLOSENESS = "missing_closeness"


class MoodletPolarity(StrEnum):
    POSITIVE = "positive"
    NEGATIVE = "negative"


class EmotionalDirection(StrEnum):
    CHEERFUL = "cheerful"
    PROUD = "proud"
    RELIEVED = "relieved"
    AFFECTIONATE = "affectionate"
    IRRITATED = "irritated"
    CROWDED = "crowded"
    FRUSTRATED = "frustrated"
    DOWNCAST = "downcast"
    LONELY = "lonely"


class MoodletGroup(StrEnum):
    FOOD_WISH = "food_wish"
    GAME_WISH = "game_wish"
    SOCIAL_WISH = "social_wish"
    AFFECTION_WISH = "affection_wish"
    INTERACTION = "interaction"
    POOR_CARE = "poor_care"


class MoodletDecay(StrEnum):
    QUIET_TIME = "quiet_time"
    RESOLVED_QUIET_TIME = "resolved_quiet_time"
    STABLE_RECOVERY = "stable_recovery"


@dataclass(frozen=True, slots=True)
class PokingParameters:
    escalation_pokes: int


@dataclass(frozen=True, slots=True)
class PettingTolerance:
    maximum_friendship_level: int
    affection_threshold: float


@dataclass(frozen=True, slots=True)
class PettingParameters:
    escalation_attempts: int
    boundary_window_seconds: int
    refusal_seconds: tuple[int, ...]
    tolerances: tuple[PettingTolerance, ...]
    friendship_loss_points: float
    friendship_loss_cap_points: float
    friendship_loss_window_seconds: int


@dataclass(frozen=True, slots=True)
class FoodMonotonyParameters:
    """The intake count still comes from the existing food balance owner."""

    sequence_window_seconds: int
    request_lifetime_seconds: int
    free_ignored_portions: int
    friendship_loss_points: float
    friendship_loss_cap_points: float
    friendship_loss_window_seconds: int


@dataclass(frozen=True, slots=True)
class WithholdingParameters:
    """Initial irritation and direct loss retain object-withholding ownership."""

    escalation_seconds: int


@dataclass(frozen=True, slots=True)
class RelocationParameters:
    friendship_loss_points: float
    friendship_loss_cap_points: float
    friendship_loss_window_seconds: int


@dataclass(frozen=True, slots=True)
class PoorCareParameters:
    """Shared exposure/recovery thresholds belong to the balance catalogue."""

    need: Literal["satiety", "energy", "fun", "social", "affection"]


MoodletParameters = (
    PokingParameters | PettingParameters | FoodMonotonyParameters
    | WithholdingParameters | RelocationParameters | PoorCareParameters | None
)


@dataclass(frozen=True, slots=True)
class MoodletDefinition:
    id: MoodletId
    polarity: MoodletPolarity
    direction: EmotionalDirection
    group: MoodletGroup
    level_points: tuple[int, ...]
    decay: MoodletDecay
    decay_stage_seconds: int
    relief_seconds: int
    parameters: MoodletParameters

    @property
    def label_key(self) -> str:
        return f"moodlet.{self.id}.label"

    @property
    def description_key(self) -> str:
        return f"moodlet.{self.id}.description"


@dataclass(frozen=True, slots=True)
class MoodletEpisode:
    """Remaining stage time is anchored at the owning pet's lived_seconds.

    Relief usage belongs to this entire episode, including refresh, escalation
    and paused recovery. These values do not themselves advance any clock.
    """

    instance_id: int
    definition_id: MoodletId
    level: int
    started_at: float
    last_trigger_at: float
    remaining_seconds: float
    relieved_levels: tuple[int, ...] = ()
    pending_repetitions: int = 0
    decay_paused: bool = False
    recovery_since: float | None = None


@dataclass(frozen=True, slots=True)
class MoodletState:
    """One entry per family, with no separate live store or emotional score.

    The baseline prevents old care history from becoming invented emotional
    evidence on migration. Instanced IDs are never reused after an episode ends.
    """

    baseline: float = 0.0
    next_instance_id: int = 1
    active: tuple[MoodletEpisode, ...] = ()
