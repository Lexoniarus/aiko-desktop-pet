"""Offline frozen readings, original deadlines and old-schema migration."""

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from test_horoscope import NOW, coordinator

from aiko_pet.infrastructure.sqlite.connection import open_database
from aiko_pet.infrastructure.sqlite.horoscope_rows import (
    read_horoscope,
    write_horoscope,
)
from aiko_pet.infrastructure.sqlite.schema import (
    APPLICATION_ID,
    MIGRATIONS,
    SCHEMA_VERSION,
)


def admitted_day():
    day = coordinator()[0].start("object_1")
    assert day is not None
    return day


class SqliteHoroscopeTests(unittest.TestCase):
    def test_reading_round_trip_including_replay_progress_and_deadline(self):
        owner, _clock, _sky, _credit = coordinator()
        day = owner.start("object_1")
        assert day is not None and day.reading is not None
        owner.advance("object_1", owner.generation, len(day.reading.reaction.beats))
        owner.put_down("object_1")
        owner.start("object_1")
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "state.sqlite3"
            with open_database(path, initialize=True) as connection:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute("INSERT INTO save_state VALUES (1,1,?,0)", (NOW,))
                write_horoscope(connection, owner.history)
                connection.commit()
            with open_database(path) as connection:
                connection.execute("BEGIN")
                self.assertEqual(read_horoscope(connection), owner.history)
                self.assertEqual(
                    connection.execute("PRAGMA foreign_key_check").fetchall(), []
                )
                self.assertIsNone(
                    connection.execute(
                        "SELECT name FROM sqlite_master WHERE name='horoscope_days'"
                    ).fetchone()
                )

    def test_v2_migrates_admission_but_drops_provider_text(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "state.sqlite3"
            connection = sqlite3.connect(path)
            connection.execute(f"PRAGMA application_id={APPLICATION_ID}")
            for migration in MIGRATIONS[:2]:
                for statement in migration.statements:
                    connection.execute(statement)
                connection.execute(
                    "INSERT INTO schema_migrations VALUES (?,?,?)",
                    (migration.version, migration.name, NOW),
                )
            connection.execute("PRAGMA user_version=2")
            connection.execute("INSERT INTO save_state VALUES (1,1,?,0)", (NOW,))
            # Named scalar columns avoid embedding legacy provider text.
            connection.execute(
                "INSERT INTO horoscope_days(day,state_id,attempts,progress_index,"
                "admitted,completed,reading_date,sign,overview,advice,"
                "disclaimer,footer) "
                "VALUES ('2026-10-25',1,1,1,1,0,'2026-10-25','aries',"
                "'Old prose','','','')"
            )
            connection.commit()
            connection.close()
            with open_database(path) as connection:
                connection.execute("BEGIN")
                history = read_horoscope(connection)
                self.assertTrue(history.days[0].admitted)
                self.assertIsNone(history.days[0].reading)
                self.assertEqual(
                    connection.execute("PRAGMA user_version").fetchone(),
                    (SCHEMA_VERSION,),
                )
