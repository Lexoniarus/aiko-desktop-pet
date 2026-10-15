"""Forward pickup and reverse put-down share approved source poses."""

import unittest

from aiko_pet.infrastructure.character_assets import load_character_catalog


class PickupPlaybackTests(unittest.TestCase):
    def test_forward_grasp_and_reverse_release_metadata(self):
        clips = load_character_catalog().clips
        pickup, down = clips["pick_up"], clips["put_down"]
        self.assertIs(pickup.frames, down.frames)
        self.assertEqual(pickup.playback_order, tuple(range(8)))
        self.assertEqual(down.playback_order, tuple(reversed(range(8))))
        self.assertEqual(pickup.frames[3].events, ("attach_object",))
        self.assertEqual(pickup.anchor, (96, 196))
        self.assertTrue(pickup.hold_last)
        self.assertAlmostEqual(pickup.duration_seconds, 1.41)
        self.assertIsNotNone(pickup.frames[3].hand_foreground)
