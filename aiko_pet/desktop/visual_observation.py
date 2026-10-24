"""Observe native gaze geometry and cached workload for pet animation.

The Tk sprite never samples hardware or maintains cursor direction history.
Desktop observations become immutable inputs for pure animation policies.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from typing import Protocol

from ..application.object_behavior import choose_object_attention
from ..application.object_feedback import InteractionPhase
from ..pet.animation.animation import PassiveObservation
from ..pet.animation.character import FRAME_WIDTH
from ..pet.animation.gaze import gaze_sector
from ..pet.mind.object_attention import LookSide, ObjectAttention


class VisualSettings(Protocol):
    @property
    def scale(self) -> int: ...

    @property
    def follow_cursor(self) -> bool: ...

    @property
    def observe_computer(self) -> bool: ...


class BusyReading(Protocol):
    def is_busy(self) -> bool: ...


class WorkloadReadings(Protocol):
    def latest(self) -> BusyReading: ...


@dataclass(frozen=True, slots=True)
class VisualAttentionPorts:
    """Read existing owners without keeping another action or movement state."""

    phase: Callable[[], InteractionPhase] = lambda: "idle"
    sleeping: Callable[[], bool] = lambda: False
    walking: Callable[[], float] = lambda: 0.0
    following_subject: Callable[[], str | None] = lambda: None
    feedback_subject: Callable[[], str | None] = lambda: None
    activity_active: Callable[[], bool] = lambda: False
    orientation_side: Callable[[], LookSide | None] = lambda: None


class DesktopVisualObservation:
    """Resolve one gaze sector and defer CPU observations during cursor gaze."""

    def __init__(
        self, *, settings: VisualSettings, monitor: WorkloadReadings,
        eyes: Callable[[], tuple[float, float]],
        attention: VisualAttentionPorts = VisualAttentionPorts(),
    ) -> None:
        self._settings = settings
        self._monitor = monitor
        self._eyes = eyes
        self._attention = attention
        self._sector: int | None = None
        self.object_target: tuple[float, float] | None = None

    @property
    def sector(self) -> int | None:
        return self._sector

    @property
    def orienting(self) -> bool:
        return self._attention.orientation_side() is not None

    def reset(self) -> None:
        """Clear gaze hysteresis on game, scale or cursor-setting changes."""
        self._sector = None

    def gaze_direction(
        self, pointer: tuple[int, int], *, game_mode: bool = False,
    ) -> int | None:
        """Project current attention into the existing hysteretic gaze atlas."""
        return self._gaze(self.attention(
            pointer, pointer_recent=True, game_mode=game_mode,
        ))

    def attention(
        self, pointer: tuple[int, int], *, pointer_recent: bool,
        game_mode: bool = False,
    ) -> ObjectAttention:
        """Normalize native geometry once; application policy selects attention."""
        eyes_x, eyes_y = self._eyes()
        width = FRAME_WIDTH * self._settings.scale
        following = self._attention.following_subject()

        def relative(point: tuple[float, float]) -> tuple[float, float]:
            return ((point[0] - eyes_x) / width, (eyes_y - point[1]) / width)

        attention = choose_object_attention(
            self._attention.phase(), sleeping=self._attention.sleeping(),
            game_open=game_mode, walking=self._attention.walking(),
            following_cursor=following is not None,
            tracking_feedback=(following is not None
                               and following == self._attention.feedback_subject()),
            activity_active=self._attention.activity_active(),
            orientation_side=self._attention.orientation_side(),
            cursor=relative(pointer)
            if self._settings.follow_cursor
            and (pointer_recent or following is not None) else None,
            target=relative(self.object_target) if self.object_target is not None
            else None,
        )
        return replace(attention, origin=(eyes_x, -eyes_y), width=width)

    def _gaze(self, attention: ObjectAttention) -> int | None:
        direction = attention.direction
        if direction is None:
            self.reset()
            return None
        width = FRAME_WIDTH * self._settings.scale
        self._sector = gaze_sector(
            0, 0, direction[0] * width, -direction[1] * width,
            scale=self._settings.scale, previous=self._sector,
        )
        return self._sector

    def observe(
        self, now: float, pointer: tuple[int, int],
        last_pointer_move: float, game_mode: bool,
        *, cursor_gaze_point: tuple[float, float] | None = None,
    ) -> PassiveObservation:
        """Return passive inputs; preserve gaze precedence over hardware."""
        attention = self.attention(
            pointer, pointer_recent=now - last_pointer_move < 4.0,
            game_mode=game_mode,
        )
        if cursor_gaze_point is not None and attention.mode in ("object", "cursor"):
            eyes_x, eyes_y = self._eyes()
            width = FRAME_WIDTH * self._settings.scale
            attention = replace(attention, direction=(
                (cursor_gaze_point[0] - eyes_x) / width,
                (eyes_y - cursor_gaze_point[1]) / width,
            ))
        direction = self._gaze(attention)
        forward = attention.direction is not None and direction is None
        busy = (
            self._monitor.latest().is_busy()
            if attention.mode != "unavailable" and direction is None and not forward
            and self._settings.observe_computer else False
        )
        return PassiveObservation(direction, busy, forward_gaze=forward)
