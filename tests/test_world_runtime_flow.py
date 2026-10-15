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
from aiko_pet.pet.state import PetState
from aiko_pet.world.contracts import ObjectFootprint, ObjectState


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
        store.save(PetState(satiety=76, energy=60), PetSettings(
            auto_walk=False, auto_routine=False, observe_computer=False,
            learn_rhythm=False, spontaneous_talk=False,
        ))
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

    def run_for(self, seconds):
        return self.run_until(lambda: False, seconds)

    def run_until(self, predicate, seconds):
        trace = []
        until = time.monotonic() + seconds

        def sample():
            world, animated = self.app._world, self.app._animated
            goal = world.awareness.intentions.goal
            row = (world.now, world.interaction.phase,
                   animated.frame_clock.active_key, animated.frame_clock.frame_index,
                   self.app.settings.x, goal.purpose if goal else None)
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

    def test_satiated_food_is_investigated_put_down_and_not_repeated(self):
        world = self.app._world
        item = world.world.place_resting("onigiri", world._body_x() + 75,
                                         ObjectFootprint(16, 16))
        trace = self.run_until(lambda: any(
            known.examined for known in world.awareness.memory.snapshot()
        ) and not world.interaction.active, 30)
        phases = {row[1] for row in trace}
        self.assertTrue({"notice", "approach", "pick_up", "inspect", "recognize",
                         "decide", "put_down"}.issubset(phases), trace)
        self.assertNotIn("eat", phases, trace)
        self.assertFalse(world.interaction.active, trace)
        self.assertEqual(world.world.get(item.instance_id).state, ObjectState.RESTING)
        known = world.awareness.memory.get(item.instance_id)
        assert known is not None
        self.assertTrue(known.examined)
        expected = ["object_notice", "object_approach", "object_pick_up",
                    "object_inspect", "object_recognized", "object_later",
                    "object_put_down"]
        self.assertEqual([event for _, event, _ in self.feedback], expected)
        for before, after in zip(self.feedback, self.feedback[1:]):
            self.assertGreater(after[0] - before[0], 1.6)
        self.assertTrue(any("Onigiri" in text for _, _, text in self.bubbles))
        self.assertTrue(any("später" in text for _, _, text in self.bubbles))
        trace = self.run_for(1.3)
        self.assertTrue(all(row[1] == "idle" for row in trace), trace)
        self.app.state.satiety = 69
        self.feedback.clear()
        trace = self.run_until(lambda: world.world.get(item.instance_id).state
                               == ObjectState.CONSUMED, 22)
        self.assertEqual(world.world.get(item.instance_id).state, ObjectState.CONSUMED,
                         trace)
        self.assertEqual(self.feedback[0][1], "object_return")
        self.assertNotIn("object_notice", [event for _, event, _ in self.feedback])
        self.assertGreater(self.app.state.satiety, 98)
        self.assertEqual(self.app.state.friendship, 15)
        self.app.state.energy = 66
        drink = world.world.place_resting("energy_drink", world._body_x() + 30,
                                          ObjectFootprint(12, 12))
        self.feedback.clear()
        trace = self.run_until(lambda: any(
            cue[1] == "object_notice" for cue in self.feedback
        ), 8)
        self.assertIn("object_notice", [cue[1] for cue in self.feedback], trace)
        started = self.feedback[0][0]
        trace += self.run_until(lambda: (
            (known := world.awareness.memory.get(drink.instance_id)) is not None
            and known.examined and world.world.get(drink.instance_id).state
            == ObjectState.RESTING and not world.interaction.active
        ), 25)
        self.assertFalse(world.interaction.active, trace)
        self.assertLess(world.now - started, 25)
        self.assertEqual(world.world.get(drink.instance_id).state, ObjectState.RESTING)
        events = [cue[1] for cue in self.feedback]
        self.assertEqual(events[events.index("object_notice"):], expected)
        self.assertTrue(any("Energy" in text for _, _, text in self.bubbles))
        self.assertLess(self.app.state.energy, 67)
        self.assertIsNone(world._visual.object_target)
        known = world.awareness.memory.get(drink.instance_id)
        assert known is not None
        self.assertEqual(known.identity, "energy_drink")
        self.assertTrue(known.examined)

    def test_sleep_during_held_inspection_puts_down_and_restart_keeps_portion(self):
        world = self.app._world
        item = world.world.place_resting("onigiri", world._body_x(),
                                         ObjectFootprint(16, 16))
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
        self.enterContext(patch.object(self.app.root, "winfo_pointerx",
                                       return_value=(self.app.settings.x or 0) + 96))
        self.enterContext(patch.object(self.app.root, "winfo_pointery",
                                       return_value=world._track().ground_y - 80))
        self.enterContext(patch("aiko_pet.desktop.world_runtime.mouse_buttons_down_windows",
                                return_value=(True, False)))
        world.begin_carry("energy_drink")
        token = world.carry_id
        assert token is not None
        self.run_until(lambda: world._offer_ready, 6)
        self.assertTrue(world._offer_ready)
        self.assertLess(self.app.state.energy, 61)
        world.release()
        self.assertEqual(world.interaction.phase, "inspect")
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
