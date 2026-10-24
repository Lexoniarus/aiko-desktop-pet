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
    CAREFREE = "carefree"
    OPTIMISTIC = "optimistic"
    RESERVED = "reserved"
    TENSE = "tense"


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


def supports_positive_expression(composition: EmotionalComposition) -> bool:
    """Ordinary positive expression follows the same primary feeling as status."""
    return composition.primary in (
        EmotionalState.CHEERFUL,
        EmotionalState.PROUD,
        EmotionalState.RELIEVED,
        EmotionalState.AFFECTIONATE,
        EmotionalState.SATISFIED,
        EmotionalState.OPTIMISTIC,
        EmotionalState.CAREFREE,
    )


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
    elif positive * 5 <= (positive + negative) * 3 and negative * 5 <= (
        positive + negative
    ) * 3:
        cautious = sum(n for d, n in directions if d in (
            EmotionalDirection.GUARDED, EmotionalDirection.UNCERTAIN,
        ))
        label = (EmotionalState.RESERVED if cautious * 2 >= negative
                 else EmotionalState.AMBIVALENT)
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
        totals = dict(directions)
        joy, safety = totals.get(EmotionalDirection.CHEERFUL, 0), totals.get(
            EmotionalDirection.SAFE, 0,
        )
        optimism, pride = totals.get(EmotionalDirection.OPTIMISTIC, 0), totals.get(
            EmotionalDirection.PROUD, 0,
        )
        uncertainty = totals.get(EmotionalDirection.UNCERTAIN, 0)
        pressure = sum(totals.get(d, 0) for d in (
            EmotionalDirection.IRRITATED, EmotionalDirection.CROWDED,
            EmotionalDirection.FRUSTRATED,
        ))
        if (polarity == MoodletPolarity.POSITIVE and joy and safety
                and (joy + safety) * 5 >= positive * 3
                and negative * 5 <= positive + negative and mood_value >= 70):
            label = EmotionalState.CAREFREE
        elif (polarity == MoodletPolarity.POSITIVE and optimism and pride
              and (optimism + pride) * 5 >= positive * 3):
            label = EmotionalState.OPTIMISTIC
        elif (polarity == MoodletPolarity.NEGATIVE and uncertainty and pressure
              and (uncertainty + pressure) * 5 >= negative * 3):
            label = EmotionalState.TENSE
        elif direction == EmotionalDirection.SAFE:
            label = EmotionalState.AFFECTIONATE
        elif direction == EmotionalDirection.UNCERTAIN:
            label = EmotionalState.TENSE
        elif direction == EmotionalDirection.GUARDED:
            label = EmotionalState.RESERVED
        else:
            label = EmotionalState(direction.value)
    return EmotionalComposition(label, positive, negative, directions, influences)
