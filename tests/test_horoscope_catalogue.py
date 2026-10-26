"""The packaged local book has reviewed coverage and matching Aiko comments."""

import json
import unittest
from collections import Counter
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from aiko_pet.infrastructure.astronomy import AstronomyEngineCalculator
from aiko_pet.infrastructure.character_mind import make_aiko_mind
from aiko_pet.infrastructure.horoscope_catalogue import (
    catalogue_coverage,
    load_horoscope_catalogue,
)
from aiko_pet.pet.emotions import EmotionalComposition, EmotionalState
from aiko_pet.pet.horoscope import (
    ZODIAC_SIGNS,
    SkySnapshot,
    build_profile,
    phase_direction,
    select_entry,
    sign_at,
)
from aiko_pet.pet.mind.dialogue_context import DialogueContext, FriendshipStage
from aiko_pet.pet.routine import context_at


class HoroscopeCatalogueTests(unittest.TestCase):
    def test_exact_reviewed_matrix_and_all_sign_selection(self):
        catalogue = load_horoscope_catalogue()
        self.assertEqual(len(catalogue.entries), 96)
        self.assertFalse(catalogue_coverage(catalogue).missing)
        cells = Counter((e.theme, e.direction) for e in catalogue.entries)
        self.assertEqual(len(cells), 48)
        self.assertEqual(set(cells.values()), {2})
        for sign in ZODIAC_SIGNS:
            for phase in (0, 90, 180, 270):
                for moon in range(0, 360, 30):
                    sky = SkySnapshot(
                        datetime(2026, 1, 1, tzinfo=timezone.utc),
                        10,
                        moon,
                        phase,
                        "fixture",
                    )
                    profile = build_profile(sign, sky)
                    entry = select_entry(catalogue, profile, "stable")
                    self.assertIsNotNone(entry)
                    self.assertEqual(
                        entry,
                        select_entry(
                            replace(
                                catalogue, entries=tuple(reversed(catalogue.entries))
                            ),
                            profile,
                            "stable",
                        ),
                    )
        self.assertTrue(
            all(len(p.text) <= 125 for e in catalogue.entries for p in e.passages)
        )

    def test_actual_engine_and_cyclic_boundaries(self):
        sky = AstronomyEngineCalculator().calculate(
            datetime(2026, 10, 25, 12, tzinfo=timezone.utc)
        )
        self.assertEqual(sign_at(sky.sun_longitude), "scorpio")
        self.assertEqual(sign_at(360), "aries")
        for angle, direction in (
            (0, "begin"),
            (90, "develop"),
            (180, "reflect"),
            (270, "conclude"),
            (360, "begin"),
        ):
            self.assertEqual(phase_direction(angle), direction)

    def test_all_comment_keys_have_four_stages_and_respect_feeling(self):
        book = make_aiko_mind(started_at=0).book
        keys = {
            p.comment_key
            for e in load_horoscope_catalogue().entries
            for p in e.passages
            if p.comment_key
        }
        self.assertEqual(len(keys), 24)
        for key in keys:
            for stage in FriendshipStage:
                context = DialogueContext(
                    stage,
                    50,
                    EmotionalComposition(EmotionalState.CALM),
                    context_at(1792929600),
                    horoscope_comment_key=key,
                )
                self.assertIsNotNone(book.choose("horoscope_comment", context, 0))
                tense = replace(
                    context, emotions=EmotionalComposition(EmotionalState.TENSE)
                )
                self.assertIsNone(book.choose("horoscope_comment", tense, 0))

    def test_packaged_entries_match_editorial_source(self):
        root = Path(__file__).resolve().parents[1]
        index = json.loads(
            (root / "aiko_pet/data/horoscope/de/index.json").read_text(encoding="utf-8")
        )
        runtime = [
            e
            for name in index["files"]
            for e in json.loads(
                (root / "aiko_pet/data/horoscope/de" / name).read_text(encoding="utf-8")
            )["entries"]
        ]
        source = json.loads(
            (root / "docs/horoscope/pilot-book-entries.de.json").read_text(
                encoding="utf-8"
            )
        )["entries"]
        self.assertEqual(
            sorted(runtime, key=lambda e: e["id"]),
            sorted(source, key=lambda e: e["id"]),
        )
