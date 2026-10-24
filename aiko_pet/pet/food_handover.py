"""Durable personal-transfer facts; no custody, recognition or reward decisions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .wish_types import WishGoal, WishId, WishTarget

MAX_FOOD_HANDOVERS = 32


class HandoverStatus(StrEnum):
    PENDING = "pending"
    EVALUATED = "evaluated"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class FoodWishSnapshot:
    instance_id: int
    definition_id: WishId
    target: WishTarget
    goal: WishGoal
    created_at: float
    expressed_at: float | None = None
    pinned: bool = False


@dataclass(frozen=True, slots=True)
class FoodHandoverReceipt:
    handover_id: str
    object_id: str
    handed_over_at: float
    wishes: tuple[FoodWishSnapshot, ...] = ()
    recognized_food_id: str | None = None
    recognized_at: float | None = None
    status: HandoverStatus = HandoverStatus.PENDING
    resolved_wish_instance_id: int | None = None
    accounted_wish_ids: tuple[int, ...] = ()
