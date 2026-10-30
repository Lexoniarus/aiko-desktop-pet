"""Data-only social fetch results and worker boundary."""

from dataclasses import dataclass
from typing import Literal, Protocol

from .social_content import PreparedSocialContent, SocialCategory, SocialProvider

FetchFailure = Literal["invalid", "temporary", "rate", "access"]


@dataclass(frozen=True, slots=True)
class SocialFetchResult:
    token: object
    category: SocialCategory
    content: PreparedSocialContent | None = None
    failure: FetchFailure | None = None
    retry_at: float | None = None


class SocialContentWorker(Protocol):
    def start(
        self,
        category: SocialCategory,
        token: object,
        provider: SocialProvider | None = None,
    ) -> None: ...

    def poll(self) -> SocialFetchResult | None: ...

    def close(self) -> None: ...
