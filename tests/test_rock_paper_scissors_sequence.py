"""Headless regression tests for serialized game reactions and cancellation."""

from __future__ import annotations

import unittest
from collections.abc import Callable

from aiko_pet.games.rock_paper_scissors import Move
from aiko_pet.presentation.rock_paper_scissors_sequence import (
    RockPaperScissorsSequence,
)
from aiko_pet.presentation.rock_paper_scissors_text_de import (
    outcome_line, score_line,
)
from aiko_pet.games.rock_paper_scissors import Outcome, Round, Score


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
        self.events: list[tuple[str, str]] = []
        self.busy: list[bool] = []
        self.animations: list[str] = []
        self.flow = RockPaperScissorsSequence(
            schedule=self.clock.schedule,
            cancel=self.clock.cancel,
            say=lambda value, _ms: self.events.append(("text", value)),
            show_emote=lambda name, _ms: self.events.append(("emote", name)),
            show_hands=lambda player, aiko, _ms: self.events.append(
                ("hands", f"{player.value}/{aiko.value}"),
            ),
            animate=self.animations.append,
            set_busy=self.busy.append,
        )

    def step(self) -> None:
        token = self.flow.pending_timer
        assert token is not None
        self.clock.fire(token)

    def test_all_cues_are_serial_and_animated_for_aikos_defeat(self) -> None:
        self.flow._game._random_index = lambda _size: 2
        self.flow.greet()
        self.assertEqual(self.animations, ["waving"])
        self.assertEqual(self.events[0][0], "text")
        self.flow.choose(Move.ROCK)
        self.assertEqual(self.busy, [True])
        self.assertEqual(self.events[-1], ("text", "Eins!"))
        self.assertEqual(self.flow.score.games, 0)
        self.step()
        self.assertEqual(self.events[-1], ("text", "Zwei!"))
        self.step()
        self.assertEqual(self.events[-1], ("text", "Drei!"))
        self.assertEqual(self.flow.score.games, 0)
        self.step()
        self.assertEqual(self.events[-1], ("emote", "exclamation"))
        self.assertEqual(self.flow.score.games, 0)
        self.step()
        self.assertEqual(self.events[-1], ("hands", "rock/scissors"))
        self.assertEqual(self.flow.score.wins, 1)
        self.step()
        self.assertEqual(self.animations, ["waving", "failed"])
        self.assertEqual(self.events[-1], ("emote", "drops"))
        self.step()
        self.assertEqual(self.events[-1][0], "text")
        self.assertIn("Punkt", self.events[-1][1])
        self.step()
        self.assertEqual(self.events[-1][0], "text")
        self.assertIn("1 Runde", self.events[-1][1])
        self.assertIn("du 1, ich 0", self.events[-1][1])
        self.step()
        self.assertEqual(self.busy, [True, False])
        self.assertFalse(self.flow.busy)
        self.assertEqual([kind for kind, _text in self.events], [
            "text", "text", "text", "text", "emote",
            "hands", "emote", "text", "text",
        ])

    def test_different_outcomes_drive_distinct_animation_and_emote(self) -> None:
        for aiko_index, animation, emote in (
            (0, "failed", "drops"),
            (1, "waving", "question"),
            (2, "jumping", "star"),
        ):
            with self.subTest(aiko_index=aiko_index):
                self.setUp()
                self.flow._game._random_index = lambda _size, n=aiko_index: n
                self.flow.choose(Move.PAPER)
                for _ in range(5):
                    self.step()
                self.assertEqual(self.animations[-1], animation)
                self.assertEqual(self.events[-1], ("emote", emote))

    def test_choice_is_blocked_until_the_final_line_finishes(self) -> None:
        self.flow.choose(Move.ROCK)
        self.flow.choose(Move.PAPER)
        self.assertEqual(self.busy, [True])
        for _ in range(8):
            self.step()
        self.flow.choose(Move.PAPER)
        self.assertEqual(self.flow.score.games, 1)
        self.assertEqual(self.busy, [True, False, True])

    def test_close_discards_stale_callbacks_and_unplayed_round(self) -> None:
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
        self.assertEqual(self.events, [("text", "Eins!")])

    def test_contextual_text_varies_without_claiming_unknown_information(self) -> None:
        result = Round(Move.ROCK, Move.SCISSORS, Outcome.WIN)
        lines = [outcome_line(result, count) for count in (1, 2, 3)]
        self.assertEqual(len(set(lines)), 3)
        scores = [
            score_line(Score(wins=count, losses=0))
            for count in (1, 2, 3)
        ]
        self.assertEqual(len(set(scores)), 3)
        self.assertIn("unentschieden 0", scores[0])


if __name__ == "__main__":
    unittest.main()
