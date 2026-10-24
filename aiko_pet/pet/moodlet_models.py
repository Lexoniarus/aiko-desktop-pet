"""Immutable Moodlet values, separate from timing and transition policies."""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from enum import StrEnum
from typing import TYPE_CHECKING, Literal

from .care_evidence import CareEvidenceState, CarePeriodSummary
from .interaction_events import InteractionMemory
from .moodlet_patterns import LongTermPatternParameters
from .moodlet_types import MoodletId, MoodletOutcome
from .need_exposure import ExposureMark

if TYPE_CHECKING:
    from .wish_types import WishTarget

MAX_MOODLET_CAUSES = 3


class MoodletPolarity(StrEnum):
    POSITIVE = "positive"
    NEGATIVE = "negative"


class MoodletAttribution(StrEnum):
    UNKNOWN = "unknown"
    USER = "user"
    AUTONOMOUS = "autonomous"


class MoodletCauseKind(StrEnum):
    LEGACY = "legacy"
    WISH_FULFILLED = "wish_fulfilled"
    WISH_FAILED = "wish_failed"
    INTERACTION = "interaction"
    POOR_CARE = "poor_care"
    LONG_TERM = "long_term"


@dataclass(frozen=True, slots=True)
class MoodletWishCause:
    """A retired wish snapshot; stable catalogue keys avoid a domain import cycle.

    The existing infrastructure codecs validate these keys against wish types
    and catalogue targets. No active-wish reference or rendered text is retained.
    """

    instance_id: int
    definition_id: str
    target_id: str
    objective: str
    required_count: int
    target: WishTarget | None = None


@dataclass(frozen=True, slots=True)
class MoodletGameResult:
    """The settled round and objective counts, all from Aiko's perspective."""

    round_outcome: MoodletOutcome
    completed_rounds: int
    wins: int
    losses: int


@dataclass(frozen=True, slots=True)
class MoodletCause:
    kind: MoodletCauseKind
    occurred_at: float
    event_id: str | None = None
    attribution: MoodletAttribution = MoodletAttribution.UNKNOWN
    wish: MoodletWishCause | None = None
    target_id: str | None = None
    outcome: MoodletOutcome = MoodletOutcome.UNKNOWN
    object_id: str | None = None
    game: MoodletGameResult | None = None
    period: CarePeriodSummary | None = None
    handed_over_at: float | None = None

    @property
    def receipt(self) -> tuple[MoodletCauseKind, str | None, int | None]:
        return self.kind, self.event_id, self.wish.instance_id if self.wish else None


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

    SAFE = "safe"
    OPTIMISTIC = "optimistic"
    UNCERTAIN = "uncertain"
    GUARDED = "guarded"


class MoodletGroup(StrEnum):
    FOOD_WISH = "food_wish"
    GAME_WISH = "game_wish"
    SOCIAL_WISH = "social_wish"
    AFFECTION_WISH = "affection_wish"
    INTERACTION = "interaction"
    POOR_CARE = "poor_care"
    GAME_SETBACK = "game_setback"
    FOOD_SETBACK = "food_setback"
    LONG_TERM = "long_term"


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
    accepted_excess_attempts: int
    trusted_friendship_level: int
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
    | WithholdingParameters | RelocationParameters | PoorCareParameters
    | LongTermPatternParameters | None
)


@dataclass(frozen=True, slots=True)
class MoodletDefinition:
    """Family metadata and fixed-stage duration, including the v1 wish fallback.

    New positive wish stages use the shared balance profile; the old fixed
    duration remains necessary to read already saved implicit lower stages.
    """

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
    def uses_positive_stage_budgets(self) -> bool:
        """Shared wish after-effects, distinct from fixed long-term stages."""
        return self.polarity == MoodletPolarity.POSITIVE and self.group in (
            MoodletGroup.FOOD_WISH, MoodletGroup.GAME_WISH,
            MoodletGroup.SOCIAL_WISH, MoodletGroup.AFFECTION_WISH,
        )

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
    Current-stage time stays in remaining_seconds; lower_stage_seconds stores
    levels one upward, excluding the current level. Empty means legacy implicit
    lower stages, never invented earned extensions.
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
    attribution: MoodletAttribution = MoodletAttribution.UNKNOWN
    causes: tuple[MoodletCause, ...] = ()
    lower_stage_seconds: tuple[float, ...] = ()

    def __post_init__(self) -> None:
        if not self.causes:
            object.__setattr__(self, "causes", (MoodletCause(
                MoodletCauseKind.LEGACY, self.last_trigger_at,
                attribution=self.attribution,
            ),))

        else:
            object.__setattr__(self, "causes", self.causes[-min(
                self.level, MAX_MOODLET_CAUSES,
            ):])

    def with_cause(self, cause: MoodletCause) -> MoodletEpisode:
        """Retain the latest real events up to current intensity (maximum three)."""
        if (not math.isfinite(cause.occurred_at)
                or not self.started_at <= cause.occurred_at <= self.last_trigger_at
                or cause.kind == MoodletCauseKind.LEGACY or not cause.event_id):
            raise ValueError("Moodlet cause must belong to its active episode")
        if any(c.receipt == cause.receipt for c in self.causes):
            return self
        known = tuple(c for c in self.causes if c.kind != MoodletCauseKind.LEGACY)
        if known and cause.occurred_at < known[-1].occurred_at:
            raise ValueError("Moodlet causes must follow event time")
        return replace(self, causes=(*known, cause))


@dataclass(frozen=True, slots=True)
class PoorCareCursor:
    accounted: ExposureMark
    handled: ExposureMark
    handled_level: int = 0
    exposed: bool = False


@dataclass(frozen=True, slots=True)
class PoorCareEvidence:
    baseline: float
    needs: tuple[PoorCareCursor, ...]


@dataclass(frozen=True, slots=True)
class MoodletState:
    """One entry per family, with no separate live store or emotional score.

    The baseline prevents old care history from becoming invented emotional
    evidence on migration. Instanced IDs are never reused after an episode ends.
    """

    baseline: float = 0.0
    next_instance_id: int = 1
    active: tuple[MoodletEpisode, ...] = ()
    interactions: InteractionMemory = InteractionMemory()
    poor_care: PoorCareEvidence | None = None
    care_evidence: CareEvidenceState | None = None


@dataclass(frozen=True, slots=True)
class MoodletContributions:
    """Separately capped signed numeric effects; episodes remain unchanged."""

    positive_points: float = 0.0
    negative_points: float = 0.0
