"""Read-only object counts; actual World stock and subjective knowledge differ."""

from dataclasses import dataclass

from ..pet.mind.object_knowledge import ObjectKnowledge
from ..world.contracts import ObjectState, WorldSnapshot


@dataclass(frozen=True, slots=True)
class ObjectStatusSnapshot:
    desktop: int = 0
    known: int = 0
    assigned: int = 0
    missing: int = 0


def snapshot_object_status(
    world: WorldSnapshot, memory: tuple[ObjectKnowledge, ...],
) -> ObjectStatusSnapshot:
    """Count learned portions, never catalog types or historical witnesses.

    Assignment describes Aiko's remembered place/custody without ambiguity.
    Reading diagnostics must not check hidden places or identify unknown items.
    """
    known = tuple(item for item in memory
                  if item.recognized and item.place_status != "superseded")
    return ObjectStatusSnapshot(
        desktop=sum(item.state == ObjectState.RESTING for item in world.objects),
        known=len(known),
        assigned=sum(item.place_status == "remembered" and not item.possible_sources
                     for item in known),
        missing=sum(item.place_status == "missing" for item in known),
    )
