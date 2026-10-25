"""Isolated native Tk quiz: input, wrapping, progression and cancellation."""

import tkinter as tk
import unittest
from unittest.mock import Mock, patch

from aiko_pet.games.quiz_catalogue import QuizCatalogue
from aiko_pet.ui.common.skin import AikoSkin
from aiko_pet.ui.common.window_geometry import WindowBounds
from aiko_pet.ui.windows.quiz_window import QuizWindow


class QuizWindowTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError as error:
            raise unittest.SkipTest('Native Tk display required') from error
        self.root.withdraw()
        self.addCleanup(self.root.destroy)
        self.skin = AikoSkin(self.root)
        self.closed = Mock()
        self.events = []
        self.scheduled = []

    def make_game(self, width=900, **kwargs):
        game = QuizWindow(
            self.root, on_closed=self.closed, speak=Mock(), animate=Mock(),
            emote=Mock(), dialogue=lambda event: event, always_on_top=False,
            skin=self.skin, round_event=self.events.append,
            bounds_at=lambda _x, _y: WindowBounds(0, 0, width, 760), **kwargs,
        )
        self.addCleanup(game.close)
        if game._sequence is not None:
            game._sequence._schedule = lambda _ms, fn: (
                self.scheduled.append(fn) or 'test-timer'
            )
            game._sequence._cancel = lambda _timer: None
        game.greet()
        self.ready()
        self.root.update()
        return game

    def ready(self):
        while self.scheduled:
            self.scheduled.pop()()

    def test_answer_buttons_commit_once_next_is_explicit_and_end_counts_once(self):
        game = self.make_game()
        sequence = game._sequence
        assert sequence is not None
        for number in range(10):
            before = sequence.game.index
            button = next(b for b, a in zip(game.answers, sequence.game.current.answers)
                          if a.id == sequence.game.current.correct_answer_id)
            button.invoke()
            self.assertEqual(sequence.game.index, before)
            self.assertTrue(all(b.cget('state') == 'disabled' for b in game.answers))
            self.assertIn('Richtig', game._explanation.cget('text'))
            self.ready()
            if number < 9:
                assert game._panel.next_button is not None
                game._panel.next_button.invoke()
        self.assertEqual(sequence.game.correct, 10)
        self.assertEqual(set(game._panel.score_labels), {'correct', 'answered'})
        self.assertEqual(sum(e.outcome == 'completed' for e in self.events), 1)
        assert game._panel.next_button is not None
        game._panel.next_button.invoke()
        self.assertEqual((sequence.game.index, sequence.game.correct), (0, 0))
        self.assertEqual(self.events[-1].session_id, self.events[0].session_id)
        self.assertEqual(self.events[-1].number, 2)
        game.close()
        game.close()
        self.closed.assert_called_once()
        self.assertEqual(self.closed.call_args.args[0].games, 0)

    def test_long_answers_wrap_in_a_narrow_work_area_and_abandon_counts_nothing(self):
        game = self.make_game(width=340)
        sequence = game._sequence
        assert sequence is not None
        longest = max(QuizCatalogue.load().questions,
                      key=lambda q: max(len(a.text) for a in q.answers))
        sequence.game.questions = (longest, *sequence.game.questions[1:])
        game._present()
        self.root.update()
        for button in game.answers:
            self.assertLessEqual(button.winfo_reqwidth(), game._panel.content_width)
            self.assertGreater(button.winfo_height(), 20)
        self.assertLessEqual(game.window.winfo_height(), 740)
        self.assertTrue(game.window.bind('1'))
        self.assertTrue(game.window.bind('<Escape>'))
        wrong = next(i for i, a in enumerate(sequence.game.current.answers)
                     if a.id != sequence.game.current.correct_answer_id)
        game.answers[wrong].invoke()
        self.assertIn('Deine Antwort', game.answers[wrong].cget('text'))
        self.assertTrue(any('✓ Richtig' in b.cget('text') for b in game.answers))
        game.close()
        self.assertFalse(any(e.outcome == 'completed' for e in self.events))

    def test_unavailable_catalogue_is_readable_and_does_not_start_or_award(self):
        with patch.object(QuizCatalogue, 'load', side_effect=ValueError('invalid')):
            game = self.make_game()
        self.assertIsNone(game._sequence)
        self.assertIn('nicht verfügbar', game._question.cget('text'))
        self.assertFalse(self.events)
        game.close()


if __name__ == '__main__':
    unittest.main()
