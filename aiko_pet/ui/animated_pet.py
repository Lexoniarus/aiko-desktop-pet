"""Animated Aiko sprite: walking, direction, sprite assets and frame display.

This object owns the character visuals. It never imports DesktopPet, hover
widgets, notification adapters or network services. All host effects use ports.
"""

from __future__ import annotations

import math
import random
import time
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Protocol

from ..animation import (
    FRAME_COUNTS, FrameClock, choose_passive_animation,
)
from ..asset_paths import ASSETS
from ..gaze import gaze_sector
from ..movement import WalkConditions, WalkController
from ..taskbar import TaskbarTrack

FRAME_WIDTH = 128
FRAME_HEIGHT = 208


class BusyReading(Protocol):
    def is_busy(self) -> bool: ...


class ActivityReadings(Protocol):
    def latest(self) -> BusyReading: ...


class CareVisuals(Protocol):
    """A read-only view of needs used by sprite presentation."""

    energy: float
    mood: float
    satiety: float
    sleeping: bool


class CharacterSettings(Protocol):
    """Presentation choices without exposing the settings repository."""

    scale: int
    x: int | None
    y: int | None
    follow_cursor: bool
    auto_walk: bool
    observe_computer: bool
    spontaneous_talk: bool


class FocusState(Protocol):
    @property
    def focused(self) -> bool: ...

    @property
    def quiet(self) -> bool: ...


class FocusReadings(Protocol):
    @property
    def current(self) -> FocusState | None: ...


@dataclass(frozen=True, slots=True)
class AnimatedPorts:
    """Effects outside the sprite's own drawing and movement state."""

    track: Callable[[], TaskbarTrack]
    toolbar_visible: Callable[[], bool]
    place_x: Callable[[float], None]
    last_spoken: Callable[[], float]
    action_until: Callable[[], float]
    action_state: Callable[[], str]
    walk_pause: Callable[[float], None]
    cursor_reaction: Callable[[str, float], None]


class AnimatedPet:
    """An independently owned character sprite, not a toolbar controller."""

    def __init__(
        self, root: tk.Tk, canvas: tk.Canvas,
        state: CareVisuals, settings: CharacterSettings,
        adaptive: FocusReadings, monitor: ActivityReadings,
        ports: AnimatedPorts,
    ) -> None:
        self.root = root
        self.canvas = canvas
        self.state = state
        self.settings = settings
        self.adaptive = adaptive
        self.monitor = monitor
        self.ports = ports
        self.frame_clock = FrameClock(started_at=time.monotonic())
        self.movement = WalkController(
            next_walk_at=time.monotonic() + random.uniform(3.0, 8.0),
        )
        self.gaze_sector: int | None = None
        self._previous_pointer: tuple[int, int] | None = None
        self.last_pointer_move = -100.0
        self.last_attention = -100.0
        self.attention_until = -100.0
        self.next_cursor_line = (
            time.monotonic() + random.uniform(200.0, 420.0)
        )
        self.sprites = self.load_sprites()
        self.image_item = self.canvas.create_image(
            0, 0, anchor="nw", image=self.sprites["idle"][0],
        )

    def load_sprites(self) -> dict[str, list[tk.PhotoImage]]:
        """Load prepared frames at Aiko's current integer pixel scale."""
        sprites: dict[str, list[tk.PhotoImage]] = {}
        for state, count in FRAME_COUNTS.items():
            frames: list[tk.PhotoImage] = []
            for i in range(count):
                path: Path = ASSETS / state / f"{i:02d}.png"
                if not path.is_file():
                    raise FileNotFoundError(f"Missing sprite: {path}")
                frame = tk.PhotoImage(file=str(path))
                if (frame.width(), frame.height()) != (
                    FRAME_WIDTH, FRAME_HEIGHT,
                ):
                    raise ValueError(f"Invalid sprite dimensions: {path}")
                if self.settings.scale == 2:
                    frame = frame.zoom(2)
                frames.append(frame)
            sprites[state] = frames
        return sprites

    def set_auto_walk(self, enabled: bool, now: float) -> None:
        """Walking configuration belongs to the character's movement owner."""
        self.settings.auto_walk = bool(enabled)
        self.movement.remaining_distance = 0
        self.movement.next_walk_at = now + random.uniform(2.5, 5)

    def set_follow_cursor(self, enabled: bool) -> None:
        self.settings.follow_cursor = bool(enabled)
        self.gaze_sector = None

    def reload_sprites(self) -> None:
        """Apply a new visual scale without touching care or hover state."""
        self.sprites = self.load_sprites()
        self.canvas.itemconfigure(
            self.image_item, image=self.sprites["idle"][0],
        )

    def show_frame(
        self, state: str, now: float, *, fixed: int | None = None,
    ) -> None:
        frames = self.sprites[state]
        index = self.frame_clock.next_index(
            state, now, len(frames), fixed=fixed,
        )
        self.canvas.itemconfigure(self.image_item, image=frames[index])

    def observe_pointer(self, now: float) -> tuple[int, int]:
        """Observe only pointer positions, not keys or application content."""
        pointer = (
            self.root.winfo_pointerx(), self.root.winfo_pointery(),
        )
        moved = (
            self._previous_pointer is not None
            and pointer != self._previous_pointer
        )
        if moved:
            self.last_pointer_move = now
            if now - self.last_attention >= 6.0:
                self.last_attention = now
                self.attention_until = now + 1.0
            if (
                self.settings.spontaneous_talk
                and self.settings.follow_cursor
                and now >= self.next_cursor_line
                and now - self.ports.last_spoken() > 100
                and not self.state.sleeping
                and not self.ports.toolbar_visible()
                and random.random() < 0.08
            ):
                eye_x = (self.settings.x or 0) + 63 * self.settings.scale
                eye_y = (self.settings.y or 0) + 82 * self.settings.scale
                distance = math.hypot(
                    pointer[0] - eye_x, pointer[1] - eye_y,
                )
                event = (
                    "cursor_far"
                    if distance > self.root.winfo_screenwidth() * 0.6
                    else "cursor_follow"
                )
                self.ports.cursor_reaction(event, now)
                self.next_cursor_line = now + random.uniform(280, 590)
        self._previous_pointer = pointer
        return pointer

    def gaze_direction(self, pointer: tuple[int, int]) -> int | None:
        if not self.settings.follow_cursor:
            self.gaze_sector = None
            return None
        eyes_x = self.root.winfo_x() + 63 * self.settings.scale
        eyes_y = self.root.winfo_y() + 82 * self.settings.scale
        self.gaze_sector = gaze_sector(
            eyes_x, eyes_y, *pointer,
            scale=self.settings.scale, previous=self.gaze_sector,
        )
        return self.gaze_sector

    def maybe_walk(self, now: float, dt: float) -> str | None:
        """Plan horizontal motion and let the host apply taskbar geometry."""
        observed = self.adaptive.current
        busy = (
            observed.focused if observed is not None
            else self.monitor.latest().is_busy()
        )
        step = self.movement.plan_step(WalkConditions(
            now=now,
            elapsed_seconds=dt,
            x=self.settings.x or 0,
            track=self.ports.track(),
            sprite_width=FRAME_WIDTH * self.settings.scale,
            energy=self.state.energy,
            auto_walk=self.settings.auto_walk,
            sleeping=self.state.sleeping,
            attention_active=now < self.attention_until,
            toolbar_visible=self.ports.toolbar_visible(),
            observing_computer=self.settings.observe_computer,
            computer_busy=busy,
            quiet_period=bool(observed is not None and observed.quiet),
        ))
        if step is None:
            return None
        old_x = self.settings.x or 0
        self.ports.place_x(old_x + step.pixels)
        delta = (self.settings.x or 0) - old_x
        if self.movement.record_displacement(delta):
            if (
                self.settings.spontaneous_talk
                and now - self.ports.last_spoken() > 130
                and random.random() < 0.23
            ):
                self.ports.walk_pause(now)
        return step.animation

    def render(
        self, now: float, elapsed: float, pointer: tuple[int, int],
    ) -> None:
        """Draw one state with unchanged sleep/action/gaze precedence."""
        if self.state.sleeping:
            self.movement.remaining_distance = 0
            self.show_frame("idle", now, fixed=2)
        elif now < self.ports.action_until():
            self.show_frame(self.ports.action_state(), now)
        else:
            moving = self.maybe_walk(now, elapsed)
            if moving is not None:
                self.show_frame(moving, now)
                return
            if now - self.last_pointer_move < 4.0:
                look = self.gaze_direction(pointer)
            else:
                look = None
                self.gaze_sector = None
            # Cursor gaze takes precedence; avoid a needless monitor read.
            computer_busy = (
                self.monitor.latest().is_busy()
                if look is None and self.settings.observe_computer
                else False
            )
            choice = choose_passive_animation(
                gaze_direction=look,
                observing_computer=self.settings.observe_computer,
                computer_busy=computer_busy,
                energy=self.state.energy,
                mood=self.state.mood,
                satiety=self.state.satiety,
            )
            self.show_frame(
                choice.animation, now, fixed=choice.fixed_frame,
            )
