"""Qualified cursor facts only affect their own persisted moodlet families."""

import unittest
from dataclasses import replace
from typing import Literal

from aiko_pet.infrastructure.moodlet_codec import decode_moodlets, encode_moodlets
from aiko_pet.pet.cursor_experiences import apply_cursor_experience
from aiko_pet.pet.interaction_events import CursorExperience
from aiko_pet.pet.moodlet_catalog import MOODLET_CATALOG
from aiko_pet.pet.moodlet_types import MoodletId
from aiko_pet.pet.state import PetState


class CursorExperienceTests(unittest.TestCase):
    def test_absolute_strength_weaker_revision_and_both_families(self):
        pet = PetState(lived_seconds=100)
        facts: tuple[tuple[str, Literal["curiosity", "fear"], int], ...] = (
            ("one", "curiosity", 2),
            ("two", "curiosity", 2),
            ("three", "curiosity", 1),
            ("four", "fear", 3),
        )
        for receipt, feeling, level in facts:
            pet.experience_cursor(CursorExperience(receipt, feeling, level))
        self.assertEqual(
            [(e.definition_id, e.level) for e in pet.moodlets.active],
            [(MoodletId.CURSOR_CURIOSITY, 2), (MoodletId.CURSOR_FEAR, 3)],
        )
        self.assertEqual(
            decode_moodlets(encode_moodlets(pet.moodlets), 100), pet.moodlets
        )

    def test_duplicate_delivery_and_saved_receipt_are_noops(self):
        pet = PetState(lived_seconds=100)
        event = CursorExperience("session:one", "fear", 2)
        pet.experience_cursor(event)
        prior = pet.capture_checkpoint()
        pet.experience_cursor(event)
        self.assertEqual(pet.capture_checkpoint(), prior)
        loaded = decode_moodlets(encode_moodlets(pet.moodlets), 100)
        self.assertIs(
            apply_cursor_experience(
                loaded, event, elapsed=100, definitions=MOODLET_CATALOG.definitions
            ),
            loaded,
        )
        pet.experience_cursor(CursorExperience("next-session:one", "fear", 2))
        self.assertEqual(len(pet.moodlets.active[0].causes), 2)

    def test_no_care_wish_relationship_or_instant_mood_mutation(self):
        pet = PetState(lived_seconds=100)
        before = pet.capture_checkpoint()
        pet.experience_cursor(CursorExperience("actual:1", "curiosity", 3))
        after = pet.capture_checkpoint()
        self.assertEqual(replace(after, moodlets=before.moodlets), before)
        self.assertEqual(after.moodlets.care_evidence, before.moodlets.care_evidence)

    def test_invalid_endpoint_does_not_partially_mutate(self):
        pet = PetState(lived_seconds=100)
        pet.experience_cursor(CursorExperience("latest", "fear", 2))
        original = pet.capture_checkpoint()
        with self.assertRaises(ValueError):
            apply_cursor_experience(
                pet.moodlets,
                CursorExperience("older", "fear", 3),
                elapsed=99,
                definitions=MOODLET_CATALOG.definitions,
            )
        self.assertEqual(pet.capture_checkpoint(), original)
        for level in (0, 4, True):
            with self.assertRaises(ValueError):
                CursorExperience("bad", "fear", level)
