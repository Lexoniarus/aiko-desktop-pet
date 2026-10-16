"""Ground reach stays local, with a bounded exception at either track edge."""

import unittest

from aiko_pet.desktop.geometry import TaskbarTrack
from aiko_pet.world.contracts import ObjectFootprint, WorldSurface


class GroundApproachTests(unittest.TestCase):
    def test_reachable_interval_intersects_sprite_reach_and_item_extent(self):
        track = TaskbarTrack(48, 1600, 900)
        for scale in (1, 2):
            width, reach = 192 * scale, 48 * scale
            surface = WorldSurface(track.right - track.left, 900,
                                   track.ground_inset(width, reach))
            footprint = ObjectFootprint(10 * scale, 10 * scale)
            for raw in (0, surface.width):
                with self.subTest(scale=scale, side=raw):
                    anchor = surface.ground_x(raw, footprint)
                    approach = track.ground_approach(track.left + anchor, width, reach)
                    assert approach is not None
                    self.assertFalse(approach.edge_grip)
                    self.assertTrue(track.can_grasp_ground(
                        track.left + anchor, approach.standing_x, width, reach,
                    ))

    def test_edge_grip_requires_closest_standing_pose_on_both_sides_and_scales(self):
        track = TaskbarTrack(48, 1600, 900)
        for scale in (1, 2):
            width, reach = 192 * scale, 48 * scale
            for object_x, boundary, direction in (
                (track.left + 10 * scale, track.left, 1),
                (track.right - 10 * scale, track.right - width, -1),
            ):
                with self.subTest(scale=scale, object_x=object_x):
                    approach = track.ground_approach(object_x, width, reach)
                    assert approach is not None
                    self.assertEqual(approach.standing_x, boundary)
                    self.assertTrue(approach.edge_grip)
                    self.assertTrue(track.can_grasp_ground(
                        object_x, boundary, width, reach,
                    ))
                    self.assertFalse(track.can_grasp_ground(
                        object_x, boundary + direction * 3, width, reach,
                    ))
                    self.assertFalse(track.can_grasp_ground(
                        object_x, boundary + direction * 200, width, reach,
                    ))

    def test_ordinary_ground_reach_is_not_extended(self):
        track = TaskbarTrack(48, 1600, 900)
        for scale in (1, 2):
            width, reach = 192 * scale, 48 * scale
            object_x = 800
            approach = track.ground_approach(object_x, width, reach)
            assert approach is not None
            self.assertFalse(approach.edge_grip)
            self.assertTrue(track.can_grasp_ground(
                object_x, approach.standing_x + reach, width, reach,
            ))
            self.assertFalse(track.can_grasp_ground(
                object_x, approach.standing_x + reach + 1, width, reach,
            ))

    def test_outside_ground_and_off_track_pet_cannot_use_edge_grip(self):
        track = TaskbarTrack(48, 1600, 900)
        for scale in (1, 2):
            width, reach = 192 * scale, 48 * scale
            for object_x in (track.left - 1, track.right + 1):
                self.assertIsNone(track.ground_approach(object_x, width, reach))
                self.assertFalse(track.can_grasp_ground(
                    object_x, track.left, width, reach,
                ))
            self.assertFalse(track.can_grasp_ground(
                track.left + 10, track.left - 1, width, reach,
            ))
            self.assertFalse(track.can_grasp_ground(
                track.right - 10, track.right - width + 1, width, reach,
            ))

    def test_track_too_narrow_for_full_window_has_no_ground_approach(self):
        track = TaskbarTrack(48, 200, 900)
        self.assertIsNone(track.ground_approach(100, 192, 48))
        self.assertFalse(track.can_grasp_ground(100, 48, 192, 48))
