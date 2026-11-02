"""One repetition decision for candidate planning, local stock and HTTP replies."""

from dataclasses import dataclass
from typing import Protocol, Sequence, TypeVar

from ..pet.social_content_evidence import SocialCategory
from .social_candidates import IdRange, JokeCandidatePolicy, JokeCatalog, JokeExclusion

JOKE_REPEAT_WINDOW = 10


class RepeatContent(Protocol):
    @property
    def category(self) -> SocialCategory: ...

    @property
    def identity(self) -> str: ...

    @property
    def fingerprint(self) -> str: ...


_Content = TypeVar("_Content", bound=RepeatContent)


@dataclass(frozen=True, slots=True)
class JokeRepeatPlan:
    ranges: tuple[IdRange, ...] | None
    released_identity: str | None = None


@dataclass(frozen=True, slots=True)
class SocialRepeatPolicy:
    entries: tuple[RepeatContent, ...]
    occupied: tuple[RepeatContent, ...] = ()

    @staticmethod
    def protected(
        entries: Sequence[_Content], *, category: SocialCategory | None = None,
        window: int = JOKE_REPEAT_WINDOW,
    ) -> tuple[_Content, ...]:
        protected: list[_Content] = []
        for current in (SocialCategory.SINGLE, SocialCategory.TWO_PARTS,
                        SocialCategory.FACT):
            recent = tuple(e for e in entries if e.category == current)
            if current != SocialCategory.FACT:
                limit = window if current == category else JOKE_REPEAT_WINDOW
                recent = recent[-limit:] if limit else ()
            protected.extend(recent)
        return tuple(protected)

    def permits(
        self, item: RepeatContent, *, local_pool_size: int | None = None,
        released_identity: str | None = None,
    ) -> bool:
        window = (JOKE_REPEAT_WINDOW if local_pool_size is None
                  else min(JOKE_REPEAT_WINDOW, max(0, local_pool_size - 1)))
        protected = self.protected(self.entries, category=item.category, window=window)
        if released_identity == item.identity and item.identity.startswith("jokeapi:"):
            last = next((e for e in reversed(self.entries)
                         if e.category == item.category
                         and e.identity.startswith("jokeapi:")), None)
            if last is not None and last.identity != item.identity:
                protected = tuple(e for e in protected
                                  if (e.category, e.identity)
                                  != (item.category, released_identity))
        return not any(e.identity == item.identity or e.fingerprint == item.fingerprint
                       for e in (*protected, *self.occupied))

    def joke_candidates(
        self, catalog: JokeCatalog, category: SocialCategory,
        exclusions: tuple[JokeExclusion, ...], now: float,
    ) -> JokeRepeatPlan:
        identities = tuple(e.identity for e in (*self.protected(self.entries),
                                               *self.occupied))
        ranges = JokeCandidatePolicy.remaining_ranges(
            catalog, category, identities, exclusions, now,
        )
        if ranges:
            return JokeRepeatPlan(ranges)
        known = tuple(e for e in self.entries if e.category == category
                      and e.identity.startswith("jokeapi:"))
        for entry in known[:-1]:
            if not self.permits(entry, released_identity=entry.identity):
                continue
            identifier = entry.identity.removeprefix("jokeapi:")
            # An eligible known repeat may recover from old duplicate receipts.
            # Content eligibility and empty-range exclusions remain authoritative.
            eligible = tuple(e for e in exclusions if not (
                e.category == category and e.reason == "duplicate"
                and str(e.lower) == identifier == str(e.upper)
            ))
            available = JokeCandidatePolicy.remaining_ranges(
                catalog, category, tuple(i for i in identities if i != entry.identity),
                eligible, now,
            )
            if available:
                return JokeRepeatPlan(available, entry.identity)
        return JokeRepeatPlan(())
