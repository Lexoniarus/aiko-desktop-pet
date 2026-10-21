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
from ..content import GERMAN_TEXT
from ..emotions import (
    EmotionalComposition,
    EmotionalState,
    derive_emotional_state,
    supports_positive_expression,
)
from ..food_catalog import DEFAULT_CATALOG
from ..moodlet_catalog import MOODLET_CATALOG
from ..needs import NeedCondition, assess_need_conditions
from ..routine import TimeContext
from ..state import PetState
from ..wish_catalog import WISH_CATALOG
from ..wishes import ActiveWish, WishArea
from .adaptive_models import Behaviour
from .catalog import DialogueBook, Reaction
from .click_policy import ClickButton, choose_click_reaction
from .cursor_attention import CursorAttention
from .dialogue_context import (
    DialogueContext,
    FriendshipStage,
    ReactionTone,
    SituationalCondition,
)
from .reaction_sequence import Cue
from .work_episode import WorkEpisodeMemory


@dataclass(frozen=True, slots=True)
class CareReactionContext:
    """Conversation facts captured before the care aggregate changes."""

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
        self.click_annoyance = False
        self.click_wakes = False
        self._clicks_during_sleep = False
        self._click_warned = False
        self.irritation_reaction_until = -1.0
        self.warm_reaction_until = -1.0
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
        """Record a short reaction tone, independently of lasting impressions."""
        self.irritation_reaction_until = max(
            self.irritation_reaction_until,
            now + BALANCE.number("mind", "irritation_seconds"),
        )

    def note_sleep_disturbance(self, now: float) -> None:
        """Remember the explicit boundary after being woken by repeated pokes."""
        self.irritation_reaction_until = max(
            self.irritation_reaction_until,
            now + BALANCE.number("mind", "irritation_seconds"),
        )
        self._click_warned = True
        self._clicks_during_sleep = False

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

    def emotional_state(self, state: PetState) -> EmotionalComposition:
        """Overall feeling never reads transient reactions, sleep or need labels."""
        return derive_emotional_state(
            state.mood,
            state.moodlets.active,
            definitions=MOODLET_CATALOG.definitions,
        )

    def reaction_tone(self, now: float) -> ReactionTone | None:
        if now < self.irritation_reaction_until:
            return ReactionTone.IRRITATED
        if now < self.warm_reaction_until:
            return ReactionTone.WARM
        return None

    def dialogue_context(
        self,
        state: PetState,
        context: TimeContext,
        now: float,
        *,
        present: bool | None = None,
    ) -> DialogueContext:
        situation = self.situation
        emotions = self.emotional_state(state)
        conditions: set[SituationalCondition] = set()
        if (
            state.energy <= BALANCE.number("mind", "tired_energy")
            or situation is not None
            and situation.strain >= BALANCE.number("mind", "tired_strain")
            and state.energy <= BALANCE.number("mind", "tired_work_energy")
        ):
            conditions.add(SituationalCondition.FATIGUED)
        if (
            state.mood >= BALANCE.number("mind", "playful_mood")
            and supports_positive_expression(emotions)
            and state.fun >= BALANCE.number("mind", "playful_fun")
            and state.energy >= BALANCE.number("mind", "playful_energy")
        ):
            conditions.add(SituationalCondition.PLAYFUL)
        return DialogueContext(
            stage=FriendshipStage.from_level(state.friendship_level),
            mood_value=state.mood,
            emotions=emotions,
            time=context,
            need_conditions=assess_need_conditions(state.needs),
            reaction_tone=self.reaction_tone(now),
            situational_conditions=frozenset(conditions),
            sleeping=state.sleeping,
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
        dialogue: DialogueContext | None = None,
    ) -> Reaction | None:
        """Choose against an immutable snapshot, including pre-care needs."""
        snapshot = dialogue or self.dialogue_context(state, context, now)
        presentation: Literal["short", "story"] = (
            "story" if event == "talk" and not snapshot.sleeping else "short"
        )
        reaction = self.book.choose(
            event,
            snapshot,
            now,
            presentation=presentation,
        )
        if reaction is None and presentation == "story":
            reaction = self.book.choose(event, snapshot, now, presentation="short")
        if reaction is not None and reaction.presentation == "story":
            self.clicks.clear()
        return reaction

    def wish_reaction(self, wish: ActiveWish) -> Reaction:
        """Render one admitted concrete desire; selection alone is not speech."""
        definition = WISH_CATALOG.definitions[wish.definition_id]
        values: dict[str, str] = {}
        if definition.area == WishArea.FOOD:
            values["target"] = DEFAULT_CATALOG.foods[wish.target_id].display_name
        elif definition.area == WishArea.GAMES:
            values["target"] = GERMAN_TEXT.format(f"game.name.{wish.target_id}")
            if definition.round_count > 1:
                values["rounds"] = str(wish.goal_snapshot.required_count)
        text = GERMAN_TEXT.format(f"wish.{wish.definition_id}.utterance", **values)
        return Reaction(
            f"wish-{wish.instance_id}",
            (Cue.text(text),),
            "idle",
            "wish_expression",
            wish_instance_id=wish.instance_id,
        )

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
        if state.sleeping != self._clicks_during_sleep:
            self.clicks.clear()
        self._clicks_during_sleep = state.sleeping
        if self.clicks and now - self.clicks[-1] > self.CLICK_WINDOW_SECONDS:
            self.clicks.clear()
        if not self.clicks:
            self._click_warned = False
        self.click_annoyance = self._click_warned and not state.sleeping
        self.click_wakes = False
        self.clicks.append(now)
        count = len(self.clicks)
        if not state.sleeping:
            self.work.note_click(self.situation)
        decision = choose_click_reaction(
            button=button,
            click_count=count,
            state=state,
            emotions=self.emotional_state(state),
            context=context,
            situation=self.situation,
            recovering=self.work.recovering(now),
            recently_petted=(
                self._last_care_action == "pet"
                and now - self._last_care_at
                < BALANCE.integer("mind", "petted_click_window_seconds")
            ),
        )
        if decision.wakes:
            self.click_wakes = True
            return None
        if decision.event is None:
            return None
        if decision.irritates:
            self.irritation_reaction_until = max(
                self.irritation_reaction_until,
                now + BALANCE.number("mind", "irritation_seconds"),
            )
        reaction = self.select_reaction(decision.event, state, context, now)
        if reaction is not None and decision.event in (
            "click_boundary",
            "click_work_boundary",
            "click_withdrawn_boundary",
        ):
            self._click_warned = True
        return reaction

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
            if effect == CareEffect.AFFECTION_REFUSED:
                return "pet_refused"
            if self.situation is not None and self.situation.focused:
                return "pet_during_work"
            if before.affection <= BALANCE.integer("mind", "care_low_affection"):
                return "pet_needs_affection"
            return "pet"
        raise ValueError(f"Unknown care event: {action}")

    def record_accepted_care(self, action: str, now: float) -> None:
        """Track accepted care timing separately from its short reaction."""
        self._last_care_action = action
        self._last_care_at = now
        self._start_care_reaction(action, now)

    def _start_care_reaction(self, action: str, now: float) -> None:
        if action in ("pet", "feed", "play", "talk"):
            self.warm_reaction_until = now + (
                BALANCE.integer("mind", "warm_after_pet_seconds")
                if action == "pet"
                else BALANCE.integer("mind", "warm_after_other_care_seconds")
            )
        if action == "sleep":
            self.irritation_reaction_until = -1.0
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
        dialogue = self.dialogue_context(state, context, now)
        situation = self.situation
        if NeedCondition.LOW_SATIETY in dialogue.need_conditions:
            return "hungry"
        if NeedCondition.LOW_SOCIAL in dialogue.need_conditions and not (
            situation and situation.focused
        ):
            # Quiet repeated reminders without suppressing other thoughts.
            if now - self._last_social_comment >= BALANCE.integer(
                "mind", "social_comment_interval_seconds"
            ):
                self._last_social_comment = now
                return "social_low"
            return "idle"
        if NeedCondition.LOW_AFFECTION in dialogue.need_conditions and not (
            situation and situation.focused
        ):
            if now - self._last_affection_comment >= BALANCE.integer(
                "mind", "affection_comment_interval_seconds"
            ):
                self._last_affection_comment = now
                return "affection_low"
            return "idle"
        if SituationalCondition.FATIGUED in dialogue.situational_conditions and not (
            situation and situation.focused
        ):
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
        if (
            dialogue.emotions.primary
            in (
                EmotionalState.SUBDUED,
                EmotionalState.DOWNCAST,
                EmotionalState.IRRITATED,
                EmotionalState.CROWDED,
                EmotionalState.FRUSTRATED,
                EmotionalState.LONELY,
            )
            or dialogue.reaction_tone == ReactionTone.IRRITATED
        ):
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
            and now - self._last_spontaneous_story
            >= BALANCE.integer(
                "dialogue",
                "spontaneous_story_quiet_seconds",
            )
            and self.rng.random()
            < BALANCE.number(
                "dialogue",
                "spontaneous_story_probability",
            )
        ):
            story = self.book.choose(
                "talk",
                snapshot,
                now,
                presentation="story",
            )
            if story is not None:
                self._last_spontaneous_story = now
                self.clicks.clear()
                return story
        return self.select_reaction(event, state, context, now)
