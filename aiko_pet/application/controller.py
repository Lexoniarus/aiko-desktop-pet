"""Care use cases independent of Tkinter, Win32 and persistence adapters."""

from __future__ import annotations

from dataclasses import dataclass

from ..pet.care_result import CareEffect, CareResult
from ..pet.mind import PetMind
from ..pet.mind.adaptive import AdaptiveRoutine
from ..pet.mind.catalog import Reaction
from ..pet.routine import TimeContext, context_at
from ..pet.state import PetState
from .active_time import (
    ActiveSessionClock,
    SessionInputs,
    TimeProgression,
    advance_session_time,
)
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

    def execute(self, command: CareCommand, inputs: SessionInputs) -> CareOutcome:
        """Preserve the original ordering of time, dialogue and care changes."""
        advance_session_time(
            self._state, self._clock, inputs, progression=self._progression,
        )
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
        before = self._mind.observe_care(
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
        event = self._mind.care_event(result, before)
        if result.effect not in (
            CareEffect.PLAY_TIRED,
            CareEffect.DRINK_SATISFIED,
        ):
            self._mind.after_care(command.action, inputs.monotonic_time)
        reaction: Reaction | None
        if command.conversation is not None:
            reaction = command.conversation.reaction
        else:
            reaction = self._mind.select_reaction(
                event,
                self._state,
                context,
                inputs.monotonic_time,
                tone=before.tone,
                dialogue=before.dialogue,
            )
        return CareOutcome(result, reaction, context)
