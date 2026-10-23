"""Immutable wish definitions and aggregate-owned inner wish progress."""

from dataclasses import dataclass, replace
from enum import StrEnum
from typing import Literal, Mapping

from .balance import BALANCE
from .care_evidence import CareExperience
from .food_handover import FoodHandoverReceipt
from .moodlets import (
    MoodletCause,
    MoodletId,
)

MAX_WISH_ROUND_RECEIPTS = 100


class WishId(StrEnum):
    FOOD = "food"
    AVOID_FOOD = "avoid_food"
    PLAY_GAME = "play_game"
    WIN_ROUND = "win_round"
    AVOID_ROUND_LOSS = "avoid_round_loss"
    WIN_OVERALL = "win_overall"
    AVOID_OVERALL_LOSS = "avoid_overall_loss"
    PLAY_ANY_GAME = "play_any_game"
    PLAY_OTHER_GAME = "play_other_game"
    REMATCH_GAME = "rematch_game"
    COMEBACK_GAME = "comeback_game"
    SOCIAL_ANY = "social_any"
    CHAT = "chat"
    SINGLE = "single"
    TWO_PARTS = "twopart"
    FACT = "fact"
    PET = "pet"


class WishArea(StrEnum):
    FOOD = "food"
    GAMES = "games"
    SOCIAL = "social"
    AFFECTION = "affection"


class WishTargetKind(StrEnum):
    FOOD = "food"
    GAME = "game"
    SOCIAL = "social"
    CARE = "care"


class WishTargetMode(StrEnum):
    EXACT = "exact"
    ANY = "any"
    EXCLUDE = "exclude"


@dataclass(frozen=True, slots=True)
class WishTarget:
    """A fixed target meaning, independent of the activity eventually chosen."""

    kind: WishTargetKind
    mode: WishTargetMode
    target_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.kind, WishTargetKind) or not isinstance(
            self.mode, WishTargetMode,
        ):
            raise ValueError("Wish target requires typed kind and mode")
        if self.mode == WishTargetMode.ANY:
            if self.target_id is not None:
                raise ValueError("Free-choice wish cannot bind a concrete target")
        elif not isinstance(self.target_id, str) or not self.target_id:
            raise ValueError("Concrete/excluded wish requires a reference target")

    def matches(self, kind: WishTargetKind, target_id: str) -> bool:
        """Match a validated activity identity within the same target kind."""
        if kind != self.kind or not target_id:
            return False
        if self.mode == WishTargetMode.ANY:
            return True
        if self.mode == WishTargetMode.EXCLUDE:
            return target_id != self.target_id
        return target_id == self.target_id


class WishExperienceKind(StrEnum):
    RECENT_PLAY = "recent_play"
    LAST_ROUND_LOSS = "last_round_loss"


@dataclass(frozen=True, slots=True)
class WishExperienceRequirement:
    """Creation prerequisite data, not evidence that the experience happened."""

    kind: WishExperienceKind
    window_seconds: int
    weight_multiplier: float


class WishObjective(StrEnum):
    """Stable goal meanings, independent of a catalogue ID's current wording."""

    FOOD_INTAKE = "food_intake"
    FOOD_HANDOVER = "food_handover"
    ACTIVITY = "activity"
    SESSION_ROUNDS = "session_rounds"
    TOTAL_ROUNDS = "total_rounds"
    RETRY_WIN = "retry_win"
    NEXT_WIN = "next_win"
    NEXT_NON_LOSS = "next_non_loss"
    BLOCK_MAJORITY = "block_majority"
    TOTAL_WINS = "total_wins"
    BLOCK_NON_LOSS = "block_non_loss"


@dataclass(frozen=True, slots=True)
class WishGoal:
    objective: WishObjective
    required_count: int


GAME_GOAL_TEXT_VARIANTS = (
    WishObjective.TOTAL_ROUNDS, WishObjective.NEXT_WIN, WishObjective.TOTAL_WINS,
)


def wish_text_key(
    key: WishId, goal: WishGoal | None,
    field: Literal["label", "description", "utterance"],
) -> str:
    """Preserve original goal wording when a catalogue ID acquires a new meaning."""
    prefix = (f"wish.goal.{goal.objective}" if goal is not None
              and key in (WishId.PLAY_GAME, WishId.WIN_ROUND, WishId.WIN_OVERALL)
              and goal.objective in GAME_GOAL_TEXT_VARIANTS else f"wish.{key}")
    return f"{prefix}.{field}"


def legacy_wish_goal(key: WishId) -> WishGoal:
    """Freeze the delivered v1 semantics without consulting a mutable catalogue."""
    games = {
        WishId.PLAY_GAME: WishGoal(WishObjective.SESSION_ROUNDS, 2),
        WishId.WIN_ROUND: WishGoal(WishObjective.RETRY_WIN, 1),
        WishId.AVOID_ROUND_LOSS: WishGoal(WishObjective.NEXT_NON_LOSS, 1),
        WishId.WIN_OVERALL: WishGoal(WishObjective.BLOCK_MAJORITY, 3),
        WishId.AVOID_OVERALL_LOSS: WishGoal(WishObjective.BLOCK_NON_LOSS, 3),
    }
    if key in games:
        return games[key]
    if key == WishId.FOOD:
        return WishGoal(WishObjective.FOOD_INTAKE, 0)
    if key in (WishId.CHAT, WishId.SINGLE, WishId.TWO_PARTS, WishId.FACT, WishId.PET):
        return WishGoal(WishObjective.ACTIVITY, 0)
    raise ValueError("Wish form has no legacy objective")


@dataclass(frozen=True, slots=True)
class WishDefinition:
    """Supported targets and a fulfillment outcome; no deadlines or progress."""

    id: WishId
    area: WishArea
    target_kind: WishTargetKind
    targets: tuple[str, ...]
    fulfillment_moodlet: MoodletId
    fulfillment_level: int
    round_count: int
    goal: WishGoal
    selection_weight: int
    target_mode: WishTargetMode = WishTargetMode.EXACT
    experience: WishExperienceRequirement | None = None

    def bind_target(self, target_id: str | None = None) -> WishTarget:
        """Freeze a concrete/excluded reference without choosing a free target."""
        target = WishTarget(self.target_kind, self.target_mode, target_id)
        if target_id is not None and target_id not in self.targets:
            raise ValueError("Wish target is outside its supported activity pool")
        return target

    @property
    def label_key(self) -> str:
        return f"wish.{self.id}.label"

    @property
    def description_key(self) -> str:
        return f"wish.{self.id}.description"


@dataclass(frozen=True, slots=True)
class GameWishProgress:
    """Bounded round receipts plus counts, never a board, deck or session score.

    A total count need not grow receipt storage for a long-pinned goal. The
    session token preserves the older shared-play single-session objective.
    """

    round_ids: tuple[str, ...] = ()
    wins: int = 0
    losses: int = 0
    session_id: str | None = None
    completed_rounds: int = 0

    def __post_init__(self) -> None:
        if self.completed_rounds == 0 and self.round_ids:
            object.__setattr__(self, "completed_rounds", len(self.round_ids))


@dataclass(frozen=True, slots=True)
class ActiveWish:
    """An original goal, pin and progress owned by the existing pet aggregate.

    Older constructors keep delivered v1 meanings; current creation supplies
    its catalogue goal explicitly alongside the matching resolution rules.
    """

    instance_id: int
    definition_id: WishId
    target_id: str
    created_at: float
    expires_at: float
    expressed_at: float | None = None
    game: GameWishProgress = GameWishProgress()
    goal: WishGoal | None = None
    pinned: bool = False
    target: WishTarget | None = None

    def __post_init__(self) -> None:
        if self.goal is None:
            object.__setattr__(self, "goal", legacy_wish_goal(self.definition_id))
        if self.target is not None and self.target_id != (self.target.target_id or ""):
            raise ValueError("Wish reference must agree with its original typed target")

    @property
    def goal_snapshot(self) -> WishGoal:
        """An instance's original objective survives later catalogue changes."""
        assert self.goal is not None
        return self.goal

    def is_active_at(self, elapsed: float) -> bool:
        """Pinning protects the original identity without moving its deadline."""
        return self.created_at <= elapsed and (self.pinned or elapsed < self.expires_at)


@dataclass(frozen=True, slots=True)
class WishState:
    """Stable identities and the single refresh deadline survive retirement.

    Removing a fulfilled/ended wish retires its identity; an event for that
    identity cannot find an active wish again after a save/reload. Relationship
    amounts still belong to the existing friendship history, not this record.
    """

    next_instance_id: int = 1
    active: tuple[ActiveWish, ...] = ()
    last_created_by_area: tuple[tuple[WishArea, float], ...] = ()
    last_expressed_at: float | None = None
    refresh_at: float | None = None
    food_handovers: tuple[FoodHandoverReceipt, ...] = ()

    @property
    def last_created_at(self) -> float | None:
        return max((stamp for _, stamp in self.last_created_by_area), default=None)


@dataclass(frozen=True, slots=True)
class WishContext:
    """Capabilities and bounded actual play context, without World-stock inference."""

    online_social: bool = False
    prepared_social: frozenset[str] = frozenset()
    petting_welcome: bool = True
    games_ready: bool = True
    crowded: bool = False
    repetitive_food: str | None = None
    petting_refused: bool = False
    recent_play: CareExperience | None = None


class WishRestriction(StrEnum):
    ONLINE_UNAVAILABLE = "online_unavailable"
    PETTING_UNWELCOME = "petting_unwelcome"
    GAME_TIRED = "game_tired"


@dataclass(frozen=True, slots=True)
class WishResolution:
    """Retired/progressed state and its one qualifying emotional outcome."""

    state: WishState
    fulfilled: WishDefinition | None = None
    cause: MoodletCause | None = None


def wish_refresh_deadline(state: WishState, elapsed: float) -> float:
    """Retirement keeps the shared refresh; legacy states acquire one deadline."""
    return (state.refresh_at if state.refresh_at is not None else
            elapsed + BALANCE.integer("wishes", "refresh_interval_seconds"))


def expire_wishes(state: WishState, *, elapsed: float) -> WishState:
    """Expire unprotected desires without generating wishes or moving the clock."""
    active = tuple(w for w in state.active if w.pinned or elapsed < w.expires_at)
    if active == state.active:
        return state
    first_expiry = min(w.expires_at for w in state.active
                       if not w.pinned and elapsed >= w.expires_at)
    return replace(state, active=active,
                   refresh_at=state.refresh_at if state.refresh_at is not None
                   else first_expiry)


def set_wish_pinned(
    state: WishState, instance_id: int, pinned: bool, *, elapsed: float,
) -> WishState:
    """Unpin until the next refresh, independent of obsolete four-hour expiry."""
    if type(pinned) is not bool:
        raise ValueError("Wish pin must be a boolean")
    state = expire_wishes(state, elapsed=elapsed)
    wish = next((w for w in state.active if w.instance_id == instance_id
                 and w.is_active_at(elapsed)), None)
    if wish is None or wish.pinned == pinned:
        return state
    deadline = wish_refresh_deadline(state, elapsed)
    if deadline <= elapsed:
        deadline = elapsed + BALANCE.integer("wishes", "refresh_interval_seconds")
    return replace(state, active=tuple(
        replace(w, pinned=pinned, expires_at=w.expires_at if pinned else deadline)
        if w.instance_id == instance_id else w
        for w in state.active
    ))


def dismiss_wish(state: WishState, instance_id: int, *, elapsed: float) -> WishState:
    """Manual retirement is neutral and uses the same vacancy/refill owner."""
    state = expire_wishes(state, elapsed=elapsed)
    wish = next((w for w in state.active if w.instance_id == instance_id
                 and w.is_active_at(elapsed)), None)
    return state if wish is None else replace(
        state, active=tuple(w for w in state.active if w.instance_id != instance_id),
        refresh_at=wish_refresh_deadline(state, elapsed),
    )


def wish_restriction(
    wish: ActiveWish,
    context: WishContext,
    definitions: Mapping[WishId, WishDefinition],
) -> WishRestriction | None:
    """Readable temporary restrictions, also reusable by the later status UI."""
    if wish.definition_id in (WishId.SINGLE, WishId.TWO_PARTS, WishId.FACT) and (
        not context.online_social or wish.target_id not in context.prepared_social
    ):
        return WishRestriction.ONLINE_UNAVAILABLE
    if wish.definition_id == WishId.PET and not context.petting_welcome:
        return WishRestriction.PETTING_UNWELCOME
    if (
        definitions[wish.definition_id].area == WishArea.GAMES
        and not context.games_ready
    ):
        return WishRestriction.GAME_TIRED
    return None


def wish_to_express(
    state: WishState,
    *,
    elapsed: float,
    sleeping: bool,
    friendship_level: int,
    mood: float,
    context: WishContext,
    definitions: Mapping[WishId, WishDefinition],
) -> ActiveWish | None:
    """Select an unspoken wish; actual speech admission remains application-owned."""
    if (
        sleeping
        or friendship_level < BALANCE.integer("wishes", "disclosure_friendship_level")
        or mood < BALANCE.number("wishes", "disclosure_mood_threshold")
        or state.last_expressed_at is not None
        and elapsed - state.last_expressed_at
        < BALANCE.integer("wishes", "disclosure_interval_seconds")
    ):
        return None
    return min(
        (
            w
            for w in state.active
            if w.is_active_at(elapsed)
            and w.expressed_at is None
            and wish_restriction(w, context, definitions) is None
        ),
        key=lambda w: (w.created_at, w.instance_id),
        default=None,
    )


def acknowledge_wish_expression(
    state: WishState,
    instance_id: int,
    *,
    elapsed: float,
) -> WishState:
    """A concrete presented cue acknowledges one live identity, exactly once."""
    wish = next((w for w in state.active if w.instance_id == instance_id), None)
    if (
        wish is None
        or wish.expressed_at is not None
        or not wish.is_active_at(elapsed)
        or state.last_expressed_at is not None
        and elapsed - state.last_expressed_at
        < BALANCE.integer("wishes", "disclosure_interval_seconds")
    ):
        return state
    return replace(
        state,
        last_expressed_at=elapsed,
        active=tuple(
            replace(w, expressed_at=elapsed) if w.instance_id == instance_id else w
            for w in state.active
        ),
    )
