"""Subjective object knowledge; authoritative World changes are never polled."""

from __future__ import annotations

from dataclasses import replace

from ..balance import BALANCE
from .object_knowledge import (
    ObjectKnowledge,
    ObjectMemorySnapshot,
    SavedObjectKnowledge,
)
from .object_perception import ObjectObservation


class ObjectMemory:
    def __init__(
        self, saved: ObjectMemorySnapshot | None = None, *, now: float = 0,
    ) -> None:
        self._known: dict[str, ObjectKnowledge] = {}
        if saved is not None:
            self.restore_snapshot(tuple(ObjectKnowledge(
                item.token, item.identity, item.kind, item.x, item.height,
                item.resting, now - item.age_seconds, item.assessed, item.disposition,
            ) for item in saved.entries))

    @staticmethod
    def _retained(item: ObjectKnowledge, now: float) -> bool:
        return item.recognized or now - item.observed_at <= BALANCE.number(
            "object_behavior", "memory_seconds",
        )

    def update(
        self, observations: tuple[ObjectObservation, ...], *, now: float,
    ) -> None:
        self._known = {
            token: item for token, item in self._known.items()
            if self._retained(item, now)
        }
        for observation in observations:
            previous = self._known.get(observation.token)
            compatible = previous is not None and (
                observation.identity is None or (
                    observation.identity == previous.identity
                    and observation.kind == previous.kind
                )
            )
            self._known[observation.token] = ObjectKnowledge(
                observation.token,
                previous.identity if compatible and observation.identity is None
                and previous is not None else observation.identity,
                previous.kind if compatible and observation.identity is None
                and previous is not None else observation.kind,
                observation.x, observation.height, observation.resting,
                observation.observed_at,
                previous.assessed if compatible and previous is not None else False,
                previous.disposition if compatible and previous is not None else None,
            )

    def get(self, token: str) -> ObjectKnowledge | None:
        return self._known.get(token)

    def mark_assessed(self, token: str) -> None:
        known = self._known.get(token)
        if known is not None and known.recognized:
            self._known[token] = replace(known, assessed=True)

    def note_placement(
        self, token: str, *, x: float, height: float, now: float, deferred: bool,
    ) -> None:
        """Learn only a confirmed own placement, including interrupted actions."""
        known = self._known.get(token)
        if known is not None:
            self._known[token] = replace(
                known, x=x, height=height, resting=True, observed_at=now,
                disposition="deferred" if deferred and known.assessed
                else "interrupted",
            )

    def note_acquired(self, token: str, *, now: float) -> None:
        known = self._known.get(token)
        if known is not None:
            self._known[token] = replace(known, resting=False, observed_at=now,
                                         disposition=None)

    def forget(self, token: str) -> None:
        """Explicit observed absence or failed local interaction invalidates it."""
        self._known.pop(token, None)

    def snapshot(self) -> tuple[ObjectKnowledge, ...]:
        return tuple(self._known.values())

    def restore_snapshot(self, known: tuple[ObjectKnowledge, ...]) -> None:
        """Restore the owner's immutable checkpoint, without consulting World."""
        self._known = {item.token: item for item in known}

    def export(self, *, now: float) -> ObjectMemorySnapshot:
        return ObjectMemorySnapshot(tuple(SavedObjectKnowledge(
            item.token, item.identity, item.kind, item.x, item.height, item.resting,
            max(0, now - item.observed_at), item.assessed, item.disposition,
        ) for item in self._known.values() if self._retained(item, now)))
