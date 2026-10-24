"""Validated, sequential text, emote and pause beats for authored reactions."""

from __future__ import annotations

from dataclasses import dataclass, replace
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
        maximum_ms = 10000 if self.kind == "text" else 8000
        if (type(self.duration_ms) is not int
                or not 250 <= self.duration_ms <= maximum_ms):
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


def conversation_timing(beats: tuple[Cue, ...]) -> tuple[Cue, ...]:
    """Prepare social reading time once, including the actual final text."""
    last_text = next(
        (index for index in range(len(beats) - 1, -1, -1)
         if beats[index].kind == "text"),
        None,
    )
    minimum = BALANCE.integer("dialogue", "conversation_minimum_text_ms")
    maximum = BALANCE.integer("dialogue", "conversation_maximum_text_ms")
    orientation = BALANCE.integer("dialogue", "conversation_orientation_ms")
    per_character = BALANCE.integer("dialogue", "conversation_reading_ms_per_character")
    final_allowance = BALANCE.integer("dialogue", "conversation_final_text_ms")
    return tuple(
        replace(
            beat,
            duration_ms=min(
                maximum,
                max(minimum, orientation + len(beat.content) * per_character)
                + (final_allowance if index == last_text else 0),
            ),
        ) if beat.kind == "text" else beat
        for index, beat in enumerate(beats)
    )
