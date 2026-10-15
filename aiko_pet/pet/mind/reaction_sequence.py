"""Sequential, mutually exclusive visual beats for Aiko's reactions.

An emote is a moment in a reaction, never a second concurrent overlay.
No AI or sprite synthesis is used; all cue names refer to verified CC0 PNGs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from ..balance import BALANCE

CUE_KINDS = frozenset({"emote", "text"})
EMOTES = frozenset(
    {
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
    }
)


@dataclass(frozen=True)
class Cue:
    """One screen occupant with a bounded lifetime."""

    kind: Literal["emote", "text"]
    content: str
    duration_ms: int

    def __post_init__(self) -> None:
        if self.kind not in CUE_KINDS or not self.content:
            raise ValueError("Invalid cue")
        if self.kind == "emote" and self.content not in EMOTES:
            raise ValueError("Missing or unsupported emote")
        if not 250 <= self.duration_ms <= 8000:
            raise ValueError("Cue duration out of range")


def compose_cues(
    text: str,
    *,
    before: str | None = None,
    followup: str | None = None,
    after: str | None = None,
    minimum_text_ms: int = BALANCE.integer("dialogue", "minimum_text_ms"),
) -> tuple[Cue, ...]:
    """Produce one coherent sequence, never overlapping emote and text.

    The optional concluding emote comes after every text fragment. Durations
    are deliberately modest: Aiko should not dominate the desktop.
    """
    if not text.strip():
        raise ValueError("Reaction must include speech")
    cues: list[Cue] = []
    if before is not None:
        cues.append(
            Cue("emote", before, BALANCE.integer("dialogue", "before_emote_ms"))
        )
    for phrase in (text, followup):
        if phrase:
            # Readability scales with length, but one line doesn't stall forever.
            reading_ms = min(
                BALANCE.integer("dialogue", "maximum_text_ms"),
                max(
                    minimum_text_ms,
                    len(phrase)
                    * BALANCE.integer("dialogue", "reading_ms_per_character"),
                ),
            )
            cues.append(Cue("text", phrase, reading_ms))
    if after is not None:
        cues.append(Cue("emote", after, BALANCE.integer("dialogue", "after_emote_ms")))
    return tuple(cues)
