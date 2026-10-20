"""Pure overall feeling from all active impressions; no timer or emotional store."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Mapping

from .balance import BALANCE
from .moodlets import (
    EmotionalDirection,
    MoodletAttribution,
    MoodletDefinition,
    MoodletEpisode,
    MoodletId,
    MoodletPolarity,
)


class EmotionalState(StrEnum):
    CHEERFUL = "cheerful"
    PROUD = "proud"
    RELIEVED = "relieved"
    AFFECTIONATE = "affectionate"
    IRRITATED = "irritated"
    CROWDED = "crowded"
    FRUSTRATED = "frustrated"
    DOWNCAST = "downcast"
    LONELY = "lonely"
    AMBIVALENT = "ambivalent"
    SUBDUED = "subdued"
    CALM = "calm"
    SATISFIED = "satisfied"


@dataclass(frozen=True, slots=True)
class EmotionalInfluence:
    instance_id: int
    cause: MoodletId
    polarity: MoodletPolarity
    direction: EmotionalDirection
    intensity: int
    last_trigger_at: float
    attribution: MoodletAttribution


@dataclass(frozen=True, slots=True)
class EmotionalComposition:
    primary: EmotionalState
    positive_intensity: int = 0
    negative_intensity: int = 0
    directions: tuple[tuple[EmotionalDirection, int], ...] = ()
    influences: tuple[EmotionalInfluence, ...] = ()


def derive_emotional_state(
    mood_value: float,
    episodes: tuple[MoodletEpisode, ...],
    *,
    definitions: Mapping[MoodletId, MoodletDefinition],
) -> EmotionalComposition:
    """Use intensity totals, never capped numeric contributions or physical labels."""
    influences = tuple(
        EmotionalInfluence(
            e.instance_id,
            e.definition_id,
            definitions[e.definition_id].polarity,
            definitions[e.definition_id].direction,
            e.level,
            e.last_trigger_at,
            e.attribution,
        )
        for e in episodes
    )
    positive = sum(
        i.intensity for i in influences if i.polarity == MoodletPolarity.POSITIVE
    )
    negative = sum(
        i.intensity for i in influences if i.polarity == MoodletPolarity.NEGATIVE
    )
    directions = tuple(
        (d, sum(i.intensity for i in influences if i.direction == d))
        for d in EmotionalDirection
        if any(i.direction == d for i in influences)
    )
    if not influences:
        label = (
            EmotionalState.SUBDUED
            if mood_value < BALANCE.number("emotions", "subdued_below_mood")
            else EmotionalState.SATISFIED
            if mood_value >= BALANCE.number("emotions", "satisfied_at_mood")
            else EmotionalState.CALM
        )
    elif positive == negative:
        label = EmotionalState.AMBIVALENT
    else:
        polarity = (
            MoodletPolarity.POSITIVE
            if positive > negative
            else MoodletPolarity.NEGATIVE
        )
        winning = tuple(i for i in influences if i.polarity == polarity)

        def rank(direction: EmotionalDirection) -> tuple[int, float, int, int]:
            relevant = tuple(i for i in winning if i.direction == direction)
            return (
                sum(i.intensity for i in relevant),
                max(i.last_trigger_at for i in relevant),
                max(i.intensity for i in relevant),
                -tuple(EmotionalDirection).index(direction),
            )

        direction = max(
            (d for d, _ in directions if any(i.direction == d for i in winning)),
            key=rank,
        )
        label = EmotionalState(direction.value)
    return EmotionalComposition(label, positive, negative, directions, influences)
