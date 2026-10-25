"""Immutable original API content, retained only by a qualifying Moodlet cause."""

import hashlib
from dataclasses import dataclass
from enum import StrEnum
from typing import Literal
from urllib.parse import urlsplit


class SocialCategory(StrEnum):
    SINGLE = "single"
    TWO_PARTS = "twopart"
    FACT = "fact"
    HOROSCOPE = "horoscope"


class SocialProvider(StrEnum):
    JOKEAPI = "jokeapi"
    QUOTATIONS = "zitat-service"
    FACTS = "uselessfacts"
    ASTROWAY = "astroway"


@dataclass(frozen=True, slots=True)
class SocialContentEvidence:
    """Validated source words and attribution, without presentation or history."""

    category: SocialCategory
    provider: SocialProvider
    identity: str
    fingerprint: str
    parts: tuple[str, ...]
    source: str
    source_url: str
    permalink: str
    author: str = ""
    author_url: str = ""
    license_name: str = ""
    license_url: str = ""

    def __post_init__(self) -> None:
        if (not isinstance(self.category, SocialCategory)
                or not isinstance(self.provider, SocialProvider)
                or (self.category, self.provider) not in (
                    (SocialCategory.SINGLE, SocialProvider.JOKEAPI),
                    (SocialCategory.SINGLE, SocialProvider.QUOTATIONS),
                    (SocialCategory.TWO_PARTS, SocialProvider.JOKEAPI),
                    (SocialCategory.FACT, SocialProvider.FACTS),
                )):
            raise ValueError("Incompatible social content category/provider")
        count = 2 if self.category == SocialCategory.TWO_PARTS else 1
        if (not isinstance(self.parts, tuple) or len(self.parts) != count
                or any(not isinstance(part, str) or not part
                       or len(part) > 2500 or part != " ".join(part.split())
                       or any(ord(char) < 32 for char in part) for part in self.parts)):
            raise ValueError("Invalid original social content parts")
        if (not isinstance(self.identity, str)
                or not self.identity.startswith(f"{self.provider.value}:")
                or not 1 <= len(self.identity.split(":", 1)[-1]) <= 128
                or any(char.isspace() or ord(char) < 32 for char in self.identity)
                or self.provider != SocialProvider.FACTS
                and not self.identity.split(":", 1)[-1].isascii()
                or self.provider != SocialProvider.FACTS
                and not self.identity.split(":", 1)[-1].isdecimal()):
            raise ValueError("Invalid original social content identity")
        expected = hashlib.sha256(" ".join(self.parts).casefold().encode()).hexdigest()
        if self.fingerprint != expected:
            raise ValueError("Original social content fingerprint mismatch")
        for value, limit in ((self.source, 1000), (self.author, 2500),
                             (self.license_name, 2500)):
            if (not isinstance(value, str) or len(value) > limit
                    or any(ord(char) < 32 for char in value)):
                raise ValueError("Invalid social source attribution")
        if not self.source or (
            self.provider == SocialProvider.QUOTATIONS and not self.author
        ):
            raise ValueError("Missing social source attribution")
        for url in (self.source_url, self.permalink, self.author_url, self.license_url):
            if not isinstance(url, str) or len(url) > 2048:
                raise ValueError("Invalid social source URL")
            if url:
                parsed = urlsplit(url)
                if (parsed.scheme not in ("http", "https") or not parsed.hostname
                        or any(char.isspace() or ord(char) < 32 for char in url)):
                    raise ValueError("Invalid social source URL")
        if not self.permalink:
            raise ValueError("Missing social content permalink")

    @property
    def kind(self) -> Literal["one_liner", "quotation", "two_part", "fact"]:
        if self.provider == SocialProvider.QUOTATIONS:
            return "quotation"
        if self.category == SocialCategory.TWO_PARTS:
            return "two_part"
        return "fact" if self.category == SocialCategory.FACT else "one_liner"
