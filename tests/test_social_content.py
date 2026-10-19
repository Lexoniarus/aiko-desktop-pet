"""Provider-shaped fixtures exercise preparation, never runtime fallback copy."""

from __future__ import annotations

import unittest
from typing import Any

from aiko_pet.application.social_content import SocialCategory, prepare_social_content


def joke_payload(category: SocialCategory, identifier: int = 1) -> dict[str, Any]:
    return {
        "error": False, "safe": True, "lang": "de", "id": identifier,
        "type": category.value, "category": "Programming",
        "flags": dict.fromkeys(
            ("nsfw", "racist", "sexist", "religious", "political", "explicit"), False,
        ),
        "joke": "Ein Testtext mit mehreren Wörtern.",
        "setup": "Eine Testfrage?", "delivery": "Eine Testantwort.",
    }


def fact_payload(identifier: str = "test") -> dict[str, str]:
    return {
        "id": identifier, "language": "de", "text": "Ein vollständiger Testtext.",
        "source": "Testquelle", "source_url": "https://example.org/source",
        "permalink": "https://example.org/fact",
    }


class SocialContentTests(unittest.TestCase):
    def test_each_format_retains_source_and_uses_existing_story_model(self) -> None:
        for category in SocialCategory:
            payload = (fact_payload() if category == SocialCategory.FACT
                       else joke_payload(category))
            item = prepare_social_content(category, payload)
            self.assertEqual(item.category, category)
            self.assertEqual(item.reaction.presentation, "story")
            self.assertEqual(item.reaction.event, "talk")
            self.assertTrue(item.source_url.startswith("https://"))
            texts = [b.content for b in item.reaction.beats if b.kind == "text"]
            if category == SocialCategory.TWO_PARTS:
                self.assertEqual(texts[1:], [payload["setup"], payload["delivery"]])
                self.assertEqual(item.reaction.beats[2].kind, "pause")
            elif category == SocialCategory.FACT:
                self.assertEqual(texts[-1], payload["text"])
                self.assertEqual(item.source, "Testquelle")
                self.assertGreater(len(texts), 1)
            else:
                self.assertEqual(texts[-1], payload["joke"])

    def test_single_split_preserves_all_words_and_literal_entities(self) -> None:
        payload = joke_payload(SocialCategory.SINGLE)
        text = "Ein Testwort &szlig; " * 15
        payload["joke"] = text
        item = prepare_social_content(SocialCategory.SINGLE, payload)
        body = item.reaction.beats[1:]
        self.assertEqual(" ".join(b.content for b in body), text.strip())
        self.assertTrue(all(len(b.content) <= 125 for b in body))

    def test_mismatched_type_language_flags_and_missing_fields_are_rejected(self):
        for field, value in (("type", "twopart"), ("lang", "en"),
                             ("safe", False), ("error", True),
                             ("id", True), ("joke", None), ("flags", {})):
            with self.subTest(field=field):
                payload = joke_payload(SocialCategory.SINGLE)
                payload[field] = value
                with self.assertRaises(ValueError):
                    prepare_social_content(SocialCategory.SINGLE, payload)

    def test_incomplete_oversized_and_non_german_facts_are_rejected(self) -> None:
        for text in ("Abgeschnitten (...) ", "Abgeschnitten…", "x" * 126,
                     "Wort " * 140, "Text\x00", ""):
            with self.subTest(text=text[:30]):
                payload = fact_payload()
                payload["text"] = text
                with self.assertRaises(ValueError):
                    prepare_social_content(SocialCategory.FACT, payload)
        payload = fact_payload()
        payload["language"] = "en"
        with self.assertRaises(ValueError):
            prepare_social_content(SocialCategory.FACT, payload)

    def test_fact_source_urls_are_data_with_http_schemes_only(self) -> None:
        payload = fact_payload()
        payload["source_url"] = "javascript:alert(1)"
        with self.assertRaises(ValueError):
            prepare_social_content(SocialCategory.FACT, payload)
