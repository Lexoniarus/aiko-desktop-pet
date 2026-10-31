"""Data-only social HTTP jobs and replies shared by scheduler and adapter."""

from dataclasses import dataclass
from typing import Literal, Protocol

from .social_candidates import IdRange, JokeCatalog, RejectionReason
from .social_content import PreparedSocialContent, SocialCategory, SocialProvider

FetchFailure = Literal["invalid", "temporary", "rate", "access", "rejected", "empty"]


@dataclass(frozen=True, slots=True)
class SocialFetchRequest:
    metadata: bool = False
    id_range: IdRange | None = None


@dataclass(frozen=True, slots=True)
class SocialFetchResult:
    token: object
    category: SocialCategory
    content: PreparedSocialContent | None = None
    failure: FetchFailure | None = None
    retry_at: float | None = None
    catalog: JokeCatalog | None = None
    rejected_id: int | None = None
    reason: RejectionReason | None = None


class SocialContentWorker(Protocol):
    def start(
        self,
        category: SocialCategory,
        token: object,
        provider: SocialProvider | None = None,
        *,
        request: SocialFetchRequest | None = None,
    ) -> None: ...

    def poll(self) -> SocialFetchResult | None: ...

    def close(self) -> None: ...
