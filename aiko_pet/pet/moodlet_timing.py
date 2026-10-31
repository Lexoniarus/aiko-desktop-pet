"""Pure stage budgets on the owning Pet's elapsed axis; never qualifies an event."""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from .balance import BALANCE
from .moodlet_models import CursorImpressionParameters

if TYPE_CHECKING:
    from .moodlet_models import MoodletDefinition, MoodletEpisode


def stage_seconds(
    episode: MoodletEpisode,
    definition: MoodletDefinition,
) -> tuple[float, ...]:
    """Level one upward. Empty stored lower stages retain the legacy schedule.

    The fixed catalogue duration remains the read contract for old implicit
    stages; new wish episodes always receive explicit lower-stage budgets.
    """
    lower = episode.lower_stage_seconds or (
        (float(definition.decay_stage_seconds),) * (episode.level - 1)
    )
    return (*lower, episode.remaining_seconds)


def initial_stage_seconds(
    definition: MoodletDefinition,
    level: int,
) -> tuple[float, ...]:
    if isinstance(definition.parameters, CursorImpressionParameters):
        return tuple(float(v) for v in definition.parameters.stage_seconds[:level])
    if not definition.uses_positive_stage_budgets:
        return (float(definition.decay_stage_seconds),) * level
    return tuple(
        BALANCE.number(
            "moodlets",
            "positive_level_one_seconds"
            if index == 0
            else "positive_upper_stage_seconds",
        )
        for index in range(level)
    )


def reinforced_stage_seconds(
    episode: MoodletEpisode,
    definition: MoodletDefinition,
    level: int,
) -> tuple[float, ...]:
    """Ascent floors each tier; only an already maximal family renews time."""
    old = stage_seconds(episode, definition)
    cap = BALANCE.number("moodlets", "positive_stage_cap_seconds")
    if episode.level == len(definition.level_points):
        extension = BALANCE.number("moodlets", "positive_renewal_seconds")
        return tuple(min(cap, seconds + extension) for seconds in old)
    base = initial_stage_seconds(definition, level)
    return tuple(
        min(cap, max(old[index] if index < len(old) else 0, seconds))
        for index, seconds in enumerate(base)
    )


def age_moodlet(
    episode: MoodletEpisode,
    seconds: float,
    definition: MoodletDefinition,
) -> MoodletEpisode | None:
    """Spend at most three stages, retaining actual lower-stage residuals."""
    if seconds == 0 and episode.remaining_seconds > 0:
        return episode
    stages = list(stage_seconds(episode, definition))
    while stages and seconds >= stages[-1]:
        seconds -= stages.pop()
    if not stages:
        return None
    level = len(stages)
    return replace(
        episode,
        level=level,
        remaining_seconds=stages[-1] - seconds,
        lower_stage_seconds=tuple(stages[:-1]) if episode.lower_stage_seconds else (),
        pending_repetitions=episode.pending_repetitions
        if level == episode.level
        else 0,
    )
