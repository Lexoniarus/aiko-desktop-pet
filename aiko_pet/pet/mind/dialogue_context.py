"""Immutable conversational facts, independent of presentation and care effects."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from ..emotions import EmotionalComposition, EmotionalState
from ..moodlets import (
    EmotionalDirection,
    MoodletAttribution,
    MoodletCauseKind,
    MoodletOutcome,
)
from ..needs import NeedCondition
from ..routine import TimeContext
from ..wishes import WishId, WishObjective
from .conversation_topics import ConversationTopic


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
    conversation_topic: ConversationTopic | None = None


@dataclass(frozen=True, slots=True)
class DialogueConditions:
    """One conjunction; a line may explicitly offer alternative conjunctions."""

    emotional_states: frozenset[EmotionalState] = frozenset()
    emotional_directions: frozenset[EmotionalDirection] = frozenset()
    need_conditions: frozenset[NeedCondition] = frozenset()
    reaction_tones: frozenset[ReactionTone] = frozenset()
    situational_conditions: frozenset[SituationalCondition] = frozenset()
    sleeping: bool | None = None
    conversation_topics: frozenset[str] = frozenset()
    conversation_attributions: frozenset[MoodletAttribution] = frozenset()
    conversation_causes: frozenset[MoodletCauseKind] = frozenset()
    conversation_objectives: frozenset[WishObjective] = frozenset()
    conversation_targets: frozenset[str] = frozenset()
    conversation_outcomes: frozenset[MoodletOutcome] = frozenset()
    conversation_round_outcomes: frozenset[MoodletOutcome] = frozenset()
    conversation_wishes: frozenset[WishId] = frozenset()

    def matches(self, context: DialogueContext) -> bool:
        topic = context.conversation_topic
        cause = topic.cause if topic is not None else None
        wish = cause.wish if cause is not None else None
        round_outcome = (cause.game.round_outcome if cause.game is not None
                         else cause.outcome) if cause is not None else None
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
            and (not self.conversation_topics or context.conversation_topic is not None
                 and context.conversation_topic.key in self.conversation_topics)
            and (not self.conversation_attributions
                 or context.conversation_topic is not None
                 and context.conversation_topic.cause is not None
                 and context.conversation_topic.cause.attribution
                 in self.conversation_attributions)
            and (not self.conversation_causes
                 or context.conversation_topic is not None
                 and context.conversation_topic.cause is not None
                 and context.conversation_topic.cause.kind in self.conversation_causes)
            and (not self.conversation_objectives or wish is not None
                 and wish.objective in self.conversation_objectives)
            and (not self.conversation_targets or cause is not None
                 and cause.target_id in self.conversation_targets)
            and (not self.conversation_outcomes or cause is not None
                 and cause.outcome in self.conversation_outcomes)
            and (not self.conversation_round_outcomes
                 or round_outcome in self.conversation_round_outcomes)
            and (not self.conversation_wishes or wish is not None
                 and wish.definition_id in self.conversation_wishes)
        )

    def specificity(self) -> tuple[int, int]:
        size = (
            bool(self.emotional_states)
            + len(self.emotional_directions)
            + len(self.need_conditions)
            + bool(self.reaction_tones)
            + len(self.situational_conditions)
            + (self.sleeping is not None)
            + bool(self.conversation_topics)
            + bool(self.conversation_attributions)
            + bool(self.conversation_causes)
            + bool(self.conversation_objectives)
            + bool(self.conversation_targets)
            + bool(self.conversation_outcomes)
            + bool(self.conversation_round_outcomes)
            + bool(self.conversation_wishes)
        )
        # A short reaction may color wording without replacing overall feeling.
        return size, 2 if self.reaction_tones else 1 if self.emotional_states else 0
