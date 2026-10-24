"""Cursor tracking must cover the entire virtual desktop, not only 450 px."""

import unittest

from aiko_pet.pet.animation.gaze import gaze_sector


class GlobalGazeTests(unittest.TestCase):
    def test_four_primary_directions_even_tens_of_thousands_of_pixels_away(self):
        x, y = 500, 800
        self.assertEqual(gaze_sector(x, y, x, -20000), 0)
        self.assertEqual(gaze_sector(x, y, 20000, y), 4)
        self.assertEqual(gaze_sector(x, y, x, 20000), 8)
        self.assertEqual(gaze_sector(x, y, -20000, y), 12)

    def test_diagonals_use_original_16_frame_atlas(self):
        self.assertEqual(gaze_sector(500, 500, 1000, 0), 2)
        self.assertEqual(gaze_sector(500, 500, 1000, 1000), 6)
        self.assertEqual(gaze_sector(500, 500, 0, 1000), 10)
        self.assertEqual(gaze_sector(500, 500, 0, 0), 14)

    def test_zero_distance_stays_stable(self):
        self.assertIsNone(gaze_sector(0, 0, 0, 0))
        self.assertIsNone(gaze_sector(0, 0, 5, 5, previous=4))
        self.assertIsNone(gaze_sector(0, 0, 5, 5, previous=4, scale=2))

    def test_hysteresis_stops_unnecessary_flickering(self):
        self.assertEqual(gaze_sector(0, 0, 19, -100, previous=0), 0)
        self.assertEqual(gaze_sector(0, 0, 40, -100, previous=0), 1)

    def test_negative_coordinates_from_left_side_monitor(self):
        self.assertEqual(gaze_sector(20, 300, -2200, 300), 12)
        self.assertEqual(gaze_sector(20, 300, -2200, -1900), 14)


if __name__ == "__main__":
    unittest.main()
