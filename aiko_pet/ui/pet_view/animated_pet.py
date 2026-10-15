"""Animated Aiko sprite: walking, direction, sprite assets and frame display.

This object owns the character visuals. It never imports DesktopPet, hover
widgets, notification adapters or network services. All host effects use ports.
"""

from __future__ import annotations

import math
import time
import tkinter as tk
from dataclasses import dataclass
from typing import Callable, Protocol
from collections.abc import Sequence

from ...pet.animation.animation import FrameClock
from ...pet.animation.ambient import AmbientDirector
from ...pet.animation.character import CharacterCatalog, FRAME_WIDTH
from ...pet.animation.gaze import gaze_sector
from ...pet.animation.priority import choose_animation_priority
from ...pet.mind.cursor_attention import CursorAttentionSnapshot
from ...pet.movement import WalkController
from .walk_driver import (
    ActivityReadings as ActivityReadings,
    BusyReading as BusyReading,
    FocusReadings as FocusReadings,
    FocusState as FocusState,
    WalkDriver,
    WalkDriverPorts,
)
from .food_overlay import FoodOverlay
from .character_sprite_cache import CharacterSpriteCache
from .rest_pose_renderer import RestPoseRenderer
from ...desktop.geometry import TaskbarTrack, FOOT_BASELINE


class CareVisuals(Protocol):
    """A read-only view of needs used by sprite presentation."""

    energy: float
    mood: float
    satiety: float
    sleeping: bool


class CharacterSettings(Protocol):
    """Writable character choices without depending on their storage."""

    @property
    def scale(self) -> int: ...

    @scale.setter
    def scale(self, value: int) -> None: ...

    @property
    def x(self) -> int | None: ...

    @x.setter
    def x(self, value: int | None) -> None: ...

    @property
    def y(self) -> int | None: ...

    @y.setter
    def y(self, value: int | None) -> None: ...

    @property
    def follow_cursor(self) -> bool: ...

    @follow_cursor.setter
    def follow_cursor(self, value: bool) -> None: ...

    @property
    def auto_walk(self) -> bool: ...

    @auto_walk.setter
    def auto_walk(self, value: bool) -> None: ...

    @property
    def observe_computer(self) -> bool: ...

    @observe_computer.setter
    def observe_computer(self, value: bool) -> None: ...


@dataclass(frozen=True, slots=True)
class AnimatedPorts:
    """Effects outside the sprite's own drawing and movement state."""

    track: Callable[[], TaskbarTrack]
    toolbar_visible: Callable[[], bool]
    place_x: Callable[[float], None]
    action_until: Callable[[], float]
    action_state: Callable[[], str]
    walk_finished: Callable[[float], None]
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
        self._ambient = AmbientDirector(started_at=time.monotonic())
        self._walk_driver = WalkDriver(
            state=state, settings=settings, adaptive=adaptive, monitor=monitor,
            walk_cycle_seconds=assets.clips["running-left"].duration_seconds,
            ports=WalkDriverPorts(
                track=ports.track,
                toolbar_visible=ports.toolbar_visible,
                place_x=ports.place_x,
                walk_finished=ports.walk_finished,
            ),
        )
        self.gaze_sector: int | None = None
        self._game_mode = False
        self._cursor_snapshot = CursorAttentionSnapshot(-100.0, -100.0)
        self._last_render_pointer: tuple[int, int] = (0, 0)
        self._sprite_cache = CharacterSpriteCache(root, assets)
        self.sprites = self.load_sprites()
        self._rest_renderer = RestPoseRenderer(root)
        self.image_item = self.canvas.create_image(
            0, 0, anchor="nw", image=self.sprites["idle"][0],
        )
        self.food_overlay = FoodOverlay(root, canvas, scale=self.settings.scale)
        self.show_frame("idle", time.monotonic())

    def load_sprites(self) -> dict[str, Sequence[tk.PhotoImage]]:
        """Reuse originals and lazily zoom only requested 2x frames."""
        return self._sprite_cache.for_scale(self.settings.scale)

    @property
    def game_mode(self) -> bool:
        return self._game_mode

    @property
    def cursor_eye_position(self) -> tuple[float, float]:
        scale = self.settings.scale
        return (
            (self.settings.x or 0) + (FRAME_WIDTH // 2) * scale,
            (self.settings.y or 0) + 82 * scale,
        )

    @property
    def movement(self) -> WalkController:
        """Compatibility access to the driver-owned walking controller."""
        return self._walk_driver.movement

    @movement.setter
    def movement(self, value: WalkController) -> None:
        self._walk_driver.movement = value

    def set_auto_walk(self, enabled: bool, now: float) -> None:
        """Delegate walking preferences to their movement owner."""
        self._walk_driver.set_auto_walk(enabled, now)

    def set_follow_cursor(self, enabled: bool) -> None:
        self.settings.follow_cursor = bool(enabled)
        self.gaze_sector = None

    def set_game_mode(self, enabled: bool) -> None:
        """Pause gaze/walking and hold a forward-facing game pose."""
        self._game_mode = bool(enabled)
        self.gaze_sector = None
        self.movement.interrupt()
        self.cancel_action(time.monotonic())

    def reload_sprites(self) -> None:
        """Replace scaled images while preserving the active playback clock."""
        self.sprites = self.load_sprites()
        self._rest_renderer.clear()
        self.food_overlay.reload(self.settings.scale)
        state, fixed = self.frame_clock.active_key or ("idle", None)
        self.show_frame(state, time.monotonic(), fixed=fixed)

    def set_food_overlay(self, food_id: str) -> None:
        """Select the held graphic without changing nutrition."""
        self.food_overlay.select(food_id)

    def begin_action(self, state: str, now: float) -> None:
        """Start a new visual action, including repeated actions of one kind."""
        self._ambient.suspend(now)
        self.frame_clock.reset()
        self._active_action = state
        self.movement.interrupt()
        self.show_frame(state, now)

    def cancel_action(self, now: float) -> None:
        """Interrupt the previous visual when entering or leaving sleep."""
        self._ambient.suspend(now)
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
        # End a complete idle blink after frame 7, then hold neutral frame 0
        # until the ambient policy schedules another one. No frame is skipped.
        if (
            state == "idle" and fixed is None and self._ambient.blinking
            and self.frame_clock.active_key == ("idle", None)
            and self.frame_clock.frame_index == len(clip.frames) - 1
            and now - self.frame_clock.frame_started_at
                >= clip.timings[-1] / 1000 - 1e-6
        ):
            self._ambient.finish_blink(now)
            fixed = 0
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
        source_index = clip.sprite_index(index)
        image = self.sprites[state][source_index]
        if (state == "idle" and fixed == 0) or (
            state == "look" and fixed is not None
        ):
            image = self._rest_renderer.resolve(
                image, offset=self._ambient.motion_offset(now),
                scale=self.settings.scale,
            )
        self.canvas.itemconfigure(self.image_item, image=image)
        self.food_overlay.render(
            clip, clip.frames[source_index], scale=self.settings.scale,
        )
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
                self.render(
                    now, 0, self._last_render_pointer,
                )
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

    def gaze_direction(self, pointer: tuple[int, int]) -> int | None:
        if self._game_mode:
            self.gaze_sector = None
            return None
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
        """Maintain the original sprite API while delegating desktop motion."""
        return self._walk_driver.step(
            now, dt, game_mode=self._game_mode,
            attention_active=now < self._cursor_snapshot.attention_until,
        )

    def render(
        self, now: float, elapsed: float, pointer: tuple[int, int],
        *, attention: CursorAttentionSnapshot | None = None,
    ) -> None:
        """Render an immutable cursor snapshot without mutating PetMind."""
        self._last_render_pointer = pointer
        if attention is not None:
            self._cursor_snapshot = attention
        priority = choose_animation_priority(
            game_mode=self._game_mode,
            sleeping=self.state.sleeping,
            active_action=self._active_action,
            action_loops=(
                self.assets.clips[self._active_action].loop
                if self._active_action is not None else False
            ),
            timed_action_active=now < self.ports.action_until(),
        )
        if priority.mode != "passive":
            self._ambient.suspend(now)
            if priority.clear_action:
                self._active_action = None
            if priority.interrupt_walk:
                self.movement.interrupt()
            selected = (
                self.ports.action_state()
                if priority.mode == "timed"
                else priority.animation
            )
            if selected is None:
                raise AssertionError("An active animation needs a clip")
            self.show_frame(selected, now)
            return
        else:
            self._active_action = None
            moving = self.maybe_walk(now, 0)
            if moving is not None:
                self._ambient.suspend(now)
                self.show_frame(moving, now)
                return
            if now - self._cursor_snapshot.last_pointer_move < 4.0:
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
            choice = self._ambient.select_passive_animation(
                now, gaze_direction=look,
                observing_computer=self.settings.observe_computer,
                computer_busy=computer_busy,
                energy=self.state.energy, mood=self.state.mood,
                satiety=self.state.satiety,
            )
            self.show_frame(choice.animation, now, fixed=choice.fixed_frame)
