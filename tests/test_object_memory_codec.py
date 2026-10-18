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
        memory.mark_assessed("object_9")
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

    def test_unknown_sighting_stays_unknown_and_unassessed(self):
        raw = deepcopy(self.raw)
        raw["entries"][0].update(identity=None, kind=None, assessed=False,
                                  disposition=None)
        known = ObjectMemory(decode_object_memory(raw, IDENTITIES)).snapshot()[0]
        self.assertIsNone(known.identity)
        self.assertFalse(known.assessed)

    def test_v1_conversion_keeps_history_without_a_live_binding(self):
        raw = deepcopy(self.raw)
        raw["version"] = 1
        del raw["next_record_id"], raw["world_next_id"]
        row = raw["entries"][0]
        del row["instance_id"]
        row["examined"] = row.pop("assessed")
        del row["place_status"], row["possible_sources"]
        restored = decode_object_memory(raw, IDENTITIES, allocated_until=10)
        self.assertEqual(restored, self.saved)
        with self.assertRaises(ValueError):
            decode_object_memory(raw, IDENTITIES, allocated_until=1)

    def test_v2_conversion_preserves_history_without_inventing_reference(self):
        raw = deepcopy(self.raw)
        raw["version"] = 2
        for row in raw["entries"]:
            del row["instance_id"]
        self.assertEqual(decode_object_memory(raw, IDENTITIES), self.saved)

    def test_learned_reference_round_trip_and_allocation_validation(self):
        raw = deepcopy(self.raw)
        raw["world_next_id"] = 10
        raw["entries"][0]["instance_id"] = "object_9"
        saved = decode_object_memory(raw, IDENTITIES, allocated_until=10)
        self.assertEqual(saved.entries[0].instance_id, "object_9")
        self.assertEqual(decode_object_memory(
            encode_object_memory(saved, world_next_id=10), IDENTITIES,
        ), saved)
        for instance in ("object_0", "object_10", "memory_9", [], True):
            with self.subTest(instance=instance):
                invalid = deepcopy(raw)
                invalid["entries"][0]["instance_id"] = instance
                with self.assertRaises(ValueError):
                    decode_object_memory(invalid, IDENTITIES)
        other = deepcopy(raw["entries"][0])
        other["token"] = "object_8"
        raw["entries"].append(other)
        with self.assertRaises(ValueError):
            decode_object_memory(raw, IDENTITIES)

    def test_unknown_sighting_cannot_store_a_learned_reference(self):
        raw = deepcopy(self.raw)
        raw["world_next_id"] = 10
        raw["entries"][0].update(identity=None, kind=None, assessed=False,
                                  disposition=None, instance_id="object_9")
        with self.assertRaises(ValueError):
            decode_object_memory(raw, IDENTITIES)

    def test_associations_reject_missing_self_and_cyclic_references(self):
        for sources in (["missing"], ["object_9"], ["object_10", "object_10"]):
            with self.subTest(sources=sources):
                raw = deepcopy(self.raw)
                raw["entries"][0]["possible_sources"] = sources
                with self.assertRaises(ValueError):
                    decode_object_memory(raw, IDENTITIES)
        raw = deepcopy(self.raw)
        other = deepcopy(raw["entries"][0])
        other.update(token="object_10", possible_sources=["object_9"])
        raw["entries"][0]["possible_sources"] = ["object_10"]
        raw["entries"].append(other)
        with self.assertRaises(ValueError):
            decode_object_memory(raw, IDENTITIES)

    def test_invalid_flags_ids_numbers_and_experiences_are_rejected(self):
        cases = (
            ("token", "object_0"), ("token", []), ("identity", "unknown_food"),
            ("kind", "food"), ("kind", []), ("x", -1), ("height", math.nan),
            ("age_seconds", math.inf), ("age_seconds", True), ("resting", 1),
            ("assessed", 0), ("disposition", []), ("disposition", "stored"),
            ("assessed", False),
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
