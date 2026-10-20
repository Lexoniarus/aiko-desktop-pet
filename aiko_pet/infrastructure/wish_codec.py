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
from ..pet.wishes import ActiveWish, GameWishProgress, WishArea, WishId, WishState


def _token(raw: Any) -> str:
    if not isinstance(raw, str) or not 1 <= len(raw) <= 128:
        raise ValueError("Invalid saved game-wish identity")
    return raw


def _game_progress(raw: Any, key: WishId) -> GameWishProgress:
    row = object_fields(raw, ("round_ids", "wins", "losses", "session_id"),
                        context="game wish progress")
    definition = WISH_CATALOG.definitions[key]
    ids = row["round_ids"]
    if not isinstance(ids, list) or len(ids) > definition.round_count:
        raise ValueError("Unbounded wish round progress")
    rounds = tuple(_token(v) for v in ids)
    if len(rounds) != len(set(rounds)):
        raise ValueError("Duplicate completed wish round")
    wins = integer_value(row["wins"], minimum=0, maximum=len(rounds),
                         context="wish wins")
    losses = integer_value(row["losses"], minimum=0, maximum=len(rounds) - wins,
                           context="wish losses")
    session = None if row["session_id"] is None else _token(row["session_id"])
    if (definition.area != WishArea.GAMES and (rounds or session is not None)
            or key == WishId.PLAY_GAME and rounds and session is None):
        raise ValueError("Incompatible game wish session/progress")
    return GameWishProgress(rounds, wins, losses, session)


def decode_wishes(raw: Any, elapsed: float) -> WishState:
    row = object_fields(raw, (
        "version", "next_instance_id", "active", "last_created_by_area",
        "last_expressed_at",
    ), optional=("refill_not_before",), context="wishes")
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
    areas: set[WishArea] = set()
    for value in rows:
        entry = object_fields(value, (
            "instance_id", "definition_id", "target_id", "created_at", "expires_at",
            "expressed_at", "game",
        ), context="active wish")
        instance = integer_value(entry["instance_id"], minimum=1,
                                 maximum=next_id - 1, context="wish instance")
        key = enum_value(entry["definition_id"], WishId, context="wish objective")
        definition = WISH_CATALOG.definitions[key]
        if instance in instances or definition.area in areas:
            raise ValueError("Duplicate wish instance or area")
        target = entry["target_id"]
        if not isinstance(target, str) or target not in definition.targets:
            raise ValueError("Unknown or incompatible wish target")
        start = number_value(entry["created_at"], minimum=0, maximum=elapsed,
                             context="wish creation")
        end = number_value(entry["expires_at"], minimum=start,
                           maximum=start + BALANCE.integer(
                               "wishes", "lifetime_seconds",
                           ),
                           context="wish deadline")
        if end <= start or dict(created).get(definition.area) != start:
            raise ValueError("Missing wish creation anchor or empty lifetime")
        spoken = (
            None if entry["expressed_at"] is None else number_value(
                entry["expressed_at"], minimum=start, maximum=min(end, elapsed),
                context="wish expression",
            )
        )
        if spoken is not None and (expressed is None or expressed < spoken):
            raise ValueError("Missing last wish expression evidence")
        active.append(ActiveWish(instance, key, target, start, end, spoken,
                                 _game_progress(entry["game"], key)))
        instances.add(instance)
        areas.add(definition.area)
    refill = (None if row.get("refill_not_before") is None else number_value(
        row["refill_not_before"], minimum=0,
        maximum=elapsed + BALANCE.integer("wishes", "refill_delay_seconds"),
        context="wish refill deadline",
    ))
    if refill is not None and not created:
        raise ValueError("Wish refill lacks creation evidence")
    return WishState(next_id, tuple(active), created, expressed, refill)


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
        refill_not_before=state.refill_not_before,
        active=[dict(
            instance_id=w.instance_id, definition_id=w.definition_id.value,
            target_id=w.target_id, created_at=w.created_at, expires_at=w.expires_at,
            expressed_at=w.expressed_at,
            game=dict(round_ids=list(w.game.round_ids), wins=w.game.wins,
                      losses=w.game.losses, session_id=w.game.session_id),
        ) for w in state.active],
    )
