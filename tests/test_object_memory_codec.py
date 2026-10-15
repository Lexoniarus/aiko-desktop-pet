"""Memory wire values preserve subjective facts without session clocks or truth."""

import math
import unittest
from copy import deepcopy

from aiko_pet.infrastructure.object_memory_codec import (
    decode_object_memory,
    encode_object_memory,
)
from aiko_pet.pet.mind.object_memory import ObjectMemory
from aiko_pet.pet.mind.object_perception import ConsumableKind, ObjectObservation

IDENTITIES: dict[str, ConsumableKind] = {"apple": "food", "energy_drink": "drink"}


class ObjectMemoryCodecTests(unittest.TestCase):
    def setUp(self):
        memory = ObjectMemory()
        memory.update((ObjectObservation(
            "object_9", "energy_drink", "drink", 700, 0, True, 9000,
        ),), now=9000)
        memory.mark_examined("object_9")
        memory.note_placement("object_9", x=650, height=0, now=9001, deferred=True)
        self.saved = memory.export(now=9999)
        self.raw = encode_object_memory(self.saved)

    def test_round_trip_preserves_old_location_experience_and_relative_age(self):
        restored = decode_object_memory(self.raw, IDENTITIES)
        self.assertEqual(restored, self.saved)
        self.assertEqual(self.raw["entries"][0]["age_seconds"], 998)
        self.assertNotIn("observed_at", self.raw["entries"][0])
        # No current World or session clock is required to restore learned facts.
        known = ObjectMemory(restored).snapshot()[0]
        self.assertEqual((known.x, known.observed_at, known.disposition),
                         (650, -998, "deferred"))

    def test_unknown_sighting_stays_unknown_and_unexamined(self):
        raw = deepcopy(self.raw)
        raw["entries"][0].update(identity=None, kind=None, examined=False,
                                  disposition=None)
        known = ObjectMemory(decode_object_memory(raw, IDENTITIES)).snapshot()[0]
        self.assertIsNone(known.identity)
        self.assertFalse(known.examined)

    def test_invalid_flags_ids_numbers_and_experiences_are_rejected(self):
        cases = (
            ("token", "object_0"), ("token", []), ("identity", "unknown_food"),
            ("kind", "food"), ("kind", []), ("x", -1), ("height", math.nan),
            ("age_seconds", math.inf), ("age_seconds", True), ("resting", 1),
            ("examined", 0), ("disposition", []), ("disposition", "stored"),
            ("examined", False),
        )
        for field, value in cases:
            with self.subTest(field=field, value=value):
                raw = deepcopy(self.raw)
                raw["entries"][0][field] = value
                with self.assertRaises(ValueError):
                    decode_object_memory(raw, IDENTITIES)

    def test_future_version_duplicate_ids_and_extra_fields_are_rejected(self):
        for change in ("version", "duplicate", "extra"):
            with self.subTest(change=change):
                raw = deepcopy(self.raw)
                if change == "version":
                    raw["version"] = 999
                elif change == "duplicate":
                    raw["entries"].append(deepcopy(raw["entries"][0]))
                else:
                    raw["entries"][0]["current_goal"] = True
                with self.assertRaises(ValueError):
                    decode_object_memory(raw, IDENTITIES)
