"""Bridge objective World values into subjective pet observations and goals."""

from __future__ import annotations

import math
from dataclasses import replace

from ..pet.balance import BALANCE
from ..pet.consumption import ConsumptionOrigin
from ..pet.mind.object_decisions import ObjectUseDecision, decide_object_use
from ..pet.mind.object_intentions import ObjectGoal, ObjectIntentions
from ..pet.mind.object_knowledge import ObjectKnowledge, ObjectMemorySnapshot
from ..pet.mind.object_memory import ObjectMemory
from ..pet.mind.object_perception import (
    ObjectCandidate,
    ObjectObservation,
    ObjectPerception,
)
from ..pet.state import PetState
from ..world.contracts import ObjectInteraction, ObjectState, WorldSnapshot
from .object_tracking import ObjectTracker


class ObjectAwareness:
    def __init__(self, saved: ObjectMemorySnapshot | None = None) -> None:
        self.perception = ObjectPerception()
        self.memory = ObjectMemory(saved)
        self.intentions = ObjectIntentions()
        self.observations: tuple[ObjectObservation, ...] = ()
        self._world_revision = -1
        self._tracker = ObjectTracker(maximum_gap=BALANCE.number(
            "object_behavior", "tracking_gap_seconds",
        ))
        self._sighting_records: dict[str, str] = {}
        self._world_records: dict[str, str] = {}
        self._owned_records: dict[str, str] = {}
        self._unnoticed: tuple[ObjectCandidate, ...] = ()

    def checked_empty(self, x: float, *, width: float, now: float) -> bool:
        """Do not turn pending local sensory evidence into confirmed absence."""
        if self.perception.attentive_seconds(now) < BALANCE.number(
            "object_behavior", "notice_seconds",
        ):
            return False
        reach = width * BALANCE.number("object_behavior", "memory_place_widths")
        return not any(abs(item.x - x) <= reach for item in self.observations
                       if item.resting) and not any(
                           abs(item.x - x) <= reach for item in self._unnoticed
                       )

    def record_for_instance(self, instance: str) -> str | None:
        return self._world_records.get(instance)

    def instance_for_record(self, record: str) -> str | None:
        return next((instance for instance, key in self._world_records.items()
                     if key == record), None)

    def known_instance(self, instance: str) -> ObjectKnowledge | None:
        record = self.record_for_instance(instance)
        return self.memory.get(record) if record is not None else None

    def assess_offer(self, token: str, state: PetState) -> ObjectUseDecision | None:
        """Assess only a currently recognized offer, never hidden World truth."""
        known = self.memory.get(token)
        if known is None or not any(
            seen.token == token and seen.identity == known.identity
            and seen.kind == known.kind and seen.identity is not None
            for seen in self.observations
        ):
            return None
        decision = decide_object_use(known, state, ConsumptionOrigin.HANDOVER)
        if decision.reason in ("unrecognized", "unavailable"):
            return None
        self.memory.mark_assessed(token)
        return decision

    def update(
        self, world: WorldSnapshot, state: PetState, *, now: float,
        x: float, height: float, width: float, attentive: bool, blocked: bool,
        held_pose: tuple[float, float] | None = None,
        committed: str | None = None,
    ) -> ObjectGoal | None:
        definitions = {item.definition_id: item for item in world.definitions}
        candidates: list[ObjectCandidate] = []
        own_actions: dict[str, str] = {}
        held: dict[str, str] = {}
        for item in world.objects:
            record = self._owned_records.get(item.instance_id)
            if item.state == ObjectState.PET_HELD:
                record = record or self._world_records.get(item.instance_id)
                if record is not None:
                    held[item.instance_id] = record
                    own_actions[item.instance_id] = record
            elif record is not None and item.state == ObjectState.RESTING:
                known = self.memory.get(record)
                if (known is not None and known.resting and item.position is not None
                        and (known.x, known.height)
                        == (item.position.x, item.position.height)):
                    own_actions[item.instance_id] = record
                    held[item.instance_id] = record
            pose = ((item.position.x, item.position.height)
                    if item.position is not None else
                    held_pose if item.state == ObjectState.PET_HELD else None)
            if pose is None:
                continue
            definition = definitions[item.definition_id]
            candidates.append(ObjectCandidate(
                item.instance_id, definition.food_id or definition.definition_id,
                "drink" if ObjectInteraction.DRINK in definition.interactions
                else "food", *pose,
                item.state == ObjectState.RESTING,
            ))
        visible = tuple(item for item in candidates if attentive and math.hypot(
            item.x - x, item.height - height,
        ) <= width * BALANCE.number("object_behavior", "notice_widths"))
        tracked = self._tracker.update(
            visible, now=now, maximum_distance=width * BALANCE.number(
                "object_behavior", "tracking_jump_widths",
            ),
        )
        sensed = self.perception.observe(
            tracked, now=now, x=x, height=height,
            width=width, attentive=attentive,
        )
        noticed = {seen.token for seen in sensed}
        self._unnoticed = tuple(item for item in tracked if item.token not in noticed)
        previous = {(item.token, item.identity, item.x, item.height, item.resting,
                     item.assessed, item.disposition, item.place_status)
                    for item in self.memory.snapshot()}
        claimed = {self._sighting_records[item.token] for item in sensed
                   if item.token in self._sighting_records}
        records: dict[str, str] = {}
        world_records: dict[str, str] = {}
        observations = []
        self.memory.update((), now=now)
        for seen in sensed:
            instance = self._tracker.resolve(seen.token)
            old = (own_actions.get(instance) if instance is not None else None)
            old = old or self._sighting_records.get(seen.token)
            record = self.memory.observe_find(
                seen, now=now, record=old,
                claimed=frozenset(claimed - {old}) if old is not None
                else frozenset(claimed),
                maximum_distance=width * BALANCE.number(
                    "object_behavior", "memory_place_widths",
                ),
            )
            claimed.add(record)
            records[seen.token] = record
            if instance is not None:
                world_records[instance] = record
                if seen.resting:
                    held.pop(instance, None)
            observations.append(replace(seen, token=record))
        self._sighting_records, self._world_records = records, world_records
        self._owned_records = held
        self.observations = tuple(observations)
        current = {(item.token, item.identity, item.x, item.height, item.resting,
                    item.assessed, item.disposition, item.place_status)
                   for item in self.memory.snapshot()}
        changed = previous != current or self._world_revision != world.revision
        self._world_revision = world.revision
        return self.intentions.choose(self.memory.snapshot(), state, x=x,
                                      now=now, blocked=blocked, changed=changed,
                                      committed=committed,
                                      observed=frozenset(item.token
                                                         for item in observations))
