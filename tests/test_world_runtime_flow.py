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
from aiko_pet.world.contracts import ObjectFootprint, ObjectState, WorldPosition


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
        trace = []
        until = time.monotonic() + seconds

        def sample():
            world, animated = self.app._world, self.app._animated
            trace.append((world.now, world.interaction.phase,
                          animated.frame_clock.active_key,
                          animated.frame_clock.frame_index,
                          self.app.settings.x,
                          world.awareness.intentions.goal))
            if time.monotonic() >= until:
                self.app.root.quit()
            else:
                self.app.root.after(25, sample)

        self.app.root.after(1, sample)
        self.app.root.mainloop()
        return trace

    def test_baseline_full_food_is_recognized_but_never_investigated(self):
        world = self.app._world
        item = world.world.place_resting("onigiri", world._body_x() + 75,
                                         ObjectFootprint(16, 16))
        trace = self.run_for(1.1)
        known = world.awareness.memory.snapshot()
        self.assertEqual(known[0].identity, "onigiri", trace)
        self.assertIsNone(world.awareness.intentions.goal, trace)
        self.assertEqual(world.world.get(item.instance_id).state, ObjectState.RESTING)
        self.assertTrue(all(row[1] == "idle" for row in trace), trace)

    def test_baseline_cursor_entry_truncates_a_committed_drink(self):
        world = self.app._world
        item = world.world.create_held("energy_drink",
                                       WorldPosition(world._body_x(), 80),
                                       ObjectFootprint(10, 10))
        self.run_for(.9)
        self.assertTrue(world.interaction.offer_on_release(item.instance_id))
        trace = self.run_for(.2)
        self.assertEqual(world.interaction.phase, "eat", trace)
        self.app.canvas.event_generate("<Enter>")
        trace += self.run_for(.1)
        self.assertEqual(world.interaction.phase, "idle", trace)
        self.assertEqual(world.world.get(item.instance_id).state, ObjectState.CONSUMED)
        self.assertGreater(self.app.state.energy, 69)
