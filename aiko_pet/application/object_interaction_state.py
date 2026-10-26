"""Typed episode and phase data; the coordinator alone owns transitions."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import ClassVar, Literal, TypeAlias

from ..pet.animation.character import PlaybackEvent
from ..pet.consumption import ConsumptionOrigin
from ..pet.mind.object_decisions import ObjectUseContext, ObjectUseDecision
from ..pet.mind.object_events import ObjectEvent
from ..pet.mind.object_knowledge import ObjectKnowledge
from ..pet.mind.object_perception import ConsumableKind
from ..pet.mind.object_withholding import WithholdingEpisode
from .object_feedback import ObjectFeedback


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
    handover_acknowledged: bool = False
    queued: Callable[[], None] | None = None
    seen: set[PlaybackEvent] = field(default_factory=set)
    effects: set[tuple[int, str]] = field(default_factory=set)
    withholding: WithholdingEpisode = field(default_factory=WithholdingEpisode)


@dataclass(slots=True)
class PhaseFeedback:
    """One phase's readable cue and optional non-replacing aside."""

    completed: bool = False
    pending: ObjectEvent | None = None
    aside: ObjectFeedback | None = None

    @property
    def contact_active(self) -> bool:
        return self.aside is not None and self.aside.event in (
            "object_busy",
            "object_busy_search",
        )

    @property
    def blocking_aside(self) -> bool:
        return self.aside is not None and not self.contact_active


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
class SearchPosition:
    """Reachable body-center bounds and actual current World-relative center."""

    left: float
    right: float
    x: float


@dataclass(frozen=True, slots=True)
class SearchRoute:
    """One physical pass; only observed arrival advances its two legs."""

    first: float
    second: float
    leg: int = 0

    @classmethod
    def begin(cls, position: SearchPosition) -> SearchRoute:
        if abs(position.x - position.left) <= abs(position.right - position.x):
            return cls(position.left, position.right)
        return cls(position.right, position.left)

    @property
    def target(self) -> float:
        return self.first if self.leg == 0 else self.second

    def observe(self, x: float) -> SearchRoute:
        # Native adapter reports the actual center; requested goals do not count.
        if self.leg < 2 and abs(x - self.target) <= 2:
            from dataclasses import replace

            return replace(self, leg=self.leg + 1)
        return self


class SearchTask:
    """One pass and its missing portions, retained across candidate actions."""

    __slots__ = ("_missing", "_route", "_unreachable", "_findings", "acute_food")

    def __init__(
        self, subject: ObjectKnowledge | None, *,
        known: tuple[ObjectKnowledge, ...] = (),
    ) -> None:
        self._missing: dict[str, ObjectKnowledge] = {}
        self._route: SearchRoute | None = None
        self._unreachable: set[str] = set()
        # Existing known stock is not a newly identified search finding. This
        # also preserves one-find/one-loss accounting when a search is rebuilt
        # after restart, without introducing another persisted history.
        self._findings = {key for item in known if item.recognized
                          and item.place_status == "remembered"
                          for key in (item.token, item.instance_id) if key is not None}
        self.acute_food = subject is None
        if subject is not None:
            self.add(subject)

    @property
    def next_subject(self) -> ObjectKnowledge | None:
        return next(iter(self._missing.values()), None)

    @property
    def progress(self) -> float:
        return self._route.leg / 2 if self._route is not None else 0.0

    @property
    def route_complete(self) -> bool:
        return self._route is not None and self._route.leg == 2

    def can_investigate(self, token: str) -> bool:
        return token not in self._unreachable

    def exclude_candidate(self, token: str) -> None:
        self._unreachable.add(token)

    def destination(self, position: SearchPosition) -> float:
        """Advance only from actual arrival; changed bounds start fresh coverage."""
        route = self._route or SearchRoute.begin(position)
        if {route.first, route.second} != {position.left, position.right}:
            route = SearchRoute.begin(position)
        self._route = route.observe(position.x)
        return self._route.target

    def add(self, known: ObjectKnowledge) -> bool:
        if known.token in self._missing or (
            known.instance_id is not None and any(
                item.instance_id == known.instance_id for item in self._missing.values()
            )
        ):
            return False
        self._missing[known.token] = known
        # A newly confirmed loss starts a new episode for that portion.
        self._findings.discard(known.token)
        if known.instance_id is not None:
            self._findings.discard(known.instance_id)
        return True

    def resolve(self, known: ObjectKnowledge) -> ObjectKnowledge | None:
        """Remove one verified subject without changing the pass or other losses."""
        token = self._match(known)
        if token is None:
            return None
        self._findings.add(known.token)
        if known.instance_id is not None:
            self._findings.add(known.instance_id)
        return self._missing.pop(token)

    def _match(self, known: ObjectKnowledge) -> str | None:
        if (not known.recognized or known.place_status == "superseded"
                or known.token in self._findings
                or known.instance_id is not None
                and known.instance_id in self._findings):
            return None
        for token, subject in self._missing.items():
            if (known.identity, known.kind) == (subject.identity, subject.kind):
                # The oldest matching missing subject is her subjective reunion.
                # Technical instance identity neither proves nor vetoes that belief.
                return token
        return None


@dataclass(slots=True)
class IdlePhase:
    name: ClassVar[Literal["idle"]] = "idle"


@dataclass(slots=True)
class CuePhase:
    name: Literal[
        "notice",
        "recognize",
        "handover",
        "finish",
        "missing",
        "notice_absence",
        "found",
    ]
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
class ReadingPhase:
    name: ClassVar[Literal["read"]] = "read"
    feedback: PhaseFeedback = field(
        default_factory=lambda: PhaseFeedback(completed=True)
    )


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
class SearchPhase:
    name: ClassVar[Literal["search"]] = "search"
    feedback: PhaseFeedback = field(default_factory=PhaseFeedback)


PhaseState: TypeAlias = (
    IdlePhase
    | CuePhase
    | ApproachPhase
    | AnimationPhase
    | PutDownPhase
    | InspectionPhase
    | ReadingPhase
    | DecisionPhase
    | WaitingPhase
    | SearchPhase
)
