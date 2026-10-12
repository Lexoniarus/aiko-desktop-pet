"""Situational dialogue decisions for Aiko's offline desktop personality.

The authored dialogue catalogue and its validation live in dialogue_catalog.
Legacy module exports remain available to callers importing aiko_pet.dialogue.
"""

from __future__ import annotations

import random
from collections import deque

from .adaptive import Behaviour
from .dialogue_catalog import (
    ANIMATIONS as ANIMATIONS,
    CATALOGUE as CATALOGUE,
    DialogueBook as DialogueBook,
    EMOTIONS as EMOTIONS,
    EMOTION_LABELS as EMOTION_LABELS,
    Line as Line,
    PERIODS as PERIODS,
    Reaction as Reaction,
)
from .domain import PetState
from .routine import TimeContext
from .computer_voice import ComputerVoice as ComputerVoice

class AikoMind:
    """Situational reactions with a short, decaying social memory.

    Aiko is the personification of this computer, not a technical narrator.
    Load is *her* effort; the same click can mean something different after
    work, in a quiet evening, or during an interrupted calculation.
    """

    RETURN_AFTER_SECONDS = 25 * 60
    CLICK_WINDOW_SECONDS = 7.5
    MAX_CLICKS_IN_BURST = 20

    def __init__(
        self, book: DialogueBook | None = None, *,
        rng: random.Random | None = None, started_at: float = 0.0,
    ) -> None:
        self.rng = rng or random.Random()
        self.book = book or DialogueBook.from_file(rng=self.rng)
        self.clicks: deque[float] = deque(maxlen=self.MAX_CLICKS_IN_BURST)
        self.irritated_until = -1.0
        self.warm_until = -1.0
        self.last_contact = started_at
        self.situation: Behaviour | None = None
        self._work_interruptions = 0
        self._last_work_duration = 0.0
        self._recovery_until = -1.0
        self._last_recovery_comment = -1.0
        self._last_work_finished_at = -1.0
        self._postwork_thought_spoken = False
        self._last_care_action = ""
        self._last_care_at = -1.0
        self._last_social_comment = float("-inf")
        self._last_affection_comment = float("-inf")

    def set_situation(self, situation: Behaviour | None, *, now: float | None = None) -> None:
        """Remember an observed work session, never infer unseen work."""
        previous = self.situation
        self.situation = situation
        if situation is None:
            self._work_interruptions = 0
            self._recovery_until = -1.0
        elif previous is not None and previous.focused and not situation.focused:
            self._last_work_duration = previous.prolonged_work_seconds
            if now is not None:
                self._recovery_until = now + 110.0
                self._last_work_finished_at = now
                self._postwork_thought_spoken = False
        elif previous is not None and not previous.focused and situation.focused:
            # New work, new episode. Old clicks cannot count as interruptions.
            self._work_interruptions = 0
            self._recovery_until = -1.0
            self._postwork_thought_spoken = False

    def emotion(self, state: PetState, now: float) -> str:
        if state.sleeping:
            return "asleep"
        if now < self.irritated_until:
            return "irritated"
        if self.situation is not None and self.situation.strain >= 75 and state.energy <= 55:
            return "tired"
        if self.situation is not None and self.situation.strain >= 60 and state.mood <= 48:
            return "withdrawn"
        if state.energy <= 25:
            return "tired"
        if state.satiety <= 25:
            return "hungry"
        if state.mood <= 28:
            return "withdrawn"
        if state.social <= 23:
            return "lonely"
        if state.affection <= 23:
            return "seeking_affection"
        if now < self.warm_until:
            return "warm"
        if state.mood >= 82 and state.energy >= 45:
            return "playful"
        return "calm"

    def say_event(
        self, event: str, state: PetState, context: TimeContext, now: float,
        *, tone: str | None = None,
    ) -> Reaction | None:
        return self.book.choose(event, tone or self.emotion(state, now), context, now)

    def click(
        self, button: str, state: PetState, context: TimeContext, now: float,
    ) -> Reaction | None:
        if button not in ("left", "right"):
            raise ValueError("Unknown mouse button")
        self.last_contact = now
        if self.clicks and now - self.clicks[-1] > self.CLICK_WINDOW_SECONDS:
            self.clicks.clear()
        self.clicks.append(now)
        count = len(self.clicks)
        if state.sleeping:
            return self.say_event("sleep_click", state, context, now)

        busy = self.situation is not None and self.situation.focused
        cheerful = state.mood >= 82 and state.energy >= 45 and not busy
        withdrawn = state.mood <= 28 and not busy
        tired = state.energy <= 26 or (
            self.situation is not None and self.situation.strain >= 72
        )
        if busy:
            self._work_interruptions += 1
            if count <= 2:
                event = "click_during_work"
            elif count <= 4:
                event = "click_work_repeat"
            elif count <= 6:
                event = "click_work_boundary"
            elif count == 7:
                event = "click_last_word"
            else:
                return None  # Not every provocation deserves a speech bubble.
        elif count == 1 and now < self._recovery_until:
            event = "click_after_work"
        elif count <= 2:
            if withdrawn:
                event = "click_withdrawn"
            elif tired:
                event = "click_sleepy"
            elif self._last_care_action == "pet" and now - self._last_care_at < 50:
                event = "click_flustered"
            elif state.social <= 23:
                event = "click_lonely"
            elif state.affection <= 23:
                event = "click_affection_low"
            elif context.night and not cheerful:
                event = "click_night"
            elif (state.friendship >= 72 and state.mood >= 60
                  and state.affection >= 40):
                event = "click_close"
            elif (state.affection >= 85 and state.friendship >= 40
                  and state.mood >= 60):
                event = "click_at_ease"
            elif state.friendship < 12:
                event = "click_reserved"
            else:
                event = "click_left" if button == "left" else "click_right"
        elif count == 3:
            event = ("click_notice_playful" if cheerful else
                     "click_notice_withdrawn" if withdrawn else "click_notice")
        elif count <= 5:
            event = ("click_tease" if cheerful else
                     "click_withdrawn_boundary" if withdrawn else
                     "click_weary" if tired else "rapid_click")
        elif withdrawn and count >= 7:
            return None
        elif withdrawn and count == 6:
            event = "click_last_word"
        elif count <= 7:
            event = "click_tease_more" if cheerful else "click_boundary"
        elif count == 8:
            event = "click_last_word"
        else:
            return None
        if count >= 4 and not cheerful:
            self.irritated_until = max(self.irritated_until, now + 13.0)
        return self.say_event(event, state, context, now)

    def care_event(
        self, action: str, state: PetState, context: TimeContext, now: float,
    ) -> tuple[str, str]:
        """Return an event and the PRE-action tone of the care interaction."""
        self.last_contact = now
        tone = self.emotion(state, now)
        if action == "feed":
            if state.satiety >= 95:
                return "feed_full", tone
            if context.meal and (
                context.day_key != state.meals_date or context.meal not in state.meals_today
            ):
                return "feed_meal", tone
            return "feed_snack", tone
        if action == "play":
            if state.energy < 8:
                return "play_tired", tone
            return ("play_close" if state.friendship >= 72 else "play"), tone
        if action == "talk":
            if self.situation is not None and self.situation.focused:
                return "talk_busy", tone
            if state.social <= 27:
                return "talk_lonely", tone
            return ("talk_close" if state.friendship >= 72 else "talk"), tone
        if action == "energy_drink":
            return ("energy_drink_full" if state.energy >= 100
                    else "energy_drink"), tone
        if action == "sleep":
            return ("wake" if state.sleeping else "sleep"), tone
        if action == "pet":
            if self.situation is not None and self.situation.focused:
                return "pet_during_work", tone
            if state.affection <= 24:
                return "pet_needs_affection", tone
            return ("pet_close" if state.friendship >= 72 else "pet"), tone
        raise ValueError(f"Unknown care event: {action}")

    def after_care(self, action: str, now: float) -> None:
        self._last_care_action = action
        self._last_care_at = now
        if action in ("pet", "feed", "play", "talk"):
            self.warm_until = now + (70 if action == "pet" else 45)
        if action == "sleep":
            self.irritated_until = -1.0
            self.clicks.clear()

    def computer_event(
        self, event: str, state: PetState, context: TimeContext, now: float,
    ) -> Reaction | None:
        """Interpret meaningful work transitions in the lived context."""
        situation = self.situation
        if event in ("computer_effort_rising", "computer_effort_heavy",
                     "computer_effort_peak") and situation is not None:
            if (situation.expectation_confident
                    and situation.expected_effort is not None
                    and situation.expected_effort < 0.3
                    and (situation.effort or 0.0) >= 0.5):
                event = "work_unexpected"
        if event.startswith("computer_effort_recovered"):
            if self._work_interruptions >= 2 and self._last_work_duration >= 18:
                event = "work_finished_interrupted"
            elif self._last_work_duration >= 20 * 60:
                event = "work_finished_long"
            self._recovery_until = now + 110.0
            self._last_recovery_comment = now
            self._last_work_finished_at = now
            self._postwork_thought_spoken = False
            self._work_interruptions = 0
        if event == "computer_uptime":
            event = "computer_uptime_grounded"
        return self.say_event(event, state, context, now)

    def return_to_pet(
        self, state: PetState, context: TimeContext, now: float,
    ) -> Reaction | None:
        elapsed = now - self.last_contact
        self.last_contact = now
        if state.sleeping or elapsed < self.RETURN_AFTER_SECONDS:
            return None
        if self.situation is not None and self.situation.focused:
            event = "return_working"
        elif now < self._recovery_until:
            event = "return_after_work"
        else:
            event = "return_close" if state.friendship >= 72 else "return"
        return self.say_event(event, state, context, now)

    def spontaneous_event(
        self, state: PetState, context: TimeContext, now: float,
    ) -> Reaction | None:
        """Choose an observed situation; no imagined apps or off-screen story."""
        if state.sleeping:
            return None
        tone = self.emotion(state, now)
        situation = self.situation
        if tone == "hungry":
            event = "hungry"
        elif tone == "lonely" and not (situation and situation.focused):
            # Missing company matters, but a permanently running PC must not
            # nag the user every five minutes for social attention.
            if now - self._last_social_comment >= 20 * 60:
                event = "social_low"
                self._last_social_comment = now
            else:
                event = "idle"
        elif tone == "seeking_affection" and not (situation and situation.focused):
            # A need for reassurance is distinct from wanting to talk.
            if now - self._last_affection_comment >= 25 * 60:
                event = "affection_low"
                self._last_affection_comment = now
            else:
                event = "idle"
        elif tone == "tired" and not (situation and situation.focused):
            event = "tired"
        elif situation is not None and situation.focused:
            if context.night and (situation.strain >= 35 or state.energy <= 45):
                event = "work_late"
            elif situation.prolonged_work_seconds >= 20 * 60:
                event = "work_long_thought"
            else:
                event = "work_concentrating"
        elif (situation is not None and self._last_work_duration >= 20 * 60
              and not self._postwork_thought_spoken
              and 60 <= now - self._last_work_finished_at <= 480):
            event = "after_work_thought"
            self._postwork_thought_spoken = True
        elif situation is not None and situation.mode == "resting":
            event = "quiet_alone" if situation.present is False else "quiet_together"
        elif tone in ("withdrawn", "irritated"):
            event = "low_mood"
        else:
            events = ["idle", "idle", "idle", "idle"]
            if state.friendship >= 78 and state.mood >= 55:
                events.append("close_thought")
            if context.period in ("breakfast", "quiet"):
                events.append("morning")
            if context.period == "lunch":
                events.append("midday")
            if context.period == "evening":
                events.append("evening")
            if context.night:
                events.append("night")
            if context.weekend:
                events.append("weekend")
            if context.local.weekday() == 0:
                events.append("monday")
            if context.local.weekday() == 4:
                events.append("friday")
            event = self.rng.choice(events)
        return self.say_event(event, state, context, now)
