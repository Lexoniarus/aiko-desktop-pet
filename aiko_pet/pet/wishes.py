"""Immutable wish definitions and aggregate-owned inner wish progress."""

import random
from dataclasses import dataclass, replace
from enum import StrEnum
from typing import Literal, Mapping

from .balance import BALANCE
from .moodlets import MoodletId

MAX_WISH_ROUND_RECEIPTS = 100


class WishId(StrEnum):
    FOOD = "food"
    AVOID_FOOD = "avoid_food"
    PLAY_GAME = "play_game"
    WIN_ROUND = "win_round"
    AVOID_ROUND_LOSS = "avoid_round_loss"
    WIN_OVERALL = "win_overall"
    AVOID_OVERALL_LOSS = "avoid_overall_loss"
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
    if key == WishId.AVOID_FOOD:
        raise ValueError("Food avoidance has no legacy objective")
    return WishGoal(WishObjective.ACTIVITY, 0)


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

    Older constructors keep delivered v1 meanings; new creation must supply
    its catalogue goal explicitly when the corresponding rules are wired.
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

    def __post_init__(self) -> None:
        if self.goal is None:
            object.__setattr__(self, "goal", legacy_wish_goal(self.definition_id))

    @property
    def goal_snapshot(self) -> WishGoal:
        """An instance's original objective survives later catalogue changes."""
        assert self.goal is not None
        return self.goal


@dataclass(frozen=True, slots=True)
class WishState:
    """Stable identities, creation evidence and a refill deadline survive retirement.

    Removing a fulfilled/ended wish retires its identity; an event for that
    identity cannot find an active wish again after a save/reload. Relationship
    amounts still belong to the existing friendship history, not this record.
    """

    next_instance_id: int = 1
    active: tuple[ActiveWish, ...] = ()
    last_created_by_area: tuple[tuple[WishArea, float], ...] = ()
    last_expressed_at: float | None = None
    refill_not_before: float | None = None

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


def fulfill_activity_wish(
    state: WishState, area: WishArea, target_id: str, *, elapsed: float,
    definitions: Mapping[WishId, WishDefinition], instance_id: int | None = None,
) -> WishResolution:
    """Called only after actual accepted intake/care or full social completion."""
    wish = next((w for w in state.active
                 if definitions[w.definition_id].area == area
                 and w.target_id == target_id
                 and (instance_id is None or w.instance_id == instance_id)
                 and w.created_at <= elapsed < w.expires_at), None)
    if wish is None:
        return WishResolution(state)
    return _retire_wish(state, wish, definitions[wish.definition_id], elapsed=elapsed)


def _retire_wish(
    state: WishState, wish: ActiveWish, fulfilled: WishDefinition | None,
    *, elapsed: float,
) -> WishResolution:
    return WishResolution(replace(
        state, active=tuple(w for w in state.active
                            if w.instance_id != wish.instance_id),
        refill_not_before=_refill_deadline(state, elapsed),
    ), fulfilled)


def _refill_deadline(state: WishState, elapsed: float) -> float:
    """One vacancy starts a pause; later retirements cannot postpone it."""
    return (state.refill_not_before if state.refill_not_before is not None else
            elapsed + BALANCE.integer("wishes", "refill_delay_seconds"))


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
            or not wish.created_at <= started_at <= elapsed < wish.expires_at
            or round_id in wish.game.round_ids):
        return WishResolution(state)
    definition = definitions[wish.definition_id]
    key = definition.id
    if key == WishId.WIN_ROUND:
        if outcome == "win":
            return _retire_wish(state, wish, definition, elapsed=elapsed)
        progress = GameWishProgress((round_id,), 0, int(outcome == "loss"))
    elif key == WishId.AVOID_ROUND_LOSS:
        return _retire_wish(state, wish, definition if outcome != "loss" else None,
                            elapsed=elapsed)
    else:
        before = wish.game
        if key == WishId.PLAY_GAME and before.session_id != session_id:
            before = GameWishProgress(session_id=session_id)
        progress = GameWishProgress(
            (*before.round_ids, round_id), before.wins + (outcome == "win"),
            before.losses + (outcome == "loss"),
            session_id if key == WishId.PLAY_GAME else None,
        )
        if len(progress.round_ids) >= wish.goal_snapshot.required_count:
            won = (key == WishId.PLAY_GAME
                   or key == WishId.WIN_OVERALL and progress.wins > progress.losses
                   or key == WishId.AVOID_OVERALL_LOSS
                   and progress.wins >= progress.losses)
            return _retire_wish(state, wish, definition if won else None,
                                elapsed=elapsed)
    return WishResolution(replace(state, active=tuple(
        replace(w, game=progress) if w.instance_id == instance_id else w
        for w in state.active
    )))


def expire_wishes(state: WishState, *, elapsed: float) -> WishState:
    """Age original deadlines in all time paths; retain identity/pacing evidence."""
    active = tuple(w for w in state.active if elapsed < w.expires_at)
    if active == state.active:
        return state
    first_expiry = min(w.expires_at for w in state.active if elapsed >= w.expires_at)
    return replace(state, active=active,
                   refill_not_before=_refill_deadline(state, first_expiry))


def replenish_wishes(
    state: WishState,
    *,
    elapsed: float,
    sleeping: bool,
    context: WishContext,
    definitions: Mapping[WishId, WishDefinition],
    rng: random.Random,
) -> WishState:
    """Fill the normal three-slot stock at this awake live endpoint only."""
    state = expire_wishes(state, elapsed=elapsed)
    if (
        sleeping
        or len(state.active) >= BALANCE.integer("wishes", "maximum_active")
        or state.refill_not_before is not None and elapsed < state.refill_not_before
    ):
        return state
    occupied = {definitions[w.definition_id].area for w in state.active}
    anchors = dict(state.last_created_by_area)
    candidates: dict[WishArea, list[tuple[WishDefinition, tuple[str, ...]]]] = {}
    for definition in definitions.values():
        area = definition.area
        if (
            definition.selection_weight == 0
            or area in occupied
            or area == WishArea.AFFECTION
            and context.crowded
            or definition.id in (WishId.SINGLE, WishId.TWO_PARTS, WishId.FACT)
            and not context.online_social
        ):
            continue
        targets = tuple(
            t
            for t in definition.targets
            if area != WishArea.FOOD or t != context.repetitive_food
        )
        if targets:
            candidates.setdefault(area, []).append((definition, targets))
    active = list(state.active)
    next_id = state.next_instance_id
    while candidates and len(active) < BALANCE.integer("wishes", "maximum_active"):
        area = rng.choice(tuple(candidates))
        definition, targets = rng.choice(candidates.pop(area))
        if next_id >= 2**63 - 1:
            raise ValueError("Wish instance allocation exhausted")
        active.append(ActiveWish(
            next_id, definition.id, rng.choice(targets), elapsed,
            elapsed + BALANCE.integer("wishes", "lifetime_seconds"),
        ))
        next_id += 1
        anchors[area] = elapsed
    return replace(
        state,
        next_instance_id=next_id,
        active=tuple(active),
        last_created_by_area=tuple((a, anchors[a]) for a in WishArea if a in anchors),
        refill_not_before=None,
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
            if w.created_at <= elapsed < w.expires_at
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
        or not wish.created_at <= elapsed < wish.expires_at
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
