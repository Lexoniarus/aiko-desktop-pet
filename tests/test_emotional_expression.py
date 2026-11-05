"""Status, dialogue and idle/click expression use one emotional interpretation."""

import unittest

from aiko_pet.application.read_snapshot import snapshot_pet
from aiko_pet.infrastructure.character_mind import make_aiko_mind
from aiko_pet.pet.animation.idle_emote import choose_idle_emote
from aiko_pet.pet.emotions import EmotionalState
from aiko_pet.pet.mind.adaptive_models import Behaviour
from aiko_pet.pet.mind.dialogue_context import SituationalCondition
from aiko_pet.pet.moodlets import MoodletEpisode, MoodletId, MoodletState
from aiko_pet.pet.routine import context_at
from aiko_pet.pet.state import PetState


class EmotionalExpressionTests(unittest.TestCase):
    def emote(self, state, mind):
        return choose_idle_emote(
            energy=state.energy,
            satiety=state.satiety,
            affection=state.affection,
            mood=state.mood,
            emotions=mind.emotional_state(state),
        )

    def test_normal_good_care_reaches_positive_expression(
        self,
    ):
        state = PetState(mood=75)
        mind = make_aiko_mind(started_at=0)
        context = mind.dialogue_context(state, context_at(1_800_000_000), 1)
        self.assertIn(SituationalCondition.PLAYFUL, context.situational_conditions)
        self.assertEqual(context.emotions.primary, EmotionalState.SATISFIED)
        self.assertEqual(self.emote(state, mind), "star")

    def test_negative_impression_prevents_cheerful_expression_at_high_mood(
        self,
    ):
        state = PetState(
            mood=95,
            moodlets=MoodletState(
                active=(MoodletEpisode(1, MoodletId.CROWDED, 2, 0, 0, 7200),)
            ),
        )
        mind = make_aiko_mind(started_at=0)
        context = mind.dialogue_context(state, context_at(1_800_000_000), 1)
        self.assertEqual(context.emotions, snapshot_pet(state).emotions)
        self.assertEqual(context.emotions.primary, EmotionalState.CROWDED)
        self.assertNotIn(SituationalCondition.PLAYFUL, context.situational_conditions)
        self.assertEqual(self.emote(state, mind), "anger")
        reactions = [mind.click("left", state, context.time, now) for now in range(3)]
        reaction = reactions[-1]
        assert reaction
        self.assertEqual(reaction.event, "click_notice")

    def test_hardware_and_friendship_do_not_invent_offense_or_exhaustion(
        self,
    ):
        state = PetState(mood=75, energy=90, friendship=50)
        mind = make_aiko_mind(started_at=0)
        mind.set_situation(Behaviour("present", 99, 0.9, None, False, True, 12, 0, 0))
        context = mind.dialogue_context(state, context_at(1_800_000_000), 1)
        self.assertEqual(context.emotions.primary, EmotionalState.SATISFIED)
        self.assertNotIn(SituationalCondition.FATIGUED, context.situational_conditions)
        reaction = mind.click("left", state, context.time, 1)
        assert reaction
        self.assertNotEqual(reaction.event, "click_sleepy")
        self.assertEqual(self.emote(state, mind), "star")

    def test_physical_shortage_remains_visible_even_during_a_positive_impression(self):
        state = PetState(
            satiety=0,
            mood=75,
            moodlets=MoodletState(
                active=(MoodletEpisode(1, MoodletId.PRIDE, 1, 0, 0, 7200),)
            ),
        )
        self.assertEqual(self.emote(state, make_aiko_mind(started_at=0)), "drops")
