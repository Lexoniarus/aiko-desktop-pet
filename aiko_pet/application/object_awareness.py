"""Bridge objective World values into subjective pet observations and goals."""

from __future__ import annotations

import math
from dataclasses import replace
from typing import Literal

from ..pet.balance import BALANCE
from ..pet.mind.object_absence import ObjectAbsencePerception
from ..pet.mind.object_attention import KnownPlaceCoverage, ObjectAttention
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

TargetEvidence = Literal["observed", "unresolved", "unseen", "forgotten"]


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
        self.checking_notice = False
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

    def target_evidence(self, record: str, *, radius: float) -> TargetEvidence:
        """Separate executable association from knowledge and local occupancy.

        Pending candidates cannot establish loss or ambiguity. Only completed
        subjective observations can show that this place now has other records.
        """
        known = self.memory.get(record)
        if known is None:
            return "forgotten"
        if self.instance_for_record(record) is not None:
            return "observed"
        if any(math.hypot(seen.x - known.x, seen.height - known.height) <= radius
               for seen in self.observations):
            return "unresolved"
        return "unseen"

    @property
    def following_cursor(self) -> bool:
        return self._tracker.following_instance is not None

    @property
    def following_record(self) -> str | None:
        instance = self._tracker.following_instance
        return self.record_for_instance(instance) if instance is not None else None

    def follow_taken(
        self, instance: str, record: str, *, now: float, attention: ObjectAttention,
        committed: str | None = None,
    ) -> bool:
        """Only an actual observed acquisition can extend visual continuity."""
        known = self.memory.get(record)
        if (attention.mode == "object" and record != committed
                or known is None or not attention.sees(known.x, known.height)
                or self.record_for_instance(instance) != record
                or not any(seen.token == record for seen in self.observations)
                or not self._tracker.follow_taken(instance)):
            return False
        # The witnessed take is already custody evidence. Do not wait for a
        # held-frame sample: a whole cursor gesture can occur between ticks.
        self.memory.note_acquired(record, now=now)
        return True

    def witness_take(
        self, instance: str, *, position: tuple[float, float], now: float,
        attention: ObjectAttention, committed: str | None = None,
    ) -> str | None:
        """Use a successful observed take at a learned place between sensor ticks."""
        record = self.record_for_instance(instance)
        known = (self.memory.get(record) if record is not None
                 else self.memory.learned_instance(instance))
        if (known is None
                or attention.mode == "object" and known.token != committed):
            return None
        continuing = self._tracker.following_instance == instance
        if (not known.at_place(x=position[0], height=position[1], resting=True)
                and not continuing):
            return None
        if not (attention.sees(*position) or continuing
                and attention.mode in ("cursor", "object")):
            return None
        if record is not None and self.follow_taken(
            instance, record, now=now, attention=attention, committed=committed,
        ):
            return record
        if continuing:
            self.memory.note_acquired(known.token, now=now)
            return known.token
        if not known.recognized or known.instance_id != instance:
            return None
        assert known.identity is not None and known.kind is not None
        tracked = self._tracker.witness_take(ObjectCandidate(
            instance, known.identity, known.kind, *position, False,
        ), now=now)
        self.perception.notice_acquisition(tracked.token)
        self._sighting_records[tracked.token] = known.token
        self._world_records[instance] = known.token
        self.observations = tuple(item for item in self.observations
                                  if item.token != known.token) + (ObjectObservation(
            known.token, None, None, *position, False, now,
        ),)
        self.memory.note_acquired(known.token, now=now)
        return known.token

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

    def _collect_candidates(
        self, world: WorldSnapshot, *,
        held_pose: tuple[float, float] | None,
        presentation: tuple[str, ItemPresentation] | None,
        inspecting: str | None,
    ) -> tuple[list[ObjectCandidate], dict[str, str], dict[str, str]]:
        """Prepare objective sensing inputs without changing subjective memory."""
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
                inspecting=record is not None and record == inspecting
                and item.state == ObjectState.PET_HELD,
                presentation=presentation[1] if presentation is not None
                and presentation[0] == item.instance_id
                and item.state == ObjectState.USER_HELD else None,
            ))
        return candidates, own_actions, held

    def _focused_candidates(
        self, candidates: tuple[ObjectCandidate, ...], *, committed: str | None,
        own_actions: dict[str, str],
    ) -> tuple[ObjectCandidate, ...]:
        """A focused place is a target check, not permission to discover neighbours."""
        subject = self.memory.get(committed) if committed is not None else None
        result = []
        for item in candidates:
            if item.token in own_actions and not item.resting:
                result.append(item)
                continue
            if subject is None:
                continue
            at_place = subject.at_place(x=item.x, height=item.height,
                                        resting=item.resting)
            bound = self._world_records.get(item.token) == committed
            if (bound and (not subject.resting or not item.resting or at_place)
                    or subject.instance_id == item.token and at_place):
                result.append(item)
        return tuple(result)

    def update(
        self, world: WorldSnapshot, state: PetState, *, now: float,
        x: float, height: float, width: float,
        attention: ObjectAttention, blocked: bool,
        held_pose: tuple[float, float] | None = None,
        committed: str | None = None,
        presentation: tuple[str, ItemPresentation] | None = None,
        inspecting: str | None = None,
        known_coverage: KnownPlaceCoverage | None = None,
    ) -> ObjectGoal | None:
        candidates, own_actions, held = self._collect_candidates(
            world, held_pose=held_pose, presentation=presentation,
            inspecting=inspecting,
        )
        checked = tuple(item for item in self.memory.snapshot()
                        if known_coverage is not None and item.recognized
                        and item.resting and item.place_status == "remembered"
                        and known_coverage.contains(
                            item.x, attention=attention,
                            ground_bounds=(0, world.surface.width),
                        ))
        place_radius = width * BALANCE.number("object_behavior", "memory_place_widths")
        recalled = frozenset(item.token for item in candidates
                             if (known := self.memory.learned_instance(item.token))
                             is not None and known in checked and known.at_place(
                                 x=item.x, height=item.height, resting=item.resting,
                             ))
        # Distant occupancy is evidence about a checked learned place only.
        occupants = tuple(item for item in candidates
                          if attention.sees(item.x, item.height) or any(
                              math.hypot(item.x - place.x, item.height - place.height)
                              <= place_radius for place in checked
                          ))
        following = self._tracker.following_instance
        following_subject = (following is not None and committed is not None
                             and self._world_records.get(following) == committed)
        visible = tuple(item for item in candidates if (
            attention.sees(item.x, item.height)
            or item.token in recalled
            or attention.mode != "unavailable" and item.token in own_actions
            and (not item.resting or own_actions[item.token] == committed)
            or item.token == following and (attention.mode == "cursor"
                                            or attention.mode == "object"
                                            and following_subject)
        ))
        if attention.mode == "object":
            visible = self._focused_candidates(visible, committed=committed,
                                                own_actions=own_actions)
        tracked = self._tracker.update(
            visible, now=now, maximum_distance=width * BALANCE.number(
                "object_behavior", "tracking_jump_widths",
            ),
            learned=frozenset(item.token for item in visible
                              if (known := self.memory.learned_instance(item.token))
                              is not None and known.at_place(
                                  x=item.x, height=item.height, resting=item.resting,
                              )),
        )
        sensed = self.perception.observe(tracked, now=now)
        self.checking_notice = len(sensed) < len(tracked)
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
                instance_id=instance,
            )
            claimed.add(record)
            records[seen.token] = record
            if instance is not None:
                world_records[instance] = record
                if seen.resting and record != committed:
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
        previous_tokens = {entry[0] for entry in previous}
        self.memory.retire_ambiguous_sightings(
            self.observations, maximum_distance=width * BALANCE.number(
                "object_behavior", "memory_place_widths",
            ),
            new_records=frozenset(seen.token for seen in self.observations
                                  if seen.token not in previous_tokens),
        )
        places = tuple(item for item in self.memory.snapshot()
                       if attention.mode != "object" or item.token == committed)
        for record in self._absence.observe(
            places, occupants, now=now, attention=attention,
            ground_bounds=(0, world.surface.width),
            known_coverage=known_coverage,
            identified={instance: known for instance, record in world_records.items()
                        if (known := self.memory.get(record)) is not None
                        and known.recognized},
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
        if committed is None and (self.checking_absence or self.absences):
            # Finish the current visible place evidence before any free wish,
            # including a continuing offer wish. Keep the wish owner intact.
            return None
        return self.intentions.choose(self.memory.snapshot(), state, x=x,
                                      now=now, blocked=blocked or self.checking_absence
                                      or bool(self.absences), changed=changed,
                                      committed=committed,
                                      observed=frozenset(item.token
                                                         for item in observations))
