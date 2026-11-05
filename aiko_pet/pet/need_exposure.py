"""Read the one bounded need history; markers never duplicate its timeline."""

import math
from dataclasses import dataclass
from typing import cast

from .balance import BALANCE
from .friendship_history import CriticalBucket, NeedDurations


@dataclass(frozen=True, slots=True)
class ExposureMark:
    """Elapsed watermark plus the already present part of its minute bucket."""

    at: float
    critical: float = 0.0
    zero: float = 0.0


def exposure_totals(
    buckets: tuple[CriticalBucket, ...], now: float,
) -> tuple[NeedDurations, NeedDurations]:
    """Canonical rolling-window reader used by the existing friendship policy."""
    cutoff = now - BALANCE.number("friendship", "history_window_seconds")
    critical, zero = [0.0] * 5, [0.0] * 5
    for bucket in buckets:
        fraction = min(1.0, max(0.0, (
            bucket.start + bucket.width - cutoff
        ) / bucket.width))
        for i in range(5):
            critical[i] += bucket.critical[i] * fraction
            zero[i] += bucket.zero[i] * fraction
    return cast(NeedDurations, tuple(critical)), cast(NeedDurations, tuple(zero))


def mark_exposure(
    buckets: tuple[CriticalBucket, ...], now: float, index: int,
) -> ExposureMark:
    size = BALANCE.number("friendship", "history_bucket_seconds")
    anchor = math.floor(now / size) * size
    for bucket in reversed(buckets):
        if bucket.start <= anchor < bucket.start + bucket.width:
            critical = min(size, max(0.0, bucket.critical[index] * size / bucket.width))
            zero = min(critical, max(0.0, bucket.zero[index] * size / bucket.width))
            return ExposureMark(now, critical, zero)
    return ExposureMark(now)


def unaccounted_exposure(
    buckets: tuple[CriticalBucket, ...], now: float, index: int, mark: ExposureMark,
) -> tuple[float, float]:
    """Exclude consumed burden exactly, including a partly filled anchor minute.

    Fully populated minutes may coalesce in the existing history. Their uniform
    density preserves this marker; partial minutes never coalesce with them.
    """
    size = BALANCE.number("friendship", "history_bucket_seconds")
    cutoff = now - BALANCE.number("friendship", "history_window_seconds")
    anchor = math.floor(mark.at / size) * size
    critical = zero = 0.0
    for bucket in buckets:
        end = bucket.start + bucket.width
        if end <= max(cutoff, anchor):
            continue
        if mark.at <= cutoff or bucket.start > anchor:
            fraction = min(1.0, max(0.0, (end - cutoff) / bucket.width))
            critical += bucket.critical[index] * fraction
            zero += bucket.zero[index] * fraction
        else:
            fraction = (end - anchor) / bucket.width
            critical += max(0.0, bucket.critical[index] * fraction - mark.critical)
            zero += max(0.0, bucket.zero[index] * fraction - mark.zero)
    return critical, zero
