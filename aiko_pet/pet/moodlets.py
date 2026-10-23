"""Immutable Moodlet definitions and aggregate-owned episode values.

Emotional directions describe individual impressions, not the derived overall
emotional state. None of these values owns a timer or mutable pet collection.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from enum import StrEnum
from typing import TYPE_CHECKING, Literal, Mapping

from .balance import BALANCE
from .care_evidence import CareEvidenceState, CarePeriodSummary
from .interaction_events import InteractionMemory
from .moodlet_patterns import LongTermPatternParameters
from .need_exposure import ExposureMark
from .needs import NeedLevels

if TYPE_CHECKING:
    from .wishes import WishTarget

MAX_MOODLET_CAUSES = 3


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
    DISAPPOINTED = "disappointed"
    FOOD_WISH_DISREGARDED = "food_wish_disregarded"
    TRUSTING = "trusting"
    APPRECIATED = "appreciated"
    OPTIMISTIC = "optimistic"
    UNCERTAIN = "uncertain"
    OVERLOOKED = "overlooked"
    GUARDED = "guarded"


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


class MoodletOutcome(StrEnum):
    UNKNOWN = "unknown"
    COMPLETED = "completed"
    WIN = "win"
    LOSS = "loss"
    DRAW = "draw"
    HANDOVER = "handover"
    INTAKE = "intake"


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


def calculate_moodlet_contributions(
    state: MoodletState, *, definitions: Mapping[MoodletId, MoodletDefinition],
) -> MoodletContributions:
    if not state.active:
        return MoodletContributions()
    groups: dict[MoodletGroup, float] = {}
    for episode in state.active:
        definition = definitions[episode.definition_id]
        groups[definition.group] = (groups.get(definition.group, 0)
                                    + definition.level_points[episode.level - 1])
    for group, field in (
        (MoodletGroup.GAME_WISH, "game_wish_cap_points"),
        (MoodletGroup.SOCIAL_WISH, "social_wish_cap_points"),
        (MoodletGroup.POOR_CARE, "poor_care_cap_points"),
    ):
        value = groups.get(group, 0)
        limit = BALANCE.number("moodlets", field)
        groups[group] = max(-limit, min(limit, value))
    return MoodletContributions(
        min(BALANCE.number("moodlets", "positive_cap_points"),
            sum(max(0, value) for value in groups.values())),
        max(-BALANCE.number("moodlets", "negative_cap_points"),
            sum(min(0, value) for value in groups.values())),
    )


def _age_episode(
    episode: MoodletEpisode, seconds: float, definition: MoodletDefinition,
) -> MoodletEpisode | None:
    """At most three stages; long gaps never create an elapsed-time replay."""
    if seconds == 0 and episode.remaining_seconds > 0:
        return episode
    level, remaining = episode.level, episode.remaining_seconds
    while seconds >= remaining:
        seconds -= remaining
        level -= 1
        if level == 0:
            return None
        remaining = float(definition.decay_stage_seconds)
    return replace(episode, level=level, remaining_seconds=remaining - seconds,
                   pending_repetitions=episode.pending_repetitions
                   if level == episode.level else 0)


def _recover_episode(
    episode: MoodletEpisode, definition: MoodletDefinition, *, elapsed: float,
    seconds: float, before: NeedLevels, after: NeedLevels,
) -> MoodletEpisode | None:
    parameters = definition.parameters
    assert isinstance(parameters, PoorCareParameters)
    low = float(getattr(before, parameters.need))
    high = float(getattr(after, parameters.need))
    threshold = BALANCE.number("moodlets", "recovery_need_threshold")
    end = elapsed + seconds
    if low < threshold and high < threshold:
        if episode.decay_paused and episode.recovery_since is None:
            return episode
        return replace(episode, decay_paused=True, recovery_since=None)
    healthy_start, healthy_end = elapsed, end
    if low < threshold <= high:
        healthy_start += seconds * (threshold - low) / (high - low)
    elif high < threshold <= low:
        healthy_end = elapsed + seconds * (threshold - low) / (high - low)
    since = (episode.recovery_since
             if low >= threshold and episode.recovery_since is not None
             else healthy_start)
    ready = since + BALANCE.number("moodlets", "recovery_stable_seconds")
    recovered = _age_episode(
        episode, max(0, healthy_end - max(healthy_start, ready)), definition,
    )
    if recovered is None:
        return None
    return replace(recovered, decay_paused=high < threshold or end < ready,
                   recovery_since=since if high >= threshold else None)


def advance_moodlets(
    state: MoodletState, seconds: float, *, elapsed: float,
    before: NeedLevels, after: NeedLevels,
    definitions: Mapping[MoodletId, MoodletDefinition], observed: bool = True,
) -> MoodletState:
    """Age existing impressions over the owner's interval; never create one.

    Need trajectories are linear within a numeric step. Unobserved time cannot
    extend observed withholding, but still advances quiet-time after-effects.
    """
    if (not math.isfinite(seconds) or seconds < 0 or not math.isfinite(elapsed)
            or elapsed < state.baseline):
        raise ValueError("Moodlet progression requires a finite elapsed interval")
    if not state.active:
        return state
    active = []
    for episode in state.active:
        definition = definitions[episode.definition_id]
        if definition.decay == MoodletDecay.STABLE_RECOVERY:
            result = _recover_episode(episode, definition, elapsed=elapsed,
                                      seconds=seconds, before=before, after=after)
        else:
            paused = episode.decay_paused and observed
            current = (episode if paused == episode.decay_paused
                       else replace(episode, decay_paused=paused))
            result = _age_episode(current, 0 if paused else seconds, definition)
        if result is not None:
            active.append(result)
    values = tuple(active)
    return state if values == state.active else replace(state, active=values)


def next_moodlet_boundary(
    state: MoodletState, *, elapsed: float,
    definitions: Mapping[MoodletId, MoodletDefinition],
) -> float:
    """Seconds to the next tier/qualification change, on the existing clock."""
    boundary = math.inf
    for episode in state.active:
        definition = definitions[episode.definition_id]
        if definition.decay == MoodletDecay.STABLE_RECOVERY:
            if episode.recovery_since is None:
                continue
            wait = (episode.recovery_since
                    + BALANCE.number("moodlets", "recovery_stable_seconds") - elapsed)
            if wait > 0:
                boundary = min(boundary, wait)
                continue
        elif episode.decay_paused:
            continue
        boundary = min(boundary, episode.remaining_seconds)
    return boundary


def reinforce_moodlet(
    state: MoodletState, definition_id: MoodletId, *, elapsed: float,
    definitions: Mapping[MoodletId, MoodletDefinition], level: int = 1,
    attribution: MoodletAttribution = MoodletAttribution.UNKNOWN,
    cause: MoodletCause | None = None,
) -> MoodletState:
    """Apply already-qualified evidence at an already-advanced pet endpoint.

    Owners in later steps qualify events and reject duplicate delivery. Here
    level is the wish fulfillment strength or newly qualified poor-care level.
    Repeated-poke/petting escalation counts only subsequent qualifying events.
    """
    definition = definitions[definition_id]
    maximum = len(definition.level_points)
    if (not math.isfinite(elapsed) or elapsed < state.baseline
            or type(level) is not int or not 1 <= level <= maximum):
        raise ValueError("Invalid Moodlet trigger time or strength")
    if definition.group == MoodletGroup.INTERACTION and level != 1:
        raise ValueError("Interaction evidence starts at one intensity level")
    active = list(state.active)
    for index, episode in enumerate(active):
        if episode.definition_id != definition_id:
            continue
        if cause is not None and any(c.receipt == cause.receipt
                                     for c in episode.causes):
            return state
        if elapsed < episode.last_trigger_at:
            raise ValueError("Moodlet evidence cannot precede its last trigger")
        parameters = definition.parameters
        pending = 0
        if isinstance(parameters, PoorCareParameters):
            if level <= episode.level:
                return state
            intensity = level
        elif isinstance(parameters, (PokingParameters, PettingParameters)):
            limit = (parameters.escalation_pokes
                     if isinstance(parameters, PokingParameters)
                     else parameters.escalation_attempts)
            pending = episode.pending_repetitions + 1
            intensity = min(maximum, episode.level + int(pending >= limit))
            pending = 0 if pending >= limit or intensity == maximum else pending
        else:
            intensity = min(maximum, episode.level + level)
        active[index] = replace(
            episode, level=intensity, last_trigger_at=elapsed,
            remaining_seconds=float(definition.decay_stage_seconds),
            pending_repetitions=pending, recovery_since=None,
            decay_paused=definition.decay != MoodletDecay.QUIET_TIME,
            attribution=attribution,
        )
        if cause is not None:
            active[index] = active[index].with_cause(cause)
        return replace(state, active=tuple(active))
    if state.next_instance_id >= 2**63 - 1:
        raise ValueError("Moodlet instance allocation exhausted")
    episode = MoodletEpisode(
        state.next_instance_id, definition_id, level, elapsed, elapsed,
        float(definition.decay_stage_seconds),
        decay_paused=definition.decay != MoodletDecay.QUIET_TIME,
        attribution=attribution,
    )
    if cause is not None:
        episode = episode.with_cause(cause)
    return replace(state, next_instance_id=state.next_instance_id + 1,
                   active=(*state.active, episode))


def resolve_moodlet_cause(
    state: MoodletState, instance_id: int, *,
    definitions: Mapping[MoodletId, MoodletDefinition],
) -> MoodletState:
    """Ending observed withholding permits decay; it does not erase emotion."""
    return replace(state, active=tuple(
        replace(e, decay_paused=False)
        if e.instance_id == instance_id
        and definitions[e.definition_id].decay == MoodletDecay.RESOLVED_QUIET_TIME
        else e for e in state.active
    ))


def relieve_moodlet(
    state: MoodletState, instance_id: int, *, elapsed: float,
    definitions: Mapping[MoodletId, MoodletDefinition],
) -> MoodletState:
    """One qualified completed helpful action credits only its current tier.

    Matching activities, intake, search resolution and action acceptance are
    supplied by their semantic owners in later steps, never inferred here.
    """
    if not math.isfinite(elapsed) or elapsed < state.baseline:
        raise ValueError("Invalid Moodlet relief time")
    active = []
    for episode in state.active:
        definition = definitions[episode.definition_id]
        eligible = (episode.instance_id == instance_id and definition.relief_seconds > 0
                    and episode.level not in episode.relieved_levels
                    and not episode.decay_paused)
        if episode.definition_id in (MoodletId.POKING, MoodletId.CROWDED):
            eligible = eligible and elapsed - episode.last_trigger_at >= BALANCE.number(
                "moodlets", "relief_quiet_seconds",
            )
        if definition.decay == MoodletDecay.STABLE_RECOVERY:
            eligible = (eligible and episode.recovery_since is not None
                        and elapsed - episode.recovery_since >= BALANCE.number(
                            "moodlets", "recovery_stable_seconds",
                        ))
        result: MoodletEpisode | None = episode
        if eligible:
            result = _age_episode(replace(
                episode, relieved_levels=(*episode.relieved_levels, episode.level),
            ), min(episode.remaining_seconds, definition.relief_seconds), definition)
        if result is not None:
            active.append(result)
    return replace(state, active=tuple(active))
