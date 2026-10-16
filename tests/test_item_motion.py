"""Pure collision math, without frame timers or native GUI setup."""

import math
import unittest

from aiko_pet.world.motion import contact_time, flight


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
