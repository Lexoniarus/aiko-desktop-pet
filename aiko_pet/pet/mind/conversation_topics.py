"""Pure Plaudern topics from retained evidence; no conversation history or clock."""

import random
from dataclasses import dataclass
from enum import StrEnum

from ...games.contracts import (
    BlackjackDecisionReason,
    BlackjackDetails,
    GameId,
    RockPaperScissorsDetails,
)
from ..food_catalog import DEFAULT_CATALOG
from ..moodlets import (
    MoodletCause,
    MoodletCauseKind,
    MoodletId,
    MoodletOutcome,
    MoodletState,
)
from ..wishes import ActiveWish


class ConversationKind(StrEnum):
    GAME = "game"
    FOOD = "food"
    AFFECTION = "affection"
    SOCIAL = "social"
    NEGATIVE = "negative"
    POOR_CARE = "poor_care"
    LONG_TERM = "long_term"
    WISH = "wish"
    STATE = "state"


NEGATIVE_FAMILIES = frozenset({
    MoodletId.POKING, MoodletId.CROWDED, MoodletId.FOOD_MONOTONY,
    MoodletId.WITHHELD, MoodletId.DISRUPTED, MoodletId.FOOD_WISH_DISREGARDED,
})
POOR_CARE_FAMILIES = frozenset({
    MoodletId.HUNGER_WORN, MoodletId.EXHAUSTION_IRRITATED, MoodletId.UNSTIMULATED,
    MoodletId.LONELY, MoodletId.MISSING_CLOSENESS,
})
LONG_TERM_FAMILIES = frozenset({
    MoodletId.TRUSTING, MoodletId.APPRECIATED, MoodletId.OPTIMISTIC,
    MoodletId.UNCERTAIN, MoodletId.OVERLOOKED, MoodletId.GUARDED,
})
CONVERSATION_KEYS = frozenset({
    "state", "wish", "affection", "game.cumulative", "food.intake", "food.handover",
    *(f"game.{game.value}.{outcome.value}" for game in GameId if game != GameId.QUIZ
      for outcome in (MoodletOutcome.WIN, MoodletOutcome.LOSS, MoodletOutcome.DRAW)),
    "game.quiz.completed",
    *(f"game.rock_paper_scissors.{outcome.value}.hands"
      for outcome in (MoodletOutcome.WIN, MoodletOutcome.LOSS, MoodletOutcome.DRAW)),
    *(f"game.blackjack.{reason.value}" for reason in BlackjackDecisionReason),
    *(f"social.{category}" for category in ("chat", "single", "twopart", "fact")),
    *(f"negative.{family.value}" for family in NEGATIVE_FAMILIES),
    *(f"poor_care.{family.value}" for family in POOR_CARE_FAMILIES),
    *(f"long_term.{family.value}" for family in LONG_TERM_FAMILIES),
})
CONVERSATION_TEXT_FIELDS = frozenset({
    "target", "count", "player_total", "aiko_total", "wish_text",
    "aiko_move", "player_move",
})


def conversation_fields(key: str) -> frozenset[str]:
    """Fields proved by a semantic key, used by the one catalogue validator."""
    if key == "wish":
        return frozenset({"wish_text"})
    if key == "game.cumulative":
        return frozenset({"target", "count"})
    if key.startswith("game.rock_paper_scissors.") and key.endswith(".hands"):
        return frozenset({"target", "aiko_move", "player_move"})
    if key.startswith("game.blackjack.") and key.rsplit(".", 1)[-1] in {
        reason.value for reason in BlackjackDecisionReason
    }:
        return frozenset({"target", "player_total", "aiko_total"})
    if key.startswith(("food.", "game.")):
        return frozenset({"target"})
    return frozenset()


@dataclass(frozen=True, slots=True)
class ConversationTopic:
    kind: ConversationKind
    episode_id: int | None = None
    moodlet_id: MoodletId | None = None
    cause: MoodletCause | None = None
    wish: ActiveWish | None = None

    @property
    def key(self) -> str:
        cause = self.cause
        if cause is None:
            return self.kind.value
        if self.kind == ConversationKind.GAME:
            if cause.wish is not None and cause.wish.required_count > 1:
                return "game.cumulative"
            if isinstance(cause.game_details, BlackjackDetails):
                return f"game.blackjack.{cause.game_details.reason.value}"
            if isinstance(cause.game_details, RockPaperScissorsDetails):
                rps_result = cause.game_details.aiko_outcome
                return f"game.rock_paper_scissors.{rps_result}.hands"
            result = (cause.game.round_outcome if cause.game is not None
                      else cause.outcome)
            return f"game.{cause.target_id}.{result.value}"
        if self.kind in (ConversationKind.NEGATIVE, ConversationKind.POOR_CARE,
                         ConversationKind.LONG_TERM):
            assert self.moodlet_id is not None
            return f"{self.kind.value}.{self.moodlet_id.value}"
        if self.kind == ConversationKind.FOOD:
            return f"food.{cause.outcome.value}"
        if self.kind == ConversationKind.SOCIAL:
            return f"social.{cause.target_id}"
        return self.kind.value


def _cause_kind(family: MoodletId, cause: MoodletCause) -> ConversationKind | None:
    if cause.kind == MoodletCauseKind.LEGACY or not cause.event_id:
        return None
    if cause.kind == MoodletCauseKind.LONG_TERM:
        return (ConversationKind.LONG_TERM if family in LONG_TERM_FAMILIES
                and cause.period is not None else None)
    if cause.kind == MoodletCauseKind.POOR_CARE:
        return ConversationKind.POOR_CARE if family in POOR_CARE_FAMILIES else None
    if family in NEGATIVE_FAMILIES:
        return ConversationKind.NEGATIVE
    if cause.target_id in {game.value for game in GameId}:
        result = cause.game.round_outcome if cause.game is not None else cause.outcome
        if (result == MoodletOutcome.COMPLETED if cause.target_id == GameId.QUIZ.value
                else result in (MoodletOutcome.WIN, MoodletOutcome.LOSS,
                                MoodletOutcome.DRAW)):
            return ConversationKind.GAME
    if cause.target_id in DEFAULT_CATALOG.foods and cause.outcome in (
        MoodletOutcome.INTAKE, MoodletOutcome.HANDOVER,
    ):
        return ConversationKind.FOOD
    if (family == MoodletId.SECURE and cause.target_id == "pet"
            and cause.outcome == MoodletOutcome.COMPLETED):
        return ConversationKind.AFFECTION
    if (cause.target_id in ("chat", "single", "twopart", "fact")
            and cause.outcome == MoodletOutcome.COMPLETED):
        return ConversationKind.SOCIAL
    return None


def select_conversation_topic(
    moodlets: MoodletState, *, rng: random.Random, elapsed: float,
    disclosed_wishes: tuple[ActiveWish, ...] = (),
) -> ConversationTopic:
    """Weight each episode once, then choose one of its actual retained causes.

    A shared event belongs once to the strongest surviving episode (stable ID
    breaks ties). Caller-supplied wishes must already be safe to disclose; this
    policy also checks disclosure/expiry and never narrates them as completed.
    """
    seen: set[str] = set()
    buckets: list[tuple[int, tuple[ConversationTopic, ...]]] = []
    for episode in sorted(moodlets.active, key=lambda e: (-e.level, e.instance_id)):
        if episode.remaining_seconds <= 0:
            continue
        topics: list[ConversationTopic] = []
        for cause in episode.causes:
            kind = _cause_kind(episode.definition_id, cause)
            if (kind is None or cause.occurred_at > elapsed or cause.event_id in seen):
                continue
            assert cause.event_id is not None
            seen.add(cause.event_id)
            topics.append(ConversationTopic(
                kind, episode.instance_id, episode.definition_id, cause,
            ))
        if topics:
            buckets.append((episode.level, tuple(topics)))
    if buckets:
        bucket = rng.choices(buckets, weights=[weight for weight, _ in buckets], k=1)[0]
        return rng.choice(bucket[1])
    wishes = tuple(w for w in disclosed_wishes
                   if w.expressed_at is not None and w.is_active_at(elapsed))
    if wishes:
        return ConversationTopic(ConversationKind.WISH, wish=rng.choice(wishes))
    return ConversationTopic(ConversationKind.STATE)
