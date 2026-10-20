"""Pure consequences of perceived interactions; the aggregate commits them."""

from dataclasses import dataclass, replace
from typing import Mapping

from .balance import BALANCE
from .interaction_events import (
    BoundaryCommunicated,
    FoodConsumed,
    FoodRepetitionMemory,
    InteractionEvent,
    Poked,
)
from .moodlets import (
    FoodMonotonyParameters,
    MoodletDefinition,
    MoodletId,
    MoodletState,
    PettingParameters,
    reinforce_moodlet,
    relieve_moodlet,
)


@dataclass(frozen=True, slots=True)
class InteractionConsequences:
    moodlets: MoodletState
    refused: bool = False
    penalty_kind: str = ""
    penalty_points: float = 0.0


def apply_interaction_event(
    state: MoodletState, event: InteractionEvent, *, elapsed: float,
    definitions: Mapping[MoodletId, MoodletDefinition],
) -> InteractionConsequences:
    memory = state.interactions
    if isinstance(event, BoundaryCommunicated):
        if event.kind == "poking":
            memory = replace(memory, poke_boundary_at=elapsed)
        elif event.kind == "petting":
            memory = replace(memory, petting_boundary_at=elapsed)
        elif event.kind == "food_variety":
            if not memory.food.request_pending:
                return InteractionConsequences(state)
            memory = replace(memory, food=replace(
                memory.food, request_pending=False, requested_at=elapsed,
                ignored_portions=0,
            ))
        else:
            raise ValueError("Unknown interaction boundary")
        return InteractionConsequences(replace(state, interactions=memory))
    if isinstance(event, Poked):
        if not event.continuing_burst:
            return InteractionConsequences(replace(
                state, interactions=replace(memory, poke_boundary_at=None),
            ))
        if memory.poke_boundary_at is not None:
            state = reinforce_moodlet(state, MoodletId.POKING, elapsed=elapsed,
                                      definitions=definitions)
        return InteractionConsequences(state)
    if isinstance(event, FoodConsumed):
        return _consume_food(state, event, elapsed=elapsed, definitions=definitions)
    parameters = definitions[MoodletId.CROWDED].parameters
    assert isinstance(parameters, PettingParameters)
    threshold = next(t.affection_threshold for t in parameters.tolerances
                     if event.friendship_level <= t.maximum_friendship_level)
    refusing = elapsed < memory.petting_refused_until
    if not refusing and event.affection < threshold:
        return InteractionConsequences(state)
    warned = (memory.petting_boundary_at is not None
              and elapsed - memory.petting_boundary_at
              <= parameters.boundary_window_seconds)
    if not refusing and not warned:
        return InteractionConsequences(state, refused=True)
    state = reinforce_moodlet(state, MoodletId.CROWDED, elapsed=elapsed,
                              definitions=definitions)
    episode = next(e for e in state.active if e.definition_id == MoodletId.CROWDED)
    memory = replace(memory, petting_refused_until=(
        elapsed + parameters.refusal_seconds[episode.level - 1]
    ))
    return InteractionConsequences(replace(state, interactions=memory), True,
                                   "petting", parameters.friendship_loss_points)


def _consume_food(
    state: MoodletState, event: FoodConsumed, *, elapsed: float,
    definitions: Mapping[MoodletId, MoodletDefinition],
) -> InteractionConsequences:
    parameters = definitions[MoodletId.FOOD_MONOTONY].parameters
    assert isinstance(parameters, FoodMonotonyParameters)
    memory = state.interactions.food
    if event.food_id == "energy_drink":
        return InteractionConsequences(state)
    same = event.food_id == memory.food_id
    episode = next((e for e in state.active
                    if e.definition_id == MoodletId.FOOD_MONOTONY), None)
    if not same:
        if episode is not None:
            state = relieve_moodlet(state, episode.instance_id, elapsed=elapsed,
                                   definitions=definitions)
        memory = FoodRepetitionMemory(food_id=event.food_id)
    count = BALANCE.integer("food", "consecutive_repeats_before_dislike") + 1
    intakes = tuple(t for t in memory.intakes
                    if elapsed - t <= parameters.sequence_window_seconds)
    memory = replace(memory, intakes=(*intakes, elapsed)[-count:])
    requested = (memory.requested_at is not None
                 and elapsed - memory.requested_at
                 < parameters.request_lifetime_seconds)
    penalty = 0.0
    if same and requested and event.personal:
        ignored = min(memory.ignored_portions + 1, parameters.free_ignored_portions + 1)
        memory = replace(memory, ignored_portions=ignored)
        if ignored > parameters.free_ignored_portions:
            penalty = parameters.friendship_loss_points
    if len(memory.intakes) == count:
        if episode is None and not requested:
            memory = replace(memory, request_pending=True, requested_at=None,
                             ignored_portions=0)
        state = reinforce_moodlet(state, MoodletId.FOOD_MONOTONY, elapsed=elapsed,
                                  definitions=definitions)
    state = replace(state, interactions=replace(state.interactions, food=memory))
    return InteractionConsequences(
        state, penalty_kind="food_variety" if penalty else "", penalty_points=penalty,
    )
