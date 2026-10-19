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
from .object_stock import FindMatch, match_find, resolved_places


class ObjectMemory:
    def __init__(
        self, saved: ObjectMemorySnapshot | None = None, *, now: float = 0,
    ) -> None:
        self._known: dict[str, ObjectKnowledge] = {}
        self._next_id = saved.next_record_id if saved is not None else 1
        if saved is not None:
            self.restore_snapshot(tuple(ObjectKnowledge(
                item.token, item.identity, item.kind, item.x, item.height,
                item.resting, now - item.age_seconds, item.assessed, item.disposition,
                item.place_status, item.possible_sources, item.instance_id,
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
                "remembered",
                (previous.possible_sources
                 if compatible and previous is not None else ()),
                previous.instance_id if compatible and previous is not None else None,
            )

    def observe_find(
        self, seen: ObjectObservation, *, now: float, record: str | None,
        claimed: frozenset[str], maximum_distance: float,
        preserve_record: bool = False,
        instance_id: str | None = None,
    ) -> str:
        """Recall learned portions at their place; identify new ones by hand/face."""
        learned = self.learned_instance(instance_id) if instance_id else None
        reunion = None
        supported = learned is not None and (
            seen.identity is not None or learned.at_place(
                x=seen.x, height=seen.height, resting=seen.resting,
            )
        )
        if supported and learned is not None:
            if (preserve_record and record is not None and record != learned.token
                    and self.get(record) is not None):
                reunion = learned
            else:
                record = learned.token
        elif (learned is not None and record == learned.token
              and learned.resting and seen.resting):
            record = None
        previous = self.get(record) if record is not None else None
        if (previous is not None and previous.instance_id is not None
                and instance_id is not None and previous.instance_id != instance_id):
            record, previous = None, None
        match = None
        if reunion is None and (
            previous is None or not previous.recognized and seen.identity is not None
        ):
            match = match_find(
                tuple(item for item in self.snapshot() if item.token != record),
                seen, claimed=claimed, maximum_distance=maximum_distance,
                instance_id=instance_id,
            )
            if preserve_record and previous is not None and match.record is not None:
                # Focus hides neighbouring evidence. A possible reunion cannot
                # replace the continuously watched subject with another record.
                match = FindMatch(None, (match.record,))
            if match.record is not None:
                if previous is not None:
                    self.forget(previous.token)
                record = match.record
            elif previous is None:
                record = f"memory_{self._next_id}"
                self._next_id += 1
        assert record is not None
        self.update((replace(seen, token=record),), now=now)
        if seen.identity is not None and instance_id is not None:
            self._known[record] = replace(self._known[record], instance_id=instance_id)
        if reunion is not None:
            current = self._known[record]
            if current.identity is None or (
                current.identity, current.kind
            ) == (reunion.identity, reunion.kind):
                self._known[record] = replace(
                    current, identity=reunion.identity, kind=reunion.kind,
                    assessed=reunion.assessed, disposition=reunion.disposition,
                    instance_id=reunion.instance_id,
                )
            self.forget(reunion.token)
        if match is not None and match.record is None:
            sources = match.possible_sources
            # A newly examined portion matching exactly one already confirmed
            # missing known type is the supported reunion, not new stock.
            # Never borrow experience for an unidentified find or ambiguous
            # competing old portions.
            eligible = tuple(
                item for token in sources
                if (item := self.get(token)) is not None
                and item.place_status == "missing"
                and item.identity == seen.identity and item.kind == seen.kind
            )
            source = eligible[0] if (
                seen.identity is not None and len(sources) == 1
                and len(eligible) == 1
            ) else None
            current = self._known[record]
            self._known[record] = replace(
                current, possible_sources=sources,
                assessed=source.assessed if source is not None else current.assessed,
                disposition=(source.disposition if source is not None
                             else current.disposition),
            )
        visible = claimed | {record}
        for key, item in tuple(self._known.items()):
            if item.token in visible or item.place_status == "superseded":
                self._known[key] = replace(item, possible_sources=tuple(
                    source for source in item.possible_sources if source not in visible
                ))
        self._reconcile_sources()
        return record

    def get(self, token: str) -> ObjectKnowledge | None:
        return self._known.get(token)

    def reunite_search(
        self, subject: ObjectKnowledge, found_token: str,
    ) -> ObjectKnowledge:
        """Commit one search-authorized subjective reunion, retaining found facts.

        Ordinary recognition still uses observe_find/match_find. Only an active
        search coordinator may transfer history between different physical items.
        The retired subject may already have been reconciled by place evidence.
        """
        found = self.get(found_token)
        if (found is None or not found.recognized
                or found.place_status == "superseded"
                or (found.identity, found.kind) != (subject.identity, subject.kind)):
            raise ValueError("Search reunion requires an identified matching find")
        if found.token == subject.token:
            return found
        self.forget(subject.token)
        reunited = replace(
            found, assessed=found.assessed or subject.assessed,
            disposition=subject.disposition or found.disposition,
            possible_sources=(),
        )
        self._known[found.token] = reunited
        return reunited

    def learned_instance(self, instance: str) -> ObjectKnowledge | None:
        """Read durable learning; this alone proves neither visibility nor reunion."""
        return next((item for item in self._known.values()
                     if item.instance_id == instance and item.recognized
                     and item.place_status != "superseded"), None)

    def retire_ambiguous_sightings(
        self, observations: tuple[ObjectObservation, ...], *, maximum_distance: float,
        new_records: frozenset[str],
    ) -> None:
        """Drop unbound unknown places superseded by completed local sightings.

        Forgetting a fleeting appearance claims neither identification nor an
        empty place. Learned records and currently observed subjects survive.
        """
        import math

        observed = {seen.token for seen in observations}
        for item in self.snapshot():
            if (not item.recognized and item.resting and item.token not in observed
                    and any(seen.token in new_records and seen.resting and math.hypot(
                        seen.x - item.x, seen.height - item.height,
                    ) <= maximum_distance for seen in observations)):
                self.forget(item.token)

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
        for key, item in tuple(self._known.items()):
            if token in item.possible_sources:
                self._known[key] = replace(
                    item, possible_sources=tuple(source for source
                                                  in item.possible_sources
                                                  if source != token),
                )

    def mark_missing(self, token: str) -> None:
        known = self.get(token)
        if known is None:
            return
        self._known[token] = replace(known, place_status="missing")
        self._reconcile_sources()

    def _reconcile_sources(self) -> None:
        # A unique same-type find may precede the confirmation that its old
        # location is missing, or follow it. Both orders preserve the
        # already learned assessment without manufacturing another portion.
        for item in tuple(self._known.values()):
            if (item.place_status != "remembered" or not item.recognized
                    or len(item.possible_sources) != 1):
                continue
            source = self.get(item.possible_sources[0])
            if (source is not None and source.place_status == "missing"
                    and source.identity == item.identity
                    and source.kind == item.kind):
                self._known[item.token] = replace(
                    item, assessed=item.assessed or source.assessed,
                    disposition=item.disposition or source.disposition,
                )
        for token in resolved_places(self.snapshot()):
            self.forget(token)
        for item in tuple(self._known.values()):
            if item.place_status == "superseded" and not item.possible_sources:
                self.forget(item.token)

    def record_consumption(self, token: str) -> None:
        known = self.get(token)
        if known is not None and len(known.possible_sources) == 1:
            self.forget(known.possible_sources[0])
        elif known is not None and known.possible_sources:
            # Keep one consumed-find witness while its former place is ambiguous.
            # It cannot become stock or a reunion candidate again.
            self._known[token] = replace(known, resting=False, disposition=None,
                                          place_status="superseded")
            self._reconcile_sources()
            return
        self.forget(token)

    def snapshot(self) -> tuple[ObjectKnowledge, ...]:
        return tuple(self._known.values())

    def restore_snapshot(self, known: tuple[ObjectKnowledge, ...]) -> None:
        """Restore the owner's immutable checkpoint, without consulting World."""
        self._known = {item.token: item for item in known}
        self._next_id = max(self._next_id, 1 + max((
            int(item.token.removeprefix("memory_")) for item in known
            if item.token.startswith("memory_")
        ), default=0))

    def export(self, *, now: float) -> ObjectMemorySnapshot:
        return ObjectMemorySnapshot(tuple(SavedObjectKnowledge(
            item.token, item.identity, item.kind, item.x, item.height, item.resting,
            max(0, now - item.observed_at), item.assessed, item.disposition,
            item.place_status, item.possible_sources, item.instance_id,
        ) for item in self._known.values() if self._retained(item, now)),
                                    self._next_id)
