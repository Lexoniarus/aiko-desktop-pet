"""Pure consequences of perceived interactions; the aggregate commits them."""

from dataclasses import dataclass, replace
from typing import Mapping

from .interaction_events import (
    BoundaryCommunicated,
    InteractionEvent,
    Poked,
)
from .moodlets import (
    MoodletDefinition,
    MoodletId,
    MoodletState,
    PettingParameters,
    reinforce_moodlet,
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
