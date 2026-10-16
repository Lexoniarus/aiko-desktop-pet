"""Real Tk application joins food perception, movement and pickup effects."""

import tempfile
import time
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import patch

from aiko_pet.application.object_feedback import FeedbackReceipt
from aiko_pet.desktop.geometry import FOOT_BASELINE
from aiko_pet.gui import DesktopPet
from aiko_pet.infrastructure.persistence import StateStore
from aiko_pet.pet.balance import BALANCE
from aiko_pet.pet.mind.object_perception import ObjectObservation
from aiko_pet.world.contracts import ObjectFootprint, ObjectState, WorldPosition


class WorldGuiTests(unittest.TestCase):
    def test_restart_during_a_held_wish_restores_facts_without_live_cursor_state(self):
        app, world = self.app, self.app._world
        with (
            patch.object(app.root, "winfo_pointerx",
                         return_value=int(world._body_x()) + world._track().left),
            patch.object(app.root, "winfo_pointery",
                         return_value=world._track().ground_y - 80),
        ):
            world.begin_carry("cookie")
            self.recognize()
            token = world.cursor.instance_id
            assert token is not None
            known = world.awareness.known_instance(token)
            assert known is not None
            self.assertIsNotNone(world.awareness.intentions.goal)
            self.restart()
        world = self.app._world
        restored = world.awareness.memory.get(known.token)
        assert restored is not None
        self.assertEqual((restored.identity, restored.assessed), ("cookie", True))
        self.assertEqual(world.awareness.observations, ())
        self.assertIsNone(world.awareness.intentions.goal)
        self.assertIsNone(world.awareness.instance_for_record(known.token))
        self.assertFalse(world.cursor.carrying)
        self.assertFalse(world.interaction.active)
        self.assertEqual(world.world.get(token).state, ObjectState.RESTING)
        self.assertIsNone(self.app.state.food.last_food_id)

    def test_restart_keeps_known_unassessed_cookie_without_identifying_again(self):
        world = self.app._world
        item = world.world.place_resting("cookie", world._body_x(),
                                         ObjectFootprint(8, 8))
        world._controls_active = lambda: True
        self.recognize()
        known = world.awareness.known_instance(item.instance_id)
        assert known is not None
        self.assertFalse(known.assessed)
        self.restart()
        world = self.app._world
        restored = world.awareness.memory.get(known.token)
        assert restored is not None
        self.assertEqual((restored.identity, restored.assessed), ("cookie", False))
        self.assertEqual(world.awareness.observations, ())
        self.assertIsNone(world.awareness.intentions.goal)
        cues = []
        present = world._present_feedback

        def capture(cue, reaction, done):
            cues.append(cue.event)
            present(cue, reaction, done)

        world._present_feedback = capture
        world.update(time.monotonic())
        self.complete_feedback()
        world.now += .3
        self.complete_feedback()
        self.assertEqual(world.interaction.phase, "pick_up")
        self.finish_pickup()
        self.assertEqual(world.interaction.phase, "decide")
        self.assertEqual(world.world.get(item.instance_id).state, ObjectState.PET_HELD)
        self.complete_feedback()
        self.assertEqual(world.interaction.phase, "eat")
        self.assertEqual(world.world.get(item.instance_id).state, ObjectState.CONSUMED)
        self.assertFalse(set(cues) & {
            "object_notice", "object_inspect", "object_recognized",
        })

    def test_known_floor_pickup_stays_known_far_from_aiko_without_a_theft_episode(self):
        app, world = self.app, self.app._world
        item = world.world.place_resting("cookie", world._body_x(),
                                         ObjectFootprint(8, 8))
        world._controls_active = lambda: True
        self.recognize()
        known = world.awareness.known_instance(item.instance_id)
        assert known is not None
        self.assertEqual(known.identity, "cookie")
        self.assertFalse(known.assessed)
        self.assertFalse(world.interaction.active)
        world._controls_active = lambda: False
        with (
            patch.object(app.root, "winfo_pointerx",
                         return_value=world._track().right - 40),
            patch.object(app.root, "winfo_pointery", return_value=100),
        ):
            world.begin_relocate(item.instance_id, item.revision)
            world.now += .2
            world.update(time.monotonic())
            current = world.awareness.known_instance(item.instance_id)
            assert current is not None
            self.assertEqual((current.token, current.identity),
                             (known.token, "cookie"))
            self.assertIsNone(world.awareness.observations[0].identity)
            self.assertTrue(world.cursor.offer_ready)
            self.assertFalse(world.interaction.active)
            self.assertIsNone(app.state.food.last_food_id)
            world.cursor.cancel()

    def test_ordinary_held_wishes_keep_identity_and_actual_origin_at_both_scales(self):
        app, world = self.app, self.app._world
        cues = []
        present = world._present_feedback

        def capture(cue, reaction, done):
            cues.append(cue.event)
            present(cue, reaction, done)

        world._present_feedback = capture
        for scale, item_id, handover in (
            (1, "apple", False), (2, "energy_drink", False),
            (1, "energy_drink", True), (2, "apple", True),
        ):
            with self.subTest(scale=scale, item=item_id, handover=handover):
                cues.clear()
                app.settings.scale = scale
                app._window.resize()
                app._animated.reload_sprites()
                world._sync_geometry()
                app._place_x(world._track().left + 40)
                app.state.satiety, app.state.energy = 76, 65
                friendship = app.state.friendship
                x = world._track().left + int(world._body_x())
                with (
                    patch.object(app.root, "winfo_pointerx", return_value=x),
                    patch.object(app.root, "winfo_pointery",
                                 return_value=world._track().ground_y - 80 * scale),
                ):
                    world.begin_carry(item_id)
                    token = world.cursor.instance_id
                    assert token is not None
                    self.recognize()
                    record = world.awareness.record_for_instance(token)
                    self.assertTrue(world.cursor.offer_ready)
                    self.assertFalse(world.interaction.active)
                    # A wish developed during holding must never count as theft.
                    for _ in range(100):
                        world.now += .25
                        world.update(time.monotonic())
                    self.assertEqual(app.state.friendship, friendship)
                    self.assertFalse(world.interaction.active)
                    if handover:
                        world.cursor.release()
                    else:
                        with patch.object(app.root, "winfo_pointery", return_value=(
                            world._track().ground_y - 300 * scale
                        )):
                            world.cursor.release()
                if not handover:
                    world.now += .1
                    world.update(time.monotonic())
                    self.assertFalse(world.interaction.active)
                    self.assertEqual(world.world.get(token).state, ObjectState.FALLING)
                    world.world.advance_motion(20, world._motion_parameters)
                    world.now += .1
                    world.update(time.monotonic())
                    self.assertEqual(world.awareness.record_for_instance(token), record)
                    self.assertEqual(cues[-1], "object_collect_wanted")
                    self.complete_feedback()
                    self.assertEqual(world.interaction.phase, "pick_up")
                    self.assertEqual(app.state.friendship, friendship)
                    self.finish_pickup()
                else:
                    self.assertEqual(world.interaction.phase, "handover")
                    self.assertEqual(world.world.get(token).state, ObjectState.PET_HELD)
                    self.complete_feedback()
                self.assertEqual(world.interaction.phase, "eat")
                self.assertEqual(world.world.get(token).state, ObjectState.CONSUMED)
                self.assertEqual(world.interaction.memory_id, record)
                self.assertEqual(world._care is not None, handover)
                if not handover:
                    self.assertEqual(app.state.friendship, friendship)
                self.assertFalse(set(cues) & {
                    "object_taken", "object_request_return", "object_withheld",
                    "object_returned", "object_inspect", "object_recognized",
                })
                self.finish_clip("eat")
                self.complete_feedback()
                self.assertFalse(world.interaction.active)

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
            stale(FeedbackReceipt(old.key, True))
            self.assertFalse(world.cursor.offer_ready)
            self.app.state.energy = 40
            world.update(time.monotonic())
            current, done = callbacks[-1]
            stale(FeedbackReceipt(old.key, False))
            self.assertTrue(world.cursor.offer_ready)
            done(FeedbackReceipt(current.key, True))
            self.assertTrue(world.cursor.offer_ready)

    def setUp(self):
        try:
            root = tk.Tk()
            root.update_idletasks()
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
        start = self.app._world.now
        for offset in (0, .3, .7):
            self.app._world.now = start + offset
            self.app._world.update(time.monotonic())
        self.complete_feedback()
        self.complete_feedback()

    def restart(self):
        store = self.app.store
        self.app.quit()
        self.app = DesktopPet(store=store)
        self.addCleanup(self.app.quit)
        self.app._runtime.stop()
        world = self.app._world
        assert world._timer is not None
        self.app.root.after_cancel(world._timer)
        world._timer = None
        world._controls_active = lambda: False
        self.app._action_playback.cancel_at(time.monotonic())

    def test_deferred_drink_survives_cold_restore_and_known_retrieval(self):
        scale, side = 2, "left"
        # Exercise the original inquiry and confirmed put-down first.
        self._placed_drink_round_trip(scale, side)
        old_world = self.app._world
        token = old_world.awareness.memory.snapshot()[0].token
        self.restart()
        world = self.app._world
        known = world.awareness.memory.get(token)
        assert known is not None
        self.assertEqual((known.identity, known.assessed, known.disposition),
                         ("energy_drink", True, "deferred"))
        self.assertEqual(world.awareness.observations, ())
        world.update(time.monotonic())
        self.assertFalse(world.interaction.active)
        self.assertIsNone(world._visual.object_target)
        self.assertFalse(self.app.settings.auto_walk)
        cues = []
        present = world._present_feedback

        def capture(cue, reaction, done):
            cues.append(cue)
            present(cue, reaction, done)

        world._present_feedback = capture
        self.app.state.energy = 55
        world.now += 1.1
        world.update(time.monotonic())
        self.assertEqual(cues[0].event, "object_recall_saved_drink")
        self.complete_feedback()
        self.assertEqual(world.interaction.phase, "approach")
        # Restored history authorizes approach, not invisible acquisition.
        world.now += .3
        world.update(time.monotonic())
        self.assertEqual(world.interaction.phase, "pick_up")
        self.finish_pickup()
        self.assertEqual(world.interaction.phase, "eat")
        self.assertGreater(self.app.state.energy, 64)
        saved = self.app.store.load_session()
        assert saved.world is not None
        assert saved.object_memory is not None
        self.assertEqual(saved.world.objects, ())
        self.assertEqual(saved.object_memory.entries, ())
        self.finish_clip("eat")
        self.complete_feedback()
        self.assertFalse(world.interaction.active)
        self.assertEqual([cue.event for cue in cues], [
            "object_recall_saved_drink", "object_consuming_drink",
            "object_finished_drink",
        ])
        self.assertEqual(self.app.state.friendship, 15)
        self.restart()
        self.assertEqual(self.app._world.awareness.memory.snapshot(), ())
        self.assertEqual(self.app._world.world.snapshot().objects, ())

    def test_observed_alternative_cannot_replace_committed_approach(self):
        world = self.app._world
        self.app._place_x(world._track().left)
        old = world.awareness.memory.observe_find(ObjectObservation(
            "old_sighting", "apple", "food", world._body_x() + 300, 0, True, 0,
        ), now=0, record=None, claimed=frozenset(), maximum_distance=10)
        world.awareness.memory.mark_assessed(old)
        world.update(time.monotonic())
        self.complete_feedback()
        self.assertEqual(world.interaction.memory_id, old)
        item = world.world.place_resting("apple", world._body_x() + 70,
                                         ObjectFootprint(8, 8))
        for stamp in (1, 1.3, 1.7):
            world.now = stamp
            world.update(time.monotonic())
        self.assertIsNone(world.awareness.known_instance(item.instance_id))
        self.complete_feedback()
        self.complete_feedback()
        world.now = 2.8
        world.update(time.monotonic())
        self.assertEqual(world.interaction.memory_id, old)
        goal = world.awareness.intentions.goal
        assert goal is not None
        self.assertEqual(goal.token, old)

    def test_hover_clicks_and_other_cancelled_gesture_keep_the_episode(self):
        world = self.app._world
        world.world.place_resting("apple", world._body_x() + 70,
                                  ObjectFootprint(8, 8))
        self.recognize()
        record = world.interaction.memory_id
        phase = world.interaction.phase
        friendship = self.app.state.friendship
        self.app._on_enter()
        self.app._on_click_left()
        self.app._on_click_right()
        world.begin_carry("energy_drink")
        world.cursor.cancel()
        self.assertEqual(world.interaction.memory_id, record)
        self.assertEqual(world.interaction.phase, phase)
        self.assertEqual(self.app.state.friendship, friendship)
        self.assertEqual(list(self.app.mind.clicks), [])
        self.complete_feedback()
        self.complete_feedback()
        world.update(time.monotonic())
        before = self.app.settings.x or 0
        self.app.mind.cursor_attention.attention_until = time.monotonic() + 100
        self.app._animation.advance_walk(time.monotonic(), .2, game_mode=False)
        self.assertNotEqual(self.app.settings.x, before)

    def test_taken_target_is_followed_through_hops_and_resumes_at_both_scales(self):
        world = self.app._world
        for scale in (1, 2):
            with self.subTest(scale=scale):
                self.app.settings.scale = scale
                self.app._window.resize()
                self.app._animated.reload_sprites()
                world._sync_geometry()
                self.app._place_x(world._track().left + 40)
                self.app.state.satiety = 50
                item = world.world.place_resting(
                    "apple", world._body_x() + 70 * scale, ObjectFootprint(8, 8),
                )
                self.recognize()
                record = world.interaction.memory_id
                episode = world.interaction.feedback_key.interaction_id
                assert record is not None
                world.begin_relocate(item.instance_id, item.revision)
                self.assertEqual(world.interaction.phase, "await_return")
                with (
                    patch.object(self.app.root, "winfo_pointerx",
                                 return_value=world._track().right - 40),
                    patch.object(self.app.root, "winfo_pointery", return_value=100),
                ):
                    world.cursor._move_carry()
                world.now += .15
                world.update(time.monotonic())
                self.assertEqual(world.interaction.phase, "await_return")
                self.assertEqual(world.awareness.record_for_instance(item.instance_id),
                                 record)
                held = world.world.get(item.instance_id)
                assert held.position is not None
                self.assertEqual(world._visual.object_target, (
                    world._track().left + held.position.x,
                    world._track().ground_y - held.position.height,
                ))
                self.complete_feedback()
                with (
                    patch.object(self.app.root, "winfo_pointerx",
                                 return_value=int(world._body_x()) + 120 * scale),
                    patch.object(self.app.root, "winfo_pointery",
                                 return_value=world._track().ground_y - 200 * scale),
                ):
                    world.cursor.release()
                world.now += .15
                world.update(time.monotonic())
                self.assertEqual(world.interaction.phase, "await_settle")
                world.world.advance_motion(20, world._motion_parameters)
                world.now += .15
                world.update(time.monotonic())
                self.assertEqual(world.interaction.phase, "approach")
                self.assertEqual(world.interaction.feedback_key.interaction_id, episode)
                self.complete_feedback()
                for index in range(10):
                    self.app._walk.step(time.monotonic() + index, 1,
                                        game_mode=False, attention_active=False)
                    world.now += .15
                    world.update(time.monotonic())
                    if world.interaction.phase == "pick_up":
                        break
                self.assertEqual(world.interaction.phase, "pick_up")
                self.finish_pickup()
                self.finish_inspection()
                self.finish_clip("eat")
                self.complete_feedback()
                self.assertEqual(world.world.get(item.instance_id).state,
                                 ObjectState.CONSUMED)

    def test_visible_withholding_changes_friendship_once_and_survives_restart(self):
        world = self.app._world
        item = world.world.place_resting("apple", world._body_x() + 70,
                                         ObjectFootprint(8, 8))
        self.recognize()
        world.begin_relocate(item.instance_id, item.revision)
        self.complete_feedback()
        initial = self.app.state.friendship
        self.assertEqual(initial, 15)
        for _ in range(44):
            world.now += .5
            world.update(time.monotonic())
            self.complete_feedback()
        self.assertAlmostEqual(self.app.state.friendship, initial - .15)
        self.assertEqual(self.app.mind.emotion(self.app.state, time.monotonic()),
                         "irritated")
        self.assertEqual(world.interaction.phase, "await_return")
        stored = self.app.store.load_session().state
        self.assertAlmostEqual(stored.friendship, initial - .15)
        world.cursor.cancel()
        self.complete_feedback()
        self.complete_feedback()
        self.assertAlmostEqual(self.app.state.friendship, initial - .15)
        self.restart()
        self.assertFalse(self.app._world.interaction.active)
        self.assertAlmostEqual(self.app.state.friendship, initial - .15)

    def test_absent_remembered_instance_requires_attentive_local_search(self):
        world = self.app._world
        self.app.state.energy = 65
        item = world.world.place_resting("energy_drink", world._body_x(),
                                         ObjectFootprint(12, 12))
        self.recognize()
        self.finish_pickup()
        self.finish_inspection()
        self.finish_clip("put_down")
        record = world.awareness.memory.snapshot()[0].token
        # Hide the actual removal from perception, then persist both owners.
        current = world.world.get(item.instance_id)
        world.world.remove(current.instance_id, expected_revision=current.revision)
        self.app._save()
        self.restart()
        world = self.app._world
        self.assertIsNotNone(world.awareness.memory.get(record))
        self.app.state.energy = 55
        world.update(time.monotonic())
        self.complete_feedback()
        self.assertEqual(world.interaction.phase, "approach")
        self.assertIsNotNone(world.awareness.memory.get(record))
        world.now += 1
        world.update(time.monotonic())
        self.assertIsNotNone(world.awareness.memory.get(record))
        self.assertEqual(world.interaction.phase, "search")
        self.complete_feedback()
        world.now += 1.1
        world.update(time.monotonic())
        self.assertEqual(world.interaction.phase, "search")
        self.assertIsNotNone(world._visual.object_target)
        world.now += 1
        world.update(time.monotonic())
        self.assertEqual(world.interaction.phase, "missing")
        missing = world.awareness.memory.get(record)
        assert missing is not None
        self.assertEqual(missing.place_status, "missing")
        self.complete_feedback()
        world.now += 20
        world.update(time.monotonic())
        self.assertFalse(world.interaction.active)
        self.assertIsNone(world.awareness.intentions.goal)
        self.assertIsNone(world._visual.object_target)

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

    def test_deferred_known_drink_releases_gaze_and_returns_only_when_wanted(self):
        world = self.app._world
        self.app.state.energy = 65
        world.world.place_resting("energy_drink", world._body_x(),
                                  ObjectFootprint(12, 12))
        self.recognize()
        self.finish_pickup()
        self.finish_inspection()
        self.assertEqual(world.interaction.phase, "put_down")
        self.finish_clip("put_down")
        self.assertFalse(world.interaction.active)
        world.now += 1
        world.update(time.monotonic())
        known, = world.awareness.memory.snapshot()
        self.assertEqual(known.identity, "energy_drink")
        self.assertTrue(known.assessed)
        self.assertIsNone(world.awareness.intentions.goal)
        self.assertIsNone(world._visual.object_target)
        eyes_x, eyes_y = self.app._window.gaze_origin()
        self.assertEqual(world._visual.gaze_direction(
            (round(eyes_x + 200), round(eyes_y)),
        ), 4)
        self.app.state.energy = 55
        world.now += 11
        world.update(time.monotonic())
        goal = world.awareness.intentions.goal
        assert goal is not None
        self.assertEqual((goal.token, goal.purpose), (known.token, "consume"))

    def test_new_drink_inquiry_bypasses_pause_after_consuming_known_food(self):
        world = self.app._world
        food = world.world.place_resting("onigiri", world._body_x(),
                                         ObjectFootprint(16, 16))
        self.recognize()
        self.finish_pickup()
        self.finish_inspection()
        self.assertEqual(world.world.get(food.instance_id).state, ObjectState.CONSUMED)
        self.finish_clip("eat")
        self.complete_feedback()
        self.assertFalse(world.interaction.active)
        consumed_at = world.now
        self.app.state.energy = 66
        cues = []
        present = world._present_feedback

        def capture(cue, reaction, done):
            cues.append(cue.event)
            present(cue, reaction, done)

        world._present_feedback = capture
        drink = world.world.place_resting("energy_drink", world._body_x(),
                                          ObjectFootprint(12, 12))
        self.recognize()
        self.assertEqual(world.interaction.phase, "pick_up")
        self.assertLess(world.now - consumed_at, BALANCE.number(
            "object_behavior", "consumed_pause_seconds",
        ))
        self.finish_pickup()
        self.finish_inspection()
        self.finish_clip("put_down")
        self.assertFalse(world.interaction.active)
        self.assertEqual(cues, [
            "object_notice", "object_approach", "object_pick_up", "object_inspect",
            "object_recognized", "object_later", "object_put_down",
        ])
        known, = world.awareness.memory.snapshot()
        self.assertEqual((known.identity, known.assessed, known.disposition),
                         ("energy_drink", True, "deferred"))
        self.assertEqual(world.world.get(drink.instance_id).state, ObjectState.RESTING)
        self.assertIsNone(world._visual.object_target)
        self.assertAlmostEqual(self.app.state.energy, 66, places=1)
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
            token = world.cursor.instance_id
            assert token is not None
            world.cursor.release()
            self.assertEqual(world.world.get(token).state, ObjectState.PET_HELD)
            self.assertEqual(world.interaction.phase, "handover")
            self.complete_feedback()
            self.assertEqual(world.world.get(token).state, ObjectState.CONSUMED)
            self.assertGreater(app.state.energy, 49)
            app._action_playback.cancel_at(time.monotonic())
            world.interrupt(lambda: None)
            world.begin_carry("energy_drink")
            # Starting a gesture saves through the shared active-time owner.
            # Establish the exact capacity boundary after that time advance.
            app.state.energy = 100
            for now in (1, 1.3, 1.7):
                world.now = now
                world.update(time.monotonic())
            token = world.cursor.instance_id
            assert token is not None
            world.cursor.release()
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

    def test_immediate_scale_save_updates_geometry_without_resetting_motion(self):
        world = self.app._world
        image = world.view.image("apple", 1)
        item = world.world.create_held("apple", WorldPosition(30, 300),
                                       ObjectFootprint(image.width() / 2,
                                                       image.width() / 2))
        world.world.release(item.instance_id, expected_revision=item.revision)
        world.world.advance_motion(.2, world._motion_parameters)
        before = world.world.get(item.instance_id).motion
        self.app.settings.scale = 2
        checkpoint = world.save_snapshot()
        changed = world.world.get(item.instance_id)
        self.assertEqual(changed.motion, before)
        self.assertEqual(changed.footprint.left,
                         world.view.image("apple", 2).width() / 2)
        self.assertEqual(checkpoint.world.surface, world._surface())
        world.world.advance_motion(20, world._motion_parameters)
        settled = world.world.get(item.instance_id)
        assert settled.position is not None
        self.assertEqual(settled.position.x, checkpoint.world.surface.ground_x(
            settled.position.x, settled.footprint,
        ))

    def test_lost_input_capture_cancels_without_falling_or_consuming(self):
        world = self.app._world
        world.begin_carry("apple")
        token = world.cursor.instance_id
        assert token is not None
        self.assertEqual(self.app.root.grab_current(), self.app.root)
        self.app.root.grab_release()
        world._frame()
        self.assertIsNone(world.cursor.instance_id)
        self.assertEqual(world.world.get(token).state, ObjectState.REMOVED)
        self.assertIsNone(self.app.state.food.last_food_id)

    def test_existing_portion_cancel_and_drop_share_capture_without_recreation(self):
        world = self.app._world
        item = world.world.place_resting("apple", world._body_x(),
                                         ObjectFootprint(8, 8))
        world.begin_relocate(item.instance_id, item.revision)
        self.assertEqual(world.cursor.instance_id, item.instance_id)
        self.app.root.grab_release()
        world.cursor.update()
        returned = world.world.get(item.instance_id)
        self.assertEqual(returned.state, ObjectState.RESTING)
        self.assertEqual(returned.position, item.position)
        with (
            patch.object(self.app.root, "winfo_pointerx", return_value=20),
            patch.object(self.app.root, "winfo_pointery", return_value=200),
        ):
            world.begin_relocate(item.instance_id, returned.revision)
            carried = world.world.get(item.instance_id)
            self.assertNotEqual(carried.position, returned.position)
            self.assertEqual(carried.state, ObjectState.USER_HELD)
            world.cursor.release()
        dropped = world.world.get(item.instance_id)
        self.assertEqual(dropped.state, ObjectState.FALLING)
        self.assertEqual(len(world.world.snapshot().objects), 1)
        world.begin_relocate(item.instance_id, dropped.revision)
        self.assertFalse(world.cursor.carrying)
        world.world.advance_motion(20, world._motion_parameters)
        self.assertEqual(world.world.get(item.instance_id).state, ObjectState.RESTING)
        self.assertIsNone(self.app.state.food.last_food_id)

    def test_existing_portion_capture_failure_returns_it_instead_of_deleting_it(self):
        world = self.app._world
        item = world.world.place_resting("apple", world._body_x(),
                                         ObjectFootprint(8, 8))
        with patch.object(self.app.root, "grab_set", side_effect=tk.TclError):
            world.begin_relocate(item.instance_id, item.revision)
        self.assertFalse(world.cursor.carrying)
        returned = world.world.get(item.instance_id)
        self.assertEqual(returned.state, ObjectState.RESTING)
        self.assertEqual(returned.position, item.position)

    def test_resting_item_press_uses_visible_pixels_and_cannot_award_pet_care(self):
        world = self.app._world
        item = world.world.place_resting("apple", world._body_x(),
                                         ObjectFootprint(8, 8))
        world._sync_view()
        self.app.root.update()
        entry = world.view._windows[item.instance_id]
        image = world.view.image("apple", 1)
        clear = next((x, y) for y in range(image.height())
                     for x in range(image.width()) if image.transparency_get(x, y)
                     or image.get(x, y) == (255, 0, 255))
        opaque = next((x, y) for y in range(image.height())
                      for x in range(image.width())
                      if not image.transparency_get(x, y)
                      and image.get(x, y) != (255, 0, 255))
        care = self.app.state.friendship
        entry.label.event_generate("<ButtonPress-1>", x=clear[0], y=clear[1])
        self.assertFalse(world.cursor.carrying)
        entry.label.event_generate("<ButtonPress-1>", x=opaque[0], y=opaque[1])
        self.assertEqual(world.cursor.instance_id, item.instance_id)
        world._sync_view()
        self.assertFalse(entry.interactive)
        world.cursor.cancel()
        self.assertEqual(self.app.state.friendship, care)

    def test_released_button_cannot_start_a_gesture_after_queued_putdown(self):
        world = self.app._world
        item = world.world.place_resting("apple", world._body_x(),
                                         ObjectFootprint(8, 8))
        pending = []
        with patch.object(world.interaction, "interrupt", side_effect=pending.append):
            world.begin_relocate(item.instance_id, item.revision)
        self.assertFalse(world.cursor.carrying)
        with patch("aiko_pet.desktop.world_runtime.mouse_buttons_down_windows",
                   return_value=(False, False)):
            pending[0]()
        self.assertFalse(world.cursor.carrying)
        self.assertEqual(world.world.get(item.instance_id).state, ObjectState.RESTING)

    def test_primary_monitor_exclusive_right_edge_returns_only_existing_portions(self):
        world = self.app._world
        for existing in (False, True):
            with (
                self.subTest(existing=existing),
                patch.object(self.app.root, "winfo_pointerx",
                             return_value=world._track().right),
                patch.object(self.app.root, "winfo_pointery", return_value=200),
            ):
                if existing:
                    item = world.world.place_resting("apple", world._body_x(),
                                                     ObjectFootprint(8, 8))
                    world.begin_relocate(item.instance_id, item.revision)
                else:
                    world.begin_carry("apple")
                token = world.cursor.instance_id
                assert token is not None
                world.cursor.release()
                expected = ObjectState.RESTING if existing else ObjectState.REMOVED
                self.assertEqual(world.world.get(token).state, expected)

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

    def _reach_placed_drink(self, scale, side):
        app, world = self.app, self.app._world
        app.settings.scale = scale
        app._window.resize()
        app._animated.reload_sprites()
        world._sync_geometry()
        app.state.energy = 65
        track = world._track()
        boundary = track.left if side == "left" else track.right - world.width
        app._place_x(boundary + (120 * scale if side == "left" else -120 * scale))
        image = world.view.image("energy_drink", scale)
        footprint = ObjectFootprint(image.width() / 2, image.width() / 2)
        x = (footprint.left if side == "left" else
             world.world.snapshot().surface.width - footprint.right)
        item = world.world.place_resting("energy_drink", x, footprint)
        self.recognize()
        self.assertEqual(world.interaction.phase, "approach")
        self.assertEqual(app._walk.movement.goal_x, boundary)
        self.assertFalse(world._can_acquire(item.instance_id))
        for index in range(10):
            app._walk.step(time.monotonic() + index, 1,
                           game_mode=False, attention_active=False)
            world.now += 1
            world.update(time.monotonic())
            current_x = app.settings.x
            assert current_x is not None
            self.assertGreaterEqual(current_x, track.left)
            self.assertLessEqual(current_x + world.width, track.right)
            if world.interaction.phase == "pick_up":
                break
        self.assertEqual(world.interaction.phase, "pick_up")
        current_x = app.settings.x
        assert current_x is not None
        self.assertAlmostEqual(current_x, boundary, delta=2)
        return item

    def _placed_drink_round_trip(self, scale, side):
        item = self._reach_placed_drink(scale, side)
        world, animated = self.app._world, self.app._animated
        clip = animated.assets.clips["pick_up"]
        for index in range(1, 4):
            stamp = animated.frame_clock.frame_started_at
            animated.show_frame("pick_up",
                                stamp + clip.timings[index - 1] / 1000 + .001)
            self.app.root.update_idletasks()
            expected = ObjectState.RESTING if index < 3 else ObjectState.PET_HELD
            self.assertEqual(world.world.get(item.instance_id).state, expected)
        world._sync_view()
        overlay = animated.food_overlay
        self.assertIsNotNone(overlay.contact_origin)
        anchor = clip.frames[3].food_anchor
        assert anchor is not None
        pivot = world.view.items.foods["energy_drink"].sprites[scale].pivot
        with patch("aiko_pet.ui.pet_view.food_overlay.time.monotonic",
                   return_value=overlay._contact_at + .14):
            world._sync_view()
        self.assertEqual(self.app.canvas.coords(overlay.item), [
            round((96 - clip.anchor[0] + anchor[0]) * scale - pivot[0]),
            round((FOOT_BASELINE - clip.anchor[1] + anchor[1]) * scale - pivot[1]),
        ])
        self.assertAlmostEqual(self.app.state.energy, 65, places=1)
        self.finish_pickup()
        self.finish_inspection()
        self.assertEqual(world.interaction.phase, "put_down")
        self.finish_clip("put_down")
        self.assertFalse(world.interaction.active)
        placed = world.world.get(item.instance_id)
        self.assertEqual(placed.state, ObjectState.RESTING)
        assert placed.position is not None and item.position is not None
        self.assertEqual(placed.position.x, world._body_x())
        self.assertNotEqual(placed.position.x, item.position.x)
        self.assertEqual(placed.position.height, 0)
        self.assertTrue(world.world.snapshot().surface.contains(
            placed.position, placed.footprint,
        ))
        known, = world.awareness.memory.snapshot()
        self.assertTrue(known.assessed)
        self.assertEqual(known.x, placed.position.x)
        self.assertIsNone(world._visual.object_target)
        self.assertAlmostEqual(self.app.state.energy, 65, places=1)

    def test_ground_pickup_rechecks_actual_reach_at_frame_four(self):
        item = self._reach_placed_drink(1, "left")
        animated, world = self.app._animated, self.app._world
        clip = animated.assets.clips["pick_up"]
        for index in (0, 1):
            animated.show_frame("pick_up", animated.frame_clock.frame_started_at
                                + clip.timings[index] / 1000 + .001)
            self.app.root.update_idletasks()
        self.app._place_x(world._track().left + world.width)
        animated.show_frame("pick_up", animated.frame_clock.frame_started_at
                            + clip.timings[2] / 1000 + .001)
        self.app.root.update_idletasks()
        self.assertFalse(world.interaction.active)
        self.assertEqual(world.world.get(item.instance_id).state, ObjectState.RESTING)
        self.assertIsNone(animated.food_overlay.current_food_id)
        self.assertAlmostEqual(self.app.state.energy, 65, places=1)

    def test_wanted_placed_drink_consumes_only_after_grasp_and_inspection(self):
        item = self._reach_placed_drink(2, "right")
        world = self.app._world
        self.app.state.energy = 50
        self.finish_pickup()
        self.assertEqual(world.interaction.phase, "inspect")
        self.assertEqual(world.world.get(item.instance_id).state, ObjectState.PET_HELD)
        self.assertEqual(self.app.state.energy, 50)
        self.finish_inspection()
        self.assertEqual(world.interaction.phase, "eat")
        self.assertEqual(world.world.get(item.instance_id).state, ObjectState.CONSUMED)
        self.assertGreater(self.app.state.energy, 59)
        self.assertLess(self.app.state.energy, 61)
        self.assertEqual(self.app.state.friendship, 15)

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
