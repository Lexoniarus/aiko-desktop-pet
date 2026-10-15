"""Immutable character clip data shared by asset readers and sprite playback."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

FRAME_WIDTH = 192
FRAME_HEIGHT = 208


@dataclass(frozen=True, slots=True)
class AnimationFrame:
    file: Path
    duration_ms: int
    events: tuple[str, ...] = ()
    food_anchor: tuple[int, int] | None = None
    hand_foreground: Path | None = None


@dataclass(frozen=True, slots=True)
class AnimationClip:
    name: str
    frames: tuple[AnimationFrame, ...]
    loop: bool
    anchor: tuple[int, int]
    return_to: str = "idle"
    playback_order: tuple[int, ...] = ()
    hold_last: bool = False

    @property
    def timings(self) -> tuple[int, ...]:
        return tuple(
            self.frames[index].duration_ms for index in (
                self.playback_order or tuple(range(len(self.frames)))
            )
        )

    def sprite_index(self, playback_index: int) -> int:
        """Map a playback step to its original sprite and overlay anchors."""
        if self.playback_order:
            return self.playback_order[playback_index]
        return playback_index

    @property
    def duration_seconds(self) -> float:
        return sum(self.timings) / 1000


@dataclass(frozen=True, slots=True)
class CharacterCatalog:
    clips: Mapping[str, AnimationClip]


@dataclass(frozen=True, slots=True)
class PlaybackEvent:
    """Identified source-pose event; consumed by application coordination."""

    action_id: int
    clip_id: str
    source_index: int
    events: tuple[str, ...] = ()
    finished: bool = False
