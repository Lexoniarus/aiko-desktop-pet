"""Typed *legacy-only* adapter for old DesktopPet methods and attributes.

All implementations below are thin forwards to the objects that now own the
data or Tk behavior. New code must inject narrow ports instead of depending
on this facade or inheriting from it; it exists for backwards compatibility.
"""

from __future__ import annotations

import tkinter as tk

from ..animation import FrameClock
from ..application.activity import ActivityCoordinator
from ..application.attention import AttentionCoordinator
from ..movement import WalkController
from ..reaction_playback import ReactionPlayer
from ..reaction_sequence import Cue
from ..routine import TimeContext
from ..taskbar import TaskbarTrack
from ..ui.action_toolbar import ActionToolbar
from ..ui.animated_pet import AnimatedPet
from ..ui.desktop_window import DesktopWindow
from ..ui.hover_ui import HoverUi
from ..ui.settings_popup import SettingsPopup
from ..ui.speech_presenter import SpeechPresenter
from ..ui.status_panel import StatusPanel
from .runtime import DesktopRuntime
from .persistence import DesktopPersistence
from .maintenance import DesktopMaintenance


class DesktopCompatibility:
    """Explicit typed compatibility surface; owns no behavior or state."""

    _window: DesktopWindow
    _animated: AnimatedPet
    _hover: HoverUi
    _activity: ActivityCoordinator
    _attention: AttentionCoordinator
    _speech: SpeechPresenter
    _reaction_player: ReactionPlayer
    _runtime: DesktopRuntime
    _persistence: DesktopPersistence
    _maintenance: DesktopMaintenance
    context: TimeContext


    @property
    def _last_track_check(self) -> float:
        return self._maintenance.last_track_check

    @_last_track_check.setter
    def _last_track_check(self, value: float) -> None:
        self._maintenance.last_track_check = value

    @property
    def _last_stack_check(self) -> float:
        return self._maintenance.last_stack_check

    @_last_stack_check.setter
    def _last_stack_check(self, value: float) -> None:
        self._maintenance.last_stack_check = value

    @property
    def _last_saved(self) -> float:
        return self._persistence.last_saved

    @_last_saved.setter
    def _last_saved(self, value: float) -> None:
        self._persistence.last_saved = value

    @property
    def _last_tick(self) -> float:
        return self._runtime.last_tick

    @_last_tick.setter
    def _last_tick(self, value: float) -> None:
        self._runtime.last_tick = value

    @property
    def _scheduled_tick(self) -> str | None:
        return self._runtime.scheduled_tick

    @_scheduled_tick.setter
    def _scheduled_tick(self, value: str | None) -> None:
        self._runtime.scheduled_tick = value

    @property
    def _scheduled_greeting(self) -> str | None:
        return self._runtime.scheduled_greeting

    @_scheduled_greeting.setter
    def _scheduled_greeting(self, value: str | None) -> None:
        self._runtime.scheduled_greeting = value

    @property
    def track(self) -> TaskbarTrack:
        return self._window.track

    @track.setter
    def track(self, value: TaskbarTrack) -> None:
        self._window.track = value

    @property
    def width(self) -> int:
        return self._window.width

    @property
    def height(self) -> int:
        return self._window.height

    @property
    def _placed(self) -> bool:
        return self._window.placed

    @_placed.setter
    def _placed(self, value: bool) -> None:
        self._window.placed = value

    @property
    def _last_spoken(self) -> float:
        return self._attention.last_spoken

    @_last_spoken.setter
    def _last_spoken(self, value: float) -> None:
        self._attention.last_spoken = value

    @property
    def _next_comment(self) -> float:
        return self._attention.next_comment

    @_next_comment.setter
    def _next_comment(self, value: float) -> None:
        self._attention.next_comment = value

    @property
    def _next_idle_emote(self) -> float:
        return self._attention.next_idle_emote

    @_next_idle_emote.setter
    def _next_idle_emote(self, value: float) -> None:
        self._attention.next_idle_emote = value

    @property
    def toolbar(self) -> ActionToolbar | None:
        """Public compatibility view of the independent hover window."""
        return self._hover.toolbar

    @property
    def status_panel(self) -> StatusPanel | None:
        return self._hover.status_panel

    @property
    def settings_popup(self) -> SettingsPopup | None:
        return self._hover.settings_popup

    @property
    def _menu_is_open(self) -> bool:
        return self._hover.menu_is_open

    @property
    def _last_hover(self) -> float:
        return self._hover.last_hover

    @_last_hover.setter
    def _last_hover(self, value: float) -> None:
        self._hover.last_hover = value

    @property
    def _last_hardware_sample(self) -> float:
        return self._activity.last_hardware_sample

    @_last_hardware_sample.setter
    def _last_hardware_sample(self, value: float) -> None:
        self._activity.last_hardware_sample = value

    @property
    def _last_adaptive_sample(self) -> float:
        return self._activity.last_adaptive_sample

    @_last_adaptive_sample.setter
    def _last_adaptive_sample(self, value: float) -> None:
        self._activity.last_adaptive_sample = value

    @property
    def _pending_computer_line(self) -> tuple[str, float] | None:
        return self._activity.pending_computer_line

    @_pending_computer_line.setter
    def _pending_computer_line(
        self, value: tuple[str, float] | None,
    ) -> None:
        self._activity.pending_computer_line = value

    @property
    def _movement(self) -> WalkController:
        return self._animated.movement

    @property
    def _frame_clock(self) -> FrameClock:
        return self._animated.frame_clock

    @property
    def sprites(self) -> dict[str, list[tk.PhotoImage]]:
        return self._animated.sprites

    @property
    def image_item(self) -> int:
        return self._animated.image_item

    @property
    def _gaze_sector(self) -> int | None:
        return self._animated.gaze_sector

    @_gaze_sector.setter
    def _gaze_sector(self, value: int | None) -> None:
        self._animated.gaze_sector = value

    def _load_sprites(self) -> dict[str, list[tk.PhotoImage]]:
        return self._animated.load_sprites()

    @property
    def _followup_timeout(self) -> str | None:
        """Compatibility view of the playback scheduler's pending timer."""
        return self._reaction_player.pending_timer

    @property
    def _speech_generation(self) -> int:
        return self._reaction_player.generation

    @property
    def _reaction_cues(self) -> tuple[Cue, ...]:
        return self._reaction_player.cues

    def _pointer_in_pet_or_toolbar(self, px: int, py: int) -> bool:
        return self._hover.pointer_inside(px, py)

    def _dismiss_if_outside(self, px: int, py: int) -> None:
        self._hover.dismiss_outside(px, py)

    def _refresh_hover(self, now: float) -> None:
        self._hover.refresh_hover(now)

    def toggle_settings_menu(self, x: int, y: int) -> None:
        self._hover.toggle_settings(x, y)

    def open_status(self) -> None:
        self._hover.open_status()

    def _refresh_status(self) -> None:
        self._hover.refresh_status()

    @property
    def _bubble(self) -> tk.Toplevel | None:
        """Compatibility view; the speech presenter owns the real widget."""
        return self._speech.bubble

    @property
    def _bubble_timeout(self) -> str | None:
        return self._speech.pending_timer

    @property
    def _emote_images(self) -> dict[str, tk.PhotoImage]:
        return self._speech.emote_images

    def _move_bubble(self) -> None:
        self._speech.move()

    def _show_emote(self, emote: str, duration_ms: int = 900) -> None:
        self._speech.show_emote(emote, duration_ms)

    def say(self, phrase: str, duration_ms: int = 1800) -> None:
        self._speech.show_text(phrase, duration_ms)

    def _hide_bubble(self) -> None:
        self._speech.hide()

    def _gaze_direction(self, pointer: tuple[int, int]) -> int | None:
        return self._animated.gaze_direction(pointer)

    def _observe_pointer(self, now: float) -> tuple[int, int]:
        return self._animated.observe_pointer(now)

    @property
    def _walk_remaining(self) -> float:
        """Legacy control surface: walking state now belongs to WalkController."""
        return self._movement.remaining_distance

    @_walk_remaining.setter
    def _walk_remaining(self, value: float) -> None:
        self._movement.remaining_distance = value

    @property
    def _next_walk(self) -> float:
        return self._movement.next_walk_at

    @_next_walk.setter
    def _next_walk(self, value: float) -> None:
        self._movement.next_walk_at = value

    def _maybe_walk(self, now: float, dt: float) -> str | None:
        return self._animated.maybe_walk(now, dt)

    def _show_frame(
        self, state: str, now: float, *, fixed: int | None = None,
    ) -> None:
        self._animated.show_frame(state, now, fixed=fixed)

    def _react_to_computer(self, now: float) -> None:
        self._activity.react_to_computer(now, self.context)

    def _interrupt_nap(self) -> bool:
        return self._activity.interrupt_nap()

    def _allow_nap(self) -> bool:
        return self._activity.allow_nap()

    def _allow_bedtime(self) -> bool | None:
        return self._activity.allow_bedtime()

    def _live_effort(self) -> float | None:
        return self._activity.live_effort()

    def _observe_adaptive(self, now: float, stamp: float) -> None:
        self._activity.observe_adaptive(now, stamp)

    def _render_current_sprite(
        self, now: float, elapsed_seconds: float, pointer: tuple[int, int],
    ) -> None:
        self._animated.render(now, elapsed_seconds, pointer)
