"""Receipt order, provider identities and wall-clock pauses survive unchanged."""

from __future__ import annotations

import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from aiko_pet.application.horoscope_models import HoroscopeDay
from aiko_pet.application.social_content import (
    BUFFERED_CATEGORIES,
    SocialCategory,
    SocialProvider,
)
from aiko_pet.application.social_history import (
    SocialContentHistory,
    SocialContentReceipt,
)
from aiko_pet.application.social_requests import (
    SocialProviderBlock,
    SocialRequestHistory,
    SocialRequestReceipt,
)
from aiko_pet.infrastructure.sqlite.connection import open_database
from aiko_pet.infrastructure.sqlite.social_rows import (
    read_social_core,
    write_social_core,
)


def social_history() -> SocialContentHistory:
    entries = []
    for index in range(10):
        for offset, category in enumerate(BUFFERED_CATEGORIES):
            identity = (
                f"uselessfacts:fact-{index}"
                if category == SocialCategory.FACT
                else f"jokeapi:{100 + index}"
                if category == SocialCategory.TWO_PARTS
                else f"zitat-service:{index}"
                if index % 2 == 0
                else f"jokeapi:{index}"
            )
            entries.append(
                SocialContentReceipt(category, identity, f"{3 * index + offset:064x}")
            )
    requests = SocialRequestHistory(
        (
            SocialRequestReceipt(SocialProvider.FACTS, 1800000000.1234567),
            SocialRequestReceipt(SocialProvider.ASTROWAY, 1800000002.1234567),
            SocialRequestReceipt(SocialProvider.JOKEAPI, 1799999999.1234567),
        ),
        (
            SocialProviderBlock(SocialProvider.ASTROWAY, 1800003600.1234567),
            SocialProviderBlock(SocialProvider.FACTS, 1799999000.1234567),
        ),
    )
    return SocialContentHistory(tuple(entries), requests)


class SqliteSocialRowsTests(unittest.TestCase):
    def setUp(self) -> None:
        folder = tempfile.TemporaryDirectory(prefix="aiko-social-rows-")
        self.addCleanup(folder.cleanup)
        self.path = Path(folder.name) / "fixture.sqlite3"
        with open_database(self.path, initialize=True) as connection:
            connection.execute(
                "INSERT INTO save_state VALUES (1, 1, 1800000000, 90000)"
            )

    def test_thirty_mixed_receipts_and_wall_clock_requests_round_trip_without_pruning(
        self,
    ) -> None:
        original = social_history()
        with open_database(self.path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            write_social_core(connection, original)
            connection.commit()
        with open_database(self.path) as connection:
            connection.execute("BEGIN")
            restored = read_social_core(connection)
            self.assertEqual(restored, original)
            self.assertEqual(
                restored.requests.ready_at(SocialProvider.ASTROWAY, 1800000010),
                original.requests.ready_at(SocialProvider.ASTROWAY, 1800000010),
            )
            self.assertEqual(len(restored.requests.blocks), 2)

    def test_eleventh_admission_rotates_only_its_category_through_existing_owner(
        self,
    ) -> None:
        original = social_history()
        updated = original.admitted(
            SocialContentReceipt(
                SocialCategory.SINGLE,
                "zitat-service:999",
                f"{999:064x}",
            )
        )
        with open_database(self.path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            write_social_core(connection, original)
            write_social_core(connection, updated)
            self.assertEqual(read_social_core(connection), updated)
            self.assertEqual(
                connection.execute(
                    "SELECT category, count(*) FROM social_receipts "
                    "GROUP BY category ORDER BY category"
                ).fetchall(),
                [("fact", 10), ("single", 10), ("twopart", 10)],
            )

    def test_corrupt_or_excessive_present_history_is_not_defaulted_or_saved(
        self,
    ) -> None:
        original = social_history()
        with open_database(self.path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            write_social_core(connection, original)
            with self.assertRaises(ValueError):
                write_social_core(
                    connection, replace(original, entries=original.entries * 2)
                )
            self.assertEqual(read_social_core(connection), original)
            connection.execute(
                "UPDATE social_requests SET provider = 'unknown' "
                "WHERE position_index = 0"
            )
            with self.assertRaises(ValueError):
                read_social_core(connection)

    def test_partial_core_read_preserves_the_separate_daily_reading(self) -> None:
        original = social_history()
        template = SocialContentHistory(
            horoscope=HoroscopeDay("2026-10-24", attempts=2)
        )
        with open_database(self.path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            write_social_core(connection, original)
            self.assertEqual(
                read_social_core(connection, template),
                replace(original, horoscope=template.horoscope),
            )


if __name__ == "__main__":
    unittest.main()
