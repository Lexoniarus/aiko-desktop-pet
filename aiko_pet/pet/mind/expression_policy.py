"""Facial intent from the actual speaking event and retained topic evidence."""

from ...games.contracts import GameId
from ..animation.expression import Expression, event_expression
from ..emotions import EmotionalState, supports_positive_expression
from ..moodlet_catalog import MOODLET_CATALOG
from ..moodlets import EmotionalDirection, MoodletOutcome
from .conversation_topics import ConversationKind
from .dialogue_context import DialogueContext, ReactionTone


def speech_expression(event: str, context: DialogueContext) -> Expression | None:
    """No inference from text, no mood mutation and no independent topic choice."""
    explicit = event_expression(event)
    if explicit is not None:
        return explicit
    if context.reaction_tone == ReactionTone.IRRITATED:
        return Expression.FIRM
    topic = context.conversation_topic if event == "talk" else None
    if topic is not None and topic.kind == ConversationKind.GAME and topic.cause:
        cause = topic.cause
        # Retained game evidence already uses Aiko's perspective, unlike the
        # player-facing live window outcomes translated by event_expression.
        outcome = cause.game.round_outcome if cause.game is not None else cause.outcome
        if cause.target_id == GameId.QUIZ.value:
            return Expression.POSITIVE
        if cause.target_id == GameId.MASTERMIND.value:
            return (Expression.POSITIVE if outcome in (
                MoodletOutcome.LOSS, MoodletOutcome.COMPLETED,
            ) else Expression.WORRIED)
        if outcome == MoodletOutcome.WIN:
            return Expression.POSITIVE
        if outcome == MoodletOutcome.LOSS:
            return Expression.DOWNCAST
        if outcome == MoodletOutcome.DRAW:
            return Expression.QUESTIONING
    if topic is not None and topic.moodlet_id is not None:
        direction = MOODLET_CATALOG.definitions[topic.moodlet_id].direction
        if direction in (EmotionalDirection.IRRITATED, EmotionalDirection.CROWDED,
                         EmotionalDirection.FRUSTRATED):
            return Expression.FIRM
        if direction in (EmotionalDirection.DOWNCAST, EmotionalDirection.LONELY):
            return Expression.DOWNCAST
        if direction in (EmotionalDirection.UNCERTAIN, EmotionalDirection.GUARDED):
            return Expression.WORRIED
        if supports_positive_expression(context.emotions):
            return Expression.POSITIVE
    primary = context.emotions.primary
    if primary in (EmotionalState.SUBDUED, EmotionalState.DOWNCAST,
                   EmotionalState.LONELY):
        return Expression.DOWNCAST
    if primary in (EmotionalState.IRRITATED, EmotionalState.CROWDED,
                   EmotionalState.FRUSTRATED):
        return Expression.FIRM
    if primary in (EmotionalState.RESERVED, EmotionalState.TENSE):
        return Expression.WORRIED
    if supports_positive_expression(context.emotions):
        return Expression.POSITIVE
    return None
