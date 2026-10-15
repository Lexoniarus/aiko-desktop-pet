"""Real Tk application joins food perception, movement and pickup effects."""

import tempfile
import time
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import patch

from aiko_pet.application.object_feedback import FeedbackReceipt
from aiko_pet.gui import DesktopPet
from aiko_pet.infrastructure.persistence import StateStore
from aiko_pet.world.contracts import ObjectFootprint, ObjectState


class WorldGuiTests(unittest.TestCase):
    def test_stale_offer_readiness_cannot_authorize_a_later_offer_state(self):
        world = self.app._world
        callbacks = []
        world._present_feedback = lambda cue, _reaction, done: callbacks.append(
            (cue, done),
        )
        with patch.object(self.app.root, "winfo_pointerx", return_value=(
            (self.app.settings.x or 0) + 96
        )), patch.object(self.app.root, "winfo_pointery",
                         return_value=world._track().ground_y - 80):
            self.app.state.energy = 40
            world.begin_carry("energy_drink")
            for stamp in (0, .3, .7):
                world.now = stamp
                world.update(time.monotonic())
            old, stale = callbacks[-1]
            self.app.state.energy = 100
            world.update(time.monotonic())
            self.app.state.energy = 40
            world.update(time.monotonic())
            current, done = callbacks[-1]
            stale(FeedbackReceipt(old.key, True))
            self.assertFalse(world._offer_ready)
            done(FeedbackReceipt(current.key, True))
            self.assertTrue(world._offer_ready)

    def setUp(self):
        try:
            root = tk.Tk()
            root.destroy()
        except tk.TclError as error:
            self.skipTest(str(error))
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.app = DesktopPet(store=StateStore(Path(folder.name) / "state.json"))
        self.addCleanup(self.app.quit)
        self.app._runtime.stop()
        world = self.app._world
        assert world._timer is not None
        self.app.root.after_cancel(world._timer)
        world._timer = None
        self.app.settings.auto_routine = False
        self.app.settings.observe_computer = False
        self.app.settings.auto_walk = False
        self.app.state.sleeping = False
        self.app.state.satiety = 50
        self.app._action_playback.cancel_at(time.monotonic())
        world._controls_active = lambda: False

    def recognize(self):
        for now in (0, .3, .7):
            self.app._world.now = now
            self.app._world.update(time.monotonic())
        self.complete_feedback()
        self.complete_feedback()

    def complete_feedback(self):
        # Component assertions skip cue dwell; runtime-flow tests use real timers.
        player = self.app._reaction_player
        if player.pending_timer is not None:
            self.app.root.after_cancel(player.pending_timer)
            player._complete(player.generation)
        self.app._world.update(time.monotonic())

    def finish_inspection(self):
        self.app._world.now += 1.1
        for _ in range(4):
            if self.app._world.interaction.phase not in (
                "inspect", "recognize", "decide",
            ):
                break
            self.complete_feedback()

    def finish_pickup(self):
        self.finish_clip("pick_up")

    def finish_clip(self, name):
        self.complete_feedback()
        animated = self.app._animated
        clip = animated.assets.clips[name]
        for _ in range(32):
            if self.app._world.interaction.phase != name:
                break
            index = animated.frame_clock.frame_index
            stamp = animated.frame_clock.frame_started_at + clip.timings[index] / 1000
            animated.show_frame(name, stamp + .001)
            self.app.root.update_idletasks()

    def test_ground_pickup_commits_nutrition_only_after_inspection_and_decision(self):
        world = self.app._world
        item = world.world.place_resting(
            "apple", world._body_x(), ObjectFootprint(8, 8),
        )
        self.recognize()
        self.assertEqual(world.interaction.phase, "pick_up")
        self.assertEqual(self.app.state.satiety, 50)
        self.finish_pickup()
        self.assertEqual(self.app.state.satiety, 50)
        self.assertEqual(world.world.get(item.instance_id).state, ObjectState.PET_HELD)
        self.finish_inspection()
        self.assertEqual(world.world.get(item.instance_id).state, ObjectState.CONSUMED)
        self.assertGreater(self.app.state.satiety, 60)
        self.assertEqual(self.app.state.friendship, 15)

    def test_recognized_release_hands_over_drink_and_full_release_falls(self):
        app, world = self.app, self.app._world
        app.state.energy = 40
        x = (app.settings.x or 0) + 96
        y = world._track().ground_y - 80
        with patch.object(app.root, "winfo_pointerx", return_value=x), patch.object(
            app.root, "winfo_pointery", return_value=y,
        ):
            world.begin_carry("energy_drink")
            self.recognize()
            token = world.carry_id
            assert token is not None
            world.release()
            self.assertEqual(world.world.get(token).state, ObjectState.PET_HELD)
            self.finish_inspection()
            self.assertEqual(world.world.get(token).state, ObjectState.CONSUMED)
            self.assertGreater(app.state.energy, 49)
            app._action_playback.cancel_at(time.monotonic())
            world.interrupt(lambda: None)
            app.state.energy = 100
            world.begin_carry("energy_drink")
            for now in (1, 1.3, 1.7):
                world.now = now
                world.update(time.monotonic())
            token = world.carry_id
            assert token is not None
            world.release()
            self.assertEqual(world.world.get(token).state, ObjectState.FALLING)

    def test_restart_restores_portion_on_ground_without_consuming_it(self):
        app = self.app
        item = app._world.world.place_resting("apple", app._world._body_x(),
                                             ObjectFootprint(8, 8))
        store = app.store
        app.quit()
        restored = DesktopPet(store=store)
        self.addCleanup(restored.quit)
        snapshot = restored._world.world.snapshot()
        self.assertEqual(len(snapshot.objects), 1)
        self.assertEqual(snapshot.objects[0].instance_id, item.instance_id)
        self.assertEqual(snapshot.objects[0].state, ObjectState.RESTING)
        self.assertAlmostEqual(restored.state.satiety, 50, places=1)

    def test_lost_input_capture_cancels_without_falling_or_consuming(self):
        world = self.app._world
        world.begin_carry("apple")
        token = world.carry_id
        assert token is not None
        self.assertEqual(self.app.root.grab_current(), self.app.root)
        self.app.root.grab_release()
        world._frame()
        self.assertIsNone(world.carry_id)
        self.assertEqual(world.world.get(token).state, ObjectState.REMOVED)
        self.assertIsNone(self.app.state.food.last_food_id)

    def test_actual_driver_reaches_food_with_random_walk_disabled(self):
        world = self.app._world
        start = self.app.settings.x or 0
        world.world.place_resting("apple", world._body_x() + 80,
                                   ObjectFootprint(8, 8))
        self.recognize()
        for index in range(4):
            self.app._walk.step(time.monotonic() + index, 1,
                                game_mode=False, attention_active=False)
            world.now += 1
            world.update(time.monotonic())
            if world.interaction.phase == "pick_up":
                break
        self.assertGreater(self.app.settings.x or 0, start)
        self.assertFalse(self.app.settings.auto_walk)
        self.assertEqual(world.interaction.phase, "pick_up")

    def test_sleep_request_after_grasp_puts_down_before_sleep_without_nutrition(self):
        world, animated = self.app._world, self.app._animated
        item = world.world.place_resting(
            "apple", world._body_x(), ObjectFootprint(8, 8),
        )
        self.recognize()
        for _ in range(3):
            index = animated.frame_clock.frame_index
            stamp = animated.frame_clock.frame_started_at
            stamp += animated.assets.clips["pick_up"].timings[index] / 1000 + .001
            animated.show_frame("pick_up", stamp)
            self.app.root.update_idletasks()
        self.assertEqual(world.world.get(item.instance_id).state, ObjectState.PET_HELD)
        self.app.interact("sleep")
        self.assertFalse(self.app.state.sleeping)
        self.finish_clip("pick_up")
        self.assertEqual(world.interaction.phase, "put_down")
        self.finish_clip("put_down")
        self.assertTrue(self.app.state.sleeping)
        self.assertEqual(world.world.get(item.instance_id).state, ObjectState.RESTING)
        self.assertIsNone(self.app.state.food.last_food_id)
