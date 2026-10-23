"""Immutable wish definitions and aggregate-owned inner wish progress."""

from dataclasses import dataclass, replace
from enum import StrEnum
from typing import Literal, Mapping

from .balance import BALANCE
from .food_handover import FoodHandoverReceipt
from .moodlets import (
    MoodletCause,
    MoodletCauseKind,
    MoodletGameResult,
    MoodletId,
    MoodletOutcome,
    MoodletWishCause,
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
    """Current capabilities/acceptance, never proof of World stock or contact."""

    online_social: bool = False
    prepared_social: frozenset[str] = frozenset()
    petting_welcome: bool = True
    games_ready: bool = True
    crowded: bool = False
    repetitive_food: str | None = None


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


def _wish_cause(
    wish: ActiveWish, *, elapsed: float, event_id: str, outcome: MoodletOutcome,
    failed: bool = False, target_id: str | None = None,
    object_id: str | None = None, game: MoodletGameResult | None = None,
) -> MoodletCause:
    goal = wish.goal_snapshot
    return MoodletCause(
        MoodletCauseKind.WISH_FAILED if failed else MoodletCauseKind.WISH_FULFILLED,
        elapsed, event_id,
        wish=MoodletWishCause(wish.instance_id, wish.definition_id.value,
                             wish.target_id, goal.objective.value, goal.required_count,
                             target=wish.target),
        target_id=wish.target_id if target_id is None else target_id,
        outcome=outcome, object_id=object_id, game=game,
    )


def fulfill_activity_wish(
    state: WishState, area: WishArea, target_id: str, *, elapsed: float,
    definitions: Mapping[WishId, WishDefinition], instance_id: int | None = None,
    object_id: str | None = None,
) -> WishResolution:
    """Called only after actual accepted intake/care or full social completion."""
    wish = next((w for w in state.active
                 if definitions[w.definition_id].area == area
                 and w.target_id == target_id
                 and w.goal_snapshot.objective != WishObjective.FOOD_HANDOVER
                 and (instance_id is None or w.instance_id == instance_id)
                 and w.is_active_at(elapsed)), None)
    if wish is None:
        return WishResolution(state)
    return _retire_wish(
        state, wish, definitions[wish.definition_id], elapsed=elapsed,
        cause=_wish_cause(wish, elapsed=elapsed,
                          event_id=f"wish:{wish.instance_id}:fulfilled",
                          outcome=MoodletOutcome.INTAKE if area == WishArea.FOOD
                          else MoodletOutcome.COMPLETED, object_id=object_id),
    )


def fulfill_food_handover_wish(
    state: WishState, food_id: str, *, elapsed: float, object_id: str,
    definitions: Mapping[WishId, WishDefinition],
) -> WishResolution:
    """A qualified personal offer resolves avoidance, never ordinary intake wishes."""
    wish = next((w for w in state.active
                 if w.goal_snapshot.objective == WishObjective.FOOD_HANDOVER
                 and definitions[w.definition_id].area == WishArea.FOOD
                 and food_id in definitions[w.definition_id].targets
                 and w.is_active_at(elapsed)), None)
    if wish is None:
        return WishResolution(state)
    return _retire_wish(
        state, wish, definitions[wish.definition_id], elapsed=elapsed,
        cause=_wish_cause(wish, elapsed=elapsed,
                          event_id=f"wish:{wish.instance_id}:handover",
                          outcome=MoodletOutcome.HANDOVER, target_id=food_id,
                          object_id=object_id),
    )


def _retire_wish(
    state: WishState, wish: ActiveWish, fulfilled: WishDefinition | None,
    *, elapsed: float, cause: MoodletCause | None = None,
) -> WishResolution:
    return WishResolution(replace(
        state, active=tuple(w for w in state.active
                            if w.instance_id != wish.instance_id),
        refresh_at=_refresh_deadline(state, elapsed),
    ), fulfilled, cause)


def _game_result(
    goal: WishGoal, progress: GameWishProgress, outcome: Literal["win", "loss", "draw"],
) -> tuple[bool, bool, MoodletOutcome]:
    """Completion and success are properties of the original goal, not its ID."""
    objective = goal.objective
    if objective in (WishObjective.RETRY_WIN, WishObjective.NEXT_WIN):
        won = outcome == "win"
        return won or objective == WishObjective.NEXT_WIN, won, MoodletOutcome(outcome)
    if objective == WishObjective.NEXT_NON_LOSS:
        return True, outcome != "loss", MoodletOutcome(outcome)
    if objective == WishObjective.TOTAL_WINS:
        return progress.wins >= goal.required_count, True, MoodletOutcome.WIN
    if objective in (WishObjective.SESSION_ROUNDS, WishObjective.TOTAL_ROUNDS):
        return (progress.completed_rounds >= goal.required_count, True,
                MoodletOutcome.COMPLETED)
    if objective not in (WishObjective.BLOCK_MAJORITY, WishObjective.BLOCK_NON_LOSS):
        raise ValueError("Unsupported game wish objective")
    result = (MoodletOutcome.WIN if progress.wins > progress.losses
              else MoodletOutcome.DRAW if progress.wins == progress.losses
              else MoodletOutcome.LOSS)
    success = (result == MoodletOutcome.WIN or result == MoodletOutcome.DRAW
               and objective == WishObjective.BLOCK_NON_LOSS)
    return progress.completed_rounds >= goal.required_count, success, result


def _refresh_deadline(state: WishState, elapsed: float) -> float:
    """Retirement keeps the shared refresh; legacy states acquire one deadline."""
    return (state.refresh_at if state.refresh_at is not None else
            elapsed + BALANCE.integer("wishes", "refresh_interval_seconds"))


def progress_game_wish(
    state: WishState, instance_id: int, *, game_id: str, session_id: str,
    round_id: str, started_at: float, elapsed: float,
    outcome: Literal["win", "loss", "draw"],
    definitions: Mapping[WishId, WishDefinition],
) -> WishResolution:
    """One real qualifying round, from Aiko's perspective; no session score."""
    wish = next((w for w in state.active if w.instance_id == instance_id), None)
    if (wish is None or wish.target_id != game_id
            or definitions[wish.definition_id].area != WishArea.GAMES
            or not wish.created_at <= started_at <= elapsed
            or not wish.is_active_at(elapsed)
            or round_id in wish.game.round_ids):
        return WishResolution(state)
    definition, goal = definitions[wish.definition_id], wish.goal_snapshot
    before = wish.game
    if (goal.objective == WishObjective.RETRY_WIN
            or goal.objective == WishObjective.SESSION_ROUNDS
            and before.session_id != session_id):
        before = GameWishProgress()
    if before.completed_rounds >= 2**63 - 1:
        raise ValueError("Wish attempt count exhausted")
    progress = GameWishProgress(
        (*before.round_ids, round_id)[-MAX_WISH_ROUND_RECEIPTS:],
        before.wins + (outcome == "win"), before.losses + (outcome == "loss"),
        session_id if goal.objective == WishObjective.SESSION_ROUNDS else None,
        before.completed_rounds + 1,
    )
    finished, success, result = _game_result(goal, progress, outcome)
    if finished:
        disappointed = (not success and goal.objective in (
            WishObjective.NEXT_NON_LOSS, WishObjective.BLOCK_NON_LOSS,
        ))
        cause = (_wish_cause(
            wish, elapsed=elapsed, event_id=round_id, outcome=result,
            failed=disappointed, game=MoodletGameResult(
                MoodletOutcome(outcome), progress.completed_rounds,
                progress.wins, progress.losses,
            ),
        ) if success or disappointed else None)
        return _retire_wish(state, wish, definition if success else None,
                            elapsed=elapsed, cause=cause)
    return WishResolution(replace(state, active=tuple(
        replace(w, game=progress) if w.instance_id == instance_id else w
        for w in state.active
    )))


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
    deadline = _refresh_deadline(state, elapsed)
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
    return state if wish is None else _retire_wish(
        state, wish, None, elapsed=elapsed,
    ).state


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
