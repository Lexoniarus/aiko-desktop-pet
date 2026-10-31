"""Bounded personal-transfer receipts inside the existing wish save section."""

from typing import Any

from ..pet.balance import BALANCE
from ..pet.catalog_validation import (
    enum_value,
    integer_value,
    number_value,
    object_fields,
)
from ..pet.food_catalog import DEFAULT_CATALOG
from ..pet.food_handover import (
    MAX_FOOD_HANDOVERS,
    FoodHandoverReceipt,
    FoodWishSnapshot,
    HandoverStatus,
)
from ..pet.wish_catalog import WISH_CATALOG
from ..pet.wishes import WishArea, WishId
from .wish_snapshot_codec import (
    decode_wish_goal,
    decode_wish_target,
    encode_wish_goal,
    encode_wish_target,
)


def _identity(raw: Any) -> str:
    if not isinstance(raw, str) or not 1 <= len(raw) <= 128:
        raise ValueError("Invalid food handover identity")
    return raw


def _snapshot(raw: Any, at: float, next_id: int) -> FoodWishSnapshot:
    row = object_fields(
        raw,
        (
            "instance_id",
            "definition_id",
            "target",
            "goal",
            "created_at",
            "expressed_at",
            "pinned",
        ),
        context="handover original wish",
    )
    key = enum_value(row["definition_id"], WishId, context="handover wish")
    if WISH_CATALOG.definitions[key].area != WishArea.FOOD:
        raise ValueError("Food handover cannot snapshot another wish area")
    start = number_value(
        row["created_at"], minimum=0, maximum=at, context="handover wish creation"
    )
    spoken = (
        None
        if row["expressed_at"] is None
        else number_value(
            row["expressed_at"],
            minimum=start,
            maximum=at,
            context="handover wish expression",
        )
    )
    if type(row["pinned"]) is not bool:
        raise ValueError("Handover wish pin must be boolean")
    return FoodWishSnapshot(
        integer_value(
            row["instance_id"],
            minimum=1,
            maximum=next_id - 1,
            context="handover wish identity",
        ),
        key,
        decode_wish_target(row["target"], key),
        decode_wish_goal(row["goal"], key),
        start,
        spoken,
        row["pinned"],
    )


def decode_food_handovers(
    raw: Any,
    elapsed: float,
    next_id: int,
) -> tuple[FoodHandoverReceipt, ...]:
    if not isinstance(raw, list) or len(raw) > MAX_FOOD_HANDOVERS:
        raise ValueError("Unbounded food handover receipts")
    receipts = []
    identities: set[str] = set()
    pending_objects: set[str] = set()
    for value in raw:
        row = object_fields(
            value,
            (
                "handover_id",
                "object_id",
                "handed_over_at",
                "wishes",
                "recognized_food_id",
                "recognized_at",
                "status",
                "resolved_wish_instance_id",
                "accounted_wish_ids",
            ),
            context="food handover",
        )
        identity, object_id = _identity(row["handover_id"]), _identity(row["object_id"])
        at = number_value(
            row["handed_over_at"],
            minimum=0,
            maximum=elapsed,
            context="food handover time",
        )
        status = enum_value(row["status"], HandoverStatus, context="handover status")
        if (
            identity in identities
            or status == HandoverStatus.PENDING
            and object_id in pending_objects
        ):
            raise ValueError("Duplicate handover or pending object")
        wishes = row["wishes"]
        if not isinstance(wishes, list) or len(wishes) > BALANCE.integer(
            "wishes", "maximum_active"
        ):
            raise ValueError("Unbounded handover wish context")
        context = tuple(_snapshot(w, at, next_id) for w in wishes)
        wish_ids = {w.instance_id for w in context}
        if len(wish_ids) != len(context):
            raise ValueError("Duplicate original handover wish")
        food = row["recognized_food_id"]
        if food is not None and (
            not isinstance(food, str) or food not in DEFAULT_CATALOG.foods
        ):
            raise ValueError("Unknown recognized handover food")
        recognized = (
            None
            if row["recognized_at"] is None
            else number_value(
                row["recognized_at"],
                minimum=at,
                maximum=elapsed,
                context="food recognition time",
            )
        )
        if (
            (food is None) != (recognized is None)
            or status == HandoverStatus.PENDING
            and food is not None
            or status == HandoverStatus.EVALUATED
            and food is None
        ):
            raise ValueError("Handover status and recognition disagree")
        accounted_raw = row["accounted_wish_ids"]
        if not isinstance(accounted_raw, list) or len(accounted_raw) > len(context):
            raise ValueError("Unbounded accounted handover wishes")
        accounted = tuple(
            integer_value(
                v, minimum=1, maximum=next_id - 1, context="accounted handover wish"
            )
            for v in accounted_raw
        )
        resolved = (
            None
            if row["resolved_wish_instance_id"] is None
            else integer_value(
                row["resolved_wish_instance_id"],
                minimum=1,
                maximum=next_id - 1,
                context="resolved handover wish",
            )
        )
        if (
            len(set(accounted)) != len(accounted)
            or not set(accounted) <= wish_ids
            or resolved is not None
            and (status != HandoverStatus.EVALUATED or resolved not in accounted)
        ):
            raise ValueError("Inconsistent handover accounting")
        receipts.append(
            FoodHandoverReceipt(
                identity,
                object_id,
                at,
                context,
                food,
                recognized,
                status,
                resolved,
                accounted,
            )
        )
        identities.add(identity)
        if status == HandoverStatus.PENDING:
            pending_objects.add(object_id)
    return tuple(receipts)


def encode_food_handovers(
    receipts: tuple[FoodHandoverReceipt, ...],
) -> list[dict[str, Any]]:
    return [
        dict(
            handover_id=r.handover_id,
            object_id=r.object_id,
            handed_over_at=r.handed_over_at,
            wishes=[
                dict(
                    instance_id=w.instance_id,
                    definition_id=w.definition_id.value,
                    target=encode_wish_target(w.target),
                    goal=encode_wish_goal(w.goal),
                    created_at=w.created_at,
                    expressed_at=w.expressed_at,
                    pinned=w.pinned,
                )
                for w in r.wishes
            ],
            recognized_food_id=r.recognized_food_id,
            recognized_at=r.recognized_at,
            status=r.status.value,
            resolved_wish_instance_id=r.resolved_wish_instance_id,
            accounted_wish_ids=list(r.accounted_wish_ids),
        )
        for r in receipts
    ]
