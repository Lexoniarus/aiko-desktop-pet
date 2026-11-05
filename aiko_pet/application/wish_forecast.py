"""Simple shared wish deadlines for local catch-up and isolated previews."""

from __future__ import annotations

import random
from collections.abc import Callable
from dataclasses import dataclass, replace

from ..pet.mind.object_memory import ObjectMemory
from ..pet.state import PetState
from ..pet.wishes import WishContext
from ..world.state import WorldState
from .active_time import SessionInputs
from .session_time import SessionTimeProgression


class RoomTimeProgression:
    def __init__(
        self,
        progression: SessionTimeProgression,
        context: Callable[[PetState], WishContext],
    ) -> None:
        self.progression, self.context = progression, context

    def _evaluate(self, state: PetState) -> None:
        deadline = state.wishes.refresh_at
        state.evaluate_wishes(
            self.context(state), rng=random.Random(f"room-wishes:{deadline}")
        )

    def advance(
        self,
        state: PetState,
        inputs: SessionInputs,
        elapsed: float,
        *,
        reconstruct: bool = False,
    ) -> None:
        checkpoint = state.capture_checkpoint()
        world, memory = self.progression.world, self.progression.memory
        physical, cognitive = world.snapshot(), memory.snapshot()
        try:
            remaining = max(0.0, elapsed)
            self._evaluate(state)
            # No movement/dialogue replay. Very long gaps discard obsolete wishes
            # through the same final evaluation instead of a historical event log.
            for _ in range(512):
                if remaining <= 0:
                    break
                deadline = state.wishes.refresh_at
                until = (
                    max(1.0, deadline - state.lived_seconds)
                    if deadline is not None
                    else remaining
                )
                step = min(remaining, until)
                remaining -= step
                endpoint = replace(inputs, wall_time=inputs.wall_time - remaining)
                self.progression.advance(state, endpoint, step, reconstruct=reconstruct)
                self._evaluate(state)
            if remaining:
                self.progression.advance(
                    state, inputs, remaining, reconstruct=reconstruct
                )
                self._evaluate(state)
        except Exception:
            state.restore_checkpoint(checkpoint)
            world.restore_snapshot(physical)
            memory.restore_snapshot(cognitive)
            raise


@dataclass(frozen=True, slots=True)
class ForecastMessage:
    wall_time: float
    kind: str
    text: str


class WishForecastService:
    def plan(
        self,
        state: PetState,
        world: WorldState,
        memory: ObjectMemory,
        inputs: SessionInputs,
        context: Callable[[PetState], WishContext],
        *,
        hours: int = 24,
    ) -> tuple[ForecastMessage, ...]:
        if not 1 <= hours <= 48:
            raise ValueError("Forecast horizon must be between one and 48 hours")
        preview = PetState(updated_at=state.updated_at)
        preview.restore_checkpoint(state.capture_checkpoint())
        physical = world.snapshot()
        other = WorldState(physical.surface, physical.definitions)
        other.restore_snapshot(physical)
        knowledge = ObjectMemory()
        knowledge.restore_snapshot(memory.snapshot())
        progression = RoomTimeProgression(
            SessionTimeProgression(other, knowledge), context
        )
        result: list[ForecastMessage] = []
        emitted: set[str] = set()
        for index in range(hours * 4):
            endpoint = replace(inputs, wall_time=inputs.wall_time + (index + 1) * 900)
            progression.advance(preview, endpoint, 900, reconstruct=True)
            if preview.sleeping:
                continue
            for kind, level, text in (
                ("food", preview.satiety, "Aiko bekommt Hunger."),
                ("rest", preview.energy, "Aiko braucht Ruhe."),
                ("social", preview.social, "Aiko würde sich über Gesellschaft freuen."),
            ):
                if level < 30 and kind not in emitted:
                    emitted.add(kind)
                    result.append(ForecastMessage(endpoint.wall_time, kind, text))
        return tuple(result[:3])
