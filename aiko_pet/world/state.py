"""Single owner of in-memory World instances and explicit custody changes."""

from __future__ import annotations

import math
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
from .motion import ItemMotion, MotionParameters, advance_motion


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
            self._next_id,
        )

    def get(self, instance_id: str) -> WorldObjectSnapshot:
        self._require_owner()
        try:
            return self._objects[instance_id]
        except KeyError:
            raise WorldOperationError(WorldFailure.UNKNOWN_INSTANCE) from None

    def restore_snapshot(self, snapshot: WorldSnapshot) -> None:
        """Owner-controlled recovery from a validated session/checkpoint."""
        self._require_owner()
        if tuple(self._definitions.values()) != snapshot.definitions:
            raise ValueError("World recovery requires the same definitions")
        objects: dict[str, WorldObjectSnapshot] = {}
        for item in snapshot.objects:
            if (item.instance_id in objects
                    or item.definition_id not in self._definitions):
                raise ValueError("Invalid restored instance identity")
            if ((item.state in (ObjectState.FALLING, ObjectState.BOUNCING))
                    != (item.motion is not None)):
                raise ValueError("Restored motion must match object state")
            if item.position is not None and not snapshot.surface.contains(
                item.position, item.footprint,
            ):
                raise ValueError("Invalid restored position")
            objects[item.instance_id] = item
        self._surface = snapshot.surface
        self._objects = objects
        self._revision = snapshot.revision
        self._next_id = max(self._next_id, snapshot.next_instance_id, 1 + max(
            (int(key.removeprefix("object_")) for key in objects), default=0,
        ))

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
        if state == ObjectState.RESTING:
            position = WorldPosition(self._surface.ground_x(position.x, footprint), 0)
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
        position = WorldPosition(self._surface.ground_x(x, item.footprint), 0)
        return self._commit(item, item.state, position)

    def release(
        self, instance_id: str, *, expected_revision: int,
    ) -> WorldObjectSnapshot:
        """Unaccepted release starts one continuous motion lifecycle."""
        item = self._expect(instance_id, expected_revision, ObjectState.USER_HELD)
        return self._commit(item, ObjectState.FALLING, item.position)

    def land(
        self, instance_id: str, *, expected_revision: int,
    ) -> WorldObjectSnapshot:
        """Record scripted final contact on reachable ground."""
        item = self._expect(instance_id, expected_revision, ObjectState.FALLING,
                            ObjectState.BOUNCING)
        if item.position is None:
            raise AssertionError("Falling objects require a position")
        position = WorldPosition(self._surface.ground_x(
            item.position.x, item.footprint), 0)
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

    def take_resting(
        self, instance_id: str, *, expected_revision: int,
    ) -> WorldObjectSnapshot:
        """Acquire the same settled portion for a new player gesture."""
        item = self._expect(instance_id, expected_revision, ObjectState.RESTING)
        self._require_free(ObjectState.USER_HELD, WorldFailure.CURSOR_OCCUPIED)
        return self._commit(item, ObjectState.USER_HELD, item.position)

    def return_user_held(
        self, instance_id: str, x: float, *, expected_revision: int,
    ) -> WorldObjectSnapshot:
        """Cancel relocation to its safe starting place, without cognition effects."""
        item = self._expect(instance_id, expected_revision, ObjectState.USER_HELD)
        position = WorldPosition(self._surface.ground_x(x, item.footprint), 0)
        return self._commit(item, ObjectState.RESTING, position)

    def _acquire(self, item: WorldObjectSnapshot) -> WorldObjectSnapshot:
        self._require_free(ObjectState.PET_HELD, WorldFailure.PET_OCCUPIED)
        return self._commit(item, ObjectState.PET_HELD, None)

    def consume(
        self, instance_id: str, *, expected_revision: int,
    ) -> WorldObjectSnapshot:
        """World-only consumption record; no nutrition, care or UI side effects."""
        item = self._expect(instance_id, expected_revision, ObjectState.PET_HELD)
        definition = self._definitions[item.definition_id]
        if not definition.interactions.intersection((
            ObjectInteraction.EAT, ObjectInteraction.DRINK,
        )):
            raise WorldOperationError(WorldFailure.NOT_EDIBLE)
        return self._commit(item, ObjectState.CONSUMED, None)

    def put_down(
        self, instance_id: str, x: float, *, expected_revision: int,
    ) -> WorldObjectSnapshot:
        """Return an acquired item at the confirmed reverse-animation event."""
        item = self._expect(instance_id, expected_revision, ObjectState.PET_HELD)
        position = WorldPosition(x, 0)
        self._validate_position(position, item.footprint)
        position = WorldPosition(self._surface.ground_x(x, item.footprint), 0)
        return self._commit(item, ObjectState.RESTING, position)

    def change_surface(
        self, surface: WorldSurface, *, recovering: bool = False,
    ) -> None:
        """Reproject active anchors atomically; reject shapes that cannot fit."""
        self._require_owner()
        if surface == self._surface:
            return
        replacements: list[tuple[WorldObjectSnapshot, WorldPosition,
                                 ObjectState, ItemMotion | None]] = []
        for item in self._objects.values():
            if item.state not in (ObjectState.CONSUMED, ObjectState.REMOVED):
                self._validate_footprint(surface, item.footprint)
            if item.position is not None:
                x = max(item.footprint.left, min(
                        item.position.x, surface.width - item.footprint.right,
                    ))
                state, motion = item.state, item.motion
                if item.state == ObjectState.RESTING:
                    ground_x = surface.ground_x(x, item.footprint)
                    if recovering:
                        x = ground_x
                    elif x != ground_x:
                        state, motion = ObjectState.BOUNCING, ItemMotion(settling=True)
                replacements.append((item, WorldPosition(
                    x, min(item.position.height, surface.height),
                ), state, motion))
        self._surface = surface
        self._revision += 1
        for item, position, state, motion in replacements:
            self._commit(item, state, position, motion=motion)

    def advance_motion(self, elapsed: float, parameters: MotionParameters) -> None:
        """Advance all flying/bouncing portions; only final contact grants rest."""
        self._require_owner()
        if not math.isfinite(elapsed) or elapsed < 0:
            raise ValueError("Invalid motion time")
        if elapsed == 0:
            return
        updates: list[tuple[WorldObjectSnapshot, ObjectState,
                            WorldPosition, ItemMotion | None]] = []
        for item in tuple(self._objects.values()):
            if (item.state not in (ObjectState.FALLING, ObjectState.BOUNCING)
                    or item.position is None or item.motion is None):
                continue
            result = advance_motion(
                item.position.x, item.position.height, item.motion, elapsed,
                self._surface.ground_interval(item.footprint), parameters,
                ceiling=self._surface.height,
            )
            state: ObjectState = (
                ObjectState.RESTING if result.motion is None else
                ObjectState.BOUNCING if result.contacted else item.state
            )
            updates.append((item, state, WorldPosition(result.x, result.height),
                            result.motion))
        for item, state, position, motion in updates:
            self._commit(item, state, position, motion=motion)

    def change_footprint(
        self, instance_id: str, footprint: ObjectFootprint, *, expected_revision: int,
    ) -> None:
        item = self._expect(
            instance_id, expected_revision, ObjectState.USER_HELD,
            ObjectState.FALLING, ObjectState.BOUNCING, ObjectState.RESTING,
            ObjectState.PET_HELD,
        )
        self._validate_footprint(self._surface, footprint)
        if item.footprint == footprint:
            return
        position = item.position
        state, motion = item.state, item.motion
        if position is not None:
            position = WorldPosition(max(footprint.left, min(
                position.x, self._surface.width - footprint.right,
            )), position.height)
            if item.state == ObjectState.RESTING:
                ground_x = self._surface.ground_x(position.x, footprint)
                if ground_x != position.x:
                    state, motion = ObjectState.BOUNCING, ItemMotion(settling=True)
        self._objects[instance_id] = replace(
            item, footprint=footprint, position=position, state=state, motion=motion,
            revision=item.revision + 1,
        )
        self._revision += 1

    def remove(
        self, instance_id: str, *, expected_revision: int,
    ) -> WorldObjectSnapshot:
        item = self._expect(
            instance_id, expected_revision, ObjectState.USER_HELD,
            ObjectState.FALLING, ObjectState.BOUNCING, ObjectState.RESTING,
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
        self._validate_footprint(self._surface, footprint)

    @staticmethod
    def _validate_footprint(surface: WorldSurface, footprint: ObjectFootprint) -> None:
        try:
            surface.ground_interval(footprint)
        except ValueError:
            raise WorldOperationError(WorldFailure.OUT_OF_BOUNDS) from None

    def _commit(
        self, item: WorldObjectSnapshot, state: ObjectState,
        position: WorldPosition | None,
        *, motion: ItemMotion | None = None,
    ) -> WorldObjectSnapshot:
        moving = state in (ObjectState.FALLING, ObjectState.BOUNCING)
        motion = (motion or item.motion or ItemMotion()) if moving else None
        if item.state == state and item.position == position and item.motion == motion:
            return item
        updated = replace(item, revision=item.revision + 1, state=state,
                          position=position,
                          motion=motion)
        self._objects[item.instance_id] = updated
        self._revision += 1
        return updated
