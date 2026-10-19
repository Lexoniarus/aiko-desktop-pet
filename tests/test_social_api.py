"""HTTP boundaries and worker lifetime without live network dependencies."""

from __future__ import annotations

import io
import json
import time
import unittest
from threading import Event
from unittest.mock import patch

from test_social_content import fact_payload, joke_payload

from aiko_pet.application.social_content import SocialCategory, prepare_social_content
from aiko_pet.infrastructure.social_api import (
    MAX_RESPONSE_BYTES,
    HttpSocialContentWorker,
    fetch_social_content,
    social_endpoint,
)


class SocialApiTests(unittest.TestCase):
    def test_each_request_is_one_german_item_with_a_finite_timeout(self) -> None:
        for category in SocialCategory:
            payload = (fact_payload() if category == SocialCategory.FACT
                       else joke_payload(category))
            response = io.BytesIO(json.dumps(payload).encode())
            with patch("aiko_pet.infrastructure.social_api.urlopen",
                       return_value=response) as opened:
                item = fetch_social_content(category)
            self.assertEqual(item.category, category)
            request = opened.call_args.args[0]
            self.assertEqual(request.full_url, social_endpoint(category))
            self.assertNotIn("amount=", request.full_url)
            self.assertEqual(opened.call_args.kwargs["timeout"], 8)
            if category != SocialCategory.FACT:
                self.assertIn(f"type={category.value}", request.full_url)
                self.assertIn("safe-mode", request.full_url)

    def test_size_limit_invalid_json_and_wrong_language_fail_preparation(self):
        english = fact_payload()
        english["language"] = "en"
        for body in (b"x" * (MAX_RESPONSE_BYTES + 1), b"broken json",
                     json.dumps(english).encode()):
            with patch("aiko_pet.infrastructure.social_api.urlopen",
                       return_value=io.BytesIO(body)):
                with self.assertRaises(ValueError):
                    fetch_social_content(SocialCategory.FACT)

    def test_worker_keeps_single_flight_and_returns_data_after_close(self) -> None:
        entered, release = Event(), Event()
        category = SocialCategory.FACT
        content = prepare_social_content(category, fact_payload())

        def fetch(_category: SocialCategory):
            entered.set()
            release.wait(2)
            return content

        worker = HttpSocialContentWorker()
        token = object()
        with patch("aiko_pet.infrastructure.social_api.fetch_social_content", fetch):
            worker.start(category, token)
            try:
                self.assertTrue(entered.wait(1))
                with self.assertRaises(RuntimeError):
                    worker.start(category, object())
                worker.close()
            finally:
                release.set()
            deadline = time.monotonic() + 2
            result = worker.poll()
            while result is None and time.monotonic() < deadline:
                time.sleep(0.001)
                result = worker.poll()
            assert result is not None
            self.assertIs(result.token, token)
            self.assertIs(result.content, content)
            with self.assertRaises(RuntimeError):
                worker.start(category, object())
