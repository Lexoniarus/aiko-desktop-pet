"""Whole-taskbar learned-place evidence stays separate from unknown discovery."""

import unittest

from aiko_pet.application.object_awareness import ObjectAwareness
from aiko_pet.pet.mind.object_attention import (
    AttentionMode,
    KnownPlaceCoverage,
    ObjectAttention,
)
from aiko_pet.pet.mind.object_perception import ObjectObservation
from aiko_pet.pet.state import PetState
from aiko_pet.world.contracts import (
    ObjectDefinition,
    ObjectFootprint,
    ObjectInteraction,
    WorldSurface,
)
from aiko_pet.world.state import WorldState


class ObjectOrientationAwarenessTests(unittest.TestCase):
    def setUp(self):
        self.world = WorldState(WorldSurface(12000, 1000), (ObjectDefinition(
            "cookie", "cookie", "cookie", frozenset((ObjectInteraction.EAT,)),
        ),))
        self.awareness = ObjectAwareness()
        self.state = PetState(satiety=100)

    def learned(self, x):
        item = self.world.place_resting("cookie", x, ObjectFootprint(8, 8))
        record = self.awareness.memory.observe_find(
            ObjectObservation("earlier", "cookie", "food", x, 0, True, 0),
            now=0, record=None, claimed=frozenset(), maximum_distance=0,
            instance_id=item.instance_id,
        )
        return item, record

    def observe(self, now, side, width=192, *, coverage=True,
                mode: AttentionMode = "survey"):
        self.awareness.update(
            self.world.snapshot(), self.state, now=now, x=6000, height=0, width=width,
            attention=ObjectAttention(mode, (side, 0), origin=(6000, 60), width=width),
            known_coverage=KnownPlaceCoverage(side) if coverage else None,
            blocked=True,
        )

    def test_distant_losses_on_both_sides_do_not_reveal_hidden_new_places(self):
        for width in (192, 384):
            with self.subTest(width=width):
                self.setUp()
                left, left_record = self.learned(100)
                right, right_record = self.learned(11900)
                self.world.move_resting(left.instance_id, 2000, expected_revision=0)
                self.world.move_resting(right.instance_id, 10000, expected_revision=0)
                for now in (0, .3, .6):
                    self.observe(now, -1, width)
                remembered_left = self.awareness.memory.get(left_record)
                remembered_right = self.awareness.memory.get(right_record)
                assert remembered_left is not None and remembered_right is not None
                self.assertEqual(remembered_left.place_status, "missing")
                self.assertEqual(remembered_right.place_status, "remembered")
                for now in (.7, 1, 1.3):
                    self.observe(now, 1, width)
                self.assertEqual({item.token for item in self.awareness.absences},
                                 {left_record, right_record})
                self.assertEqual(len(self.awareness.memory.snapshot()), 2)
                self.assertIsNone(self.awareness.known_instance(left.instance_id))
                self.assertIsNone(self.awareness.known_instance(right.instance_id))

    def test_distant_known_place_recall_does_not_identify_its_neighbour(self):
        item, record = self.learned(11900)
        neighbour = self.world.place_resting("cookie", 11890, ObjectFootprint(8, 8))
        for now in (0, .3, .6):
            self.observe(now, 1)
        known = self.awareness.known_instance(item.instance_id)
        assert known is not None
        self.assertEqual((known.token, known.identity), (record, "cookie"))
        self.assertIsNone(self.awareness.known_instance(neighbour.instance_id))
        self.assertEqual(len(self.awareness.memory.snapshot()), 1)
        self.assertEqual(self.awareness.absences, ())

    def test_distant_unknown_replacement_does_not_hide_loss_or_gain_identity(self):
        item, record = self.learned(100)
        self.world.move_resting(item.instance_id, 2000, expected_revision=0)
        replacement = self.world.place_resting("cookie", 100, ObjectFootprint(8, 8))
        for now in (0, .3, .6):
            self.observe(now, -1)
        self.assertEqual(tuple(item.token for item in self.awareness.absences),
                         (record,))
        self.assertFalse(self.awareness.checking_absence)
        self.assertIsNone(self.awareness.known_instance(replacement.instance_id))
        known = self.awareness.memory.get(record)
        assert known is not None
        self.assertEqual(known.place_status, "missing")
        self.assertEqual((known.identity, known.x), ("cookie", 100))
        self.assertIsNone(self.awareness.known_instance(item.instance_id))
        self.assertEqual(len(self.awareness.memory.snapshot()), 1)

    def test_coverage_requires_actual_survey_and_fresh_uninterrupted_evidence(self):
        item, record = self.learned(100)
        self.world.remove(item.instance_id, expected_revision=0)
        cases: tuple[tuple[float, bool, AttentionMode], ...] = (
            (0, False, "survey"), (.6, False, "survey"),
            (.9, True, "object"), (1.2, True, "unavailable"),
        )
        for now, coverage, mode in cases:
            self.observe(now, -1, coverage=coverage, mode=mode)
        self.assertEqual(self.awareness.absences, ())
        self.observe(1.5, -1)
        self.observe(1.8, -1)
        self.assertEqual(self.awareness.absences, ())
        self.observe(2.1, -1)
        self.assertEqual(tuple(item.token for item in self.awareness.absences),
                         (record,))
