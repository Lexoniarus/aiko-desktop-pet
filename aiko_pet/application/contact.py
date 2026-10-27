"""Coordinate intentional pet hover, click, and greeting interactions.

The mind decides which response fits the contact. Application coordination
uses only effect ports and never imports Tk widgets or speech presenters.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, replace
from typing import Callable

from ..pet.balance import BALANCE
from ..pet.interaction_events import BoundaryCommunicated, Poked
from ..pet.mind import PetMind
from ..pet.mind.adaptive import AdaptiveRoutine
from ..pet.mind.catalog import Reaction
from ..pet.mind.click_policy import POKING_BOUNDARY_EVENTS, ClickButton
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
    story_active: Callable[[], bool] = lambda: False
    advance_story: Callable[[], bool] = lambda: False
    foreground_active: Callable[[], bool] = lambda: False
    playback_active: Callable[[], bool] = lambda: False
    interruptible_playback: Callable[[], bool] = lambda: False
    reaction_event: Callable[[], str | None] = lambda: None
    care_holding: Callable[[], bool] = lambda: False
    advance_time: Callable[[], None] = lambda: None
    wake_from_clicks: Callable[[], None] = lambda: None
    cursor_watching: Callable[[], bool] = lambda: False


class ContactCoordinator:
    """Coordinate contact after foreground ownership has granted it."""

    def __init__(
        self,
        *,
        state: PetState,
        mind: PetMind,
        adaptive: AdaptiveRoutine,
        ports: ContactPorts,
    ) -> None:
        self._state = state
        self._mind = mind
        self._adaptive = adaptive
        self._ports = ports

    def can_interact(self, action: str) -> bool:
        """Derive user-action permission from current owners, never UI hover."""
        if self._ports.foreground_active() or self._ports.game_open():
            return False
        if self._state.sleeping:
            return action == "sleep"  # Waking ends the current lifecycle action.
        return not self._ports.story_active() and (
            self._ports.care_holding() or not self._ports.playback_active()
            or self._ports.interruptible_playback()
        )

    def note_text(self, event: str) -> None:
        acknowledge_interaction_text(self._state, event)

    def record_contact(self, now: float) -> None:
        self._mind.last_contact = now

    def enter(self, *, preserve_cursor: bool = True) -> None:
        """Open controls immediately; an observed flyover is not a new action."""
        now = time.monotonic()
        if (preserve_cursor and self._ports.cursor_watching()
                or self._ports.care_holding() or not self.can_interact("pet")):
            self._ports.mark_hover(now)
            self._ports.show_toolbar()
            return
        reaction = (
            self._mind.return_to_pet(
                self._state,
                self._ports.context(),
                now,
            )
            if self._ports.toolbar_hidden() and not self._ports.story_active()
            else None
        )
        if self._state.moodlets.interactions.food.request_pending:
            reaction = self._mind.select_reaction(
                "feed_variety_request", self._state, self._ports.context(), now,
            )
        self._ports.mark_hover(now)
        self._ports.interrupt_walk()
        self._ports.show_toolbar()
        if not self._ports.story_active():
            self._ports.react(
                reaction, BALANCE.integer("dialogue", "contact_reaction_ms")
            )

    def click(self, button: ClickButton) -> None:
        """Deliver an intentional click only after initiating hover."""
        if button not in ("left", "right"):
            raise ValueError("Unknown click button")
        if button == "left" and self._ports.advance_story():
            self._mind.clicks.clear()
            self._mind.last_contact = time.monotonic()
            return
        if self._ports.game_open():
            return
        if self._ports.story_active():
            return
        # A click reply can be interrupted by the next click in the same burst.
        # Real care/game playback stays exclusive; World admits object contact
        # upstream through its existing request_contact/acknowledge_contact path.
        event = self._ports.reaction_event()
        click_reply = event is not None and (
            event.startswith("click_") or event in ("rapid_click", "sleep_click")
        )
        sleep_reply = self._state.sleeping and event == "sleep"
        if self._ports.playback_active() and not (
            click_reply or sleep_reply or self._ports.interruptible_playback()
        ):
            return
        self._ports.advance_time()
        self.enter(preserve_cursor=False)
        now = time.monotonic()
        self._adaptive.note_interaction(time.time())
        reaction = self._mind.click(
            button, self._state, self._ports.context(), now,
        )
        if self._state.sleeping and self._mind.click_wakes:
            self._ports.wake_from_clicks()
            return
        if not self._state.sleeping:
            self._state.experience_interaction(Poked(len(self._mind.clicks) > 1))
        if self._mind.click_annoyance:
            self._state.apply_relationship_penalty(
                "click", BALANCE.number("friendship", "click_loss"),
            )
        self.react_to_click(reaction)

    def react_to_click(self, reaction: Reaction | None) -> None:
        if self._ports.game_open():
            return
        if reaction is None:
            self._ports.cancel_followup()
            self._ports.hide_speech()
            return
        if (
            len(self._mind.clicks)
            >= BALANCE.integer("dialogue", "hide_click_emote_from_count")
            and reaction.beats[0].kind == "emote"
        ):
            reaction = replace(reaction, beats=reaction.beats[1:])
        self._ports.react(reaction, BALANCE.integer("dialogue", "contact_reaction_ms"))

    def greet(self) -> None:
        now = time.monotonic()
        if not self._ports.should_greet(now):
            return
        self._ports.react(
            self._mind.select_reaction(
                "greeting",
                self._state,
                self._ports.context(),
                now,
            ),
            BALANCE.integer("dialogue", "greeting_reaction_ms"),
        )


def acknowledge_interaction_text(state: PetState, event: str) -> None:
    """Translate actually presented feedback into language-neutral boundary facts."""
    if event in POKING_BOUNDARY_EVENTS:
        state.experience_interaction(BoundaryCommunicated("poking"))
    elif event == "feed_variety_request":
        state.experience_interaction(BoundaryCommunicated("food_variety"))
    elif event == "pet_refused":
        state.experience_interaction(BoundaryCommunicated("petting"))
