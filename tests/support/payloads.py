from __future__ import annotations

from typing import Any

from aiko_pet.application.social_content import SocialCategory


def joke_payload(category: SocialCategory, identifier: int = 1) -> dict[str, Any]:
    return {
        "error": False,
        "safe": True,
        "lang": "de",
        "id": identifier,
        "type": category.value,
        "category": "Programming",
        "flags": dict.fromkeys(
            ("nsfw", "racist", "sexist", "religious", "political", "explicit"), False
        ),
        "joke": "Ein Testtext mit mehreren Wörtern.",
        "setup": "Eine Testfrage?",
        "delivery": "Eine Testantwort.",
    }


def fact_payload(identifier: str = "test") -> dict[str, str]:
    return {
        "id": identifier,
        "language": "de",
        "text": "Ein vollständiger Testtext.",
        "source": "Testquelle",
        "source_url": "https://example.org/source",
        "permalink": "https://example.org/fact",
    }
