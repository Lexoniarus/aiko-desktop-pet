"""Durable learning stays distinct from fleeting sightings and own actions."""

import unittest
from dataclasses import replace

from aiko_pet.pet.mind.object_memory import ObjectMemory
from aiko_pet.pet.mind.object_perception import ObjectObservation


class ObjectMemoryTests(unittest.TestCase):
    def test_observed_relocation_preserves_identity_and_completed_inspection(self):
        memory = ObjectMemory()
        seen = ObjectObservation("one", "apple", "food", 100, 0, True, 1)
        memory.update((seen,), now=1)
        memory.mark_examined("one")
        memory.update((replace(seen, observed_at=2),), now=2)
        self.assertTrue(memory.snapshot()[0].examined)
        memory.update((), now=3)
        self.assertTrue(memory.snapshot()[0].examined)
        memory.update((replace(seen, x=200, observed_at=4),), now=4)
        self.assertTrue(memory.snapshot()[0].examined)
        self.assertEqual(memory.snapshot()[0].x, 200)

    def test_known_identity_survives_ten_minutes_without_revealing_hidden_changes(self):
        memory = ObjectMemory()
        seen = ObjectObservation("one", "apple", "food", 100, 0, True, 1)
        memory.update((seen,), now=1)
        memory.update((), now=100)
        self.assertEqual(memory.snapshot()[0].x, 100)
        memory.update((), now=10000)
        self.assertEqual(memory.snapshot()[0].identity, "apple")
        self.assertEqual(memory.snapshot()[0].x, 100)
        memory.forget("one")
        self.assertEqual(memory.snapshot(), ())

    def test_new_observed_location_retains_learned_identity(self):
        memory = ObjectMemory()
        seen = ObjectObservation("one", "apple", "food", 100, 0, True, 1)
        memory.update((seen,), now=1)
        memory.update((replace(seen, x=300, identity=None, kind=None,
                               observed_at=2),), now=2)
        self.assertEqual(memory.snapshot()[0].identity, "apple")
        self.assertEqual(memory.snapshot()[0].x, 300)
        memory.forget("one")
        self.assertEqual(memory.snapshot(), ())

    def test_only_unidentified_sightings_expire_after_600_active_seconds(self):
        memory = ObjectMemory()
        memory.update((ObjectObservation("one", None, None, 100, 0, True, 1),), now=1)
        memory.mark_examined("one")
        self.assertFalse(memory.snapshot()[0].examined)
        memory.update((), now=601)
        self.assertEqual(len(memory.snapshot()), 1)
        memory.update((), now=601.1)
        self.assertEqual(memory.snapshot(), ())

    def test_conflicting_recognition_invalidates_inspection_and_disposition(self):
        memory = ObjectMemory()
        seen = ObjectObservation("one", "apple", "food", 100, 0, True, 1)
        memory.update((seen,), now=1)
        memory.mark_examined("one")
        memory.note_placement("one", x=200, height=0, now=2, deferred=True)
        memory.update((replace(seen, identity="onigiri", observed_at=3),), now=3)
        known = memory.snapshot()[0]
        self.assertEqual(known.identity, "onigiri")
        self.assertFalse(known.examined)
        self.assertIsNone(known.disposition)

    def test_portable_snapshot_reanchors_age_without_manufacturing_offline_time(self):
        memory = ObjectMemory()
        memory.update((ObjectObservation("one", None, None, 100, 0, True, 5000),),
                      now=5000)
        saved = memory.export(now=5500)
        self.assertEqual(saved.entries[0].age_seconds, 500)
        restored = ObjectMemory(saved, now=0)
        self.assertEqual(restored.snapshot()[0].observed_at, -500)
        restored.update((), now=100)
        self.assertEqual(len(restored.snapshot()), 1)
        restored.update((), now=101)
        self.assertEqual(restored.snapshot(), ())

    def test_own_placement_distinguishes_deliberate_reserve_from_interruption(self):
        memory = ObjectMemory()
        memory.update((ObjectObservation("one", "apple", "food", 100, 0, False, 1),),
                      now=1)
        memory.mark_examined("one")
        memory.note_placement("one", x=200, height=0, now=2, deferred=True)
        known = memory.snapshot()[0]
        self.assertEqual((known.x, known.resting, known.disposition),
                         (200, True, "deferred"))
        restored = ObjectMemory(memory.export(now=10000))
        self.assertTrue(restored.snapshot()[0].examined)
        self.assertEqual(restored.snapshot()[0].disposition, "deferred")
        memory.note_placement("one", x=300, height=0, now=3, deferred=False)
        self.assertEqual(memory.snapshot()[0].disposition, "interrupted")
