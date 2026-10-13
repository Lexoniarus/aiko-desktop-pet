"""Pure need-decay rules; the pet aggregate owns applying their results."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .routine import TimeContext
from .value_rules import clamp_need_value


class NeedValues(Protocol):
    """Required current values, readable without a concrete PetState."""

    sleeping: bool
    satiety: float
    mood: float
    energy: float
    social: float
    affection: float


@dataclass(frozen=True, slots=True)
class NeedLevels:
    """Calculated next values, not a mutable reference to the pet."""

    satiety: float
    mood: float
    energy: float
    social: float
    affection: float


def calculate_need_decay(
    record: NeedValues,
    hours: float,
    context: TimeContext | None,
    effort: float | None = None,
) -> NeedLevels:
    """Calculate established awake/asleep decay without changing the record."""
    if record.sleeping:
        return NeedLevels(
            satiety=clamp_need_value(record.satiety - hours * 1.4),
            mood=clamp_need_value(record.mood + hours * 0.5),
            energy=clamp_need_value(record.energy + hours * 22.0),
            social=clamp_need_value(record.social - hours * 0.35),
            affection=clamp_need_value(record.affection - hours * 0.25),
        )
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
    # CPU/GPU effort is her observed work; unseen work is never invented.
    intensity = 0.0 if effort is None else max(
        0.0, min(1.0, (effort - 0.15) / 0.85),
    )
    satiety_rate *= 1.0 + 0.95 * intensity
    mood_rate -= 2.1 * intensity
    energy_rate += 2.8 * intensity
    social_rate = 1.8 + 0.35 * intensity
    affection_rate = 1.35
    if record.social < 20:
        mood_rate -= 0.7
    if record.affection < 20:
        mood_rate -= 0.8
    return NeedLevels(
        satiety=clamp_need_value(record.satiety - hours * satiety_rate),
        mood=clamp_need_value(record.mood + hours * mood_rate),
        energy=clamp_need_value(record.energy - hours * energy_rate),
        social=clamp_need_value(record.social - hours * social_rate),
        affection=clamp_need_value(record.affection - hours * affection_rate),
    )


def apply_need_decay(
    record: NeedValues, hours: float,
    context: TimeContext | None, effort: float | None = None,
) -> None:
    """Legacy mutable-record adapter; PetState applies calculations itself."""
    next_values = calculate_need_decay(record, hours, context, effort)
    record.satiety = next_values.satiety
    record.mood = next_values.mood
    record.energy = next_values.energy
    record.social = next_values.social
    record.affection = next_values.affection
