"""Original words belong to bounded active causes, not repetition receipts."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from dataclasses import replace
from pathlib import Path
from typing import Any

from aiko_pet.application.settings import PetSettings
from aiko_pet.application.social_content import SocialCategory, SocialProvider
from aiko_pet.infrastructure.moodlet_cause_codec import (
    decode_moodlet_causes,
    encode_moodlet_cause,
)
from aiko_pet.infrastructure.sqlite.moodlet_cause_rows import read_causes
from aiko_pet.infrastructure.sqlite.store import SqliteStateStore
from aiko_pet.pet.moodlets import (
    MoodletAttribution,
    MoodletCause,
    MoodletCauseKind,
    MoodletEpisode,
    MoodletId,
    MoodletOutcome,
    MoodletState,
)
from aiko_pet.pet.social_content_evidence import (
    SocialCategory as DomainCategory,
)
from aiko_pet.pet.social_content_evidence import (
    SocialContentEvidence,
)
from aiko_pet.pet.state import PetState
from tools.persistence_test_support import save_test_session

WALL = 1800000000


def evidence(
    category: SocialCategory = SocialCategory.SINGLE,
    provider: SocialProvider = SocialProvider.JOKEAPI,
    *, text: str = "Ein vollständiger Testtext.",
) -> SocialContentEvidence:
    parts = (text, "Eine vollständige Testantwort.") if (
        category == SocialCategory.TWO_PARTS
    ) else (text,)
    return SocialContentEvidence(
        category, provider, f"{provider.value}:1",
        hashlib.sha256(" ".join(parts).casefold().encode()).hexdigest(), parts,
        "Testquelle", "https://example.org/source", "https://example.org/content",
        "Testautor" if provider == SocialProvider.QUOTATIONS else "",
        "https://example.org/author" if provider == SocialProvider.QUOTATIONS else "",
        "CC BY 4.0" if provider == SocialProvider.QUOTATIONS else "",
        "https://creativecommons.org/licenses/by/4.0/"
        if provider == SocialProvider.QUOTATIONS else "",
    )


def social_cause(content: SocialContentEvidence) -> MoodletCause:
    return MoodletCause(
        MoodletCauseKind.INTERACTION, 50, "social:actual",
        MoodletAttribution.USER, target_id=content.category.value,
        outcome=MoodletOutcome.COMPLETED, social_content=content,
    )


def decode_cause(raw: dict[str, Any]) -> tuple[MoodletCause, ...]:
    return decode_moodlet_causes(
        [raw], started=50, trigger=50, key=MoodletId.CONNECTION, baseline=0,
    )


class SocialEvidenceContractTests(unittest.TestCase):
    def test_canonical_vocabulary_and_four_original_formats_round_trip(self):
        self.assertIs(SocialCategory, DomainCategory)
        for category, provider, kind in (
            (SocialCategory.SINGLE, SocialProvider.JOKEAPI, "one_liner"),
            (SocialCategory.SINGLE, SocialProvider.QUOTATIONS, "quotation"),
            (SocialCategory.TWO_PARTS, SocialProvider.JOKEAPI, "two_part"),
            (SocialCategory.FACT, SocialProvider.FACTS, "fact"),
        ):
            with self.subTest(kind=kind):
                content = evidence(category, provider)
                self.assertEqual(content.kind, kind)
                cause = social_cause(content)
                self.assertEqual(decode_cause(encode_moodlet_cause(cause)), (cause,))
                legacy = replace(cause, social_content=None)
                self.assertNotIn("social_content", encode_moodlet_cause(legacy))
                self.assertEqual(decode_cause(encode_moodlet_cause(legacy)), (legacy,))

    def test_malformed_originals_and_incompatible_causes_fail_strictly(self):
        original = social_cause(evidence())
        for update in (
            {"parts": []}, {"parts": ["Changed after validation."]},
            {"parts": "not a list"}, {"parts": [False]},
            {"category": "horoscope"}, {"provider": "uselessfacts"},
            {"identity": "jokeapi:bad"}, {"fingerprint": True},
            {"source": None}, {"source_url": "file:///private"},
            {"permalink": ""}, {"author": 5}, {"unexpected": "field"},
        ):
            raw = encode_moodlet_cause(original)
            raw["social_content"].update(update)
            with self.subTest(update=update), self.assertRaises(ValueError):
                decode_cause(raw)
        for update in (
            {"target_id": "fact"}, {"outcome": MoodletOutcome.LOSS},
            {"kind": MoodletCauseKind.LEGACY}, {"object_id": "object:1"},
        ):
            with self.subTest(update=update), self.assertRaises(ValueError):
                replace(original, **update)
        with self.assertRaises(ValueError):
            replace(evidence(), parts=["Mutable parts"])  # type: ignore[arg-type]


class SocialEvidenceStorageTests(unittest.TestCase):
    def test_sqlite_reopens_old_and_original_content_and_removes_trimmed_bodies(self):
        causes = tuple(replace(
            social_cause(evidence(text=f"Originaler Testinhalt {number}.")),
            occurred_at=10 * number, event_id=f"social:{number}",
        ) for number in range(1, 6))
        episode = MoodletEpisode(
            1, MoodletId.CONNECTION, 3, 10, 50, 7200, causes=causes,
        )
        pet = PetState(
            updated_at=WALL, lived_seconds=100,
            moodlets=MoodletState(next_instance_id=2, active=(episode,)),
        )
        with tempfile.TemporaryDirectory(prefix="aiko-social-evidence-") as folder:
            path = Path(folder) / "state.sqlite3"
            for active, count in (
                ((episode,), 3), ((replace(episode, level=1),), 1),
                ((replace(episode, level=1, causes=(replace(
                    causes[-1], social_content=None,
                ),)),), 1), ((), 0),
            ):
                pet._change(moodlets=replace(pet.moodlets, active=active))
                save_test_session(SqliteStateStore(path), pet, PetSettings())
                loaded = SqliteStateStore(path).load_session(now=WALL).state
                self.assertEqual(loaded.moodlets, pet.moodlets)
                with closing(sqlite3.connect(path)) as connection:
                    snapshots = [json.loads(row[0]) for row in connection.execute(
                        "SELECT details_snapshot FROM moodlet_causes "
                        "ORDER BY position_index"
                    )]
                    self.assertEqual(len(snapshots), count)
                    expected = [
                        cause.social_content for e in active for cause in e.causes
                    ]
                    self.assertEqual([row["version"] for row in snapshots], [
                        3 if content is not None else 1 for content in expected
                    ])
                    for row, content in zip(snapshots, expected, strict=True):
                        if content is not None:
                            self.assertEqual(row["social_content"]["parts"],
                                             list(content.parts))

    def test_sqlite_rejects_wrong_version_missing_or_mixed_content_envelopes(self):
        with tempfile.TemporaryDirectory(prefix="aiko-social-envelope-") as folder:
            path = Path(folder) / "state.sqlite3"
            cause = social_cause(evidence())
            pet = PetState(updated_at=WALL, lived_seconds=100, moodlets=MoodletState(
                next_instance_id=2, active=(MoodletEpisode(
                    1, MoodletId.CONNECTION, 1, 50, 50, 7200, causes=(cause,),
                ),),
            ))
            save_test_session(SqliteStateStore(path), pet, PetSettings())
            with closing(sqlite3.connect(path)) as connection:
                for extra in (
                    dict(version=True), dict(version=3),
                    dict(version=3, social_content=None),
                    dict(version=2, social_content={}),
                    dict(version=1, social_content={}),
                    dict(version=3, social_content={}, game_details={}),
                ):
                    connection.execute(
                        "UPDATE moodlet_causes SET details_snapshot = ?",
                        (json.dumps(dict(game=None, period=None) | extra),),
                    )
                    with self.subTest(extra=extra), self.assertRaises(ValueError):
                        read_causes(connection)


if __name__ == "__main__":
    unittest.main()
