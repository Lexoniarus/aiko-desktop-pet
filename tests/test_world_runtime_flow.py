"""Exercise real Tk widgets and desktop gates with controlled event time."""

import tempfile
import time
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import patch

from aiko_pet.application.settings import PetSettings
from aiko_pet.infrastructure.persistence import StateStore
from aiko_pet.pet.balance import BALANCE
from aiko_pet.pet.mind.catalog import Reaction
from aiko_pet.pet.mind.object_perception import ObjectObservation
from aiko_pet.pet.mind.reaction_sequence import Cue
from aiko_pet.pet.state import PetState
from aiko_pet.world.contracts import ObjectFootprint, ObjectState
from tools.desktop_test_support import create_test_desktop
from tools.pet_test_support import set_test_pet_values
from tools.tk_test_time import ControlledTkTime


class WorldRuntimeFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            root = tk.Tk()
            root.destroy()
        except tk.TclError as error:
            raise unittest.SkipTest(str(error)) from error

    def setUp(self):
        self.timing = self.enterContext(ControlledTkTime())
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        store = StateStore(Path(folder.name) / "state.json")
        store.save(
            PetState(satiety=76, energy=60),
            PetSettings(
                auto_walk=False,
                auto_routine=False,
                observe_computer=False,
                learn_rhythm=False,
                spontaneous_talk=False,
            ),
        )
        self.app = create_test_desktop(store=store)
        self.addCleanup(self.app.quit)
        greeting = self.app._runtime.scheduled_greeting
        if greeting is not None:
            self.app.root.after_cancel(greeting)
            self.app._runtime.scheduled_greeting = None
        for method in ("winfo_pointerx", "winfo_pointery"):
            self.enterContext(patch.object(self.app.root, method, return_value=0))
        self.feedback = []
        self.bubbles = []
        self.orientation_sides = []
        present = self.app._world._present_feedback

        def observe_feedback(cue, reaction, done):
            self.feedback.append((self.app._world.now, cue.event, reaction.text))
            present(cue, reaction, done)

        self.app._world._present_feedback = observe_feedback

    def bubble_text(self):
        bubble = self.app._speech.bubble
        if bubble is None:
            return ""
        pending = list(bubble.winfo_children())
        while pending:
            widget = pending.pop()
            if isinstance(widget, tk.Label) and widget.cget("text"):
                return str(widget.cget("text"))
            pending.extend(widget.winfo_children())
        return ""

    def begin_native_search(self):
        app, world = self.app, self.app._world
        app.settings.follow_cursor = False
        set_test_pet_values(app.state, satiety=100, energy=100)
        track = world._track()
        app._place_x(track.left + (track.right - track.left - world.width) / 2)
        x = world._body_x() + .3 * world.width
        item = world.world.place_resting("cookie", x, ObjectFootprint(8, 8))
        record = world.awareness.memory.observe_find(
            ObjectObservation("earlier", "cookie", "food", x, 0, True, world.now),
            now=world.now, record=None, claimed=frozenset(), maximum_distance=0,
            instance_id=item.instance_id,
        )
        world.awareness.memory.mark_assessed(record)
        world.world.remove(item.instance_id, expected_revision=item.revision)
        world._behavior.request_orientation()
        trace = self.run_until(lambda: world.interaction.search_ready, 12)
        self.assertTrue(world.interaction.search_ready, trace)
        self.run_for(.3)
        return record

    def test_stationary_hover_opens_ui_without_pausing_search_or_candidate(self):
        record = self.begin_native_search()
        app, world = self.app, self.app._world
        app.root.update_idletasks()
        pointer = (app.root.winfo_rootx() + app.root.winfo_width() // 2,
                   app.root.winfo_rooty() + app.root.winfo_height() // 2)
        direction = -1 if app._walk.movement.remaining_distance < 0 else 1
        candidate = world.world.place_resting(
            "onigiri", world._body_x() + direction * 1.5 * world.width,
            ObjectFootprint(8, 8),
        )
        friendship = app.state.friendship
        with (
            patch.object(app.root, "winfo_pointerx", return_value=pointer[0]),
            patch.object(app.root, "winfo_pointery", return_value=pointer[1]),
            # The simulated hover belongs to this sprite even when another
            # application covers it on the machine running these timer tests.
            patch.object(app.root, "winfo_containing", return_value=app.canvas),
        ):
            self.assertTrue(app._hover.pointer_inside(*pointer))
            trace = self.run_until(lambda: world.interaction.phase == "approach", 3)
            self.assertEqual(world.interaction.phase, "approach", trace)
            self.assertTrue(app._hover.menu_engaged)
            self.assertIsNotNone(app._hover.toolbar)
            toolbar = app._hover.toolbar
            assert toolbar is not None
            self.assertTrue(all(button.cget("state") == "disabled"
                                for action, button in toolbar.buttons.items()
                                if action != "place_item"))
            social = app.state.social
            toolbar.buttons["talk"].invoke()
            app._hover._interact("talk")
            self.assertEqual(app.state.social, social)
            self.assertIsNone(app._hover.social_menu)
            app._hover._food_selected("energy_drink")
            # Placement saves and advances measured life time. Natural need
            # decay is valid; blocked talk and stock placement grant no care.
            self.assertLessEqual(app.state.social, social)
            self.assertTrue(world.cursor.carrying)
            world.cursor.cancel()
            before = app.settings.x
            self.run_for(.2)
            self.assertNotEqual(app.settings.x, before)
        focus = world.interaction.memory_id
        assert focus is not None
        self.assertEqual(world.awareness.instance_for_record(focus),
                         candidate.instance_id)
        self.assertTrue(world.interaction.search_active)
        missing = world.awareness.memory.get(record)
        assert missing is not None
        self.assertEqual(missing.place_status, "missing")
        self.assertEqual(app.state.friendship, friendship)
        self.assertEqual(list(app.mind.clicks), [])
        self.assertEqual([event for _, event, _ in self.feedback], [
            "object_place_missing", "object_search", "object_approach",
        ])

    def test_search_click_reply_keeps_native_patrol_and_hover_active(self):
        record = self.begin_native_search()
        app, world = self.app, self.app._world
        app.root.update_idletasks()
        friendship, social = app.state.friendship, app.state.social
        for click in (app._on_click_left, app._on_click_right):
            pointer = (app.root.winfo_rootx() + app.root.winfo_width() // 2,
                       app.root.winfo_rooty() + app.root.winfo_height() // 2)
            with (
                patch.object(app.root, "winfo_pointerx", return_value=pointer[0]),
                patch.object(app.root, "winfo_pointery", return_value=pointer[1]),
            ):
                click()
                self.run_until(lambda: world.interaction.contact_feedback_active, 1)
                self.assertTrue(world.interaction.contact_feedback_active)
                self.assertEqual(self.feedback[-1][1], "object_busy_search")
                self.assertTrue(self.bubble_text())
                self.assertTrue(app._hover.menu_engaged)
                toolbar = app._hover.toolbar
                assert toolbar is not None
                self.assertTrue(all(button.cget("state") == "disabled"
                                    for action, button in toolbar.buttons.items()
                                    if action != "place_item"))
                before = app.settings.x
                progress = world.interaction.search_progress
                self.run_for(.35)
                self.assertIsNotNone(app._speech.bubble)
                self.assertNotEqual(app.settings.x, before)
                self.assertTrue(world.interaction.search_ready)
                self.assertEqual(world.interaction.search_progress, progress)
                self.assertEqual(world.interaction.memory_id, record)
                self.assertFalse(world.cursor.carrying)
                self.assertEqual(app.state.friendship, friendship)
                self.assertAlmostEqual(app.state.social, social, delta=.05)
                self.assertEqual(list(app.mind.clicks), [])
        direction = -1 if app._walk.movement.remaining_distance < 0 else 1
        world.world.place_resting(
            "onigiri", world._body_x() + direction * 1.5 * world.width,
            ObjectFootprint(8, 8),
        )
        trace = self.run_until(lambda: world.interaction.phase == "approach", 3)
        self.assertEqual(world.interaction.phase, "approach", trace)
        self.assertTrue(world.interaction.search_active)
        self.assertFalse(world.interaction.contact_feedback_active)
        self.assertEqual([event for _, event, _ in self.feedback], [
            "object_place_missing", "object_search", "object_busy_search",
            "object_approach",
        ])

    def test_conversation_focus_ends_only_after_native_sequence_completion(self):
        world = self.app._world
        x = world._body_x() + .2 * world.width
        item = world.world.place_resting("cookie", x, ObjectFootprint(8, 8))
        record = world.awareness.memory.observe_find(
            ObjectObservation(item.instance_id, "cookie", "food", x, 0, True,
                              world.now),
            now=world.now, record=None, claimed=frozenset(), maximum_distance=0,
            instance_id=item.instance_id,
        )
        world.awareness.memory.mark_assessed(record)
        original = world.awareness.memory.get(record)
        # Keep the real care/focus/player wiring, without replaying a long
        # catalogue story whose pacing is covered by scheduler tests.
        reaction = Reaction(
            "focus-wiring", (Cue("pause", "", 250), Cue("text", "Moment.", 250),
                             Cue("pause", "", 250)), "idle", "talk",
        )
        with patch.object(self.app.mind, "select_reaction", return_value=reaction):
            self.app.interact("talk")
        self.assertEqual(world._attention().mode, "unavailable")
        with (
            patch.object(self.app.root, "winfo_pointerx", return_value=int(
                world._track().left + world.world.snapshot().surface.width * .2,
            )),
            patch.object(self.app.root, "winfo_pointery",
                         return_value=world._track().ground_y),
        ):
            world.begin_relocate(item.instance_id, item.revision)
            self.assertFalse(world.awareness.following_cursor)
            world.cursor.release()
        world.world.place_resting("onigiri", world._body_x() - .7 * world.width,
                                   ObjectFootprint(8, 8))
        self.run_for(.08)
        self.assertIsNone(self.app._speech.bubble)
        self.assertEqual(world._attention().mode, "unavailable")
        self.assertIsNotNone(self.app._reaction_player.pending_timer)
        self.assertEqual(world.awareness.memory.get(record), original)
        self.assertEqual(len(world.awareness.memory.snapshot()), 1)
        self.assertEqual(self.feedback, [])
        self.run_until(lambda: bool(self.feedback), 5)
        self.assertTrue(self.feedback)
        self.assertEqual(self.feedback[0][1], "object_place_missing")
        self.assertEqual(self.orientation_sides, [-1, 1])
        missing = world.awareness.memory.get(record)
        assert missing is not None
        self.assertEqual(missing.place_status, "missing")

    def test_restored_food_uses_readable_recall_and_full_eat_without_reinspection(self):
        world = self.app._world
        set_test_pet_values(self.app.state, satiety=76)
        set_test_pet_values(self.app.state, energy=66)
        item = world.world.place_resting(
            "onigiri", world._body_x() + 20, ObjectFootprint(16, 16)
        )
        record = world.awareness.memory.observe_find(
            ObjectObservation(item.instance_id, "onigiri", "food",
                              world._body_x() + 20, 0, True, world.now),
            now=world.now, record=None, claimed=frozenset(), maximum_distance=0,
            instance_id=item.instance_id,
        )
        world.awareness.memory.mark_assessed(record)
        world.awareness.memory.note_placement(
            record,
            x=world._body_x() + 20,
            height=0,
            now=world.now,
            deferred=True,
        )
        store = self.app.store
        self.app.quit()
        self.app = create_test_desktop(store=store)
        self.addCleanup(self.app.quit)
        greeting = self.app._runtime.scheduled_greeting
        if greeting is not None:
            self.app.root.after_cancel(greeting)
            self.app._runtime.scheduled_greeting = None
        for method in ("winfo_pointerx", "winfo_pointery"):
            self.enterContext(patch.object(self.app.root, method, return_value=0))
        world = self.app._world
        self.assertEqual(world.awareness.observations, ())
        self.feedback.clear()
        self.bubbles.clear()
        present = world._present_feedback

        def observe_feedback(cue, reaction, done):
            self.feedback.append((world.now, cue.event, reaction.text))
            present(cue, reaction, done)

        world._present_feedback = observe_feedback
        idle = self.run_until(lambda: world.orientation_side() is None, 3)
        self.assertTrue(all(row[1] == "idle" for row in idle), idle)
        self.assertIsNone(world._visual.object_target)
        set_test_pet_values(self.app.state, satiety=55)
        trace = self.run_until(lambda: world.interaction.phase == "finish", 18)
        self.assertEqual(world.interaction.phase, "finish", trace)
        phases = {row[1] for row in trace}
        self.assertTrue(
            {"notice", "approach", "pick_up", "eat", "finish"}.issubset(phases), trace
        )
        self.assertTrue(phases.isdisjoint({"inspect", "recognize", "decide"}), trace)
        eating = next(row[0] for row in trace if row[1] == "eat")
        finished = next(row[0] for row in trace if row[1] == "finish")
        self.assertGreaterEqual(finished - eating, 3.4, trace)
        self.assertEqual(
            [cue[1] for cue in self.feedback],
            [
                "object_recall_saved_food",
                "object_consuming_food",
                "object_finished_food",
            ],
        )
        self.assertTrue(any("Onigiri" in text for _, _, text in self.bubbles))
        loaded = store.load_session()
        assert loaded.world is not None
        assert loaded.object_memory is not None
        self.assertEqual(loaded.world.objects, ())
        self.assertEqual(loaded.object_memory.entries, ())
        self.assertEqual(self.app.state.friendship, 15)

    def run_for(self, seconds):
        return self.run_until(lambda: False, seconds)

    def run_until(self, predicate, seconds):
        trace = []
        until = time.monotonic() + seconds

        def sample():
            world, animated = self.app._world, self.app._animated
            goal = world.awareness.intentions.goal
            side = world.orientation_side()
            if side is not None and world._attention().mode == "survey":
                if not self.orientation_sides or self.orientation_sides[-1] != side:
                    self.orientation_sides.append(side)
            row = (
                world.now,
                world.interaction.phase,
                animated.frame_clock.active_key,
                animated.frame_clock.frame_index,
                self.app.settings.x,
                goal.purpose if goal else None,
            )
            if not trace or row[1:] != trace[-1][1:]:
                trace.append(row)
            text = self.bubble_text()
            if text and (not self.bubbles or self.bubbles[-1][2] != text):
                self.bubbles.append((world.now, world.interaction.phase, text))

        while True:
            sample()
            if predicate() or time.monotonic() + 1e-9 >= until:
                break
            self.timing.advance(min(.025, until - time.monotonic()))
        return trace

    def test_right_edge_scale_two_pickup_uses_actual_motion_and_attachment(self):
        app, world = self.app, self.app._world
        scale = 2
        app.settings.scale = scale
        app._window.resize()
        app._animated.reload_sprites()
        world._sync_geometry()
        set_test_pet_values(app.state, energy=65)
        track = world._track()
        boundary = track.right - world.width
        app._place_x(boundary - 60 * scale)
        image = world.view.image("energy_drink", scale)
        footprint = ObjectFootprint(image.width() / 2, image.width() / 2)
        item = world.world.place_resting(
            "energy_drink", world.world.snapshot().surface.width - footprint.right,
            footprint,
        )
        assert item.position is not None
        object_x = track.left + item.position.x
        self.assertFalse(world._can_acquire(item.instance_id))
        trace = self.run_until(
            lambda: world.world.get(item.instance_id).state == ObjectState.PET_HELD,
            12,
        )
        self.assertEqual(world.world.get(item.instance_id).state,
                         ObjectState.PET_HELD, trace)
        current_x = app.settings.x
        assert current_x is not None
        self.assertAlmostEqual(current_x, boundary, delta=2)
        self.assertTrue(track.can_grasp_ground(
            object_x, current_x, int(world.width),
            world.width * BALANCE.number("object_behavior", "reach_widths"),
        ))
        self.assertIn("approach", {row[1] for row in trace})
        self.assertIn("pick_up", {row[1] for row in trace})
        for row in trace:
            self.assertGreaterEqual(row[4], track.left)
            self.assertLessEqual(row[4] + world.width, track.right)
        self.assertGreater(app.state.energy, 64)
        self.assertLess(app.state.energy, 66)

    def test_satiated_food_is_investigated_put_down_and_not_repeated(self):
        world = self.app._world
        item = world.world.place_resting(
            "onigiri", world._body_x() + 75, ObjectFootprint(16, 16)
        )
        trace = self.run_until(
            lambda: (
                any(known.assessed for known in world.awareness.memory.snapshot())
                and not world.interaction.active
            ),
            30,
        )
        phases = {row[1] for row in trace}
        self.assertTrue(
            {
                "notice",
                "approach",
                "pick_up",
                "inspect",
                "recognize",
                "decide",
                "put_down",
            }.issubset(phases),
            trace,
        )
        self.assertNotIn("eat", phases, trace)
        self.assertFalse(world.interaction.active, trace)
        self.assertEqual(world.world.get(item.instance_id).state, ObjectState.RESTING)
        known = world.awareness.known_instance(item.instance_id)
        assert known is not None
        self.assertTrue(known.assessed)
        expected = [
            "object_notice",
            "object_approach",
            "object_pick_up",
            "object_inspect",
            "object_recognized",
            "object_later",
            "object_put_down",
        ]
        self.assertEqual([event for _, event, _ in self.feedback], expected)
        for before, after in zip(self.feedback, self.feedback[1:]):
            self.assertGreater(after[0] - before[0], 1.6)
        self.assertTrue(any("Onigiri" in text for _, _, text in self.bubbles))
        self.assertTrue(any(phase == "put_down" and text
                            for _, phase, text in self.bubbles))
        trace = self.run_for(1.3)
        self.assertTrue(all(row[1] == "idle" for row in trace), trace)

    def test_sleep_during_held_inspection_puts_down_and_restart_keeps_portion(self):
        world = self.app._world
        item = world.world.place_resting(
            "onigiri", world._body_x(), ObjectFootprint(16, 16)
        )
        trace = self.run_until(lambda: world.interaction.phase == "inspect", 15)
        self.assertEqual(world.interaction.phase, "inspect", trace)
        self.app.interact("sleep")
        self.assertFalse(self.app.state.sleeping)
        trace = self.run_until(lambda: self.app.state.sleeping, 4)
        self.assertTrue(self.app.state.sleeping, trace)
        self.assertEqual(world.world.get(item.instance_id).state, ObjectState.RESTING)
        self.assertIsNone(self.app.state.food.last_food_id)
        store = self.app.store
        self.app.quit()
        restored = create_test_desktop(store=store)
        self.addCleanup(restored.quit)
        saved = restored._world.world.get(item.instance_id)
        self.assertEqual(saved.state, ObjectState.RESTING)
        self.assertIsNone(restored.state.food.last_food_id)

    def test_handover_is_staged_and_cursor_entry_preserves_full_drink_animation(self):
        world = self.app._world
        self.app.root.update_idletasks()
        eyes = self.app._animated.cursor_eye_position
        image = world.view.image("energy_drink", self.app.settings.scale)
        sprite = world.view.items.foods["energy_drink"].sprites[self.app.settings.scale]
        # Present the item's displayed center at the actual eyes, independent
        # of startup placement, desktop geometry and source sprite pivots.
        pointer = (int(eyes[0] + sprite.pivot[0] - image.width() / 2),
                   int(eyes[1] + sprite.pivot[1] - image.height() / 2))
        self.enterContext(
            patch.object(
                self.app.root,
                "winfo_pointerx",
                return_value=pointer[0],
            )
        )
        self.enterContext(
            patch.object(
                self.app.root,
                "winfo_pointery",
                return_value=pointer[1],
            )
        )
        self.enterContext(
            patch(
                "aiko_pet.desktop.cursor_item_gesture.mouse_buttons_down_windows",
                return_value=(True, False),
            )
        )
        world.begin_carry("energy_drink")
        token = world.cursor.instance_id
        assert token is not None
        self.run_until(lambda: world.cursor.offer_ready, 6)
        self.assertTrue(world.cursor.offer_ready)
        self.assertLess(self.app.state.energy, 61)
        world.cursor.release()
        self.assertEqual(world.interaction.phase, "handover")
        self.assertEqual(world.world.get(token).state, ObjectState.PET_HELD)
        self.assertLess(self.app.state.energy, 61)
        trace = self.run_until(lambda: world.interaction.phase == "eat", 12)
        self.assertEqual(world.interaction.phase, "eat", trace)
        started = world.now
        self.app.canvas.event_generate("<Enter>")
        trace += self.run_until(lambda: world.interaction.phase == "finish", 6)
        self.assertEqual(world.interaction.phase, "finish", trace)
        self.assertGreaterEqual(world.now - started, 3.4, trace)
        self.assertEqual(world.world.get(token).state, ObjectState.CONSUMED)
        self.assertGreater(self.app.state.energy, 69)
