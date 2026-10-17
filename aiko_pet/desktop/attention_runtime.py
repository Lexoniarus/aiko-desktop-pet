"""Run established attention policies against current desktop visibility.

No UI effect is chosen in the presenter: domain/application policy returns the
event, this desktop adapter coordinates the host snapshot and presentation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from ..application.activity import TimeProgress
from ..application.attention import AttentionCoordinator
from ..pet.animation.idle_emote import choose_idle_emote
from ..pet.routine import TimeContext
from ..ui.pet_view.attention_presenter import AttentionPresenter


@dataclass(frozen=True, slots=True)
class AttentionRuntimePorts:
    """Read the host's current interaction state without owning widgets."""

    context: Callable[[], TimeContext]
    game_open: Callable[[], bool]
    toolbar_active: Callable[[], bool]
    settings_engaged: Callable[[], bool]
    bubble_visible: Callable[[], bool]
    reaction_pending: Callable[[], bool]
    walking: Callable[[], bool]
    action_until: Callable[[], float]
    refresh_toolbar: Callable[[], None]
    foreground_active: Callable[[], bool] = lambda: False


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

    def handle_time_progress(self, progress: TimeProgress, now: float) -> None:
        """Present period transitions, leaving domain dialogue to attention."""
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

    def cursor_moved(
        self,
        distance: float,
        screen_width: int,
        now: float,
    ) -> None:
        if self._ports.foreground_active() or self._ports.reaction_pending():
            return
        reaction = self.attention.cursor_reaction(
            distance,
            screen_width,
            now,
            self._ports.context(),
            toolbar_visible=self._ports.toolbar_active(),
        )
        if reaction is not None:
            self._presenter.show_reaction(reaction, 2600)

    def walk_finished(self, now: float) -> None:
        if self._ports.reaction_pending():
            return
        reaction = self.attention.walk_reaction(now, self._ports.context())
        if reaction is not None:
            self._presenter.show_reaction(reaction, 2600)

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
        )
        self._presenter.show_idle_emote(emote)

    def maybe_show_idle_emote(self, now: float) -> None:
        ports = self._ports
        if ports.game_open() or ports.foreground_active() or ports.reaction_pending():
            return
        animation = self.attention.select_idle_animation(
            now,
            action_until=ports.action_until(),
            walking=ports.walking(),
            toolbar_visible=ports.toolbar_active(),
        )
        if animation is not None:
            self._presenter.show_animation(animation, 1.6)
            self.idle_emote()

    def maybe_speak_spontaneously(self, now: float) -> None:
        ports = self._ports
        if ports.game_open() or ports.foreground_active() or ports.reaction_pending():
            return
        choice = self.attention.spontaneous(
            now,
            ports.context(),
            toolbar_visible=ports.toolbar_active(),
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
            toolbar_visible=ports.toolbar_active(),
        )
        if note is None:
            return
        self._presenter.show_notification(
            f"{note.title}: {note.message}",
            3500,
        )
        self.attention.mark_spoken(now)
