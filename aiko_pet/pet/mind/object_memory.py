"""Subjective object knowledge; authoritative World changes are never polled."""

from __future__ import annotations

from dataclasses import replace

from ..balance import BALANCE
from .object_perception import ObjectObservation


class ObjectMemory:
    def __init__(self) -> None:
        self._known: dict[str, ObjectObservation] = {}

    def update(
        self, observations: tuple[ObjectObservation, ...], *, now: float,
    ) -> None:
        self._known = {
            token: item for token, item in self._known.items()
            if now - item.observed_at <= BALANCE.number(
                "object_behavior", "memory_seconds",
            )
        }
        for observation in observations:
            previous = self._known.get(observation.token)
            if previous is not None:
                observation = replace(observation, examined=(observation.examined or (
                    previous.examined and observation.x == previous.x
                    and observation.height == previous.height
                    and observation.resting == previous.resting
                )))
            if previous is not None and observation.identity is None:
                observation = replace(observation, identity=previous.identity,
                                      kind=previous.kind)
            self._known[observation.token] = observation

    def get(self, token: str) -> ObjectObservation | None:
        return self._known.get(token)

    def mark_examined(self, token: str) -> None:
        known = self._known.get(token)
        if known is not None:
            self._known[token] = replace(known, examined=True)

    def forget(self, token: str) -> None:
        """Explicit observed absence or failed local interaction invalidates it."""
        self._known.pop(token, None)

    def snapshot(self) -> tuple[ObjectObservation, ...]:
        return tuple(self._known.values())
