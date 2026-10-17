"""Pure, deterministic goodbye timeline used by explicit settings exit."""

from __future__ import annotations

import unittest
from collections.abc import Callable

from aiko_pet.desktop.farewell import FarewellSequence
from aiko_pet.pet.mind.reaction_sequence import Cue


class FarewellSequenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.events: list[str] = []
        self.waiting: dict[str, Callable[[], None]] = {}
        self.delays: list[int] = []
        self.serial = 0

        def schedule(delay: int, callback: Callable[[], None]) -> str:
            self.delays.append(delay)
            self.serial += 1
            key = f"timer-{self.serial}"
            self.waiting[key] = callback
            return key

        def cancel(token: str) -> None:
            self.waiting.pop(token, None)

        self.sequence = FarewellSequence(
            schedule=schedule,
            cancel=cancel,
            prepare=lambda: self.events.append("prepare"),
            animate=lambda: self.events.append("waving-greeting"),
            say=lambda line, duration: self.events.append(
                f"say:{line}:{duration}",
            ),
            finish=lambda: self.events.append("shutdown"),
            seconds=1.895,
        )

    def test_one_goodbye_then_exactly_one_shutdown(self) -> None:
        self.sequence.begin()
        self.sequence.begin()
        self.assertTrue(self.sequence.active)
        duration = max(2600, Cue.text(FarewellSequence.TEXT).duration_ms)
        self.assertEqual(self.delays, [duration])
        self.assertEqual(
            self.events,
            [
                "prepare",
                "waving-greeting",
                f"say:{FarewellSequence.TEXT}:{duration + 500}",
            ],
        )
        key = self.sequence.pending_timer
        assert key is not None
        self.waiting.pop(key)()
        self.assertFalse(self.sequence.active)
        self.assertIsNone(self.sequence.pending_timer)
        self.assertEqual(self.events[-1], "shutdown")
        self.assertEqual(self.events.count("shutdown"), 1)

    def test_forced_shutdown_cancels_delayed_callback(self) -> None:
        self.sequence.begin()
        key = self.sequence.pending_timer
        assert key is not None
        self.sequence.cancel()
        self.sequence.cancel()
        self.assertNotIn(key, self.waiting)
        self.assertFalse(self.sequence.active)
        self.assertNotIn("shutdown", self.events)

    def test_invalid_length_and_failed_presentation_still_quit(self) -> None:
        with self.assertRaises(ValueError):
            FarewellSequence(
                schedule=lambda _delay, _callback: "timer",
                cancel=lambda _token: None,
                prepare=lambda: None,
                animate=lambda: None,
                say=lambda _line, _delay: None,
                finish=lambda: None,
                seconds=0.0,
            )

        self.sequence._animate = lambda: (_ for _ in ()).throw(RuntimeError())
        self.sequence.begin()
        self.assertFalse(self.sequence.active)
        self.assertEqual(self.events[-1], "shutdown")


if __name__ == "__main__":
    unittest.main()
