"""Bridge objective World values into subjective pet observations and goals."""

from __future__ import annotations

import math
from dataclasses import replace

from ..pet.balance import BALANCE
from ..pet.mind.object_absence import ObjectAbsencePerception
from ..pet.mind.object_decisions import ObjectUseDecision
from ..pet.mind.object_intentions import ObjectGoal, ObjectIntentions
from ..pet.mind.object_knowledge import ObjectKnowledge, ObjectMemorySnapshot
from ..pet.mind.object_memory import ObjectMemory
from ..pet.mind.object_perception import (
    ItemPresentation,
    ObjectCandidate,
    ObjectObservation,
    ObjectPerception,
)
from ..pet.state import PetState
from ..world.contracts import ObjectInteraction, ObjectState, WorldSnapshot
from .object_tracking import ObjectTracker


def held_type_conflicts_with_memory(
    known: ObjectKnowledge | None, instance: str, world: WorldSnapshot,
) -> bool:
    """Require hand identification when physical type contradicts old knowledge.

    Only the application boundary compares objective and subjective values;
    the result is a safety guard, never an identification event or new type
    written into Aiko's memory.
    """
    if known is None or not known.recognized:
        return False
    item = next((entry for entry in world.objects
                 if entry.instance_id == instance), None)
    if item is None or item.state != ObjectState.PET_HELD:
        return True
    definition = next((entry for entry in world.definitions
                       if entry.definition_id == item.definition_id), None)
    if definition is None:
        return True
    real_kind = ("drink" if ObjectInteraction.DRINK in definition.interactions
                 else "food")
    return (known.identity != (definition.food_id or definition.definition_id)
            or known.kind != real_kind)


class ObjectAwareness:
    def __init__(self, saved: ObjectMemorySnapshot | None = None) -> None:
        self.perception = ObjectPerception()
        self._absence = ObjectAbsencePerception()
        self._absences: dict[str, ObjectKnowledge] = {}
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

    @property
    def absences(self) -> tuple[ObjectKnowledge, ...]:
        """Confirmed sensory facts waiting for the application to acknowledge."""
        return tuple(self._absences.values())

    @property
    def checking_absence(self) -> bool:
        return self._absence.checking

    def acknowledge_absence(self, record: str) -> None:
        self._absences.pop(record, None)

    def record_for_instance(self, instance: str) -> str | None:
        return self._world_records.get(instance)

    def instance_for_record(self, record: str) -> str | None:
        return next((instance for instance, key in self._world_records.items()
                     if key == record), None)

    def known_instance(self, instance: str) -> ObjectKnowledge | None:
        record = self.record_for_instance(instance)
        return self.memory.get(record) if record is not None else None

    def follow_taken(self, instance: str, record: str) -> bool:
        """Only an actual observed acquisition can extend visual continuity."""
        return (self.record_for_instance(instance) == record
                and any(seen.token == record for seen in self.observations)
                and self._tracker.follow_taken(instance))

    def assess_offer(self, token: str, state: PetState) -> ObjectUseDecision | None:
        """Use learned identity only with current subjective visibility."""
        known = self.memory.get(token)
        if known is None or not known.recognized or not any(
            seen.token == token and seen.presented for seen in self.observations
        ):
            return None
        decision = self.intentions.assess_offer(known, state)
        if decision.reason in ("unrecognized", "unavailable"):
            return None
        self.memory.mark_assessed(token)
        return decision

    def update(
        self, world: WorldSnapshot, state: PetState, *, now: float,
        x: float, height: float, width: float, attentive: bool, blocked: bool,
        held_pose: tuple[float, float] | None = None,
        committed: str | None = None,
        presentation: tuple[str, ItemPresentation] | None = None,
        inspecting: str | None = None,
    ) -> ObjectGoal | None:
        definitions = {item.definition_id: item for item in world.definitions}
        focused_instance = (self.instance_for_record(committed)
                            if committed is not None else None)
        focused_memory = self.memory.get(committed) if committed is not None else None
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
                inspecting=record is not None and record == inspecting
                and item.state == ObjectState.PET_HELD,
                presentation=presentation[1] if presentation is not None
                and presentation[0] == item.instance_id
                and item.state == ObjectState.USER_HELD else None,
            ))
        # Occupancy can disprove emptiness without noticing an unrelated subject.
        occupants = tuple(item for item in candidates if attentive and math.hypot(
            item.x - x, item.height - height,
        ) <= width * BALANCE.number("object_behavior", "notice_widths"))
        if committed is not None:
            # Filter before tracking, recognition and stock reconciliation.
            candidates = [item for item in candidates if (
                item.token == focused_instance
                or own_actions.get(item.token) == committed
                or focused_instance is None and focused_memory is not None
                and math.hypot(item.x - focused_memory.x,
                               item.height - focused_memory.height)
                <= width * BALANCE.number("object_behavior", "memory_place_widths")
            )]
        following = self._tracker.following_instance
        visible = tuple(item for item in candidates if attentive and (
            item.token == following or math.hypot(item.x - x, item.height - height)
            <= width * BALANCE.number("object_behavior", "notice_widths")
        ))
        tracked = self._tracker.update(
            visible, now=now, maximum_distance=width * BALANCE.number(
                "object_behavior", "tracking_jump_widths",
            ),
        )
        sensed = self.perception.observe(
            tracked, now=now, x=x, height=height,
            width=width, attentive=attentive,
            following=next((item.token for item in tracked
                            if self._tracker.resolve(item.token)
                            == self._tracker.following_instance), None),
        )
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
                preserve_record=old is not None and (
                    old == committed or instance == following
                ),
            )
            claimed.add(record)
            records[seen.token] = record
            if instance is not None:
                world_records[instance] = record
                if seen.resting:
                    held.pop(instance, None)
            observations.append(replace(seen, token=record))
            if instance is not None:
                item = next(item for item in world.objects
                            if item.instance_id == instance)
                if item.state == ObjectState.USER_HELD:
                    self._tracker.follow_taken(instance)
                elif item.state == ObjectState.RESTING and instance == following:
                    self._tracker.stop_following()
        self._sighting_records, self._world_records = records, world_records
        self._owned_records = held
        self.observations = tuple(observations)
        for record in self._absence.observe(
            self.memory.snapshot(), occupants, now=now, x=x, height=height,
            width=width, attentive=attentive, ground_bounds=(0, world.surface.width),
            focused=committed,
        ):
            known = self.memory.get(record)
            self.memory.mark_missing(record)
            if known is not None:
                self._absences[record] = known
        self._absences = {key: item for key, item in self._absences.items()
                          if (entry := self.memory.get(key)) is not None
                          and entry.place_status == "missing"}
        current = {(item.token, item.identity, item.x, item.height, item.resting,
                    item.assessed, item.disposition, item.place_status)
                   for item in self.memory.snapshot()}
        changed = previous != current or self._world_revision != world.revision
        self._world_revision = world.revision
        return self.intentions.choose(self.memory.snapshot(), state, x=x,
                                      now=now, blocked=blocked or self.checking_absence
                                      or bool(self.absences), changed=changed,
                                      committed=committed,
                                      observed=frozenset(item.token
                                                         for item in observations))
