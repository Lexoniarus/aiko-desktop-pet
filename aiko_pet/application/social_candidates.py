"""Pure, bounded JokeAPI selection; content history is never silently relaxed."""

from dataclasses import dataclass
from typing import Literal

from ..pet.social_content_evidence import SocialCategory

JOKE_FILTER_REVISION = 1
MAX_JOKE_ID = 100_000
MAX_JOKE_EXCLUSIONS = 512
JOKE_METADATA_SECONDS = 3600
JOKE_EXCLUSION_SECONDS = 86400
RejectionReason = Literal["format", "incomplete", "length", "no_match", "duplicate"]
IdRange = tuple[int, int]


@dataclass(frozen=True, slots=True)
class JokeCatalog:
    lower: int
    upper: int
    valid_until: float


@dataclass(frozen=True, slots=True)
class JokeExclusion:
    category: SocialCategory
    lower: int
    upper: int
    reason: RejectionReason
    until: float
    revision: int = JOKE_FILTER_REVISION


class JokeCandidatePolicy:
    """Return disjoint allowed intervals, without enumerating the provider pool."""

    @staticmethod
    def remaining_ranges(
        catalog: JokeCatalog,
        category: SocialCategory,
        identities: tuple[str, ...],
        exclusions: tuple[JokeExclusion, ...],
        now: float,
    ) -> tuple[IdRange, ...]:
        blocked = [(e.lower, e.upper) for e in exclusions
                   if e.category == category and e.until > now
                   and e.revision == JOKE_FILTER_REVISION]
        for identity in identities:
            prefix, _, value = identity.partition(":")
            if prefix == "jokeapi" and value.isascii() and value.isdigit():
                identifier = int(value)
                blocked.append((identifier, identifier))
        cursor = catalog.lower
        result = []
        for lower, upper in sorted(blocked):
            if upper < cursor or lower > catalog.upper:
                continue
            if lower > cursor:
                result.append((cursor, lower - 1))
            cursor = max(cursor, upper + 1)
        if cursor <= catalog.upper:
            result.append((cursor, catalog.upper))
        return tuple(result)
