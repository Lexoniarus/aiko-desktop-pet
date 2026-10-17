"""Durable learning stays distinct from fleeting sightings and own actions."""

import unittest
from dataclasses import replace

from aiko_pet.pet.mind.object_memory import ObjectMemory
from aiko_pet.pet.mind.object_perception import ObjectObservation


class ObjectMemoryTests(unittest.TestCase):
    def test_unknown_find_at_confirmed_empty_place_does_not_inherit_identity(self):
        memory = ObjectMemory()
        memory.update((ObjectObservation(
            "old", "cookie", "food", 100, 0, True, 0,
        ),), now=0)
        memory.mark_assessed("old")
        memory.mark_missing("old")
        # A restart preserves facts, not live sighting continuity.
        memory = ObjectMemory(memory.export(now=1))
        record = memory.observe_find(ObjectObservation(
            "new_sighting", None, None, 100, 0, True, 2,
        ), now=2, record=None, claimed=frozenset(), maximum_distance=10)
        self.assertNotEqual(record, "old")
        found = memory.get(record)
        assert found is not None
        self.assertIsNone(found.identity)
        self.assertIsNone(found.kind)
        self.assertFalse(found.assessed)
        old = memory.get("old")
        assert old is not None
        self.assertEqual((old.identity, old.place_status), ("cookie", "missing"))
        memory.observe_find(ObjectObservation(
            "new_sighting", "cookie", "food", 100, 70, False, 3,
        ), now=3, record=record, claimed=frozenset(), maximum_distance=10,
                            preserve_record=True)
        self.assertIsNone(memory.get("old"))
        self.assertEqual(len(memory.snapshot()), 1)

    def test_found_before_or_after_missing_resolves_one_old_place(self):
        for missing_first in (True, False):
            with self.subTest(missing_first=missing_first):
                memory = ObjectMemory()
                seen = ObjectObservation("sighting_1", "apple", "food", 100, 0,
                                         True, 0)
                old = memory.observe_find(seen, now=0, record=None,
                                          claimed=frozenset(), maximum_distance=10)
                memory.mark_assessed(old)
                if missing_first:
                    memory.mark_missing(old)
                new = memory.observe_find(
                    replace(seen, token="sighting_2", x=500, observed_at=1),
                    now=1, record=None, claimed=frozenset(), maximum_distance=10,
                )
                if not missing_first:
                    memory.mark_missing(old)
                self.assertIsNone(memory.get(old))
                found = memory.get(new)
                assert found is not None
                self.assertTrue(found.assessed)
                self.assertEqual(found.possible_sources, ())
                self.assertEqual(len(memory.snapshot()), 1)

    def test_subjective_ids_do_not_recycle_after_consumption_and_restart(self):
        memory = ObjectMemory()
        seen = ObjectObservation("sighting_1", "apple", "food", 100, 0, True, 0)
        old = memory.observe_find(seen, now=0, record=None,
                                  claimed=frozenset(), maximum_distance=10)
        memory.record_consumption(old)
        restored = ObjectMemory(memory.export(now=1))
        new = restored.observe_find(seen, now=1, record=None,
                                    claimed=frozenset(), maximum_distance=10)
        self.assertNotEqual(new, old)

    def test_observed_relocation_preserves_identity_and_completed_inspection(self):
        memory = ObjectMemory()
        seen = ObjectObservation("one", "apple", "food", 100, 0, True, 1)
        memory.update((seen,), now=1)
        memory.mark_assessed("one")
        memory.update((replace(seen, observed_at=2),), now=2)
        self.assertTrue(memory.snapshot()[0].assessed)
        memory.update((), now=3)
        self.assertTrue(memory.snapshot()[0].assessed)
        memory.update((replace(seen, x=200, observed_at=4),), now=4)
        self.assertTrue(memory.snapshot()[0].assessed)
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
        memory.mark_assessed("one")
        self.assertFalse(memory.snapshot()[0].assessed)
        memory.update((), now=601)
        self.assertEqual(len(memory.snapshot()), 1)
        memory.update((), now=601.1)
        self.assertEqual(memory.snapshot(), ())

    def test_conflicting_recognition_invalidates_inspection_and_disposition(self):
        memory = ObjectMemory()
        seen = ObjectObservation("one", "apple", "food", 100, 0, True, 1)
        memory.update((seen,), now=1)
        memory.mark_assessed("one")
        memory.note_placement("one", x=200, height=0, now=2, deferred=True)
        memory.update((replace(seen, identity="onigiri", observed_at=3),), now=3)
        known = memory.snapshot()[0]
        self.assertEqual(known.identity, "onigiri")
        self.assertFalse(known.assessed)
        self.assertIsNone(known.disposition)

    def test_matching_newly_identified_find_recovers_unique_missing_history(self):
        memory = ObjectMemory()
        old = ObjectObservation("old_apple", "apple", "food", 100, 0, True, 0)
        memory.update((old,), now=0)
        memory.mark_assessed(old.token)
        memory.note_placement(old.token, x=100, height=0, now=0, deferred=True)
        memory.mark_missing(old.token)
        memory.update((ObjectObservation(
            "new_find", None, None, 700, 0, True, 2,
        ),), now=2)
        matched = memory.observe_find(ObjectObservation(
            "new_find", "apple", "food", 700, 80, False, 3,
        ), now=3, record="new_find", claimed=frozenset(),
            maximum_distance=10, preserve_record=True)
        self.assertEqual(matched, "new_find")
        self.assertIsNone(memory.get(old.token))
        found = memory.get(matched)
        assert found is not None
        self.assertEqual(found.identity, "apple")
        self.assertTrue(found.assessed)
        self.assertEqual(found.disposition, "deferred")
        self.assertEqual(found.possible_sources, ())

    def test_different_identified_find_never_replaces_missing_apple(self):
        memory = ObjectMemory()
        memory.update((ObjectObservation(
            "old", "apple", "food", 100, 0, True, 0,
        ),), now=0)
        memory.mark_assessed("old")
        memory.mark_missing("old")
        memory.update((ObjectObservation(
            "new", None, None, 700, 0, True, 2,
        ),), now=2)
        memory.observe_find(ObjectObservation(
            "new", "cookie", "food", 700, 80, False, 3,
        ), now=3, record="new", claimed=frozenset(),
            maximum_distance=10, preserve_record=True)
        old = memory.get("old")
        new = memory.get("new")
        assert old is not None and new is not None
        self.assertEqual((old.identity, old.place_status), ("apple", "missing"))
        self.assertEqual((new.identity, new.assessed), ("cookie", False))

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
        memory.mark_assessed("one")
        memory.note_placement("one", x=200, height=0, now=2, deferred=True)
        known = memory.snapshot()[0]
        self.assertEqual((known.x, known.resting, known.disposition),
                         (200, True, "deferred"))
        restored = ObjectMemory(memory.export(now=10000))
        self.assertTrue(restored.snapshot()[0].assessed)
        self.assertEqual(restored.snapshot()[0].disposition, "deferred")
        memory.note_placement("one", x=300, height=0, now=3, deferred=False)
        self.assertEqual(memory.snapshot()[0].disposition, "interrupted")
