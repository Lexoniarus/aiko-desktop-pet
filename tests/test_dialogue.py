"""No-network dialogue/voice regression tests for Aiko's desktop version."""

import json
import random
import unittest
from collections import Counter
from datetime import datetime
from tempfile import TemporaryDirectory
from pathlib import Path

from aiko_pet.personality.mind import AikoMind
from aiko_pet.personality.catalog import (
    ANIMATIONS,
    CATALOGUE,
    DialogueBook,
    EMOTION_LABELS,
    Line,
    Reaction,
)
from aiko_pet.pet.state import PetState
from aiko_pet.pet.routine import context_at


def require_reaction(value: Reaction | None) -> Reaction:
    """Fail immediately if an expected authored dialogue is unavailable."""
    assert value is not None, "Expected a dialogue reaction"
    return value


def ctx(day='2026-10-12', hour=15):
    timestamp = datetime.fromisoformat(f'{day}T{hour:02d}:00:00').astimezone().timestamp()
    return context_at(timestamp)


class VoiceCatalogueTests(unittest.TestCase):
    def setUp(self):
        self.book = DialogueBook.from_file(rng=random.Random(32))
        self.state = PetState()
        self.context = ctx()

    def test_authored_phrases_are_unique_and_german(self):
        self.assertGreaterEqual(len(self.book.lines), 150)
        self.assertEqual(len(self.book.lines), len({x.id for x in self.book.lines}))
        self.assertEqual(len(self.book.lines), len({x.text for x in self.book.lines}))
        self.assertTrue(all(x.text.strip() and x.animation in ANIMATIONS for x in self.book.lines))

    def test_no_academy_or_story_world_reference_in_dialogues(self):
        forbidden = ('academy', 'kobe', 'chronicles', 'unterricht', 'hausaufgaben')
        self.assertTrue(all(not any(f in x.text.lower() for f in forbidden) for x in self.book.lines))

    def test_every_important_interaction_has_several_reactions(self):
        counts = Counter(line.event for line in self.book.lines)
        for event in ('click_left', 'click_right', 'rapid_click', 'pet',
                      'feed_meal', 'feed_snack', 'play', 'sleep', 'wake',
                      'return', 'cursor_follow', 'idle', 'walk_pause'):
            with self.subTest(event=event):
                self.assertGreaterEqual(counts[event], 5)

    def test_animation_mapping_is_existing_original_assets(self):
        frames = Path(__file__).resolve().parents[1] / 'aiko_pet' / 'assets' / 'frames'
        self.assertTrue(all((frames / x.animation / '00.png').is_file() for x in self.book.lines))

    def test_rotation_avoids_immediately_repeating_with_fresh_lines(self):
        ids = [
            require_reaction(self.book.choose('click_left', 'calm', self.context, 100 + i)).line_id
            for i in range(6)
        ]
        self.assertEqual(len(ids), len(set(ids)))

    def test_weighted_selection_respects_period_and_emotion(self):
        morning = ctx(hour=8)
        response = self.book.choose('morning', 'calm', morning, 500)
        self.assertIsNotNone(response)
        self.assertIsNone(self.book.choose('morning', 'calm', ctx(hour=17), 501))
        self.assertIsNotNone(self.book.choose('night', 'calm', ctx(hour=0), 600))
        self.assertIsNone(self.book.choose('hungry', 'calm', morning, 500))
        self.assertIsNotNone(self.book.choose('hungry', 'hungry', morning, 500))

    def test_fallback_rotation_when_every_phrase_is_recent(self):
        for i in range(26):
            self.assertIsNotNone(self.book.choose('click_right', 'calm', self.context, 10+i))

    def test_missing_event_is_explicit(self):
        self.assertIsNone(self.book.choose('unknown', 'calm', self.context, 500))

    def test_malformed_lines_and_duplicate_ids_are_rejected(self):
        data = json.loads(CATALOGUE.read_text('utf-8'))
        data['lines'][0]['animation'] = 'teleport'
        with TemporaryDirectory() as tmp:
            file = Path(tmp) / 'voice.json'
            file.write_text(json.dumps(data), encoding='utf-8')
            with self.assertRaises(ValueError):
                DialogueBook.from_file(file)
        line = Line.parse(json.loads(CATALOGUE.read_text('utf-8'))['lines'][0])
        with self.assertRaises(ValueError):
            DialogueBook((line, line))


class EmotionTests(unittest.TestCase):
    def setUp(self):
        self.mind = AikoMind(rng=random.Random(8), started_at=10.0)
        self.state = PetState()
        self.context = ctx()

    def test_priority_sleep_rapid_click_tired_hungry_low_mood(self):
        self.assertEqual(self.mind.emotion(PetState(sleeping=True), 10), 'asleep')
        self.mind.irritated_until = 100
        self.assertEqual(self.mind.emotion(self.state, 50), 'irritated')
        self.assertEqual(self.mind.emotion(PetState(energy=7), 101), 'tired')
        self.assertEqual(self.mind.emotion(PetState(satiety=14), 101), 'hungry')
        self.assertEqual(self.mind.emotion(PetState(mood=12), 101), 'withdrawn')
        self.assertEqual(self.mind.emotion(PetState(mood=97), 101), 'playful')
        self.assertEqual(self.mind.emotion(self.state, 101), 'calm')
        self.assertTrue(all(EMOTION_LABELS.values()))

    def test_rising_click_pressure_changes_reaction(self):
        events = [require_reaction(self.mind.click('left', self.state, self.context, t)).event for t in (11, 12, 13, 14)]
        self.assertEqual(events, ['click_left', 'click_left', 'click_notice', 'rapid_click'])
        self.assertEqual(self.mind.emotion(self.state, 15), 'irritated')
        self.assertEqual(require_reaction(self.mind.click('right', self.state, self.context, 30)).event, 'click_right')
        self.assertEqual(self.mind.emotion(self.state, 30), 'calm')

    def test_both_mouse_buttons_have_distinct_speech_triggers(self):
        left = self.mind.click('left', self.state, self.context, 20)
        right = self.mind.click('right', self.state, self.context, 22)
        assert left is not None
        assert right is not None
        self.assertEqual(left.event, 'click_left')
        self.assertEqual(right.event, 'click_right')
        self.assertNotEqual(left.text, right.text)

    def test_sleep_click_does_not_wake(self):
        self.state.sleeping = True
        reaction = self.mind.click('left', self.state, self.context, 20)
        assert reaction is not None
        self.assertEqual(reaction.event, 'sleep_click')
        self.assertTrue(self.state.sleeping)

    def test_pre_action_tone_preserved_and_warmth_temporary(self):
        self.assertEqual(self.mind.care_event('pet', self.state, self.context, 10), ('pet', 'calm'))
        self.mind.after_care('pet', 10)
        self.assertEqual(self.mind.emotion(self.state, 11), 'warm')
        self.assertEqual(self.mind.emotion(self.state, 81), 'calm')

    def test_feeding_uses_meal_snack_full(self):
        breakfast = ctx(hour=8)
        self.assertEqual(self.mind.care_event('feed', self.state, breakfast, 20)[0], 'feed_meal')
        self.state.meals_date = breakfast.day_key
        self.state.meals_today = ['breakfast']
        self.assertEqual(self.mind.care_event('feed', self.state, breakfast, 21)[0], 'feed_snack')
        self.state.satiety = 99
        self.assertEqual(self.mind.care_event('feed', self.state, breakfast, 22)[0], 'feed_full')

    def test_playing_and_sleeping_emit_appropriate_events(self):
        self.assertEqual(self.mind.care_event('play', self.state, self.context, 20)[0], 'play')
        self.state.energy = 6
        self.assertEqual(self.mind.care_event('play', self.state, self.context, 22)[0], 'play_tired')
        self.assertEqual(self.mind.care_event('sleep', self.state, self.context, 23)[0], 'sleep')
        self.state.sleeping = True
        self.assertEqual(self.mind.care_event('sleep', self.state, self.context, 24)[0], 'wake')

    def test_return_triggers_only_after_absence(self):
        self.assertIsNone(self.mind.return_to_pet(self.state, self.context, 100))
        reaction = self.mind.return_to_pet(self.state, self.context, 100 + 26*60)
        assert reaction is not None
        self.assertEqual(reaction.event, 'return')
        self.assertIsNone(self.mind.return_to_pet(self.state, self.context, 100 + 27*60))
        self.state.sleeping = True
        self.assertIsNone(self.mind.return_to_pet(self.state, self.context, 100 + 55*60))

    def test_spontaneous_comment_is_suppressed_during_sleep(self):
        self.state.sleeping = True
        self.assertIsNone(self.mind.spontaneous_event(self.state, self.context, 30))
        self.state.sleeping = False
        self.assertIsNotNone(self.mind.spontaneous_event(self.state, self.context, 31))

    def test_hungry_tired_and_low_mood_have_specific_comments(self):
        self.assertEqual(require_reaction(self.mind.spontaneous_event(PetState(satiety=5), self.context, 10)).event, 'hungry')
        self.assertEqual(require_reaction(self.mind.spontaneous_event(PetState(energy=5), self.context, 20)).event, 'tired')
        self.assertEqual(require_reaction(self.mind.spontaneous_event(PetState(mood=5), self.context, 30)).event, 'low_mood')


if __name__ == '__main__':
    unittest.main()
