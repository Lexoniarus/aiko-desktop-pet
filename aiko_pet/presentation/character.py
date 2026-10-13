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


@dataclass(frozen=True, slots=True)
class AnimationClip:
    name: str
    frames: tuple[AnimationFrame, ...]
    loop: bool
    anchor: tuple[int, int]
    return_to: str = "idle"

    @property
    def timings(self) -> tuple[int, ...]:
        return tuple(frame.duration_ms for frame in self.frames)

    @property
    def duration_seconds(self) -> float:
        return sum(self.timings) / 1000


@dataclass(frozen=True, slots=True)
class CharacterCatalog:
    clips: Mapping[str, AnimationClip]
