"""Commit confirmed physical custody and subjective own-action facts together."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from ..pet.mind.object_memory import ObjectMemory
from ..world.state import WorldState


class ObjectCustody:
    def __init__(self, world: WorldState, memory: ObjectMemory) -> None:
        self._world, self._memory = world, memory

    @contextmanager
    def _change(self) -> Iterator[None]:
        world, memory = self._world.snapshot(), self._memory.snapshot()
        try:
            yield
        except Exception:
            self._world.restore_snapshot(world)
            self._memory.restore_snapshot(memory)
            raise

    def accept_handover_on_release(
        self, token: str, *, memory_id: str, expected_revision: int, now: float,
    ) -> None:
        with self._change():
            self._world.accept_handover_on_release(
                token, expected_revision=expected_revision,
            )
            self._memory.note_acquired(memory_id, now=now)

    def collect_resting(
        self, token: str, *, memory_id: str, expected_revision: int, now: float,
    ) -> None:
        with self._change():
            self._world.collect_resting(token, expected_revision=expected_revision)
            self._memory.note_acquired(memory_id, now=now)

    def put_down(
        self, token: str, x: float, *, memory_id: str,
        expected_revision: int, now: float,
        deferred: bool,
    ) -> None:
        with self._change():
            placed = self._world.put_down(token, x, expected_revision=expected_revision)
            assert placed.position is not None
            self._memory.note_placement(
                memory_id, x=placed.position.x, height=placed.position.height,
                now=now, deferred=deferred,
            )
