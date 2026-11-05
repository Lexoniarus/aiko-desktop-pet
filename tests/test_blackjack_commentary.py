"""Casino commentary stays readable and yields to gameplay without a backlog."""
import unittest
from unittest.mock import Mock

from aiko_pet.presentation.games.blackjack_commentary import BlackjackCommentary
from tools.reaction_test_support import FakeScheduler


class BlackjackCommentaryTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeScheduler()
        self.say, self.emote = Mock(), Mock()
        self.express, self.silence = Mock(), Mock()
        self.speech = BlackjackCommentary(
            schedule=self.clock.schedule, cancel=self.clock.cancel,
            say=self.say, emote=self.emote, express=self.express, silence=self.silence,
        )

    def finish(self):
        token = self.speech._timer
        assert token is not None
        self.clock.fire(token)

    def test_phrase_result_aside_and_one_emoji_finish_without_replay(self):
        self.speech.cue('stand', 'Eine ausführliche Ansage. ' * 4)
        token = self.speech._timer
        self.speech.cue('reveal', 'Diese alte Ansage ist inzwischen überholt.')
        self.speech.result('win', 'Du hast gewonnen.', 'Das war mein Casinoauftritt.')
        self.assertEqual(self.speech._timer, token)
        self.say.assert_called_once()
        self.assertGreater(self.say.call_args.args[1], 3000)
        self.finish()
        self.assertEqual(self.say.call_args.args[0], 'Du hast gewonnen.')
        self.finish()
        self.assertEqual(self.say.call_args.args[0], 'Das war mein Casinoauftritt.')
        self.finish()
        self.emote.assert_called_once_with('star', 450)
        self.finish()
        self.assertFalse(self.speech.active)
        self.assertEqual(self.say.call_count, 3)
        self.assertEqual(self.clock.callbacks, {})

    def test_new_hand_keeps_current_phrase_but_drops_unheard_old_aside(self):
        self.speech.result('win', 'Du hast gewonnen.', 'Ein alter Nachsatz.')
        current = self.speech._timer
        self.speech.clear_pending()
        self.assertEqual(self.speech._timer, current)
        self.silence.assert_not_called()
        self.finish()
        self.say.assert_called_once()
        self.assertFalse(self.speech.active)
        self.emote.assert_not_called()

    def test_player_action_and_close_cancel_old_text_and_emoji_callbacks(self):
        self.speech.result('win', 'Du hast gewonnen.', 'Ein alter Nachsatz.')
        token = self.speech._timer
        assert token is not None
        stale = self.clock.callbacks[token][1]
        self.speech.interrupt()
        self.speech.cue('stand', 'Dein neuer Zug.')
        current = self.speech._timer
        stale()
        self.assertEqual(self.speech._timer, current)
        self.assertEqual(self.say.call_args.args[0], 'Dein neuer Zug.')
        self.emote.assert_not_called()
        self.silence.assert_called_once()
        self.speech.interrupt()
        self.assertEqual(self.clock.callbacks, {})
