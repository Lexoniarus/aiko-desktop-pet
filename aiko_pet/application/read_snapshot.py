"""Immutable, language-neutral pet data for application read operations."""

from __future__ import annotations

from dataclasses import dataclass

from ..pet.balance import BALANCE
from ..pet.emotions import EmotionalComposition, derive_emotional_state
from ..pet.mind.dialogue_context import FriendshipStage
from ..pet.mood import NeedMoodFactors, calculate_mood_target
from ..pet.moodlet_catalog import MOODLET_CATALOG
from ..pet.moodlet_timing import stage_seconds
from ..pet.moodlets import (
    EmotionalDirection,
    MoodletAttribution,
    MoodletCause,
    MoodletDecay,
    MoodletId,
    MoodletPolarity,
    calculate_moodlet_contributions,
)
from ..pet.needs import NeedCondition, NeedLevels, assess_need_conditions
from ..pet.state import PetState
from ..pet.wish_catalog import WISH_CATALOG
from ..pet.wishes import (
    WishArea,
    WishContext,
    WishGoal,
    WishId,
    WishRestriction,
    WishTargetKind,
    wish_restriction,
)


@dataclass(frozen=True, slots=True)
class MoodletRead:
    """Current stage time, not an invented wall-clock expiry while paused."""

    instance_id: int
    definition_id: MoodletId
    level: int
    polarity: MoodletPolarity
    direction: EmotionalDirection
    attribution: MoodletAttribution
    mood_points: int
    remaining_stage_seconds: float
    remaining_decay_seconds: float
    decay: MoodletDecay
    decay_paused: bool
    recovery_wait_seconds: float | None
    causes: tuple[MoodletCause, ...] = ()


@dataclass(frozen=True, slots=True)
class GameWishRead:
    completed_rounds: int
    required_count: int
    wins: int
    losses: int


@dataclass(frozen=True, slots=True)
class WishRead:
    """An inner wish remains readable regardless of whether it was spoken."""

    instance_id: int
    definition_id: WishId
    area: WishArea
    target_kind: WishTargetKind
    target_id: str
    remaining_seconds: float
    expressed: bool
    restriction: WishRestriction | None
    game: GameWishRead | None
    goal: WishGoal | None = None
    pinned: bool = False


def _moodlet_reads(state: PetState) -> tuple[MoodletRead, ...]:
    result = []
    for episode in state.moodlets.active:
        definition = MOODLET_CATALOG.definitions[episode.definition_id]
        result.append(
            MoodletRead(
                episode.instance_id,
                episode.definition_id,
                episode.level,
                definition.polarity,
                definition.direction,
                episode.attribution,
                definition.level_points[episode.level - 1],
                episode.remaining_seconds,
                sum(stage_seconds(episode, definition)),
                definition.decay,
                episode.decay_paused,
                (
                    max(
                        0,
                        episode.recovery_since
                        + BALANCE.number("moodlets", "recovery_stable_seconds")
                        - state.lived_seconds,
                    )
                    if episode.recovery_since is not None
                    else None
                ),
                episode.causes,
            )
        )
    return tuple(result)


def _wish_reads(state: PetState, context: WishContext) -> tuple[WishRead, ...]:
    result = []
    for wish in state.wishes.active:
        definition = WISH_CATALOG.definitions[wish.definition_id]
        result.append(
            WishRead(
                wish.instance_id,
                wish.definition_id,
                definition.area,
                definition.target_kind,
                wish.target_id,
                max(0, wish.expires_at - state.lived_seconds),
                wish.expressed_at is not None,
                wish_restriction(wish, context, WISH_CATALOG.definitions),
                (
                    GameWishRead(
                        wish.game.completed_rounds,
                        wish.goal_snapshot.required_count,
                        wish.game.wins,
                        wish.game.losses,
                    )
                    if definition.area == WishArea.GAMES
                    else None
                ),
                wish.goal_snapshot,
                wish.pinned,
            )
        )
    return tuple(result)


@dataclass(frozen=True, slots=True)
class PetReadSnapshot:
    """Stable value copy, not a mutable reference to PetState."""

    satiety: float
    mood: float
    energy: float
    social: float
    affection: float
    friendship: float
    friendship_level: int
    sleeping: bool
    meals_date: str
    meals_today: tuple[str, ...]
    lived_seconds: float
    emotions: EmotionalComposition
    need_conditions: frozenset[NeedCondition]
    moodlets: tuple[MoodletRead, ...]
    wishes: tuple[WishRead, ...]
    mood_target: float
    friendship_stage: FriendshipStage
    sleep_reason: str
    contact_absence_seconds: float | None
    last_food_id: str | None = None
    food_digest_minutes: float = 0.0
    fun: float = BALANCE.number("initial", "fun")

    @property
    def needs(self) -> NeedLevels:
        """Exactly five care values; mood and friendship stay separate reads."""
        return NeedLevels(
            self.satiety,
            self.energy,
            self.fun,
            self.social,
            self.affection,
        )


def snapshot_pet(
    state: PetState,
    *,
    wish_context: WishContext = WishContext(),
) -> PetReadSnapshot:
    """Copy a pet's current read-side values, without computing UI text."""
    return PetReadSnapshot(
        satiety=state.satiety,
        mood=state.mood,
        energy=state.energy,
        social=state.social,
        affection=state.affection,
        friendship=state.friendship,
        friendship_level=state.friendship_level,
        sleeping=state.sleeping,
        meals_date=state.meals_date,
        meals_today=tuple(state.meals_today),
        lived_seconds=state.lived_seconds,
        emotions=derive_emotional_state(
            state.mood,
            state.moodlets.active,
            definitions=MOODLET_CATALOG.definitions,
        ),
        need_conditions=assess_need_conditions(state.needs),
        moodlets=_moodlet_reads(state),
        wishes=_wish_reads(state, wish_context),
        mood_target=calculate_mood_target(
            NeedMoodFactors(
                state.satiety, state.energy, state.fun, state.social, state.affection
            ),
            calculate_moodlet_contributions(
                state.moodlets, definitions=MOODLET_CATALOG.definitions,
            ),
        ),
        friendship_stage=FriendshipStage.from_level(state.friendship_level),
        sleep_reason=(
            "care_break"
            if state.sleep_episode.care_break
            else "manual"
            if state.sleeping and state.sleep_origin == "manual"
            else state.sleep_episode.kind or "unknown"
            if state.sleeping
            else "awake"
        ),
        contact_absence_seconds=(
            max(0, state.lived_seconds - state.friendship_history.last_contact)
            if state.friendship_history.last_contact is not None
            else None
        ),
        last_food_id=state.food.last_food_id,
        food_digest_minutes=state.food.remaining_digest_minutes,
        fun=state.fun,
    )
