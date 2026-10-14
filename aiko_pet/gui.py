"""Frameless Windows desktop companion using only Tkinter and prepared PNGs.

Aiko lives along the Windows taskbar, follows the cursor with 16 hand-authored
gaze sprites and exposes her care actions in a mouse-hover toolbar.
"""

from __future__ import annotations

import time
import tkinter as tk
from dataclasses import replace
from tkinter import font as tkfont
from tkinter import messagebox

from .application.session import PetSessionRestorer
from .application.settings import SettingKey
from .application.activity import ActivityCallbacks, ActivityCoordinator
from .desktop.preferences import DesktopPreferencePorts, DesktopPreferences
from .desktop.runtime import (
    DesktopRuntime, DesktopTickPorts,
)
from .desktop.persistence import DesktopPersistence
from .desktop.maintenance import DesktopMaintenance
from .application.attention import AttentionCoordinator
from .application.commands import CareCommand
from .application.controller import CareController
from .application.active_time import ActiveSessionClock
from .pet.food import DEFAULT_FOOD_ID, FoodId
from .infrastructure.active_time import active_uptime_seconds
from .ui.hover_ui import HoverUi, HoverUiPorts
from .ui.game_speech import GameSpeech
from .application.game_experience import (
    GameExperienceCoordinator, experience_from_rock_paper_scissors,
)
from .application.router import ApplicationRouter
from .presentation.read_models import DesktopPresentation
from .config import load_env_file
from .desktop.global_input import (
    idle_seconds_windows, mouse_buttons_down_windows,
)
from .desktop.input import DesktopInput, DesktopInputActions
from .desktop.lifecycle import DesktopLifecycle
from .desktop.farewell import FarewellSequence
from .personality.mind import AikoMind
from .personality.workload_events import WorkloadEventDetector
from .personality.catalog import Reaction
from .pet.routine import TimeContext, context_at
from .presentation.reaction_playback import ReactionPlayer, choose_idle_emote
from .infrastructure.character_assets import load_character_catalog
from .infrastructure.persistence import StateStore
from .infrastructure.hardware.monitor import ActivityMonitor
from .ui.desktop_window import (
    DesktopWindow, MAGENTA,
)
from .desktop.window_stack import WindowStack
from .ui.animated_pet import AnimatedPet, AnimatedPorts
from .ui.speech_presenter import SpeechAnchor, SpeechPresenter


class DesktopPet:
    """Compose one desktop session from its owning components.

    Character, settings, input, window and simulation behavior belong to
    their respective components, not to a second state stored on this shell.
    """

    _overlay_stack: WindowStack

    def __init__(
        self, *, store: StateStore | None = None,
        activity_monitor: ActivityMonitor | None = None,
    ) -> None:
        self.store = store or StateStore()
        session = PetSessionRestorer(self.store).restore()
        self.state = session.state
        self.settings = session.settings
        self.adaptive = session.adaptive
        self.context: TimeContext = context_at(time.time())
        self._character_assets = load_character_catalog()
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
            DesktopTickPorts(
                is_closed=lambda: self._closed,
                request_tick=self._tick,
                greet=self._greet_on_start,
                advance_lifecycle=self._advance_pet_lifecycle,
                refresh_taskbar=lambda now: self._maintenance.refresh_track(now),
                poll_desktop_clicks=lambda: self._input.poll_global_click(),
                refresh_hover=lambda now: self._hover.refresh_hover(now),
                observe_computer=lambda now: self._activity.react_to_computer(
                    now, self.context,
                ),
                observe_pointer=lambda now: self._animated.observe_pointer(now),
                render_character=lambda now, elapsed, pointer: (
                    self._animated.render(now, elapsed, pointer)
                ),
                show_idle_emote=self._maybe_show_idle_emote,
                speak_spontaneously=self._maybe_speak_spontaneously,
                present_notification=self._present_pending_notification,
                refresh_overlays_and_save=self._refresh_overlays_and_autosave,
            ),
            schedule=self.root.after,
            cancel=self.root.after_cancel,
        )
        self._action_until = 0.0
        self._action_state = "idle"
        self._persistence = DesktopPersistence(
            self.store, self.state, self.settings, self.adaptive,
        )
        self.mind = AikoMind(started_at=self._persistence.last_saved)
        active_clock = ActiveSessionClock(active_uptime_seconds)
        self.application = ApplicationRouter(
            CareController(self.state, self.mind, self.adaptive, clock=active_clock),
            game_experience=GameExperienceCoordinator(
                self.state, self.mind, self.adaptive, clock=active_clock,
            ),
        )
        self.workload_events = WorkloadEventDetector()
        self.activity_monitor = activity_monitor or ActivityMonitor()
        self.activity_monitor.set_enabled(self.settings.observe_computer)
        self._activity = ActivityCoordinator(
            self.state, self.settings, self.mind, self.adaptive,
            self.workload_events, self.activity_monitor,
            ActivityCallbacks(
                read_idle_seconds=lambda: idle_seconds_windows(),
                start_review=lambda now: self._start_action(
                    "review", 1.4, started_at=now,
                ),
                react=self._react,
                action_until=lambda: self._action_until,
                last_spoken=lambda: self._attention.last_spoken,
                read_pointer=lambda: (
                    self.root.winfo_pointerx(), self.root.winfo_pointery(),
                ),
                read_mouse_buttons=mouse_buttons_down_windows,
            ),
            clock=active_clock,
        )
        self._animated = AnimatedPet(
            self.root, self.canvas, self.state, self.settings,
            self.adaptive, self.activity_monitor,
            AnimatedPorts(
                track=lambda: self._window.track,
                toolbar_visible=lambda: self._hover.interaction_active,
                place_x=self._place_x,
                action_until=lambda: self._action_until,
                action_state=lambda: self._action_state,
                walk_finished=self._on_walk_finished,
                cursor_moved=self._on_cursor_moved,
                extend_action=self._extend_action,
            ),
            assets=self._character_assets,
        )
        self._closed = False
        self._attention = AttentionCoordinator(
            self.state, self.settings, self.mind, self.workload_events,
            self.activity_monitor, self.application,
            started_at=self._persistence.last_saved,
        )
        self._speech = SpeechPresenter(
            root=self.root,
            anchor=lambda: SpeechAnchor(
                x=self.settings.x or 0, y=self.settings.y or 0,
                width=self._window.width,
            ),
            font_name=self._speech_font,
            always_on_top=lambda: self.settings.always_on_top,
            restore_stack=lambda: self._overlay_stack.restore(),
            transparent_color=MAGENTA,
        )
        self._reaction_player = ReactionPlayer(
            schedule=self.root.after,
            cancel_timer=self.root.after_cancel,
            display_emote=self._speech.show_emote,
            display_text=self._speech.show_text,
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
                self.settings.x or self._window.track.left,
            ),
            maintain_stack=self._overlay_stack.maintain,
            started_at=self._runtime.last_tick,
        )
        self._views = DesktopPresentation(
            self.state, self.settings, self.mind, self.adaptive,
            self.activity_monitor,
            context=lambda: self.context,
            sprite_size=lambda: (self._window.width, self._window.height),
        )
        self._hover = HoverUi(
            self.root, self.canvas,
            HoverUiPorts(
                hover_snapshot=self._views.hover,
                status_snapshot=self._views.status,
                settings_snapshot=self._views.settings_view,
                anchor=self._views.anchor,
                care=self.interact,
                feed=lambda selected: self.interact(
                    "feed", food_id=selected,
                ),
                game_completed=lambda score: self.application.complete_game(
                    experience_from_rock_paper_scissors(score),
                    runtime=self._activity.care_runtime(time.time(), time.monotonic()),
                ),
                open_sprite_hover=self._on_enter,
                record_contact=self._record_hover_contact,
                save_position=self._save_hover_position,
                set_option=self._set_popup_option,
                toggle_scale=self.toggle_scale,
                forget_rhythm=self.forget_rhythm,
                reset_toolbar=self.reset_toolbar_position,
                center=self.center,
                quit=lambda: self._farewell.begin(),
                move_speech=self._speech.move,
                restore_stack=self._overlay_stack.restore,
                always_on_top=lambda: self.settings.always_on_top,
                game_speech=GameSpeech(
                    self._reaction_player, self._speech,
                    self._mark_reaction_spoken,
                    self._animated.set_game_mode,
                    lambda name: self._start_action(name, 0),
                ),
            ),
        )
        self._input = DesktopInput(
            self.root, self.canvas,
            DesktopInputActions(
                enter=self._on_enter,
                left_click=self._on_click_left,
                right_click=self._on_click_right,
                show_menu=self._hover.open_settings,
                dismiss_outside=self._hover.dismiss_outside,
                open_status=self._hover.open_status,
                quit=self.quit,
                closed=lambda: self._closed,
            ),
        )
        self._preferences = DesktopPreferences(
            settings=self.settings,
            state=self.state,
            adaptive=self.adaptive,
            activity=self._activity,
            attention=self._attention,
            animated=self._animated,
            window=self._window,
            hover=self._hover,
            speech=self._speech,
            overlay_stack=self._overlay_stack,
            ports=DesktopPreferencePorts(
                place_x=self._place_x,
                save=self._save,
                set_context=self._set_context,
            ),
        )
        self._lifecycle = DesktopLifecycle(
            root=self.root,
            inputs=self._input,
            runtime=self._runtime,
            monitor=self.activity_monitor,
            application=self.application,
            overlays=self._overlay_stack,
            hover=self._hover,
            reaction=self._reaction_player,
            speech=self._speech,
            place_initially=self._place_initially,
            save=self._save,
            stop_animation=self._animated.stop,
        )
        self._farewell = FarewellSequence(
            schedule=self.root.after, cancel=self.root.after_cancel,
            prepare=self._lifecycle.prepare_farewell,
            animate=lambda: self._start_action("waving-greeting", 0),
            say=self._speech.show_text, finish=self.quit,
            seconds=self._character_assets.clips["waving-greeting"].duration_seconds,
        )
        self._lifecycle.start()

    def _record_hover_contact(self, now: float) -> None:
        self.mind.last_contact = now

    def _overlay_windows(self) -> list[tk.Tk | tk.Toplevel]:
        """Back-to-front display order, independent of Tk's focus state."""
        windows: list[tk.Tk | tk.Toplevel] = [self.root]
        if self._hover.toolbar is not None and self._hover.toolbar.visible:
            windows.append(self._hover.toolbar.window)
        if self._hover.game_window is not None:
            windows.append(self._hover.game_window.window)
        if self._hover.food_menu is not None:
            windows.append(self._hover.food_menu.window)
        if self._speech.bubble is not None:
            windows.append(self._speech.bubble)
        if self._hover.settings_window is not None:
            windows.append(self._hover.settings_window.window)
        return windows

    def _setup_events(self) -> None:
        self._input.initialize()

    def _place_initially(self) -> None:
        self._place_x(self._window.initial_x())

    def _place_x(self, x: float) -> None:
        if not self._window.place_x(x):
            return
        if self._hover.toolbar is not None and self._hover.toolbar.visible:
            self._hover.toolbar.place()
        self._speech.move()

    def _set_context(self, context: TimeContext) -> None:
        """Update the session's current local-time snapshot."""
        self.context = context

    def _save_hover_position(
        self, x: int | None, y: int | None,
    ) -> None:
        self._preferences.record_toolbar_position(x, y)

    def _on_enter(self, _event: tk.Event | None = None) -> None:
        now = time.monotonic()
        was_hidden = self._hover.toolbar is None or not self._hover.toolbar.visible
        reaction = (
            self.mind.return_to_pet(self.state, self.context, now)
            if was_hidden else None
        )
        self._hover.last_hover = now
        self._animated.movement.interrupt()
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
        if self._hover.game_open:
            return
        if reaction is None:
            self._cancel_followup()
            self._speech.hide()
            return
        if len(self.mind.clicks) >= 3 and reaction.emote_before is not None:
            reaction = replace(reaction, emote_before=None)
        self._react(reaction, 2800)

    def _react(self, reaction: Reaction | None, duration_ms: int = 2600) -> None:
        """Delegate the timeline; the GUI only renders visual effects."""
        if self._hover.game_open:
            return
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

    def _set_popup_option(self, name: SettingKey, value: bool) -> None:
        """Preserve the public desktop callback while routing to its owner."""
        self._preferences.set_option(name, value)

    def _poll_desktop_click(self) -> None:
        self._input.poll_global_click()

    def _start_action(
        self, state: str, duration: float, *, started_at: float | None = None,
    ) -> None:
        now = time.monotonic() if started_at is None else started_at
        clip = self._character_assets.clips[state]
        if not clip.loop:
            duration = clip.duration_seconds
        self._action_state = state
        self._action_until = now + duration
        self._animated.begin_action(state, now)

    def _extend_action(self, deadline: float) -> None:
        self._action_until = max(self._action_until, deadline)

    def interact(
        self, action: str, *, food_id: FoodId | None = None,
    ) -> None:
        """Run a care command through the shared application boundary."""
        stamp = time.time()
        now = time.monotonic()
        result = self.application.dispatch(
            CareCommand.from_action(action, food_id=food_id),
            runtime=self._activity.care_runtime(stamp, now),
        )
        self.context = result.context
        if result.food_consumed:
            self._animated.set_food_overlay(food_id or DEFAULT_FOOD_ID)
        if action == "sleep":
            self._action_until = now
            self._animated.cancel_action(now)
        visual = {"feed": "eat", "pet": "petting"}.get(action)
        if action == "feed" and not result.food_consumed:
            visual = None
        reaction = result.reaction
        if visual is not None and not self.state.sleeping:
            if reaction is not None:
                reaction = replace(reaction, animation=visual)
            else:
                self._start_action(visual, 0.0)
        if reaction is None:
            self._cancel_followup()
            self._speech.show_text(result.fallback_text, 2450)
        else:
            self._react(reaction, 2900)
        if self._hover.toolbar is not None:
            self._hover.toolbar.refresh()
        self._hover.refresh_status()
        self._save()

    def set_topmost(self, value: bool) -> None:
        self._preferences.set_topmost(value)

    def set_auto_walk(self, value: bool) -> None:
        self._preferences.set_auto_walk(value)

    def set_auto_routine(self, enabled: bool) -> None:
        self._preferences.set_auto_routine(enabled)

    def set_follow_cursor(self, enabled: bool) -> None:
        self._preferences.set_follow_cursor(enabled)

    def set_spontaneous_talk(self, enabled: bool) -> None:
        self._preferences.set_spontaneous_talk(enabled)

    def set_learn_rhythm(self, enabled: bool) -> None:
        self._preferences.set_learn_rhythm(enabled)

    def forget_rhythm(self) -> None:
        self._preferences.forget_rhythm()

    def set_observe_computer(self, enabled: bool) -> None:
        self._preferences.set_observe_computer(enabled)

    def toggle_scale(self) -> None:
        self._preferences.toggle_scale()

    def reset_toolbar_position(self) -> None:
        self._preferences.reset_toolbar_position()

    def center(self) -> None:
        self._preferences.center()

    def _idle_emote(self) -> None:
        """Occasional unspoken state, never interrupting an existing scene."""
        if (
            self._speech.bubble is not None
            or self._reaction_player.pending_timer is not None
        ):
            return
        emote = choose_idle_emote(
            energy=self.state.energy,
            satiety=self.state.satiety,
            mood=self.state.mood,
            affection=self.state.affection,
        )
        self._speech.show_emote(emote, 1100)

    def _on_cursor_moved(
        self, distance: float, screen_width: int, now: float,
    ) -> None:
        event = self._attention.cursor_moved(
            distance, screen_width, now,
            toolbar_visible=self._hover.interaction_active,
        )
        if event is not None:
            self._react(self.mind.say_event(
                event, self.state, self.context, now,
            ))

    def _on_walk_finished(self, now: float) -> None:
        if self._attention.walk_finished(now):
            self._react(self.mind.say_event(
                "walk_pause", self.state, self.context, now,
            ))

    def _advance_pet_lifecycle(self, now: float, wall_time: float) -> None:
        progress = self._activity.advance_lifecycle(
            now, wall_time, self.context,
        )
        self.context = progress.context
        if progress.period_changed:
            if self._hover.toolbar is not None:
                self._hover.toolbar.refresh()
            if self.settings.spontaneous_talk and progress.sleep_changed:
                event = "sleep" if self.state.sleeping else "wake"
                self._react(self.mind.say_event(
                    event, self.state, self.context, now,
                ))

    def _refresh_taskbar_track(self, now: float) -> None:
        self._maintenance.refresh_track(now)

    def _maybe_show_idle_emote(self, now: float) -> None:
        """An independent policy decides whether Aiko is free for a gesture."""
        if self._hover.game_open:
            return
        animation = self._attention.idle_animation(
            now, action_until=self._action_until,
            walking=self._animated.movement.remaining_distance != 0,
            toolbar_visible=self._hover.interaction_active,
        )
        if animation is not None:
            self._start_action(animation, 1.6)
            self._idle_emote()

    def _maybe_speak_spontaneously(self, now: float) -> None:
        if self._hover.game_open:
            return
        decision = self._attention.spontaneous(
            now, self.context,
            toolbar_visible=self._hover.interaction_active,
            action_until=self._action_until,
            bubble_visible=self._speech.bubble is not None,
            popup_visible=self._hover.settings_engaged,
        )
        if decision.due:
            self._react(decision.reaction, 3600)

    def _present_pending_notification(self, now: float) -> None:
        """The Tk event loop alone turns queued data into rendered text."""
        if self._hover.game_open:
            return
        notification = self._attention.next_notification(
            now,
            action_until=self._action_until,
            bubble_visible=self._speech.bubble is not None,
            popup_visible=self._hover.settings_engaged,
            toolbar_visible=self._hover.interaction_active,
        )
        if notification is None:
            return
        self._speech.show_text(f"{notification.title}: {notification.message}", 3500)
        self._attention.mark_spoken(now)

    def _refresh_overlays_and_autosave(self, now: float) -> None:
        """Refresh visible panels, window layering and periodic persistence."""
        if self._hover.toolbar is not None and self._hover.toolbar.visible:
            self._hover.toolbar.refresh()
        self._hover.refresh_status()
        self._hover.refresh_settings()
        self._maintenance.refresh_stack(now)
        if self._persistence.due(now):
            self._save()

    def _tick(self) -> None:
        """Run the desktop scheduler, which owns update phase ordering."""
        self._runtime.tick()

    def _save(self) -> None:
        """Advance application state before writing it; report I/O failures."""
        self._activity.advance_state(time.time())
        failure = self._persistence.save()
        if failure is not None:
            messagebox.showwarning(
                "Aiko", f"Spielstand konnte nicht gespeichert werden:\n{failure}",
            )

    def quit(self) -> None:
        """Delegate ordered cleanup of all desktop session resources."""
        if self._closed:
            return
        self._closed = True
        self._farewell.cancel()
        self._lifecycle.stop()

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    load_env_file()
    app = DesktopPet()
    app.run()


if __name__ == "__main__":
    main()
