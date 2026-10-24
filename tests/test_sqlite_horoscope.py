"""Daily continuation survives SQL reload without another request or care credit."""

from __future__ import annotations

import tempfile
import unittest
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

from test_horoscope import horoscope_payload
from test_social_coordinator import ManualSocialWorker
from test_sqlite_adaptive_rows import profile
from test_sqlite_social_rows import social_history

from aiko_pet.application.horoscope import prepare_horoscope
from aiko_pet.application.horoscope_models import HoroscopeDay, HoroscopeRequest
from aiko_pet.application.settings import PetSettings
from aiko_pet.application.social_content import SocialCategory
from aiko_pet.application.social_coordinator import SocialContentCoordinator
from aiko_pet.application.social_history import SocialContentHistory
from aiko_pet.application.storage_contracts import StorageError
from aiko_pet.infrastructure.sqlite.adaptive_rows import read_adaptive, write_adaptive
from aiko_pet.infrastructure.sqlite.connection import open_database
from aiko_pet.infrastructure.sqlite.settings_rows import read_settings, write_settings
from aiko_pet.infrastructure.sqlite.social_rows import (
    read_social_history,
    write_social_history,
)
from aiko_pet.pet.mind.adaptive_models import AdaptiveMemory

DAY = "2026-10-24"
NOW = datetime(2026, 10, 24, 12).timestamp()


def admitted_day() -> HoroscopeDay:
    prepared = prepare_horoscope(
        horoscope_payload(day=DAY), HoroscopeRequest("aries", DAY)
    )
    assert prepared.horoscope is not None
    return HoroscopeDay(DAY, 3, prepared.horoscope, 2, True)


class SqliteHoroscopeTests(unittest.TestCase):
    def setUp(self) -> None:
        folder = tempfile.TemporaryDirectory(prefix="aiko-horoscope-rows-")
        self.addCleanup(folder.cleanup)
        self.path = Path(folder.name) / "fixture.sqlite3"
        with open_database(self.path, initialize=True) as connection:
            connection.execute("INSERT INTO save_state VALUES (1, 1, ?, 90000)", (NOW,))

    def test_absent_failed_cached_admitted_completed_and_new_day_states_round_trip(
        self,
    ) -> None:
        admitted = admitted_day()
        assert admitted.reading is not None
        prepared = prepare_horoscope(
            horoscope_payload(day=DAY), HoroscopeRequest("aries", DAY)
        )
        completed = replace(
            admitted, index=len(prepared.reaction.beats), completed=True
        )
        with open_database(self.path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            for day in (
                None,
                HoroscopeDay(DAY),
                HoroscopeDay(DAY, attempts=3),
                replace(admitted, index=0, admitted=False),
                admitted,
                completed,
                HoroscopeDay("2026-10-25"),
            ):
                expected = replace(social_history(), horoscope=day)
                write_social_history(connection, expected)
                self.assertEqual(read_social_history(connection), expected)
                self.assertEqual(
                    connection.execute(
                        "SELECT count(*) FROM horoscope_days"
                    ).fetchone(),
                    (0 if day is None else 1,),
                )

    def test_sql_resume_keeps_original_sign_progress_and_does_not_book_care_twice(
        self,
    ) -> None:
        day = admitted_day()
        expected = replace(social_history(), horoscope=day)
        with open_database(self.path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            write_settings(connection, PetSettings(zodiac_sign="leo"))
            write_social_history(connection, expected)
            connection.commit()
        with open_database(self.path) as connection:
            connection.execute("BEGIN")
            loaded = read_social_history(connection)
            settings = read_settings(connection)
        self.assertEqual(settings.zodiac_sign, "leo")
        self.assertEqual(loaded.horoscope, day)
        worker = ManualSocialWorker()
        coordinator = SocialContentCoordinator(
            worker,
            history=loaded,
            wall_time=lambda: NOW,
            zodiac_sign=lambda: settings.zodiac_sign,
        )
        coordinator.set_enabled(True)
        before = list(worker.requests)
        selected = coordinator.select(SocialCategory.HOROSCOPE)
        assert selected.content is not None
        care = Mock()
        self.assertTrue(coordinator.admit_horoscope(selected.content, care))
        care.assert_not_called()
        self.assertEqual(worker.requests, before)
        self.assertEqual(coordinator.horoscope.index, 2)
        self.assertEqual(coordinator.horoscope.reading, day.reading)
        self.assertTrue(
            coordinator.horoscope_progress(
                DAY,
                len(selected.content.reaction.beats),
                completed=True,
            )
        )
        with open_database(self.path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            write_social_history(connection, coordinator.history)
            connection.commit()
        with open_database(self.path) as connection:
            connection.execute("BEGIN")
            finished = read_social_history(connection)
        restarted = SocialContentCoordinator(
            ManualSocialWorker(),
            history=finished,
            wall_time=lambda: NOW,
            zodiac_sign=lambda: "virgo",
        )
        restarted.set_enabled(True)
        self.assertEqual(restarted.select(SocialCategory.HOROSCOPE).status, "completed")

    def test_three_failed_attempts_survive_reload_and_sign_change(self) -> None:
        with open_database(self.path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            original = SocialContentHistory(horoscope=HoroscopeDay(DAY, attempts=3))
            write_social_history(connection, original)
            loaded = read_social_history(connection)
        worker = ManualSocialWorker()
        coordinator = SocialContentCoordinator(
            worker, history=loaded, wall_time=lambda: NOW, zodiac_sign=lambda: "leo"
        )
        coordinator.set_enabled(True)
        before = list(worker.requests)
        self.assertEqual(coordinator.select(SocialCategory.HOROSCOPE).status, "limited")
        self.assertEqual(worker.requests, before)

    def test_incompatible_progress_and_sign_are_not_defaulted_or_saved(self) -> None:
        expected = replace(social_history(), horoscope=admitted_day())
        assert expected.horoscope is not None
        with open_database(self.path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            write_social_history(connection, expected)
            invalid = replace(expected, horoscope=replace(expected.horoscope, index=12))
            with self.assertRaises(ValueError):
                write_social_history(connection, invalid)
            self.assertEqual(read_social_history(connection), expected)
            for statement in (
                "UPDATE horoscope_days SET progress_index = 12",
                "UPDATE horoscope_days SET sign = 'unknown'",
            ):
                write_social_history(connection, expected)
                connection.execute(statement)
                with self.assertRaises(ValueError):
                    read_social_history(connection)

    def test_failure_rolls_back_adaptive_settings_social_and_horoscope_as_one_snapshot(
        self,
    ) -> None:
        adaptive, settings = profile(), PetSettings(zodiac_sign="leo")
        history = replace(social_history(), horoscope=admitted_day())
        with open_database(self.path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            write_adaptive(connection, adaptive)
            write_settings(connection, settings)
            write_social_history(connection, history)
            connection.commit()
        with self.assertRaises(StorageError):
            with open_database(self.path) as connection:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute(
                    "UPDATE save_state SET revision = 2, lived_seconds = 90030"
                )
                write_adaptive(connection, AdaptiveMemory())
                write_settings(connection, PetSettings(zodiac_sign="virgo"))
                write_social_history(
                    connection,
                    SocialContentHistory(
                        horoscope=HoroscopeDay("2026-10-25"),
                    ),
                )
                connection.execute(
                    "INSERT INTO provider_pauses VALUES ('astroway', 1, -1, 0)"
                )
        with open_database(self.path) as connection:
            connection.execute("BEGIN")
            self.assertEqual(read_adaptive(connection), adaptive)
            self.assertEqual(read_settings(connection), settings)
            self.assertEqual(read_social_history(connection), history)
            self.assertEqual(
                connection.execute(
                    "SELECT revision, lived_seconds FROM save_state"
                ).fetchone(),
                (1, 90000),
            )


if __name__ == "__main__":
    unittest.main()
