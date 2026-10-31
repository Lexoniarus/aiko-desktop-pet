"""HTTP boundaries and worker lifetime without live network dependencies."""

from __future__ import annotations

import io
import json
import time
import unittest
from datetime import datetime, timezone
from email.message import Message
from email.utils import format_datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Event, Thread
from types import SimpleNamespace
from unittest.mock import patch
from urllib.error import HTTPError

from test_social_content import fact_payload, joke_payload
from test_social_sayings import quote_payload

from aiko_pet.application.social_content import (
    BUFFERED_CATEGORIES,
    SocialCategory,
    SocialProvider,
    prepare_social_content,
)
from aiko_pet.infrastructure.social_api import (
    MAX_RESPONSE_BYTES,
    HttpSocialContentWorker,
    SocialFetchError,
    SocialHttpResponse,
    fetch_social_content,
    fetch_social_response,
    social_endpoint,
)


def http_headers(values: dict[str, str]) -> Message:
    result = Message()
    for name, value in values.items():
        result[name] = value
    return result


class HeaderResponse(io.BytesIO):
    headers: Message


class SocialApiTests(unittest.TestCase):
    def test_quote_endpoint_is_free_public_path_and_preserves_attribution(self):
        response = io.BytesIO(json.dumps(quote_payload()).encode())
        with patch(
            "aiko_pet.infrastructure.social_api.urlopen", return_value=response
        ) as opened:
            item = fetch_social_content(
                SocialCategory.SINGLE, SocialProvider.QUOTATIONS
            )
        request = opened.call_args.args[0]
        self.assertEqual(
            request.full_url, "https://api.zitat-service.de/v1/quote?language=de"
        )
        self.assertEqual(
            request.header_items(),
            [
                ("Accept", "application/json"),
                ("User-agent", "AikoDesktopPet/1.0"),
            ],
        )
        self.assertEqual(item.provider, SocialProvider.QUOTATIONS)
        for category in (SocialCategory.TWO_PARTS, SocialCategory.FACT):
            with self.assertRaises(ValueError):
                social_endpoint(category, SocialProvider.QUOTATIONS)

    def test_rate_limit_seconds_dates_and_missing_headers_use_finite_backoff(self):
        now = 100000.0
        date = format_datetime(
            datetime.fromtimestamp(now + 120, timezone.utc), usegmt=True
        )
        for headers, expected in (
            ({"Retry-After": "30"}, now + 30),
            ({"Retry-After": date}, now + 120),
            ({}, now + 900),
            ({"Retry-After": "invalid"}, now + 900),
            ({"Retry-After": "10", "RateLimit-Reset": date}, now + 120),
        ):
            error = HTTPError(
                social_endpoint(SocialCategory.SINGLE),
                429,
                "test",
                http_headers(headers),
                None,
            )
            with (
                patch("aiko_pet.infrastructure.social_api.urlopen", side_effect=error),
                patch(
                    "aiko_pet.infrastructure.social_api.time",
                    SimpleNamespace(time=lambda: now),
                ),
            ):
                with self.assertRaises(SocialFetchError) as raised:
                    fetch_social_response(SocialCategory.SINGLE)
            self.assertEqual(raised.exception.failure, "rate")
            self.assertEqual(raised.exception.retry_at, expected)

    def test_last_available_response_keeps_content_and_carries_provider_reset(self):
        response = HeaderResponse(
            json.dumps(joke_payload(SocialCategory.SINGLE)).encode()
        )
        reset = format_datetime(
            datetime.fromtimestamp(100120, timezone.utc), usegmt=True
        )
        response.headers = http_headers({
            "RateLimit-Remaining": "0",
            "RateLimit-Reset": reset,
        })
        with (
            patch("aiko_pet.infrastructure.social_api.urlopen", return_value=response),
            patch(
                "aiko_pet.infrastructure.social_api.time",
                SimpleNamespace(time=lambda: 100000),
            ),
        ):
            result = fetch_social_response(SocialCategory.SINGLE)
        self.assertEqual(result.content.category, SocialCategory.SINGLE)
        self.assertEqual(result.retry_at, 100120)

    def test_access_changes_stop_for_a_day_and_server_errors_back_off(self):
        for status, failure, delay in (
            (401, "access", 86400),
            (403, "access", 86400),
            (404, "access", 86400),
            (500, "temporary", 60),
        ):
            error = HTTPError(
                social_endpoint(SocialCategory.SINGLE), status, "test", Message(), None
            )
            with (
                patch("aiko_pet.infrastructure.social_api.urlopen", side_effect=error),
                patch(
                    "aiko_pet.infrastructure.social_api.time",
                    SimpleNamespace(time=lambda: 100000),
                ),
            ):
                with self.assertRaises(SocialFetchError) as raised:
                    fetch_social_response(SocialCategory.SINGLE)
            self.assertEqual(raised.exception.failure, failure)
            self.assertEqual(raised.exception.retry_at, 100000 + delay)

    def test_success_with_remaining_budget_does_not_misread_reset_as_a_pause(self):
        response = HeaderResponse(
            json.dumps(joke_payload(SocialCategory.SINGLE)).encode()
        )
        response.headers = http_headers({
            "Retry-After": "60",
            "RateLimit-Remaining": "118",
            "RateLimit-Reset": ("Fri Oct 23 2026 09:27:33 GMT+0000 "
                                "(Coordinated Universal Time)"),
        })
        with patch("aiko_pet.infrastructure.social_api.urlopen", return_value=response):
            self.assertIsNone(fetch_social_response(SocialCategory.SINGLE).retry_at)

    def test_redirect_never_requests_an_unreviewed_endpoint(self):
        paths: list[str] = []

        class RedirectHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                paths.append(self.path)
                self.send_response(302)
                self.send_header("Location", "/unreviewed")
                self.end_headers()

            def log_message(self, format, *args):
                pass

        server = HTTPServer(("127.0.0.1", 0), RedirectHandler)
        self.addCleanup(server.server_close)
        server.timeout = 2
        thread = Thread(target=server.handle_request, daemon=True)
        thread.start()
        url = f"http://127.0.0.1:{server.server_port}/reviewed"
        with patch(
            "aiko_pet.infrastructure.social_api.social_endpoint", return_value=url
        ):
            with self.assertRaises(SocialFetchError) as raised:
                fetch_social_response(SocialCategory.SINGLE)
        thread.join(2)
        self.assertEqual(raised.exception.failure, "access")
        self.assertEqual(paths, ["/reviewed"])

    def test_each_request_is_one_german_item_with_a_finite_timeout(self) -> None:
        for category in BUFFERED_CATEGORIES:
            payload = (
                fact_payload()
                if category == SocialCategory.FACT
                else joke_payload(category)
            )
            response = io.BytesIO(json.dumps(payload).encode())
            with patch(
                "aiko_pet.infrastructure.social_api.urlopen", return_value=response
            ) as opened:
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
        for body in (
            b"x" * (MAX_RESPONSE_BYTES + 1),
            b"broken json",
            json.dumps(english).encode(),
        ):
            with patch(
                "aiko_pet.infrastructure.social_api.urlopen",
                return_value=io.BytesIO(body),
            ):
                with self.assertRaises(ValueError):
                    fetch_social_content(SocialCategory.FACT)

    def test_worker_keeps_single_flight_and_returns_data_after_close(self) -> None:
        entered, release = Event(), Event()
        category = SocialCategory.FACT
        content = prepare_social_content(category, fact_payload())

        def fetch(_category: SocialCategory, _provider=None):
            entered.set()
            release.wait(2)
            return SocialHttpResponse(content)

        worker = HttpSocialContentWorker()
        token = object()
        with patch("aiko_pet.infrastructure.social_api.fetch_social_response", fetch):
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
