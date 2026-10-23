"""Chronological emotional balance and passive loss in existing need progression."""

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
from .moodlet_catalog import MOODLET_CATALOG
from .moodlets import MoodletGroup, MoodletPolarity, MoodletState
from .need_exposure import exposure_totals


def _setting(key: str) -> float:
    return BALANCE.number("friendship", key)


def friendship_factor(points: float) -> float:
    anchors = _anchors()
    for (x, factor), (end, final) in zip(anchors, anchors[1:]):
        if points <= end:
            return factor + (final - factor) * max(0.0, points - x) / (end - x)
    return anchors[-1][1]


def _anchors(*, positive: bool = False) -> tuple[tuple[float, float], ...]:
    prefix = "positive_" if positive else ""
    return (
        (0.0, _setting(f"{prefix}zero_factor")),
        *(
            (_setting(f"{name}_points"), _setting(f"{prefix}{name}_factor"))
            for name in ("lower", "middle", "higher", "peak")
        ),
        (100.0, _setting(f"{prefix}peak_factor")),
    )


def passive_friendship(points: float, reference_loss: float) -> float:
    """Reference-only projection using the same progressive balance solver."""
    return balance_friendship(points, positive=0, negative=max(0, reference_loss))


def balance_friendship(points: float, *, positive: float, negative: float) -> float:
    """Integrate simultaneous contributions exactly through linear factor segments."""
    if not all(math.isfinite(v) for v in (points, positive, negative)) or (
        not 0 <= points <= 100 or min(positive, negative) < 0
    ):
        raise ValueError("Invalid relationship balance")
    if positive == negative == 0 or points == 0 and positive == 0 or (
        points == 100 and negative == 0
    ):
        return points
    gains, losses = _anchors(positive=True), _anchors()
    remaining = 1.0
    while remaining > 1e-12:
        # Both factor functions are continuous at anchors.
        index = min(len(gains) - 2, max(i for i, (x, _) in enumerate(gains)
                                       if x <= points))

        def coefficients(i: int) -> tuple[float, float]:
            (low, gain), (high, next_gain) = gains[i:i + 2]
            loss, next_loss = losses[i][1], losses[i + 1][1]
            slope = (positive * (next_gain - gain)
                     - negative * (next_loss - loss)) / (high - low)
            return slope, positive * gain - negative * loss - slope * low

        slope, intercept = coefficients(index)
        velocity = slope * points + intercept
        if abs(velocity) < 1e-14 or points == 100 and velocity > 0 or (
            points == 0 and velocity < 0
        ):
            break
        if velocity < 0 and points == gains[index][0] and index:
            index -= 1
            slope, intercept = coefficients(index)
            velocity = slope * points + intercept
        boundary = gains[index + (velocity > 0)][0]
        final_velocity = slope * boundary + intercept
        crossing = (math.log(final_velocity / velocity) / slope
                    if slope and final_velocity * velocity > 0 else
                    (boundary - points) / velocity if not slope else math.inf)
        spend = min(remaining, max(0, crossing))
        points = (boundary if crossing <= remaining else
                  points + velocity * math.expm1(slope * spend) / slope if slope else
                  points + velocity * spend)
        remaining -= spend
    return max(0.0, min(100.0, points))


def emotional_friendship_rates(
    before: float, after: float, moodlets: MoodletState, *, recent_contact: bool,
) -> tuple[float, float]:
    """Average raw amounts per status interval, without numeric-mood family caps."""
    thresholds = tuple(_setting(key) for key in (
        "mood_negative_floor", "mood_neutral_low", "mood_neutral_high",
        "mood_positive_ceiling",
    ))

    def baseline(mood: float) -> tuple[float, float]:
        low, neutral_low, neutral_high, high = thresholds
        return (
            _setting("mood_positive_rate") * max(0, min(1, (mood - neutral_high)
                                                       / (high - neutral_high)))
            if recent_contact else 0,
            _setting("mood_negative_rate") * max(0, min(1, (neutral_low - mood)
                                                       / (neutral_low - low))),
        )

    cuts = sorted({0.0, 1.0, *(max(0, min(1, (t - before) / (after - before)))
                              for t in thresholds)} if after != before else {0.0, 1.0})
    positive = negative = 0.0
    for left, right in zip(cuts, cuts[1:]):
        first, last = (baseline(before + (after - before) * at)
                       for at in (left, right))
        positive += (first[0] + last[0]) / 2 * (right - left)
        negative += (first[1] + last[1]) / 2 * (right - left)
    for episode in moodlets.active:
        definition = MOODLET_CATALOG.definitions[episode.definition_id]
        long_term = definition.group == MoodletGroup.LONG_TERM
        policy = MOODLET_CATALOG.long_term_policy
        if definition.polarity == MoodletPolarity.POSITIVE:
            positive += episode.level * (policy.positive_friendship_rate if long_term
                                         else _setting("positive_moodlet_rate"))
        else:
            negative += episode.level * (policy.negative_friendship_rate if long_term
                                         else _setting("negative_moodlet_rate"))
    return positive, negative


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
        if (matching and end >= bucket_start + size
                and abs(older.start + older.width - bucket_start) < 1e-7):
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
    mood_before: float | None = None,
    mood_after: float | None = None,
    moodlets: MoodletState | None = None,
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
    continuous = history.continuous_since

    def advance_points(
        points: float, left: float, right: float, passive: float,
    ) -> float:
        duration = right - left
        if (continuous is None or start + (left + right) / 2 < continuous
                or mood_before is None or mood_after is None):
            return passive_friendship(points, passive * duration / 3600)
        positive, negative = emotional_friendship_rates(
            mood_before + (mood_after - mood_before) * left / seconds,
            mood_before + (mood_after - mood_before) * right / seconds,
            moodlets or MoodletState(), recent_contact=(history.last_contact is not None
                and start + (left + right) / 2 - history.last_contact
                < _setting("absence_grace_seconds")),
        )
        units = duration / BALANCE.number("simulation", "status_interval_seconds")
        return balance_friendship(points, positive=positive * units,
                                  negative=negative * units + passive * duration / 3600)
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
        points = progress.points
        for low, high in zip(age_boundaries, age_boundaries[1:] + [float("inf")]):
            duration = max(0.0, min(ages[1], high) - max(ages[0], low))
            if duration:
                left = max(ages[0], low) - ages[0]
                points = advance_points(points, left, left + duration,
                                        absence_rate(max(ages[0], low) + duration / 2))
        return FriendshipProgress(
            points,
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
            points = advance_points(points, left + (right - left) * low,
                                    left + (right - left) * high, reference)
    return FriendshipProgress(
        points,
        prune_history(replace(history, critical=buckets), start + seconds),
        start + seconds,
    )
