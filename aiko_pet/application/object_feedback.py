"""Identified, language-neutral phase feedback and presentation receipts."""

from dataclasses import dataclass
from typing import Literal

from ..pet.mind.object_events import ObjectEvent

InteractionPhase = Literal[
    "idle", "notice", "approach", "pick_up", "inspect", "recognize", "decide",
    "handover", "search", "found", "eat", "put_down", "finish", "missing",
]


@dataclass(frozen=True, slots=True)
class FeedbackKey:
    interaction_id: str
    phase_id: int


@dataclass(frozen=True, slots=True)
class ObjectFeedback:
    key: FeedbackKey
    event: ObjectEvent
    record_id: str
    identity: str | None


@dataclass(frozen=True, slots=True)
class FeedbackReceipt:
    key: FeedbackKey
    completed: bool
