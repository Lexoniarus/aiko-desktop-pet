"""Care use cases independent of Tkinter, Win32 and persistence adapters."""

from __future__ import annotations

from dataclasses import dataclass

from ..adaptive import AdaptiveRoutine
from ..dialogue import AikoMind, Reaction
from ..pet.state import PetState
from ..pet.routine import TimeContext, context_at
from .commands import CareCommand


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


@dataclass(frozen=True, slots=True)
class CareOutcome:
    """The result of a care use case; presentation is a separate concern."""

    fallback_text: str
    reaction: Reaction | None
    context: TimeContext


class CareController:
    """Coordinate existing pet and conversation rules without UI side effects."""

    def __init__(
        self, state: PetState, mind: AikoMind, adaptive: AdaptiveRoutine,
    ) -> None:
        self._state = state
        self._mind = mind
        self._adaptive = adaptive

    def execute(self, command: CareCommand, runtime: CareRuntime) -> CareOutcome:
        """Preserve the original ordering of time, dialogue and care changes."""
        self._state.advance(
            runtime.wall_time,
            auto_routine=runtime.auto_routine,
            allow_bedtime=runtime.allow_bedtime,
            allow_nap=runtime.allow_nap,
            interrupt_nap=runtime.interrupt_nap,
            effort=runtime.effort,
        )
        self._adaptive.note_interaction(runtime.wall_time)
        context = context_at(runtime.wall_time)
        event, previous_emotion = self._mind.care_event(
            command.action, self._state, context, runtime.monotonic_time,
        )
        fallback = self._state.interact(command.action, now=runtime.wall_time)
        if event not in ("play_tired", "energy_drink_full"):
            self._mind.after_care(command.action, runtime.monotonic_time)
        reaction = self._mind.say_event(
            event, self._state, context, runtime.monotonic_time,
            tone=previous_emotion,
        )
        return CareOutcome(fallback, reaction, context)
