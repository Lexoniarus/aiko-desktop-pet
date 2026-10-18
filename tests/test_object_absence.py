"""Absence requires a local, uninterrupted look, not a missing execution ID."""

import unittest
from dataclasses import replace

from aiko_pet.pet.mind.object_absence import ObjectAbsencePerception
from aiko_pet.pet.mind.object_knowledge import ObjectKnowledge
from aiko_pet.pet.mind.object_perception import ObjectCandidate
from tools.pet_test_support import object_test_attention

PLACE = ObjectKnowledge("noticed", None, None, 100, 0, True, 0)
OCCUPANT = ObjectCandidate("unnoticed", "cookie", "food", 100, 0, True)


class ObjectAbsenceTests(unittest.TestCase):
    def setUp(self):
        self.sensor = ObjectAbsencePerception()

    def sample(self, now, occupants=(), known=(PLACE,), **kwargs):
        attention = kwargs.pop("attention", object_test_attention(
            100, width=100, attentive=kwargs.pop("attentive", True),
        ))
        return self.sensor.observe(known, occupants, now=now, attention=attention,
                                   ground_bounds=(0, 1500), **kwargs)

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

    def test_identified_other_portion_cannot_hide_a_missing_neighbour(self):
        missing = replace(PLACE, identity="apple", kind="food", instance_id="old")
        other = replace(missing, token="other", x=110, instance_id="different")
        occupant = replace(OCCUPANT, x=110)
        self.sample(0, (occupant,), known=(missing,), attentive=True)
        self.assertFalse(self.sensor.checking)
        identified = {occupant.token: other}
        self.sample(.6, (occupant,), known=(missing,), attentive=True,
                    identified=identified)
        self.assertEqual(self.sample(1.2, (occupant,), known=(missing,), attentive=True,
                                     identified=identified), (missing.token,))

    def test_distraction_or_time_gap_cannot_accumulate_absence(self):
        for interruption in ("attention", "gap"):
            with self.subTest(interruption=interruption):
                self.sensor = ObjectAbsencePerception()
                self.sample(0, attentive=True)
                self.sample(.4, attentive=interruption != "attention")
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

    def test_unidentified_place_stays_within_local_notice_range(self):
        # An unidentified sighting has no learned place for distant orientation.
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
