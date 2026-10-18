"""Real Tk application joins food perception, movement and pickup effects."""

import tempfile
import time
import tkinter as tk
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from aiko_pet.application.object_feedback import FeedbackReceipt
from aiko_pet.desktop.geometry import FOOT_BASELINE
from aiko_pet.gui import DesktopPet
from aiko_pet.infrastructure.persistence import StateStore
from aiko_pet.pet.balance import BALANCE
from aiko_pet.pet.mind.object_perception import ObjectObservation
from aiko_pet.world.contracts import ObjectFootprint, ObjectState, WorldPosition
from tools.pet_test_support import set_test_pet_values


class WorldGuiTests(unittest.TestCase):
    def _search_multiple_relocated_portions(self, scale):
        self._resize_for_search_test(scale)
        app, runtime = self.app, self.app._world
        app._place_x(runtime._track().left)
        set_test_pet_values(app.state, satiety=100, energy=100)
        runtime._controls_active = lambda: True
        self.look_at(runtime._body_x() + 3 * runtime.width)
        area = runtime.world.snapshot().surface.width
        portions = []
        for kind, offset in (("dango", runtime.width),
                             ("dango", 1.1 * runtime.width),
                             ("energy_drink", 1.4 * runtime.width),
                             ("onigiri", 1.5 * runtime.width)):
            image = runtime.view.image(kind, scale)
            footprint = ObjectFootprint(image.width() / 2, image.width() / 2)
            x = (area - footprint.right if kind == "onigiri"
                 else runtime._body_x() + offset)
            portions.append(runtime.world.place_resting(kind, x, footprint))
        self.observe_and_acknowledge()
        for item in portions:
            kind = "drink" if item.definition_id == "energy_drink" else "food"
            observed = runtime.awareness.record_for_instance(item.instance_id)
            if item.definition_id == "onigiri" and observed is None:
                # Historical identified stock may lie beyond today's local
                # notice field. First hand/face acquisition is covered elsewhere.
                assert item.position is not None
                record = runtime.awareness.memory.observe_find(ObjectObservation(
                    "earlier_far_place", item.definition_id, kind,
                    item.position.x, 0, True, runtime.now,
                ), now=runtime.now, record=None, claimed=frozenset(),
                    maximum_distance=0, instance_id=item.instance_id)
            else:
                self.seed_previous_identification(
                    item.instance_id, item.definition_id, kind,
                )
                record = runtime.awareness.record_for_instance(item.instance_id)
                assert record is not None
            runtime.awareness.memory.mark_assessed(record)
        self.restart()
        app = self.app
        runtime = self.app._world
        self.look_at(runtime._body_x() + 3 * runtime.width)
        self.observe_and_acknowledge()
        self.assertEqual(runtime.interaction.phase, "idle")
        # Relocate as soon as actual approach starts, before hand inspection.
        runtime.world.place_resting("apple", runtime._body_x() + 1.8 * runtime.width,
                                    ObjectFootprint(8, 8))
        self.observe_and_acknowledge()
        self.assertEqual(runtime.interaction.phase, "approach")
        app._walk.step(time.monotonic(), .1, game_mode=False, attention_active=True)
        self.assertEqual(runtime._attention().mode, "object")
        remembered = {known.instance_id: known
                      for known in runtime.awareness.memory.snapshot()
                      if known.instance_id in {item.instance_id for item in portions}}
        area = runtime.world.snapshot().surface.width
        for item, fraction in zip(portions, (.55, .65, .8, .94), strict=True):
            current = runtime.world.get(item.instance_id)
            # Real gestures while walking toward another committed item must
            # not count as witnessed transport, even with old visible bindings.
            with (
                patch.object(self.app.root, "winfo_pointerx", return_value=int(
                    runtime._track().left + area * fraction,
                )),
                patch.object(self.app.root, "winfo_pointery",
                             return_value=runtime._track().ground_y),
            ):
                runtime.begin_relocate(item.instance_id, current.revision)
                self.assertFalse(runtime.awareness.following_cursor)
                runtime.cursor.release()
            runtime.world.advance_motion(1, runtime._motion_parameters)
            self.assertEqual(runtime.world.get(item.instance_id).state,
                             ObjectState.RESTING)
        # An unrelated new find is part of the same investigation flow. At 2x
        # one learned portion is really absent, so the pass must also finish.
        novel = runtime.world.place_resting(
            "cookie", area * .72, ObjectFootprint(8, 8),
        )
        expected = [item.instance_id for item in portions]
        if scale == 2:
            absent = runtime.world.get(expected.pop())
            runtime.world.remove(absent.instance_id, expected_revision=absent.revision)
        found, recognized, events, missing = [], [], [], []
        completed_losses = set()
        expected_losses = {known.token for known in remembered.values()}
        present = runtime._present_feedback

        def capture(cue, reaction, done):
            events.append(cue.event)
            if (runtime.interaction.search_active and cue.event in
                    ("object_approach", "object_pick_up", "object_inspect")):
                self.assertEqual(completed_losses, expected_losses)
                self.assertEqual(runtime.awareness.absences, ())
                if cue.event == "object_approach" and events.count(cue.event) == 1:
                    self.assertIsNone(runtime.orientation_side())
            if cue.event == "object_place_missing":
                lost = runtime.awareness.memory.get(cue.record_id)
                assert lost is not None
                self.assertEqual(lost.place_status, "missing")
                self.assertNotIn("object_notice", events)
                learned = [runtime.awareness.memory.get(item.token)
                           for item in remembered.values()]
                self.assertTrue(all(item is not None for item in learned))
                self.assertEqual({item.place_status for item in learned
                                  if item is not None}, {"missing"})
            known = runtime.awareness.memory.get(cue.record_id)
            if cue.event == "object_place_missing" and known is not None:
                missing.append((known.instance_id, cue.identity))
            if cue.event == "object_found" and known is not None:
                found.append(known.instance_id)
            if cue.event in ("object_recognized", "object_found") and known is not None:
                recognized.append(known.instance_id)

            def received(receipt):
                if cue.event == "object_place_missing" and receipt.completed:
                    completed_losses.add(cue.record_id)
                done(receipt)

            present(cue, reaction, received)

        runtime._present_feedback = capture
        for step in range(60):
            app._walk.step(time.monotonic() + step, .2,
                           game_mode=False, attention_active=True)
            runtime.now += .3
            runtime.update(time.monotonic())
            self.complete_feedback()
            self.assertEqual({known.instance_id: known
                              for known in runtime.awareness.memory.snapshot()
                              if known.instance_id in remembered}, remembered)
            if runtime.interaction.phase == "pick_up":
                break
        self.assertEqual(runtime.interaction.phase, "pick_up")
        self.finish_pickup()
        self.assertEqual(runtime.interaction.phase, "inspect")
        # Complete the action, then inspect old places on both sides. On wide
        # tracks the far place also lies beyond ordinary local noticing.
        self.assertEqual(runtime.awareness.absences, ())
        self.finish_inspection()
        self.finish_clip("put_down")
        self.complete_feedback()
        set_test_pet_values(self.app.state, satiety=30, energy=50)
        for step in range(300):
            runtime.now += .3
            runtime.update(time.monotonic())
            self.complete_feedback()
            phase = runtime.interaction.phase
            if runtime.interaction.search_active:
                self.assertTrue(all(item.state != ObjectState.CONSUMED
                                    for item in runtime.world.snapshot().objects))
            if phase == "pick_up":
                self.finish_pickup()
            elif phase == "inspect":
                self.finish_inspection()
            elif phase == "put_down":
                self.finish_clip("put_down")
            app = self.app
            app._walk.step(time.monotonic() + step, 1,
                           game_mode=False, attention_active=True)
            if len(found) == len(expected) and not runtime.interaction.search_active:
                break
        self.assertCountEqual(found, expected)
        self.assertCountEqual(missing, [(item.instance_id, item.definition_id)
                                        for item in portions])
        inspected = {*expected, novel.instance_id}
        self.assertCountEqual(
            [item for item in recognized if item in inspected], inspected,
        )
        self.assertEqual(events.count("object_search"), 1)
        self.assertEqual(events.count("object_missing"), int(scale == 2))
        self.assertNotIn("object_want", events)
        self.assertNotIn("object_notice", events)
        self.assertFalse(runtime.interaction.search_active)
        self.assertTrue(all(runtime.world.get(item).state == ObjectState.RESTING
                            for item in expected))

    def test_restart_shared_search_of_relocated_close_portions_at_scale_one(self):
        self._search_multiple_relocated_portions(1)

    def test_restart_shared_search_of_relocated_close_portions_at_scale_two(self):
        self._search_multiple_relocated_portions(2)

    def _care_focus_defers_environment_until_complete(self, action):
        app, runtime = self.app, self.app._world
        app._place_x(runtime._track().left + runtime.width)
        set_test_pet_values(app.state, satiety=100, energy=100)
        runtime._controls_active = lambda: True
        self.look_at(runtime._body_x() + runtime.width)
        known_item = runtime.world.place_resting(
            "cookie", runtime._body_x() + .2 * runtime.width, ObjectFootprint(8, 8),
        )
        self.observe_and_acknowledge()
        self.seed_previous_identification(known_item.instance_id, "cookie", "food")
        record = runtime.awareness.record_for_instance(known_item.instance_id)
        assert record is not None
        runtime.awareness.memory.mark_assessed(record)
        original = runtime.awareness.memory.get(record)
        runtime._controls_active = lambda: (
            app._hover.interaction_active or app._reaction_player.story_active
        )
        app.interact(action)
        self.assertEqual(runtime._attention().mode, "unavailable")
        current = runtime.world.get(known_item.instance_id)
        with (
            patch.object(app.root, "winfo_pointerx", return_value=int(
                runtime._track().left + runtime._body_x() + 3 * runtime.width,
            )),
            patch.object(app.root, "winfo_pointery",
                         return_value=runtime._track().ground_y),
        ):
            runtime.begin_relocate(known_item.instance_id, current.revision)
            self.assertFalse(runtime.awareness.following_cursor)
            runtime.cursor.release()
        runtime.world.advance_motion(1, runtime._motion_parameters)
        runtime.world.place_resting(
            "onigiri", max(8, runtime._body_x() - .7 * runtime.width),
            ObjectFootprint(8, 8),
        )
        events = []
        present = runtime._present_feedback

        def capture(cue, reaction, done):
            events.append(cue.event)
            present(cue, reaction, done)

        runtime._present_feedback = capture
        for _ in range(4):
            runtime.now += .3
            runtime.update(time.monotonic())
            self.assertEqual(runtime.awareness.memory.get(record), original)
            self.assertEqual(len(runtime.awareness.memory.snapshot()), 1)
            self.assertEqual(runtime.awareness.absences, ())
        # An animation ending alone cannot release an unfinished conversation.
        app._action_playback.cancel_at(time.monotonic())
        self.assertIsNotNone(app._reaction_player.pending_timer)
        self.assertEqual(runtime._attention().mode, "unavailable")
        self.assertEqual(events, [])
        self.complete_feedback()
        for _ in range(3):
            runtime.now += .3
            runtime.update(time.monotonic())
        self.finish_orientation()
        self.assertTrue(events)
        self.assertEqual(events[0], "object_place_missing")
        self.assertNotIn("object_notice", events)

    def test_petting_focus_defers_environment_until_complete(self):
        self._care_focus_defers_environment_until_complete("pet")

    def test_conversation_focus_defers_environment_until_complete(self):
        self._care_focus_defers_environment_until_complete("talk")

    def _search_face_reunion(self, during_approach):
        self._resize_for_search_test(2)
        app, runtime = self.app, self.app._world
        app._place_x(runtime._track().left)
        set_test_pet_values(app.state, satiety=100, energy=100)
        runtime._controls_active = lambda: True
        drink = runtime.world.place_resting("energy_drink", runtime._body_x(),
                                            ObjectFootprint(8, 8))
        self.observe_and_acknowledge()
        self.seed_previous_identification(drink.instance_id, "energy_drink", "drink")
        record = runtime.awareness.record_for_instance(drink.instance_id)
        assert record is not None
        runtime.awareness.memory.mark_assessed(record)
        current = runtime.world.get(drink.instance_id)
        runtime.world.move_resting(drink.instance_id,
                                   runtime.world.snapshot().surface.width * .9,
                                   expected_revision=current.revision)
        runtime._controls_active = lambda: False
        for _ in range(4):
            runtime.now += .3
            runtime.update(time.monotonic())
        self.finish_orientation()
        self.assertEqual(runtime.interaction.phase, "notice_absence")
        self.complete_feedback()
        self.assertEqual(runtime.interaction.phase, "search")
        if during_approach:
            # The relocated item is outside the current field. Follow the real
            # search route until it becomes a visible investigation candidate.
            for step in range(30):
                self.complete_feedback()
                self.app._walk.step(time.monotonic() + step, .2,
                                    game_mode=False, attention_active=True)
                runtime.now += .3
                runtime.update(time.monotonic())
                if runtime.interaction.phase == "approach":
                    break
            self.assertEqual(runtime.interaction.phase, "approach")
        cues = []
        present = runtime._present_feedback

        def capture(cue, reaction, done):
            cues.append(cue.event)
            present(cue, reaction, done)

        runtime._present_feedback = capture
        current = runtime.world.get(drink.instance_id)
        eyes_x, eyes_y = runtime._animated.cursor_eye_position
        with (
            patch.object(app.root, "winfo_pointerx",
                         return_value=int(eyes_x)),
            patch.object(app.root, "winfo_pointery",
                         return_value=int(eyes_y)),
        ):
            runtime.begin_relocate(drink.instance_id, current.revision)
            self.assertTrue(runtime.interaction.search_active)
            for _ in range(8):
                runtime.now += .3
                runtime.update(time.monotonic())
                self.complete_feedback()
        self.assertEqual(cues.count("object_found"), 1)
        self.assertNotIn("object_pick_up", cues)
        self.assertNotIn("object_want", cues)
        self.assertFalse(runtime.interaction.search_active)
        self.assertEqual(runtime.world.get(drink.instance_id).state,
                         ObjectState.USER_HELD)

    def test_search_accepts_face_reunion_without_pickup(self):
        self._search_face_reunion(False)

    def test_search_candidate_taken_during_approach_is_reunited_at_the_face(self):
        self._search_face_reunion(True)

    def _fast_observed_cursor_relocation(self, scale):
        self._resize_for_search_test(scale)
        app, runtime = self.app, self.app._world
        app._place_x(runtime._track().left)
        set_test_pet_values(app.state, satiety=100, energy=100)
        runtime._controls_active = lambda: True
        item = runtime.world.place_resting(
            "dango", runtime._body_x() + 2 * runtime.width, ObjectFootprint(8, 8),
        )
        assert item.position is not None
        self.look_at(item.position.x)
        self.observe_and_acknowledge()
        self.seed_previous_identification(item.instance_id, "dango", "food")
        record = runtime.awareness.record_for_instance(item.instance_id)
        assert record is not None
        runtime.awareness.memory.mark_assessed(record)
        runtime._controls_active = lambda: False
        self.look_at(runtime._body_x() - runtime.width)
        for _ in range(2):
            runtime.now += .3
            runtime.update(time.monotonic())
        self.assertIsNone(runtime.awareness.record_for_instance(item.instance_id))
        self.assertIsNotNone(runtime.awareness.memory.get(record))
        cues = []
        present = runtime._present_feedback

        def capture(cue, reaction, done):
            cues.append(cue.event)
            present(cue, reaction, done)

        runtime._present_feedback = capture
        for offset in (1, 2, 1):
            current = runtime.world.get(item.instance_id)
            with (
                patch.object(app.root, "winfo_pointerx", return_value=int(
                    runtime._track().left + runtime._body_x() + offset * runtime.width,
                )),
                patch.object(app.root, "winfo_pointery",
                             return_value=runtime._track().ground_y),
            ):
                runtime.begin_relocate(item.instance_id, current.revision)
                self.assertEqual(runtime.awareness._tracker.following_instance,
                                 item.instance_id)
                # A real click/drop can occur between two perception ticks.
                # In particular there is no intermediate USER_HELD observation.
                runtime.cursor.release()
            self.look_at(runtime._body_x() + offset * runtime.width)
            runtime.world.advance_motion(1, runtime._motion_parameters)
            for _ in range(8):
                runtime.now += .2
                runtime.update(time.monotonic())
                self.complete_feedback()
            known = runtime.awareness.known_instance(item.instance_id)
            assert known is not None
            self.assertEqual((known.token, known.identity), (record, "dango"))
            self.assertEqual(known.place_status, "remembered")
            self.assertEqual(runtime.interaction.phase, "idle")
            self.assertEqual(len(runtime.awareness.memory.snapshot()), 1)
            placed = runtime.world.get(item.instance_id)
            assert placed.position is not None
            self.assertEqual((known.x, known.height),
                             (placed.position.x, placed.position.height))
        self.assertEqual(cues, [])

        # A longer held gesture includes this known item's own refusal cue.
        eyes_x, eyes_y = app._animated.cursor_eye_position
        current = runtime.world.get(item.instance_id)
        assert current.position is not None
        pointer = [int(runtime._track().left + current.position.x),
                   int(runtime._track().ground_y - current.position.height)]
        with (
            patch.object(app.root, "winfo_pointerx", side_effect=lambda: pointer[0]),
            patch.object(app.root, "winfo_pointery", side_effect=lambda: pointer[1]),
        ):
            runtime.begin_relocate(item.instance_id, current.revision)
            self.assertTrue(runtime.awareness.following_cursor)
            pointer[:] = [int(eyes_x), int(eyes_y)]
            for _ in range(10):
                runtime.now += .2
                runtime.cursor._move_carry()
                runtime.update(time.monotonic())
            self.assertEqual(cues, ["object_refuse"])
            self.assertEqual(app._reaction_player.subject, record)
            self.assertTrue(runtime.awareness.following_cursor)
            self.assertEqual(runtime._attention().mode, "object")
            pointer[:] = [int(runtime._track().left + runtime._body_x()
                             + 2 * runtime.width),
                          int(runtime._track().ground_y - runtime.width)]
            runtime.cursor.release()
            for _ in range(80):
                runtime.world.advance_motion(.1, runtime._motion_parameters)
                runtime.now += .1
                runtime.update(time.monotonic())
                if runtime.world.get(item.instance_id).state == ObjectState.RESTING:
                    break
            self.assertEqual(runtime.world.get(item.instance_id).state,
                             ObjectState.RESTING)
            self.complete_feedback()
            for _ in range(3):
                runtime.now += .2
                runtime.update(time.monotonic())
        known = runtime.awareness.memory.get(record)
        assert known is not None
        self.assertTrue(known.recognized and known.resting)
        self.assertEqual(len(runtime.awareness.memory.snapshot()), 1)
        self.assertEqual(cues, ["object_refuse"])

    def test_fast_observed_cursor_relocation_at_scale_one(self):
        self._fast_observed_cursor_relocation(1)

    def test_fast_observed_cursor_relocation_at_scale_two(self):
        self._fast_observed_cursor_relocation(2)

    def _learn_and_restart_close_pair(self, scale, kinds):
        self._resize_for_search_test(scale)
        runtime = self.app._world
        self.app._place_x(runtime._track().left + runtime.width)
        set_test_pet_values(self.app.state, satiety=100)
        set_test_pet_values(self.app.state, energy=100)
        portions = [runtime.world.place_resting(kind, runtime._body_x() + offset,
                                                ObjectFootprint(8, 8))
                    for kind, offset in zip(kinds, (0, runtime.width * .1),
                                            strict=True)]
        cues = []
        present = runtime._present_feedback

        def capture(cue, reaction, done):
            cues.append((cue.event, runtime.interaction.instance_id,
                         runtime.interaction.phase))
            present(cue, reaction, done)

        runtime._present_feedback = capture
        for step in range(100):
            runtime.now += .3
            runtime.update(time.monotonic())
            self.complete_feedback()
            phase = runtime.interaction.phase
            if phase == "pick_up":
                self.finish_pickup()
            elif phase == "inspect":
                self.finish_inspection()
            elif phase == "put_down":
                self.finish_clip("put_down")
            self.app._walk.step(time.monotonic() + step, 1,
                                game_mode=False, attention_active=True)
        expected_instances = {item.instance_id for item in portions}
        recognized = [instance for event, instance, _ in cues
                      if event == "object_recognized"]
        self.assertCountEqual(recognized, expected_instances)
        self.assertTrue(all(phase == "recognize" for event, _, phase in cues
                            if event == "object_recognized"))
        self.assertEqual(runtime.interaction.phase, "idle")
        learned = runtime.awareness.memory.export(now=runtime.now)
        self.assertEqual(len(learned.entries), 2)
        self.assertEqual({entry.instance_id for entry in learned.entries},
                         expected_instances)
        self.assertTrue(all(entry.assessed for entry in learned.entries))
        records = {entry.instance_id: entry.token for entry in learned.entries}
        for _ in range(2):
            self.restart()
            runtime = self.app._world
            self.assertEqual(runtime.awareness.observations, ())
            # The saved reference does not grant instant visibility on startup.
            self.assertTrue(all(runtime.awareness.record_for_instance(instance) is None
                                for instance in expected_instances))
            for step in range(60):
                runtime.now += .3
                runtime.update(time.monotonic())
                self.complete_feedback()
                self.assertEqual(runtime.interaction.phase, "idle")
                self.assertEqual(len(runtime.awareness.memory.snapshot()), 2)
            for instance, record in records.items():
                assert instance is not None
                self.assertEqual(runtime.awareness.record_for_instance(instance),
                                 record)
            current = runtime.awareness.memory.export(now=runtime.now)
            self.assertEqual(current.next_record_id, learned.next_record_id)

    def test_close_known_pair_cold_restart_at_scale_one(self):
        self._learn_and_restart_close_pair(1, ("energy_drink", "dango"))

    def test_close_known_pair_cold_restart_at_scale_two(self):
        self._learn_and_restart_close_pair(2, ("energy_drink", "dango"))

    def test_close_same_type_pair_cold_restart_keeps_distinct_portions(self):
        self._learn_and_restart_close_pair(2, ("dango", "dango"))

    def test_coincident_learned_portions_remain_visible_after_restart(self):
        runtime = self.app._world
        set_test_pet_values(self.app.state, satiety=100)
        set_test_pet_values(self.app.state, energy=100)
        records = {}
        for _ in range(2):
            item = runtime.world.place_resting("dango", runtime._body_x(),
                                               ObjectFootprint(8, 8))
            # Fixture of earlier permitted identification and own placement;
            # the nearby-pair cases above exercise those actual clips.
            record = runtime.awareness.memory.observe_find(ObjectObservation(
                "identified", "dango", "food", runtime._body_x(), 0, True, 0,
            ), now=0, record=None, claimed=frozenset(), maximum_distance=0,
                instance_id=item.instance_id)
            runtime.awareness.memory.mark_assessed(record)
            records[item.instance_id] = record
        self.restart()
        runtime = self.app._world
        for _ in range(40):
            runtime.now += .3
            runtime.update(time.monotonic())
            self.assertEqual(runtime.interaction.phase, "idle")
        self.assertEqual(len(runtime.awareness.observations), 2)
        self.assertEqual(len(runtime.awareness.memory.snapshot()), 2)
        for instance, record in records.items():
            self.assertEqual(runtime.awareness.record_for_instance(instance), record)

    def _resize_for_search_test(self, scale):
        self.app.settings.scale = scale
        self.app._window.resize()
        self.app._animated.reload_sprites()
        self.app._world._sync_geometry()

    def _relocated_unknown_pair_after_inspection(self, scale):
        self._resize_for_search_test(scale)
        runtime = self.app._world
        track = runtime._track()
        self.app._place_x(track.left)
        base, width = runtime._body_x(), runtime.width
        portions = [runtime.world.place_resting(kind, base + offset * width,
                                                ObjectFootprint(8, 8))
                    for kind, offset in (("apple", 0), ("cookie", 1),
                                         ("energy_drink", 1.2))]
        self.observe_and_acknowledge()
        self.finish_pickup()
        self.assertEqual(runtime.interaction.phase, "inspect")
        for step in range(8):
            for index, portion in enumerate(portions[1:]):
                current = runtime.world.get(portion.instance_id)
                offset = 1.2 if (index + step) % 2 else 1
                runtime.world.move_resting(current.instance_id, base + offset * width,
                                           expected_revision=current.revision)
            runtime.now += .2
            runtime.update(time.monotonic())
        self.finish_inspection()
        self.finish_clip("eat")
        self.complete_feedback()
        self.look_at(base + width)
        for _ in range(24):
            runtime.now += .2
            runtime.update(time.monotonic())
            self.complete_feedback()
            goal = runtime._walk.movement.goal_x
            if goal is not None:
                self.app._place_x(goal)
            if runtime.interaction.phase == "pick_up":
                break
        self.assertEqual(runtime.interaction.phase, "pick_up")
        record = runtime.interaction.memory_id
        assert record is not None
        self.assertIn(runtime.awareness.instance_for_record(record),
                      {item.instance_id for item in portions[1:]})

    def test_relocated_unknown_pair_after_inspection_at_scale_one(self):
        self._relocated_unknown_pair_after_inspection(1)

    def test_relocated_unknown_pair_after_inspection_at_scale_two(self):
        self._relocated_unknown_pair_after_inspection(2)

    def test_taken_unknown_drink_is_recognized_then_accepted_or_refused_at_cursor(self):
        app, world = self.app, self.app._world
        cues = []
        present = world._present_feedback

        def capture(cue, reaction, done):
            cues.append(cue)
            present(cue, reaction, done)

        world._present_feedback = capture
        for scale, energy in ((1, 65), (2, 100)):
            with self.subTest(scale=scale, energy=energy):
                cues.clear()
                app.settings.scale = scale
                app._window.resize()
                app._animated.reload_sprites()
                world._sync_geometry()
                app._place_x(world._track().left + 40)
                set_test_pet_values(app.state, energy=energy)
                start = world.now
                item = world.world.place_resting(
                    "energy_drink", world._body_x() + 200 * scale,
                    ObjectFootprint(8, 8),
                )
                self.look_at(world._body_x() + 200 * scale)
                for offset in (0, .3):
                    world.now = start + offset
                    world.update(time.monotonic())
                self.complete_feedback()
                self.assertEqual(world.interaction.phase, "approach")
                record = world.interaction.memory_id
                episode = world.interaction.feedback_key.interaction_id
                known = world.awareness.known_instance(item.instance_id)
                assert known is not None
                self.assertIsNone(known.identity)
                with (
                    patch.object(app.root, "winfo_pointerx",
                                 return_value=(int(world._body_x())
                                               + world._track().left)),
                    patch.object(app.root, "winfo_pointery", return_value=(
                        world._track().ground_y - 80 * scale
                    )),
                ):
                    world.begin_relocate(item.instance_id, item.revision)
                    set_test_pet_values(app.state, energy=energy)
                    self.assertEqual(world.interaction.phase, "await_return")
                    for offset in (.3, .6, .9, 1.2, 1.4):
                        world.now = start + offset
                        world.update(time.monotonic())
                    self.complete_feedback()
                    self.assertEqual(world.interaction.phase, "recognize_offer")
                    self.assertEqual(cues[-1].event, "object_recognized")
                    self.assertEqual(cues[-1].identity, "energy_drink")
                    self.assertEqual(world.interaction.memory_id, record)
                    self.assertEqual(world.interaction.feedback_key.interaction_id,
                                     episode)
                    self.assertEqual(world.world.get(item.instance_id).state,
                                     ObjectState.USER_HELD)
                    self.complete_feedback()
                    self.assertEqual(world.interaction.phase, "decide_offer")
                    expected = "object_offer" if energy < 100 else "object_refuse"
                    self.assertEqual(cues[-1].event, expected)
                    self.complete_feedback()
                    if energy < 100:
                        self.assertEqual(world.interaction.phase, "await_return")
                        world.cursor.release()
                        self.assertEqual(world.interaction.phase, "handover")
                        self.complete_feedback()
                        self.finish_clip("eat")
                        self.complete_feedback()
                    else:
                        self.assertFalse(world.interaction.active)
                        friendship = app.state.friendship
                        for _ in range(100):
                            set_test_pet_values(app.state, energy=100)
                            world.now += .25
                            world.update(time.monotonic())
                            self.complete_feedback()
                        self.assertEqual(app.state.friendship, friendship)
                        self.assertNotIn("object_request_return",
                                         [cue.event for cue in cues])
                        self.assertNotIn("object_withheld", [cue.event for cue in cues])
                        world.cursor.cancel()

    def test_restart_during_a_held_wish_restores_facts_without_live_cursor_state(self):
        app, world = self.app, self.app._world
        with (
            patch.object(app.root, "winfo_pointerx",
                         return_value=int(world._body_x()) + world._track().left),
            patch.object(app.root, "winfo_pointery",
                         return_value=world._track().ground_y - 80),
        ):
            world.begin_carry("cookie")
            self.observe_and_acknowledge()
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
        self.observe_and_acknowledge()
        self.seed_previous_identification(item.instance_id, "cookie", "food")
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
        self.finish_orientation()
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
        self.observe_and_acknowledge()
        self.seed_previous_identification(item.instance_id, "cookie", "food")
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
            self.assertFalse(world.cursor.offer_ready)
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
                set_test_pet_values(app.state, satiety=76, energy=65)
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
                    self.observe_and_acknowledge()
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
            set_test_pet_values(self.app.state, energy=40)
            world.begin_carry("energy_drink")
            for stamp in (0, .3, .7, 1.1):
                world.now = stamp
                world.update(time.monotonic())
            old, stale = callbacks[-1]
            set_test_pet_values(self.app.state, energy=100)
            world.update(time.monotonic())
            stale(FeedbackReceipt(old.key, True))
            self.assertFalse(world.cursor.offer_ready)
            set_test_pet_values(self.app.state, energy=40)
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
        self.settle_native_positions()
        world = self.app._world
        assert world._timer is not None
        self.app.root.after_cancel(world._timer)
        world._timer = None
        self.app.settings.auto_routine = False
        self.app.settings.observe_computer = False
        self.app.settings.auto_walk = False
        set_test_pet_values(self.app.state, sleeping=False)
        set_test_pet_values(self.app.state, satiety=50)
        self.app._action_playback.cancel_at(time.monotonic())
        world._controls_active = lambda: False

    def settle_native_positions(self):
        # Manual ticks must let Tk apply a requested move before reading eyes.
        place = self.app._window.place_x

        def settled_place(x):
            changed = place(x)
            self.app.root.update_idletasks()
            return changed

        self.enterContext(patch.object(self.app._window, "place_x",
                                      side_effect=settled_place))
        self.app.root.update_idletasks()

    def look_at(self, x, height=0):
        """Move the test cursor into the scene; keep the real attention policy."""
        track = self.app._world._track()
        pointer = int(track.left + x), int(track.ground_y - height)
        self.enterContext(patch.object(self.app.root, "winfo_pointerx",
                                      return_value=pointer[0]))
        self.enterContext(patch.object(self.app.root, "winfo_pointery",
                                      return_value=pointer[1]))
        cursor = self.app.mind.cursor_attention
        cursor.observe((-1, -1), time.monotonic())
        cursor.observe(pointer, time.monotonic())

    def finish_orientation(self):
        """Drive the public gaze/sensor sequence; leave cue receipts untouched."""
        world = self.app._world
        for _ in range(20):
            world.now += .2
            world.update(time.monotonic())
            if world.orientation_side() is None:
                return
        self.fail("Remembered-place orientation did not finish")

    def observe_and_acknowledge(self):
        start = self.app._world.now
        # Include both .5-second learned-place looks before ordinary dispatch.
        for offset in (0, .3, .6, .9, 1.2, 1.5, 1.8):
            self.app._world.now = start + offset
            self.app._world.update(time.monotonic())
        self.finish_orientation()
        if self.app._world.cursor.carrying:
            # A free unknown offer begins its one-second presentation only
            # after learned-place orientation has released attention.
            for _ in range(4):
                self.app._world.now += .3
                self.app._world.update(time.monotonic())
        self.complete_feedback()
        self.complete_feedback()

    def restart(self):
        store = self.app.store
        self.app.quit()
        self.app = DesktopPet(store=store)
        self.addCleanup(self.app.quit)
        self.app._runtime.stop()
        self.settle_native_positions()
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
        self.finish_orientation()
        self.assertIsNone(world._visual.object_target)
        self.assertFalse(self.app.settings.auto_walk)
        cues = []
        present = world._present_feedback

        def capture(cue, reaction, done):
            cues.append(cue)
            present(cue, reaction, done)

        world._present_feedback = capture
        set_test_pet_values(self.app.state, energy=55)
        world.now += 1.1
        world.update(time.monotonic())
        self.finish_orientation()
        self.assertEqual(cues[0].event, "object_recall_saved_drink")
        self.complete_feedback()
        # Orientation has supplied fresh exact-place evidence; the actual
        # reachable portion may now be grasped without another identification.
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
        # The current target really exists. An empty remembered place now has
        # separate early-loss coverage rather than masquerading as an approach.
        target = world.world.place_resting("apple", world._body_x() + 300,
                                           ObjectFootprint(8, 8))
        old = world.awareness.memory.observe_find(ObjectObservation(
            "old_sighting", "apple", "food", world._body_x() + 300, 0, True, 0,
        ), now=0, record=None, claimed=frozenset(), maximum_distance=10,
            instance_id=target.instance_id)
        world.awareness.memory.mark_assessed(old)
        world.update(time.monotonic())
        self.finish_orientation()
        self.complete_feedback()
        self.assertEqual(world.interaction.memory_id, old)
        item = world.world.place_resting("apple", world._body_x() + 70,
                                         ObjectFootprint(8, 8))
        # A committed walk keeps its own item focus; even a nearby alternative
        # must remain unnoticed until this interaction ends.
        self.app._walk.step(time.monotonic(), .01,
                            game_mode=False, attention_active=False)
        self.assertGreater(self.app._walk.movement.remaining_distance, 0)
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
        self.observe_and_acknowledge()
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
                set_test_pet_values(self.app.state, satiety=50)
                item = world.world.place_resting(
                    "apple", world._body_x() + 70 * scale, ObjectFootprint(8, 8),
                )
                self.observe_and_acknowledge()
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
                self.assertEqual(world.interaction.phase, "await_return")
                known = world.awareness.memory.get(record)
                assert known is not None
                self.assertIsNone(known.identity)
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
        self.observe_and_acknowledge()
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

    def test_absent_remembered_instance_requires_deliberate_place_check(self):
        world = self.app._world
        set_test_pet_values(self.app.state, energy=65)
        item = world.world.place_resting("energy_drink", world._body_x(),
                                         ObjectFootprint(12, 12))
        self.observe_and_acknowledge()
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
        set_test_pet_values(self.app.state, energy=55)
        world.update(time.monotonic())
        self.complete_feedback()
        self.assertEqual(world.interaction.phase, "idle")
        self.assertIsNotNone(world.awareness.memory.get(record))
        world.now += 1
        world.update(time.monotonic())
        self.assertIsNotNone(world.awareness.memory.get(record))
        self.finish_orientation()
        self.assertEqual(world.interaction.phase, "notice_absence")
        self.complete_feedback()
        self.assertEqual(world.interaction.phase, "search")
        self.complete_feedback()
        world.now += 1.1
        world.update(time.monotonic())
        self.assertEqual(world.interaction.phase, "search")
        self.assertIsNotNone(world._visual.object_target)
        world.now += 1
        world.update(time.monotonic())
        self.assertEqual(world.interaction.phase, "search")
        self.complete_search_route()
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

    def test_unknown_absence_finishes_without_search_before_new_discovery(self):
        world = self.app._world
        world.awareness.memory.update((ObjectObservation(
            "earlier", None, None, world._body_x() - 80, 0, True, 0,
        ),), now=0)
        world.world.place_resting("cookie", world._body_x() + 80,
                                  ObjectFootprint(8, 8))
        cues = []
        present = world._present_feedback

        def capture(cue, reaction, done):
            cues.append(cue)
            present(cue, reaction, done)

        world._present_feedback = capture
        for now in (0, .3):
            world.now = now
            world.update(time.monotonic())
            self.assertFalse(world.interaction.active)
        world.now = .5
        world.update(time.monotonic())
        self.assertEqual(world.interaction.phase, "notice_absence")
        self.assertEqual(cues[0].event, "object_place_missing")
        self.assertIsNone(cues[0].identity)
        self.complete_feedback()
        self.assertIsNone(world.awareness.memory.get("earlier"))
        self.assertEqual(cues[1].event, "object_notice")
        for _ in range(5):
            world.now += .25
            world.update(time.monotonic())
        self.assertEqual([cue.event for cue in cues].count("object_place_missing"), 1)
        self.assertEqual([cue.event for cue in cues].count("object_search"), 0)

    def test_missing_unwanted_reserve_starts_one_bounded_search(self):
        world = self.app._world
        set_test_pet_values(self.app.state, energy=100)
        world.awareness.memory.update((ObjectObservation(
            "reserve", "energy_drink", "drink", world._body_x(), 0, True, 0,
        ),), now=0)
        world.awareness.memory.mark_assessed("reserve")
        cues = []
        present = world._present_feedback

        def capture(cue, reaction, done):
            cues.append(cue)
            present(cue, reaction, done)

        world._present_feedback = capture
        for now in (0, .3, .5):
            world.now = now
            world.update(time.monotonic())
        self.finish_orientation()
        self.assertEqual(cues[0].identity, "energy_drink")
        self.complete_feedback()
        self.assertEqual(world.interaction.phase, "search")
        self.assertEqual(cues[1].event, "object_search")
        self.complete_feedback()
        world.now += 2.1
        world.update(time.monotonic())
        self.assertEqual(world.interaction.phase, "search")
        self.complete_search_route()
        self.assertEqual(world.interaction.phase, "missing")
        self.complete_feedback()
        self.assertFalse(world.interaction.active)
        for _ in range(6):
            world.now += 1
            world.update(time.monotonic())
        self.assertEqual([cue.event for cue in cues].count("object_place_missing"), 1)
        self.assertEqual([cue.event for cue in cues].count("object_search"), 1)

    def complete_search_route(self):
        # Component gate uses real native positions; runtime movement is covered
        # separately rather than treating elapsed time as travelled distance.
        world = self.app._world
        for _ in range(2):
            target = world._walk.movement.goal_x
            assert target is not None
            self.app._place_x(target)
            world.now += .1
            world.update(time.monotonic())

    def complete_feedback(self):
        # Component assertions skip cue dwell; runtime-flow tests use real timers.
        player = self.app._reaction_player
        if player.pending_timer is not None:
            self.app.root.after_cancel(player.pending_timer)
            player._complete(player.generation)
        self.app._world.update(time.monotonic())

    def finish_inspection(self):
        # Sample continuous hand inspection, rather than skipping sensory ticks.
        for _ in range(4):
            self.app._world.now += .3
            self.app._world.update(time.monotonic())
        for _ in range(4):
            if self.app._world.interaction.phase not in (
                "inspect", "recognize", "decide",
            ):
                break
            self.complete_feedback()

    def seed_previous_identification(self, instance, identity, kind):
        """Known-history fixture; first identification has its own coverage."""
        awareness = self.app._world.awareness
        record = awareness.record_for_instance(instance)
        seen = next(seen for seen in awareness.observations if seen.token == record)
        awareness.memory.observe_find(
            replace(seen, identity=identity, kind=kind), now=self.app._world.now,
            record=record, claimed=frozenset(), maximum_distance=0,
            preserve_record=True, instance_id=instance,
        )

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
        self.observe_and_acknowledge()
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
        set_test_pet_values(self.app.state, energy=65)
        world.world.place_resting("energy_drink", world._body_x(),
                                  ObjectFootprint(12, 12))
        self.observe_and_acknowledge()
        self.finish_pickup()
        self.finish_inspection()
        self.assertEqual(world.interaction.phase, "put_down")
        self.finish_clip("put_down")
        self.assertFalse(world.interaction.active)
        world.now += 1
        world.update(time.monotonic())
        self.finish_orientation()
        known, = world.awareness.memory.snapshot()
        self.assertEqual(known.identity, "energy_drink")
        self.assertTrue(known.assessed)
        self.assertIsNone(world.awareness.intentions.goal)
        self.assertIsNone(world._visual.object_target)
        eyes_x, eyes_y = self.app._window.gaze_origin()
        self.assertEqual(world._visual.gaze_direction(
            (round(eyes_x + 200), round(eyes_y)),
        ), 4)
        set_test_pet_values(self.app.state, energy=55)
        world.now += 11
        world.update(time.monotonic())
        goal = world.awareness.intentions.goal
        assert goal is not None
        self.assertEqual((goal.token, goal.purpose), (known.token, "consume"))

    def test_new_drink_inquiry_bypasses_pause_after_consuming_known_food(self):
        world = self.app._world
        food = world.world.place_resting("onigiri", world._body_x(),
                                         ObjectFootprint(16, 16))
        self.observe_and_acknowledge()
        self.finish_pickup()
        self.finish_inspection()
        self.assertEqual(world.world.get(food.instance_id).state, ObjectState.CONSUMED)
        self.finish_clip("eat")
        self.complete_feedback()
        self.assertFalse(world.interaction.active)
        consumed_at = world.now
        set_test_pet_values(self.app.state, energy=66)
        cues = []
        present = world._present_feedback

        def capture(cue, reaction, done):
            cues.append(cue.event)
            present(cue, reaction, done)

        world._present_feedback = capture
        drink = world.world.place_resting("energy_drink", world._body_x(),
                                          ObjectFootprint(12, 12))
        self.observe_and_acknowledge()
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

    def test_recognized_drink_handover_then_unknown_full_drink_is_examined(self):
        app, world = self.app, self.app._world
        set_test_pet_values(app.state, energy=40)
        x = (app.settings.x or 0) + 96
        y = world._track().ground_y - 80
        with patch.object(app.root, "winfo_pointerx", return_value=x), patch.object(
            app.root, "winfo_pointery", return_value=y,
        ):
            world.begin_carry("energy_drink")
            self.observe_and_acknowledge()
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
            set_test_pet_values(app.state, energy=100)
            for now in (1, 1.3, 1.7):
                world.now = now
                world.update(time.monotonic())
            token = world.cursor.instance_id
            assert token is not None
            known = world.awareness.known_instance(token)
            assert known is not None
            self.assertIsNone(known.identity)
            world.cursor.release()
            self.assertEqual(world.world.get(token).state, ObjectState.PET_HELD)
            self.assertEqual(world.interaction.phase, "inspect")
            # Session save/advance can tick the need fractionally below 100.
            # The full-capacity refusal must be evaluated at the hand decision.
            set_test_pet_values(app.state, energy=100)
            self.finish_inspection()
            self.assertEqual(world.interaction.phase, "put_down")
            self.finish_clip("put_down")
            self.assertAlmostEqual(app.state.energy, 100, delta=.01)
            self.assertIsNone(app.state.food.last_food_id)

    def test_missing_apple_is_announced_before_unknown_replacement_inspection(self):
        world = self.app._world
        world._controls_active = lambda: True
        first = world.world.place_resting(
            "apple", world._body_x(), ObjectFootprint(8, 8),
        )
        for now in (0, .3):
            world.now = now
            world.update(time.monotonic())
        self.seed_previous_identification(first.instance_id, "apple", "food")
        record = world.awareness.record_for_instance(first.instance_id)
        assert record is not None
        world.awareness.memory.mark_assessed(record)
        world.world.remove(first.instance_id, expected_revision=first.revision)
        replacement = world.world.place_resting(
            "cookie", world._body_x(), ObjectFootprint(8, 8),
        )
        world.now = .4
        world.update(time.monotonic())
        recalled = world.awareness.known_instance(replacement.instance_id)
        assert recalled is not None
        self.assertIsNone(recalled.identity)
        self.assertNotEqual(recalled.token, record)
        # Loss priority applies even without appetite for the remembered apple.
        set_test_pet_values(self.app.state, satiety=100)
        world._controls_active = lambda: False
        world.now = .7
        world.update(time.monotonic())
        self.finish_orientation()
        self.assertEqual(world.interaction.phase, "notice_absence")
        missing = world.awareness.memory.get(record)
        assert missing is not None
        self.assertEqual(missing.place_status, "missing")
        self.complete_feedback()
        self.assertEqual(world.interaction.phase, "search")
        self.complete_feedback()
        for _ in range(8):
            world.now += .2
            world.update(time.monotonic())
            if world.interaction.phase == "approach":
                break
        self.assertEqual(world.interaction.phase, "approach")
        self.complete_feedback()
        self.assertEqual(world.interaction.phase, "pick_up")
        self.finish_pickup()
        self.assertEqual(world.interaction.phase, "inspect")
        self.assertEqual(world.world.get(replacement.instance_id).state,
                         ObjectState.PET_HELD)
        self.assertIsNone(self.app.state.food.last_food_id)
        set_test_pet_values(self.app.state, satiety=50)
        self.finish_inspection()
        self.assertEqual(world.interaction.phase, "put_down")
        self.assertIsNone(self.app.state.food.last_food_id)
        self.finish_clip("put_down")
        self.assertEqual(world.world.get(replacement.instance_id).state,
                         ObjectState.RESTING)
        self.assertTrue(world.interaction.search_active)
        self.assertEqual(world.awareness.memory.get(record), missing)

    def test_unpresented_unknown_item_is_accepted_and_identified_in_hands(self):
        world = self.app._world
        pointer_x = (self.app.settings.x or 0) + 96
        pointer_y = world._track().ground_y - 80
        with (
            patch.object(self.app.root, "winfo_pointerx", return_value=pointer_x),
            patch.object(self.app.root, "winfo_pointery", return_value=pointer_y),
        ):
            world.begin_carry("cookie")
            token = world.cursor.instance_id
            assert token is not None
            for now in (0, .3):
                world.now = now
                world.update(time.monotonic())
            known = world.awareness.known_instance(token)
            assert known is not None
            self.assertIsNone(known.identity)
            self.assertFalse(world.cursor.offer_ready)
            world.cursor.release()
        self.assertEqual(world.world.get(token).state, ObjectState.PET_HELD)
        self.assertEqual(world.interaction.phase, "inspect")
        self.assertAlmostEqual(self.app.state.satiety, 50, delta=1)
        self.finish_inspection()
        self.assertEqual(world.world.get(token).state, ObjectState.CONSUMED)
        self.assertEqual(self.app.state.food.last_food_id, "cookie")

    def test_refused_identified_offer_still_falls_instead_of_entering_hands(self):
        world = self.app._world
        set_test_pet_values(self.app.state, satiety=100)
        pointer_x = (self.app.settings.x or 0) + 96
        pointer_y = world._track().ground_y - 80
        with (
            patch.object(self.app.root, "winfo_pointerx", return_value=pointer_x),
            patch.object(self.app.root, "winfo_pointery", return_value=pointer_y),
        ):
            world.begin_carry("cookie")
            token = world.cursor.instance_id
            assert token is not None
            for now in (0, .3, .7, 1.1):
                world.now = now
                world.update(time.monotonic())
            known = world.awareness.known_instance(token)
            assert known is not None
            self.assertTrue(known.assessed)
            self.assertFalse(world.cursor.offer_ready)
            world.cursor.release()
        self.assertEqual(world.world.get(token).state, ObjectState.FALLING)
        self.assertFalse(world.interaction.active)
        self.assertIsNone(self.app.state.food.last_food_id)

    def test_missing_unknown_approach_target_releases_without_patrol(self):
        world = self.app._world
        origin = world._body_x()
        surface = world.world.snapshot().surface
        target = origin + 250 if origin + 250 <= surface.width - 8 else origin - 250
        item = world.world.place_resting(
            "apple", target, ObjectFootprint(8, 8),
        )
        cues = []
        presenter = world._present_feedback

        def capture(cue, reaction, done):
            cues.append(cue.event)
            presenter(cue, reaction, done)

        world._present_feedback = capture
        self.look_at(target)
        self.observe_and_acknowledge()
        self.assertEqual(world.interaction.phase, "approach")
        record = world.interaction.memory_id
        assert record is not None
        current = world.world.get(item.instance_id)
        world.world.remove(item.instance_id, expected_revision=current.revision)
        for _ in range(3):
            world.now += .3
            world.update(time.monotonic())
        self.assertFalse(world.interaction.active)
        self.assertNotIn("object_search", cues)
        self.assertIsNone(world.awareness.memory.get(record))
        self.assertIsNone(world._walk.movement.goal_x)
        for _ in range(3):
            world.now += .2
            world.update(time.monotonic())
        self.assertNotIn("object_search", cues)

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
        self.observe_and_acknowledge()
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
        set_test_pet_values(app.state, energy=65)
        track = world._track()
        boundary = track.left if side == "left" else track.right - world.width
        app._place_x(boundary + (120 * scale if side == "left" else -120 * scale))
        image = world.view.image("energy_drink", scale)
        footprint = ObjectFootprint(image.width() / 2, image.width() / 2)
        x = (footprint.left if side == "left" else
             world.world.snapshot().surface.width - footprint.right)
        item = world.world.place_resting("energy_drink", x, footprint)
        self.look_at(x)
        self.observe_and_acknowledge()
        self.assertEqual(world.interaction.phase, "approach")
        self.assertEqual(app._walk.movement.goal_x, boundary)
        self.assertFalse(world._can_acquire(item.instance_id))
        for index in range(10):
            app._walk.step(time.monotonic() + index, 1,
                           game_mode=False, attention_active=False)
            if app._walk.movement.remaining_distance:
                attention = world._visual.attention(
                    (0, 0), pointer_recent=True,
                )
                self.assertEqual(attention.mode, "object")
                self.assertFalse(attention.sees_environment(.1, 0))
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
        attention = world._visual.attention(
            (0, 0), pointer_recent=True,
        )
        self.assertEqual(attention.mode, "object")
        self.assertFalse(attention.sees_environment(.1, 0))
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
        set_test_pet_values(self.app.state, energy=50)
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
        self.observe_and_acknowledge()
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
