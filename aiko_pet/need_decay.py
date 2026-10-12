"""Need and mood decay while awake or asleep, independent from rendering."""

from __future__ import annotations

from typing import Protocol

from .routine import TimeContext
from .value_rules import clamp_need_value


class NeedValues(Protocol):
    """Minimum mutable fields for applying the care simulation decay."""

    sleeping: bool
    satiety: float
    mood: float
    energy: float
    social: float
    affection: float


def apply_need_decay(
    record: NeedValues,
    hours: float,
    context: TimeContext | None,
    effort: float | None = None,
) -> None:
    """Update needs using the original sleeping and workload-dependent rates."""
    if record.sleeping:
        record.satiety = clamp_need_value(record.satiety - hours * 1.4)
        record.mood = clamp_need_value(record.mood + hours * 0.5)
        record.energy = clamp_need_value(record.energy + hours * 22.0)
        record.social = clamp_need_value(record.social - hours * 0.35)
        record.affection = clamp_need_value(record.affection - hours * 0.25)
        return
    # A relaxed rhythm; weekends are slightly gentler, no obligations.
    if context is None:
        satiety_rate, mood_rate, energy_rate = 3.0, -2.0, 2.2
    else:
        satiety_rate = 4.0 if context.meal is not None else 2.4
        mood_rate = (
            0.3 if context.weekend and context.period in ("free", "evening")
            else -0.4 if context.period == "quiet"
            else -0.9
        )
        energy_rate = (
            1.1 if context.weekend and context.period == "free"
            else 1.5 if context.period == "quiet"
            else 2.0
        )
    # CPU/GPU effort is *her* observed work. RAM use alone adds only
    # small pressure upstream. Missing telemetry means normal decay.
    intensity = 0.0 if effort is None else max(
        0.0, min(1.0, (effort - 0.15) / 0.85),
    )
    satiety_rate *= 1.0 + 0.95 * intensity
    mood_rate -= 2.1 * intensity
    energy_rate += 2.8 * intensity
    social_rate = 1.8 + 0.35 * intensity
    # Affection is emotional care, not CPU/GPU usage and not conversation.
    affection_rate = 1.35
    if record.social < 20:
        mood_rate -= 0.7
    if record.affection < 20:
        mood_rate -= 0.8
    record.satiety = clamp_need_value(record.satiety - hours * satiety_rate)
    record.mood = clamp_need_value(record.mood + hours * mood_rate)
    record.energy = clamp_need_value(record.energy - hours * energy_rate)
    record.social = clamp_need_value(record.social - hours * social_rate)
    record.affection = clamp_need_value(record.affection - hours * affection_rate)
