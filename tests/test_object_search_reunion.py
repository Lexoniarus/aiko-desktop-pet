"""Search-only subjective reunion preserves physical facts and save invariants."""

from __future__ import annotations

import unittest
from dataclasses import replace

from aiko_pet.application.object_interaction_state import SearchTask
from aiko_pet.infrastructure.object_memory_codec import (
    decode_object_memory,
    encode_object_memory,
)
from aiko_pet.pet.mind.object_knowledge import ObjectKnowledge
from aiko_pet.pet.mind.object_memory import ObjectMemory
from aiko_pet.pet.mind.object_perception import ObjectObservation

OLD = ObjectKnowledge(
    "memory_1", "onigiri", "food", 100, 0, True, 0,
    True, "deferred", "missing", instance_id="object_1",
)
FOUND = ObjectKnowledge(
    "memory_3", "onigiri", "food", 600, 80, False, 10,
    instance_id="object_3",
)


class ObjectSearchReunionTests(unittest.TestCase):
    def test_matching_find_resolves_one_subject_and_cannot_be_reused(self) -> None:
        second = replace(OLD, token="memory_2", instance_id="object_2")
        search = SearchTask(OLD)
        search.add(second)
        for candidate in (
            replace(FOUND, identity=None, kind=None),
            replace(FOUND, identity="apple"),
            replace(FOUND, kind="drink"),
            replace(FOUND, place_status="superseded"),
        ):
            self.assertIsNone(search.resolve(candidate))
        self.assertEqual(search.resolve(FOUND), OLD)
        self.assertEqual(search.next_subject, second)
        self.assertIsNone(search.resolve(FOUND))
        self.assertIsNone(search.resolve(replace(FOUND, token="memory_4")))
        self.assertEqual(search.resolve(replace(
            FOUND, token="memory_5", instance_id="object_5",
        )), second)
        self.assertIsNone(search.next_subject)

    def test_reunion_transfers_history_without_replacing_found_facts(self) -> None:
        memory = ObjectMemory()
        another = replace(OLD, token="memory_2", instance_id="object_2")
        memory.restore_snapshot((OLD, another, replace(
            FOUND, possible_sources=(OLD.token, another.token),
        )))
        found = memory.reunite_search(OLD, FOUND.token)
        self.assertEqual(found, replace(FOUND, assessed=True, disposition="deferred"))
        self.assertIsNone(memory.get(OLD.token))
        self.assertEqual(memory.get(another.token), another)
        self.assertIsNone(memory.learned_instance("object_1"))
        self.assertEqual(memory.learned_instance("object_3"), found)
        saved = memory.export(now=20)
        restored = ObjectMemory(decode_object_memory(
            encode_object_memory(saved, world_next_id=4),
            {"onigiri": "food"}, allocated_until=4,
        ), now=100)
        self.assertEqual(restored.export(now=100), saved)

    def test_original_portion_later_requires_fresh_identification(self) -> None:
        memory = ObjectMemory()
        memory.restore_snapshot((OLD, FOUND))
        memory.reunite_search(OLD, FOUND.token)
        token = memory.observe_find(
            ObjectObservation("sighting", None, None, 100, 0, True, 20),
            now=20, record=None, claimed=frozenset(), maximum_distance=25,
            instance_id="object_1",
        )
        self.assertNotIn(token, (OLD.token, FOUND.token))
        unknown = memory.get(token)
        assert unknown is not None
        self.assertFalse(unknown.recognized)
        token = memory.observe_find(
            ObjectObservation("sighting", "onigiri", "food", 100, 80, False, 21),
            now=21, record=token, claimed=frozenset(), maximum_distance=25,
            preserve_record=True, instance_id="object_1",
        )
        known = memory.get(token)
        assert known is not None
        self.assertFalse(known.assessed)
        self.assertIsNone(known.disposition)
        self.assertEqual(known.instance_id, "object_1")
        self.assertEqual(len(memory.snapshot()), 2)

    def test_rebuilt_search_does_not_reuse_already_known_or_reunited_stock(self):
        memory = ObjectMemory()
        second = replace(OLD, token="memory_2", instance_id="object_2")
        memory.restore_snapshot((OLD, second, FOUND))
        memory.reunite_search(OLD, FOUND.token)
        restored = ObjectMemory(memory.export(now=20))
        task = SearchTask(second, known=restored.snapshot())
        self.assertIsNone(task.resolve(FOUND))
        self.assertEqual(task.next_subject, second)
        fresh = replace(FOUND, token="memory_4", instance_id="object_4")
        self.assertEqual(task.resolve(fresh), second)

    def test_a_new_confirmed_loss_can_reopen_a_previously_known_portion(self):
        task = SearchTask(OLD, known=(FOUND,))
        self.assertIsNone(task.resolve(FOUND))
        self.assertTrue(task.add(replace(FOUND, place_status="missing")))
        self.assertEqual(task.resolve(FOUND), OLD)
        self.assertIsNone(task.resolve(FOUND))

    def test_ordinary_identification_does_not_inherit_same_kind_missing_history(self):
        memory = ObjectMemory()
        memory.restore_snapshot((OLD,))
        token = memory.observe_find(
            ObjectObservation("new", "onigiri", "food", 600, 80, False, 10),
            now=10, record=None, claimed=frozenset(), maximum_distance=25,
            instance_id="object_3",
        )
        found = memory.get(token)
        assert found is not None
        self.assertFalse(found.assessed)
        self.assertIsNone(found.disposition)
        self.assertEqual(memory.get(OLD.token), OLD)

    def test_invalid_reunion_keeps_memory_unchanged(self) -> None:
        memory = ObjectMemory()
        memory.restore_snapshot((OLD, replace(FOUND, identity="apple")))
        before = memory.snapshot()
        with self.assertRaises(ValueError):
            memory.reunite_search(OLD, FOUND.token)
        self.assertEqual(memory.snapshot(), before)


if __name__ == "__main__":
    unittest.main()
