"""Identified, language-neutral phase feedback and presentation receipts."""

from dataclasses import dataclass
from typing import Literal

InteractionPhase = Literal[
    "idle", "notice", "approach", "pick_up", "inspect", "recognize", "decide",
    "eat", "put_down", "finish",
]
ObjectEvent = Literal[
    "object_notice", "object_return", "object_approach", "object_pick_up",
    "object_inspect", "object_recognized", "object_unknown", "object_want",
    "object_later", "object_consuming", "object_put_down", "object_finished",
    "object_handover", "object_offer", "object_refuse",
]


@dataclass(frozen=True, slots=True)
class FeedbackKey:
    interaction_id: str
    phase_id: int


@dataclass(frozen=True, slots=True)
class ObjectFeedback:
    key: FeedbackKey
    event: ObjectEvent
    instance_id: str
    identity: str | None


@dataclass(frozen=True, slots=True)
class FeedbackReceipt:
    key: FeedbackKey
    completed: bool
