"""Joint World/Pet consumption with origin, receipts and owner recovery."""

from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
from dataclasses import dataclass

from ..pet.consumption import ConsumptionOrigin
from ..pet.mind import PetMind
from ..pet.mind.adaptive import AdaptiveRoutine
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
        self, state: PetState, mind: PetMind, adaptive: AdaptiveRoutine, *,
        clock: ActiveSessionClock,
    ) -> None:
        self._state = state
        self._mind = mind
        self._adaptive = adaptive
        self._clock = clock
        self._receipts: OrderedDict[
            str, tuple[str, ConsumptionOrigin, ConsumptionOutcome]
        ] = OrderedDict()

    def complete(
        self, world: WorldState, interaction_id: str, instance_id: str,
        origin: ConsumptionOrigin, inputs: SessionInputs,
    ) -> ConsumptionOutcome:
        previous = self._receipts.get(interaction_id)
        if previous is not None:
            if previous[:2] != (instance_id, origin):
                raise ValueError("Conflicting consumption interaction")
            return previous[2]
        advance_session_time(self._state, self._clock, inputs)
        item = world.get(instance_id)
        if item.state != ObjectState.PET_HELD:
            return ConsumptionOutcome(False)
        context = context_at(inputs.wall_time)
        before = self._mind.observe_care(self._state, context, inputs.monotonic_time)
        checkpoint = deepcopy(self._state)
        prepared = deepcopy(self._state)
        result = prepared.consume_item(item.definition_id, origin, now=inputs.wall_time)
        if result is None or result.consumed_item_id is None:
            return ConsumptionOutcome(False)
        world_checkpoint = world.snapshot()
        try:
            world.consume(instance_id, expected_revision=item.revision)
            self._state.restore_values(prepared)
        except Exception:
            world.restore_snapshot(world_checkpoint)
            self._state.restore_values(checkpoint)
            raise
        care = CareOutcome(result, None, context)
        outcome = ConsumptionOutcome(True, care)
        self._receipts[interaction_id] = (instance_id, origin, outcome)
        if len(self._receipts) > 4096:
            self._receipts.popitem(last=False)
        if origin == ConsumptionOrigin.HANDOVER:
            self._adaptive.note_interaction(inputs.wall_time)
            self._mind.after_care(result.action, inputs.monotonic_time)
            reaction = self._mind.select_reaction(
                self._mind.care_event(result, before), self._state, context,
                inputs.monotonic_time, tone=before.tone,
            )
            outcome = ConsumptionOutcome(True, CareOutcome(result, reaction, context))
            self._receipts[interaction_id] = (instance_id, origin, outcome)
        return outcome
