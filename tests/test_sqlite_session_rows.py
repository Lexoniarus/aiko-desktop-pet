"""One read assembles all existing owners without changing any saved clock."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_sqlite_adaptive_rows import profile
from test_sqlite_care_evidence import complete_emotional_state
from test_sqlite_food_handovers import handover_state
from test_sqlite_horoscope import admitted_day

from aiko_pet.application.session import PetSessionRestorer
from aiko_pet.application.settings import PetSettings
from aiko_pet.application.social_history import SocialContentHistory
from aiko_pet.application.storage_contracts import SaveRevision
from aiko_pet.infrastructure.sqlite.connection import open_database
from aiko_pet.infrastructure.sqlite.session_rows import (
    read_session_rows,
    write_session_rows,
)
from aiko_pet.pet.state import PetState


class SqliteSessionRowsTests(unittest.TestCase):
    def setUp(self) -> None:
        folder = tempfile.TemporaryDirectory(prefix="aiko-session-rows-")
        self.addCleanup(folder.cleanup)
        self.path = Path(folder.name) / "fixture.sqlite3"

    def test_all_pet_and_application_owners_share_the_same_revision_and_time(
        self,
    ) -> None:
        pet = PetState(
            updated_at=1800000000,
            lived_seconds=100000,
            moodlets=complete_emotional_state(),
            wishes=handover_state(),
        )
        settings, adaptive = PetSettings(zodiac_sign="leo"), profile()
        history = SocialContentHistory(horoscope=admitted_day())
        with open_database(self.path, initialize=True) as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                "INSERT INTO save_state VALUES (1, 7, 1800000000, 100000)"
            )
            write_session_rows(
                connection,
                pet.capture_checkpoint(),
                settings,
                adaptive=adaptive,
                social_history=history,
                world=None,
                object_memory=None,
                world_recovery_x=0,
            )
            connection.commit()
        with (
            open_database(self.path) as connection,
            patch.object(
                PetState,
                "advance",
                side_effect=AssertionError("Storage must not advance time"),
            ),
        ):
            connection.execute("BEGIN")
            loaded = read_session_rows(connection, ())
        self.assertEqual(loaded.state.capture_checkpoint(), pet.capture_checkpoint())
        self.assertEqual(
            (loaded.settings, loaded.adaptive_memory, loaded.social_history),
            (settings, adaptive, history),
        )
        self.assertEqual(loaded.revision, SaveRevision(7))
        self.assertTrue(loaded.restored_from_save)
        self.assertIsNone(loaded.world)

        class Reader:
            def load_session(self, *, now: float | None = None):
                return loaded

        restored = PetSessionRestorer(Reader(), wall_time=lambda: 1800000000).restore()
        self.assertEqual(restored.revision, SaveRevision(7))

    def test_partial_database_is_not_returned_as_a_fresh_replacement_pet(self) -> None:
        with open_database(self.path, initialize=True) as connection:
            connection.execute("BEGIN")
            with self.assertRaises(ValueError):
                read_session_rows(connection, ())


if __name__ == "__main__":
    unittest.main()
