"""Policy for spontaneous dialogue, idle gestures and incoming notifications.

No Tkinter, desktop coordinates, or transport code. Only the GUI is allowed
to present the returned decisions; the inbox retains deferred notifications.
"""

from __future__ import annotations

import random
from dataclasses import dataclass


from ..pet.mind import PetMind
from ..pet.mind.workload_events import WorkloadEventDetector
from ..pet.mind.catalog import Reaction
from ..pet.state import PetState
from ..pet.routine import TimeContext
from .settings import PetSettings
from .ports import ComputerReadings
from .events import IncomingNotification
from .router import ApplicationRouter
from .care_requests import choose_care_request


@dataclass(frozen=True, slots=True)
class SpontaneousChoice:
    """Keep intentional dialogue silence distinct from no due dialogue slot."""

    due: bool
    reaction: Reaction | None = None


class AttentionCoordinator:
    """Own Aiko's attention clocks and non-interrupting notification rules."""

    def __init__(
        self, state: PetState, settings: PetSettings, mind: PetMind,
        voice: WorkloadEventDetector, monitor: ComputerReadings,
        router: ApplicationRouter, *, started_at: float,
    ) -> None:
        self.state = state
        self.settings = settings
        self.mind = mind
        self.workload_events = voice
        self.monitor = monitor
        self.router = router
        self.last_spoken = -1000.0
        self.next_care_request = started_at
        self.next_comment = started_at + random.uniform(180.0, 360.0)
        self.next_idle_emote = started_at + random.uniform(70.0, 170.0)
        self.next_cursor_line = started_at + random.uniform(200.0, 420.0)

    def mark_spoken(self, now: float) -> None:
        self.last_spoken = now

    def reschedule_comment(self, now: float) -> None:
        self.next_comment = now + random.uniform(180.0, 360.0)

    def set_spontaneous_talk(self, enabled: bool, now: float) -> None:
        self.settings.spontaneous_talk = bool(enabled)
        self.reschedule_comment(now)

    def should_greet(self, now: float) -> bool:
        return (
            self.settings.spontaneous_talk
            and now - self.last_spoken >= 15
        )

    def cursor_moved(
        self, distance: float, screen_width: int, now: float, *,
        toolbar_visible: bool,
    ) -> str | None:
        """Choose a rare cursor remark from an observed movement."""
        if (
            not self.settings.spontaneous_talk
            or not self.settings.follow_cursor
            or now < self.next_cursor_line
            or now - self.last_spoken <= 100
            or self.state.sleeping
            or toolbar_visible
        ):
            return None
        if random.random() >= 0.08:
            return None
        self.next_cursor_line = now + random.uniform(280.0, 590.0)
        return "cursor_far" if distance > screen_width * 0.6 else "cursor_follow"

    def walk_finished(self, now: float) -> bool:
        """Allow the character to comment occasionally after a completed walk."""
        return bool(
            self.settings.spontaneous_talk
            and now - self.last_spoken > 130
            and random.random() < 0.23
        )

    def cursor_reaction(
        self, distance: float, screen_width: int, now: float,
        context: TimeContext, *, toolbar_visible: bool,
    ) -> Reaction | None:
        """Interpret existing cursor event keys before entering the UI."""
        event = self.cursor_moved(
            distance, screen_width, now, toolbar_visible=toolbar_visible,
        )
        if event is None:
            return None
        return self.mind.say_event(event, self.state, context, now)

    def walk_reaction(
        self, now: float, context: TimeContext,
    ) -> Reaction | None:
        """Convert completed walks into an already selected dialogue event."""
        if not self.walk_finished(now):
            return None
        return self.mind.say_event("walk_pause", self.state, context, now)

    def idle_animation(
        self, now: float, *, action_until: float,
        walking: bool, toolbar_visible: bool,
    ) -> str | None:
        """Return one gesture only when Aiko is free to express herself."""
        if now < self.next_idle_emote:
            return None
        self.next_idle_emote = now + random.uniform(85.0, 190.0)
        if (
            self.state.sleeping or now < action_until
            or walking or toolbar_visible
        ):
            return None
        return random.choice(("waiting", "review", "idle"))

    def spontaneous(
        self, now: float, context: TimeContext, *,
        toolbar_visible: bool,
        action_until: float = 0.0, bubble_visible: bool = False,
        popup_visible: bool = False,
    ) -> SpontaneousChoice:
        """Select measured-effort or personal dialogue when allowed."""
        if (
            not self.settings.spontaneous_talk
            or self.state.sleeping
            or toolbar_visible
            or bubble_visible or popup_visible or now < action_until
            or now - self.last_spoken < 85
        ):
            return SpontaneousChoice(False)
        request = choose_care_request(self.state)
        if (
            request is not None and now >= self.next_care_request
            and not self.mind.recently_cared_for(now)
        ):
            reaction = self.mind.say_event(request, self.state, context, now)
            if reaction is not None:
                self.next_care_request = now + 30 * 60
                return SpontaneousChoice(True, reaction)
        if now < self.next_comment:
            return SpontaneousChoice(False)
        self.next_comment = now + random.uniform(175.0, 360.0)
        event = self.workload_events.maybe_event(self.monitor.latest(), now)
        reaction = (
            self.mind.computer_event(event, self.state, context, now)
            if event is not None
            else self.mind.spontaneous_event(self.state, context, now)
        )
        return SpontaneousChoice(True, reaction)

    def next_notification(
        self, now: float, *, action_until: float,
        bubble_visible: bool, popup_visible: bool,
        toolbar_visible: bool,
    ) -> IncomingNotification | None:
        """Consume at most one event without interrupting any visible UI."""
        if (
            self.state.sleeping
            or now < action_until
            or now - self.last_spoken < 3
            or bubble_visible or popup_visible or toolbar_visible
        ):
            return None
        return self.router.next_notification()
