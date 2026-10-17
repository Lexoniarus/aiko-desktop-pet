"""Typed episode and phase data; the coordinator alone owns transitions."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import ClassVar, Literal, TypeAlias

from ..pet.animation.character import PlaybackEvent
from ..pet.consumption import ConsumptionOrigin
from ..pet.mind.object_decisions import ObjectUseContext, ObjectUseDecision
from ..pet.mind.object_events import ObjectEvent
from ..pet.mind.object_intentions import ObjectGoal
from ..pet.mind.object_perception import ConsumableKind
from ..pet.mind.object_withholding import WithholdingEpisode
from .object_feedback import FeedbackKey


@dataclass(slots=True)
class InteractionEpisode:
    """One committed subject across phases, observed takes and actual return.

    This mutable record is private to the coordinator. A fresh episode creates
    fresh effect histories; ending one drops it before cancellation calls back.
    Phase prerequisites, session counters and contact cooldowns live elsewhere.
    """

    interaction_id: str
    memory_id: str
    origin: ConsumptionOrigin
    use_context: ObjectUseContext
    instance_id: str | None = None
    identity: str | None = None
    kind: ConsumableKind | None = None
    retrieving: bool = False
    queued: Callable[[], None] | None = None
    seen: set[PlaybackEvent] = field(default_factory=set)
    effects: set[tuple[int, str]] = field(default_factory=set)
    withholding: WithholdingEpisode = field(default_factory=WithholdingEpisode)


@dataclass(slots=True)
class PhaseFeedback:
    """One phase's readable cue and optional non-replacing aside."""

    completed: bool = False
    pending: ObjectEvent | None = None
    auxiliary_key: FeedbackKey | None = None


@dataclass(slots=True)
class AnimationProgress:
    action_id: int | None = None
    finished: bool = False


@dataclass(slots=True)
class OfferAppraisal:
    """Current and latest assessment carried across waiting/offer cue changes."""

    decision: ObjectUseDecision = field(
        default_factory=lambda: ObjectUseDecision(False, "unrecognized"),
    )
    latest: ObjectUseDecision | None = None


@dataclass(frozen=True, slots=True)
class SearchReadout:
    """Immutable search facts also retained for the existing diagnostic reads."""

    x: float = 0.0
    started_at: float = 0.0


@dataclass(slots=True)
class IdlePhase:
    name: ClassVar[Literal["idle"]] = "idle"


@dataclass(slots=True)
class CuePhase:
    name: Literal["notice", "recognize", "handover", "finish", "missing"]
    feedback: PhaseFeedback = field(default_factory=PhaseFeedback)


@dataclass(slots=True)
class ApproachPhase:
    name: ClassVar[Literal["approach"]] = "approach"
    arrived: bool = False
    feedback: PhaseFeedback = field(default_factory=PhaseFeedback)


@dataclass(slots=True)
class AnimationPhase:
    name: Literal["pick_up", "eat"]
    playback: AnimationProgress = field(default_factory=AnimationProgress)
    feedback: PhaseFeedback = field(default_factory=PhaseFeedback)


@dataclass(slots=True)
class PutDownPhase:
    name: ClassVar[Literal["put_down"]] = "put_down"
    defer_if_uninterrupted: bool
    playback: AnimationProgress = field(default_factory=AnimationProgress)
    feedback: PhaseFeedback = field(default_factory=PhaseFeedback)


@dataclass(slots=True)
class InspectionPhase:
    name: ClassVar[Literal["inspect"]] = "inspect"
    started_at: float
    feedback: PhaseFeedback = field(default_factory=PhaseFeedback)


@dataclass(slots=True)
class DecisionPhase:
    name: ClassVar[Literal["decide"]] = "decide"
    decision: ObjectUseDecision
    feedback: PhaseFeedback = field(default_factory=PhaseFeedback)


@dataclass(slots=True)
class WaitingPhase:
    name: Literal["await_return", "await_settle", "recognize_offer", "decide_offer"]
    appraisal: OfferAppraisal = field(default_factory=OfferAppraisal)
    feedback: PhaseFeedback = field(default_factory=PhaseFeedback)


@dataclass(slots=True)
class AbsencePhase:
    name: ClassVar[Literal["notice_absence"]] = "notice_absence"
    search_after: bool
    feedback: PhaseFeedback = field(default_factory=PhaseFeedback)


@dataclass(slots=True)
class SearchPhase:
    name: ClassVar[Literal["search"]] = "search"
    readout: SearchReadout
    feedback: PhaseFeedback = field(default_factory=PhaseFeedback)


@dataclass(slots=True)
class FoundPhase:
    name: ClassVar[Literal["found"]] = "found"
    goal: ObjectGoal
    feedback: PhaseFeedback = field(default_factory=PhaseFeedback)


PhaseState: TypeAlias = (
    IdlePhase | CuePhase | ApproachPhase | AnimationPhase | PutDownPhase
    | InspectionPhase | DecisionPhase | WaitingPhase | AbsencePhase
    | SearchPhase | FoundPhase
)
