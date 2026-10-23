"""Detached accepted-content attribution, without another history or API request."""

from dataclasses import dataclass

from ...application.social_content import PreparedSocialContent, SocialProvider


@dataclass(frozen=True, slots=True)
class ContentCredit:
    provider: str
    source: str
    source_url: str
    entry_url: str
    author: str = ""
    author_url: str = ""
    license_name: str = ""
    license_url: str = ""


@dataclass(frozen=True, slots=True)
class CreditsSnapshot:
    accepted: ContentCredit | None = None


def project_credits(content: PreparedSocialContent | None) -> CreditsSnapshot:
    if content is None:
        return CreditsSnapshot()
    return CreditsSnapshot(
        ContentCredit(
            {SocialProvider.FACTS: "Random Useless Facts",
             SocialProvider.JOKEAPI: "JokeAPI",
             SocialProvider.QUOTATIONS: "Zitat-Service"}[content.provider],
            content.source,
            content.source_url,
            content.permalink,
            content.author, content.author_url,
            content.license_name, content.license_url,
        )
    )
