"""Characterize object behavior through real Tk timers and desktop gates."""

import tempfile
import time
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import patch

from aiko_pet.application.settings import PetSettings
from aiko_pet.gui import DesktopPet
from aiko_pet.infrastructure.persistence import StateStore
from aiko_pet.pet.mind.object_perception import ObjectObservation
from aiko_pet.pet.state import PetState
from aiko_pet.world.contracts import ObjectFootprint, ObjectState
from tools.pet_test_support import set_test_pet_values


class WorldRuntimeFlowTests(unittest.TestCase):
    def setUp(self):
        try:
            root = tk.Tk()
            root.destroy()
        except tk.TclError as error:
            self.skipTest(str(error))
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
        self.app = DesktopPet(store=store)
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
        self.assertTrue(app._hover.pointer_inside(*pointer))
        direction = -1 if app._walk.movement.remaining_distance < 0 else 1
        candidate = world.world.place_resting(
            "onigiri", world._body_x() + direction * 1.5 * world.width,
            ObjectFootprint(8, 8),
        )
        friendship = app.state.friendship
        with (
            patch.object(app.root, "winfo_pointerx", return_value=pointer[0]),
            patch.object(app.root, "winfo_pointery", return_value=pointer[1]),
        ):
            trace = self.run_until(lambda: world.interaction.phase == "approach", 3)
            self.assertEqual(world.interaction.phase, "approach", trace)
            self.assertTrue(app._hover.interaction_active)
            self.assertIsNotNone(app._hover.toolbar)
            toolbar = app._hover.toolbar
            assert toolbar is not None
            self.assertTrue(all(button.cget("state") == "disabled"
                                for button in toolbar.buttons.values()))
            social = app.state.social
            toolbar.buttons["talk"].invoke()
            app._hover._interact("talk")
            app._hover._food_selected("energy_drink")
            self.assertEqual(app.state.social, social)
            self.assertFalse(world.cursor.carrying)
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

    def test_each_missing_portion_gets_a_readable_named_bubble_before_patrol(self):
        world = self.app._world
        set_test_pet_values(self.app.state, satiety=100, energy=100)
        for offset, identity in ((.3, "dango"), (.5, "energy_drink"),
                                 (.7, "onigiri")):
            x = world._body_x() + offset * world.width
            item = world.world.place_resting(identity, x, ObjectFootprint(8, 8))
            world.awareness.memory.observe_find(
                ObjectObservation(item.instance_id, identity,
                                  "drink" if identity == "energy_drink" else "food",
                                  x, 0, True, world.now),
                now=world.now, record=None, claimed=frozenset(), maximum_distance=0,
                instance_id=item.instance_id,
            )
            world.world.move_resting(item.instance_id,
                                     world.world.snapshot().surface.width * .95,
                                     expected_revision=item.revision)
        track = world._track()
        pointer = int(track.left + world._body_x() + world.width), track.ground_y
        for method, value in zip(("winfo_pointerx", "winfo_pointery"), pointer):
            self.enterContext(patch.object(self.app.root, method, return_value=value))
        cursor = self.app.mind.cursor_attention
        cursor.observe((-1, -1), time.monotonic())
        cursor.observe(pointer, time.monotonic())
        trace = self.run_until(lambda: world.interaction.search_ready, 25)
        self.assertTrue(world.interaction.search_ready, trace)
        missing = [(stamp, text) for stamp, event, text in self.feedback
                   if event == "object_place_missing"]
        self.assertEqual(len(missing), 3, self.feedback)
        # The presenter formats the actual visible bubble from each cue identity.
        visible = [text for _, _, text in self.bubbles]
        for name in ("Dango", "Energy", "Onigiri"):
            self.assertTrue(any(name in text for text in visible), visible)
        events = [event for _, event, _ in self.feedback]
        self.assertEqual(events, ["object_place_missing"] * 3 + ["object_search"])
        for before, after in zip(self.feedback, self.feedback[1:]):
            self.assertGreater(after[0] - before[0], 1.6)

    def test_same_type_replacement_waits_for_all_actual_missing_bubbles(self):
        app, world = self.app, self.app._world
        set_test_pet_values(app.state, satiety=100, energy=100)
        track = world._track()
        app._place_x(track.left + (track.right - track.left - world.width) / 2)
        body = world._body_x()
        records = set()
        for identity, old, new in (("dango", .3, 2.5),
                                   ("energy_drink", -.7, 3.3),
                                   ("onigiri", .9, -2.5)):
            x = body + old * world.width
            item = world.world.place_resting(identity, x, ObjectFootprint(8, 8))
            record = world.awareness.memory.observe_find(
                ObjectObservation("earlier", identity,
                                  "drink" if identity == "energy_drink" else "food",
                                  x, 0, True, world.now),
                now=world.now, record=None, claimed=frozenset(), maximum_distance=0,
                instance_id=item.instance_id,
            )
            records.add(record)
            world.awareness.memory.mark_assessed(record)
            world.world.move_resting(item.instance_id, body + new * world.width,
                                     expected_revision=item.revision)
        replacement = world.world.place_resting(
            "dango", body + .3 * world.width, ObjectFootprint(8, 8),
        )
        completed = set()
        approaches = []
        present = world._present_feedback

        def observe_feedback(cue, reaction, done):
            if cue.event in ("object_approach", "object_pick_up", "object_inspect"):
                self.assertEqual(completed, records)
                self.assertEqual(world.awareness.absences, ())
            if cue.event == "object_approach":
                self.assertIsNone(world.orientation_side())
                self.assertFalse(world.awareness.checking_absence)
                approaches.append(cue.record_id)

            def received(receipt):
                if cue.event == "object_place_missing" and receipt.completed:
                    completed.add(cue.record_id)
                done(receipt)

            present(cue, reaction, received)

        world._present_feedback = observe_feedback
        world._behavior.request_orientation()
        trace = self.run_until(lambda: world.interaction.phase == "inspect", 32)
        self.assertEqual(world.interaction.phase, "inspect", trace)
        self.assertEqual(world.interaction.instance_id, replacement.instance_id)
        self.assertEqual(len(approaches), 1)
        self.assertEqual(completed, records)
        self.assertEqual([event for _, event, _ in self.feedback], [
            "object_place_missing", "object_place_missing", "object_place_missing",
            "object_search", "object_approach", "object_pick_up", "object_inspect",
        ])
        for name in ("Dango", "Energy", "Onigiri"):
            self.assertTrue(any(name in text for _, _, text in self.bubbles),
                            self.bubbles)
        known = world.awareness.known_instance(replacement.instance_id)
        assert known is not None
        self.assertFalse(known.recognized)
        self.assertTrue(all(
            (missing := world.awareness.memory.get(record)) is not None
            and missing.place_status == "missing" for record in records
        ))

    def test_conversation_holds_environment_until_actual_sequence_completion(self):
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
        self.run_for(1)
        self.assertIsNotNone(self.app._reaction_player.pending_timer)
        self.assertEqual(world.awareness.memory.get(record), original)
        self.assertEqual(len(world.awareness.memory.snapshot()), 1)
        self.assertEqual(self.feedback, [])
        self.run_until(lambda: bool(self.feedback), 35)
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
        self.app = DesktopPet(store=store)
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
            if predicate() or time.monotonic() >= until:
                self.app.root.quit()
            else:
                self.app.root.after(25, sample)

        self.app.root.after(1, sample)
        self.app.root.mainloop()
        return trace

    def _edge_investigation(self, scale, side):
        app, world = self.app, self.app._world
        app.settings.scale = scale
        app._window.resize()
        app._animated.reload_sprites()
        set_test_pet_values(app.state, energy=65)
        track = world._track()
        boundary = track.left if side == "left" else track.right - world.width
        app._place_x(boundary + (60 * scale if side == "left" else -60 * scale))
        image = world.view.image("energy_drink", scale)
        footprint = ObjectFootprint(image.width() / 2, image.width() / 2)
        x = (
            footprint.left
            if side == "left"
            else world.world.snapshot().surface.width - footprint.right
        )
        item = world.world.place_resting("energy_drink", x, footprint)
        trace = self.run_until(
            lambda: (
                (known := world.awareness.known_instance(item.instance_id)) is not None
                and known.assessed
                and world.world.get(item.instance_id).state == ObjectState.RESTING
                and not world.interaction.active
                and world.orientation_side() is None
            ),
            30,
        )
        self.assertFalse(world.interaction.active, trace)
        self.assertTrue(
            {
                "approach",
                "pick_up",
                "inspect",
                "recognize",
                "decide",
                "put_down",
            }.issubset({row[1] for row in trace}),
            trace,
        )
        self.assertNotIn("eat", {row[1] for row in trace})
        current_x = app.settings.x
        assert current_x is not None
        self.assertAlmostEqual(current_x, boundary, delta=2)
        for row in trace:
            self.assertGreaterEqual(row[4], track.left)
            self.assertLessEqual(row[4] + world.width, track.right)
        placed = world.world.get(item.instance_id)
        assert placed.position is not None
        self.assertEqual(placed.position.x, world._body_x())
        self.assertNotEqual(placed.position.x, x)
        self.assertIsNone(world._visual.object_target)
        self.assertGreater(app.state.energy, 64)
        self.assertLess(app.state.energy, 66)

    def test_left_edge_investigation_at_scale_one_uses_actual_timers_and_motion(self):
        self._edge_investigation(1, "left")

    def test_right_edge_investigation_at_scale_two_uses_actual_timers_and_motion(self):
        self._edge_investigation(2, "right")

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
        restored = DesktopPet(store=store)
        self.addCleanup(restored.quit)
        saved = restored._world.world.get(item.instance_id)
        self.assertEqual(saved.state, ObjectState.RESTING)
        self.assertIsNone(restored.state.food.last_food_id)

    def test_handover_is_staged_and_cursor_entry_preserves_full_drink_animation(self):
        world = self.app._world
        self.enterContext(
            patch.object(
                self.app.root,
                "winfo_pointerx",
                return_value=(self.app.settings.x or 0) + 96,
            )
        )
        self.enterContext(
            patch.object(
                self.app.root,
                "winfo_pointery",
                return_value=world._track().ground_y - 80,
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
