"""Local catalogue, stable answers and noncompetitive quiz completion."""

import copy
import json
import random
import tempfile
import unittest
from collections import Counter
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock

from aiko_pet.application.active_time import ActiveSessionClock, SessionInputs
from aiko_pet.application.game_experience import GameExperienceCoordinator
from aiko_pet.games.contracts import GameId, GameRoundEvent, SessionSummary
from aiko_pet.games.quiz import QuizSession
from aiko_pet.games.quiz_catalogue import QuizCatalogue
from aiko_pet.infrastructure.character_mind import make_aiko_mind
from aiko_pet.infrastructure.pet_codec import decode_pet_state, encode_pet_state
from aiko_pet.pet.fun import GameExperience
from aiko_pet.pet.mind.adaptive import AdaptiveRoutine
from aiko_pet.pet.moodlets import MoodletId, MoodletOutcome
from aiko_pet.pet.needs import NeedLevels
from aiko_pet.pet.state import PetState
from aiko_pet.pet.wish_catalog import WISH_CATALOG
from aiko_pet.pet.wish_selection import replenish_wishes
from aiko_pet.pet.wishes import (
    ActiveWish,
    WishContext,
    WishId,
    WishState,
)
from aiko_pet.ui.windows.quiz_sequence import QuizSequence

ROOT = Path(__file__).resolve().parents[1]
WALL = 1800000000.0


class QuizTests(unittest.TestCase):
    def setUp(self):
        self.catalogue = QuizCatalogue.load()

    def test_reviewed_catalogue_identity_distribution_and_content(self):
        source = json.loads((ROOT / 'docs/quiz/catalogue.de.json').read_text('utf-8'))
        self.assertEqual(len(self.catalogue.questions), 200)
        self.assertEqual(Counter(q.topic for q in self.catalogue.questions),
                         source['targets']['topic_counts'])
        self.assertEqual(Counter(q.difficulty for q in self.catalogue.questions),
                         {'easy': 100, 'medium': 70, 'tricky': 30})
        for q, original in zip(self.catalogue.questions, source['questions']):
            self.assertEqual((q.id, q.revision, q.text, q.correct_answer_id),
                             (original['id'], original['revision'],
                              original['question'], original['correct_answer_id']))
            self.assertEqual([(a.id, a.text) for a in q.answers],
                             [(a['id'], a['text']) for a in original['answers']])

    def test_loader_rejects_ambiguous_unapproved_missing_and_duplicate_content(self):
        original = json.loads((ROOT / 'aiko_pet/data/quiz.de.json').read_text('utf-8'))
        for defect in ('duplicate', 'choices', 'solution', 'approval', 'short'):
            raw = copy.deepcopy(original)
            row = raw['questions'][0]
            if defect == 'duplicate':
                raw['questions'][1] = copy.deepcopy(row)
            elif defect == 'choices':
                row['answers'][1]['text'] = row['answers'][0]['text']
            elif defect == 'solution':
                row['correct_answer_id'] = 'absent'
            elif defect == 'approval':
                row['editorial_status'] = 'draft'
            else:
                raw['questions'] = raw['questions'][:9]
            with self.subTest(defect=defect), tempfile.TemporaryDirectory() as temp:
                path = Path(temp) / 'quiz.json'
                path.write_text(json.dumps(raw), encoding='utf-8')
                with self.assertRaises(ValueError):
                    QuizCatalogue.load(path)

    def test_selection_shuffle_and_one_answer_per_question(self):
        for seed in range(20):
            game = QuizSession(self.catalogue, random.Random(seed))
            self.assertEqual(len({q.id for q in game.questions}), 10)
            self.assertGreaterEqual(len({q.topic for q in game.questions}), 7)
            for index in range(10):
                q = game.current
                with self.assertRaises(ValueError):
                    game.answer('foreign-id')
                game.answer(q.correct_answer_id)
                with self.assertRaises(ValueError):
                    game.answer(q.correct_answer_id)
                if index < 9:
                    game.advance()
            self.assertEqual((game.correct, game.rounds_completed), (10, 1))
            first = {q.id for q in game.questions}
            game.new_round()
            self.assertFalse(first & {q.id for q in game.questions})
            self.assertEqual(game.correct, 0)

    def test_final_resolution_precedes_completion_and_close_is_cancellable(self):
        calls = []
        scheduled = []
        game = QuizSession(self.catalogue, random.Random(1))
        sequence = QuizSequence(
            game, schedule=lambda _delay, fn: scheduled.append(fn) or 'pending',
            cancel=Mock(), present=lambda: calls.append(('view', game.finished)),
            say=Mock(), animate=Mock(), emote=Mock(), dialogue=lambda e: e,
            round_event=lambda e: calls.append(('event', e)),
        )
        sequence.greet()
        scheduled.pop()()
        for index in range(10):
            wrong = next(a.id for a in game.current.answers
                         if a.id != game.current.correct_answer_id)
            self.assertTrue(sequence.answer(wrong))
            self.assertFalse(sequence.answer(wrong))
            if index < 9:
                scheduled.pop()()
                sequence.advance()
        event_index = next(i for i, c in enumerate(calls)
                           if c[0] == 'event' and c[1].outcome == 'completed')
        self.assertEqual(calls[event_index - 1], ('view', True))
        self.assertEqual(game.correct, 0)
        sequence.close()
        for fn in scheduled:
            fn()
        self.assertEqual(sum(c[0] == 'event' and c[1].outcome == 'completed'
                             for c in calls), 1)

    def test_noncompetitive_contract_cannot_report_win_or_draw(self):
        with self.assertRaises(ValueError):
            SessionSummary(GameId.QUIZ, wins=1)
        with self.assertRaises(ValueError):
            GameExperience('quiz', 1, neutral_units=1)
        for outcome in ('win', 'loss', 'draw'):
            with self.assertRaises(ValueError):
                GameRoundEvent(GameId.QUIZ, 's', 1, outcome)


class QuizCareTests(unittest.TestCase):
    def setUp(self):
        self.pet = PetState(updated_at=WALL, lived_seconds=100, fun=30, friendship=50)
        self.inputs = SessionInputs(WALL, 0, False, None, False, False, None)
        self.coordinator = self.make_coordinator()

    def make_coordinator(self):
        return GameExperienceCoordinator(
            self.pet, make_aiko_mind(started_at=0), AdaptiveRoutine(),
            clock=ActiveSessionClock(lambda: 0),
        )

    def round(self, number=1, session='s'):
        start = GameRoundEvent(GameId.QUIZ, session, number)
        self.coordinator.observe_round(start, self.inputs)
        self.coordinator.observe_round(replace(start, outcome='completed'), self.inputs)
        return start

    def install(self, key, target):
        definition = WISH_CATALOG.definitions[key]
        typed = definition.bind_target(target)
        wish = ActiveWish(1, key, target or '', 0, 1000,
                          goal=definition.goal_for_target(typed), target=typed)
        self.pet.restore_checkpoint(replace(self.pet.capture_checkpoint(),
                                           wishes=WishState(2, (wish,))))

    def test_named_quiz_wish_needs_one_round_and_survives_save_without_draw(self):
        self.install(WishId.PLAY_GAME, 'quiz')
        self.assertEqual(self.pet.wishes.active[0].goal_snapshot.required_count, 1)
        start = self.round()
        self.assertEqual(self.pet.fun, 39)
        self.assertFalse(self.pet.wishes.active)
        episode = next(e for e in self.pet.moodlets.active
                       if e.definition_id == MoodletId.SHARED_PLAY)
        self.assertEqual(episode.causes[0].outcome, MoodletOutcome.COMPLETED)
        self.pet = decode_pet_state(encode_pet_state(self.pet), now=WALL)
        self.coordinator = self.make_coordinator()
        before = self.pet.capture_checkpoint()
        self.coordinator.observe_round(start, self.inputs)
        self.coordinator.observe_round(replace(start, outcome='completed'), self.inputs)
        self.assertEqual(self.pet.capture_checkpoint(), before)

    def test_any_game_accumulates_quiz_and_competitive_round(self):
        self.install(WishId.PLAY_ANY_GAME, None)
        self.round()
        self.assertEqual(self.pet.wishes.active[0].game.completed_rounds, 1)
        self.pet = decode_pet_state(encode_pet_state(self.pet), now=WALL)
        self.coordinator = self.make_coordinator()
        start = GameRoundEvent(GameId.BLACKJACK, 'cards', 1)
        self.coordinator.observe_round(start, self.inputs)
        self.coordinator.observe_round(replace(start, outcome='loss'), self.inputs)
        self.assertFalse(self.pet.wishes.active)

    def test_abandoned_round_and_new_later_wish_cannot_receive_completion(self):
        start = GameRoundEvent(GameId.QUIZ, 's', 1)
        self.coordinator.observe_round(start, self.inputs)
        self.install(WishId.PLAY_GAME, 'quiz')
        self.coordinator.complete(GameExperience('quiz', 0), self.inputs)
        self.coordinator.observe_round(replace(start, outcome='completed'), self.inputs)
        self.assertEqual(self.pet.fun, 30)
        self.assertTrue(self.pet.wishes.active)

    def test_window_session_cap_and_duplicate_receipts(self):
        for number in range(1, 6):
            start = self.round(number)
            before = self.pet.capture_checkpoint()
            self.coordinator.observe_round(
                replace(start, outcome='completed'), self.inputs,
            )
            self.assertEqual(self.pet.capture_checkpoint(), before)
        self.assertEqual(self.pet.fun, 50)
        self.coordinator.complete(GameExperience('quiz', 0), self.inputs)
        self.assertEqual(self.pet.fun, 50)

    def test_started_round_does_not_adopt_a_later_wish(self):
        start = GameRoundEvent(GameId.QUIZ, 'later', 1)
        self.coordinator.observe_round(start, self.inputs)
        self.install(WishId.PLAY_GAME, 'quiz')
        self.coordinator.observe_round(replace(start, outcome='completed'), self.inputs)
        self.assertEqual(self.pet.fun, 39)
        self.assertEqual(self.pet.wishes.active[0].game.completed_rounds, 0)

    def test_exact_wish_completion_does_not_also_progress_general_wish(self):
        self.install(WishId.PLAY_GAME, 'quiz')
        exact = self.pet.wishes.active[0]
        definition = WISH_CATALOG.definitions[WishId.PLAY_ANY_GAME]
        general = ActiveWish(2, definition.id, '', 0, 1000,
                             goal=definition.goal, target=definition.bind_target())
        self.pet.restore_checkpoint(replace(self.pet.capture_checkpoint(),
                                           wishes=WishState(3, (exact, general))))
        self.round()
        self.assertEqual(len(self.pet.wishes.active), 1)
        self.assertEqual(self.pet.wishes.active[0].instance_id, 2)
        self.assertEqual(self.pet.wishes.active[0].game.completed_rounds, 0)

    def test_nonloss_wish_is_not_completed_or_failed_by_quiz(self):
        self.install(WishId.AVOID_ROUND_LOSS, 'blackjack')
        self.round()
        self.assertEqual(self.pet.wishes.active[0].game.completed_rounds, 0)
        self.assertFalse(any(e.definition_id in (MoodletId.RELIEF,
                                                MoodletId.DISAPPOINTED)
                             for e in self.pet.moodlets.active))

    def test_high_fun_reduction_applies_to_a_completed_quiz(self):
        self.pet.restore_checkpoint(replace(self.pet.capture_checkpoint(), fun=90))
        self.round()
        self.assertAlmostEqual(self.pet.fun, 98.25)
        self.coordinator.complete(GameExperience('quiz', 0), self.inputs)
        self.assertAlmostEqual(self.pet.fun, 98.25)

    def test_quiz_cannot_create_or_complete_competitive_wishes(self):
        for key in (WishId.WIN_ROUND, WishId.AVOID_ROUND_LOSS, WishId.REMATCH_GAME):
            self.assertNotIn('quiz', WISH_CATALOG.definitions[key].targets)
        definition = WISH_CATALOG.definitions[WishId.PLAY_GAME]
        # Force selection to exercise the actual creation path for a named quiz.
        definition = replace(definition, targets=('quiz',))
        wishes = replenish_wishes(
            WishState(), elapsed=100, sleeping=False,
            needs=NeedLevels(50, 50, 50, 50, 50),
            context=WishContext(), definitions={WishId.PLAY_GAME: definition},
            rng=random.Random(1),
        )
        self.assertEqual(len(wishes.active), 1)
        self.assertEqual(wishes.active[0].goal_snapshot.required_count, 1)


if __name__ == '__main__':
    unittest.main()
