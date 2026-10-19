"""Joint World/Pet consumption with origin, receipts and owner recovery."""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass

from ..pet.consumption import ConsumptionOrigin
from ..pet.mind import PetMind
from ..pet.mind.adaptive import AdaptiveRoutine
from ..pet.mind.object_knowledge import ObjectKnowledge
from ..pet.mind.object_memory import ObjectMemory
from ..pet.mind.object_perception import ConsumableKind
from ..pet.routine import context_at
from ..pet.state import PetState
from ..pet.state_values import PreparedItemConsumption
from ..world.contracts import ObjectState
from ..world.state import WorldState
from .active_time import (
    ActiveSessionClock,
    SessionInputs,
    TimeProgression,
    advance_session_time,
)
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
        progression: TimeProgression | None = None,
        memory: ObjectMemory,
    ) -> None:
        self._state = state
        self._mind = mind
        self._adaptive = adaptive
        self._clock = clock
        self._progression = progression
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
        advance_session_time(
            self._state, self._clock, inputs, progression=self._progression,
        )
        item = world.get(instance_id)
        if item.state != ObjectState.PET_HELD:
            return ConsumptionOutcome(False)
        context = context_at(inputs.wall_time)
        before = (
            self._mind.preview_care(self._state, context, inputs.monotonic_time)
            if origin == ConsumptionOrigin.HANDOVER
            else None
        )
        prepared = self.apply_portion(
            self._state, world, self._memory, instance_id, memory_id,
            origin, now=inputs.wall_time,
        )
        if prepared is None:
            return ConsumptionOutcome(False)
        care = CareOutcome(prepared.result, None, context)
        outcome = ConsumptionOutcome(True, care)
        self._receipts[interaction_id] = (instance_id, memory_id, origin, outcome)
        if len(self._receipts) > 4096:
            self._receipts.popitem(last=False)
        if origin == ConsumptionOrigin.HANDOVER:
            assert before is not None
            self._mind.record_care_contact(inputs.monotonic_time)
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
            outcome = ConsumptionOutcome(
                True, CareOutcome(prepared.result, reaction, context),
            )
            self._receipts[interaction_id] = (instance_id, memory_id, origin, outcome)
        return outcome

    @staticmethod
    def remembered_sources(
        memory: ObjectMemory, *, kind: ConsumableKind = "food",
    ) -> tuple[ObjectKnowledge, ...]:
        """Subjective grounds for trying a place, without polling World truth."""
        return tuple(known for known in memory.snapshot()
                     if known.recognized and known.assessed and known.kind == kind
                     and known.resting and known.place_status == "remembered")

    @staticmethod
    def remembered_stock(
        world: WorldState, memory: ObjectMemory, *, kind: ConsumableKind = "food",
    ) -> tuple[ObjectKnowledge, ...]:
        """Only acquired identity and an unchanged accessible resting place qualify."""
        snapshot = world.snapshot()
        objects = {item.instance_id: item for item in snapshot.objects}
        definitions = {item.definition_id: item for item in snapshot.definitions}
        result: list[ObjectKnowledge] = []
        if any(item.state == ObjectState.PET_HELD for item in snapshot.objects):
            return ()
        for known in ObjectConsumption.remembered_sources(memory, kind=kind):
            item = objects.get(known.instance_id or "")
            if (item is None or item.state != ObjectState.RESTING
                    or item.position is None or not known.at_place(
                        x=item.position.x, height=item.position.height, resting=True,
                    ) or (definitions[item.definition_id].food_id
                          or item.definition_id) != known.identity):
                continue
            result.append(known)
        return tuple(sorted(result, key=lambda entry: entry.token))

    @staticmethod
    def apply_portion(
        state: PetState, world: WorldState, memory: ObjectMemory,
        instance_id: str, memory_id: str, origin: ConsumptionOrigin,
        *, now: float, collect: bool = False,
    ) -> PreparedItemConsumption | None:
        """One transaction for animation intake and historical known-stock intake."""
        item = world.get(instance_id)
        if collect:
            known = memory.get(memory_id)
            if known is None or known.kind is None:
                return None
            if not any(k.token == memory_id and k.instance_id == instance_id
                       for k in ObjectConsumption.remembered_stock(
                           world, memory, kind=known.kind,
                       )):
                return None
        elif item.state != ObjectState.PET_HELD:
            return None
        definition = next(d for d in world.snapshot().definitions
                          if d.definition_id == item.definition_id)
        consumable = definition.food_id or "energy_drink"
        known = memory.get(memory_id)
        if known is None or known.identity != consumable:
            return None
        prepared = state.prepare_item_consumption(consumable, origin, now=now)
        if prepared is None:
            return None
        checkpoint, physical, cognitive = (
            state.capture_checkpoint(), world.snapshot(), memory.snapshot(),
        )
        try:
            if collect:
                item = world.collect_resting(
                    instance_id, expected_revision=item.revision,
                )
            world.consume(instance_id, expected_revision=item.revision)
            state.restore_checkpoint(prepared.checkpoint)
            memory.record_consumption(memory_id)
            if origin == ConsumptionOrigin.AUTONOMOUS:
                state.note_sleep_intake()
        except Exception:
            world.restore_snapshot(physical)
            state.restore_checkpoint(checkpoint)
            memory.restore_snapshot(cognitive)
            raise
        return prepared
