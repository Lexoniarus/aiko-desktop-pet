"""A complete deliberate check precedes free action without becoming a search."""

import unittest
from dataclasses import replace

from aiko_pet.application.object_orientation import OrientationProgress
from aiko_pet.pet.mind.object_attention import ObjectAttention
from aiko_pet.pet.mind.object_knowledge import ObjectKnowledge

KNOWN = ObjectKnowledge("known", "cookie", "food", 100, 0, True, 0)
LEFT = ObjectAttention("survey", (-1, 0), origin=(500, 60), width=100)
RIGHT = replace(LEFT, direction=(1, 0))


class ObjectOrientationTests(unittest.TestCase):
    def advance(self, progress, now, attention=LEFT, known=(KNOWN,)):
        return progress.advance(
            now=now, attention=attention, known=known, ground_bounds=(0, 2000),
            duration=.5, maximum_gap=1,
        )

    def test_both_sides_need_their_own_continuous_look_and_completion_is_stable(self):
        progress = self.advance(OrientationProgress(), 0)
        coverage = progress.coverage
        assert coverage is not None
        self.assertEqual(coverage.side, -1)
        progress = self.advance(progress, .5)
        self.assertEqual(progress.side, 1)
        self.assertFalse(progress.complete)
        progress = self.advance(progress, .6, RIGHT)
        self.assertFalse(self.advance(progress, 1, RIGHT).complete)
        progress = self.advance(progress, 1.1, RIGHT)
        self.assertTrue(progress.complete)
        self.assertIsNone(progress.coverage)
        self.assertIs(self.advance(progress, 2), progress)

    def test_unknown_or_ineligible_places_do_not_create_an_empty_waiting_ritual(self):
        for known in ((), (replace(KNOWN, identity=None, kind=None),),
                      (replace(KNOWN, resting=False),),
                      (replace(KNOWN, place_status="missing"),),
                      (replace(KNOWN, x=2001),)):
            with self.subTest(known=known):
                self.assertTrue(self.advance(OrientationProgress(), 0, known=known)
                                .complete)

    def test_wrong_gaze_and_time_gaps_cannot_finish_a_side(self):
        progress = self.advance(OrientationProgress(), 0)
        interrupted = self.advance(progress, .4, RIGHT)
        self.assertIsNone(interrupted.since)
        self.assertFalse(self.advance(interrupted, .6).complete)
        delayed = self.advance(progress, 2)
        self.assertEqual(delayed.since, 2)
        self.assertEqual(delayed.side, -1)

    def test_bound_activity_resets_the_check_without_borrowing_its_elapsed_time(self):
        progress = self.advance(OrientationProgress(), 0)
        progress = self.advance(progress, .5)
        for attention in (replace(LEFT, mode="object"),
                          ObjectAttention("unavailable", None)):
            with self.subTest(attention=attention):
                reset = self.advance(progress, 1, attention)
                self.assertEqual(reset, OrientationProgress())
                reset = self.advance(reset, 2)
                self.assertEqual(reset.side, -1)
                self.assertEqual(reset.since, 2)

    def test_appraisal_does_not_decide_if_a_learned_place_needs_checking(self):
        for known in (KNOWN, replace(KNOWN, assessed=True, disposition="deferred")):
            with self.subTest(known=known):
                progress = self.advance(OrientationProgress(), 0, known=(known,))
                self.assertFalse(progress.complete)
                self.assertEqual(progress.side, -1)

    def test_last_left_loss_does_not_skip_the_remaining_right_look(self):
        progress = self.advance(OrientationProgress(), 0)
        progress = self.advance(progress, .5, known=())
        self.assertEqual(progress.side, 1)
        progress = self.advance(progress, .6, RIGHT, known=())
        self.assertFalse(progress.complete)
        self.assertTrue(self.advance(progress, 1.1, RIGHT, known=()).complete)
