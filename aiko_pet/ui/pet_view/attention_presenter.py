"""Render approved attention effects, without making behavioral decisions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from ...pet.mind.catalog import Reaction


@dataclass(frozen=True, slots=True)
class AttentionViewPorts:
    """Only the visual effects permitted to the attention presenter."""

    start_action: Callable[[str, float], None]
    react: Callable[[Reaction | None, int], None]
    show_emote: Callable[[str, int], None]
    show_text: Callable[[str, int], None]
    show_nonblocking_text: Callable[[str, int], bool] | None = None
    show_nonblocking_emote: Callable[[str, int], None] | None = None


class AttentionPresenter:
    """Execute presentation decisions with no PetMind or PetState reference."""

    def __init__(self, ports: AttentionViewPorts) -> None:
        self._ports = ports

    def show_reaction(
        self, reaction: Reaction | None, duration_ms: int,
    ) -> None:
        self._ports.react(reaction, duration_ms)

    def show_animation(self, animation: str, duration: float) -> None:
        self._ports.start_action(animation, duration)

    def show_idle_emote(self, emote: str, duration_ms: int = 1100) -> None:
        self._ports.show_emote(emote, duration_ms)

    def show_cursor_emote(self, emote: str, duration_ms: int) -> None:
        """A cue has no action/reaction ownership and never locks contact."""
        display = self._ports.show_nonblocking_emote or self._ports.show_emote
        display(emote, duration_ms)

    def show_cursor_warning(self, text: str, duration_ms: int) -> bool:
        display = self._ports.show_nonblocking_text
        return display(text, duration_ms) if display is not None else False

    def show_notification(self, text: str, duration_ms: int = 3500) -> None:
        self._ports.show_text(text, duration_ms)
