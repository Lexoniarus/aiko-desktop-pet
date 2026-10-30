"""Candidate exclusion transfer and schema compatibility."""

import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from aiko_pet.application.social_candidates import JokeExclusion
from aiko_pet.application.social_content import SocialCategory
from aiko_pet.application.social_history import SocialContentHistory
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
