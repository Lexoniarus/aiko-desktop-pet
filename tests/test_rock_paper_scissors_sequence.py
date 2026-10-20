"""Headless checks for player-only score and Aiko-only bubble events."""

from __future__ import annotations

import unittest
from collections.abc import Callable

from aiko_pet.games.contracts import GameRoundEvent
from aiko_pet.games.rock_paper_scissors import Move, Outcome, Round, Score
from aiko_pet.ui.windows.rock_paper_scissors_dialogue import GameDialogue, outcome_event
from aiko_pet.ui.windows.rock_paper_scissors_sequence import (
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
        self.events: list[tuple[str, str]] = []
        self.reveals: list[tuple[Move, Score]] = []
        self.busy: list[bool] = []
        self.animations: list[str] = []
        self.rounds: list[GameRoundEvent] = []
        self.flow = RockPaperScissorsSequence(
            schedule=self.clock.schedule,
            cancel=self.clock.cancel,
            say=lambda value, _ms: self.events.append(("text", value)),
            show_emote=lambda name, _ms: self.events.append(("emote", name)),
            show_aiko_hand=lambda move, _ms: self.events.append(
                ("aiko_hand", move.value),
            ),
            reveal_player=lambda move, score: self.reveals.append(
                (move, score),
            ),
            animate=self.animations.append,
            set_busy=self.busy.append,
            round_event=self.rounds.append,
        )

    def step(self) -> None:
        token = self.flow.pending_timer
        assert token is not None
        self.clock.fire(token)

    def test_two_hands_reveal_in_separate_views_once(self) -> None:
        self.flow._game._random_index = lambda _size: 2
        self.flow.greet()
        self.assertEqual(self.animations, ["waving-greeting"])
        self.flow.choose(Move.ROCK)
        self.assertEqual([e.outcome for e in self.rounds], [None])
        self.assertEqual(self.events[-1], ("text", "Eins!"))
        self.assertEqual(self.busy, [True])
        for expected in ("Zwei!", "Drei!"):
            self.step()
            self.assertEqual(self.events[-1], ("text", expected))
            self.assertEqual(self.flow.score.games, 0)
        self.step()
        self.assertEqual(self.events[-1], ("emote", "exclamation"))
        self.assertEqual(self.reveals, [])
        self.step()
        self.assertEqual(self.events[-1], ("aiko_hand", "scissors"))
        self.assertEqual(
            self.reveals,
            [
                (Move.ROCK, Score(wins=1)),
            ],
        )
        self.assertEqual(self.flow.score.games, 1)
        self.assertEqual([e.outcome for e in self.rounds], [None, "win"])
        self.assertEqual(self.rounds[0].identity, self.rounds[1].identity)
        self.step()
        self.assertEqual(self.animations[-1], "failed")
        self.assertEqual(self.events[-1], ("emote", "drops"))
        self.step()
        self.assertEqual(self.events[-1][0], "text")
        from aiko_pet.pet.mind.catalog import DialogueBook

        allowed = {
            line.text
            for line in DialogueBook.from_file().lines
            if line.event == "game_player_win"
        }
        self.assertIn(self.events[-1][1], allowed)
        # Aiko must never narrate the player hand or overall score.
        self.assertNotIn("Stein", self.events[-1][1])
        self.step()
        self.assertEqual(self.busy, [True, False])
        self.assertEqual(len(self.reveals), 1)
        self.assertEqual(
            [kind for kind, _ in self.events],
            [
                "text",
                "text",
                "text",
                "text",
                "emote",
                "aiko_hand",
                "emote",
                "text",
            ],
        )

    def test_all_outcomes_trigger_correct_emotes_and_animations(self) -> None:
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

    def test_second_choice_is_blocked_until_outcome_finishes(self) -> None:
        self.flow.choose(Move.ROCK)
        self.flow.choose(Move.PAPER)
        self.assertEqual(self.busy, [True])
        for _ in range(7):
            self.step()
        self.flow.choose(Move.PAPER)
        self.assertEqual(self.flow.score.games, 1)
        self.assertEqual(self.busy, [True, False, True])

    def test_closing_discards_callbacks_and_unplayed_rounds(self) -> None:
        self.flow.choose(Move.ROCK)
        token = self.flow.pending_timer
        assert token is not None
        stale = self.clock.tasks[token][1]
        self.flow.close()
        self.assertEqual(self.flow.score.games, 0)
        self.assertIsNone(self.flow.pending_timer)
        self.assertEqual(self.clock.tasks, {})
        stale()
        self.flow.choose(Move.PAPER)
        self.flow.greet()
        self.assertEqual(self.events, [("text", "Eins!")])
        self.assertEqual(self.reveals, [])

    def test_outcome_dialogue_varies_without_narrating_player_score(self) -> None:
        result = Round(Move.ROCK, Move.SCISSORS, Outcome.WIN)
        dialogue, other = GameDialogue(), GameDialogue()
        remarks = [dialogue.choose(outcome_event(result)) for _ in range(3)]
        self.assertEqual(len(dialogue._book.recent), 3)
        self.assertEqual(tuple(other._book.recent), ())
        self.assertEqual(len(set(remarks)), 3)
        self.assertTrue(all("Stein" not in remark for remark in remarks))


if __name__ == "__main__":
    unittest.main()
