"""Compatibility imports; the canonical implementation lives in pet.mind."""

import random as random

from ..pet.mind.mind import (
    PetMind as PetMind,
    AikoMind as AikoMind,
    ANIMATIONS as ANIMATIONS,
    CATALOGUE as CATALOGUE,
    DialogueBook as DialogueBook,
    EMOTIONS as EMOTIONS,
    EMOTION_LABELS as EMOTION_LABELS,
    Line as Line,
    PERIODS as PERIODS,
    Reaction as Reaction,
    ClickButton as ClickButton,
    choose_click_reaction as choose_click_reaction,
    WorkEpisodeMemory as WorkEpisodeMemory,
    PetState as PetState,
    TimeContext as TimeContext,
)
