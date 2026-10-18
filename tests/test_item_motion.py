"""Pure collision math, without frame timers or native GUI setup."""

import math
import unittest

from aiko_pet.world.motion import (
    ItemMotion,
    MotionParameters,
    advance_motion,
    contact_time,
    flight,
)


class FlightTests(unittest.TestCase):
    def test_contact_apex_and_partitioned_elapsed_time(self):
        self.assertEqual(contact_time(0, -20, 900), 0)
        self.assertAlmostEqual(contact_time(0, 90, 900), .2)
        apex, velocity = flight(0, 90, .1, 900)
        self.assertAlmostEqual(apex, 4.5)
        self.assertEqual(velocity, 0)
        h, v = flight(600, 0, .2, 900)
        h, v = flight(h, v, .3, 900)
        self.assertEqual((h, v), flight(600, 0, .5, 900))
        self.assertAlmostEqual(flight(600, 0, contact_time(600, 0, 900), 900)[0], 0)

    def test_invalid_inputs_and_crossed_contact_are_rejected(self):
        for values in ((-1, 0, 900), (1, math.inf, 900), (1, 0, 0)):
            with self.subTest(values=values), self.assertRaises(ValueError):
                contact_time(*values)
        with self.assertRaises(ValueError):
            flight(1, 0, 1, 900)


class ReboundTests(unittest.TestCase):
    parameters = MotionParameters(900, .42, .65, .35, 25, 100, 12, 8)

    def test_shrunken_ceiling_dissipates_upward_energy_without_frame_dependence(self):
        whole = advance_motion(400, 90, ItemMotion(vy=300), .3,
                               (96, 704), self.parameters, ceiling=100)
        split = advance_motion(400, 90, ItemMotion(vy=300), .1,
                               (96, 704), self.parameters, ceiling=100)
        assert split.motion is not None
        split = advance_motion(split.x, split.height, split.motion, .2,
                               (96, 704), self.parameters, ceiling=100)
        self.assertAlmostEqual(whole.height, split.height)
        assert whole.motion is not None and split.motion is not None
        self.assertAlmostEqual(whole.motion.vy, split.motion.vy)
        self.assertLessEqual(whole.height, 100)

    def test_both_edges_heights_and_partitioned_time_end_safely(self):
        for x in (8, 400, 792):
            for height in (0, 1, 600):
                with self.subTest(x=x, height=height):
                    result = advance_motion(x, height, ItemMotion(), 20,
                                            (96, 704), self.parameters)
                    self.assertIsNone(result.motion)
                    self.assertTrue(96 <= result.x <= 704)
                    h, position, motion = height, x, ItemMotion()
                    settled = False
                    for _ in range(400):
                        step = advance_motion(position, h, motion, .05,
                                              (96, 704), self.parameters)
                        position, h = step.x, step.height
                        if step.motion is None:
                            settled = True
                            break
                        motion = step.motion
                    self.assertTrue(settled)
                    self.assertAlmostEqual(position, result.x)

    def test_drop_height_controls_impulse_and_number_of_hops(self):
        counts = []
        for height in (2, 600):
            t = contact_time(height, 0, self.parameters.gravity)
            first = advance_motion(8, height, ItemMotion(), t + 1e-8,
                                   (96, 704), self.parameters)
            motion = first.motion
            assert motion is not None
            counts.append(motion.vy)
            x, h = first.x, first.height
            previous = motion.vy
            contacts = 1
            while not motion.settling:
                step = advance_motion(x, h, motion,
                                      contact_time(h, motion.vy, 900) + 1e-8,
                                      (96, 704), self.parameters)
                contacts += 1
                if step.motion is None:
                    break
                self.assertLess(step.motion.vy, previous)
                x, h, motion = step.x, step.height, step.motion
                previous = motion.vy
            counts.append(contacts)
        self.assertGreater(counts[2], counts[0])
        self.assertGreater(counts[3], counts[1])

    def test_low_energy_outside_finishes_continuously_without_a_fake_hop(self):
        first = advance_motion(8, 0, ItemMotion(), .1, (96, 704), self.parameters)
        self.assertEqual(first.height, 0)
        self.assertGreater(first.x, 8)
        self.assertLess(first.x, 96)
        assert first.motion is not None
        self.assertTrue(first.motion.settling)
        last = advance_motion(first.x, 0, first.motion, 2, (96, 704), self.parameters)
        self.assertEqual(last.x, 96)
        self.assertIsNone(last.motion)
