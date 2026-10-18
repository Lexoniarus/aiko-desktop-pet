"""Situational dialogue decisions for a locally authored desktop pet.

The authored dialogue catalogue and its validation live in pet.mind.catalog.
"""

from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass
from typing import Literal

from ..balance import BALANCE
from ..care_result import CareEffect, CareResult
from ..routine import TimeContext
from ..state import PetState
from .adaptive_models import Behaviour
from .catalog import DialogueBook, Reaction
from .click_policy import ClickButton, choose_click_reaction
from .cursor_attention import CursorAttention
from .dialogue_context import DialogueContext, FriendshipStage
from .work_episode import WorkEpisodeMemory


@dataclass(frozen=True, slots=True)
class CareReactionContext:
    """Conversation facts captured before the care aggregate changes."""

    tone: str
    affection: float
    meal_due: bool
    dialogue: DialogueContext


class PetMind:
    """Situational reactions with a short, decaying social memory.

    A character catalogue supplies the authored reactions. Their context
    depends on observed work, need levels and the pet's recent interactions.
    """

    RETURN_AFTER_SECONDS = BALANCE.integer("mind", "return_after_seconds")
    CLICK_WINDOW_SECONDS = BALANCE.number("mind", "click_window_seconds")
    MAX_CLICKS_IN_BURST = BALANCE.integer("mind", "maximum_clicks_in_burst")

    def __init__(
        self,
        book: DialogueBook,
        *,
        rng: random.Random | None = None,
        started_at: float = 0.0,
    ) -> None:
        self.rng = rng or random.Random()
        self.book = book
        self.clicks: deque[float] = deque(maxlen=self.MAX_CLICKS_IN_BURST)
        self.irritated_until = -1.0
        self.warm_until = -1.0
        self.last_contact = started_at
        self.cursor_attention = CursorAttention()
        self.situation: Behaviour | None = None
        self.work = WorkEpisodeMemory()
        self._last_care_action = ""
        self._last_care_at = -1.0
        self._last_social_comment = float("-inf")
        self._last_affection_comment = float("-inf")
        self._last_spontaneous_story = float("-inf")

    def note_object_withholding(self, now: float) -> None:
        """Express temporary frustration using the existing emotion owner."""
        self.irritated_until = max(
            self.irritated_until, now + BALANCE.number("mind", "irritation_seconds"),
        )

    def set_situation(
        self,
        situation: Behaviour | None,
        *,
        now: float | None = None,
    ) -> None:
        """Remember an observed work session, never infer unseen work."""
        previous = self.situation
        self.situation = situation
        self.work.observe(previous, situation, now=now)

    def emotion(self, state: PetState, now: float) -> str:
        if state.sleeping:
            return "asleep"
        if now < self.irritated_until:
            return "irritated"
        if (
            self.situation is not None
            and self.situation.strain >= BALANCE.integer("mind", "tired_strain")
            and state.energy <= BALANCE.integer("mind", "tired_work_energy")
        ):
            return "tired"
        if (
            self.situation is not None
            and self.situation.strain >= 60
            and state.mood <= BALANCE.integer("mind", "withdrawn_work_mood")
        ):
            return "withdrawn"
        if state.energy <= BALANCE.integer("mind", "tired_energy"):
            return "tired"
        if state.satiety <= BALANCE.integer("mind", "hungry_satiety"):
            return "hungry"
        if state.mood <= BALANCE.integer("mind", "withdrawn_mood"):
            return "withdrawn"
        if state.social <= BALANCE.integer("mind", "lonely_social"):
            return "lonely"
        if state.affection <= BALANCE.integer("mind", "low_affection"):
            return "seeking_affection"
        if now < self.warm_until:
            return "warm"
        if (
            state.mood >= BALANCE.integer("mind", "playful_mood")
            and state.fun >= BALANCE.integer("mind", "playful_fun")
            and state.energy >= BALANCE.integer("mind", "playful_energy")
        ):
            return "playful"
        return "calm"

    def dialogue_context(
        self,
        state: PetState,
        context: TimeContext,
        now: float,
        *,
        present: bool | None = None,
    ) -> DialogueContext:
        needs = set()
        for name, value, threshold in (
            ("hungry", state.satiety, BALANCE.integer("mind", "hungry_satiety")),
            ("tired", state.energy, BALANCE.integer("mind", "tired_energy")),
            ("lonely", state.social, BALANCE.integer("mind", "care_lonely_social")),
            (
                "seeking_affection",
                state.affection,
                BALANCE.integer("mind", "care_low_affection"),
            ),
        ):
            if value <= threshold:
                needs.add(name)
        situation = self.situation
        return DialogueContext(
            FriendshipStage.from_level(state.friendship_level),
            self.emotion(state, now),
            context,
            frozenset(needs),
            working=bool(situation and situation.focused),
            present=present
            if present is not None
            else (situation.present if situation else None),
        )

    def select_reaction(
        self,
        event: str,
        state: PetState,
        context: TimeContext,
        now: float,
        *,
        tone: str | None = None,
        dialogue: DialogueContext | None = None,
    ) -> Reaction | None:
        """Choose against an immutable snapshot, including pre-care needs."""
        snapshot = dialogue or self.dialogue_context(state, context, now)
        mood = tone or snapshot.mood
        presentation: Literal["short", "story"] = (
            "story" if event == "talk" and mood != "asleep" else "short"
        )
        reaction = self.book.choose(
            event,
            mood,
            snapshot.time,
            now,
            dialogue=snapshot,
            presentation=presentation,
        )
        if reaction is None and presentation == "story":
            reaction = self.book.choose(
                event, mood, snapshot.time, now, dialogue=snapshot, presentation="short"
            )
        if reaction is not None and reaction.presentation == "story":
            self.clicks.clear()
        return reaction

    def contact_text(
        self, event: str, state: PetState, context: TimeContext, now: float
    ) -> str:
        """Choose short copy for deliberate game or farewell contact."""
        reaction = self.select_reaction(
            event,
            state,
            context,
            now,
            dialogue=self.dialogue_context(state, context, now, present=True),
        )
        if reaction is None:
            raise ValueError(f"Missing contact dialogue: {event}")
        return reaction.text

    def click(
        self,
        button: ClickButton,
        state: PetState,
        context: TimeContext,
        now: float,
    ) -> Reaction | None:
        """Track one click and request the context-appropriate dialogue event."""
        if button not in ("left", "right"):
            raise ValueError("Unknown mouse button")
        self.last_contact = now
        if self.clicks and now - self.clicks[-1] > self.CLICK_WINDOW_SECONDS:
            self.clicks.clear()
        self.clicks.append(now)
        count = len(self.clicks)
        if state.sleeping:
            return self.select_reaction("sleep_click", state, context, now)

        self.work.note_click(self.situation)
        decision = choose_click_reaction(
            button=button,
            click_count=count,
            state=state,
            context=context,
            situation=self.situation,
            recovering=self.work.recovering(now),
            recently_petted=(
                self._last_care_action == "pet"
                and now - self._last_care_at
                < BALANCE.integer("mind", "petted_click_window_seconds")
            ),
        )
        if decision.event is None:
            return None
        if decision.irritates:
            self.irritated_until = max(
                self.irritated_until, now + BALANCE.number("mind", "irritation_seconds")
            )
        return self.select_reaction(decision.event, state, context, now)

    def observe_care(
        self,
        state: PetState,
        context: TimeContext,
        now: float,
    ) -> CareReactionContext:
        """Record an actual care contact and capture its preceding context."""
        before = self.preview_care(state, context, now)
        self.record_care_contact(now)
        return before

    def preview_care(
        self,
        state: PetState,
        context: TimeContext,
        now: float,
    ) -> CareReactionContext:
        """Read pre-care facts without claiming an uncommitted interaction."""
        return CareReactionContext(
            tone=self.emotion(state, now),
            affection=state.affection,
            dialogue=self.dialogue_context(state, context, now, present=True),
            meal_due=bool(
                context.meal
                and (
                    context.day_key != state.meals_date
                    or context.meal not in state.meals_today
                )
            ),
        )

    def record_care_contact(self, now: float) -> None:
        """Only call after a concrete human care action has been accepted."""
        self.last_contact = now

    def care_event(self, result: CareResult, before: CareReactionContext) -> str:
        """Interpret the one committed effect without deciding acceptance again."""
        action = result.action
        effect = result.effect
        if action == "feed":
            if effect == CareEffect.FOOD_SATISFIED:
                return "feed_full"
            if effect == CareEffect.FOOD_REPEAT:
                return "feed_repeat"
            return "feed_meal" if before.meal_due else "feed_snack"
        if action == "play":
            if effect == CareEffect.PLAY_TIRED:
                return "play_tired"
            return "play"
        if action == "talk":
            if self.situation is not None and self.situation.focused:
                return "talk_busy"
            return "talk"
        if action == "energy_drink":
            return (
                "energy_drink_full"
                if effect == CareEffect.DRINK_SATISFIED
                else "energy_drink"
            )
        if action == "sleep":
            return "wake" if effect == CareEffect.SLEEP_ENDED else "sleep"
        if action == "pet":
            if self.situation is not None and self.situation.focused:
                return "pet_during_work"
            if before.affection <= BALANCE.integer("mind", "care_low_affection"):
                return "pet_needs_affection"
            return "pet"
        raise ValueError(f"Unknown care event: {action}")

    def after_care(self, action: str, now: float) -> None:
        self._last_care_action = action
        self._last_care_at = now
        if action in ("pet", "feed", "play", "talk"):
            self.warm_until = now + (
                BALANCE.integer("mind", "warm_after_pet_seconds")
                if action == "pet"
                else BALANCE.integer("mind", "warm_after_other_care_seconds")
            )
        if action == "sleep":
            self.irritated_until = -1.0
            self.clicks.clear()

    def recently_cared_for(self, now: float) -> bool:
        """Give accepted care three minutes before another gentle request."""
        return self._last_care_at >= 0 and now - self._last_care_at < BALANCE.integer(
            "care_requests", "post_care_quiet_seconds"
        )

    def select_computer_reaction(
        self,
        event: str,
        state: PetState,
        context: TimeContext,
        now: float,
    ) -> Reaction | None:
        """Interpret meaningful work transitions in the lived context."""
        event = self.work.interpret_event(event, self.situation, now)
        if event == "computer_uptime":
            event = "computer_uptime_grounded"
        return self.select_reaction(event, state, context, now)

    def return_to_pet(
        self,
        state: PetState,
        context: TimeContext,
        now: float,
    ) -> Reaction | None:
        elapsed = now - self.last_contact
        self.last_contact = now
        if state.sleeping or elapsed < self.RETURN_AFTER_SECONDS:
            return None
        if self.situation is not None and self.situation.focused:
            event = "return_working"
        elif self.work.recovering(now):
            event = "return_after_work"
        else:
            event = "return"
        return self.select_reaction(event, state, context, now)

    def _choose_idle_topic(self, state: PetState, context: TimeContext) -> str:
        """Select a grounded idle topic using the existing weighted rotation."""
        events = ["idle", "idle", "idle", "idle"]
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
        return self.rng.choice(events)

    def _select_spontaneous_event(
        self,
        state: PetState,
        context: TimeContext,
        now: float,
    ) -> str:
        """Prioritize real needs, measured work and recently observed rest."""
        tone = self.emotion(state, now)
        situation = self.situation
        if tone == "hungry":
            return "hungry"
        if tone == "lonely" and not (situation and situation.focused):
            # Quiet repeated reminders without suppressing other thoughts.
            if now - self._last_social_comment >= BALANCE.integer(
                "mind", "social_comment_interval_seconds"
            ):
                self._last_social_comment = now
                return "social_low"
            return "idle"
        if tone == "seeking_affection" and not (situation and situation.focused):
            if now - self._last_affection_comment >= BALANCE.integer(
                "mind", "affection_comment_interval_seconds"
            ):
                self._last_affection_comment = now
                return "affection_low"
            return "idle"
        if tone == "tired" and not (situation and situation.focused):
            return "tired"
        if situation is not None and situation.focused:
            if context.night and (
                situation.strain >= BALANCE.integer("mind", "work_comment_strain")
                or state.energy <= BALANCE.integer("mind", "work_comment_energy")
            ):
                return "work_late"
            if situation.prolonged_work_seconds >= BALANCE.integer(
                "mind", "prolonged_work_seconds"
            ):
                return "work_long_thought"
            return "work_concentrating"
        if situation is not None and self.work.take_postwork_thought(now):
            return "after_work_thought"
        if situation is not None and situation.mode == "resting":
            return "quiet_alone" if situation.present is False else "quiet_together"
        if tone in ("withdrawn", "irritated"):
            return "low_mood"
        return self._choose_idle_topic(state, context)

    def select_spontaneous_reaction(
        self,
        state: PetState,
        context: TimeContext,
        now: float,
    ) -> Reaction | None:
        """Speak about actual observations, without imagined applications."""
        if state.sleeping:
            return None
        event = self._select_spontaneous_event(state, context, now)
        snapshot = self.dialogue_context(state, context, now)
        if (
            event in ("idle", "low_mood", "tired", "social_low", "affection_low")
            and not snapshot.working
            and snapshot.present is True
            and now - self._last_spontaneous_story >= BALANCE.integer(
                "dialogue", "spontaneous_story_quiet_seconds",
            )
            and self.rng.random() < BALANCE.number(
                "dialogue", "spontaneous_story_probability",
            )
        ):
            story = self.book.choose(
                "talk",
                snapshot.mood,
                context,
                now,
                dialogue=snapshot,
                presentation="story",
            )
            if story is not None:
                self._last_spontaneous_story = now
                self.clicks.clear()
                return story
        return self.select_reaction(event, state, context, now)
