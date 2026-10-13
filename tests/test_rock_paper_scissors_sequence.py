"""Headless ordered-speech and cancellation tests for Aiko's minigame."""

from __future__ import annotations

import unittest
from collections.abc import Callable

from aiko_pet.games.rock_paper_scissors import Move
from aiko_pet.presentation.rock_paper_scissors_sequence import (
    RockPaperScissorsSequence,
)


class FakeClock:
    def __init__(self) -> None:
        self.next_id = 0
        self.tasks: dict[str, tuple[int, Callable[[], None]]] = {}

    def schedule(self, delay: int, action: Callable[[], None]) -> str:
        self.next_id += 1
        name = str(self.next_id)
        self.tasks[name] = delay, action
        return name

    def cancel(self, token: str) -> None:
        self.tasks.pop(token, None)

    def fire(self, token: str) -> None:
        _, action = self.tasks.pop(token)
        action()


class RockPaperScissorsSequenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.clock = FakeClock()
        self.lines: list[str] = []
        self.busy: list[bool] = []
        self.flow = RockPaperScissorsSequence(
            schedule=self.clock.schedule,
            cancel=self.clock.cancel,
            say=lambda text, _ms: self.lines.append(text),
            set_busy=self.busy.append,
        )

    def step(self) -> None:
        token = self.flow.pending_timer
        assert token is not None
        self.clock.fire(token)

    def test_every_spoken_cue_is_sequential_and_score_is_last(self) -> None:
        self.flow._game._random_index = lambda _count: 2
        self.flow.greet()
        self.assertEqual(len(self.lines), 1)
        self.flow.choose(Move.ROCK)
        self.assertEqual(self.lines[-1], "Eins!")
        self.assertEqual(self.busy, [True])
        self.assertEqual(self.flow.score.games, 0)
        for phrase in ("Zwei!", "Drei!"):
            self.step()
            self.assertEqual(self.lines[-1], phrase)
            self.assertEqual(self.flow.score.games, 0)
        self.step()
        self.assertIn("Du hast ✊🏻 Stein", self.lines[-1])
        self.assertIn("Ich habe ✌🏻 Schere", self.lines[-1])
        self.assertEqual(self.flow.score.wins, 1)
        self.step()
        self.assertIn("du hast gewonnen", self.lines[-1])
        self.step()
        self.assertIn("1 Runde", self.lines[-1])
        self.assertIn("Unentschieden: 0", self.lines[-1])
        self.step()
        self.assertEqual(self.busy, [True, False])
        self.assertFalse(self.flow.busy)
        self.assertEqual(len(self.lines), 7)

    def test_second_selection_is_ignored_until_all_lines_finish(self) -> None:
        self.flow.choose(Move.ROCK)
        self.flow.choose(Move.PAPER)
        self.assertEqual(self.busy, [True])
        for _ in range(6):
            self.step()
        self.flow.choose(Move.PAPER)
        self.assertEqual(self.flow.score.games, 1)
        self.assertEqual(self.busy, [True, False, True])

    def test_exit_cancels_callbacks_and_does_not_add_an_unplayed_round(self) -> None:
        self.flow.choose(Move.ROCK)
        token = self.flow.pending_timer
        assert token is not None
        stale = self.clock.tasks[token][1]
        self.flow.close()
        self.assertIsNone(self.flow.pending_timer)
        self.assertEqual(self.flow.score.games, 0)
        self.assertEqual(self.clock.tasks, {})
        stale()
        self.flow.choose(Move.PAPER)
        self.flow.greet()
        self.assertEqual(self.lines, ["Eins!"])


if __name__ == "__main__":
    unittest.main()
