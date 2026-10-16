"""Finds reconcile remembered places without omniscient identity or counts."""

import unittest
from dataclasses import replace

from aiko_pet.infrastructure.object_memory_codec import (
    decode_object_memory,
    encode_object_memory,
)
from aiko_pet.pet.mind.object_knowledge import ObjectKnowledge
from aiko_pet.pet.mind.object_memory import ObjectMemory
from aiko_pet.pet.mind.object_perception import ObjectObservation
from aiko_pet.pet.mind.object_stock import match_find, resolved_places, summarize_stock

APPLE = ObjectKnowledge("memory_1", "apple", "food", 100, 0, True, 0, True)


class ObjectStockTests(unittest.TestCase):
    def test_local_unique_reunion_uses_evidence_not_sighting_id(self):
        for handle in ("world_1", "other_999"):
            seen = ObjectObservation(handle, "apple", "food", 105, 0, True, 2)
            match = match_find((APPLE,), seen, claimed=frozenset(),
                               maximum_distance=10)
            self.assertEqual(match.record, APPLE.token)
            separate = match_find((APPLE,), seen, claimed=frozenset((APPLE.token,)),
                                  maximum_distance=10)
            self.assertIsNone(separate.record)
            self.assertEqual(separate.possible_sources, ())

    def test_distant_find_links_sources_without_copying_their_experience(self):
        seen = ObjectObservation("new", "apple", "food", 500, 0, True, 2)
        other = replace(APPLE, token="memory_2", x=200)
        match = match_find((APPLE, other), seen, claimed=frozenset(),
                           maximum_distance=10)
        self.assertIsNone(match.record)
        self.assertEqual(match.possible_sources, ("memory_1", "memory_2"))
        unknown = match_find((APPLE,), replace(seen, identity=None, kind=None),
                             claimed=frozenset(), maximum_distance=10)
        self.assertEqual(unknown.possible_sources, ())

    def test_one_find_cannot_explain_two_missing_portions(self):
        missing = replace(APPLE, place_status="missing")
        second = replace(missing, token="memory_2", x=200)
        found = replace(APPLE, token="memory_3", x=500,
                        possible_sources=(missing.token, second.token))
        summary = summarize_stock((missing, second, found))
        self.assertEqual((summary.available_minimum, summary.available_maximum),
                         (1, 1))
        self.assertEqual((summary.missing_minimum, summary.missing_maximum), (1, 2))

    def test_uncertain_places_are_not_automatically_extra_confirmed_stock(self):
        found = replace(APPLE, token="memory_2", x=500,
                        possible_sources=(APPLE.token,))
        summary = summarize_stock((APPLE, found))
        self.assertEqual((summary.available_minimum, summary.available_maximum),
                         (1, 2))
        distinct = summarize_stock((APPLE, replace(found, possible_sources=())))
        self.assertEqual((distinct.available_minimum, distinct.available_maximum),
                         (2, 2))

    def test_two_finds_can_explain_two_checked_places_without_identity_claims(self):
        first = replace(APPLE, place_status="missing")
        second = replace(first, token="memory_2", x=200)
        found = replace(APPLE, token="memory_3", x=500,
                        possible_sources=(first.token, second.token))
        another = replace(found, token="memory_4", x=600)
        self.assertEqual(resolved_places((first, second, found)), frozenset())
        self.assertEqual(resolved_places((first, second, found, another)),
                         frozenset((first.token, second.token)))

    def test_consumed_ambiguous_find_keeps_one_witness_until_evidence_resolves_it(self):
        memory = ObjectMemory()

        def observe(x, claimed=frozenset()):
            return memory.observe_find(ObjectObservation(
                "sighting", "apple", "food", x, 0, True, 0,
            ), now=0, record=None, claimed=claimed, maximum_distance=10)

        first = observe(100)
        second = observe(200, frozenset((first,)))
        found = observe(500)
        memory.record_consumption(found)
        memory.mark_missing(first)
        memory.mark_missing(second)
        summary = summarize_stock(memory.snapshot())
        self.assertEqual((summary.missing_minimum, summary.missing_maximum), (1, 2))
        saved = encode_object_memory(memory.export(now=1))
        restored = ObjectMemory(decode_object_memory(saved, {"apple": "food"}))
        self.assertEqual(summarize_stock(restored.snapshot()), summary)
        # Seeing the first original portion excludes it from the consumed find.
        restored.observe_find(ObjectObservation(
            "new_handle", "apple", "food", 100, 0, True, 2,
        ), now=2, record=None, claimed=frozenset(), maximum_distance=10)
        remaining, = restored.snapshot()
        self.assertEqual(remaining.token, first)
        self.assertEqual(remaining.place_status, "remembered")
