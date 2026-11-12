"""Semantic idle gestures reuse artwork without changing legacy clip behavior."""

from dataclasses import dataclass, replace
from types import MappingProxyType

from .character import CharacterCatalog

QUESTION_REQUEST_CLIP = "idle-question-request"


@dataclass(frozen=True, slots=True)
class IdleGestureChoice:
    wish_instance_id: int
    semantic_name: str = "question_request"

    @property
    def clip_id(self) -> str:
        if self.semantic_name != "question_request":
            raise ValueError("Unknown idle gesture")
        return QUESTION_REQUEST_CLIP


def with_idle_gestures(catalog: CharacterCatalog) -> CharacterCatalog:
    """Play the selected Waiting artwork once, then return to Idle."""
    request = replace(
        catalog.clip_for("waiting", 2), name=QUESTION_REQUEST_CLIP,
        loop=False, hold_last=False, return_to="idle",
    )
    if "waiting" in catalog.hd_action_clips:
        return replace(catalog, hd_action_clips=MappingProxyType({
            **catalog.hd_action_clips, QUESTION_REQUEST_CLIP: request,
        }))
    return replace(catalog, clips=MappingProxyType({
        **catalog.clips, QUESTION_REQUEST_CLIP: request,
    }))
