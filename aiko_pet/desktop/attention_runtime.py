"""Run established attention policies against current desktop visibility.

No UI effect is chosen in the presenter: domain/application policy returns the
event, this desktop adapter coordinates the host snapshot and presentation.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Literal

from ..application.activity import TimeProgress
from ..application.attention import AttentionCoordinator
from ..pet.animation.idle_behaviour import IdleBehaviourProfile
from ..pet.animation.idle_emote import choose_idle_emote
from ..pet.animation.idle_gesture import IdleGestureChoice
from ..pet.interaction_events import (
    CursorExperience,
    CursorWarning,
    CursorWarningReceipt,
)
from ..pet.mind.cursor_behaviour import parameter
from ..pet.routine import TimeContext
from ..ui.pet_view.attention_presenter import AttentionPresenter


@dataclass(frozen=True, slots=True)
class AttentionRuntimePorts:
    """Read the host's current interaction state without owning widgets."""

    context: Callable[[], TimeContext]
    game_open: Callable[[], bool]
    menu_engaged: Callable[[], bool]
    settings_engaged: Callable[[], bool]
    bubble_visible: Callable[[], bool]
    reaction_pending: Callable[[], bool]
    walking: Callable[[], bool]
    action_until: Callable[[], float]
    refresh_toolbar: Callable[[], None]
    foreground_active: Callable[[], bool] = lambda: False
    clock: Callable[[], float] = lambda: time.monotonic()
    apply_idle_profile: Callable[[IdleBehaviourProfile], None] = lambda _profile: None
    render_character: Callable[[float, tuple[int, int]], None] = lambda _now, _p: None
    prepare_idle_gesture: Callable[
        [bool, float], Literal["blocked", "turning", "ready"]
    ] = lambda _requested, _now: "blocked"
    idle_gesture_duration: Callable[[str], float] = lambda _clip: 0.0


class DesktopAttentionRuntime:
    """Coordinate application choices without storing a second pet state."""

    def __init__(
        self,
        attention: AttentionCoordinator,
        presenter: AttentionPresenter,
        ports: AttentionRuntimePorts,
    ) -> None:
        self.attention = attention
        self._presenter = presenter
        self._ports = ports
        self._idle_gesture: IdleGestureChoice | None = None

    def handle_time_progress(self, progress: TimeProgress, now: float) -> None:
        """Present period transitions, leaving domain dialogue to attention."""
        self.attention.evaluate_wishes()
        if not progress.period_changed:
            return
        self._ports.refresh_toolbar()
        if not progress.sleep_changed:
            return
        reaction = self.attention.select_sleep_transition_reaction(
            now,
            progress.context,
        )
        if reaction is not None:
            self._presenter.show_reaction(reaction, 2600)

    def render_character(self, now: float, pointer: tuple[int, int]) -> None:
        """Prepare once after lifecycle/attention admission in the main tick."""
        self._ports.apply_idle_profile(self.attention.idle_profile())
        self._ports.render_character(now, pointer)

    def cursor_warning(self, event: CursorWarning, now: float) -> CursorWarningReceipt:
        ports = self._ports
        displayed = False
        if (0 <= now - event.created_at <= parameter("warning_candidate_seconds")
                and not any((ports.game_open(), ports.foreground_active(),
                             ports.reaction_pending(), ports.bubble_visible(),
                             ports.menu_engaged(), ports.settings_engaged()))):
            reaction = self.attention.mind.select_reaction(
                ("cursor_notice_playful" if event.tone == "playful"
                 else "cursor_warning_near_fast"),
                self.attention.state, ports.context(), now,
            )
            if reaction is not None:
                displayed = self._presenter.show_cursor_warning(
                    reaction.text, int(parameter("warning_duration_ms")),
                )
        return CursorWarningReceipt(
            event.warning_id, ports.clock() if displayed else now, displayed,
        )

    def cursor_experience(self, event: CursorExperience) -> None:
        """Brief feeling cue in a free speech slot; drop rather than queue."""
        ports = self._ports
        if (ports.game_open() or ports.foreground_active() or ports.reaction_pending()
                or ports.bubble_visible() or ports.menu_engaged()
                or ports.settings_engaged()):
            return
        emote = ("idea" if event.level >= 2 else "question"
                 ) if event.feeling == "curiosity" else (
                     "drops" if event.level >= 2 else "exclamation")
        event_name = ("cursor_play_start", "cursor_play_more", "cursor_play_peak")[
            event.level - 1
        ] if event.feeling == "curiosity" else "cursor_fear_response"
        reaction = self.attention.mind.select_reaction(
            event_name, self.attention.state, ports.context(), ports.clock(),
        )
        if reaction is not None:
            self._presenter.show_cursor_comment(reaction.text, 3000)
        else:
            self._presenter.show_cursor_emote(emote, 1500)

    def idle_emote(self) -> None:
        ports = self._ports
        if ports.bubble_visible() or ports.reaction_pending():
            return
        state = self.attention.state
        emote = choose_idle_emote(
            energy=state.energy,
            satiety=state.satiety,
            mood=state.mood,
            affection=state.affection,
            emotions=self.attention.mind.emotional_state(state),
        )
        self._presenter.show_idle_emote(emote)

    def maybe_show_idle_emote(self, now: float) -> None:
        ports = self._ports
        if any((ports.game_open(), ports.foreground_active(), ports.reaction_pending(),
                ports.menu_engaged(), ports.settings_engaged(), ports.bubble_visible(),
                ports.walking(), now < ports.action_until())):
            self._idle_gesture = None
            ports.prepare_idle_gesture(False, now)
            return
        if self._idle_gesture is not None:
            if (self._idle_gesture != self.attention.idle_gesture_choice()
                    or now >= self.attention.next_idle_emote):
                self._idle_gesture = None
                ports.prepare_idle_gesture(False, now)
                return
        else:
            self._idle_gesture = self.attention.select_idle_animation(
                now, action_until=ports.action_until(), walking=False,
                toolbar_visible=False,
            )
        if self._idle_gesture is None:
            ports.prepare_idle_gesture(False, now)
            return
        status = ports.prepare_idle_gesture(True, now)
        if status == "turning":
            return
        choice, self._idle_gesture = self._idle_gesture, None
        ports.prepare_idle_gesture(False, now)
        if status == "ready":
            duration = ports.idle_gesture_duration(choice.clip_id)
            if duration > 0:
                self._presenter.show_animation(choice.clip_id, duration)
                self.idle_emote()

    def maybe_speak_spontaneously(self, now: float) -> None:
        ports = self._ports
        if ports.game_open() or ports.foreground_active() or ports.reaction_pending():
            return
        choice = self.attention.spontaneous(
            now,
            ports.context(),
            toolbar_visible=ports.menu_engaged(),
            action_until=ports.action_until(),
            bubble_visible=ports.bubble_visible(),
            popup_visible=ports.settings_engaged(),
        )
        if choice.due:
            self._presenter.show_reaction(choice.reaction, 3600)

    def present_notification(self, now: float) -> None:
        ports = self._ports
        if ports.game_open() or ports.foreground_active() or ports.reaction_pending():
            return
        note = self.attention.next_notification(
            now,
            action_until=ports.action_until(),
            bubble_visible=ports.bubble_visible(),
            popup_visible=ports.settings_engaged(),
            toolbar_visible=ports.menu_engaged(),
        )
        if note is None:
            return
        self._presenter.show_notification(
            f"{note.title}: {note.message}",
            3500,
        )
        self.attention.mark_spoken(now)
