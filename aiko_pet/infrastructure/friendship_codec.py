"""Strict version-one relationship histories on the aggregate's elapsed axis."""

from __future__ import annotations

import math
from typing import Any, cast

from ..pet.balance import BALANCE
from ..pet.catalog_validation import object_fields
from ..pet.friendship import (
    CARE_FRIENDSHIP_GAIN,
    PENALTY_KINDS,
    REWARD_KINDS,
    penalty_budget,
)
from ..pet.friendship_history import (
    CriticalBucket,
    FriendshipHistory,
    NeedDurations,
    RelationshipEvent,
)


def _number(raw: Any, maximum: float) -> float:
    if type(raw) not in (int, float):
        raise ValueError("Relationship history requires finite numbers")
    try:
        valid = math.isfinite(raw) and 0 <= raw <= maximum
    except OverflowError:
        valid = False
    if not valid:
        raise ValueError("Relationship value outside elapsed axis")
    return float(raw)


def _events(
    raw: Any, elapsed: float, *, penalties: bool
) -> tuple[RelationshipEvent, ...]:
    # Include wishes carried into the window, not only newly created wishes.
    limit = 65 if penalties else (
        65 + math.ceil(BALANCE.number("friendship", "history_window_seconds")
                       / BALANCE.number("wishes", "creation_interval_seconds"))
        + BALANCE.integer("wishes", "maximum_active")
    )
    if not isinstance(raw, list) or len(raw) > limit:
        raise ValueError("Unbounded relationship event history")
    allowed = PENALTY_KINDS if penalties else REWARD_KINDS
    events = []
    previous = -1.0
    for value in raw:
        row = object_fields(
            value, ("at", "kind", "amount"), context="relationship event"
        )
        if not isinstance(row["kind"], str) or row["kind"] not in allowed:
            raise ValueError("Unknown relationship event")
        stamp = _number(row["at"], elapsed)
        amount = _number(row["amount"], 100)
        if stamp < previous or amount <= 0:
            raise ValueError("Unordered or empty relationship credit")
        events.append(RelationshipEvent(stamp, row["kind"], amount))
        previous = stamp
    for i, event in enumerate(events):
        if penalties:
            window, cap = penalty_budget(event.kind)
        else:
            window = BALANCE.number("friendship", "short_window_seconds")
            cap = BALANCE.number("friendship", "short_cap")
        used = sum(
            e.amount
            for e in events[: i + 1]
            if e.at > event.at - window and (not penalties or e.kind == event.kind)
        )
        if used > cap + 1e-8:
            raise ValueError("Relationship event budget exceeded")
    if (
        not penalties
        and sum(e.amount for e in events)
        > BALANCE.number(
            "friendship",
            "daily_cap",
        )
        + 1e-8
    ):
        raise ValueError("Relationship daily budget exceeded")
    return tuple(events)


def decode_friendship(raw: Any, elapsed: float) -> FriendshipHistory:
    row = object_fields(
        raw,
        (
            "version",
            "baseline",
            "last_contact",
            "rewards",
            "eligible",
            "critical",
            "penalties",
        ),
        context="relationship",
    )
    if type(row["version"]) is not int or row["version"] != 1:
        raise ValueError("Unsupported relationship version")
    baseline = None if row["baseline"] is None else _number(row["baseline"], elapsed)
    contact = (
        None if row["last_contact"] is None else _number(row["last_contact"], elapsed)
    )
    rewards = _events(row["rewards"], elapsed, penalties=False)
    penalties = _events(row["penalties"], elapsed, penalties=True)
    eligible = object_fields(
        row["eligible"],
        (),
        optional=CARE_FRIENDSHIP_GAIN,
        context="relationship eligibility",
    )
    anchors = tuple((a, _number(t, elapsed)) for a, t in eligible.items())
    size = BALANCE.number("friendship", "history_bucket_seconds")
    window = BALANCE.number("friendship", "history_window_seconds")
    if (
        not isinstance(row["critical"], list)
        or len(row["critical"]) > math.ceil(window / size) + 1
    ):
        raise ValueError("Unbounded critical need history")
    buckets = []
    previous = -1.0
    for value in row["critical"]:
        entry = object_fields(
            value, ("start", "critical", "zero", "width"), context="critical bucket"
        )
        start = _number(entry["start"], elapsed)
        if start <= previous or not math.isclose(
            start / size, round(start / size), abs_tol=1e-8
        ):
            raise ValueError("Unordered or unaligned critical bucket")
        width = _number(entry["width"], window + size)
        if width < size or not math.isclose(width / size, round(width / size)):
            raise ValueError("Invalid critical span width")
        if start < previous:
            raise ValueError("Overlapping critical spans")
        durations = []
        for key in ("critical", "zero"):
            numbers = entry[key]
            if not isinstance(numbers, list) or len(numbers) != 5:
                raise ValueError("Critical history must cover all five needs")
            durations.append(
                cast(NeedDurations, tuple(_number(v, width + 1e-7) for v in numbers))
            )
        if any(z > c + 1e-8 for c, z in zip(*durations)):
            raise ValueError("Zero duration exceeds critical duration")
        buckets.append(CriticalBucket(start, durations[0], durations[1], width))
        previous = start + width - 1e-7
    if baseline is None:
        if contact is not None or rewards or anchors or buckets or penalties:
            raise ValueError("Uninitialized relationship cannot claim history")
    elif (
        contact is not None
        and contact < baseline
        or any(e.at < baseline for e in (*rewards, *penalties))
        or any(t < baseline for _, t in anchors)
    ):
        raise ValueError("Relationship evidence precedes migration")
    return FriendshipHistory(
        baseline, contact, rewards, anchors, tuple(buckets), penalties
    )


def valid_friendship(raw: Any, elapsed: float) -> bool:
    try:
        decode_friendship(raw, elapsed)
    except (ValueError, TypeError, OverflowError):
        return False
    return True


def encode_friendship(history: FriendshipHistory) -> dict[str, Any]:
    def events(values: tuple[RelationshipEvent, ...]) -> list[dict[str, Any]]:
        return [dict(at=e.at, kind=e.kind, amount=e.amount) for e in values]

    return dict(
        version=1,
        baseline=history.baseline,
        last_contact=history.last_contact,
        rewards=events(history.rewards),
        eligible=dict(history.eligible),
        critical=[
            dict(
                start=b.start,
                critical=list(b.critical),
                zero=list(b.zero),
                width=b.width,
            )
            for b in history.critical
        ],
        penalties=events(history.penalties),
    )
