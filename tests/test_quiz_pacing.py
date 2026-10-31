"""Quiz presentation gets reading time without changing brisk game cues."""
import unittest
from unittest.mock import Mock

from aiko_pet.games.quiz import QuizSession
from aiko_pet.games.quiz_catalogue import QuizCatalogue
from aiko_pet.ui.common.game_pacing import GAME_PACING
from aiko_pet.ui.windows.quiz_sequence import QuizSequence
from tools.reaction_test_support import FakeScheduler


class QuizPacingTests(unittest.TestCase):
    def test_short_options_and_full_bubbles_have_readable_bounded_time(self):
        self.assertEqual(GAME_PACING.quiz_text_ms('A: Mars'), 1400)
        self.assertEqual(GAME_PACING.text_ms('A: Mars'), 750)
        text = 'Eine Information. ' * 7
        self.assertGreaterEqual(GAME_PACING.quiz_text_ms(text), 4500)
        self.assertLessEqual(GAME_PACING.quiz_text_ms(text), 5000)
        self.assertLessEqual(GAME_PACING.text_ms(text), 3200)
        self.assertEqual(GAME_PACING.emote_ms, 450)

    def test_long_presentation_chunks_keep_their_full_reading_time_and_cancel(self):
        clock, say, done = FakeScheduler(), Mock(), Mock()
        sequence = QuizSequence(
            QuizSession(QuizCatalogue.load()), schedule=clock.schedule,
            cancel=clock.cancel, present=Mock(), say=say, animate=Mock(), emote=Mock(),
        )
        text = ('Das ist eine ausführliche Erklärung '
                'mit mehreren vollständigen Sätzen. ') * 5
        sequence._read(text, done)
        heard = []
        while clock.callbacks:
            line, duration = say.call_args.args
            self.assertGreater(duration, GAME_PACING.text_ms(line))
            token = sequence._timer
            assert token is not None
            self.assertEqual(clock.callbacks[token][0], duration)
            heard.append(line)
            clock.fire(token)
        self.assertEqual(' '.join(heard), text.strip())
        done.assert_called_once()
        sequence._read(text, done)
        token = sequence._timer
        assert token is not None
        stale = clock.callbacks[token][1]
        before = say.call_count
        sequence.close()
        stale()
        self.assertEqual(say.call_count, before)
        done.assert_called_once()
