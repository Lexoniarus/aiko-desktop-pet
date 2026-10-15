"""Single owner of in-memory World instances and explicit custody changes."""

from __future__ import annotations

from dataclasses import replace
from enum import StrEnum
from threading import get_ident
from typing import Iterable

from .contracts import (
    ObjectDefinition,
    ObjectFootprint,
    ObjectInteraction,
    ObjectState,
    WorldObjectSnapshot,
    WorldPosition,
    WorldSnapshot,
    WorldSurface,
)


class WorldFailure(StrEnum):
    UNKNOWN_DEFINITION = "unknown_definition"
    UNKNOWN_INSTANCE = "unknown_instance"
    STALE_REVISION = "stale_revision"
    INVALID_TRANSITION = "invalid_transition"
    OUT_OF_BOUNDS = "out_of_bounds"
    CURSOR_OCCUPIED = "cursor_occupied"
    PET_OCCUPIED = "pet_occupied"
    NOT_EDIBLE = "not_edible"


class WorldOperationError(ValueError):
    """Language-neutral failure; rejected operations leave the World unchanged."""

    def __init__(self, reason: WorldFailure) -> None:
        super().__init__(reason.value)
        self.reason = reason


class WorldState:
    """Own instances on one thread; distribute immutable snapshots to readers.

    Named acquisition methods record already authorized handover/collection.
    Perception, reach, appetite and pet nutrition are application responsibilities.
    Consuming here changes only World custody; it is not an eating use case.
    """

    def __init__(
        self, surface: WorldSurface, definitions: Iterable[ObjectDefinition],
    ) -> None:
        catalog: dict[str, ObjectDefinition] = {}
        for definition in definitions:
            if definition.definition_id in catalog:
                raise ValueError("Duplicate object definition")
            catalog[definition.definition_id] = definition
        self._surface = surface
        self._definitions = catalog
        self._objects: dict[str, WorldObjectSnapshot] = {}
        self._revision = 0
        self._next_id = 1
        self._owner_thread = get_ident()

    def _require_owner(self) -> None:
        if get_ident() != self._owner_thread:
            raise RuntimeError("World access requires the owner thread")

    def snapshot(self) -> WorldSnapshot:
        self._require_owner()
        return WorldSnapshot(
            self._surface, self._revision, tuple(self._definitions.values()),
            tuple(self._objects.values()),
        )

    def get(self, instance_id: str) -> WorldObjectSnapshot:
        self._require_owner()
        try:
            return self._objects[instance_id]
        except KeyError:
            raise WorldOperationError(WorldFailure.UNKNOWN_INSTANCE) from None

    def create_held(
        self, definition_id: str, position: WorldPosition,
        footprint: ObjectFootprint,
    ) -> WorldObjectSnapshot:
        """Create one cursor-carried portion, without any feeding effect."""
        return self._create(definition_id, position, footprint, ObjectState.USER_HELD)

    def place_resting(
        self, definition_id: str, x: float, footprint: ObjectFootprint,
    ) -> WorldObjectSnapshot:
        """Explicit scripted ground placement, without inventing a mouse gesture."""
        return self._create(
            definition_id, WorldPosition(x, 0), footprint, ObjectState.RESTING,
        )

    def _create(
        self, definition_id: str, position: WorldPosition,
        footprint: ObjectFootprint, state: ObjectState,
    ) -> WorldObjectSnapshot:
        self._require_owner()
        if definition_id not in self._definitions:
            raise WorldOperationError(WorldFailure.UNKNOWN_DEFINITION)
        self._validate_position(position, footprint)
        if state == ObjectState.USER_HELD:
            self._require_free(ObjectState.USER_HELD, WorldFailure.CURSOR_OCCUPIED)
        instance_id = f"object_{self._next_id}"
        item = WorldObjectSnapshot(
            instance_id, definition_id, 0, state, position, footprint,
        )
        self._objects[instance_id] = item
        self._next_id += 1
        self._revision += 1
        return item

    def move_held(
        self, instance_id: str, position: WorldPosition, *, expected_revision: int,
    ) -> WorldObjectSnapshot:
        item = self._expect(instance_id, expected_revision, ObjectState.USER_HELD)
        self._validate_position(position, item.footprint)
        return self._commit(item, item.state, position)

    def move_resting(
        self, instance_id: str, x: float, *, expected_revision: int,
    ) -> WorldObjectSnapshot:
        """Explicit World relocation; observers do not automatically learn it."""
        item = self._expect(instance_id, expected_revision, ObjectState.RESTING)
        position = WorldPosition(x, 0)
        self._validate_position(position, item.footprint)
        return self._commit(item, item.state, position)

    def release(
        self, instance_id: str, *, expected_revision: int,
    ) -> WorldObjectSnapshot:
        """Unaccepted release starts falling; physics is a later stage."""
        item = self._expect(instance_id, expected_revision, ObjectState.USER_HELD)
        return self._commit(item, ObjectState.FALLING, item.position)

    def land(
        self, instance_id: str, *, expected_revision: int,
    ) -> WorldObjectSnapshot:
        """Record scripted ground contact, preserving the horizontal anchor."""
        item = self._expect(instance_id, expected_revision, ObjectState.FALLING)
        if item.position is None:
            raise AssertionError("Falling objects require a position")
        position = WorldPosition(item.position.x, 0)
        self._validate_position(position, item.footprint)
        return self._commit(item, ObjectState.RESTING, position)

    def accept_handover_on_release(
        self, instance_id: str, *, expected_revision: int,
    ) -> WorldObjectSnapshot:
        """Apply a handover authorized by the future release interaction."""
        item = self._expect(instance_id, expected_revision, ObjectState.USER_HELD)
        return self._acquire(item)

    def collect_resting(
        self, instance_id: str, *, expected_revision: int,
    ) -> WorldObjectSnapshot:
        item = self._expect(instance_id, expected_revision, ObjectState.RESTING)
        return self._acquire(item)

    def _acquire(self, item: WorldObjectSnapshot) -> WorldObjectSnapshot:
        self._require_free(ObjectState.PET_HELD, WorldFailure.PET_OCCUPIED)
        return self._commit(item, ObjectState.PET_HELD, None)

    def consume(
        self, instance_id: str, *, expected_revision: int,
    ) -> WorldObjectSnapshot:
        """World-only consumption record; no nutrition, care or UI side effects."""
        item = self._expect(instance_id, expected_revision, ObjectState.PET_HELD)
        definition = self._definitions[item.definition_id]
        if ObjectInteraction.EAT not in definition.interactions:
            raise WorldOperationError(WorldFailure.NOT_EDIBLE)
        return self._commit(item, ObjectState.CONSUMED, None)

    def remove(
        self, instance_id: str, *, expected_revision: int,
    ) -> WorldObjectSnapshot:
        item = self._expect(
            instance_id, expected_revision, ObjectState.USER_HELD,
            ObjectState.FALLING, ObjectState.RESTING,
        )
        return self._commit(item, ObjectState.REMOVED, None)

    def _expect(
        self, instance_id: str, revision: int, *allowed: ObjectState,
    ) -> WorldObjectSnapshot:
        item = self.get(instance_id)
        if type(revision) is not int or item.revision != revision:
            raise WorldOperationError(WorldFailure.STALE_REVISION)
        if item.state not in allowed:
            raise WorldOperationError(WorldFailure.INVALID_TRANSITION)
        return item

    def _require_free(self, state: ObjectState, reason: WorldFailure) -> None:
        if any(item.state == state for item in self._objects.values()):
            raise WorldOperationError(reason)

    def _validate_position(
        self, position: WorldPosition, footprint: ObjectFootprint,
    ) -> None:
        if not self._surface.contains(position, footprint):
            raise WorldOperationError(WorldFailure.OUT_OF_BOUNDS)

    def _commit(
        self, item: WorldObjectSnapshot, state: ObjectState,
        position: WorldPosition | None,
    ) -> WorldObjectSnapshot:
        if item.state == state and item.position == position:
            return item
        updated = replace(item, revision=item.revision + 1, state=state,
                          position=position)
        self._objects[item.instance_id] = updated
        self._revision += 1
        return updated
