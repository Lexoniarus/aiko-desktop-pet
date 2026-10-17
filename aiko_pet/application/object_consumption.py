"""Joint World/Pet consumption with origin, receipts and owner recovery."""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass

from ..pet.consumption import ConsumptionOrigin
from ..pet.mind import PetMind
from ..pet.mind.adaptive import AdaptiveRoutine
from ..pet.mind.object_memory import ObjectMemory
from ..pet.routine import context_at
from ..pet.state import PetState
from ..world.contracts import ObjectState
from ..world.state import WorldState
from .active_time import ActiveSessionClock, SessionInputs, advance_session_time
from .controller import CareOutcome


@dataclass(frozen=True, slots=True)
class ConsumptionOutcome:
    accepted: bool
    care: CareOutcome | None = None


class ObjectConsumption:
    def __init__(
        self,
        state: PetState,
        mind: PetMind,
        adaptive: AdaptiveRoutine,
        *,
        clock: ActiveSessionClock,
        memory: ObjectMemory,
    ) -> None:
        self._state = state
        self._mind = mind
        self._adaptive = adaptive
        self._clock = clock
        self._memory = memory
        self._receipts: OrderedDict[
            str, tuple[str, str, ConsumptionOrigin, ConsumptionOutcome]
        ] = OrderedDict()

    def commit(
        self,
        world: WorldState,
        interaction_id: str,
        instance_id: str,
        origin: ConsumptionOrigin,
        inputs: SessionInputs, *, memory_id: str,
    ) -> ConsumptionOutcome:
        """Commit effects once at consumption start, before visual playback ends."""
        previous = self._receipts.get(interaction_id)
        if previous is not None:
            if previous[:3] != (instance_id, memory_id, origin):
                raise ValueError("Conflicting consumption interaction")
            return previous[3]
        advance_session_time(self._state, self._clock, inputs)
        item = world.get(instance_id)
        if item.state != ObjectState.PET_HELD:
            return ConsumptionOutcome(False)
        context = context_at(inputs.wall_time)
        before = (
            self._mind.observe_care(self._state, context, inputs.monotonic_time)
            if origin == ConsumptionOrigin.HANDOVER
            else None
        )
        checkpoint = self._state.capture_checkpoint()
        definition = next(
            definition
            for definition in world.snapshot().definitions
            if definition.definition_id == item.definition_id
        )
        consumable_id = definition.food_id or "energy_drink"
        known = self._memory.get(memory_id)
        if known is None or known.identity != consumable_id:
            return ConsumptionOutcome(False)
        prepared = self._state.prepare_item_consumption(
            consumable_id, origin, now=inputs.wall_time,
        )
        if prepared is None:
            return ConsumptionOutcome(False)
        world_checkpoint = world.snapshot()
        memory_checkpoint = self._memory.snapshot()
        try:
            world.consume(instance_id, expected_revision=item.revision)
            self._state.restore_checkpoint(prepared.checkpoint)
            self._memory.record_consumption(memory_id)
        except Exception:
            world.restore_snapshot(world_checkpoint)
            self._state.restore_checkpoint(checkpoint)
            self._memory.restore_snapshot(memory_checkpoint)
            raise
        care = CareOutcome(prepared.result, None, context)
        outcome = ConsumptionOutcome(True, care)
        self._receipts[interaction_id] = (instance_id, memory_id, origin, outcome)
        if len(self._receipts) > 4096:
            self._receipts.popitem(last=False)
        if origin == ConsumptionOrigin.HANDOVER:
            assert before is not None
            self._adaptive.note_interaction(inputs.wall_time)
            self._mind.after_care(prepared.result.action, inputs.monotonic_time)
            reaction = self._mind.select_reaction(
                self._mind.care_event(prepared.result, before),
                self._state,
                context,
                inputs.monotonic_time,
                tone=before.tone,
                dialogue=before.dialogue,
            )
            outcome = ConsumptionOutcome(True, CareOutcome(result, reaction, context))
            self._receipts[interaction_id] = (instance_id, memory_id, origin, outcome)
        return outcome
