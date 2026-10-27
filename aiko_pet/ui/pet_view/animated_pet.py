"""Animated Aiko sprite: frame playback, sprites and item overlays.

This object owns the character visuals. It never imports DesktopPet, hover
widgets, notification adapters or network services. All host effects use ports.
"""

from __future__ import annotations

import math
import time
import tkinter as tk
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Callable, Protocol

from ...desktop.geometry import FOOT_BASELINE
from ...pet.animation.ambient import AmbientDirector
from ...pet.animation.animation import FrameClock
from ...pet.animation.character import FRAME_WIDTH, CharacterCatalog, PlaybackEvent
from ...pet.animation.item_assets import ItemCatalog
from ...pet.animation.priority import RenderDecision
from ...pet.mind.cursor_attention import CursorAttentionSnapshot
from .body_pose_cache import BodyPoseCache
from .character_sprite_cache import CharacterSpriteCache
from .food_overlay import FoodOverlay
from .rest_pose_renderer import RestPoseRenderer


class CareVisuals(Protocol):
    """A read-only view of needs used by sprite presentation."""

    @property
    def energy(self) -> float: ...

    @property
    def mood(self) -> float: ...

    @property
    def satiety(self) -> float: ...

    @property
    def sleeping(self) -> bool: ...


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


@dataclass(frozen=True, slots=True)
class AnimatedPorts:
    """Effects outside the sprite's own drawing and movement state."""

    walk_step: Callable[[float, float], str | None]
    walk_active: Callable[[], bool]
    interrupt_walk: Callable[[], None]
    choose_animation: Callable[
        [float, tuple[int, int], float, bool, str | None], RenderDecision
    ]
    reset_gaze: Callable[[], None]
    extend_action: Callable[[float], None]


class AnimatedPet:
    """An independently owned character sprite, not a toolbar controller."""

    def __init__(
        self,
        root: tk.Tk,
        canvas: tk.Canvas,
        state: CareVisuals,
        settings: CharacterSettings,
        ports: AnimatedPorts,
        *,
        assets: CharacterCatalog,
        items: ItemCatalog,
        ambient: AmbientDirector,
    ) -> None:
        self.root = root
        self.canvas = canvas
        self.state = state
        self.settings = settings
        self.ports = ports
        self.assets = assets
        self._frame_timer: str | None = None
        self._frame_generation = 0
        self.action_id = 0
        self.on_playback: Callable[[PlaybackEvent], None] = lambda _event: None
        self._emitted: set[tuple[int, str, int, bool]] = set()
        self._active_action: str | None = None
        self._stopped = False
        self._closed = False
        self._last_motion_at = time.monotonic()
        self._walk_progress = 0.0
        self.frame_clock = FrameClock(started_at=time.monotonic())
        self._ambient = ambient
        self._game_mode = False
        self._cursor_snapshot = CursorAttentionSnapshot(-100.0, -100.0)
        self._last_render_pointer: tuple[int, int] = (0, 0)
        self._display_clip = "idle"
        self._sprite_cache = CharacterSpriteCache(root, assets)
        self._body_cache = BodyPoseCache(root, assets)
        self.sprites = self.load_sprites()
        self._rest_renderer = RestPoseRenderer(root)
        self.image_item = self.canvas.create_image(
            0,
            0,
            anchor="nw",
            image=self.sprites["idle"][0],
        )
        self.food_overlay = FoodOverlay(
            root,
            canvas,
            catalog=items,
            scale=self.settings.scale,
        )
        self.show_frame("idle", time.monotonic())

    def load_sprites(self) -> dict[str, Sequence[tk.PhotoImage]]:
        """Reuse originals and lazily zoom only requested 2x frames."""
        sprites = dict(self._sprite_cache.for_scale(self.settings.scale))
        sprites.update(self._body_cache.for_scale(self.settings.scale))
        return sprites

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

    def set_game_mode(self, enabled: bool) -> None:
        """Pause gaze/walking and hold a forward-facing game pose."""
        self._game_mode = bool(enabled)
        self.ports.reset_gaze()
        self.ports.interrupt_walk()

    def reload_sprites(self) -> None:
        """Replace scaled images while preserving the active playback clock."""
        self._body_cache.clear()
        self.sprites = self.load_sprites()
        self._rest_renderer.clear()
        self.food_overlay.reload(self.settings.scale)
        state, fixed = self.frame_clock.active_key or ("idle", None)
        if state not in self.sprites:
            state = self._display_clip
        self.show_frame(state, time.monotonic(), fixed=fixed)

    def set_food_overlay(self, food_id: str) -> None:
        """Select the held graphic without changing nutrition."""
        self.food_overlay.select(food_id)

    def begin_action(self, state: str, now: float) -> None:
        """Start a new visual action, including repeated actions of one kind."""
        self._ambient.suspend(now)
        self.frame_clock.reset()
        self._active_action = state
        self.action_id += 1
        self._emitted.clear()
        self.ports.interrupt_walk()
        self.show_frame(state, now)

    def cancel_action(self, now: float) -> None:
        """Interrupt the previous visual when entering or leaving sleep."""
        self._ambient.suspend(now)
        self.frame_clock.reset()
        self._active_action = None
        self.ports.interrupt_walk()
        self.show_frame("sleep" if self.state.sleeping else "idle", now)

    def hold_last_pose(self, state: str, now: float) -> None:
        """Present an explicit held pose without replaying a ground pickup."""
        self.frame_clock.frame_index = len(self.assets.clips[state].timings) - 1
        self.frame_clock.frame_started_at = now
        self.frame_clock.finished = True
        self.show_frame(state, now)

    def show_frame(
        self,
        state: str,
        now: float,
        *,
        fixed: int | None = None,
    ) -> None:
        if self._stopped:
            return
        clip = self.assets.body_clips.get(state) or self.assets.clips[state]
        self._display_clip = state
        # End a complete idle blink after frame 7, then hold neutral frame 0
        # until the ambient policy schedules another one. No frame is skipped.
        if (
            state == "idle"
            and fixed is None
            and self._ambient.blinking
            and self.frame_clock.active_key == ("idle", None)
            and self.frame_clock.frame_index == len(clip.frames) - 1
            and now - self.frame_clock.frame_started_at
            >= clip.timings[-1] / 1000 - 1e-6
        ):
            self._ambient.finish_blink(now)
            fixed = 0
        walking = clip.movement or state in ("running-left", "running-right")
        clock_key = clip.family or state
        if walking and self.frame_clock.active_key != (clock_key, fixed):
            self._last_motion_at = now
            self._walk_progress = 0.0
        index = self.frame_clock.next_index(
            clock_key,
            now,
            clip.timings,
            fixed=fixed,
            loop=clip.loop,
        )
        if self._active_action == state and not clip.loop:
            self.ports.extend_action(self.frame_clock.end_time)
        self.canvas.coords(
            self.image_item,
            (FRAME_WIDTH // 2 - clip.anchor[0]) * self.settings.scale,
            (FOOT_BASELINE - clip.anchor[1]) * self.settings.scale,
        )
        source_index = clip.sprite_index(index)
        if self._active_action == state:
            key = (self.action_id, state, index, self.frame_clock.finished)
            if key not in self._emitted:
                self._emitted.add(key)
                events = clip.frames[source_index].events
                if state == "put_down":
                    events = ("detach_object",) if source_index == 2 else ()
                self.on_playback(
                    PlaybackEvent(
                        self.action_id,
                        state,
                        source_index,
                        events,
                        self.frame_clock.finished,
                    )
                )
        image = self.sprites[state][source_index]
        if (
            state == "idle"
            or (state == "look" and fixed is not None)
            or state.startswith("body-look-")
        ):
            image = self._rest_renderer.resolve(
                image,
                offset=self._ambient.motion_offset(now),
                scale=self.settings.scale,
            )
        self.canvas.itemconfigure(self.image_item, image=image)
        self.food_overlay.render(
            clip,
            clip.frames[source_index],
            scale=self.settings.scale,
        )
        if self._frame_timer is not None:
            self.root.after_cancel(self._frame_timer)
            self._frame_timer = None
        self._frame_generation += 1
        generation = self._frame_generation
        delay = self.frame_clock.next_delay_ms
        if self.frame_clock.finished and self._active_action == state:
            if clip.hold_last:
                return
            self._active_action = None
            self.show_frame(clip.return_to, now)
        elif delay is not None:
            if walking:
                motion_wait = max(
                    1,
                    math.ceil(
                        33 - (now - self._last_motion_at) * 1000 - 1e-6,
                    ),
                )
                delay = min(delay, motion_wait)
            self._frame_timer = self.root.after(
                delay,
                lambda: self._advance_frame(state, fixed, generation),
            )

    def _advance_frame(
        self,
        state: str,
        fixed: int | None,
        generation: int,
    ) -> None:
        if self._stopped or generation != self._frame_generation:
            return
        self._frame_timer = None
        now = time.monotonic()
        clip = self.assets.body_clips.get(state) or self.assets.clips[state]
        if clip.movement or state in ("running-left", "running-right"):
            progress = self.frame_clock.progress_seconds(
                now,
                clip.timings,
            )
            elapsed = max(0.0, progress - self._walk_progress)
            self._walk_progress = progress
            self._last_motion_at = now
            moving = self.ports.walk_step(now, elapsed)
            if moving is None or not self.ports.walk_active():
                self.render(now, self._last_render_pointer)
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

    def close(self) -> None:
        """Release Tk images before destruction, never from later worker GC."""
        if self._closed:
            return
        self._closed = True
        self.stop()
        self.on_playback = lambda _event: None
        self.food_overlay.close()
        self._rest_renderer.clear()
        self.sprites.clear()
        self._sprite_cache.close()
        self._body_cache.close()

    def render(
        self, now: float, pointer: tuple[int, int],
        *,
        attention: CursorAttentionSnapshot | None = None,
    ) -> None:
        """Render an immutable cursor snapshot without mutating PetMind."""
        self._last_render_pointer = pointer
        if attention is not None:
            self._cursor_snapshot = attention
        decision = self.ports.choose_animation(
            now,
            pointer,
            self._cursor_snapshot.last_pointer_move,
            self._game_mode,
            self._active_action,
        )
        if decision.clear_action:
            self._active_action = None
            if (
                decision.sprite.animation == "pick_up"
                and decision.sprite.fixed_frame is not None
            ):
                # Empty hands are a visual offer; the cursor still owns the item.
                self.food_overlay.select(None)
        self.show_frame(
            decision.sprite.animation,
            now,
            fixed=decision.sprite.fixed_frame,
        )
