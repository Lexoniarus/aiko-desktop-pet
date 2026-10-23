"""Versioned inner wishes and bounded objective progress; no wish decisions."""

from __future__ import annotations

from typing import Any

from ..pet.balance import BALANCE
from ..pet.catalog_validation import (
    enum_value,
    integer_value,
    number_value,
    object_fields,
)
from ..pet.wish_catalog import WISH_CATALOG
from ..pet.wishes import (
    MAX_WISH_ROUND_RECEIPTS,
    ActiveWish,
    GameWishProgress,
    WishArea,
    WishGoal,
    WishId,
    WishObjective,
    WishState,
    WishTargetMode,
    legacy_wish_goal,
)
from .food_handover_codec import decode_food_handovers, encode_food_handovers
from .wish_snapshot_codec import (
    decode_wish_goal as decode_wish_goal,
)
from .wish_snapshot_codec import (
    decode_wish_target,
    encode_wish_target,
)
from .wish_snapshot_codec import (
    encode_wish_goal as encode_wish_goal,
)


def _token(raw: Any) -> str:
    if not isinstance(raw, str) or not 1 <= len(raw) <= 128:
        raise ValueError("Invalid saved game-wish identity")
    return raw


def _game_progress(raw: Any, key: WishId, goal: WishGoal) -> GameWishProgress:
    row = object_fields(raw, ("round_ids", "wins", "losses", "session_id"),
                        optional=("completed_rounds",),
                        context="game wish progress")
    definition = WISH_CATALOG.definitions[key]
    ids = row["round_ids"]
    if not isinstance(ids, list) or len(ids) > MAX_WISH_ROUND_RECEIPTS:
        raise ValueError("Unbounded wish round progress")
    rounds = tuple(_token(v) for v in ids)
    if len(rounds) != len(set(rounds)):
        raise ValueError("Duplicate completed wish round")
    cumulative_wins = goal.objective == WishObjective.TOTAL_WINS
    count = integer_value(row.get("completed_rounds", len(rounds)),
                          minimum=len(rounds),
                          maximum=2**63 - 1 if cumulative_wins else goal.required_count,
                          context="wish completed rounds")
    if (bool(count) != bool(rounds)
            or not cumulative_wins and count != len(rounds)):
        raise ValueError("Wish progress lacks bounded round evidence")
    wins = integer_value(row["wins"], minimum=0, maximum=count,
                         context="wish wins")
    losses = integer_value(row["losses"], minimum=0, maximum=count - wins,
                           context="wish losses")
    if cumulative_wins and wins > goal.required_count:
        raise ValueError("Excess cumulative wish wins")
    session = None if row["session_id"] is None else _token(row["session_id"])
    if (definition.area != WishArea.GAMES and (rounds or session is not None)
            or goal.objective == WishObjective.SESSION_ROUNDS
            and rounds and session is None):
        raise ValueError("Incompatible game wish session/progress")
    return GameWishProgress(rounds, wins, losses, session, count)


def decode_wishes(raw: Any, elapsed: float) -> WishState:
    row = object_fields(raw, (
        "version", "next_instance_id", "active", "last_created_by_area",
        "last_expressed_at",
    ), optional=("refill_not_before", "refresh_at", "food_handovers"), context="wishes")
    if type(row["version"]) is not int or row["version"] != 1:
        raise ValueError("Unsupported saved wish version")
    next_id = integer_value(row["next_instance_id"], minimum=1,
                            maximum=2**63 - 1, context="wishes.next_instance_id")
    anchors = object_fields(row["last_created_by_area"], (), optional=WishArea,
                            context="wish creation pacing")
    created = tuple((area, number_value(anchors[area], minimum=0, maximum=elapsed,
                                        context="wish creation time"))
                    for area in WishArea if area in anchors)
    expressed = (
        None if row["last_expressed_at"] is None else number_value(
            row["last_expressed_at"], minimum=0, maximum=elapsed,
            context="last wish expression",
        )
    )
    if next_id <= len(created) or (expressed is not None and not created):
        raise ValueError("Wish allocation/expression lacks creation evidence")
    rows = row["active"]
    if (not isinstance(rows, list)
            or len(rows) > BALANCE.integer("wishes", "maximum_active")):
        raise ValueError("Unbounded active wishes")
    active: list[ActiveWish] = []
    instances: set[int] = set()
    goals: set[tuple[WishId, WishGoal, WishTargetMode, str]] = set()
    for value in rows:
        entry = object_fields(value, (
            "instance_id", "definition_id", "target_id", "created_at", "expires_at",
            "expressed_at", "game",
        ), optional=("goal", "pinned", "target"), context="active wish")
        instance = integer_value(entry["instance_id"], minimum=1,
                                 maximum=next_id - 1, context="wish instance")
        key = enum_value(entry["definition_id"], WishId, context="wish objective")
        definition = WISH_CATALOG.definitions[key]
        if "goal" in entry:
            goal = decode_wish_goal(entry["goal"], key)
        else:
            goal = legacy_wish_goal(key)
        pinned = entry.get("pinned", False)
        if type(pinned) is not bool:
            raise ValueError("Wish pin must be a boolean")
        reference = entry["target_id"]
        target = (None if entry.get("target") is None
                  else decode_wish_target(entry["target"], key))
        if (not isinstance(reference, str)
                or target is None and reference not in definition.targets
                or target is not None and reference != (target.target_id or "")):
            raise ValueError("Unknown or incompatible wish target")
        signature = (key, goal, target.mode if target else WishTargetMode.EXACT,
                     reference)
        if instance in instances or signature in goals:
            raise ValueError("Duplicate wish instance or goal")
        start = number_value(entry["created_at"], minimum=0, maximum=elapsed,
                             context="wish creation")
        end = number_value(entry["expires_at"], minimum=start,
                           maximum=start + BALANCE.integer(
                               "wishes", "lifetime_seconds",
                           ),
                           context="wish deadline")
        if end <= start or dict(created).get(definition.area, -1) < start:
            raise ValueError("Missing wish creation anchor or empty lifetime")
        spoken = (
            None if entry["expressed_at"] is None else number_value(
                entry["expressed_at"], minimum=start,
                maximum=elapsed if pinned else min(end, elapsed),
                context="wish expression",
            )
        )
        if spoken is not None and (expressed is None or expressed < spoken):
            raise ValueError("Missing last wish expression evidence")
        active.append(ActiveWish(
            instance, key, reference, start, end, spoken,
            _game_progress(entry["game"], key, goal), goal, pinned, target,
        ))
        instances.add(instance)
        goals.add(signature)
    refill = (None if row.get("refill_not_before") is None else number_value(
        row["refill_not_before"], minimum=0,
        maximum=elapsed + BALANCE.integer("wishes", "refill_delay_seconds"),
        context="wish refill deadline",
    ))
    if refill is not None and not created:
        raise ValueError("Wish refill lacks creation evidence")
    refresh = None if row.get("refresh_at") is None else number_value(
        row["refresh_at"], minimum=0,
        maximum=elapsed + max(BALANCE.integer("wishes", "refresh_interval_seconds"),
                              BALANCE.integer("wishes", "refill_delay_seconds")),
        context="shared wish refresh deadline",
    )
    if refill is not None and refresh is not None and refill != refresh:
        raise ValueError("Conflicting legacy and shared wish refresh deadlines")
    if refresh is None:
        refresh = refill
    handovers = decode_food_handovers(row.get("food_handovers", []), elapsed, next_id)
    return WishState(next_id, tuple(active), created, expressed, refresh, handovers)


def valid_wishes(raw: Any, elapsed: float) -> bool:
    try:
        decode_wishes(raw, elapsed)
    except (ValueError, TypeError, OverflowError):
        return False
    return True


def encode_wishes(state: WishState) -> dict[str, Any]:
    return dict(
        version=1, next_instance_id=state.next_instance_id,
        last_created_by_area={a.value: at for a, at in state.last_created_by_area},
        last_expressed_at=state.last_expressed_at,
        refresh_at=state.refresh_at,
        food_handovers=encode_food_handovers(state.food_handovers),
        active=[dict(
            instance_id=w.instance_id, definition_id=w.definition_id.value,
            target_id=w.target_id, created_at=w.created_at, expires_at=w.expires_at,
            expressed_at=w.expressed_at,
            goal=encode_wish_goal(w.goal_snapshot), pinned=w.pinned,
            target=None if w.target is None else encode_wish_target(w.target),
            game=dict(round_ids=list(w.game.round_ids), wins=w.game.wins,
                      losses=w.game.losses, session_id=w.game.session_id,
                      completed_rounds=w.game.completed_rounds),
        ) for w in state.active],
    )
