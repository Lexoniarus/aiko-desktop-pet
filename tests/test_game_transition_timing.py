"""One visible reaction phase and cancellation of superseded game callbacks."""
import unittest
from unittest.mock import Mock

from aiko_pet.games.quiz import QuizSession
from aiko_pet.games.quiz_catalogue import QuizCatalogue
from aiko_pet.ui.windows.game_waiting import GameWaiting
from aiko_pet.ui.windows.quiz_sequence import QuizSequence
from tools.reaction_test_support import FakeScheduler


class GameTransitionTimingTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeScheduler()
        self.say, self.emote = Mock(), Mock()
        self.dialogue = Mock(return_value='A' * 100)

    def test_old_wait_callback_cannot_erase_new_wait_after_answer_and_restart(self):
        waiting = GameWaiting(self.clock.schedule, self.clock.cancel, None,
                              lambda: (0, 0), Mock())
        waiting.set_active(True)
        token = waiting._timer
        assert token is not None
        stale = self.clock.callbacks[token][1]
        waiting.set_active(False)
        waiting.set_active(True)
        current = waiting._timer
        assert current is not None
        stale()
        self.assertEqual(waiting._timer, current)
        self.assertEqual(waiting._step, 0)
        self.clock.fire(current)
        self.assertEqual(waiting._step, 1)
        waiting.set_active(False)
        self.assertEqual(self.clock.callbacks, {})

    def test_old_quiz_reading_cannot_erase_or_repeat_current_phase(self):
        sequence = QuizSequence(
            QuizSession(QuizCatalogue.load()), schedule=self.clock.schedule,
            cancel=self.clock.cancel, present=Mock(), say=self.say,
            animate=Mock(), emote=self.emote,
        )
        self.addCleanup(sequence.close)
        previous, current = Mock(), Mock()
        sequence._later(1000, previous)
        token = sequence._timer
        assert token is not None
        stale = self.clock.callbacks[token][1]
        sequence._later(750, current)
        token = sequence._timer
        assert token is not None
        callback = self.clock.callbacks[token][1]
        stale()
        self.assertEqual(sequence._timer, token)
        previous.assert_not_called()
        self.clock.fire(token)
        callback()
        current.assert_called_once()
        self.assertIsNone(sequence._timer)
