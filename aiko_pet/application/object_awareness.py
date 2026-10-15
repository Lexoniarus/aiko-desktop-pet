"""Bridge objective World values into subjective pet observations and goals."""

from __future__ import annotations

from ..pet.mind.object_intentions import ObjectGoal, ObjectIntentions
from ..pet.mind.object_knowledge import ObjectMemorySnapshot
from ..pet.mind.object_memory import ObjectMemory
from ..pet.mind.object_perception import (
    ObjectCandidate,
    ObjectObservation,
    ObjectPerception,
)
from ..pet.state import PetState
from ..world.contracts import ObjectInteraction, ObjectState, WorldSnapshot


class ObjectAwareness:
    def __init__(self, saved: ObjectMemorySnapshot | None = None) -> None:
        self.perception = ObjectPerception()
        self.memory = ObjectMemory(saved)
        self.intentions = ObjectIntentions()
        self.observations: tuple[ObjectObservation, ...] = ()
        self._world_revision = -1

    def update(
        self, world: WorldSnapshot, state: PetState, *, now: float,
        x: float, height: float, width: float, attentive: bool, blocked: bool,
        held_pose: tuple[float, float] | None = None,
    ) -> ObjectGoal | None:
        definitions = {item.definition_id: item for item in world.definitions}
        candidates: list[ObjectCandidate] = []
        for item in world.objects:
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
        observations = self.perception.observe(
            tuple(candidates), now=now, x=x, height=height,
            width=width, attentive=attentive,
        )
        self.observations = observations
        previous = {(item.token, item.identity, item.x, item.height, item.resting,
                     item.examined, item.disposition)
                    for item in self.memory.snapshot()}
        self.memory.update(observations, now=now)
        current = {(item.token, item.identity, item.x, item.height, item.resting,
                    item.examined, item.disposition)
                   for item in self.memory.snapshot()}
        changed = previous != current or self._world_revision != world.revision
        self._world_revision = world.revision
        return self.intentions.choose(self.memory.snapshot(), state, x=x,
                                      now=now, blocked=blocked, changed=changed)
