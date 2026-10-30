"""Fingerduell phase boundaries, public reveal and cancelled recovery."""
import unittest

from aiko_pet.games.rock_paper_scissors import Move
from aiko_pet.ui.windows.rock_paper_scissors_sequence import RockPaperScissorsSequence
from tools.reaction_test_support import FakeScheduler


class RockPaperScissorsSequenceTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeScheduler()
        self.events, self.reveals, self.busy, self.rounds = [], [], [], []
        self.flow = RockPaperScissorsSequence(
            schedule=self.clock.schedule, cancel=self.clock.cancel,
            say=lambda value, ms: self.events.append(('text', value)),
            show_emote=lambda value, ms: self.events.append(('emote', value)),
            show_aiko_hand=lambda value, ms: self.events.append(('hand', value)),
            reveal_player=lambda move, score: self.reveals.append((move, score)),
            animate=lambda _: None, set_busy=self.busy.append,
            dialogue=lambda event: event, round_event=self.rounds.append,
        )

    def step(self):
        self.flow.advance()

    def test_words_and_reveal_occur_on_the_three_forward_markers(self):
        self.flow._game._random_index = lambda _: 2
        self.flow.choose(Move.ROCK)
        self.assertEqual(self.events, [])
        for index, word in enumerate(('Schere!', 'Stein!', 'Papier!')):
            self.step()
            self.assertIn(('text', word), self.events)
            self.assertEqual(self.flow.score.games, int(index == 2))
            if index < 2:
                self.assertTrue(self.flow.busy)
                self.step()
        self.assertFalse(self.flow.busy)
        self.assertEqual(self.busy, [True, False])
        self.assertEqual(self.events[-1], ('hand', Move.SCISSORS))
        self.assertEqual(self.reveals[0][1].wins, 1)
        self.assertEqual([e.outcome for e in self.rounds], [None, 'win'])
        self.assertEqual(self.rounds[0].identity, self.rounds[1].identity)
        self.step()
        self.assertEqual(self.events[-1], ('emote', 'drops'))
        self.step()
        self.assertEqual(self.events[-1], ('text', 'game_player_win'))
        self.assertEqual(len(self.reveals), 1)

    def test_all_nine_results_and_immediate_choice_after_reveal(self):
        for player in Move:
            for index in range(3):
                self.setUp()
                self.flow._game._random_index = lambda _, i=index: i
                self.flow.choose(player)
                for _ in range(5):
                    self.step()
                self.assertEqual(self.flow.score.games, 1)
                token = self.flow.pending_timer
                assert token is not None
                stale = self.clock.callbacks[token][1]
                self.flow.choose(Move.PAPER)
                self.assertTrue(self.flow.busy)
                stale()
                self.assertEqual(self.flow.score.games, 1)
                for _ in range(5):
                    self.step()
                self.assertEqual(self.flow.score.games, 2)
                self.assertEqual(len(self.reveals), 2)

    def test_duplicate_choice_before_reveal_and_close_do_not_score(self):
        self.flow.choose(Move.ROCK)
        token = self.flow.pending_timer
        assert token is not None
        stale = self.clock.callbacks[token][1]
        self.flow.choose(Move.PAPER)
        self.assertEqual(self.busy, [True])
        self.flow.close()
        stale()
        self.flow.choose(Move.SCISSORS)
        self.assertEqual(self.flow.score.games, 0)
        self.assertEqual(self.reveals, [])
        self.assertEqual(self.clock.callbacks, {})
