"""Care use cases independent of Tkinter, Win32 and persistence adapters."""

from __future__ import annotations

from dataclasses import dataclass

from ..pet.mind.adaptive import AdaptiveRoutine
from ..pet.mind import PetMind
from ..pet.mind.catalog import Reaction
from ..pet.food import FoodActivity, FOOD_BALANCE, DEFAULT_FOOD_ID
from ..pet.state import PetState
from ..pet.routine import TimeContext, context_at
from .commands import CareCommand
from .active_time import ActiveSessionClock


@dataclass(frozen=True, slots=True)
class CareRuntime:
    """Trusted clock and observed conditions supplied by the desktop host."""

    wall_time: float
    monotonic_time: float
    auto_routine: bool
    allow_bedtime: bool | None
    allow_nap: bool
    interrupt_nap: bool
    effort: float | None
    food_activity: FoodActivity | None = None


@dataclass(frozen=True, slots=True)
class CareOutcome:
    """The result of a care use case; presentation is a separate concern."""

    fallback_text: str
    reaction: Reaction | None
    context: TimeContext
    food_consumed: bool = False
    consumed_item_id: str | None = None


class CareController:
    """Coordinate existing pet and conversation rules without UI side effects."""

    def __init__(
        self, state: PetState, mind: PetMind, adaptive: AdaptiveRoutine,
        *, clock: ActiveSessionClock,
    ) -> None:
        self._state = state
        self._mind = mind
        self._adaptive = adaptive
        self._clock = clock

    def execute(self, command: CareCommand, runtime: CareRuntime) -> CareOutcome:
        """Preserve the original ordering of time, dialogue and care changes."""
        self._state.advance(
            runtime.wall_time,
            auto_routine=runtime.auto_routine,
            allow_bedtime=runtime.allow_bedtime,
            allow_nap=runtime.allow_nap,
            interrupt_nap=runtime.interrupt_nap,
            effort=runtime.effort,
            elapsed_seconds=self._clock.consume(),
            food_activity=runtime.food_activity,
        )
        self._adaptive.note_interaction(runtime.wall_time)
        context = context_at(runtime.wall_time)
        event, previous_emotion = self._mind.care_event(
            command.action, self._state, context, runtime.monotonic_time,
            food_id=command.food_id,
        )
        food_consumed = (
            command.action == "feed"
            and self._state.satiety < FOOD_BALANCE.too_full_to_eat_threshold
        )
        drink_consumed = (
            command.action == "energy_drink" and self._state.energy < 100
        )
        fallback = self._state.interact(
            command.action, now=runtime.wall_time, food_id=command.food_id,
        )
        if event not in ("play_tired", "energy_drink_full"):
            self._mind.after_care(command.action, runtime.monotonic_time)
        reaction = self._mind.select_reaction(
            event, self._state, context, runtime.monotonic_time,
            tone=previous_emotion,
        )
        item_id = (
            (command.food_id or DEFAULT_FOOD_ID) if food_consumed
            else ("energy_drink" if drink_consumed else None)
        )
        return CareOutcome(fallback, reaction, context, food_consumed, item_id)
