"""Numeric base mood, nuanced by impressions without a second emotional store."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Mapping

from .balance import BALANCE
from .moodlets import (
    EmotionalDirection,
    MoodletAttribution,
    MoodletDefinition,
    MoodletEpisode,
    MoodletGroup,
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
    """Keep all topic evidence; bounded modifiers colour the numeric base mood."""
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
    base = (
        EmotionalState.SUBDUED
        if mood_value < BALANCE.number("emotions", "subdued_below_mood")
        else EmotionalState.SATISFIED
        if mood_value >= BALANCE.number("emotions", "satisfied_at_mood")
        else EmotionalState.CALM
    )
    weighted = _modifiers(influences, definitions)
    good = sum(weight for i, weight in weighted
               if i.polarity == MoodletPolarity.POSITIVE)
    bad = sum(weight for i, weight in weighted
              if i.polarity == MoodletPolarity.NEGATIVE)
    if not weighted:
        label = base
    elif base == EmotionalState.SUBDUED:
        # Positive history stays available as a topic, but cannot turn a low
        # actual mood into optimism. Negative causes can explain its flavour.
        label = (_direction_label(weighted, MoodletPolarity.NEGATIVE, mood_value)
                 if bad else base)
    elif base == EmotionalState.CALM and max(good, bad) < BALANCE.number(
        "emotions", "noticeable_modifier_intensity",
    ):
        label = base
    elif good * 5 <= (good + bad) * 3 + 1e-9 and bad * 5 <= (
        good + bad
    ) * 3 + 1e-9:
        label = _mixed_label(weighted, bad)
    elif good > bad:
        label = _direction_label(weighted, MoodletPolarity.POSITIVE, mood_value)
    elif base == EmotionalState.SATISFIED and bad < BALANCE.number(
        "emotions", "noticeable_modifier_intensity",
    ):
        label = _mixed_label(weighted, bad)
    else:
        label = _direction_label(weighted, MoodletPolarity.NEGATIVE, mood_value)
    return EmotionalComposition(label, positive, negative, directions, influences)


def _modifiers(
    influences: tuple[EmotionalInfluence, ...],
    definitions: Mapping[MoodletId, MoodletDefinition],
) -> tuple[tuple[EmotionalInfluence, float], ...]:
    """One bounded long-term background per polarity; no episode is discarded."""
    long_totals = {
        polarity: sum(i.intensity for i in influences if i.polarity == polarity
                      and definitions[i.cause].group == MoodletGroup.LONG_TERM)
        for polarity in MoodletPolarity
    }
    cap = BALANCE.number("emotions", "long_term_modifier_cap")
    return tuple((i, i.intensity * min(1, cap / long_totals[i.polarity])
                  if definitions[i.cause].group == MoodletGroup.LONG_TERM
                  else float(i.intensity)) for i in influences)


def _mixed_label(
    weighted: tuple[tuple[EmotionalInfluence, float], ...], negative: float,
) -> EmotionalState:
    cautious = sum(weight for i, weight in weighted
                   if i.direction in (EmotionalDirection.GUARDED,
                                      EmotionalDirection.UNCERTAIN))
    return (EmotionalState.RESERVED if cautious * 2 >= negative
            else EmotionalState.AMBIVALENT)


def _direction_label(
    weighted: tuple[tuple[EmotionalInfluence, float], ...],
    polarity: MoodletPolarity, mood_value: float,
) -> EmotionalState:
    winning = tuple((i, weight) for i, weight in weighted if i.polarity == polarity)

    def rank(direction: EmotionalDirection) -> tuple[float, float, int, int]:
        relevant = tuple((i, weight) for i, weight in winning
                         if i.direction == direction)
        return (
            sum(weight for _, weight in relevant),
            max(i.last_trigger_at for i, _ in relevant),
            max(i.intensity for i, _ in relevant),
            -tuple(EmotionalDirection).index(direction),
        )

    direction = max((i.direction for i, _ in winning), key=rank)
    totals = {d: sum(weight for i, weight in winning if i.direction == d)
              for d in EmotionalDirection}
    positive = sum(weight for i, weight in weighted
                   if i.polarity == MoodletPolarity.POSITIVE)
    negative = sum(weight for i, weight in weighted
                   if i.polarity == MoodletPolarity.NEGATIVE)
    joy, safety = totals[EmotionalDirection.CHEERFUL], totals[EmotionalDirection.SAFE]
    optimism = totals[EmotionalDirection.OPTIMISTIC]
    pride = totals[EmotionalDirection.PROUD]
    uncertainty = totals[EmotionalDirection.UNCERTAIN]
    pressure = sum(totals[d] for d in (
        EmotionalDirection.IRRITATED, EmotionalDirection.CROWDED,
        EmotionalDirection.FRUSTRATED,
    ))
    if (polarity == MoodletPolarity.POSITIVE and joy and safety
            and (joy + safety) * 5 >= positive * 3
            and negative * 5 <= positive + negative and mood_value >= 70):
        return EmotionalState.CAREFREE
    if (polarity == MoodletPolarity.POSITIVE and optimism and pride
            and (optimism + pride) * 5 >= positive * 3):
        return EmotionalState.OPTIMISTIC
    if (polarity == MoodletPolarity.NEGATIVE and uncertainty and pressure
            and (uncertainty + pressure) * 5 >= negative * 3):
        return EmotionalState.TENSE
    special = {
        EmotionalDirection.SAFE: EmotionalState.AFFECTIONATE,
        EmotionalDirection.UNCERTAIN: EmotionalState.TENSE,
        EmotionalDirection.GUARDED: EmotionalState.RESERVED,
    }
    if direction in special:
        return special[direction]
    return EmotionalState(direction.value)
