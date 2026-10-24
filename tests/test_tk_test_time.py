"""Validate the clock that drives real-widget tests without wall-clock waits."""

import time
import tkinter as tk
import unittest

from aiko_pet import gui
from tools.tk_test_time import ControlledTkTime


class ControlledTkTimeTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(str(error))
        self.addCleanup(self.root.destroy)

    def test_callbacks_keep_deadlines_and_nested_order_with_consistent_clocks(self):
        with ControlledTkTime() as clock:
            label = tk.Label(self.root, text="before")
            wall = time.time()
            monotonic = time.monotonic()

            def first():
                label.configure(text="first")
                self.root.after(50, lambda: label.configure(text="second"))

            self.root.after(100, first)
            clock.advance(.099)
            self.assertEqual(label.cget("text"), "before")
            clock.advance(.001)
            self.assertEqual(label.cget("text"), "first")
            self.assertAlmostEqual(time.time() - wall, .1, places=5)
            self.assertAlmostEqual(time.monotonic() - monotonic, .1)
            clock.advance(.049)
            self.assertEqual(label.cget("text"), "first")
            clock.advance(.001)
            self.assertEqual(label.cget("text"), "second")

    def test_cancelled_and_destroyed_widget_callbacks_never_run(self):
        with ControlledTkTime() as clock:
            calls = []
            token = self.root.after(10, lambda: calls.append("cancelled"))
            self.root.after_cancel(token)
            window = tk.Toplevel(self.root)
            window.after(10, lambda: calls.append("destroyed"))
            window.destroy()
            self.root.after(20, lambda: calls.append("current"))
            clock.advance(.1)
            self.assertEqual(calls, ["current"])

    def test_native_update_runs_zero_delay_then_idle_without_advancing_time(self):
        with ControlledTkTime():
            now = time.monotonic()
            calls = []
            self.root.after_idle(lambda: calls.append("idle"))
            self.root.after(0, lambda: calls.append("timer"))
            self.root.update()
            self.assertEqual(calls, ["timer", "idle"])
            self.assertEqual(time.monotonic(), now)

    def test_callback_failure_surfaces_and_restores_native_functions(self):
        monotonic, wall, after = time.monotonic, time.time, tk.Misc.after
        runtime = gui.DesktopRuntime
        with self.assertRaisesRegex(RuntimeError, "callback failed"):
            with ControlledTkTime() as clock:
                def fail():
                    raise RuntimeError("callback failed")

                self.root.after(5, fail)
                clock.advance(.01)
        self.assertIs(time.monotonic, monotonic)
        self.assertIs(time.time, wall)
        self.assertIs(tk.Misc.after, after)
        self.assertIs(gui.DesktopRuntime, runtime)

    def test_clock_cannot_rewind_or_accept_nonfinite_time(self):
        with ControlledTkTime() as clock:
            for seconds in (-1, float("nan"), float("inf")):
                with self.subTest(seconds=seconds), self.assertRaises(ValueError):
                    clock.advance(seconds)
