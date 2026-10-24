"""Reading time, serial code reveal, cancellation and real round evidence."""

import unittest

from aiko_pet.games.mastermind import MastermindSession
from aiko_pet.ui.windows.mastermind_sequence import MastermindSequence

SECRET = ("red", "red", "blue", "green")


class MastermindSequenceTests(unittest.TestCase):
    def setUp(self):
        self.tasks = {}
        self.serial = 0
        self.codes, self.events, self.lines, self.emotes = [], [], [], []
        self.hidden = 0
        self.flow = MastermindSequence(
            schedule=self.schedule,
            cancel=lambda key: self.tasks.pop(key, None),
            present=lambda *_view: None,
            show_code=self.codes.append,
            hide_code=self.hide,
            say=lambda *line: self.lines.append(line),
            animate=lambda _clip: None,
            emote=lambda *emote: self.emotes.append(emote),
            dialogue=lambda event: event,
            round_event=self.events.append,
            game=MastermindSession(lambda: SECRET),
        )
        self.addCleanup(self.flow.close)

    def hide(self):
        self.hidden += 1

    def schedule(self, delay, callback):
        self.serial += 1
        key = str(self.serial)
        self.tasks[key] = delay, callback
        return key

    def advance_callback(self):
        key = next(iter(self.tasks))
        _, callback = self.tasks.pop(key)
        callback()

    def drain(self):
        while self.tasks:
            self.advance_callback()

    def test_greeting_blocks_input_then_reveals_only_after_terminal_guess(self):
        self.flow.greet()
        self.assertFalse(self.flow.submit(SECRET))
        self.assertGreaterEqual(self.lines[-1][1], 4000)
        self.assertEqual(self.codes[0].slots, (None,) * 4)
        self.advance_callback()
        self.assertTrue(self.flow.submit(SECRET))
        self.assertFalse(self.flow.submit(SECRET))
        for _ in range(4):
            self.assertEqual(next(iter(self.tasks.values()))[0], 90)
            self.assertEqual(self.codes[-1].slots, (None,) * 4)
            self.advance_callback()
        for count in range(1, 5):
            self.assertEqual(next(iter(self.tasks.values()))[0], 180)
            self.advance_callback()
            self.assertEqual(
                self.codes[-1].slots, SECRET[:count] + (None,) * (4 - count)
            )
        self.assertEqual(self.emotes[-1], ("star", 800))
        self.flow.next_round()
        self.assertEqual(self.flow.game.score.games, 1)
        self.drain()
        self.assertFalse(self.flow.busy)
        self.assertEqual([e.outcome for e in self.events], [None, "win"])
        self.flow.next_round()
        self.assertEqual(self.codes[-1].slots, (None,) * 4)
        self.assertEqual(self.flow.game.view.guesses, ())

    def test_close_during_reveal_retains_completed_result_and_cancels_stale_step(self):
        self.flow.greet()
        self.drain()
        self.flow.submit(SECRET)
        for _ in range(4):
            self.advance_callback()
        stale = next(iter(self.tasks.values()))[1]
        count = len(self.codes)
        score = self.flow.close()
        stale()
        self.assertEqual(score.wins, 1)
        self.assertEqual(len(self.codes), count)
        self.assertEqual(self.hidden, 1)
        self.assertFalse(self.tasks)
        self.flow.close()
        self.assertEqual(self.hidden, 1)

    def test_last_attempt_line_and_loss_do_not_leak_secret(self):
        self.flow.greet()
        self.drain()
        for attempt in range(10):
            self.assertTrue(self.flow.submit(("white",) * 4))
            for _ in range(4):
                self.advance_callback()
            if attempt == 8:
                self.assertEqual(self.lines[-1][0], "game_mm_last")
            if attempt < 9:
                self.assertEqual(self.codes[-1].slots, (None,) * 4)
            self.drain()
        self.assertEqual(self.flow.game.score.losses, 1)
        self.assertEqual(self.codes[-1].slots, SECRET)
        self.assertEqual([e.outcome for e in self.events], [None, "loss"])

    def test_interrupted_unfinished_round_has_no_completed_units(self):
        self.flow.greet()
        self.drain()
        self.flow.submit(("white",) * 4)
        self.assertEqual(self.flow.close().games, 0)
        self.assertFalse(self.tasks)

    def test_close_during_feedback_does_not_award_a_pending_result(self):
        self.flow.greet()
        self.drain()
        self.flow.submit(SECRET)
        stale = next(iter(self.tasks.values()))[1]
        self.assertEqual(self.flow.close().games, 0)
        stale()
        self.assertEqual([e.outcome for e in self.events], [None])
        self.assertEqual(self.codes[-1].slots, (None,) * 4)
