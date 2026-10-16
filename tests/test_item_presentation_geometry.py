"""Offer geometry uses the displayed portion and existing face reference."""

import unittest

from aiko_pet.desktop.geometry import item_face_offset


class ItemPresentationGeometryTests(unittest.TestCase):
    def test_pivot_and_scale_produce_the_same_face_relative_position(self):
        for scale in (1, 2):
            with self.subTest(scale=scale):
                self.assertEqual(item_face_offset(
                    (500 + 10 * scale, 300 + 15 * scale),
                    pivot=(20 * scale, 25 * scale), size=(40 * scale, 50 * scale),
                    eyes=(500, 300), width=100 * scale,
                ), (.1, .15))

    def test_screen_origin_and_eye_to_floor_distance_do_not_change_offer_distance(self):
        self.assertEqual(item_face_offset(
            (1925, 800), pivot=(5, 10), size=(10, 20),
            eyes=(1920, 800), width=100,
        ), (.05, 0))
