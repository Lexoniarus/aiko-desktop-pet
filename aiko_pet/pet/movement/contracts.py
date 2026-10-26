"""Pure inputs and results for horizontal movement, independent of desktop APIs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

MotionSource = Literal["world", "cursor", "idle"]
MotionKind = Literal["step", "walk", "run"]


@dataclass(frozen=True, slots=True)
class MotionRequest:
    source: MotionSource
    token: int
    target_x: float
    kind: MotionKind = "run"
    until: float = float("inf")


class HorizontalTrack(Protocol):
    """Readable lateral movement bounds in screen-independent coordinates."""

    @property
    def left(self) -> int: ...

    @property
    def right(self) -> int: ...


@dataclass(frozen=True)
class WalkConditions:
    """Values needed to decide whether and how far a pet should move."""

    now: float
    elapsed_seconds: float
    speed_pixels_per_second: float
    stride_pixels: float
    x: float
    track: HorizontalTrack
    sprite_width: int
    energy: float
    auto_walk: bool
    sleeping: bool
    attention_active: bool
    menu_engaged: bool
    observing_computer: bool
    computer_busy: bool
    quiet_period: bool


@dataclass(frozen=True)
class WalkStep:
    """Requested horizontal displacement and matching sprite animation."""

    pixels: float
    direction: int
    kind: MotionKind = "run"
