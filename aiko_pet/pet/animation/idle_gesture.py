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
    """A one-shot playback alias; source frames and legacy waiting stay intact."""
    clips = dict(catalog.clips)
    clips[QUESTION_REQUEST_CLIP] = replace(
        clips["waiting"], name=QUESTION_REQUEST_CLIP,
        loop=False, hold_last=False, return_to="idle",
    )
    return replace(catalog, clips=MappingProxyType(clips))
