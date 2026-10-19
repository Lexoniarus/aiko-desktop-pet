"""Frameless Windows desktop companion using only Tkinter and prepared PNGs.

Aiko lives along the Windows taskbar, follows the cursor with 16 hand-authored
gaze sprites and exposes her care actions in a mouse-hover toolbar.
"""

from __future__ import annotations

import time
import tkinter as tk
from tkinter import font as tkfont
from tkinter import messagebox

from .application.active_time import ActiveSessionClock
from .application.activity import ActivityCallbacks
from .application.assembly import assemble_application
from .application.attention import AttentionCoordinator
from .application.commands import CareCommand
from .application.contact import ContactCoordinator, ContactPorts
from .application.game_experience import experience_from_rock_paper_scissors
from .application.session import PetSessionRestorer
from .application.settings import SettingKey
from .config import load_env_file
from .desktop.animation_assembly import AnimationAssemblyPorts, assemble_animation
from .desktop.attention_runtime import AttentionRuntimePorts, DesktopAttentionRuntime
from .desktop.farewell import FarewellSequence
from .desktop.global_input import (
    idle_seconds_windows,
    mouse_buttons_down_windows,
)
from .desktop.input import DesktopInput, DesktopInputActions
from .desktop.lifecycle import DesktopLifecycle
from .desktop.maintenance import DesktopMaintenance
from .desktop.persistence import DesktopPersistence
from .desktop.pointer_runtime import PointerRuntime, PointerRuntimePorts
from .desktop.preferences import DesktopPreferencePorts, DesktopPreferences
from .desktop.runtime import DesktopRuntime, DesktopTickPorts
from .desktop.session_runtime import DesktopSessionRuntime, SessionRuntimePorts
from .desktop.window_stack import WindowStack
from .desktop.world_access import WorldRuntimeAccess
from .desktop.world_runtime import DesktopWorldRuntime
from .infrastructure.active_time import elapsed_uptime_seconds
from .infrastructure.character_assets import load_character_catalog
from .infrastructure.character_mind import make_aiko_mind
from .infrastructure.hardware.monitor import ActivityMonitor
from .infrastructure.persistence import StateStore
from .pet.content import GERMAN_TEXT
from .pet.food import FoodId
from .pet.mind.catalog import Reaction
from .pet.routine import TimeContext, context_at
from .ui.pet_view.action_playback import ActionPlayback
from .ui.pet_view.attention_presenter import AttentionPresenter, AttentionViewPorts
from .ui.pet_view.care_presenter import CarePresenter, CareViewPorts
from .ui.pet_view.desktop_window import MAGENTA, DesktopWindow
from .ui.pet_view.object_feedback_presenter import ObjectFeedbackPresenter
from .ui.pet_view.reaction_player import ReactionPlayer
from .ui.pet_view.speech_presenter import SpeechAnchor, SpeechPresenter
from .ui.view_models.food_models import food_choices
from .ui.view_models.read_models import DesktopPresentation
from .ui.windows.game_speech import GameSpeech
from .ui.windows.hover_ui import HoverUi, HoverUiPorts


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
        active_clock = ActiveSessionClock(elapsed_uptime_seconds, wall_time=time.time)
        session = PetSessionRestorer(self.store, clock=active_clock).restore()
        self.state = session.state
        self.settings = session.settings
        self.adaptive = session.adaptive
        self.context: TimeContext = context_at(time.time())
        self._character_assets = load_character_catalog()
        self._window = DesktopWindow(self.settings)
        self.root = self._window.root
        self.canvas = self._window.canvas
        self.background = self._window.background
        self._world_access = WorldRuntimeAccess()
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
                advance_lifecycle=lambda now, wall: (
                    self._session_runtime.advance_lifecycle(now, wall)
                ),
                refresh_taskbar=lambda now: self._maintenance.refresh_track(now),
                poll_desktop_clicks=lambda: self._input.poll_global_click(),
                refresh_hover=lambda now: self._hover.refresh_hover(now),
                observe_computer=lambda now: self._activity.react_to_computer(
                    now, self.context,
                ),
                observe_pointer=lambda now: self._pointer_runtime.observe(now),
                render_character=lambda now, _elapsed, pointer: (
                    self._animated.render(
                        now, pointer,
                        attention=self.mind.cursor_attention.snapshot(),
                    )
                ),
                show_idle_emote=self._maybe_show_idle_emote,
                speak_spontaneously=self._maybe_speak_spontaneously,
                present_notification=self._present_pending_notification,
                refresh_overlays_and_save=lambda now: (
                    self._session_runtime.refresh(now)
                ),
                observe_objects=lambda now: self._world.update(now),
            ),
            schedule=self.root.after,
            cancel=self.root.after_cancel,
        )
        self._action_playback = ActionPlayback(
            self._character_assets,
            begin=lambda state, now: self._animated.begin_action(state, now),
            cancel=lambda now: self._animated.cancel_action(now),
        )
        self._persistence = DesktopPersistence(
            self.store, self.state, self.settings, self.adaptive,
        )
        self.mind = make_aiko_mind(started_at=self._persistence.last_saved)
        self.activity_monitor = activity_monitor or ActivityMonitor()
        self.activity_monitor.set_enabled(self.settings.observe_computer)
        services = assemble_application(
            state=self.state, settings=self.settings, mind=self.mind,
            adaptive=self.adaptive, monitor=self.activity_monitor,
            clock=active_clock,
            callbacks=ActivityCallbacks(
                speech_busy=lambda: self._reaction_player.pending_timer is not None,
                read_idle_seconds=idle_seconds_windows,
                start_review=lambda now: self._start_action(
                    "review", 1.4, started_at=now,
                ),
                react=self._react,
                action_until=lambda: self._action_playback.until,
                last_spoken=lambda: self._attention.last_spoken,
                read_pointer=lambda: (
                    self.root.winfo_pointerx(), self.root.winfo_pointery(),
                ),
                read_mouse_buttons=mouse_buttons_down_windows,
                defer_routine=self._world_access.defer_routine,
            ),
        )
        self._cursor_observation = services.cursor_observation
        self.application = services.router
        self.workload_events = services.workload_events
        self._activity = services.activity
        visuals = assemble_animation(
            root=self.root, canvas=self.canvas,
            state=self.state, settings=self.settings, adaptive=self.adaptive,
            monitor=self.activity_monitor, assets=self._character_assets,
            ports=AnimationAssemblyPorts(
                track=lambda: self._window.track,
                toolbar_visible=lambda: self._hover.interaction_active,
                place_x=self._place_x,
                walk_finished=self._on_walk_finished,
                gaze_origin=self._window.gaze_origin,
                game_mode=lambda: self._animated.game_mode,
                action_until=lambda: self._action_playback.until,
                action_clip_id=lambda: self._action_playback.clip_id,
                attention_until=lambda: self.mind.cursor_attention.attention_until,
                extend_action=self._action_playback.extend,
                object_focus=self._world_access.focused,
                object_phase=self._world_access.phase,
                following_subject=self._world_access.following_record,
                orientation_side=self._world_access.orientation_side,
                feedback_subject=lambda: self._reaction_player.subject,
                activity_active=lambda: (time.monotonic() < self._action_playback.until
                    or ((self._reaction_player.pending_timer is not None
                         or self._speech.bubble is not None)
                        and not self._world_access.contact_feedback_active())),
            ),
        )
        self._walk = visuals.walk
        self._visual = visuals.visual
        self._animation = visuals.animation
        self._animated = visuals.sprite
        self._item_catalog = visuals.items
        self._food_choices = food_choices(visuals.items)
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
            hide_speech=self._speech.hide,
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
            object_status=self._world_access.object_status,
        )
        self._hover = HoverUi(
            self.root, self.canvas,
            HoverUiPorts(
                hover_snapshot=self._views.hover,
                status_snapshot=self._views.status,
                settings_snapshot=self._views.settings_view,
                anchor=self._views.anchor,
                care=self.interact,
                can_interact=lambda action: self._contact.can_interact(action),
                food_choices=self._food_choices,
                feed=lambda selected: self._world.begin_carry(selected),
                defer_game=lambda action: self._world.interrupt(action),
                game_completed=lambda score: self.application.complete_game(
                    experience_from_rock_paper_scissors(score),
                    inputs=self._activity.session_inputs(time.time(), time.monotonic()),
                ),
                open_sprite_hover=self._on_enter,
                record_contact=lambda now: self._contact.record_contact(now),
                save_position=self._save_hover_position,
                set_option=self._apply_setting,
                toggle_scale=self.toggle_scale,
                forget_rhythm=self.forget_rhythm,
                reset_toolbar=self.reset_toolbar_position,
                center=self.center,
                quit=lambda: self._farewell.begin(),
                move_speech=self._speech.move,
                restore_stack=self._overlay_stack.restore,
                always_on_top=lambda: self.settings.always_on_top,
                game_dialogue=lambda event: self.mind.contact_text(
                    event, self.state, self.context, time.monotonic()),
                game_speech=GameSpeech(
                    self._reaction_player, self._speech,
                    self._mark_reaction_spoken,
                    self._set_game_mode,
                    lambda name: self._start_action(name, 0),
                ),
            ),
        )
        self._contact = ContactCoordinator(
            state=self.state, mind=self.mind, adaptive=self.adaptive,
            ports=ContactPorts(
                context=lambda: self.context,
                toolbar_hidden=lambda: (
                    self._hover.toolbar is None or not self._hover.toolbar.visible),
                mark_hover=self._hover.note_sprite_hover,
                interrupt_walk=lambda: self._world.interrupt(
                    self._walk.movement.interrupt),
                show_toolbar=lambda: self._hover.show_toolbar(),
                game_open=lambda: self._hover.game_open,
                cancel_followup=lambda: self._cancel_followup(),
                hide_speech=lambda: self._speech.hide(),
                react=lambda reaction, duration: self._react(reaction, duration),
                should_greet=lambda now: self._attention.should_greet(now),
                story_active=lambda: self._reaction_player.story_active,
                advance_story=self._reaction_player.advance_story,
                foreground_active=lambda: (self._object_feedback_active()
                    or self._world_access.defer_routine()),
                playback_active=lambda: (time.monotonic() < self._action_playback.until
                    or self._reaction_player.pending_timer is not None
                    or self._speech.bubble is not None),
                reaction_event=lambda: self._reaction_player.event,
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
        self._attention_view = AttentionPresenter(AttentionViewPorts(
            start_action=lambda name, duration: self._start_action(
                name, duration,
            ),
            react=lambda reaction, duration: self._react(reaction, duration),
            show_emote=lambda emote, duration: self._speech.show_emote(
                emote, duration,
            ),
            show_text=lambda text, duration: self._speech.show_text(
                text, duration,
            ),
        ))
        self._attention_runtime = DesktopAttentionRuntime(
            self._attention, self._attention_view,
            AttentionRuntimePorts(
                context=lambda: self.context,
                game_open=lambda: self._hover.game_open,
                toolbar_active=lambda: self._hover.interaction_active,
                settings_engaged=lambda: self._hover.settings_engaged,
                bubble_visible=lambda: self._speech.bubble is not None,
                reaction_pending=lambda: (
                    self._reaction_player.pending_timer is not None
                ),
                walking=lambda: (
                    self._walk.movement.remaining_distance != 0
                ),
                action_until=lambda: self._action_playback.until,
                refresh_toolbar=self._refresh_care_toolbar,
                foreground_active=self._object_feedback_active,
            ),
        )
        self._care_view = CarePresenter(CareViewPorts(
            set_item=lambda item: self._animated.set_food_overlay(item),
            cancel_action=self._action_playback.cancel_at,
            start_action=self._start_action,
            cancel_followup=self._cancel_followup,
            react=lambda reaction, duration: self._react(reaction, duration),
            show_text=lambda text, duration: self._speech.show_text(
                text, duration,
            ),
            refresh_toolbar=self._refresh_care_toolbar,
            refresh_status=lambda: self._hover.refresh_status(),
        ))
        self._pointer_runtime = PointerRuntime(
            self._cursor_observation, PointerRuntimePorts(
                sample=self._input.pointer_sample,
                game_mode=lambda: self._animated.game_mode,
                eyes=lambda: self._animated.cursor_eye_position,
                on_motion=self._on_cursor_moved,
            ),
        )
        self._session_runtime = DesktopSessionRuntime(
            activity=self._activity, attention=self._attention_runtime,
            maintenance=self._maintenance, persistence=self._persistence,
            ports=SessionRuntimePorts(
                context=lambda: self.context,
                set_context=self._set_context,
                toolbar_visible=lambda: (
                    self._hover.toolbar is not None and self._hover.toolbar.visible
                ),
                refresh_toolbar=self._refresh_care_toolbar,
                refresh_status=self._hover.refresh_status,
                refresh_settings=self._hover.refresh_settings,
                save=self._save,
            ),
        )
        self._preferences = DesktopPreferences(
            settings=self.settings,
            adaptive=self.adaptive,
            activity=self._activity,
            attention=self._attention,
            animated=self._animated, walk=self._walk,
            visual=self._visual, window=self._window,
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
            stop_animation=self._animated.close,
        )
        self._farewell = FarewellSequence(
            wording=lambda: self.mind.contact_text(
                "farewell", self.state, self.context, time.monotonic()),
            schedule=self.root.after, cancel=self.root.after_cancel,
            prepare=self._lifecycle.prepare_farewell,
            animate=lambda: self._start_action("waving-greeting", 0),
            say=self._speech.show_text, finish=self.quit,
            seconds=self._character_assets.clips["waving-greeting"].duration_seconds,
        )
        self._world = DesktopWorldRuntime(
            root=self.root, state=self.state, settings=self.settings,
            mind=self.mind, adaptive=self.adaptive, items=self._item_catalog,
            clock=active_clock, track=lambda: self._window.track,
            walk=self._walk, visual=self._visual, animated=self._animated,
            playback=self._action_playback, inputs=self._activity.session_inputs,
            game_open=lambda: self._hover.game_open,
            controls_active=lambda: (self._hover.interaction_active
                                     or self._reaction_player.story_active),
            present_feedback=ObjectFeedbackPresenter(
                self._reaction_player, self._item_catalog,
            ).show,
            cancel_feedback=self._reaction_player.cancel,
            feedback=lambda text: self._speech.show_text(text, 2450),
            save=self._save,
            restored_world=session.world,
            restored_memory=session.object_memory,
        )
        self._world_access.bind(self._world)
        self._persistence.attach_world(self._world.save_snapshot)
        self._lifecycle.start()

    def _object_feedback_active(self) -> bool:
        return hasattr(self, "_world") and (
            self._world.interaction.active or self._world.cursor.carrying
        )

    def _set_game_mode(self, enabled: bool) -> None:
        self._action_playback.cancel_at(time.monotonic())
        self._animated.set_game_mode(enabled)
        self.mind.cursor_attention.reset()

    def _overlay_windows(self) -> list[tk.Tk | tk.Toplevel]:
        """Back-to-front display order, independent of Tk's focus state."""
        windows: list[tk.Tk | tk.Toplevel] = [self.root]
        if hasattr(self, "_world"):
            windows.extend(self._world.view.windows)
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
        self._contact.enter()

    def _on_click_left(self, _event: tk.Event | None = None) -> None:
        if not self._world.cursor.carrying:
            self._world.request_contact(lambda: self._contact.click("left"))

    def _on_click_right(self, _event: tk.Event | None = None) -> None:
        self._world.request_contact(lambda: self._contact.click("right"))

    def _greet_on_start(self) -> None:
        self._contact.greet()

    def _mark_reaction_spoken(self) -> None:
        self._attention.mark_spoken(time.monotonic())

    def _cancel_followup(self) -> None:
        """Cancel an older reaction, including every pending follow-up."""
        self._reaction_player.cancel()

    def _react(self, reaction: Reaction | None, duration_ms: int = 2600) -> None:
        """Delegate the timeline; the GUI only renders visual effects."""
        if self._hover.game_open or self._object_feedback_active():
            return
        self._reaction_player.play(
            reaction, duration_ms, animate=not self.state.sleeping,
        )

    def _apply_setting(self, name: SettingKey, value: bool) -> None:
        """Apply a setting through the desktop preference owner."""
        self._preferences.set_option(name, value)

    def _start_action(
        self, state: str, duration: float, *, started_at: float | None = None,
    ) -> None:
        if self._object_feedback_active():
            return
        self._action_playback.start(
            state, duration, started_at=started_at,
        )

    def _refresh_care_toolbar(self) -> None:
        toolbar = self._hover.toolbar
        if toolbar is not None:
            toolbar.refresh()

    def interact(
        self, action: str, *, food_id: FoodId | None = None,
    ) -> None:
        """Run a care command through the shared application boundary."""
        if self._world.cursor.carrying:
            self._world.cursor.cancel()
        if (self._world.interaction.active
                or self._world.awareness.intentions.goal is not None):
            self._world.interrupt(lambda: self.interact(action, food_id=food_id))
            return
        stamp = time.time()
        now = time.monotonic()
        result = self.application.dispatch(
            CareCommand.from_action(action, food_id=food_id),
            inputs=self._activity.session_inputs(stamp, now),
        )
        self.context = result.context
        self._care_view.present(
            result, now=now, sleeping=self.state.sleeping,
        )
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

    def _on_cursor_moved(
        self, distance: float, screen_width: int, now: float,
    ) -> None:
        self._attention_runtime.cursor_moved(distance, screen_width, now)

    def _on_walk_finished(self, now: float) -> None:
        self._attention_runtime.walk_finished(now)

    def _maybe_show_idle_emote(self, now: float) -> None:
        self._attention_runtime.maybe_show_idle_emote(now)

    def _maybe_speak_spontaneously(self, now: float) -> None:
        self._attention_runtime.maybe_speak_spontaneously(now)

    def _present_pending_notification(self, now: float) -> None:
        self._attention_runtime.present_notification(now)

    def _tick(self) -> None:
        """Run the desktop scheduler, which owns update phase ordering."""
        self._runtime.tick()

    def _save(self) -> None:
        """Advance application state before writing it; report I/O failures."""
        failure = self._session_runtime.advance_and_save()
        if failure is not None:
            messagebox.showwarning(
                GERMAN_TEXT.format("ui.application_name"), GERMAN_TEXT.format(
                    "ui.save_failed", failure=str(failure),
                ),
            )

    def quit(self) -> None:
        """Delegate ordered cleanup of all desktop session resources."""
        if self._closed:
            return
        self._closed = True
        self._farewell.cancel()
        self._world.close()
        self._lifecycle.stop()

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    load_env_file()
    app = DesktopPet()
    app.run()


if __name__ == "__main__":
    main()
