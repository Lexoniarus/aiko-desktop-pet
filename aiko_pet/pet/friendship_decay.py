"""Chronological passive relationship loss over the existing need integration."""

from __future__ import annotations

import math
from dataclasses import replace
from typing import cast

from .balance import BALANCE
from .friendship import prune_history
from .friendship_history import (
    CriticalBucket,
    FriendshipProgress,
    NeedDurations,
)
from .need_exposure import exposure_totals


def _setting(key: str) -> float:
    return BALANCE.number("friendship", key)


def friendship_factor(points: float) -> float:
    anchors = _anchors()
    for (x, factor), (end, final) in zip(anchors, anchors[1:]):
        if points <= end:
            return factor + (final - factor) * max(0.0, points - x) / (end - x)
    return anchors[-1][1]


def _anchors() -> tuple[tuple[float, float], ...]:
    return (
        (0.0, _setting("zero_factor")),
        *(
            (_setting(f"{name}_points"), _setting(f"{name}_factor"))
            for name in ("lower", "middle", "higher", "peak")
        ),
        (100.0, _setting("peak_factor")),
    )


def passive_friendship(points: float, reference_loss: float) -> float:
    """Solve the linear factor segments exactly, including level crossings."""
    if reference_loss <= 0 or points <= 0:
        return points
    anchors = _anchors()
    remaining = reference_loss
    while points > 1e-12 and remaining > 1e-12:
        index = max(i for i, (x, _) in enumerate(anchors[:-1]) if x < points)
        (low, factor), (high, final) = anchors[index : index + 2]
        slope = (final - factor) / (high - low)
        current = factor + slope * (points - low)
        needed = (
            math.log(current / factor) / slope if slope else (points - low) / factor
        )
        spend = min(needed, remaining)
        if spend >= needed:
            points = low
        elif slope:
            points = low + (current * math.exp(-slope * spend) - factor) / slope
        else:
            points -= factor * spend
        remaining -= spend
    return max(0.0, points)


def absence_rate(age: float) -> float:
    if age <= _setting("absence_grace_seconds"):
        return 0.0
    for boundary, rate in (
        ("middle", "first"),
        ("long", "middle"),
        ("extended", "long"),
    ):
        if age <= _setting(f"absence_{boundary}_seconds"):
            return _setting(f"absence_{rate}_rate")
    return _setting("absence_extended_rate")


def _append(
    buckets: tuple[CriticalBucket, ...],
    start: float,
    end: float,
    critical: tuple[bool, ...],
    zero: tuple[bool, ...],
) -> tuple[CriticalBucket, ...]:
    size = _setting("history_bucket_seconds")
    cutoff = end - _setting("history_window_seconds")
    kept = []
    for bucket in buckets:
        if bucket.start + bucket.width <= cutoff:
            continue
        trim = max(0.0, math.floor(cutoff / size) * size - bucket.start)
        fraction = (bucket.width - trim) / bucket.width
        kept.append(
            CriticalBucket(
                bucket.start + trim,
                cast(NeedDurations, tuple(v * fraction for v in bucket.critical)),
                cast(NeedDurations, tuple(v * fraction for v in bucket.zero)),
                bucket.width - trim,
            )
            if trim
            else bucket
        )
    if not any(critical):
        return tuple(kept)
    bucket_start = math.floor(start / size) * size
    previous = (
        kept.pop()
        if kept and kept[-1].start == bucket_start
        else CriticalBucket(bucket_start, width=size)
    )
    updated = CriticalBucket(
        bucket_start,
        cast(
            NeedDurations,
            tuple(previous.critical[i] + (end - start) * critical[i] for i in range(5)),
        ),
        cast(
            NeedDurations,
            tuple(previous.zero[i] + (end - start) * zero[i] for i in range(5)),
        ),
        size,
    )
    if kept:
        older = kept[-1]
        matching = all(
            (a == b == 0) or (abs(a - older.width) < 1e-7 and abs(b - size) < 1e-7)
            for first, last in (
                (older.critical, updated.critical),
                (older.zero, updated.zero),
            )
            for a, b in zip(first, last)
        )
        if matching and abs(older.start + older.width - bucket_start) < 1e-7:
            kept.pop()
            updated = CriticalBucket(
                older.start,
                cast(
                    NeedDurations,
                    tuple(a + b for a, b in zip(older.critical, updated.critical)),
                ),
                cast(
                    NeedDurations,
                    tuple(a + b for a, b in zip(older.zero, updated.zero)),
                ),
                older.width + size,
            )
    return (*kept, updated)


def advance_friendship(
    progress: FriendshipProgress,
    seconds: float,
    before: tuple[float, ...],
    after: tuple[float, ...],
    *,
    sleeping: bool,
) -> FriendshipProgress:
    """Integrate a numeric need step; no clocks, aggregate writes or extra ticks."""
    start, history = progress.elapsed, progress.history
    if seconds <= 0:
        return progress
    if history.baseline is None:
        return replace(progress, elapsed=start + seconds)
    contact = (
        history.last_contact if history.last_contact is not None else history.baseline
    )
    if not history.critical and all(
        min(a, b) >= _setting("critical_need") or i == 1 and sleeping and b > a
        for i, (a, b) in enumerate(zip(before, after))
    ):
        # Absence is the sole rate. Its reference integral can be solved in one
        # pass without allocating a minute grid for healthy long intervals.
        age_boundaries = [
            0.0,
            *(
                _setting(f"absence_{key}_seconds")
                for key in ("grace", "middle", "long", "extended")
            ),
        ]
        ages = (start - contact, start + seconds - contact)
        reference = 0.0
        for low, high in zip(age_boundaries, age_boundaries[1:] + [float("inf")]):
            duration = max(0.0, min(ages[1], high) - max(ages[0], low))
            if duration:
                reference += (
                    duration / 3600 * absence_rate(max(ages[0], low) + duration / 2)
                )
        return FriendshipProgress(
            passive_friendship(progress.points, reference),
            prune_history(history, start + seconds),
            start + seconds,
        )
    size = _setting("history_bucket_seconds")
    cuts = {0.0, seconds}
    cursor = (math.floor(start / size) + 1) * size
    while cursor < start + seconds:
        cuts.add(cursor - start)
        cursor += size
    for key in ("grace", "middle", "long", "extended"):
        offset = contact + _setting(f"absence_{key}_seconds") - start
        if 0 < offset < seconds:
            cuts.add(offset)
    for a, b in zip(before, after):
        if a != b:
            offset = (_setting("critical_need") - a) / (b - a) * seconds
            if 0 < offset < seconds:
                cuts.add(offset)
    points, buckets = progress.points, history.critical
    ordered = sorted(cuts)
    for left, right in zip(ordered, ordered[1:]):
        fraction = (left + right) / (2 * seconds)
        critical = tuple(
            a + (b - a) * fraction < _setting("critical_need")
            and not (i == 1 and sleeping and b > a)
            for i, (a, b) in enumerate(zip(before, after))
        )
        zero = tuple(
            a == b == 0 and critical[i] for i, (a, b) in enumerate(zip(before, after))
        )
        initial = exposure_totals(buckets, start + left)
        buckets = _append(buckets, start + left, start + right, critical, zero)
        final = exposure_totals(buckets, start + right)
        boundaries = {0.0, 1.0}
        for kind, (first, last) in enumerate(zip(initial, final)):
            for i, (a, b) in enumerate(zip(first, last)):
                if b == a:
                    continue
                thresholds = (
                    (_setting("zero_allowance_seconds"),)
                    if kind == 1
                    else (
                        _setting("critical_allowance_seconds"),
                        _setting("strong_neglect_seconds"),
                    )
                )
                for threshold in thresholds:
                    part = (threshold - a) / (b - a)
                    if 0 < part < 1 and critical[i]:
                        boundaries.add(part)
        subdivisions = sorted(boundaries)
        for low, high in zip(subdivisions, subdivisions[1:]):
            middle = (low + high) / 2
            elapsed = start + left + (right - left) * middle
            neglect = 0.0
            for i, active in enumerate(critical):
                if not active:
                    continue
                duration = initial[0][i] + (final[0][i] - initial[0][i]) * middle
                zero_duration = initial[1][i] + (final[1][i] - initial[1][i]) * middle
                eligible = (
                    duration >= _setting("critical_allowance_seconds")
                    or zero[i]
                    and zero_duration >= _setting("zero_allowance_seconds")
                )
                if eligible:
                    strong = duration >= _setting("strong_neglect_seconds")
                    key = ("strong_" if strong else "") + (
                        "zero" if zero[i] else "critical"
                    )
                    neglect = max(neglect, _setting(f"{key}_loss_rate"))
            reference = max(absence_rate(elapsed - contact), neglect)
            points = passive_friendship(
                points, reference * (right - left) * (high - low) / 3600
            )
    return FriendshipProgress(
        points,
        prune_history(replace(history, critical=buckets), start + seconds),
        start + seconds,
    )
