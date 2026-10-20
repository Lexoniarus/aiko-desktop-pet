"""Detached accepted-content attribution, without another history or API request."""

from dataclasses import dataclass

from ...application.social_content import PreparedSocialContent, SocialCategory


@dataclass(frozen=True, slots=True)
class ContentCredit:
    provider: str
    source: str
    source_url: str
    entry_url: str


@dataclass(frozen=True, slots=True)
class CreditsSnapshot:
    accepted: ContentCredit | None = None


def project_credits(content: PreparedSocialContent | None) -> CreditsSnapshot:
    if content is None:
        return CreditsSnapshot()
    return CreditsSnapshot(
        ContentCredit(
            "Random Useless Facts"
            if content.category == SocialCategory.FACT
            else "JokeAPI",
            content.source,
            content.source_url,
            content.permalink,
        )
    )
