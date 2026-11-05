"""One visible reaction phase and cancellation of superseded game callbacks."""
import unittest
from unittest.mock import Mock

from aiko_pet.ui.windows.game_commentary import GameCommentary
from tools.reaction_test_support import FakeScheduler


class GameCommentaryTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeScheduler()
        self.say, self.emote = Mock(), Mock()
        self.dialogue = Mock(return_value='A' * 100)
        self.comments = GameCommentary(
            schedule=self.clock.schedule, cancel=self.clock.cancel,
            say=self.say, emote=self.emote, dialogue=self.dialogue, express=Mock(),
        )

    def test_same_assessment_finishes_once_before_one_emoji_without_replay(self):
        duration = self.comments.event('balanced')
        token = next(iter(self.clock.callbacks))
        self.comments.event('balanced', 'question')
        self.assertEqual(list(self.clock.callbacks), [token])
        self.say.assert_called_once_with('A' * 100, duration)
        self.dialogue.assert_called_once_with('balanced')
        self.assertTrue(self.comments.active)
        self.clock.fire(token)
        self.emote.assert_called_once_with('question', 450)
        self.assertTrue(self.comments.active)
        self.clock.fire(next(iter(self.clock.callbacks)))
        self.assertFalse(self.comments.active)
        self.assertEqual(self.comments._timers, [])
        self.say.assert_called_once()

    def test_old_comment_and_gaze_callbacks_cannot_return_in_next_move(self):
        self.comments.event('old', 'question')
        look = Mock()
        self.comments.later(1800, look)
        stale = [fn for _, fn in self.clock.callbacks.values()]
        self.comments.event('new', 'star')
        expected = list(self.clock.callbacks)
        for fn in stale:
            fn()
        self.assertEqual(list(self.clock.callbacks), expected)
        self.assertTrue(self.comments.active)
        self.emote.assert_not_called()
        look.assert_not_called()
        token = expected[0]
        callback = self.clock.callbacks[token][1]
        self.clock.fire(token)
        callback()
        self.emote.assert_called_once_with('star', 450)
