"""Candidate filtering at the HTTP boundary, exhaustion, and persisted rejections."""

import io
import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from dataclasses import replace
from email.message import Message
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit

from test_social_content import joke_payload
from test_social_coordinator import ManualSocialWorker

from aiko_pet.application.settings import PetSettings
from aiko_pet.application.social_candidates import (
    JOKE_FILTER_REVISION,
    JokeCandidatePolicy,
    JokeCatalog,
    JokeExclusion,
)
from aiko_pet.application.social_content import SocialCategory, SocialProvider
from aiko_pet.application.social_coordinator import SocialContentCoordinator
from aiko_pet.application.social_fetch import SocialFetchRequest, SocialFetchResult
from aiko_pet.application.social_history import (
    SocialContentHistory,
    SocialContentReceipt,
)
from aiko_pet.infrastructure.persistence import StateStore
from aiko_pet.infrastructure.social_api import (
    HttpSocialContentWorker,
    SocialFetchError,
    fetch_joke_catalog,
    fetch_social_response,
    social_endpoint,
)
from aiko_pet.infrastructure.social_candidate_codec import decode_joke_exclusions
from aiko_pet.infrastructure.social_history_codec import (
    decode_social_history,
    encode_social_history,
)
from aiko_pet.infrastructure.sqlite.connection import open_database
from aiko_pet.infrastructure.sqlite.schema import APPLICATION_ID, MIGRATIONS
from aiko_pet.infrastructure.sqlite.social_rows import (
    read_social_core,
    write_social_core,
)
from aiko_pet.pet.state import PetState
from tools.persistence_test_support import save_test_session

TWO = SocialCategory.TWO_PARTS


class HeaderResponse(io.BytesIO):
    headers: dict[str, str] = {}


class CandidateTests(unittest.TestCase):
    def setUp(self):
        self.worker = ManualSocialWorker()
        self.now = self.worker.clock()
        self.catalog = JokeCatalog(0, 5, self.now + 3600)
        selection = patch("aiko_pet.application.social_coordinator.choice",
                          side_effect=lambda ranges: ranges[0])
        selection.start()
        self.addCleanup(selection.stop)

    def coordinator(self, history=None, *, catalog=True, persist=lambda: None):
        history = history or SocialContentHistory()
        # Isolate two-part selection without changing shared provider quotas.
        requests = history.requests
        for provider in (SocialProvider.FACTS, SocialProvider.QUOTATIONS):
            requests = requests.blocked(provider, self.now + 3600)
        history = replace(history, requests=requests).excluded(JokeExclusion(
            SocialCategory.SINGLE, 0, 5, "no_match", self.now + 3600,
        ), self.now)
        return SocialContentCoordinator(
            self.worker, history=history, wall_time=self.worker.clock,
            joke_catalog=self.catalog if catalog else None, persist_requests=persist,
        )

    def complete_failure(self, social, failure, *, identifier=None, reason=None):
        category, token = self.worker.requests[-1]
        self.worker.clock.now += 10
        self.worker.result = SocialFetchResult(
            token, category, failure=failure, rejected_id=identifier, reason=reason,
        )
        return social.poll()

    def plan(self) -> SocialFetchRequest:
        plan = self.worker.plans[-1]
        assert plan is not None
        return plan

    def test_known_ids_are_removed_before_every_dispatch_including_warm_stock(self):
        history = SocialContentHistory(tuple(
            SocialContentReceipt(TWO, f"jokeapi:{i}", f"{i + 1:064x}")
            for i in (1, 3)
        ))
        social = self.coordinator(history)
        social.set_enabled(True)
        first = self.plan()
        self.assertEqual(first.id_range, (0, 0))
        self.worker.complete(0)
        social.poll()
        second = self.plan()
        self.assertEqual(second.id_range, (2, 2))
        for plan in (first, second):
            url = social_endpoint(TWO, request=plan)
            bounds = parse_qs(urlsplit(url).query)["idRange"][0]
            lower, upper = map(int, bounds.split("-"))
            self.assertTrue(all(not lower <= i <= upper for i in (1, 3)))

    def test_rejected_id_is_persisted_before_next_request_and_not_requested_again(self):
        snapshots = []
        social = self.coordinator(persist=lambda: snapshots.append(social.history))
        social.set_enabled(True)
        social.select(TWO)
        self.complete_failure(social, "rejected", identifier=0, reason="format")
        self.assertEqual(self.plan().id_range, (1, 5))
        self.assertTrue(any(any(e.reason == "format" for e in h.exclusions)
                            for h in snapshots))
        self.assertEqual(social.history.requests.blocks,
                         snapshots[0].requests.blocks)
        self.assertEqual(social.history.entries, ())

    def test_no_match_marks_only_requested_category_and_interval(self):
        social = self.coordinator()
        social.set_enabled(True)
        self.assertEqual(self.plan().id_range, (0, 5))
        social.select(TWO)
        result = self.complete_failure(social, "empty", reason="no_match")
        assert result is not None
        self.assertEqual(result.status, "exhausted")
        self.assertFalse(any(b.provider == SocialProvider.JOKEAPI
                             for b in social.history.requests.blocks))
        self.assertEqual(social.select(TWO).status, "exhausted")
        self.assertEqual(len(self.worker.requests), 1)

    def test_small_pool_with_all_ids_in_history_stops_without_http(self):
        history = SocialContentHistory(tuple(
            SocialContentReceipt(TWO, f"jokeapi:{i}", f"{i + 1:064x}")
            for i in range(6)
        ))
        social = self.coordinator(history)
        social.set_enabled(True)
        self.assertEqual(social.select(TWO).status, "exhausted")
        self.assertEqual(self.worker.requests, [])
        self.assertEqual(social.history.entries, history.entries)

    def test_three_invalid_responses_bound_search_without_provider_pause(self):
        social = self.coordinator()
        social.set_enabled(True)
        social.select(TWO)
        for _ in range(2):
            self.complete_failure(social, "invalid")
        result = self.complete_failure(social, "invalid")
        assert result is not None
        self.assertEqual(result.status, "search_paused")
        self.assertEqual(len(self.worker.requests), 3)
        self.assertFalse(any(b.provider == SocialProvider.JOKEAPI
                             for b in social.history.requests.blocks))
        self.assertEqual(social.select(TWO).status, "waiting")
        self.assertEqual(len(self.worker.requests), 4)

    def test_metadata_is_a_separate_budgeted_job_and_never_plays_content(self):
        social = self.coordinator(catalog=False)
        social.set_enabled(True)
        self.assertTrue(self.plan().metadata)
        self.assertEqual(len(social.history.requests.attempts), 1)
        category, token = self.worker.requests[-1]
        social.select(TWO)
        self.worker.clock.now += 10
        self.worker.result = SocialFetchResult(token, category, catalog=self.catalog)
        self.assertIsNone(social.poll())
        self.assertFalse(self.plan().metadata)
        self.assertEqual(self.worker.requests[-1][0], TWO)
        self.assertEqual(len(social.history.requests.attempts), 2)
        self.assertEqual(social.count(TWO), 0)

    def test_metadata_failure_does_not_loop_background_requests(self):
        social = self.coordinator(catalog=False)
        social.set_enabled(True)
        social.select(TWO)
        result = self.complete_failure(social, "invalid")
        assert result is not None
        self.assertEqual(result.status, "error")
        for _ in range(5):
            social.poll()
        self.assertEqual(len(self.worker.requests), 1)

    def test_expiry_and_filter_revision_release_only_rejection_exclusions(self):
        entries = (
            JokeExclusion(TWO, 0, 1, "format", self.now),
            JokeExclusion(TWO, 2, 3, "no_match", self.now + 100,
                          JOKE_FILTER_REVISION + 1),
            JokeExclusion(SocialCategory.SINGLE, 4, 5, "format", self.now + 100),
        )
        self.assertEqual(JokeCandidatePolicy.remaining_ranges(
            self.catalog, TWO, ("jokeapi:3",), entries, self.now,
        ), ((0, 2), (4, 5)))

    def test_exclusions_roundtrip_sqlite_and_keep_effect_after_restart(self):
        history = SocialContentHistory().excluded(
            JokeExclusion(TWO, 0, 2, "format", self.now + 3600), self.now,
        )
        with tempfile.TemporaryDirectory() as directory:
            store = StateStore(Path(directory) / "test.sqlite3")
            save_test_session(store, PetState(updated_at=self.now), PetSettings(),
                              social_history=history)
            restored = store.load_session(now=self.now).social_history
        self.assertEqual(restored, history)
        social = self.coordinator(restored)
        social.set_enabled(True)
        self.assertEqual(self.plan().id_range, (3, 5))

    def test_version_five_history_loads_with_empty_exclusions(self):
        raw = encode_social_history(SocialContentHistory())
        raw["version"] = 5
        del raw["exclusions"]
        self.assertEqual(decode_social_history(raw).exclusions, ())
        raw["version"] = 6
        with self.assertRaises(ValueError):
            decode_social_history(raw)

    def test_malformed_exclusion_metadata_fails_strictly(self):
        raw = encode_social_history(SocialContentHistory().excluded(
            JokeExclusion(TWO, 0, 2, "format", self.now + 10), self.now,
        ))["exclusions"]
        for key, value in (("lower", True), ("upper", 100001), ("until", float("nan")),
                           ("revision", True), ("category", "fact"),
                           ("reason", "network")):
            row = dict(raw[0], **{key: value})
            with self.subTest(field=key), self.assertRaises(ValueError):
                decode_joke_exclusions([row])

    def test_v3_database_migration_preserves_receipts_and_old_provider_pause(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "v3.sqlite3"
            with closing(sqlite3.connect(path)) as connection:
                connection.execute(f"PRAGMA application_id={APPLICATION_ID}")
                for migration in MIGRATIONS[:3]:
                    for statement in migration.statements:
                        connection.execute(statement)
                    connection.execute("INSERT INTO schema_migrations VALUES (?,?,?)",
                                       (migration.version, migration.name, self.now))
                connection.execute("PRAGMA user_version=3")
                connection.execute("INSERT INTO save_state VALUES (1,1,?,0)",
                                   (self.now,))
                connection.execute("INSERT INTO social_receipts VALUES (0,1,?,?,?,0)",
                                   ("twopart", "jokeapi:1", "a" * 64))
                connection.execute(
                    "INSERT INTO provider_pauses VALUES ('jokeapi',1,0,?)",
                    (self.now + 60,),
                )
                connection.commit()
            with open_database(path) as connection:
                connection.execute("BEGIN IMMEDIATE")
                history = read_social_core(connection)
                self.assertEqual(history.entries[0].identity, "jokeapi:1")
                self.assertEqual(history.requests.blocks[0].until, self.now + 60)
                self.assertEqual(history.exclusions, ())
                history = history.excluded(
                    JokeExclusion(TWO, 2, 2, "format", self.now + 3600), self.now,
                )
                write_social_core(connection, history)
                connection.commit()
            with open_database(path) as connection:
                connection.execute("BEGIN")
                self.assertEqual(read_social_core(connection), history)


class CandidateHttpTests(unittest.TestCase):
    def test_exact_range_and_existing_safety_filters_reach_http(self):
        payload = joke_payload(TWO, 3)
        with patch("aiko_pet.infrastructure.social_api.urlopen",
                   return_value=io.BytesIO(json.dumps(payload).encode())) as opened:
            fetch_social_response(TWO, request=SocialFetchRequest(id_range=(3, 4)))
        url = opened.call_args.args[0].full_url
        self.assertIn("idRange=3-4", url)
        self.assertIn("safe-mode", url)
        self.assertIn("type=twopart", url)
        self.assertEqual(opened.call_args.kwargs["timeout"], 8)

    def test_filtered_empty_response_is_not_technical_backoff(self):
        body = json.dumps(dict(error=True, internalError=False, code=106)).encode()
        error = HTTPError("https://v2.jokeapi.dev/joke/Any", 400, "empty", Message(),
                          io.BytesIO(body))
        with patch("aiko_pet.infrastructure.social_api.urlopen", side_effect=error):
            with self.assertRaises(SocialFetchError) as raised:
                fetch_social_response(TWO, request=SocialFetchRequest(id_range=(3, 4)))
        self.assertEqual(raised.exception.failure, "empty")
        self.assertIsNone(raised.exception.retry_at)
        self.assertTrue(error.closed)

    def test_unrequested_identity_is_not_played_or_recorded_as_rejected(self):
        body = json.dumps(joke_payload(TWO, 8)).encode()
        with patch("aiko_pet.infrastructure.social_api.urlopen",
                   return_value=io.BytesIO(body)):
            with self.assertRaises(SocialFetchError) as raised:
                fetch_social_response(TWO, request=SocialFetchRequest(id_range=(3, 4)))
        self.assertEqual(raised.exception.failure, "invalid")
        self.assertIsNone(raised.exception.rejected_id)

    def test_empty_range_can_still_carry_an_actual_exhausted_http_budget(self):
        headers = Message()
        headers["RateLimit-Remaining"] = "0"
        headers["Retry-After"] = "45"
        body = json.dumps(dict(error=True, internalError=False, code=106)).encode()
        error = HTTPError("https://v2.jokeapi.dev/joke/Any", 400, "empty", headers,
                          io.BytesIO(body))
        with (
            patch("aiko_pet.infrastructure.social_api.urlopen", side_effect=error),
            patch("aiko_pet.infrastructure.social_api.time.time", return_value=1000),
        ):
            with self.assertRaises(SocialFetchError) as raised:
                fetch_social_response(TWO, request=SocialFetchRequest(id_range=(3, 4)))
        self.assertEqual(raised.exception.failure, "empty")
        self.assertEqual(raised.exception.retry_at, 1045)

    def test_wrong_provider_or_category_cannot_dispatch_catalog_requests(self):
        worker = HttpSocialContentWorker()
        with patch("aiko_pet.infrastructure.social_api.urlopen") as opened:
            for category, provider in ((SocialCategory.FACT, SocialProvider.JOKEAPI),
                                       (TWO, SocialProvider.FACTS)):
                with self.subTest(category=category), self.assertRaises(ValueError):
                    worker.start(category, object(), provider,
                                 request=SocialFetchRequest(metadata=True))
            opened.assert_not_called()
        worker.close()

    def test_recognized_long_single_retains_its_id_and_rejection_reason(self):
        payload = joke_payload(SocialCategory.SINGLE, 3)
        payload["joke"] = "a" * 126
        with patch("aiko_pet.infrastructure.social_api.urlopen",
                   return_value=io.BytesIO(json.dumps(payload).encode())):
            with self.assertRaises(SocialFetchError) as raised:
                fetch_social_response(SocialCategory.SINGLE,
                                      request=SocialFetchRequest(id_range=(3, 4)))
        self.assertEqual(raised.exception.failure, "rejected")
        self.assertEqual(raised.exception.rejected_id, 3)
        self.assertEqual(raised.exception.reason, "length")

    def test_catalog_bounds_are_validated_without_hardcoded_provider_count(self):
        for bounds, valid in (([0, 35], True), ([0, True], False),
                              ([2, 1], False), ([0, 100001], False)):
            response = HeaderResponse(json.dumps(dict(
                error=False, jokes=dict(idRange=dict(de=bounds)),
            )).encode())
            with self.subTest(bounds=bounds), patch(
                "aiko_pet.infrastructure.social_api.urlopen", return_value=response,
            ) as opened:
                if valid:
                    catalog, _ = fetch_joke_catalog()
                    self.assertEqual((catalog.lower, catalog.upper), (0, 35))
                    self.assertEqual(opened.call_args.args[0].full_url,
                                     "https://v2.jokeapi.dev/info")
                else:
                    with self.assertRaises(SocialFetchError):
                        fetch_joke_catalog()
