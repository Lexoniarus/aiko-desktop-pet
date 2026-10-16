"""Immutable conversational facts, independent of presentation and care effects."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from ..routine import TimeContext


class FriendshipStage(StrEnum):
    ACQUAINTANCE = "acquaintance"
    FAMILIAR = "familiar"
    FRIEND = "friend"
    CLOSE = "close"

    @classmethod
    def from_level(cls, level: int) -> FriendshipStage:
        if not 1 <= level <= 10:
            raise ValueError("Friendship level outside 1..10")
        if level <= 2:
            return cls.ACQUAINTANCE
        if level <= 5:
            return cls.FAMILIAR
        if level <= 8:
            return cls.FRIEND
        return cls.CLOSE


@dataclass(frozen=True, slots=True)
class DialogueContext:
    stage: FriendshipStage
    mood: str
    time: TimeContext
    needs: frozenset[str] = frozenset()
    working: bool = False
    recovering: bool = False
    present: bool | None = None

    @property
    def states(self) -> frozenset[str]:
        return self.needs | {self.mood}
