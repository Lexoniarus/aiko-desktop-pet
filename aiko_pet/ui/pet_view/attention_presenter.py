"""Display approved attention decisions without owning pet or UI state.

AttentionCoordinator owns timing and selection. This adapter translates its
results into animation/speech effects through explicitly granted host ports.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from ...application.attention import AttentionCoordinator
from ...pet.animation.idle_emote import choose_idle_emote
from ...pet.mind.catalog import Reaction
from ...pet.routine import TimeContext


@dataclass(frozen=True, slots=True)
class AttentionViewPorts:
    """Read-only UI conditions and narrowly scoped visual effects."""

    context: Callable[[], TimeContext]
    game_open: Callable[[], bool]
    toolbar_active: Callable[[], bool]
    settings_engaged: Callable[[], bool]
    bubble_visible: Callable[[], bool]
    reaction_pending: Callable[[], bool]
    walking: Callable[[], bool]
    action_until: Callable[[], float]
    start_action: Callable[[str, float], None]
    react: Callable[[Reaction | None, int], None]
    show_emote: Callable[[str, int], None]
    show_text: Callable[[str, int], None]


class AttentionPresenter:
    """Render an attention decision, leaving selection with the application."""

    def __init__(
        self, attention: AttentionCoordinator, *, ports: AttentionViewPorts,
    ) -> None:
        self._attention = attention
        self._ports = ports

    def idle_emote(self) -> None:
        """Display one need-based icon only if no conversation is active."""
        ports = self._ports
        if ports.bubble_visible() or ports.reaction_pending():
            return
        state = self._attention.state
        emote = choose_idle_emote(
            energy=state.energy,
            satiety=state.satiety,
            mood=state.mood,
            affection=state.affection,
        )
        ports.show_emote(emote, 1100)

    def cursor_moved(
        self, distance: float, screen_width: int, now: float,
    ) -> None:
        event = self._attention.cursor_moved(
            distance, screen_width, now,
            toolbar_visible=self._ports.toolbar_active(),
        )
        if event is not None:
            self._ports.react(
                self._attention.mind.say_event(
                    event, self._attention.state, self._ports.context(), now,
                ), 2600,
            )

    def walk_finished(self, now: float) -> None:
        if self._attention.walk_finished(now):
            self._ports.react(
                self._attention.mind.say_event(
                    "walk_pause", self._attention.state,
                    self._ports.context(), now,
                ), 2600,
            )

    def maybe_show_idle_emote(self, now: float) -> None:
        ports = self._ports
        if ports.game_open():
            return
        animation = self._attention.idle_animation(
            now, action_until=ports.action_until(),
            walking=ports.walking(),
            toolbar_visible=ports.toolbar_active(),
        )
        if animation is not None:
            ports.start_action(animation, 1.6)
            self.idle_emote()

    def maybe_speak_spontaneously(self, now: float) -> None:
        ports = self._ports
        if ports.game_open():
            return
        choice = self._attention.spontaneous(
            now, ports.context(),
            toolbar_visible=ports.toolbar_active(),
            action_until=ports.action_until(),
            bubble_visible=ports.bubble_visible(),
            popup_visible=ports.settings_engaged(),
        )
        if choice.due:
            ports.react(choice.reaction, 3600)

    def present_notification(self, now: float) -> None:
        ports = self._ports
        if ports.game_open():
            return
        note = self._attention.next_notification(
            now,
            action_until=ports.action_until(),
            bubble_visible=ports.bubble_visible(),
            popup_visible=ports.settings_engaged(),
            toolbar_visible=ports.toolbar_active(),
        )
        if note is None:
            return
        ports.show_text(f"{note.title}: {note.message}", 3500)
        self._attention.mark_spoken(now)
