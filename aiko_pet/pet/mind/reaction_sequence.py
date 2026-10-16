"""Validated, sequential text, emote and pause beats for authored reactions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from ..balance import BALANCE
from ..catalog_validation import object_fields

CUE_KINDS = frozenset({"emote", "text", "pause"})
EMOTES = frozenset({
    "alert",
    "anger",
    "cloud",
    "drops",
    "exclamation",
    "faceHappy",
    "faceSad",
    "heart",
    "idea",
    "laugh",
    "music",
    "question",
    "sleeps",
    "star",
    "swirl",
})


@dataclass(frozen=True, slots=True)
class Cue:
    """One occupant of the speech surface, or a deliberate silent pause."""

    kind: Literal["emote", "text", "pause"]
    content: str
    duration_ms: int

    def __post_init__(self) -> None:
        if self.kind not in CUE_KINDS:
            raise ValueError("Invalid cue kind")
        if type(self.duration_ms) is not int or not 250 <= self.duration_ms <= 8000:
            raise ValueError("Cue duration out of range")
        if self.kind == "text" and not 1 <= len(self.content.strip()) <= 125:
            raise ValueError("Invalid dialogue text")
        if self.kind == "emote" and self.content not in EMOTES:
            raise ValueError("Missing or unsupported emote")
        if self.kind == "pause" and self.content:
            raise ValueError("Pause cannot contain text")

    @classmethod
    def text(cls, content: str) -> Cue:
        return cls(
            "text",
            content,
            min(
                BALANCE.integer("dialogue", "maximum_text_ms"),
                max(
                    BALANCE.integer("dialogue", "minimum_text_ms"),
                    len(content)
                    * BALANCE.integer("dialogue", "reading_ms_per_character"),
                ),
            ),
        )

    @classmethod
    def parse(cls, raw: Any) -> Cue:
        data = object_fields(
            raw, ("kind",), optional=("content", "duration_ms"), context="dialogue beat"
        )
        kind = data["kind"]
        content = data.get("content", "")
        if not isinstance(content, str):
            raise ValueError("Cue content must be text")
        if kind == "text":
            if "duration_ms" in data:
                raise ValueError("Text duration is derived from its length")
            return cls.text(content)
        if kind not in ("emote", "pause"):
            raise ValueError("Invalid cue kind")
        duration = data.get(
            "duration_ms",
            BALANCE.integer("dialogue", "emote_ms" if kind == "emote" else "pause_ms"),
        )
        if type(duration) is not int:
            raise ValueError("Invalid cue duration")
        return cls(kind, content, duration)
