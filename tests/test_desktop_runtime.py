"""Headless desktop tick lifecycle and ordering tests."""

from __future__ import annotations

import unittest
from collections.abc import Callable

from aiko_pet.desktop.runtime import DesktopRuntime, TICK_MILLISECONDS


class FakeStages:
    def __init__(self) -> None:
        self._closed = False
        self.calls: list[str] = []
        self.pointer = (3, 7)
        self.elapsed: float | None = None
        self.wall_time: float | None = None

    def _greet_on_start(self) -> None:
        self.calls.append("greet")

    def _advance_pet_lifecycle(self, now: float, wall_time: float) -> None:
        self.calls.append("lifecycle")
        self.wall_time = wall_time

    def _refresh_taskbar_track(self, now: float) -> None:
        self.calls.append("track")

    def _poll_desktop_click(self) -> None:
        self.calls.append("click")

    def _refresh_hover(self, now: float) -> None:
        self.calls.append("hover")

    def _react_to_computer(self, now: float) -> None:
        self.calls.append("computer")

    def _observe_pointer(self, now: float) -> tuple[int, int]:
        self.calls.append("pointer")
        return self.pointer

    def _render_current_sprite(
        self, now: float, elapsed: float, pointer: tuple[int, int],
    ) -> None:
        self.calls.append("sprite")
        self.elapsed = elapsed
        assert pointer == self.pointer

    def _maybe_show_idle_emote(self, now: float) -> None:
        self.calls.append("emote")

    def _maybe_speak_spontaneously(self, now: float) -> None:
        self.calls.append("dialogue")

    def _present_pending_notification(self, now: float) -> None:
        self.calls.append("notification")

    def _refresh_overlays_and_autosave(self, now: float) -> None:
        self.calls.append("maintenance")

    def _tick(self) -> None:
        self.calls.append("tick")


class DesktopRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.stages = FakeStages()
        self.scheduled: dict[str, tuple[int, Callable[[], None]]] = {}
        self.cancelled: list[str] = []
        self.next_id = 0
        self.now = 10.0

        def schedule(milliseconds: int, callback: Callable[[], None]) -> str:
            self.next_id += 1
            key = f"timer-{self.next_id}"
            self.scheduled[key] = (milliseconds, callback)
            return key

        self.runtime = DesktopRuntime(
            self.stages,
            schedule=schedule,
            cancel=self.cancelled.append,
            monotonic=lambda: self.now,
            wall_time=lambda: 1_781_000_000.0,
        )

    def test_start_and_stop_own_only_their_two_timers(self) -> None:
        self.runtime.start()
        first = self.runtime.scheduled_tick
        greeting = self.runtime.scheduled_greeting
        assert first is not None and greeting is not None
        self.assertEqual(self.scheduled[first][0], TICK_MILLISECONDS)
        self.assertEqual(self.scheduled[greeting][0], 460)
        self.runtime.start()
        self.assertEqual(self.next_id, 2)
        self.runtime.stop()
        self.assertEqual(self.cancelled, [first, greeting])
        self.assertIsNone(self.runtime.scheduled_tick)
        self.assertIsNone(self.runtime.scheduled_greeting)

    def test_manual_tick_preserves_exact_phase_order_and_dt_bound(self) -> None:
        self.runtime.start()
        first = self.runtime.scheduled_tick
        assert first is not None
        self.now = 500.0
        self.runtime.tick()
        self.assertEqual(self.cancelled, [first])
        self.assertEqual(self.stages.elapsed, 0.5)
        self.assertEqual(self.stages.wall_time, 1_781_000_000.0)
        self.assertEqual(self.stages.calls, [
            "lifecycle", "track", "click", "hover", "computer",
            "pointer", "sprite", "emote", "dialogue",
            "notification", "maintenance",
        ])
        self.assertIsNotNone(self.runtime.scheduled_tick)

    def test_closed_desktop_never_starts_or_reschedules(self) -> None:
        self.stages._closed = True
        self.runtime.start()
        self.runtime.tick()
        self.assertEqual(self.next_id, 0)
        self.stages._closed = False
        self.runtime.start()
        self.stages._closed = True
        self.runtime.tick()
        self.assertEqual(self.next_id, 2)


if __name__ == "__main__":
    unittest.main()
