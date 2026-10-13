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
from .desktop.compatibility import DesktopCompatibility
from .desktop.runtime import (
    DesktopRuntime, TICK_MILLISECONDS as TICK_MILLISECONDS,
)
from .desktop.persistence import DesktopPersistence
from .desktop.maintenance import DesktopMaintenance
from .application.attention import AttentionCoordinator
from .application.commands import CareCommand
from .application.controller import CareController, CareRuntime
from .ui.hover_ui import HoverUi, HoverUiPorts
from .application.router import ApplicationRouter
from .application.read_models import DesktopViewSource
from .animation import (
    FRAME_COUNTS as FRAME_COUNTS, FRAME_TIMINGS as FRAME_TIMINGS,
    FrameClock as FrameClock,
)
from .config import load_env_file
from .desktop_input import idle_seconds_windows
from .desktop.input import DesktopInput, DesktopInputActions
from .dialogue import AikoMind, ComputerVoice, Reaction
from .movement import WalkController as WalkController
from .routine import TimeContext, context_at
from .reaction_sequence import Cue as Cue, EMOTES as EMOTES
from .reaction_playback import ReactionPlayer, choose_idle_emote
from .storage import StateStore
from .system_activity import ActivityMonitor
from .taskbar import TaskbarTrack as TaskbarTrack
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
from .ui.action_toolbar import ActionToolbar as ActionToolbar
from .ui.animated_pet import AnimatedPet, AnimatedPorts
from .ui.settings_popup import SettingsPopup as SettingsPopup
from .ui.speech_presenter import SpeechAnchor, SpeechPresenter
from .ui.status_panel import StatusPanel as StatusPanel


class DesktopPet(DesktopCompatibility):
    _overlay_stack: WindowStack

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
        self._runtime = DesktopRuntime(
            self, schedule=self.root.after, cancel=self.root.after_cancel,
        )
        self._action_until = 0.0
        self._action_state = "idle"
        self._persistence = DesktopPersistence(
            self.store, self.state, self.settings, self.adaptive, self,
        )
        self.mind = AikoMind(started_at=self._last_saved)
        self.application = ApplicationRouter(
            CareController(self.state, self.mind, self.adaptive),
        )
        self.computer_voice = ComputerVoice()
        self.activity_monitor = activity_monitor or ActivityMonitor()
        self.activity_monitor.set_enabled(self.settings.observe_computer)
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
        self._maintenance = DesktopMaintenance(
            check_taskbar=self._window.update_track,
            reposition=lambda: self._place_x(
                self.settings.x or self.track.left,
            ),
            maintain_stack=self._overlay_stack.maintain,
            started_at=self._last_tick,
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
        self._input = DesktopInput(
            self.root, self.canvas,
            DesktopInputActions(
                enter=self._on_enter,
                left_click=self._on_click_left,
                right_click=self._on_click_right,
                show_menu=self.toggle_settings_menu,
                dismiss_outside=self._dismiss_if_outside,
                open_status=self.open_status,
                quit=self.quit,
                closed=lambda: self._closed,
            ),
        )
        self._setup_events()
        self._place_initially()
        self.root.update_idletasks()
        self.root.deiconify()
        self._overlay_stack.restore()
        self.activity_monitor.start()
        self._runtime.start()

    def _record_hover_contact(self, now: float) -> None:
        self.mind.last_contact = now

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

    def _setup_events(self) -> None:
        self._input.initialize()

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

    def _on_tk_press(self, event: tk.Event) -> None:
        self._input.on_tk_press(event)

    def _on_focus_out(self, event: tk.Event) -> None:
        self._input.on_focus_out(event)

    def _dismiss_after_focus_loss(self) -> None:
        self._input.dismiss_after_focus_loss()

    def _show_menu(self, event: tk.Event) -> None:
        self._input.on_menu(event)

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

    def _poll_desktop_click(self) -> None:
        self._input.poll_global_click()

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
        self._window.set_topmost(self.settings.always_on_top)
        self._hover.set_topmost(self.settings.always_on_top)
        self._speech.set_topmost(self.settings.always_on_top)
        self._overlay_stack.restore()
        self._save()

    def set_auto_walk(self, value: bool) -> None:
        self._animated.set_auto_walk(value, time.monotonic())
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
        self._animated.set_follow_cursor(enabled)
        self._save()

    def set_spontaneous_talk(self, enabled: bool) -> None:
        self._attention.set_spontaneous_talk(enabled, time.monotonic())
        self._save()

    def set_learn_rhythm(self, enabled: bool) -> None:
        self.settings.learn_rhythm = bool(enabled)
        self._save()

    def forget_rhythm(self) -> None:
        self.adaptive.forget_profile()
        self._refresh_status()
        self._save()

    def set_observe_computer(self, enabled: bool) -> None:
        self._activity.set_observation_enabled(enabled)
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

    def _on_cursor_reaction(self, event: str, now: float) -> None:
        self._react(self.mind.say_event(
            event, self.state, self.context, now,
        ))

    def _on_walk_pause(self, now: float) -> None:
        self._react(self.mind.say_event(
            "walk_pause", self.state, self.context, now,
        ))

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
        self._maintenance.refresh_track(now)

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
        self._maintenance.refresh_stack(now)
        if self._persistence.due(now):
            self._save()

    def _tick(self) -> None:
        """Compatibility entrypoint; DesktopRuntime owns phase ordering."""
        self._runtime.tick()

    def _save(self) -> None:
        """Show persistence failures; disk I/O and catch-up live elsewhere."""
        failure = self._persistence.save()
        if failure is not None:
            messagebox.showwarning(
                "Aiko", f"Spielstand konnte nicht gespeichert werden:\n{failure}",
            )

    def quit(self) -> None:
        if self._closed:
            return
        self._closed = True
        self.application.close()
        self._runtime.stop()
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
