"""Qualified cursor facts only affect their own persisted moodlet families."""

import unittest
from dataclasses import replace
from typing import Literal

from aiko_pet.infrastructure.moodlet_codec import decode_moodlets, encode_moodlets
from aiko_pet.pet.cursor_experiences import (
    active_cursor_feeling,
    apply_cursor_experience,
)
from aiko_pet.pet.interaction_events import CursorExperience
from aiko_pet.pet.moodlet_catalog import MOODLET_CATALOG
from aiko_pet.pet.moodlet_types import MoodletId
from aiko_pet.pet.state import PetState


class CursorExperienceTests(unittest.TestCase):
    def test_absolute_strength_and_new_feeling_replaces_previous_family(self):
        pet = PetState(lived_seconds=100)
        facts: tuple[tuple[str, Literal["curiosity", "fear"], int], ...] = (
            ("one", "curiosity", 2),
            ("two", "curiosity", 2),
            ("three", "curiosity", 1),
            ("four", "fear", 3),
        )
        for receipt, feeling, level in facts:
            pet.experience_cursor(CursorExperience(receipt, feeling, level))
            if feeling == "curiosity":
                self.assertEqual(pet.moodlets.active[0].level, 2)
        self.assertEqual(
            [(e.definition_id, e.level) for e in pet.moodlets.active],
            [(MoodletId.CURSOR_FEAR, 3)],
        )
        self.assertEqual(
            decode_moodlets(encode_moodlets(pet.moodlets), 100), pet.moodlets
        )
        fear_id = pet.moodlets.active[0].instance_id
        pet.experience_cursor(CursorExperience("five", "curiosity", 1))
        self.assertEqual(len(pet.moodlets.active), 1)
        self.assertEqual(
            pet.moodlets.active[0].definition_id, MoodletId.CURSOR_CURIOSITY,
        )
        self.assertEqual(pet.moodlets.active[0].level, 1)
        self.assertGreater(pet.moodlets.active[0].instance_id, fear_id)

    def test_legacy_mixed_json_keeps_newest_with_exact_budget_and_metadata(self):
        curious = PetState(lived_seconds=100)
        fearful = PetState(lived_seconds=100)
        curious.experience_cursor(CursorExperience("earlier", "curiosity", 3))
        fearful.experience_cursor(CursorExperience("later", "fear", 2))
        first = encode_moodlets(curious.moodlets)["active"][0]
        second = encode_moodlets(fearful.moodlets)["active"][0]
        first.update(instance_id=1, started_at=90, last_trigger_at=90)
        first["causes"][0]["occurred_at"] = 90
        second["instance_id"] = 2
        raw = dict(version=1, baseline=0, next_instance_id=3, active=[first, second])
        loaded = decode_moodlets(raw, 100)
        self.assertEqual(active_cursor_feeling(loaded), "fear")
        self.assertEqual(encode_moodlets(loaded)["active"], [second])
        self.assertEqual(loaded.next_instance_id, 3)
        # A genuinely newer positive impression wins irrespective of old strength.
        first["last_trigger_at"] = 100
        first["causes"][0]["occurred_at"] = 100
        second.update(started_at=95, last_trigger_at=95)
        second["causes"][0]["occurred_at"] = 95
        loaded = decode_moodlets(raw, 100)
        self.assertEqual(active_cursor_feeling(loaded), "curiosity")
        self.assertEqual(encode_moodlets(loaded)["active"], [first])

    def test_equal_legacy_timestamps_prefer_fear_in_either_storage_order(self):
        encoded = []
        for n, feeling in enumerate(("curiosity", "fear"), 1):
            pet = PetState(lived_seconds=100)
            pet.experience_cursor(CursorExperience(f"old:{n}", feeling, 1))
            row = encode_moodlets(pet.moodlets)["active"][0]
            row["instance_id"] = n
            encoded.append(row)
        for rows in (encoded, list(reversed(encoded))):
            result = decode_moodlets(dict(
                version=1, baseline=0, next_instance_id=3, active=rows,
            ), 100)
            self.assertEqual(active_cursor_feeling(result), "fear")
            self.assertEqual(result.active[0].instance_id, 2)

    def test_expired_impression_is_not_an_active_turning_mode(self):
        pet = PetState(lived_seconds=100)
        pet.experience_cursor(CursorExperience("old", "curiosity", 1))
        expired = replace(pet.moodlets, active=(replace(
            pet.moodlets.active[0], remaining_seconds=0,
        ),))
        self.assertIsNone(active_cursor_feeling(expired))

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
