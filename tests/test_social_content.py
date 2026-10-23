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

    def test_single_preserves_entities_but_never_splits_long_items(self) -> None:
        payload = joke_payload(SocialCategory.SINGLE)
        text = ('Die Selbsthilfegruppe "HTML-Sonderzeichen-Probleme" trifft sich '
                'heute im gro&szlig;en Saal.')
        payload["joke"] = text
        item = prepare_social_content(SocialCategory.SINGLE, payload)
        body = [b for b in item.reaction.beats[1:] if b.kind == "text"]
        self.assertEqual(" ".join(b.content for b in body), text.strip())
        self.assertTrue(all(len(b.content) <= 125 for b in body))
        payload["joke"] = "Ein Testwort &szlig; " * 15
        with self.assertRaises(ValueError):
            prepare_social_content(SocialCategory.SINGLE, payload)

    def test_varied_framing_preserves_full_content_and_uses_only_a_final_emote(self):
        for category in SocialCategory:
            intros, endings = set(), set()
            for i in range(24):
                payload = (fact_payload(str(i)) if category == SocialCategory.FACT
                           else joke_payload(category, i))
                field = ("text" if category == SocialCategory.FACT else "joke"
                         if category == SocialCategory.SINGLE else "delivery")
                payload[field] = f"Vollständiger Anbietertext Nummer {i}."
                item = prepare_social_content(category, payload)
                texts = [b.content for b in item.reaction.beats if b.kind == "text"]
                intros.add(texts[0])
                endings.add(item.reaction.beats[-1].kind)
                self.assertEqual(texts[-1], payload[field])
                self.assertLessEqual(len(texts), 5)
                self.assertTrue(all(len(text) <= 125 for text in texts))
                emotes = [i for i, b in enumerate(item.reaction.beats)
                          if b.kind == "emote"]
                self.assertTrue(not emotes or emotes == [len(item.reaction.beats) - 1])
                self.assertIsNone(item.reaction.completed_social)
            self.assertEqual(len(intros), 3)
            self.assertEqual(endings, {"text", "emote"})

    def test_full_five_bubble_budget_preserves_all_words_with_framing(self):
        payload = joke_payload(SocialCategory.TWO_PARTS)
        payload["setup"] = "Frage " * 35
        payload["delivery"] = "Antwort " * 25
        item = prepare_social_content(SocialCategory.TWO_PARTS, payload)
        texts = [b.content for b in item.reaction.beats if b.kind == "text"]
        self.assertEqual(len(texts), 5)
        self.assertEqual(" ".join(texts[1:]),
                         " ".join((payload["setup"] + payload["delivery"]).split()))
        payload["delivery"] += "Antwort " * 20
        with self.assertRaises(ValueError):
            prepare_social_content(SocialCategory.TWO_PARTS, payload)

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
