"""Candidate exclusion transfer and schema compatibility."""

import io
import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from email.message import Message
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

from test_social_content import joke_payload

from aiko_pet.application.social_candidates import JokeExclusion
from aiko_pet.application.social_content import SocialCategory, SocialProvider
from aiko_pet.application.social_fetch import SocialFetchRequest
from aiko_pet.application.social_history import SocialContentHistory
from aiko_pet.infrastructure.social_api import (
    HttpSocialContentWorker,
    SocialFetchError,
    fetch_joke_catalog,
    fetch_social_response,
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

TWO = SocialCategory.TWO_PARTS


class HeaderResponse(io.BytesIO):
    headers: dict[str, str] = {}


class CandidateTests(unittest.TestCase):
    def setUp(self):
        self.now = 1800000000

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
