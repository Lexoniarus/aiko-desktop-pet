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
from typing import Callable, Protocol

from ..presentation.animation import (
    FrameClock, choose_passive_animation,
)
from ..presentation.character import CharacterCatalog, FRAME_HEIGHT, FRAME_WIDTH
from ..presentation.gaze import gaze_sector
from ..presentation.movement import WalkConditions, WalkController
from ..desktop.geometry import TaskbarTrack, FOOT_BASELINE


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
    action_until: Callable[[], float]
    action_state: Callable[[], str]
    walk_finished: Callable[[float], None]
    cursor_moved: Callable[[float, int, float], None]
    extend_action: Callable[[float], None]


class AnimatedPet:
    """An independently owned character sprite, not a toolbar controller."""

    def __init__(
        self, root: tk.Tk, canvas: tk.Canvas,
        state: CareVisuals, settings: CharacterSettings,
        adaptive: FocusReadings, monitor: ActivityReadings,
        ports: AnimatedPorts, *, assets: CharacterCatalog,
    ) -> None:
        self.root = root
        self.canvas = canvas
        self.state = state
        self.settings = settings
        self.adaptive = adaptive
        self.monitor = monitor
        self.ports = ports
        self.assets = assets
        self._frame_timer: str | None = None
        self._frame_generation = 0
        self._active_action: str | None = None
        self._stopped = False
        self._last_motion_at = time.monotonic()
        self._walk_progress = 0.0
        self.frame_clock = FrameClock(started_at=time.monotonic())
        self.movement = WalkController(
            next_walk_at=time.monotonic() + random.uniform(60.0, 180.0),
        )
        self.gaze_sector: int | None = None
        self._previous_pointer: tuple[int, int] | None = None
        self.last_pointer_move = -100.0
        self.last_attention = -100.0
        self.attention_until = -100.0
        self.sprites = self.load_sprites()
        self.image_item = self.canvas.create_image(
            0, 0, anchor="nw", image=self.sprites["idle"][0],
        )
        self.show_frame("idle", time.monotonic())

    def load_sprites(self) -> dict[str, list[tk.PhotoImage]]:
        """Load prepared frames at Aiko's current integer pixel scale."""
        sprites: dict[str, list[tk.PhotoImage]] = {}
        for state, clip in self.assets.clips.items():
            frames: list[tk.PhotoImage] = []
            for definition in clip.frames:
                path = definition.file
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
        self.movement.interrupt()
        self.movement.pause(now)

    def set_follow_cursor(self, enabled: bool) -> None:
        self.settings.follow_cursor = bool(enabled)
        self.gaze_sector = None

    def reload_sprites(self) -> None:
        """Replace scaled images while preserving the active playback clock."""
        self.sprites = self.load_sprites()
        state, fixed = self.frame_clock.active_key or ("idle", None)
        self.show_frame(state, time.monotonic(), fixed=fixed)

    def begin_action(self, state: str, now: float) -> None:
        """Start a new visual action, including repeated actions of one kind."""
        self.frame_clock.reset()
        self._active_action = state
        self.movement.interrupt()
        self.show_frame(state, now)

    def cancel_action(self, now: float) -> None:
        """Interrupt the previous visual when entering or leaving sleep."""
        self.frame_clock.reset()
        self._active_action = None
        self.movement.interrupt()
        self.show_frame("sleep" if self.state.sleeping else "idle", now)

    def show_frame(
        self, state: str, now: float, *, fixed: int | None = None,
    ) -> None:
        if self._stopped:
            return
        clip = self.assets.clips[state]
        walking = state in ("running-left", "running-right")
        if walking and self.frame_clock.active_key != (state, fixed):
            self._last_motion_at = now
            self._walk_progress = 0.0
        index = self.frame_clock.next_index(
            state, now, clip.timings, fixed=fixed, loop=clip.loop,
        )
        if self._active_action == state and not clip.loop:
            self.ports.extend_action(self.frame_clock.end_time)
        self.canvas.coords(
            self.image_item,
            (FRAME_WIDTH // 2 - clip.anchor[0]) * self.settings.scale,
            (FOOT_BASELINE - clip.anchor[1]) * self.settings.scale,
        )
        self.canvas.itemconfigure(self.image_item, image=self.sprites[state][index])
        if self._frame_timer is not None:
            self.root.after_cancel(self._frame_timer)
            self._frame_timer = None
        self._frame_generation += 1
        generation = self._frame_generation
        delay = self.frame_clock.next_delay_ms
        if self.frame_clock.finished and self._active_action == state:
            self._active_action = None
            self.show_frame(clip.return_to, now)
        elif delay is not None:
            if walking:
                motion_wait = max(1, math.ceil(
                    33 - (now - self._last_motion_at) * 1000 - 1e-6,
                ))
                delay = min(delay, motion_wait)
            self._frame_timer = self.root.after(
                delay, lambda: self._advance_frame(state, fixed, generation),
            )

    def _advance_frame(
        self, state: str, fixed: int | None, generation: int,
    ) -> None:
        if self._stopped or generation != self._frame_generation:
            return
        self._frame_timer = None
        now = time.monotonic()
        if state in ("running-left", "running-right"):
            progress = self.frame_clock.progress_seconds(
                now, self.assets.clips[state].timings,
            )
            elapsed = max(0.0, progress - self._walk_progress)
            self._walk_progress = progress
            self._last_motion_at = now
            moving = self.maybe_walk(now, elapsed)
            if moving is None or self.movement.remaining_distance == 0:
                self.render(now, 0, self._previous_pointer or (0, 0))
                return
            state = moving
        self.show_frame(state, now, fixed=fixed)

    def stop(self) -> None:
        """Cancel animation callbacks before the desktop destroys Tk."""
        self._stopped = True
        self._frame_generation += 1
        if self._frame_timer is not None:
            self.root.after_cancel(self._frame_timer)
            self._frame_timer = None

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
            eye_x = (self.settings.x or 0) + (FRAME_WIDTH // 2) * self.settings.scale
            eye_y = (self.settings.y or 0) + 82 * self.settings.scale
            distance = math.hypot(pointer[0] - eye_x, pointer[1] - eye_y)
            self.ports.cursor_moved(
                distance, self.root.winfo_screenwidth(), now,
            )
        self._previous_pointer = pointer
        return pointer

    def gaze_direction(self, pointer: tuple[int, int]) -> int | None:
        if not self.settings.follow_cursor:
            self.gaze_sector = None
            return None
        eyes_x = self.root.winfo_x() + (FRAME_WIDTH // 2) * self.settings.scale
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
            speed_pixels_per_second=(
                68 * self.settings.scale
                / self.assets.clips["running-left"].duration_seconds
            ),
            stride_pixels=68 * self.settings.scale,
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
        if step.pixels == 0:
            return step.animation
        old_x = self.settings.x or 0
        self.ports.place_x(old_x + step.pixels)
        delta = (self.settings.x or 0) - old_x
        track = self.ports.track()
        blocked = (
            (step.pixels < 0 and (self.settings.x or 0) <= track.left)
            or (step.pixels > 0 and (self.settings.x or 0)
                >= track.right - FRAME_WIDTH * self.settings.scale)
        )
        if self.movement.record_displacement(delta, now=now, blocked=blocked):
            self.ports.walk_finished(now)
        return step.animation

    def render(
        self, now: float, elapsed: float, pointer: tuple[int, int],
    ) -> None:
        """Draw one state with unchanged sleep/action/gaze precedence."""
        if self.state.sleeping:
            self.movement.interrupt()
            self._active_action = None
            self.show_frame("sleep", now)
        elif (
            self._active_action is not None
            and not self.assets.clips[self._active_action].loop
        ):
            self.show_frame(self._active_action, now)
        elif now < self.ports.action_until():
            self.show_frame(self.ports.action_state(), now)
        else:
            self._active_action = None
            moving = self.maybe_walk(now, 0)
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
