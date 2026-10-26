"""Immutable local reading episodes; no provider request or footer contract."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from typing import Any, Protocol

from ..pet.horoscope import ZODIAC_SIGNS as ZODIAC_SIGNS
from ..pet.horoscope import SkySnapshot
from ..pet.mind.catalog import Reaction
from ..world.contracts import ObjectInteraction, ObjectState, WorldSnapshot

BOOK_LIFETIME_SECONDS = 3600.0


def local_day(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp).date().isoformat()


def checked_day(value: Any) -> str:
    if not isinstance(value, str) or date.fromisoformat(value).isoformat() != value:
        raise ValueError("Invalid horoscope date")
    return value


@dataclass(frozen=True, slots=True)
class DailyReadingRequest:
    date: str
    sign: str
    instant_utc: datetime

    def __post_init__(self) -> None:
        checked_day(self.date)
        if self.sign not in ZODIAC_SIGNS or self.instant_utc.utcoffset() is None:
            raise ValueError("Invalid local horoscope request")


def daily_request(timestamp: float, sign: str) -> DailyReadingRequest:
    day = datetime.fromtimestamp(timestamp).date()
    noon = datetime.combine(day, time(12)).astimezone(timezone.utc)
    return DailyReadingRequest(day.isoformat(), sign, noon)


class SkyCalculator(Protocol):
    def calculate(self, instant_utc: datetime) -> SkySnapshot: ...


@dataclass(frozen=True, slots=True)
class PreparedBookReading:
    date: str
    sign: str
    entry_id: str
    entry_revision: int
    catalogue_revision: int
    reaction: Reaction
    comment_id: str = ""
    sky: SkySnapshot | None = None

    def __post_init__(self) -> None:
        checked_day(self.date)
        texts = [cue for cue in self.reaction.beats if cue.kind == "text"]
        if (
            self.sign not in ZODIAC_SIGNS
            or not self.entry_id
            or type(self.entry_revision) is not int
            or self.entry_revision < 1
            or type(self.catalogue_revision) is not int
            or self.catalogue_revision < 1
            or not 1 <= len(texts) <= 12
            or len(self.reaction.beats) > 40
        ):
            raise ValueError("Invalid frozen local reading")


@dataclass(frozen=True, slots=True)
class HoroscopeDay:
    date: str
    sign: str | None = None
    reading: PreparedBookReading | None = None
    index: int = 0
    admitted: bool = False
    completed: bool = False
    book_instance_id: str | None = None
    first_put_down_at: float | None = None

    def __post_init__(self) -> None:
        checked_day(self.date)
        if (
            self.sign is not None
            and self.sign not in ZODIAC_SIGNS
            or type(self.index) is not int
            or self.index < 0
            or type(self.admitted) is not bool
            or type(self.completed) is not bool
            or self.completed
            and not self.admitted
        ):
            raise ValueError("Invalid daily reading state")
        if self.reading is not None:
            if (
                self.reading.date != self.date
                or self.reading.sign != self.sign
                or not self.admitted
                or not self.book_instance_id
                or self.index > len(self.reading.reaction.beats)
            ):
                raise ValueError("Inconsistent frozen daily reading")
        elif self.index or self.book_instance_id is not None:
            raise ValueError("Legacy markers cannot contain local book progress")
        if self.first_put_down_at is not None and (
            isinstance(self.first_put_down_at, bool)
            or not math.isfinite(self.first_put_down_at)
            or self.first_put_down_at < 0
            or not self.completed
            or self.reading is None
        ):
            raise ValueError("Invalid first completed book put-down")

    @property
    def expires_at(self) -> float | None:
        return (
            None
            if self.first_put_down_at is None
            else self.first_put_down_at + BOOK_LIFETIME_SECONDS
        )


@dataclass(frozen=True, slots=True)
class HoroscopeHistory:
    days: tuple[HoroscopeDay, ...] = ()

    def __post_init__(self) -> None:
        if len(self.days) > 2 or len({day.date for day in self.days}) != len(self.days):
            raise ValueError("Keep only the current day and an unexpired prior book")
        books = [day.book_instance_id for day in self.days if day.book_instance_id]
        if len(books) != len(set(books)):
            raise ValueError("A physical book cannot contain two daily readings")


def validate_book_bindings(
    history: HoroscopeHistory, world: WorldSnapshot | None
) -> None:
    """Check live bindings and preserve allocated, already retired identities.

    World omits terminal instances on disk. Absence is not proof of corruption,
    and a wall clock change must not invalidate a legitimately retired book.
    """
    objects = {} if world is None else {
        item.instance_id: item for item in world.objects
    }
    definitions = {} if world is None else {
        definition.definition_id: definition for definition in world.definitions
    }
    for day in history.days:
        if day.reading is None:
            continue
        token = day.book_instance_id or ""
        if (world is None or not re.fullmatch(r"object_[1-9][0-9]*", token)
                or int(token.removeprefix("object_")) >= world.next_instance_id):
            raise ValueError("Horoscope reading requires an allocated World identity")
        item = objects.get(token)
        if item is None:
            continue
        definition = definitions.get(item.definition_id)
        if definition is None or ObjectInteraction.READ not in definition.interactions:
            raise ValueError("Horoscope reading must reference a readable object")
        if (item.state not in (ObjectState.CONSUMED, ObjectState.REMOVED)
                and item.expires_at != day.expires_at):
            raise ValueError("Book and reading must share the original expiry")
