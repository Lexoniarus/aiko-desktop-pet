"""Care use cases independent of Tkinter, Win32 and persistence adapters."""

from __future__ import annotations

from dataclasses import dataclass, replace

from ..pet.care_result import CareEffect, CareResult
from ..pet.interaction_events import SocialCompletion
from ..pet.mind import PetMind
from ..pet.mind.adaptive import AdaptiveRoutine
from ..pet.mind.catalog import Reaction
from ..pet.routine import TimeContext, context_at
from ..pet.state import PetState
from ..pet.wish_catalog import WISH_CATALOG
from ..pet.wishes import WishArea
from .active_time import (
    ActiveSessionClock,
    SessionInputs,
    TimeProgression,
    advance_session_time,
)
from .care_requests import food_variety_event
from .commands import CareCommand


@dataclass(frozen=True, slots=True)
class CareOutcome:
    """The result of a care use case; presentation is a separate concern."""

    result: CareResult
    reaction: Reaction | None
    context: TimeContext

    @property
    def food_consumed(self) -> bool:
        return self.result.food_consumed

    @property
    def consumed_item_id(self) -> str | None:
        return self.result.consumed_item_id


class CareController:
    """Coordinate existing pet and conversation rules without UI side effects."""

    def __init__(
        self,
        state: PetState,
        mind: PetMind,
        adaptive: AdaptiveRoutine,
        *,
        clock: ActiveSessionClock,
        progression: TimeProgression | None = None,
    ) -> None:
        self._state = state
        self._mind = mind
        self._adaptive = adaptive
        self._clock = clock
        self._progression = progression

    def advance_time(self, inputs: SessionInputs) -> None:
        advance_session_time(
            self._state, self._clock, inputs, progression=self._progression,
        )

    def set_wish_pinned(
        self, instance_id: int, pinned: bool, inputs: SessionInputs,
    ) -> None:
        self.advance_time(inputs)
        self._state.set_wish_pinned(instance_id, pinned)

    def dismiss_wish(self, instance_id: int, inputs: SessionInputs) -> None:
        self.advance_time(inputs)
        self._state.dismiss_wish(instance_id)

    def complete_social(
        self, completion: SocialCompletion, inputs: SessionInputs, *,
        arrangement_ready: bool,
    ) -> None:
        self.advance_time(inputs)
        self._state.complete_social_experience(
            completion, arrangement_ready=arrangement_ready,
        )

    def execute(self, command: CareCommand, inputs: SessionInputs) -> CareOutcome:
        """Preserve the original ordering of time, dialogue and care changes."""
        self.advance_time(inputs)
        self._adaptive.note_interaction(inputs.wall_time)
        context = context_at(inputs.wall_time)
        if command.wake_from_clicks:
            # Time progression may already have ended sleep. This command only
            # wakes; replaying a sleep toggle must never put her back to bed.
            result = (
                self._state.interact(
                    "sleep", now=inputs.wall_time,
                    sleep_context=self._adaptive.sleep_context(),
                ) if self._state.sleeping
                else CareResult("sleep", CareEffect.SLEEP_ENDED)
            )
            self._mind.note_sleep_disturbance(inputs.monotonic_time)
            wake_reaction = self._mind.select_reaction(
                "click_wake", self._state, context, inputs.monotonic_time,
            )
            return CareOutcome(result, wake_reaction, context)
        before = self._mind.preview_care(
            self._state,
            context,
            inputs.monotonic_time,
        )
        result = self._state.interact(
            command.action,
            now=inputs.wall_time,
            food_id=command.food_id,
            sleep_context=self._adaptive.sleep_context(),
        )
        event = (food_variety_event(self._state, result)
                 or self._mind.care_event(result, before))
        if result.effect not in (
            CareEffect.PLAY_TIRED,
            CareEffect.DRINK_SATISFIED,
        ) and not result.affection_refused:
            self._mind.record_care_contact(inputs.monotonic_time)
            self._mind.record_accepted_care(command.action, inputs.monotonic_time)
        reaction: Reaction | None
        if command.conversation is not None:
            reaction = command.conversation.reaction
        else:
            reaction = self._mind.select_reaction(
                event,
                self._state,
                context,
                inputs.monotonic_time,
                dialogue=before.dialogue,
            )
        if result.effect == CareEffect.CONVERSATION and reaction is not None:
            category = (command.conversation.category.value
                        if command.conversation is not None else "chat")
            wish = next((w for w in self._state.wishes.active
                         if WISH_CATALOG.definitions[w.definition_id].area
                         == WishArea.SOCIAL and w.target_id == category), None)
            reaction = replace(reaction, completed_social=SocialCompletion(
                category, wish.instance_id if wish else None,
            ))
        return CareOutcome(result, reaction, context)
