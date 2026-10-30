"""Real game host: guided reveals and autonomous waits require no pointer event."""
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from aiko_pet.games.contracts import GameId
from aiko_pet.infrastructure.persistence import StateStore
from aiko_pet.ui.common.game_pacing import GAME_PACING
from aiko_pet.ui.windows.quiz_window import QuizWindow
from tools.desktop_test_support import create_test_desktop
from tools.tk_test_time import ControlledTkTime


class QuizPresentationGuiTests(unittest.TestCase):
    def setUp(self):
        self.clock = self.enterContext(ControlledTkTime())
        folder = self.enterContext(tempfile.TemporaryDirectory())
        self.pet = create_test_desktop(store=StateStore(Path(folder) / 'test.json'))
        self.addCleanup(self.pet.quit)
        self.pet.settings.auto_routine = False
        self.pet.settings.spontaneous_talk = False
        self.pet._hover.open_game(GameId.QUIZ)
        game = self.pet._hover.game_window
        assert isinstance(game, QuizWindow)
        self.game = game

    def until(self, predicate):
        for _ in range(2000):
            if predicate():
                return
            self.clock.advance(.1)
        self.fail('Quiz presentation did not reach its boundary')

    def test_automatic_wait_pose_without_hover_is_interrupted_by_selection(self):
        sequence = self.game._sequence
        assert sequence is not None
        self.assertTrue(all(not b.winfo_manager() for b in self.game.answers))
        started = self.clock.monotonic()
        self.until(lambda: not sequence.busy)
        self.assertLessEqual(self.clock.monotonic() - started, 28)
        self.assertEqual(sequence.visible_answers, 4)
        self.clock.advance(22.1)
        self.assertEqual(self.pet._animated._game_clip, 'idle-question-request')
        self.assertEqual(self.game._waiting._step, 2)
        correct = sequence.game.current.correct_answer_id
        self.assertTrue(sequence.answer(correct))
        self.assertIsNone(self.pet._animated._game_clip)
        self.assertFalse(self.game._waiting.active)
        self.assertFalse(sequence.revealed)
        self.assertEqual(self.game._panel.score_labels['correct'].cget('text'), '0')
        self.until(lambda: sequence.revealed)
        self.assertEqual(self.game._panel.score_labels['correct'].cget('text'), '1')
        self.assertIn('Richtig', self.game._explanation.cget('text'))
        self.until(lambda: not sequence.busy)
        self.assertFalse(self.game._waiting.active)
        self.game.next_question()
        self.assertEqual(sequence.visible_answers, 0)
        self.assertTrue(all(not b.winfo_manager() for b in self.game.answers))

    def test_question_and_short_answer_remain_visible_past_brisk_game_deadlines(self):
        sequence = self.game._sequence
        assert sequence is not None
        question = replace(
            sequence.game.current,
            text=('Welcher Planet wird wegen seiner Farbe '
                  'oft als Roter Planet bezeichnet?'),
            answers=tuple(replace(a, text=f'Option {i + 1}')
                          for i, a in enumerate(sequence.game.current.answers)),
        )
        sequence.game.questions = (question, *sequence.game.questions[1:])
        self.until(lambda: sequence.question_visible)
        bubble = self.pet._speech.bubble
        assert bubble is not None
        self.clock.advance(GAME_PACING.text_ms(question.text) / 1000)
        self.assertIs(self.pet._speech.bubble, bubble)
        self.assertEqual(sequence.visible_answers, 0)
        self.assertTrue(sequence.busy)
        self.until(lambda: sequence.visible_answers == 1)
        bubble = self.pet._speech.bubble
        assert bubble is not None
        self.clock.advance(.8)
        self.assertIs(self.pet._speech.bubble, bubble)
        self.assertEqual(sequence.visible_answers, 1)
        self.assertFalse(sequence.answer(question.correct_answer_id))
        self.until(lambda: not sequence.busy)
        self.assertEqual(sequence.visible_answers, 4)
        self.assertTrue(sequence.answer(question.correct_answer_id))

    def test_close_mid_moderation_cancels_speech_props_and_unfinished_receipt(self):
        self.clock.advance(7)
        sequence = self.game._sequence
        assert sequence is not None
        self.game.close()
        after = self.pet.state.fun
        self.clock.advance(80)
        self.assertLessEqual(self.pet.state.fun, after)
        self.assertEqual(sequence.game.rounds_completed, 0)
        self.assertIsNone(sequence._timer)
        assert self.game._effects is not None
        self.assertEqual(self.game._effects._windows, {})
        self.assertFalse(self.pet._animated.game_mode)
        self.assertIsNone(self.pet._speech.bubble)
