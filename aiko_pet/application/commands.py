"""Typed commands accepted by Aiko's application layer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias, cast

from ..pet.care_result import CARE_ACTIONS, CareAction
from ..pet.food import FOOD_CATALOG, FoodId
from .events import IncomingNotification
from .horoscope_models import PreparedBookReading
from .social_content import PreparedSocialContent


@dataclass(frozen=True, slots=True)
class CareCommand:
    """An intentional local care action, never an untrusted API event."""

    action: CareAction
    food_id: FoodId | None = None
    conversation: PreparedSocialContent | None = None
    book_reading: PreparedBookReading | None = None
    wake_from_clicks: bool = False

    def __post_init__(self) -> None:
        if self.action not in CARE_ACTIONS:
            raise ValueError(f"Unsupported care action: {self.action}")
        if self.food_id is not None and (
            self.action != "feed" or self.food_id not in FOOD_CATALOG
        ):
            raise ValueError("Invalid food selection for care action")
        if self.conversation is not None and (
            self.action != "talk"
            or not isinstance(self.conversation, PreparedSocialContent)
        ):
            raise ValueError("Prepared conversations require the talk action")
        if self.book_reading is not None and (
            self.action != "talk"
            or self.conversation is not None
            or not isinstance(self.book_reading, PreparedBookReading)
        ):
            raise ValueError("Book care requires one local reading payload")
        if type(self.wake_from_clicks) is not bool or (
            self.wake_from_clicks and self.action != "sleep"
        ):
            raise ValueError("Click waking requires the sleep action")

    @classmethod
    def from_action(
        cls,
        action: str,
        *,
        food_id: FoodId | None = None,
        conversation: PreparedSocialContent | None = None,
        wake_from_clicks: bool = False,
        book_reading: PreparedBookReading | None = None,
    ) -> CareCommand:
        """Check a UI string before converting it to a typed care command."""
        if action not in CARE_ACTIONS:
            raise ValueError(f"Unsupported care action: {action}")
        return cls(
            cast(CareAction, action),
            food_id=food_id,
            conversation=conversation,
            wake_from_clicks=wake_from_clicks,
            book_reading=book_reading,
        )


@dataclass(frozen=True, slots=True)
class NotificationCommand:
    """An already validated, authorized notification from an adapter."""

    notification: IncomingNotification


ApplicationCommand: TypeAlias = CareCommand | NotificationCommand
