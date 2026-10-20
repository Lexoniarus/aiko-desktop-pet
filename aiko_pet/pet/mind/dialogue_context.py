"""Immutable conversational facts, independent of presentation and care effects."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from ..emotions import EmotionalComposition, EmotionalState
from ..moodlets import EmotionalDirection
from ..needs import NeedCondition
from ..routine import TimeContext


class FriendshipStage(StrEnum):
    ACQUAINTANCE = "acquaintance"
    FAMILIAR = "familiar"
    FRIEND = "friend"
    CLOSE = "close"

    @classmethod
    def from_level(cls, level: int) -> FriendshipStage:
        if not 1 <= level <= 10:
            raise ValueError("Friendship level outside 1..10")
        if level <= 2:
            return cls.ACQUAINTANCE
        if level <= 5:
            return cls.FAMILIAR
        if level <= 8:
            return cls.FRIEND
        return cls.CLOSE


class ReactionTone(StrEnum):
    IRRITATED = "irritated"
    WARM = "warm"


class SituationalCondition(StrEnum):
    FATIGUED = "fatigued"
    PLAYFUL = "playful"


@dataclass(frozen=True, slots=True)
class DialogueContext:
    stage: FriendshipStage
    mood_value: float
    emotions: EmotionalComposition
    time: TimeContext
    need_conditions: frozenset[NeedCondition] = frozenset()
    reaction_tone: ReactionTone | None = None
    situational_conditions: frozenset[SituationalCondition] = frozenset()
    sleeping: bool = False
    working: bool = False
    present: bool | None = None


@dataclass(frozen=True, slots=True)
class DialogueConditions:
    """One conjunction; a line may explicitly offer alternative conjunctions."""

    emotional_states: frozenset[EmotionalState] = frozenset()
    emotional_directions: frozenset[EmotionalDirection] = frozenset()
    need_conditions: frozenset[NeedCondition] = frozenset()
    reaction_tones: frozenset[ReactionTone] = frozenset()
    situational_conditions: frozenset[SituationalCondition] = frozenset()
    sleeping: bool | None = None

    def matches(self, context: DialogueContext) -> bool:
        return (
            (
                not self.emotional_states
                or context.emotions.primary in self.emotional_states
            )
            and self.emotional_directions <= {d for d, _ in context.emotions.directions}
            and self.need_conditions <= context.need_conditions
            and (
                not self.reaction_tones or context.reaction_tone in self.reaction_tones
            )
            and self.situational_conditions <= context.situational_conditions
            and (self.sleeping is None or self.sleeping == context.sleeping)
        )

    def specificity(self) -> tuple[int, int]:
        size = (
            bool(self.emotional_states)
            + len(self.emotional_directions)
            + len(self.need_conditions)
            + bool(self.reaction_tones)
            + len(self.situational_conditions)
            + (self.sleeping is not None)
        )
        # A short reaction may color wording without replacing overall feeling.
        return size, 2 if self.reaction_tones else 1 if self.emotional_states else 0
