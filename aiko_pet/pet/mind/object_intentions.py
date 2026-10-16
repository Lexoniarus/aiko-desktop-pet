"""Stable need-driven goals selected from subjective knowledge only."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from ..balance import BALANCE
from ..food import is_repeated_food
from ..state import PetState
from .object_decisions import decide_object_use
from .object_knowledge import ObjectKnowledge
from .object_perception import ConsumableKind


@dataclass(frozen=True, slots=True)
class ObjectGoal:
    token: str
    identity: str | None
    kind: ConsumableKind | None
    x: float
    height: float
    observed_at: float
    purpose: Literal["investigate", "consume"] = "consume"


class ObjectIntentions:
    def __init__(self) -> None:
        self.goal: ObjectGoal | None = None
        self._next_check = 0.0
        self._retry: dict[str, float] = {}
        self._pause_until = 0.0

    def cancel(self, now: float, *, consumed: bool = False) -> None:
        if self.goal is not None:
            self._retry[self.goal.token] = now + BALANCE.number(
                "object_behavior", "retry_seconds",
            )
        self.goal = None
        self._next_check = 0
        if consumed:
            self._pause_until = now + BALANCE.number(
                "object_behavior", "consumed_pause_seconds",
            )

    def choose(
        self, known: tuple[ObjectKnowledge, ...], state: PetState, *,
        x: float, now: float, blocked: bool = False, changed: bool = False,
        observed: frozenset[str] = frozenset(),
    ) -> ObjectGoal | None:
        if state.sleeping or blocked:
            self.cancel(now)
            return None
        if not changed and now < self._next_check:
            return self.goal
        self._next_check = now + BALANCE.number("object_behavior", "reevaluate_seconds")
        available = {item.token for item in known if item.token in observed
                     and item.resting and item.place_status == "remembered"
                     and decide_object_use(item, state).consume}
        options: list[tuple[tuple[bool, float, bool, float, str], ObjectGoal]] = []
        for item in known:
            if not item.resting or item.place_status != "remembered":
                continue
            # Rest after consumption limits renewed supply seeking. Curiosity
            # about a different, unexamined portion remains an independent goal.
            if item.assessed and now < self._pause_until:
                continue
            wanted = decide_object_use(item, state).consume
            if item.assessed and not wanted:
                continue
            threshold = BALANCE.number(
                "object_behavior",
                "seek_food_satiety" if item.kind == "food" else "seek_drink_energy",
            )
            level = state.satiety if item.kind == "food" else state.energy
            if now < self._retry.get(item.token, 0):
                continue
            goal = ObjectGoal(item.token, item.identity, item.kind,
                              item.x, item.height, item.observed_at,
                              "consume" if item.assessed else "investigate")
            if (self.goal is not None and item.token == self.goal.token
                    and (not available or item.token in available)):
                self.goal = goal
                return goal
            repetitive = (item.identity is not None and item.kind == "food"
                          and is_repeated_food(state.food, item.identity))
            rank = (item.token not in available,
                    -(threshold - level) / threshold if wanted else 0, repetitive,
                    abs(item.x - x), item.token)
            options.append((rank, goal))
        self.goal = min(options, key=lambda option: option[0])[1] if options else None
        return self.goal
