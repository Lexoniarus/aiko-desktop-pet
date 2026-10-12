"""Frameless Windows desktop companion using only Tkinter and prepared PNGs.

Aiko lives along the Windows taskbar, follows the cursor with 16 hand-authored
gaze sprites and exposes her care actions in a mouse-hover toolbar.
"""

from __future__ import annotations

import random
import time
import tkinter as tk
from dataclasses import replace
from tkinter import font as tkfont
from tkinter import messagebox

from .adaptive import AdaptiveRoutine
from .application.activity import ActivityCallbacks, ActivityCoordinator
from .application.attention import AttentionCoordinator
from .application.commands import CareCommand
from .application.controller import CareController, CareRuntime
from .ui.hover_ui import HoverUi, HoverUiPorts
from .application.router import ApplicationRouter
from .application.read_models import DesktopViewSource
from .animation import (
    FRAME_COUNTS as FRAME_COUNTS, FRAME_TIMINGS as FRAME_TIMINGS,
    FrameClock,
)
from .config import load_env_file
from .desktop_input import GlobalMouseClicks, idle_seconds_windows
from .dialogue import AikoMind, ComputerVoice, Reaction
from .movement import WalkController
from .routine import TimeContext, context_at
from .reaction_sequence import Cue, EMOTES as EMOTES
from .reaction_playback import ReactionPlayer, choose_idle_emote
from .storage import StateStore
from .system_activity import ActivityMonitor
from .taskbar import TaskbarTrack
from .ui.desktop_window import (
    DesktopWindow, FRAME_WIDTH as FRAME_WIDTH,
    FRAME_HEIGHT as FRAME_HEIGHT, MAGENTA as MAGENTA,
)
from .window_stack import WindowStack
from .asset_paths import (
    ASSETS as ASSETS,
    EMOTE_ASSETS as EMOTE_ASSETS,
    SCI_FI_UI as SCI_FI_UI,
)
from .ui.action_toolbar import ActionToolbar
from .ui.animated_pet import AnimatedPet, AnimatedPorts
from .ui.settings_popup import SettingsPopup
from .ui.speech_presenter import SpeechAnchor, SpeechPresenter
from .ui.status_panel import StatusPanel

TICK_MILLISECONDS = 140



class DesktopPet:
    def __init__(
        self, *, store: StateStore | None = None,
        activity_monitor: ActivityMonitor | None = None,
    ) -> None:
        self.store = store or StateStore()
        self.state, self.settings = self.store.load()
        self.adaptive = AdaptiveRoutine(self.store.load_memory())
        self.context: TimeContext = context_at(time.time())
        self._window = DesktopWindow(self.settings)
        self.root = self._window.root
        self.canvas = self._window.canvas
        self.background = self._window.background
        self._speech_font = (
            "Kenney Mini"
            if "Kenney Mini" in set(tkfont.families(root=self.root))
            else "Segoe UI"
        )
        self._last_tick = time.monotonic()
        self._last_track_check = self._last_tick
        self._action_until = 0.0
        self._action_state = "idle"
        self._last_saved = time.monotonic()
        self.mind = AikoMind(started_at=self._last_saved)
        self.application = ApplicationRouter(
            CareController(self.state, self.mind, self.adaptive),
        )
        self.computer_voice = ComputerVoice()
        self.activity_monitor = activity_monitor or ActivityMonitor()
        self.activity_monitor.set_enabled(self.settings.observe_computer)
        self._mouse_clicks = GlobalMouseClicks()
        self._mouse_clicks.clicked()  # establish a baseline before showing UI
        self._activity = ActivityCoordinator(
            self.state, self.settings, self.mind, self.adaptive,
            self.computer_voice, self.activity_monitor,
            ActivityCallbacks(
                read_idle_seconds=lambda: idle_seconds_windows(),
                start_review=lambda now: self._start_action(
                    "review", 1.4, started_at=now,
                ),
                react=self._react,
                action_until=lambda: self._action_until,
                last_spoken=lambda: self._last_spoken,
            ),
        )
        self._animated = AnimatedPet(
            self.root, self.canvas, self.state, self.settings,
            self.adaptive, self.activity_monitor,
            AnimatedPorts(
                track=lambda: self.track,
                toolbar_visible=lambda: (
                    self.toolbar is not None and self.toolbar.visible
                ),
                place_x=self._place_x,
                last_spoken=lambda: self._last_spoken,
                action_until=lambda: self._action_until,
                action_state=lambda: self._action_state,
                walk_pause=self._on_walk_pause,
                cursor_reaction=self._on_cursor_reaction,
            ),
        )
        self._closed = False
        self._scheduled_tick: str | None = None
        self._scheduled_greeting: str | None = None
        self._attention = AttentionCoordinator(
            self.state, self.settings, self.mind, self.computer_voice,
            self.activity_monitor, self.application,
            started_at=self._last_saved,
        )
        self._speech = SpeechPresenter(
            root=self.root,
            anchor=lambda: SpeechAnchor(
                x=self.settings.x or 0, y=self.settings.y or 0,
                width=self.width,
            ),
            font_name=self._speech_font,
            always_on_top=lambda: self.settings.always_on_top,
            restore_stack=lambda: self._overlay_stack.restore(),
            transparent_color=MAGENTA,
        )
        self._reaction_player = ReactionPlayer(
            schedule=self.root.after,
            cancel_timer=self.root.after_cancel,
            display_emote=self._show_emote,
            display_text=self.say,
            start_action=self._start_action,
            mark_spoken=self._mark_reaction_spoken,
            is_closed=lambda: self._closed,
        )
        self._overlay_stack = WindowStack(
            self._overlay_windows, enabled=self.settings.always_on_top,
        )
        self._views = DesktopViewSource(
            self.state, self.settings, self.mind, self.adaptive,
            self.activity_monitor,
            context=lambda: self.context,
            sprite_size=lambda: (self.width, self.height),
        )
        self._hover = HoverUi(
            self.root, self.canvas,
            HoverUiPorts(
                hover_snapshot=self._views.hover,
                status_snapshot=self._views.status,
                settings_snapshot=self._views.settings_view,
                anchor=self._views.anchor,
                care=self.interact,
                open_sprite_hover=self._on_enter,
                record_contact=self._record_hover_contact,
                save_position=self._save_hover_position,
                set_option=self._set_popup_option,
                toggle_scale=self.toggle_scale,
                forget_rhythm=self.forget_rhythm,
                reset_toolbar=self.reset_toolbar_position,
                center=self.center,
                quit=self.quit,
                move_speech=self._move_bubble,
                restore_stack=self._overlay_stack.restore,
                always_on_top=lambda: self.settings.always_on_top,
            ),
        )
        self._last_stack_check = self._last_tick
        self._setup_events()
        self._place_initially()
        self.root.update_idletasks()
        self.root.deiconify()
        self._overlay_stack.restore()
        self.activity_monitor.start()
        self._scheduled_greeting = self.root.after(460, self._greet_on_start)
        self._scheduled_tick = self.root.after(TICK_MILLISECONDS, self._tick)

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

    def _record_hover_contact(self, now: float) -> None:
        self.mind.last_contact = now

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

    def _overlay_windows(self) -> list[tk.Tk | tk.Toplevel]:
        """Back-to-front display order, independent of Tk's focus state."""
        windows: list[tk.Tk | tk.Toplevel] = [self.root]
        if self.toolbar is not None and self.toolbar.visible:
            windows.append(self.toolbar.window)
        if self.status_panel is not None:
            windows.append(self.status_panel.window)
        if self._bubble is not None:
            windows.append(self._bubble)
        if self.settings_popup is not None:
            windows.append(self.settings_popup.window)
        return windows

    def _load_sprites(self) -> dict[str, list[tk.PhotoImage]]:
        return self._animated.load_sprites()

    def _setup_events(self) -> None:
        # The care controls stay in the hover bar, but mouse clicks now
        # get their own expressive reactions. Shift+right-click opens settings.
        self.canvas.bind("<Enter>", self._on_enter)
        self.canvas.bind("<Button-1>", self._on_click_left)
        self.canvas.bind("<Button-3>", self._on_click_right)
        self.canvas.bind("<Shift-Button-3>", self._show_menu)
        self.root.bind("<Control-q>", lambda _event: self.quit())
        self.root.bind("<F2>", lambda _event: self.open_status())
        self.root.bind_all("<ButtonPress>", self._on_tk_press, add="+")
        self.root.bind_all("<FocusOut>", self._on_focus_out, add="+")
        self.root.protocol("WM_DELETE_WINDOW", self.quit)

    def _place_initially(self) -> None:
        self._place_x(self._window.initial_x())

    def _place_x(self, x: float) -> None:
        if not self._window.place_x(x):
            return
        if self.toolbar is not None and self.toolbar.visible:
            self.toolbar.place()
        self._move_bubble()

    def _save_hover_position(
        self, x: int | None, y: int | None,
    ) -> None:
        self.settings.toolbar_x = x
        self.settings.toolbar_y = y
        if x is not None:
            self._last_hover = time.monotonic()
        self._save()

    def _on_enter(self, _event: tk.Event | None = None) -> None:
        now = time.monotonic()
        # Only the first Enter after a long absence gets a welcome back;
        # repeatedly refreshing hover must not spam the same response.
        was_hidden = self.toolbar is None or not self.toolbar.visible
        reaction = (
            self.mind.return_to_pet(self.state, self.context, now)
            if was_hidden else None
        )
        self._last_hover = now
        self._walk_remaining = 0
        self._next_walk = now + random.uniform(3.0, 6.0)
        self._hover.show_toolbar()
        self._react(reaction, 2800)

    def _on_click_left(self, _event: tk.Event | None = None) -> None:
        self._on_enter()
        now = time.monotonic()
        self.adaptive.note_interaction(time.time())
        self._react_to_click(self.mind.click("left", self.state, self.context, now))

    def _on_click_right(self, _event: tk.Event | None = None) -> None:
        self._on_enter()
        now = time.monotonic()
        self.adaptive.note_interaction(time.time())
        self._react_to_click(self.mind.click("right", self.state, self.context, now))

    def _greet_on_start(self) -> None:
        if not self._attention.should_greet(time.monotonic()):
            return
        self._react(self.mind.say_event(
            "greeting", self.state, self.context, time.monotonic(),
        ), 3300)

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

    def _mark_reaction_spoken(self) -> None:
        self._attention.mark_spoken(time.monotonic())

    def _cancel_followup(self) -> None:
        """Cancel an older reaction, including every pending follow-up."""
        self._reaction_player.cancel()

    def _react_to_click(self, reaction: Reaction | None) -> None:
        if reaction is None:
            # Deliberate silence must not be followed by a stale second line.
            self._cancel_followup()
            self._hide_bubble()
            return
        # During rapid tapping, skip the opening icon so the actual response
        # remains visible instead of resetting the same 700ms cue forever.
        if len(self.mind.clicks) >= 3 and reaction.emote_before is not None:
            reaction = replace(reaction, emote_before=None)
        self._react(reaction, 2800)

    def _react(self, reaction: Reaction | None, duration_ms: int = 2600) -> None:
        """Delegate the timeline; the GUI only renders visual effects."""
        self._reaction_player.play(
            reaction, duration_ms, animate=not self.state.sleeping,
        )

    def _pointer_in_pet_or_toolbar(self, px: int, py: int) -> bool:
        return self._hover.pointer_inside(px, py)

    def _dismiss_if_outside(self, px: int, py: int) -> None:
        self._hover.dismiss_outside(px, py)

    def _on_tk_press(self, event: tk.Event) -> None:
        # Tk covers clicks inside Aiko's own windows; the Windows mouse-state
        # poll below also catches clicks in other applications.
        self._dismiss_if_outside(event.x_root, event.y_root)

    def _on_focus_out(self, _event: tk.Event) -> None:
        # Fallback for focus changes Tk receives while another app is clicked.
        if not self._closed:
            self.root.after(100, self._dismiss_after_focus_loss)

    def _dismiss_after_focus_loss(self) -> None:
        if self._closed:
            return
        self._dismiss_if_outside(
            self.root.winfo_pointerx(), self.root.winfo_pointery(),
        )

    def _refresh_hover(self, now: float) -> None:
        self._hover.refresh_hover(now)

    def _show_menu(self, event: tk.Event) -> None:
        self.toggle_settings_menu(event.x_root, event.y_root)

    def _set_popup_option(self, name: str, value: bool) -> None:
        setters = {
            "always_on_top": self.set_topmost,
            "auto_walk": self.set_auto_walk,
            "auto_routine": self.set_auto_routine,
            "follow_cursor": self.set_follow_cursor,
            "spontaneous_talk": self.set_spontaneous_talk,
            "observe_computer": self.set_observe_computer,
            "learn_rhythm": self.set_learn_rhythm,
        }
        setter = setters.get(name)
        if setter is None:
            raise ValueError(f"Unknown setting: {name}")
        setter(value)

    def toggle_settings_menu(self, x: int, y: int) -> None:
        self._hover.toggle_settings(x, y)

    def _poll_desktop_click(self) -> None:
        if self._mouse_clicks.clicked():
            self._dismiss_if_outside(
                self.root.winfo_pointerx(), self.root.winfo_pointery(),
            )

    def _start_action(
        self, state: str, duration: float, *, started_at: float | None = None,
    ) -> None:
        now = time.monotonic() if started_at is None else started_at
        self._action_state = state
        self._action_until = now + duration
        self._walk_remaining = 0
        self._next_walk = now + duration + random.uniform(2.5, 5)

    def interact(self, action: str) -> None:
        """Run a care command through the shared application boundary."""
        stamp = time.time()
        now = time.monotonic()
        result = self.application.dispatch(
            CareCommand.from_action(action),
            runtime=CareRuntime(
                wall_time=stamp,
                monotonic_time=now,
                auto_routine=self.settings.auto_routine,
                allow_bedtime=self._allow_bedtime(),
                allow_nap=self._allow_nap(),
                interrupt_nap=self._interrupt_nap(),
                effort=self._live_effort(),
            ),
        )
        self.context = result.context
        if result.reaction is None:
            # A fallback must not be overwritten by an older, queued aside.
            self._cancel_followup()
            self.say(result.fallback_text, 2450)
        else:
            self._react(result.reaction, 2900)
        if self.toolbar is not None:
            self.toolbar.refresh()
        self._refresh_status()
        self._save()

    def set_topmost(self, value: bool) -> None:
        self.settings.always_on_top = bool(value)
        self._overlay_stack.enabled = self.settings.always_on_top
        self.root.wm_attributes("-topmost", self.settings.always_on_top)
        if self.toolbar is not None:
            self.toolbar.window.wm_attributes("-topmost", self.settings.always_on_top)
        if self.status_panel is not None:
            self.status_panel.window.wm_attributes(
                "-topmost", self.settings.always_on_top,
            )
        if self._bubble is not None:
            self._bubble.wm_attributes("-topmost", self.settings.always_on_top)
        if self.settings_popup is not None:
            self.settings_popup.window.wm_attributes(
                "-topmost", self.settings.always_on_top,
            )
        self._overlay_stack.restore()
        self._save()

    def set_auto_walk(self, value: bool) -> None:
        self.settings.auto_walk = bool(value)
        self._walk_remaining = 0
        self._next_walk = time.monotonic() + random.uniform(2.5, 5)
        self._save()

    def set_auto_routine(self, enabled: bool) -> None:
        self.settings.auto_routine = bool(enabled)
        self.state.advance(time.time(), auto_routine=self.settings.auto_routine)
        self.context = context_at(time.time())
        if self.toolbar is not None:
            self.toolbar.refresh()
        self._refresh_status()
        self._save()

    def set_follow_cursor(self, enabled: bool) -> None:
        self.settings.follow_cursor = bool(enabled)
        self._gaze_sector = None
        self._save()

    def set_spontaneous_talk(self, enabled: bool) -> None:
        self.settings.spontaneous_talk = bool(enabled)
        self._attention.reschedule_comment(time.monotonic())
        self._save()

    def set_learn_rhythm(self, enabled: bool) -> None:
        self.settings.learn_rhythm = bool(enabled)
        self._save()

    def forget_rhythm(self) -> None:
        self.adaptive.forget_profile()
        self._refresh_status()
        self._save()

    def set_observe_computer(self, enabled: bool) -> None:
        self.settings.observe_computer = bool(enabled)
        self.activity_monitor.set_enabled(self.settings.observe_computer)
        self.computer_voice.reset_samples()
        self._last_hardware_sample = 0.0
        self._last_adaptive_sample = 0.0
        self._pending_computer_line = None
        if not enabled:
            self.mind.set_situation(None)
        if self.toolbar is not None:
            self.toolbar.refresh()
        self._save()

    def toggle_scale(self) -> None:
        original_center = (self.settings.x or 0) + self.width / 2
        self.settings.scale = 2 if self.settings.scale == 1 else 1
        self._window.resize()
        self._animated.reload_sprites()
        self._last_sprite_key = None
        self._gaze_sector = None
        self._placed = False  # Force Tk geometry update even at unchanged x/y.
        self._place_x(original_center - self.width / 2)
        if self.toolbar is not None and self.toolbar.visible:
            self.toolbar.place()
        self._save()

    def reset_toolbar_position(self) -> None:
        if self.toolbar is not None:
            self.toolbar.reset_position()
        else:
            self.settings.toolbar_x = None
            self.settings.toolbar_y = None
            self._save()

    def center(self) -> None:
        self._place_x((self.track.left + self.track.right - self.width) / 2)
        self._walk_remaining = 0
        self._save()

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

    def _idle_emote(self) -> None:
        """Occasional unspoken state, never interrupting an existing scene."""
        if self._bubble is not None or self._followup_timeout is not None:
            return
        emote = choose_idle_emote(
            energy=self.state.energy,
            satiety=self.state.satiety,
            mood=self.state.mood,
            affection=self.state.affection,
        )
        self._show_emote(emote, 1100)

    def say(self, phrase: str, duration_ms: int = 1800) -> None:
        self._speech.show_text(phrase, duration_ms)

    def _hide_bubble(self) -> None:
        self._speech.hide()

    def _gaze_direction(self, pointer: tuple[int, int]) -> int | None:
        return self._animated.gaze_direction(pointer)

    def _observe_pointer(self, now: float) -> tuple[int, int]:
        return self._animated.observe_pointer(now)

    def _on_cursor_reaction(self, event: str, now: float) -> None:
        self._react(self.mind.say_event(
            event, self.state, self.context, now,
        ))

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

    def _on_walk_pause(self, now: float) -> None:
        self._react(self.mind.say_event(
            "walk_pause", self.state, self.context, now,
        ))

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

    def _advance_pet_lifecycle(self, now: float, wall_time: float) -> None:
        progress = self._activity.advance_lifecycle(
            now, wall_time, self.context,
        )
        self.context = progress.context
        if progress.period_changed:
            if self.toolbar is not None:
                self.toolbar.refresh()
            if self.settings.spontaneous_talk and progress.sleep_changed:
                event = "sleep" if self.state.sleeping else "wake"
                self._react(self.mind.say_event(
                    event, self.state, self.context, now,
                ))

    def _refresh_taskbar_track(self, now: float) -> None:
        """Reposition Aiko only when taskbar geometry actually changes."""
        if now - self._last_track_check >= 4.0:
            self._last_track_check = now
            if self._window.update_track():
                self._place_x(self.settings.x or self.track.left)

    def _render_current_sprite(
        self, now: float, elapsed_seconds: float, pointer: tuple[int, int],
    ) -> None:
        self._animated.render(now, elapsed_seconds, pointer)

    def _maybe_show_idle_emote(self, now: float) -> None:
        """An independent policy decides whether Aiko is free for a gesture."""
        animation = self._attention.idle_animation(
            now, action_until=self._action_until,
            walking=self._walk_remaining != 0,
            toolbar_visible=bool(self.toolbar and self.toolbar.visible),
        )
        if animation is not None:
            self._start_action(animation, 1.6)
            self._idle_emote()

    def _maybe_speak_spontaneously(self, now: float) -> None:
        decision = self._attention.spontaneous(
            now, self.context,
            toolbar_visible=bool(self.toolbar and self.toolbar.visible),
        )
        if decision.due:
            self._react(decision.reaction, 3600)

    def _present_pending_notification(self, now: float) -> None:
        """The Tk event loop alone turns queued data into rendered text."""
        notification = self._attention.next_notification(
            now,
            action_until=self._action_until,
            bubble_visible=self._bubble is not None,
            popup_visible=self.settings_popup is not None,
            toolbar_visible=bool(self.toolbar and self.toolbar.visible),
        )
        if notification is None:
            return
        self.say(f"{notification.title}: {notification.message}", 3500)
        self._attention.mark_spoken(now)

    def _refresh_overlays_and_autosave(self, now: float) -> None:
        """Refresh visible panels, window layering and periodic persistence."""
        if self.toolbar is not None and self.toolbar.visible:
            self.toolbar.refresh()
        self._refresh_status()
        # Focus changes from browser voice input can reorder foreign topmost
        # windows. Repair only after an actual overlapping z-order loss.
        if now - self._last_stack_check >= 1.5:
            self._last_stack_check = now
            self._overlay_stack.maintain()
        if now - self._last_saved >= 55:
            self._save()

    def _tick(self) -> None:
        """Coordinate one desktop update; behavior is owned by small methods."""
        if self._closed:
            return
        # A manual test refresh must not create a second scheduled timer.
        if self._scheduled_tick is not None:
            self.root.after_cancel(self._scheduled_tick)
            self._scheduled_tick = None
        now = time.monotonic()
        dt = max(0.0, min(0.5, now - self._last_tick))
        self._last_tick = now
        stamp = time.time()
        self._advance_pet_lifecycle(now, stamp)
        self._refresh_taskbar_track(now)
        self._poll_desktop_click()
        self._refresh_hover(now)
        self._react_to_computer(now)
        pointer = self._observe_pointer(now)
        self._render_current_sprite(now, dt, pointer)
        self._maybe_show_idle_emote(now)
        self._maybe_speak_spontaneously(now)
        self._present_pending_notification(now)
        self._refresh_overlays_and_autosave(now)
        if not self._closed:
            self._scheduled_tick = self.root.after(TICK_MILLISECONDS, self._tick)

    def _save(self) -> None:
        self.state.advance(
            time.time(), auto_routine=self.settings.auto_routine,
            allow_bedtime=self._allow_bedtime(),
            allow_nap=self._allow_nap(),
            interrupt_nap=self._interrupt_nap(),
            effort=self._live_effort(),
        )
        try:
            self.store.save(self.state, self.settings,
                            adaptive=self.adaptive.memory)
        except OSError as error:
            messagebox.showwarning(
                "Aiko", f"Spielstand konnte nicht gespeichert werden:\n{error}",
            )
        self._last_saved = time.monotonic()

    def quit(self) -> None:
        if self._closed:
            return
        self._closed = True
        self.application.close()
        for scheduled in (self._scheduled_tick, self._scheduled_greeting):
            if scheduled is not None:
                self.root.after_cancel(scheduled)
        self.activity_monitor.stop()
        self._save()
        self._cancel_followup()
        self._hide_bubble()
        if self.settings_popup is not None:
            self.settings_popup.close()
        self._hover.close_toolbar()
        if self.status_panel is not None:
            self.status_panel.close()
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    load_env_file()
    app = DesktopPet()
    app.run()


if __name__ == "__main__":
    main()
