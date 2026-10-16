"""Stable need-driven goals selected from subjective knowledge only."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

from ..balance import BALANCE
from ..food import is_repeated_food
from ..state import PetState
from .object_decisions import ObjectUseContext, ObjectUseDecision, decide_object_use
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
    use_context: ObjectUseContext = ObjectUseContext.SUPPLY


class ObjectIntentions:
    def __init__(self) -> None:
        self.goal: ObjectGoal | None = None
        self._next_check = 0.0
        self._retry: dict[str, float] = {}
        self._pause_until = 0.0

    def assess_offer(
        self, known: ObjectKnowledge, state: PetState,
    ) -> ObjectUseDecision:
        """A visible offer can create a wish without starting a theft episode."""
        decision = decide_object_use(known, state, ObjectUseContext.OFFER)
        if decision.consume:
            self.goal = ObjectGoal(
                known.token, known.identity, known.kind, known.x, known.height,
                known.observed_at, "consume", ObjectUseContext.CONTINUING_WISH,
            )
        elif (self.goal is not None and self.goal.token == known.token
              and self.goal.use_context == ObjectUseContext.CONTINUING_WISH):
            self.goal = None
        return decision

    def cancel(self, now: float, *, consumed: bool = False) -> None:
        self.complete(self.goal.token if self.goal is not None else None,
                      now, consumed=consumed)

    def complete(
        self, token: str | None, now: float, *, consumed: bool = False,
    ) -> None:
        """Finish the named attempt without cancelling a newer selected goal."""
        if token is not None:
            self._retry[token] = now + BALANCE.number(
                "object_behavior", "retry_seconds",
            )
        if self.goal is not None and self.goal.token == token:
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
        committed: str | None = None,
    ) -> ObjectGoal | None:
        if committed is not None and not state.sleeping:
            if self.goal is None or self.goal.token != committed:
                return None
            subject = next((item for item in known if item.token == committed), None)
            if subject is not None:
                self.goal = replace(
                    self.goal, identity=subject.identity, kind=subject.kind,
                    x=subject.x, height=subject.height,
                    observed_at=subject.observed_at,
                )
            return self.goal
        if self.goal is not None and not state.sleeping:
            subject = next((item for item in known
                            if item.token == self.goal.token), None)
            if (self.goal.use_context == ObjectUseContext.CONTINUING_WISH
                    and subject is not None and subject.place_status == "remembered"
                    and (subject.resting or subject.token in observed)
                    and subject.identity == self.goal.identity
                    and subject.kind == self.goal.kind
                    and decide_object_use(subject, state,
                                          self.goal.use_context).consume):
                self.goal = replace(
                    self.goal, x=subject.x, height=subject.height,
                    observed_at=subject.observed_at,
                )
                return self.goal
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
