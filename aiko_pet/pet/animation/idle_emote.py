"""Pure, need-dependent idle emote choice for a pet."""

from __future__ import annotations

from ..balance import BALANCE
from ..emotions import (
    EmotionalComposition,
    EmotionalState,
    supports_positive_expression,
)


def choose_idle_emote(
    *,
    energy: float,
    satiety: float,
    mood: float,
    affection: float,
    emotions: EmotionalComposition,
) -> str:
    """Keep direct physical cues and derive emotional cues from the shared feeling."""
    if energy < BALANCE.integer("idle_emotes", "tired_energy"):
        return "sleeps"
    if satiety < BALANCE.integer("idle_emotes", "hungry_satiety"):
        return "drops"
    if emotions.primary in (
        EmotionalState.IRRITATED,
        EmotionalState.CROWDED,
        EmotionalState.FRUSTRATED,
        EmotionalState.TENSE,
    ):
        return "anger"
    if emotions.primary in (
        EmotionalState.SUBDUED,
        EmotionalState.DOWNCAST,
        EmotionalState.LONELY,
    ):
        return "faceSad"
    if emotions.primary in (EmotionalState.AMBIVALENT, EmotionalState.RESERVED):
        return "question"
    if affection < BALANCE.integer("idle_emotes", "low_affection"):
        return "heart"
    if mood >= BALANCE.integer(
        "idle_emotes", "happy_mood"
    ) and supports_positive_expression(emotions):
        return "star"
    return "idea"
