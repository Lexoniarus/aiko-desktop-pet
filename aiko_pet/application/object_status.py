"""Read-only object counts; actual World stock and subjective knowledge differ."""

from collections import Counter
from dataclasses import dataclass

from ..pet.mind.object_knowledge import ObjectKnowledge
from ..world.contracts import ObjectState, WorldSnapshot


@dataclass(frozen=True, slots=True)
class ObjectStatusSnapshot:
    desktop: int = 0
    known: int = 0
    assigned: int = 0
    missing: int = 0
    undiscovered: int = 0
    unidentified: int = 0
    unresolved: int = 0


def snapshot_object_status(
    world: WorldSnapshot, memory: tuple[ObjectKnowledge, ...], *,
    observed_bindings: tuple[tuple[str, str], ...] = (),
) -> ObjectStatusSnapshot:
    """Count learned portions, never catalog types or historical witnesses.

    Assignment describes Aiko's remembered place/custody without ambiguity.
    Reading diagnostics must not check hidden places or identify unknown items.
    """
    known = tuple(item for item in memory
                  if item.recognized and item.place_status != "superseded")
    retained = {item.token: item for item in memory
                if item.place_status != "superseded"}
    desktop = {item.instance_id for item in world.objects
               if item.state == ObjectState.RESTING}
    # Only acquired identity bindings or the existing tracker associate a record
    # with actual stock. Proximity and World food types are not discovery evidence.
    links: dict[str, set[str]] = {}
    for instance, record in (
        *((item.instance_id, item.token) for item in retained.values()
          if item.instance_id is not None),
        *observed_bindings,
    ):
        if instance in desktop and record in retained:
            links.setdefault(instance, set()).add(record)
    uses = Counter(record for records in links.values() for record in records)
    associated = {instance for instance, records in links.items()
                  if len(records) == 1 and uses[next(iter(records))] == 1}
    bound_records = {record for instance in associated for record in links[instance]}
    unbound = any(item.instance_id is None and item.token not in bound_records
                  for item in retained.values())
    unmatched = desktop - associated
    # Old unknown/ambiguous sightings may belong to unmatched current stock.
    # Report uncertainty explicitly rather than asserting "never discovered".
    unresolved = unmatched if unbound else unmatched.intersection(links)
    return ObjectStatusSnapshot(
        desktop=len(desktop),
        undiscovered=len(unmatched - unresolved),
        unidentified=sum(not item.recognized for item in retained.values()),
        unresolved=len(unresolved),
        known=len(known),
        assigned=sum(item.place_status == "remembered" and not item.possible_sources
                     for item in known),
        missing=sum(item.place_status == "missing" for item in known),
    )
