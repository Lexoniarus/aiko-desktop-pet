"""One local daily reading owner, replayable books and non-renewing expiry."""

from __future__ import annotations

import time
from dataclasses import replace
from typing import Callable

from ..pet.horoscope import (
    HoroscopeCatalogue,
    HoroscopeEntry,
    build_profile,
    select_entry,
)
from ..pet.mind.catalog import Reaction
from .horoscope import prepare_book_reading
from .horoscope_models import (
    HoroscopeDay,
    HoroscopeHistory,
    SkyCalculator,
    daily_request,
    local_day,
)

ReadingReactions = Callable[
    [HoroscopeEntry], tuple[Reaction, Reaction | None, Reaction]
]


class HoroscopeCoordinator:
    def __init__(
        self,
        catalogue: HoroscopeCatalogue,
        calculator: SkyCalculator,
        *,
        sign: Callable[[], str | None],
        reactions: ReadingReactions,
        credit: Callable[[HoroscopeDay], Callable[[], None]],
        persist: Callable[[], bool],
        history: HoroscopeHistory = HoroscopeHistory(),
        wall_time: Callable[[], float] = time.time,
        expire_at: Callable[[str, float], Callable[[], None]] = lambda _b,
        _t: lambda: None,
    ) -> None:
        self._catalogue, self._calculator = catalogue, calculator
        self._sign, self._reactions, self._credit = sign, reactions, credit
        self._persist, self._time = persist, wall_time
        self._history = history
        self._generation = 0
        self._expire_at = expire_at

    @property
    def history(self) -> HoroscopeHistory:
        return self._history

    @property
    def generation(self) -> int:
        return self._generation

    def for_book(self, book: str) -> HoroscopeDay | None:
        return next(
            (day for day in self.history.days if day.book_instance_id == book), None
        )

    def today(self) -> HoroscopeDay | None:
        today = local_day(self._time())
        return next((day for day in self.history.days if day.date == today), None)

    def availability(self, book: str | None = None) -> str:
        day = self.for_book(book) if book is not None else None
        if day is not None:
            if day.expires_at is not None and self._time() >= day.expires_at:
                return "expired"
            if day.date != local_day(self._time()) and not day.completed:
                return "expired"
            return "replay" if day.completed else "resume"
        current = self.today()
        if current is not None and current.completed:
            return "completed"
        if current is not None and current.book_instance_id is not None:
            return "bound"
        return "ready" if self._sign() else "sign"

    def obsolete_books(self) -> tuple[str, ...]:
        today = local_day(self._time())
        return tuple(
            day.book_instance_id
            for day in self.history.days
            if day.date < today
            and not day.completed
            and day.book_instance_id is not None
        )

    def _write(self, day: HoroscopeDay) -> bool:
        now, today = self._time(), local_day(self._time())
        keep = tuple(
            old
            for old in self.history.days
            if old.date != day.date
            and (
                old.date == today or old.expires_at is not None and now < old.expires_at
            )
        )
        previous = self._history
        self._history = HoroscopeHistory((*keep, day))
        try:
            saved = self._persist()
        except Exception:
            self._history = previous
            raise
        if not saved:
            self._history = previous
            return False
        return True

    def start(self, book: str) -> HoroscopeDay | None:
        status = self.availability(book)
        if status not in ("ready", "resume", "replay"):
            return None
        self._generation += 1
        if status in ("resume", "replay"):
            existing = self.for_book(book)
            assert existing is not None
            day = replace(existing, index=0) if status == "replay" else existing
            return day if self._write(day) else None
        old = self.today()
        sign = old.sign if old is not None and old.admitted else self._sign()
        if sign is None:
            return None
        request = daily_request(self._time(), sign)
        sky = self._calculator.calculate(request.instant_utc)
        profile = build_profile(sign, sky)
        entry = select_entry(self._catalogue, profile, f"{request.date}:{sign}")
        if entry is None:
            return None
        opening, comment, closing = self._reactions(entry)
        prepared = prepare_book_reading(
            request,
            entry,
            self._catalogue,
            sky,
            opening,
            comment,
            closing,
        )
        day = HoroscopeDay(
            request.date, sign, prepared, admitted=True, book_instance_id=book
        )
        undo: Callable[[], None] = (
            (lambda: None) if old is not None and old.admitted else self._credit(day)
        )
        try:
            saved = self._write(day)
        except Exception:
            undo()
            raise
        if not saved:
            undo()
            return None
        return day

    def advance(self, book: str, generation: int, index: int) -> bool:
        day = self.for_book(book)
        if (
            generation != self._generation
            or day is None
            or day.reading is None
            or self.availability(book) == "expired"
            or type(index) is not int
            or not day.index <= index <= len(day.reading.reaction.beats)
        ):
            return False
        complete = index == len(day.reading.reaction.beats)
        return self._write(
            replace(day, index=index, completed=day.completed or complete)
        )

    def pause(self) -> None:
        self._generation += 1

    def put_down(self, book: str) -> float | None:
        day = self.for_book(book)
        if day is None or not day.completed:
            return None
        if day.first_put_down_at is None:
            day = replace(day, first_put_down_at=self._time())
            assert day.expires_at is not None
            undo = self._expire_at(book, day.expires_at)
            try:
                saved = self._write(day)
            except Exception:
                undo()
                raise
            if not saved:
                undo()
                return None
        return day.expires_at
