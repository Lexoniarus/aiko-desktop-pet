"""One public Sprüche action, complete short source text and separate credit."""

from __future__ import annotations

import unittest
from dataclasses import replace
from typing import Any

from test_social_content import joke_payload
from test_social_coordinator import TEST_JOKE_CATALOG, ManualSocialWorker

from aiko_pet.application.social_content import (
    SocialCategory,
    SocialProvider,
    prepare_social_content,
)
from aiko_pet.application.social_coordinator import SocialContentCoordinator
from aiko_pet.application.social_history import (
    SocialContentHistory,
    SocialContentReceipt,
)
from aiko_pet.ui.view_models.credits import project_credits


def quote_payload(identifier: int = 1) -> dict[str, Any]:
    return dict(
        quote="Der Zweifel ist der Weisheit Anfang.",
        language="de",
        link=f"https://www.zitat-service.de/de/quotations/{identifier}",
        authorName="René Descartes",
        authorId=262,
        authorLink="https://de.wikipedia.org/wiki/Ren%C3%A9_Descartes",
        source="Test-Ausgabe",
        sourceLink="https://example.org/original",
    )


def quotation(payload: dict[str, Any]):
    return prepare_social_content(
        SocialCategory.SINGLE, payload, provider=SocialProvider.QUOTATIONS
    )


class SayingPreparationTests(unittest.TestCase):
    def test_quote_preserves_body_author_and_all_source_metadata(self):
        payload = quote_payload()
        payload["quote"] = "Behalten Sie Ihren eigenen Blick: Denken Sie selbst."
        item = quotation(payload)
        texts = [b.content for b in item.reaction.beats if b.kind == "text"]
        self.assertEqual(texts[1:], [payload["quote"], "Von René Descartes."])
        self.assertEqual(item.category, SocialCategory.SINGLE)
        self.assertEqual(item.identity, "zitat-service:1")
        self.assertEqual(item.permalink, payload["link"])
        self.assertEqual(
            (item.source, item.source_url), (payload["source"], payload["sourceLink"])
        )
        credit = project_credits(item).accepted
        assert credit is not None
        self.assertEqual(credit.provider, "Zitat-Service")
        self.assertEqual(credit.author_url, payload["authorLink"])
        self.assertEqual(credit.license_name, "CC BY 4.0")
        self.assertEqual(
            credit.license_url, "https://creativecommons.org/licenses/by/4.0/"
        )
        self.assertIsNone(item.reaction.completed_social)

    def test_final_second_belongs_to_author_bubble_even_before_emote(self):
        endings = set()
        for index in range(20):
            payload = quote_payload(index)
            payload["quote"] = f"Vollständiger Testtext Nummer {index}."
            item = quotation(payload)
            texts = [b for b in item.reaction.beats if b.kind == "text"]
            self.assertEqual(len(texts), 3)
            self.assertEqual(texts[1].duration_ms, 4000)
            self.assertEqual(texts[-1].duration_ms, 5000)
            endings.add(item.reaction.beats[-1].kind)
        self.assertEqual(endings, {"text", "emote"})

    def test_exact_125_character_boundary_counts_literal_entities_in_both_sources(self):
        for length in (125, 126):
            text = "x" * (length - len(" &szlig;.")) + " &szlig;."
            for quote in (True, False):
                payload = (
                    quote_payload() if quote else joke_payload(SocialCategory.SINGLE)
                )
                payload["quote" if quote else "joke"] = text
                if length == 126:
                    with self.assertRaises(ValueError):
                        (
                            quotation(payload)
                            if quote
                            else prepare_social_content(SocialCategory.SINGLE, payload)
                        )
                else:
                    item = (
                        quotation(payload)
                        if quote
                        else prepare_social_content(SocialCategory.SINGLE, payload)
                    )
                    body = [b.content for b in item.reaction.beats if b.kind == "text"][
                        1
                    ]
                    self.assertEqual(body, text)
                    self.assertEqual(len(body), 125)

    def test_two_sentences_and_single_colon_are_not_automatic_rejections(self):
        for text in (
            "Ich hab gerade den DJ angerufen. Er hat aufgelegt.",
            "Ein Gedanke: Lernen braucht Zeit.",
        ):
            payload = joke_payload(SocialCategory.SINGLE)
            payload["joke"] = text
            item = prepare_social_content(SocialCategory.SINGLE, payload)
            self.assertEqual(item.reaction.beats[1].content, text)

    def test_short_dialogues_paragraphs_and_staged_delivery_are_rejected(self):
        for text in (
            'A: "Hallo." B: "Guten Tag."',
            "A: Hallo. B: Guten Tag.",
            "Informatiker: Hallo.\nKollegin: Guten Tag.",
            "Frage: Warum? Antwort: Darum.",
            "Ein erster Absatz.\n\nEin zweiter Absatz.",
        ):
            for quote in (True, False):
                payload = (
                    quote_payload() if quote else joke_payload(SocialCategory.SINGLE)
                )
                payload["quote" if quote else "joke"] = text
                with self.assertRaises(ValueError):
                    (
                        quotation(payload)
                        if quote
                        else prepare_social_content(SocialCategory.SINGLE, payload)
                    )
        payload = joke_payload(SocialCategory.SINGLE)
        payload["joke"] = "Einleitung.\nDie Pointe."
        with self.assertRaises(ValueError):
            prepare_social_content(SocialCategory.SINGLE, payload)

    def test_quote_formatting_whitespace_is_normalized_without_changing_words(self):
        payload = quote_payload()
        payload["quote"] = "  Ein  vollständiger\nGedanke.  "
        item = quotation(payload)
        self.assertEqual(item.reaction.beats[1].content, "Ein vollständiger Gedanke.")
        joke = joke_payload(SocialCategory.SINGLE)
        joke["joke"] = "Ein vollständiger Gedanke."
        self.assertEqual(
            item.fingerprint,
            prepare_social_content(SocialCategory.SINGLE, joke).fingerprint,
        )

    def test_unknown_author_and_dialect_remain_unchanged(self):
        payload = quote_payload()
        payload["authorName"] = "Unbekannt"
        payload["quote"] = "Dat sleit in as`n Pluum in`t Peerd."
        for key in ("source", "sourceLink", "authorLink"):
            payload.pop(key)
        item = quotation(payload)
        self.assertEqual(item.author, "Unbekannt")
        self.assertEqual(item.source_url, "")
        self.assertEqual(item.reaction.beats[1].content, payload["quote"])
        self.assertEqual(item.reaction.beats[2].content, "Von Unbekannt.")

    def test_wrong_language_identity_metadata_and_oversized_author_are_rejected(self):
        for field, value in (
            ("language", "en"),
            ("quote", "abgeschnitten…"),
            ("link", "https://example.org/de/quotations/1"),
            ("link", "https://www.zitat-service.de/de/quotations/1?extra=yes"),
            ("authorName", None),
            ("authorName", "x" * 125),
            ("sourceLink", "javascript:alert(1)"),
            ("authorLink", "file:///local"),
        ):
            with self.subTest(field=field, value=value):
                payload = quote_payload()
                payload[field] = value
                with self.assertRaises(ValueError):
                    quotation(payload)
        for category in (SocialCategory.TWO_PARTS, SocialCategory.FACT):
            with self.assertRaises(ValueError):
                prepare_social_content(
                    category, quote_payload(), provider=SocialProvider.QUOTATIONS
                )


class MixedSayingTests(unittest.TestCase):
    def setUp(self):
        self.worker = ManualSocialWorker()
        self.content = SocialContentCoordinator(
            self.worker, joke_catalog=TEST_JOKE_CATALOG, wall_time=self.worker.clock
        )
        self.content.set_enabled(True)

    def test_two_total_saying_slots_mix_sources_and_alternate_admitted_items(self):
        for index in range(6):
            self.worker.complete(index)
            self.content.poll()
        self.assertEqual(self.content.count(SocialCategory.SINGLE), 2)
        first = self.content.select(SocialCategory.SINGLE).content
        assert first is not None
        self.assertEqual(first.provider, SocialProvider.JOKEAPI)
        self.content.accept(first)
        second = self.content.select(SocialCategory.SINGLE).content
        assert second is not None
        self.assertEqual(second.provider, SocialProvider.QUOTATIONS)
        self.content.accept(second)
        self.assertEqual(
            [e.category for e in self.content.history.entries],
            [SocialCategory.SINGLE] * 2,
        )

    def test_failed_joke_source_delivers_available_quote_with_same_public_category(
        self,
    ):
        self.content.select(SocialCategory.SINGLE)
        self.worker.complete(1, fail=True)
        self.assertIsNone(self.content.poll())
        self.assertEqual(self.worker.providers[-1], SocialProvider.QUOTATIONS)
        self.worker.complete(2)
        result = self.content.poll()
        assert result is not None and result.content is not None
        self.assertEqual(result.status, "ready")
        self.assertEqual(result.content.category, SocialCategory.SINGLE)
        self.assertFalse(self.content.history.entries)

    def test_provider_mismatch_cannot_enter_buffer(self):
        self.worker.complete(1)
        assert self.worker.result is not None
        self.worker.result = replace(
            self.worker.result, content=quotation(quote_payload())
        )
        self.content.poll()
        self.assertEqual(self.content.count(SocialCategory.SINGLE), 0)

    def test_hundred_sayings_share_one_history_across_both_sources(self):
        history = SocialContentHistory()
        for index in range(102):
            prefix = "jokeapi" if index % 2 else "zitat-service"
            history = history.admitted(
                SocialContentReceipt(
                    SocialCategory.SINGLE,
                    f"{prefix}:{index}",
                    f"{index:064x}",
                )
            )
        self.assertEqual(len(history.entries), 100)
        self.assertEqual(history.entries[0].identity, "zitat-service:2")
        self.assertEqual({e.category for e in history.entries}, {SocialCategory.SINGLE})

    def test_same_words_deduplicate_across_sources_and_unknown_authors(self):
        self.worker.complete(1)
        self.content.poll()
        first = self.content.select(SocialCategory.SINGLE).content
        assert first is not None
        self.content.accept(first)
        payload = quote_payload(99)
        payload["quote"] = "  TEST  1. "
        self.assertTrue(self.content._duplicate(quotation(payload)))
