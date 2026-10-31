"""Regression for persistent optimism despite a low actual mood and needs."""

import unittest

from aiko_pet.application.read_snapshot import snapshot_pet
from aiko_pet.infrastructure.character_mind import make_aiko_mind
from aiko_pet.pet.animation.expression import Expression, mood_expression
from aiko_pet.pet.emotions import EmotionalState, derive_emotional_state
from aiko_pet.pet.moodlet_catalog import MOODLET_CATALOG
from aiko_pet.pet.moodlets import (
    EmotionalDirection,
    MoodletEpisode,
    MoodletId,
    MoodletState,
)
from aiko_pet.pet.routine import context_at
from aiko_pet.pet.state import PetState


def episodes(*items):
    return tuple(MoodletEpisode(i + 1, key, level, 0, i, 7200)
                 for i, (key, level) in enumerate(items))


class EmotionalBaseMoodTests(unittest.TestCase):
    def derive(self, mood, *items):
        return derive_emotional_state(mood, episodes(*items),
                                      definitions=MOODLET_CATALOG.definitions)

    def test_three_long_term_bonuses_cannot_override_low_or_neutral_actual_mood(self):
        items = ((MoodletId.APPRECIATED, 1), (MoodletId.OPTIMISTIC, 2),
                 (MoodletId.TRUSTING, 1))
        for mood, expected in ((35, EmotionalState.SUBDUED),
                               (55, EmotionalState.CALM),
                               (85, EmotionalState.OPTIMISTIC)):
            with self.subTest(mood=mood):
                result = self.derive(mood, *items)
                self.assertEqual(result.primary, expected)
                self.assertEqual(result.positive_intensity, 4)
                self.assertEqual(len(result.influences), 3)
                self.assertIn((EmotionalDirection.OPTIMISTIC, 2), result.directions)

    def test_live_state_shape_keeps_causes_and_shared_read_only_interpretation(self):
        state = PetState(mood=35, fun=15, energy=88, satiety=77,
                         moodlets=MoodletState(active=episodes(
                             (MoodletId.APPRECIATED, 1), (MoodletId.OPTIMISTIC, 2),
                             (MoodletId.TRUSTING, 1), (MoodletId.UNSTIMULATED, 1),
                             (MoodletId.CONNECTION, 1), (MoodletId.POKING, 1),
                         )))
        before = state.capture_checkpoint()
        mind = make_aiko_mind(started_at=0)
        read = snapshot_pet(state)
        dialogue = mind.dialogue_context(state, context_at(1_800_000_000), 1)
        self.assertEqual(read.emotions.primary, EmotionalState.IRRITATED)
        self.assertEqual(dialogue.emotions, read.emotions)
        self.assertEqual(mind.emotional_state(state), read.emotions)
        self.assertEqual(state.capture_checkpoint(), before)
        self.assertEqual(len(read.emotions.influences), 6)

    def test_diverse_states_require_the_base_and_matching_modifiers(self):
        cases = (
            (20, (), EmotionalState.SUBDUED),
            (60, (), EmotionalState.CALM),
            (80, (), EmotionalState.SATISFIED),
            (60, ((MoodletId.CHEERFUL, 2),), EmotionalState.CHEERFUL),
            (60, ((MoodletId.PRIDE, 2),), EmotionalState.PROUD),
            (60, ((MoodletId.RELIEF, 2),), EmotionalState.RELIEVED),
            (60, ((MoodletId.CONNECTION, 2),), EmotionalState.AFFECTIONATE),
            (80, ((MoodletId.OPTIMISTIC, 2),), EmotionalState.OPTIMISTIC),
            (80, ((MoodletId.CHEERFUL, 2), (MoodletId.TRUSTING, 2)),
             EmotionalState.CAREFREE),
            (20, ((MoodletId.POKING, 1),), EmotionalState.IRRITATED),
            (60, ((MoodletId.CROWDED, 2),), EmotionalState.CROWDED),
            (20, ((MoodletId.UNSTIMULATED, 1),), EmotionalState.FRUSTRATED),
            (20, ((MoodletId.HUNGER_WORN, 1),), EmotionalState.DOWNCAST),
            (20, ((MoodletId.LONELY, 1),), EmotionalState.LONELY),
            (60, ((MoodletId.PRIDE, 2), (MoodletId.POKING, 2)),
             EmotionalState.AMBIVALENT),
            (20, ((MoodletId.GUARDED, 2),), EmotionalState.RESERVED),
            (60, ((MoodletId.CURSOR_FEAR, 2),), EmotionalState.TENSE),
        )
        self.assertEqual({expected for _, _, expected in cases}, set(EmotionalState))
        for mood, items, expected in cases:
            with self.subTest(mood=mood, expected=expected):
                self.assertEqual(self.derive(mood, *items).primary, expected)

    def test_background_warmth_is_neutral_at_rest_and_joy_is_distinct(self):
        for feeling in (EmotionalState.SATISFIED, EmotionalState.AFFECTIONATE,
                        EmotionalState.OPTIMISTIC, EmotionalState.RELIEVED):
            self.assertEqual(mood_expression(feeling), Expression.NEUTRAL)
        for feeling in (EmotionalState.CHEERFUL, EmotionalState.CAREFREE,
                        EmotionalState.PROUD):
            self.assertEqual(mood_expression(feeling), Expression.POSITIVE)
