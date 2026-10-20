"""Immutable wish definitions and aggregate-owned inner wish progress."""

import random
from dataclasses import dataclass, replace
from enum import StrEnum
from typing import Literal, Mapping

from .balance import BALANCE
from .moodlets import MoodletId


class WishId(StrEnum):
    FOOD = "food"
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

    @property
    def label_key(self) -> str:
        return f"wish.{self.id}.label"

    @property
    def description_key(self) -> str:
        return f"wish.{self.id}.description"


@dataclass(frozen=True, slots=True)
class GameWishProgress:
    """Only the bounded objective block, never a board, deck or session score.

    Completed round identities support duplicate detection. A session token
    distinguishes the shared-play objective's single-session progress.
    """

    round_ids: tuple[str, ...] = ()
    wins: int = 0
    losses: int = 0
    session_id: str | None = None


@dataclass(frozen=True, slots=True)
class ActiveWish:
    instance_id: int
    definition_id: WishId
    target_id: str
    created_at: float
    expires_at: float
    expressed_at: float | None = None
    game: GameWishProgress = GameWishProgress()


@dataclass(frozen=True, slots=True)
class WishState:
    """Stable identities and bounded pacing evidence survive removed wishes.

    Removing a fulfilled/ended wish retires its identity; an event for that
    identity cannot find an active wish again after a save/reload. Relationship
    amounts still belong to the existing friendship history, not this record.
    """

    next_instance_id: int = 1
    active: tuple[ActiveWish, ...] = ()
    last_created_by_area: tuple[tuple[WishArea, float], ...] = ()
    last_expressed_at: float | None = None

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
    return _retire_wish(state, wish, definitions[wish.definition_id])


def _retire_wish(
    state: WishState, wish: ActiveWish, fulfilled: WishDefinition | None,
) -> WishResolution:
    return WishResolution(replace(
        state, active=tuple(w for w in state.active
                            if w.instance_id != wish.instance_id),
    ), fulfilled)


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
            return _retire_wish(state, wish, definition)
        progress = GameWishProgress((round_id,), 0, int(outcome == "loss"))
    elif key == WishId.AVOID_ROUND_LOSS:
        return _retire_wish(state, wish, definition if outcome != "loss" else None)
    else:
        before = wish.game
        if key == WishId.PLAY_GAME and before.session_id != session_id:
            before = GameWishProgress(session_id=session_id)
        progress = GameWishProgress(
            (*before.round_ids, round_id), before.wins + (outcome == "win"),
            before.losses + (outcome == "loss"),
            session_id if key == WishId.PLAY_GAME else None,
        )
        if len(progress.round_ids) >= definition.round_count:
            won = (key == WishId.PLAY_GAME
                   or key == WishId.WIN_OVERALL and progress.wins > progress.losses
                   or key == WishId.AVOID_OVERALL_LOSS
                   and progress.wins >= progress.losses)
            return _retire_wish(state, wish, definition if won else None)
    return WishResolution(replace(state, active=tuple(
        replace(w, game=progress) if w.instance_id == instance_id else w
        for w in state.active
    )))


def expire_wishes(state: WishState, *, elapsed: float) -> WishState:
    """Age original deadlines in all time paths; retain identity/pacing evidence."""
    active = tuple(w for w in state.active if elapsed < w.expires_at)
    return replace(state, active=active) if active != state.active else state


def create_wish(
    state: WishState,
    *,
    elapsed: float,
    sleeping: bool,
    context: WishContext,
    definitions: Mapping[WishId, WishDefinition],
    rng: random.Random,
) -> WishState:
    """One current live opportunity, not a reconstruction of missed wishes."""
    state = expire_wishes(state, elapsed=elapsed)
    last = state.last_created_at
    if (
        sleeping
        or len(state.active) >= BALANCE.integer("wishes", "maximum_active")
        or last is not None
        and elapsed - last < BALANCE.integer("wishes", "creation_interval_seconds")
    ):
        return state
    occupied = {definitions[w.definition_id].area for w in state.active}
    anchors = dict(state.last_created_by_area)
    candidates: dict[WishArea, list[tuple[WishDefinition, tuple[str, ...]]]] = {}
    for definition in definitions.values():
        area = definition.area
        if (
            area in occupied
            or area in anchors
            and elapsed - anchors[area]
            < BALANCE.integer("wishes", "same_area_interval_seconds")
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
    if not candidates:
        return state
    area = rng.choice(tuple(candidates))
    definition, targets = rng.choice(candidates[area])
    wish = ActiveWish(
        state.next_instance_id,
        definition.id,
        rng.choice(targets),
        elapsed,
        elapsed + BALANCE.integer("wishes", "lifetime_seconds"),
    )
    anchors[area] = elapsed
    return replace(
        state,
        next_instance_id=state.next_instance_id + 1,
        active=(*state.active, wish),
        last_created_by_area=tuple((a, anchors[a]) for a in WishArea if a in anchors),
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
