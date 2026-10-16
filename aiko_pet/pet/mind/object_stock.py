"""Pure subjective place matching and bounded stock uncertainty."""

from __future__ import annotations

import math
from dataclasses import dataclass

from .object_knowledge import ObjectKnowledge
from .object_perception import ObjectObservation


@dataclass(frozen=True, slots=True)
class FindMatch:
    record: str | None
    possible_sources: tuple[str, ...] = ()


def match_find(
    records: tuple[ObjectKnowledge, ...], seen: ObjectObservation, *,
    claimed: frozenset[str], maximum_distance: float,
) -> FindMatch:
    """Only perceived type/place support a reunion, never an instance handle."""
    compatible = [item for item in records if item.token not in claimed
                  and item.place_status != "superseded"
                  and item.recognized and (seen.identity is None or (
                      item.identity == seen.identity and item.kind == seen.kind))]
    local = [item for item in compatible if item.resting == seen.resting
             and (seen.identity is not None or item.place_status != "missing")
             and math.hypot(item.x - seen.x, item.height - seen.height)
             <= maximum_distance]
    if len(local) == 1:
        return FindMatch(local[0].token)
    return FindMatch(None, tuple(sorted(item.token for item in compatible
                                       if seen.identity is not None)))


def _matching_size(edges: dict[str, tuple[str, ...]]) -> int:
    owners: dict[str, str] = {}

    def assign(token: str, visited: set[str]) -> bool:
        for source in edges[token]:
            if source in visited:
                continue
            visited.add(source)
            if source not in owners or assign(owners[source], visited):
                owners[source] = token
                return True
        return False

    return sum(assign(token, set()) for token in edges)


@dataclass(frozen=True, slots=True)
class StockSummary:
    available_minimum: int
    available_maximum: int
    missing_minimum: int
    missing_maximum: int


def summarize_stock(records: tuple[ObjectKnowledge, ...]) -> StockSummary:
    """A possible reunion explains at most one other place/portion."""
    available = {item.token: item for item in records
                 if item.place_status == "remembered" and item.resting}
    missing = {item.token for item in records if item.place_status == "missing"}
    finds = {item.token: item for item in records if item.possible_sources
             and (item.token in available or item.place_status == "superseded")}
    active_links = {token: tuple(source for source in item.possible_sources
                                 if source in available)
                    for token, item in finds.items()}
    missing_links = {token: tuple(source for source in item.possible_sources
                                  if source in missing)
                     for token, item in finds.items()}
    return StockSummary(
        len(available) - _matching_size(active_links), len(available),
        len(missing) - _matching_size(missing_links), len(missing),
    )


def resolved_places(records: tuple[ObjectKnowledge, ...]) -> frozenset[str]:
    """Retire a checked group only when distinct finds can explain every place."""
    by_token = {item.token: item for item in records}
    edges = {item.token: item.possible_sources for item in records
             if item.possible_sources}
    adjacent: dict[str, set[str]] = {}
    for token, sources in edges.items():
        for source in sources:
            adjacent.setdefault(token, set()).add(source)
            adjacent.setdefault(source, set()).add(token)
    visited: set[str] = set()
    resolved: set[str] = set()
    for token in adjacent:
        if token in visited:
            continue
        group: set[str] = set()
        pending = [token]
        while pending:
            current = pending.pop()
            if current in group:
                continue
            group.add(current)
            pending.extend(adjacent[current] - group)
        visited.update(group)
        relations = {key: value for key, value in edges.items() if key in group}
        places = {source for values in relations.values() for source in values}
        if (all(by_token[source].place_status == "missing" for source in places)
                and _matching_size(relations) == len(places)):
            resolved.update(places)
    return frozenset(resolved)
