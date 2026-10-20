"""Typed immutable dialogue fixtures; no legacy mixed emotion/need vocabulary."""

from aiko_pet.pet.emotions import EmotionalComposition, EmotionalState
from aiko_pet.pet.mind.dialogue_context import (
    DialogueContext,
    FriendshipStage,
    ReactionTone,
    SituationalCondition,
)
from aiko_pet.pet.needs import NeedCondition
from aiko_pet.pet.routine import TimeContext


def dialogue_context(
    time: TimeContext,
    *,
    stage: FriendshipStage = FriendshipStage.ACQUAINTANCE,
    emotional_state: EmotionalState = EmotionalState.CALM,
    mood_value: float = 60,
    need_conditions: frozenset[NeedCondition] = frozenset(),
    reaction_tone: ReactionTone | None = None,
    situational_conditions: frozenset[SituationalCondition] = frozenset(),
    sleeping: bool = False,
    present: bool | None = None,
) -> DialogueContext:
    return DialogueContext(
        stage,
        mood_value,
        EmotionalComposition(emotional_state),
        time,
        need_conditions,
        reaction_tone,
        situational_conditions,
        sleeping,
        present=present,
    )
