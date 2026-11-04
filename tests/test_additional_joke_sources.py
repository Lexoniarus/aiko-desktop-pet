"""Reviewed external library, bounded live adapter, and finite repetition guards."""

import io
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from support.payloads import joke_payload
from support.social import TEST_JOKE_CATALOG, ManualSocialWorker

from aiko_pet.application.joke_content_policy import wording_allowed
from aiko_pet.application.settings import PetSettings
from aiko_pet.application.social_content import (
    SocialCategory,
    SocialProvider,
    prepare_social_content,
)
from aiko_pet.application.social_coordinator import SocialContentCoordinator
from aiko_pet.application.social_history import (
    JOKE_REPEAT_WINDOW,
    SocialContentHistory,
    SocialContentReceipt,
)
from aiko_pet.application.social_requests import REQUEST_CAPS, SocialRequestHistory
from aiko_pet.desktop.social_runtime import (
    SocialConversationRuntime,
    SocialRuntimePorts,
)
from aiko_pet.infrastructure.local_jokes import REVIEW_PATH, load_local_jokes
from aiko_pet.infrastructure.persistence import StateStore
from aiko_pet.infrastructure.social_api import (
    fetch_social_response,
    social_endpoint,
)
from aiko_pet.infrastructure.social_history_codec import (
    decode_social_history,
    encode_social_history,
)
from aiko_pet.pet.state import PetState
from aiko_pet.ui.view_models.credits import project_credits
from tools.persistence_test_support import save_test_session

SINGLE, TWO = SocialCategory.SINGLE, SocialCategory.TWO_PARTS


class AdditionalJokeSourceTests(unittest.TestCase):
    def test_live_adapter_uses_only_reviewed_keyless_german_category(self):
        for category, expected in ((SINGLE, "flachwitze"), (TWO, "scherzfragen")):
            text = ("Ein kleiner Test." if category == SINGLE
                    else "Welche Zahl? Die Drei.")
            body = json.dumps([dict(text=text, language="de")]).encode()
            with patch("aiko_pet.infrastructure.social_api.urlopen",
                       return_value=io.BytesIO(body)) as opened:
                result = fetch_social_response(category, SocialProvider.WITZAPI)
            request = opened.call_args.args[0]
            self.assertEqual(request.full_url, "https://witzapi.de/api/joke/"
                             f"?limit=1&language=de&category={expected}")
            self.assertEqual(opened.call_args.kwargs["timeout"], 8)
            self.assertEqual(result.content.provider, SocialProvider.WITZAPI)
            self.assertEqual(result.content.permalink, "")
            assert result.content.evidence is not None
            self.assertEqual(" ".join(result.content.evidence.parts), text)

    def test_malformed_language_and_unknown_formats_are_rejected(self):
        for payload in ([], [{"text": "Test.", "language": "en"}],
                        [{"text": "Test.", "language": "de"}] * 2,
                        [dict(text="Mehrere? Fragen? Und Antworten.", language="de")]):
            with self.subTest(payload=payload), patch(
                "aiko_pet.infrastructure.social_api.urlopen",
                return_value=io.BytesIO(json.dumps(payload).encode()),
            ), self.assertRaises(ValueError):
                fetch_social_response(TWO, SocialProvider.WITZAPI)

    def test_local_library_cannot_accidentally_use_an_http_endpoint(self):
        for category in (SINGLE, TWO, SocialCategory.FACT):
            with self.assertRaises(ValueError):
                social_endpoint(category, SocialProvider.PYJOKES)

    def test_wording_checks_reject_observed_derogatory_and_political_material(self):
        for text in ("Ein Politiker im Bundestag.", "Ein Blondinenwitz.",
                     "Ein Witz mit dem alten Begriff Eskimos.", "So ein Arschloch.",
                     "Ein Witz über Trump.", "Noch ein Behindertenwitz."):
            with self.subTest(text=text):
                self.assertFalse(wording_allowed(text))
                with self.assertRaises(ValueError):
                    prepare_social_content(SINGLE, dict(text=text, language="de"),
                                           provider=SocialProvider.WITZAPI)
        self.assertTrue(wording_allowed(
            "Warum hat der Keks Schatten? Wegen des Baums."
        ))

    def test_question_answer_is_not_misclassified_as_a_short_saying(self):
        with self.assertRaises(ValueError):
            prepare_social_content(SINGLE, dict(text="Welche Zahl? Die Drei.",
                                               language="de"),
                                   provider=SocialProvider.WITZAPI)

    def test_complete_two_part_ellipsis_is_preserved_but_truncation_is_not(self):
        payload = joke_payload(TWO, 31)
        payload.update(setup="Wenn der Test weitergeht...",
                       delivery="...folgt die Antwort.")
        item = prepare_social_content(TWO, payload)
        assert item.evidence is not None
        self.assertEqual(item.evidence.parts, (payload["setup"], payload["delivery"]))
        for field, value in (("delivery", "Eine abgebrochene Antwort..."),
                             ("setup", "Ein abgeschnittener [...] Test")):
            with self.subTest(field=field), self.assertRaises(ValueError):
                prepare_social_content(TWO, dict(payload, **{field: value}))

    def test_pinned_review_loads_only_approved_texts_with_attribution(self):
        with patch("aiko_pet.infrastructure.social_api.urlopen") as opened:
            items = load_local_jokes()
        opened.assert_not_called()
        self.assertEqual(len(items), 17)
        self.assertEqual(sum(i.category == TWO for i in items), 13)
        for item in items:
            assert item.evidence is not None
            self.assertTrue(wording_allowed(" ".join(item.evidence.parts)))
            self.assertEqual(item.license_name, "BSD-3-Clause")
            credit = project_credits(item).accepted
            assert credit is not None
            self.assertEqual(credit.provider, "pyjokes (lokal)")
        self.assertTrue(all(i.provider == SocialProvider.PYJOKES for i in items))

    def test_changed_package_text_or_version_cannot_bypass_review(self):
        for mutate in (lambda raw: raw.update(package_version="999.0"),
                       lambda raw: raw["entries"][0].update(fingerprint="0" * 64)):
            raw = json.loads(REVIEW_PATH.read_text(encoding="utf-8"))
            mutate(raw)
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "review.json"
                path.write_text(json.dumps(raw), encoding="utf-8")
                with self.assertRaises(ValueError):
                    load_local_jokes(path)

    def test_offline_library_rotates_small_pools_without_http_or_early_repeats(self):
        for category in (SINGLE, TWO):
            worker = ManualSocialWorker()
            history = SocialContentHistory(requests=SocialRequestHistory())
            for provider in REQUEST_CAPS:
                history = replace(history, requests=history.requests.blocked(
                    provider, worker.clock() + 86400,
                ))
            items = load_local_jokes()
            content = SocialContentCoordinator(
                worker, history=history, local_content=items, wall_time=worker.clock,
                joke_catalog=TEST_JOKE_CATALOG,
            )
            content.set_enabled(True)
            previous = []
            guard = min(JOKE_REPEAT_WINDOW,
                        sum(i.category == category for i in items) - 1)
            for _ in range(45):
                choice = content.select(category)
                assert choice.content is not None
                self.assertEqual(choice.status, "ready")
                self.assertNotIn(choice.content.identity, previous[-guard:])
                content.accept(choice.content)
                previous.append(choice.content.identity)
                self.assertEqual(decode_social_history(encode_social_history(
                    content.history,
                )), content.history)
            self.assertEqual(worker.requests, [])
            self.assertEqual(content.history.requests.attempts, ())

    def test_repeated_admission_moves_receipt_without_duplicate_save_rows(self):
        first = SocialContentReceipt(TWO, "jokeapi:1", "a" * 64)
        other = SocialContentReceipt(TWO, "jokeapi:2", "b" * 64)
        history = SocialContentHistory().admitted(first).admitted(other).admitted(first)
        self.assertEqual(history.entries, (other, first))
        self.assertEqual(decode_social_history(encode_social_history(history)), history)

    def test_local_selection_preserves_protected_text_from_other_categories(self):
        local = load_local_jokes()[0]
        for category, identity in ((SocialCategory.FACT, "uselessfacts:prior"),
                                   (TWO, "jokeapi:999")):
            with self.subTest(category=category):
                receipt = SocialContentReceipt(category, identity, local.fingerprint)
                worker = ManualSocialWorker()
                content = SocialContentCoordinator(
                    worker, history=SocialContentHistory((receipt,)),
                    local_content=(local,), wall_time=worker.clock,
                    joke_catalog=TEST_JOKE_CATALOG,
                )
                content.set_enabled(True)
                self.assertNotIn(local, content.local_candidates(local.category))
                self.assertNotEqual(content.select(local.category).status, "ready")
                self.assertEqual(content.history.entries, (receipt,))
                content.close()

    def test_old_jokes_release_after_ten_newer_items_without_erasing_archive(self):
        history = SocialContentHistory()
        for index in range(19):
            history = history.admitted(SocialContentReceipt(
                TWO, f"jokeapi:{index}", f"{index:064x}",
            ))
        self.assertEqual(len(history.entries), 19)
        self.assertEqual(len(history.protected_entries), 10)
        self.assertNotIn(history.entries[0], history.protected_entries)

    def test_new_source_receipts_roundtrip_with_original_content_in_normal_save(self):
        items = [load_local_jokes()[0], prepare_social_content(
            TWO, dict(text="Welche Zahl? Die Drei.", language="de"),
            provider=SocialProvider.WITZAPI,
        )]
        history = SocialContentHistory()
        for item in items:
            history = history.admitted(SocialContentReceipt(
                item.category, item.identity, item.fingerprint, item.intro_variant,
            ))
        with tempfile.TemporaryDirectory() as directory:
            store = StateStore(Path(directory) / "test.sqlite3")
            save_test_session(store, PetState(updated_at=1800000000), PetSettings(),
                              social_history=history)
            self.assertEqual(store.load_session(now=1800000000).social_history, history)

    def test_failed_lookup_gets_a_followup_message_without_conversation_reward(self):
        worker = ManualSocialWorker()
        content = SocialContentCoordinator(worker, wall_time=worker.clock,
                                           joke_catalog=TEST_JOKE_CATALOG)
        statuses, deferred, started = [], [], []
        runtime = SocialConversationRuntime(content, SocialRuntimePorts(
            can_start=lambda: True, defer=deferred.append,
            start=lambda item: started.append(item) or True,
            show_wait=lambda reaction: None, clear_wait=lambda: None,
            show_status=statuses.append,
        ))
        runtime.set_enabled(True)
        runtime.select(TWO)
        worker.complete(1, fail=True)  # Initial background saying request.
        runtime.poll()
        worker.complete(2, fail=True)  # The selected JokeAPI request.
        runtime.poll()
        worker.complete(3, fail=True)  # The second online joke source.
        runtime.poll()
        self.assertFalse(runtime.waiting)
        self.assertTrue(statuses)
        self.assertFalse(started)
        self.assertEqual(content.history.entries, ())
        runtime.close()
