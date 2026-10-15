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
        trace = self.run_for(1.3)
        self.assertTrue(all(row[1] == "idle" for row in trace), trace)

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
