"""Wish speech uses actual playback receipts, never queueing or fake contact."""

import random
import unittest
from dataclasses import replace
from unittest.mock import Mock, patch

from aiko_pet.application.attention import AttentionCoordinator
from aiko_pet.application.settings import PetSettings
from aiko_pet.infrastructure.character_mind import make_aiko_mind
from aiko_pet.infrastructure.pet_codec import decode_pet_state, encode_pet_state
from aiko_pet.pet.mind.catalog import Reaction
from aiko_pet.pet.mind.reaction_sequence import Cue
from aiko_pet.pet.mind.workload_events import WorkloadEventDetector
from aiko_pet.pet.moodlets import MoodletId
from aiko_pet.pet.routine import context_at
from aiko_pet.pet.state import PetState
from aiko_pet.pet.wish_catalog import WISH_CATALOG, WishCatalog
from aiko_pet.pet.wishes import ActiveWish, WishArea, WishId, WishState
from aiko_pet.ui.pet_view.reaction_player import ReactionPlayer
from tools.pet_test_support import set_test_pet_values
from tools.reaction_test_support import FakeScheduler


class WishExpressionTests(unittest.TestCase):
    def setUp(self):
        self.state = PetState(
            satiety=90,
            energy=90,
            fun=90,
            social=90,
            affection=90,
            mood=75,
            friendship=50,
            lived_seconds=100,
            updated_at=1800000000,
            wishes=WishState(
                2,
                (ActiveWish(1, WishId.FOOD, "apple", 0, 14400),),
                ((WishArea.FOOD, 0),),
            ),
        )
        self.settings = PetSettings()
        self.mind = make_aiko_mind(started_at=0, rng=random.Random(7))
        self.prepared = frozenset()
        self.attention = AttentionCoordinator(
            self.state,
            self.settings,
            self.mind,
            WorkloadEventDetector(),
            Mock(),
            Mock(),
            started_at=0,
            prepared_social=lambda: self.prepared,
        )
        self.attention.next_comment = 99999
        self.scheduler = FakeScheduler()
        self.shown = []
        self.player = ReactionPlayer(
            schedule=self.scheduler.schedule,
            cancel_timer=self.scheduler.cancel,
            display_text=lambda text, duration: self.shown.append(text),
            display_emote=lambda text, duration: None,
            start_action=lambda name, duration: None,
            mark_spoken=lambda: None,
            is_closed=lambda: False,
            on_wish_text=self.attention.note_wish_text,
        )

    def select(self, **kwargs):
        return self.attention.spontaneous(
            1000, context_at(1800000000), toolbar_visible=False, **kwargs
        )

    def test_pinned_wish_can_be_spoken_after_original_deadline_and_saved_once(self):
        self.state.set_wish_pinned(1, True)
        self.state.restore_checkpoint(replace(self.state.capture_checkpoint(),
                                              lived_seconds=20000))
        reaction = self.select().reaction
        assert reaction is not None
        self.assertEqual(reaction.wish_instance_id, 1)
        self.player.play(reaction)
        self.assertEqual(self.state.wishes.active[0].expressed_at, 20000)
        self.assertEqual(self.state.wishes.active[0].expires_at, 14400)
        loaded = decode_pet_state(encode_pet_state(self.state), now=1800000000)
        self.assertEqual(loaded.wishes, self.state.wishes)
        self.assertFalse(self.select().due)

    def test_spoken_round_count_comes_from_original_goal_instead_of_current_catalogue(
        self,
    ):
        definitions = dict(WISH_CATALOG.definitions)
        definitions[WishId.WIN_OVERALL] = replace(definitions[WishId.WIN_OVERALL],
                                                  round_count=5)
        original = ActiveWish(1, WishId.WIN_OVERALL, "blackjack", 0, 14400)
        with patch("aiko_pet.pet.mind.mind.WISH_CATALOG", WishCatalog(definitions)):
            reaction = self.mind.wish_reaction(original)
        self.assertIn("3", reaction.text)
        self.assertNotIn("5", reaction.text)

    def test_selected_wish_is_concrete_but_unspoken_until_display_then_persists(self):
        before = self.state.capture_checkpoint()
        choice = self.select()
        self.assertTrue(choice.due)
        assert choice.reaction is not None
        self.assertEqual(choice.reaction.wish_instance_id, 1)
        self.assertIn("Apfel", choice.reaction.text)
        self.assertEqual(self.state.capture_checkpoint(), before)
        self.player.play(choice.reaction)
        self.assertEqual(len(self.shown), 1)
        self.assertEqual(self.state.wishes.active[0].expressed_at, 100)
        self.assertEqual(
            replace(self.state.capture_checkpoint(), wishes=before.wishes), before
        )
        loaded = decode_pet_state(encode_pet_state(self.state), now=1800000000)
        self.assertEqual(loaded.wishes, self.state.wishes)
        self.assertFalse(self.select().due)

    def test_cancel_before_text_and_stale_timer_do_not_report_a_wish(self):
        reaction = self.select().reaction
        assert reaction is not None
        delayed = replace(reaction, beats=(Cue("emote", "idea", 500), *reaction.beats))
        self.player.play(delayed)
        pending = self.player.pending_timer
        assert pending is not None
        stale = self.scheduler.callbacks[pending][1]
        self.player.cancel()
        stale()
        self.assertFalse(self.shown)
        self.assertIsNone(self.state.wishes.active[0].expressed_at)
        self.assertIsNone(self.state.wishes.last_expressed_at)
        self.player.play(reaction)
        current = self.player.pending_timer
        assert current is not None
        callback = self.scheduler.callbacks[current][1]
        self.scheduler.fire(current)
        callback()
        self.assertEqual(len(self.shown), 1)
        self.assertEqual(self.state.wishes.last_expressed_at, 100)

    def test_expired_identity_and_unrelated_text_cannot_acknowledge(self):
        reaction = self.select().reaction
        set_test_pet_values(self.state, lived_seconds=14400)
        self.player.play(reaction)
        self.assertIsNone(self.state.wishes.last_expressed_at)
        self.player.play(Reaction.spoken("other", "Hallo.", "idle", "greeting"))
        self.assertIsNone(self.state.wishes.last_expressed_at)

    def test_disclosure_respects_busy_settings_thresholds_and_urgent_care(self):
        for kwargs in (
            dict(bubble_visible=True),
            dict(popup_visible=True),
            dict(action_until=1001),
        ):
            self.assertFalse(self.select(**kwargs).due)
        self.settings.spontaneous_talk = False
        self.assertFalse(self.select().due)
        self.settings.spontaneous_talk = True
        for field, value in (("friendship", 0), ("mood", 49), ("sleeping", True)):
            before = self.state.capture_checkpoint()
            set_test_pet_values(self.state, **{field: value})
            self.assertFalse(self.select().due)
            self.state.restore_checkpoint(before)
        set_test_pet_values(self.state, satiety=0)
        choice = self.select()
        assert choice.reaction is not None
        self.assertEqual(choice.reaction.event, "care_request_feed")
        self.attention.next_care_request = 99999
        self.assertFalse(self.select().due)  # Urgency also beats wish during cooldown.

    def test_existing_acceptance_is_reused_without_starting_petting_or_game(self):
        set_test_pet_values(self.state, affection=100, energy=0)
        before = self.state.capture_checkpoint()
        context = self.attention.wish_context()
        self.assertFalse(context.petting_welcome)
        self.assertFalse(context.games_ready)
        self.assertEqual(self.state.capture_checkpoint(), before)
        self.assertFalse(
            any(
                e.definition_id == MoodletId.CROWDED for e in self.state.moodlets.active
            )
        )

    def test_inner_creation_is_not_blocked_by_low_trust_or_speech_setting(self):
        self.state.restore_checkpoint(
            replace(
                self.state.capture_checkpoint(),
                wishes=WishState(),
                mood=0,
                friendship=0,
                satiety=60,
            )
        )
        self.settings.spontaneous_talk = False
        self.attention.evaluate_wishes()
        self.assertEqual(len(self.state.wishes.active), 3)
        self.assertFalse(self.select().due)

    def test_all_twelve_forms_render_actual_targets_and_goal_scope(self):
        for definition in WISH_CATALOG.definitions.values():
            for target in definition.targets:
                with self.subTest(objective=definition.id, target=target):
                    reaction = self.mind.wish_reaction(
                        ActiveWish(5, definition.id, target, 0, 14400,
                                   goal=definition.goal)
                    )
                    self.assertEqual(len(reaction.beats), 1)
                    self.assertEqual(reaction.wish_instance_id, 5)
                    self.assertNotIn("{", reaction.text)
                    if definition.round_count > 1:
                        self.assertIn(str(definition.round_count), reaction.text)
