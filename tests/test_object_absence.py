"""Absence requires a local, uninterrupted look, not a missing execution ID."""

import unittest
from dataclasses import replace

from aiko_pet.pet.mind.object_absence import ObjectAbsencePerception
from aiko_pet.pet.mind.object_knowledge import ObjectKnowledge
from aiko_pet.pet.mind.object_perception import ObjectCandidate

PLACE = ObjectKnowledge("noticed", None, None, 100, 0, True, 0)
OCCUPANT = ObjectCandidate("unnoticed", "cookie", "food", 100, 0, True)


class ObjectAbsenceTests(unittest.TestCase):
    def setUp(self):
        self.sensor = ObjectAbsencePerception()

    def sample(self, now, occupants=(), known=(PLACE,), **kwargs):
        return self.sensor.observe(known, occupants, now=now, x=100, height=0,
                                   width=100, ground_bounds=(0, 1500), **kwargs)

    def test_unknown_presence_can_be_confirmed_missing_once(self):
        self.assertEqual(self.sample(0, attentive=True), ())
        self.assertTrue(self.sensor.checking)
        self.assertEqual(self.sample(.3, attentive=True), ())
        self.assertEqual(self.sample(.5, attentive=True), (PLACE.token,))
        self.assertFalse(self.sensor.checking)
        self.assertEqual(self.sample(.7, attentive=True), ())

    def test_pending_occupants_reset_local_evidence(self):
        self.sample(0, attentive=True)
        self.sample(.4, (OCCUPANT,), attentive=True)
        self.assertEqual(self.sample(.6, attentive=True), ())
        self.assertEqual(self.sample(.9, attentive=True), ())
        self.assertEqual(self.sample(1.1, attentive=True), (PLACE.token,))

    def test_distraction_gap_or_changed_focus_cannot_accumulate_absence(self):
        for interruption in ("attention", "gap", "focus"):
            with self.subTest(interruption=interruption):
                self.sensor = ObjectAbsencePerception()
                self.sample(0, attentive=True)
                self.sample(.4, attentive=interruption != "attention",
                            focused="other" if interruption == "focus" else None)
                now = 5 if interruption == "gap" else .6
                self.assertEqual(self.sample(now, attentive=True), ())
                self.assertEqual(self.sample(now + .5, attentive=True), (PLACE.token,))

    def test_hidden_boundary_missing_and_own_custody_places_supply_no_loss(self):
        for item in (replace(PLACE, x=1400), replace(PLACE, x=1501),
                     replace(PLACE, resting=False),
                     replace(PLACE, place_status="missing")):
            with self.subTest(item=item):
                self.sensor = ObjectAbsencePerception()
                for now in (0, .5, 1):
                    self.assertEqual(self.sample(now, known=(item,),
                                                 attentive=True), ())

    def test_missing_place_has_the_same_notice_distance_as_a_new_item(self):
        # Notice and loss both use exactly notice_widths, with no extra
        # memory-place radius removed from the detection distance.
        boundary = replace(PLACE, x=700)
        self.assertEqual(self.sample(0, known=(boundary,), attentive=True), ())
        self.assertEqual(self.sample(.5, known=(boundary,), attentive=True),
                         (boundary.token,))
        self.sensor = ObjectAbsencePerception()
        outside = replace(PLACE, x=701)
        for stamp in (0, .5, 1):
            self.assertEqual(self.sample(stamp, known=(outside,),
                                         attentive=True), ())
        self.assertFalse(self.sensor.checking)

    def test_visible_ground_edge_is_not_excluded_from_missing_perception(self):
        at_edge = replace(PLACE, x=0)
        self.assertEqual(self.sample(0, known=(at_edge,), attentive=True), ())
        self.assertEqual(self.sample(.5, known=(at_edge,), attentive=True),
                         (at_edge.token,))

    def test_empty_place_evidence_is_not_borrowed_from_neighbour_or_old_location(self):
        self.sample(0, attentive=True)
        self.sample(.5, attentive=True)
        self.assertFalse(self.sensor.checking)
        moved = replace(PLACE, x=150)
        self.assertEqual(self.sample(.6, known=(moved,), attentive=True), ())
        self.assertTrue(self.sensor.checking)
