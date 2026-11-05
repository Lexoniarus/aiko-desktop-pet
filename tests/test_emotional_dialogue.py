"""Overall impressions, care conditions and immediate reactions stay independent."""

import unittest
from dataclasses import replace

from aiko_pet.infrastructure.character_mind import make_aiko_mind
from aiko_pet.pet.emotions import EmotionalState
from aiko_pet.pet.mind.catalog import Line
from aiko_pet.pet.mind.dialogue_context import DialogueConditions, ReactionTone
from aiko_pet.pet.moodlets import (
    EmotionalDirection,
    MoodletEpisode,
    MoodletId,
    MoodletState,
)
from aiko_pet.pet.needs import NeedCondition
from aiko_pet.pet.routine import context_at
from aiko_pet.pet.state import PetState


class EmotionalDialogueTests(unittest.TestCase):
    def test_need_and_reaction_do_not_replace_lasting_emotional_composition(self):
        state = PetState(
            satiety=10,
            mood=80,
            moodlets=MoodletState(
                active=(MoodletEpisode(1, MoodletId.PRIDE, 2, 0, 0, 3600),)
            ),
        )
        mind = make_aiko_mind(started_at=0)
        mind.note_object_withholding(10)
        context = mind.dialogue_context(state, context_at(1_800_000_000), 11)
        self.assertEqual(context.emotions.primary, EmotionalState.PROUD)
        self.assertIn(NeedCondition.LOW_SATIETY, context.need_conditions)
        self.assertEqual(context.reaction_tone, ReactionTone.IRRITATED)
        hungry = DialogueConditions(
            need_conditions=frozenset({NeedCondition.LOW_SATIETY})
        )
        irritated = DialogueConditions(
            reaction_tones=frozenset({ReactionTone.IRRITATED})
        )
        self.assertTrue(hungry.matches(context))
        self.assertTrue(irritated.matches(context))
        later = mind.dialogue_context(state, context.time, 10_000)
        self.assertIsNone(later.reaction_tone)
        self.assertEqual(later.emotions, context.emotions)

    def test_sleep_clears_short_reaction_but_not_the_lasting_impression(self):
        state = PetState(
            moodlets=MoodletState(
                active=(MoodletEpisode(1, MoodletId.POKING, 2, 0, 0, 3600),)
            )
        )
        mind = make_aiko_mind(started_at=0)
        mind.note_object_withholding(10)
        mind.record_accepted_care("sleep", 11)
        self.assertIsNone(mind.reaction_tone(12))
        self.assertEqual(mind.emotional_state(state).primary, EmotionalState.IRRITATED)
        self.assertEqual(len(state.moodlets.active), 1)

    def test_secondary_directions_remain_available_for_combined_dialogue_filters(self):
        state = PetState(
            moodlets=MoodletState(
                active=(
                    MoodletEpisode(1, MoodletId.PRIDE, 2, 0, 0, 3600),
                    MoodletEpisode(2, MoodletId.POKING, 1, 0, 0, 3600),
                )
            )
        )
        context = make_aiko_mind(started_at=0).dialogue_context(
            state, context_at(1_800_000_000), 10
        )
        conditions = DialogueConditions(
            emotional_states=frozenset({EmotionalState.PROUD}),
            emotional_directions=frozenset({EmotionalDirection.IRRITATED}),
        )
        self.assertTrue(conditions.matches(context))
        self.assertFalse(replace(conditions, sleeping=True).matches(context))

    def test_catalogue_rejects_cross_layer_and_legacy_filter_names(self):
        original = make_aiko_mind(started_at=0).book.lines[0]
        raw = dict(
            id="typed",
            event=original.event,
            conditions=[],
            animation="idle",
            periods=[],
            weekdays=[],
            beats=[dict(kind="text", content="Hallo.")],
        )
        self.assertEqual(Line.parse(raw).id, "typed")
        for key, value in (
            ("moods", ["hungry"]),
            ("conditions", [{"emotional_states": ["hungry"]}]),
            ("conditions", [{"need_conditions": ["proud"]}]),
            ("conditions", [{"reaction_tones": ["lonely"]}]),
        ):
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                Line.parse(dict(raw, **{key: value}))
