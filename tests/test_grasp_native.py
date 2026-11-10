"""Approved grasp sprites and palm placement through the actual native clock."""

import unittest

from tests import test_hd_eating_playback as fixture
from tools.tk_test_time import ControlledTkTime


class GraspNativeTests(unittest.TestCase):
    def setUp(self):
        native = fixture.HdEatingPlaybackTests("runTest")
        self.addCleanup(native.doCleanups)
        native.setUp()
        self.state, self.anim = native.state, native.anim
        self.assets, self.canvas = native.assets, native.canvas
        self.settings = native.settings

    def test_new_grasp_finishes_once_and_holds_the_object_pose(self):
        before = self.state.capture_checkpoint()
        events = []
        self.anim.on_playback = events.append
        with ControlledTkTime() as clock:
            self.anim.set_food_overlay("onigiri")
            self.anim.begin_action("pick_up", clock.monotonic())
            clock.advance(self.assets.clip_for("pick_up", 2).duration_seconds + .02)
        self.assertEqual(sum("attach_object" in e.events for e in events), 1)
        self.assertEqual(sum(e.finished for e in events), 1)
        self.assertEqual(self.anim._display_clip, "pick_up")
        self.assertEqual(self.canvas.itemcget(self.anim.food_overlay.item, "state"),
                         "normal")
        self.assertEqual(self.state.capture_checkpoint(), before)

    def test_both_sizes_use_hd_and_shared_palm_for_food_and_book(self):
        for scale in (1, 2):
            self.settings.scale = scale
            self.anim.reload_sprites()
            for item in ("onigiri", "horoscope_book"):
                self.anim.set_food_overlay(item)
                self.anim.show_frame("hold_item", 0, fixed=0)
                im = self.anim.sprites["hold_item"][0]
                self.assertEqual(im.width(), 192 * scale)
                overlay = self.anim.food_overlay
                x, y = self.canvas.coords(overlay.item)
                image = (overlay._book_images[(item, "carry_closed", scale)]
                         if item == "horoscope_book"
                         else overlay._images[(item, scale)])
                self.assertAlmostEqual(x + image.width() / 2, 96 * scale, delta=.5)
                self.assertLessEqual(y + image.height(), 194 * scale + .5)
                self.assertLessEqual(y + image.height() / 2, 147 * scale + .5)

    def test_hint_is_independent_and_cannot_survive_cancel(self):
        with ControlledTkTime() as clock:
            self.anim.set_food_overlay("onigiri")
            self.anim.begin_action("inspect_hold", clock.monotonic())
            action = self.anim.action_id
            self.anim.inspection_hint()
            self.assertEqual(self.anim.action_id, action)
            self.assertEqual(self.canvas.itemcget(self.anim._hint_item, "state"),
                             "normal")
            self.anim.cancel_action(clock.monotonic())
            clock.advance(1)
            self.assertEqual(self.canvas.itemcget(self.anim._hint_item, "state"),
                             "hidden")
