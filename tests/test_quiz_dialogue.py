"""The authored quizmaster voice respects relationship and emotional context."""

import unittest

from aiko_pet.pet.emotions import EmotionalComposition, EmotionalState
from aiko_pet.pet.mind.dialogue_context import DialogueContext, FriendshipStage
from aiko_pet.pet.routine import context_at
from aiko_pet.ui.windows.rock_paper_scissors_dialogue import GameDialogue


class QuizDialogueTests(unittest.TestCase):
    def context(self, stage, emotion=EmotionalState.CALM):
        return DialogueContext(stage, 60, EmotionalComposition(emotion),
                               context_at(1800000000))

    def test_quizmaster_introductions_follow_all_four_friendship_stages(self):
        voice = GameDialogue()
        introductions = {
            voice.choose('game_quiz_greeting', self.context(stage))
            for stage in FriendshipStage
        }
        self.assertEqual(len(introductions), 4)

    def test_downcast_and_irritated_voice_does_not_force_cheerful_banter(self):
        voice = GameDialogue()
        for emotion in (EmotionalState.DOWNCAST, EmotionalState.IRRITATED):
            line = voice.choose('game_quiz_correct',
                                self.context(FriendshipStage.CLOSE, emotion))
            self.assertEqual(line, 'Das ist richtig. Ein Punkt für dich.')


if __name__ == '__main__':
    unittest.main()
