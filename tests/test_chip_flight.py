"""The chip follows one parabola and clears the full registered playfield."""

import unittest

from aiko_pet.ui.view_models.chip_flight import ChipTarget, flight_point


class ChipFlightTests(unittest.TestCase):
    def test_arc_endpoints_and_clearance_from_both_sides(self):
        for start in ((10., 700.), (900., 700.)):
            for x in (310., 430., 550.):
                target = ChipTarget(x, 160, 290, 570, 180, 32)
                self.assertEqual(flight_point(0, start, target), start)
                self.assertEqual(flight_point(1, start, target), (x, 160))
                for i in range(1, 100):
                    px, py = flight_point(i / 100, start, target)
                    if px + 16 >= target.left and px - 16 <= target.right:
                        self.assertLessEqual(py + 16, target.top + 1e-6)

    def test_horizontal_velocity_is_constant_and_vertical_motion_quadratic(self):
        target = ChipTarget(600, 180, 300, 650, 200)
        points = [flight_point(i / 10, (20, 700), target) for i in range(11)]
        steps = [points[i + 1][0] - points[i][0] for i in range(10)]
        self.assertTrue(all(abs(step - steps[0]) < 1e-6 for step in steps))
        self.assertLess(points[1][1], points[0][1])
        self.assertGreater(points[-1][1], points[-2][1])
