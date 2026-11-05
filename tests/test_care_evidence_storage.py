"""Precise emotional facts survive storage and rollback without replaying activity."""

import copy
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from support.care import CARE_EVIDENCE_STORAGE_ELAPSED as ELAPSED
from support.care import CARE_EVIDENCE_STORAGE_WALL as WALL
from support.care import emotional_state

from aiko_pet.application.settings import PetSettings
from aiko_pet.frontend.view_models.moodlet_causes import cause_description
from aiko_pet.infrastructure.moodlet_codec import decode_moodlets, encode_moodlets
from aiko_pet.infrastructure.persistence import StateStore
from aiko_pet.infrastructure.pet_codec import decode_pet_state, encode_pet_state
from aiko_pet.pet.moodlets import (
    MoodletEpisode,
    MoodletId,
    MoodletState,
)
from aiko_pet.pet.state import PetState
from tools.persistence_test_support import save_test_session
from tools.pet_test_support import require_test_value


class CareEvidenceStorageTests(unittest.TestCase):
    def test_whole_pet_store_and_checkpoint_preserve_budgets_and_original_facts(self):
        pet = PetState(
            updated_at=WALL, lived_seconds=ELAPSED, moodlets=emotional_state()
        )
        checkpoint = pet.capture_checkpoint()
        raw = json.loads(json.dumps(encode_pet_state(pet), allow_nan=False))
        self.assertEqual(
            decode_pet_state(raw, now=WALL).capture_checkpoint(), checkpoint
        )
        with tempfile.TemporaryDirectory() as folder:
            store = StateStore(Path(folder) / "state.json")
            save_test_session(store, pet, PetSettings())
            loaded = store.load_session(now=WALL).state
        self.assertEqual(loaded.capture_checkpoint(), checkpoint)
        loaded.restore_checkpoint(replace(checkpoint, moodlets=MoodletState()))
        loaded.restore_checkpoint(checkpoint)
        self.assertEqual(loaded.moodlets.active[1].lower_stage_seconds, (4200, 2700))
        # One real two-tier outcome remains one cause, including its free-choice goal.
        self.assertEqual(len(loaded.moodlets.active[1].causes), 1)
        self.assertIn(
            "Länger anhaltendes Erlebnis",
            cause_description(loaded.moodlets.active[0].causes[0]),
        )
        self.assertFalse(loaded.wishes.active)
        food_cause = cause_description(loaded.moodlets.active[2].causes[0])
        self.assertIn("Wunsch gescheitert", food_cause)
        self.assertNotIn("Spielwunsch", food_cause)
        self.assertEqual(copy.deepcopy(pet).capture_checkpoint(), checkpoint)

    def test_missing_legacy_fields_do_not_invent_budgets_periods_or_encounters(self):
        old = MoodletState(
            100, 2, (MoodletEpisode(1, MoodletId.PRIDE, 2, 100, 100, 7200),)
        )
        raw = encode_moodlets(old)
        del raw["active"][0]["lower_stage_seconds"]
        for cause in raw["active"][0]["causes"]:
            del cause["period"]
            del cause["handed_over_at"]
        loaded = decode_moodlets(raw, ELAPSED)
        self.assertEqual(loaded, old)
        self.assertIsNone(loaded.care_evidence)
        self.assertEqual(loaded.active[0].lower_stage_seconds, ())
        self.assertEqual(loaded.active[0].remaining_seconds, 7200)

    def test_family_watermarks_are_independent_and_summary_outlives_raw_evidence(self):
        original = emotional_state()
        restored = decode_moodlets(encode_moodlets(original), ELAPSED)
        pending = replace(original, active=())
        self.assertFalse(decode_moodlets(encode_moodlets(pending), ELAPSED).active)
        progress = require_test_value(restored.care_evidence).progress
        self.assertEqual([p.processed_until for p in progress], [86400, 0])
        without_raw = replace(restored, care_evidence=None)
        self.assertEqual(
            decode_moodlets(encode_moodlets(without_raw), ELAPSED), without_raw
        )
        self.assertEqual(
            require_test_value(without_raw.active[0].causes[0].period).encounters, 3
        )

    def test_bad_stage_budgets_and_mismatched_original_causes_are_rejected(self):
        original = encode_moodlets(emotional_state())
        for mutate in (
            lambda r: r["active"][0].update(lower_stage_seconds=[100]),
            lambda r: r["active"][1].update(lower_stage_seconds=[100]),
            lambda r: r["active"][1].update(lower_stage_seconds=[100, 5401]),
            lambda r: r["active"][1].update(lower_stage_seconds=[100, True]),
            lambda r: r["active"][1]["causes"][0].update(target_id=None),
            lambda r: r["active"][2]["causes"][0].update(target_id="apple"),
            lambda r: r["active"][2]["causes"][0].update(handed_over_at=88001),
            lambda r: r["active"][0]["causes"][0]["period"].update(ended_at=86000),
            lambda r: r["active"][0]["causes"][0]["period"].update(encounters=True),
            lambda r: r["active"][0]["causes"][0].update(kind="interaction"),
        ):
            raw = copy.deepcopy(original)
            mutate(raw)
            with self.assertRaises(ValueError):
                decode_moodlets(raw, ELAPSED)
