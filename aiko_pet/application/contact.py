"""Coordinate intentional pet hover, click, and greeting interactions.

The mind decides which response fits the contact. Application coordination
uses only effect ports and never imports Tk widgets or speech presenters.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, replace
from typing import Callable

from ..pet.mind import PetMind
from ..pet.mind.adaptive import AdaptiveRoutine
from ..pet.mind.catalog import Reaction
from ..pet.routine import TimeContext
from ..pet.state import PetState


@dataclass(frozen=True, slots=True)
class ContactPorts:
    """The desktop effects an intentional contact is allowed to request."""

    context: Callable[[], TimeContext]
    toolbar_hidden: Callable[[], bool]
    mark_hover: Callable[[float], None]
    interrupt_walk: Callable[[], None]
    show_toolbar: Callable[[], None]
    game_open: Callable[[], bool]
    cancel_followup: Callable[[], None]
    hide_speech: Callable[[], None]
    react: Callable[[Reaction | None, int], None]
    should_greet: Callable[[float], bool]


class ContactCoordinator:
    """Keep direct user contact higher priority than autonomous pet actions."""

    def __init__(
        self, *, state: PetState, mind: PetMind,
        adaptive: AdaptiveRoutine, ports: ContactPorts,
    ) -> None:
        self._state = state
        self._mind = mind
        self._adaptive = adaptive
        self._ports = ports

    def record_contact(self, now: float) -> None:
        self._mind.last_contact = now

    def enter(self) -> None:
        """Preserve toolbar and walk-interruption order on pointer entry."""
        now = time.monotonic()
        reaction = (
            self._mind.return_to_pet(
                self._state, self._ports.context(), now,
            )
            if self._ports.toolbar_hidden() else None
        )
        self._ports.mark_hover(now)
        self._ports.interrupt_walk()
        self._ports.show_toolbar()
        self._ports.react(reaction, 2800)

    def click(self, button: str) -> None:
        """Deliver an intentional click only after initiating hover."""
        self.enter()
        now = time.monotonic()
        self._adaptive.note_interaction(time.time())
        # PetMind validates the available button types itself.
        if button not in ("left", "right"):
            raise ValueError("Unknown click button")
        self.react_to_click(self._mind.click(
            button, self._state, self._ports.context(), now,
        ))

    def react_to_click(self, reaction: Reaction | None) -> None:
        if self._ports.game_open():
            return
        if reaction is None:
            self._ports.cancel_followup()
            self._ports.hide_speech()
            return
        if len(self._mind.clicks) >= 3 and reaction.emote_before is not None:
            reaction = replace(reaction, emote_before=None)
        self._ports.react(reaction, 2800)

    def greet(self) -> None:
        now = time.monotonic()
        if not self._ports.should_greet(now):
            return
        self._ports.react(
            self._mind.say_event(
                "greeting", self._state, self._ports.context(), now,
            ), 3300,
        )
