"""Perceived boundaries, timed impressions and direct loss stay separate."""

import unittest
from dataclasses import replace
from unittest.mock import Mock

from aiko_pet.application.contact import acknowledge_interaction_text
from aiko_pet.infrastructure.moodlet_codec import decode_moodlets, encode_moodlets
from aiko_pet.infrastructure.pet_codec import decode_pet_state, encode_pet_state
from aiko_pet.pet.care_result import CareEffect
from aiko_pet.pet.interaction_events import Poked
from aiko_pet.pet.moodlets import MoodletId
from aiko_pet.pet.state import PetState
from aiko_pet.ui.pet_view.reaction_player import ReactionPlayer


class NegativeInteractionTests(unittest.TestCase):
    def test_poking_requires_delivered_boundary_and_current_burst(self):
        pet = PetState(friendship=50)
        pet.experience_interaction(Poked(True))
        self.assertFalse(pet.moodlets.active)
        acknowledge_interaction_text(pet, "click_boundary")
        for count in range(7):
            pet.experience_interaction(Poked(True))
            self.assertEqual(pet.moodlets.active[0].level, 1 + count // 3)
        self.assertEqual(pet.friendship, 50)
        pet.experience_interaction(Poked(False))
        prior = pet.moodlets
        pet.experience_interaction(Poked(True))
        self.assertEqual(pet.moodlets, prior)

    def test_selected_or_cancelled_boundary_is_not_communicated(self):
        from aiko_pet.infrastructure.character_mind import make_aiko_mind
        from aiko_pet.pet.routine import context_at

        pet = PetState()
        reaction = make_aiko_mind(started_at=0).select_reaction(
            "click_boundary", pet, context_at(pet.updated_at), 1,
        )
        self.assertIsNotNone(reaction)
        assert reaction is not None
        from aiko_pet.pet.mind.reaction_sequence import Cue

        reaction = replace(reaction, beats=(Cue("emote", "question", 500),
                                           Cue("text", "Bitte aufhören.", 1000)))
        callbacks = []
        player = ReactionPlayer(schedule=lambda _ms, cb: callbacks.append(cb) or "t",
                                cancel_timer=Mock(), display_emote=Mock(),
                                display_text=Mock(), start_action=Mock(),
                                mark_spoken=Mock(), is_closed=lambda: False,
                                on_text=lambda event: acknowledge_interaction_text(
                                    pet, event))
        player.play(reaction)
        self.assertIsNone(pet.moodlets.interactions.poke_boundary_at)
        player.cancel()
        callbacks[0]()
        self.assertIsNone(pet.moodlets.interactions.poke_boundary_at)
        player.play(reaction)
        callbacks[-1]()
        self.assertEqual(pet.moodlets.interactions.poke_boundary_at, 0)

    def test_petting_first_refusal_has_no_care_or_loss_then_violations_stack(self):
        pet = PetState(affection=100, friendship=50)
        for expected in (CareEffect.AFFECTION_ENOUGH, CareEffect.AFFECTION_ENOUGH_FIRM):
            self.assertEqual(pet.interact("pet").effect, expected)
            self.assertFalse(pet.moodlets.active)
            self.assertFalse(pet.friendship_history.penalties)
        history, needs = pet.friendship_history, pet.needs
        before_loss = pet.friendship
        self.assertEqual(pet.interact("pet").effect, CareEffect.AFFECTION_REFUSED)
        self.assertFalse(pet.moodlets.active)
        self.assertEqual(pet.friendship_history, history)
        acknowledge_interaction_text(pet, "pet_refused")
        for count in range(7):
            self.assertEqual(pet.interact("pet").effect,
                             CareEffect.AFFECTION_BOUNDARY_IGNORED)
            self.assertEqual(pet.moodlets.active[0].level, 1 + count // 3)
        self.assertEqual(pet.needs, needs)
        self.assertEqual(pet.friendship, before_loss - 1)
        self.assertEqual(pet.friendship_history.last_contact, history.last_contact)
        self.assertEqual(pet.moodlets.interactions.petting_refused_until, 1200)

    def test_refusal_and_budget_survive_restart_without_creating_care(self):
        pet = PetState(affection=95, friendship=50)
        for _ in range(3):
            pet.interact("pet")
        before_loss = pet.friendship
        acknowledge_interaction_text(pet, "pet_refused")
        pet.interact("pet")
        pet = decode_pet_state(encode_pet_state(pet), now=pet.updated_at)
        pet.interact("pet")
        self.assertEqual(pet.friendship, before_loss - .5)
        self.assertEqual(pet.moodlets.active[0].definition_id, MoodletId.CROWDED)

    def test_pre_action_threshold_and_refusal_expiry(self):
        pet = PetState(affection=59, friendship=0)
        self.assertEqual(pet.interact("pet").effect, CareEffect.AFFECTION)
        self.assertGreater(pet.affection, 60)
        self.assertEqual(pet.moodlets.interactions.petting_excess_attempts, 0)
        self.assertEqual(pet.interact("pet").effect, CareEffect.AFFECTION_ENOUGH)
        self.assertEqual(pet.interact("pet").effect, CareEffect.AFFECTION_ENOUGH_FIRM)
        self.assertEqual(pet.interact("pet").effect, CareEffect.AFFECTION_REFUSED)
        acknowledge_interaction_text(pet, "pet_refused")
        pet.interact("pet")
        from tools.pet_test_support import set_test_pet_values

        set_test_pet_values(pet, affection=10, lived_seconds=299)
        self.assertEqual(pet.interact("pet").effect,
                         CareEffect.AFFECTION_BOUNDARY_IGNORED)
        set_test_pet_values(pet, lived_seconds=600)
        self.assertEqual(pet.interact("pet").effect, CareEffect.AFFECTION)

    def test_older_moodlet_save_defaults_evidence_and_rejects_future_boundary(self):
        pet = PetState(lived_seconds=100)
        saved = encode_moodlets(pet.moodlets)
        saved.pop("interactions")
        self.assertEqual(decode_moodlets(saved, 100), pet.moodlets)
        saved = encode_moodlets(pet.moodlets)
        saved["interactions"]["petting_boundary_at"] = 101
        with self.assertRaises(ValueError):
            decode_moodlets(saved, 100)

    def test_petting_warning_evidence_roundtrips_and_migrates_legacy_boundary(self):
        pet = PetState(lived_seconds=100)
        memory = replace(pet.moodlets.interactions, petting_excess_attempts=2,
                         petting_last_excess_at=100)
        state = replace(pet.moodlets, interactions=memory)
        self.assertEqual(decode_moodlets(encode_moodlets(state), 100), state)
        legacy = encode_moodlets(pet.moodlets)
        facts = legacy["interactions"]
        facts.pop("petting_excess_attempts")
        facts.pop("petting_last_excess_at")
        facts["petting_boundary_at"] = 100
        restored = decode_moodlets(legacy, 100).interactions
        self.assertEqual(restored.petting_boundary_at, 100)
        self.assertEqual(restored.petting_excess_attempts, 3)
        self.assertEqual(restored.petting_last_excess_at, 100)

    def test_petting_warning_storage_rejects_unbounded_or_incomplete_evidence(self):
        for count, at in ((4, 100), (-1, None), (True, 100), (1, None),
                          (0, 100), (2, 101)):
            with self.subTest(count=count, at=at):
                saved = encode_moodlets(PetState(lived_seconds=100).moodlets)
                saved["interactions"].update(petting_excess_attempts=count,
                                              petting_last_excess_at=at)
                with self.assertRaises(ValueError):
                    decode_moodlets(saved, 100)

    def test_pure_care_plan_and_commit_share_petting_acceptance(self):
        from aiko_pet.pet.care_actions import plan_care_action

        for friendship, affection, effect in (
            (0, 59, CareEffect.AFFECTION), (0, 60, CareEffect.AFFECTION_ENOUGH),
            (20, 79, CareEffect.AFFECTION), (20, 80, CareEffect.AFFECTION_ENOUGH),
            (50, 89, CareEffect.AFFECTION), (50, 90, CareEffect.AFFECTION_ENOUGH),
            (90, 100, CareEffect.AFFECTION),
        ):
            with self.subTest(friendship=friendship, affection=affection):
                pet = PetState(friendship=friendship, affection=affection)
                checkpoint = pet.capture_checkpoint()
                plan = plan_care_action(pet, "pet", now=pet.updated_at)
                self.assertEqual(pet.capture_checkpoint(), checkpoint)
                result = pet.interact("pet", now=pet.updated_at)
                self.assertEqual(result, plan.result)
                self.assertEqual(result.effect, effect)

    def test_petting_warnings_survive_restart_and_reset_after_ten_quiet_minutes(self):
        from tools.pet_test_support import set_test_pet_values

        pet = PetState(affection=100, friendship=50)
        pet.interact("pet")
        pet = decode_pet_state(encode_pet_state(pet), now=pet.updated_at)
        set_test_pet_values(pet, lived_seconds=599)
        self.assertEqual(pet.interact("pet").effect, CareEffect.AFFECTION_ENOUGH_FIRM)
        pet = decode_pet_state(encode_pet_state(pet), now=pet.updated_at)
        set_test_pet_values(pet, lived_seconds=1199)
        self.assertEqual(pet.interact("pet").effect, CareEffect.AFFECTION_ENOUGH)
        self.assertIsNone(pet.moodlets.interactions.petting_boundary_at)
        self.assertFalse(pet.moodlets.active)

    def test_undelivered_boundary_repeats_refusal_without_loss_or_moodlet(self):
        pet = PetState(affection=100, friendship=50)
        acknowledge_interaction_text(pet, "pet_refused")  # No pending boundary.
        self.assertIsNone(pet.moodlets.interactions.petting_boundary_at)
        pet.interact("pet")
        pet.interact("pet")
        before = pet.friendship_history
        before_loss = pet.friendship
        for _ in range(4):
            self.assertEqual(pet.interact("pet").effect, CareEffect.AFFECTION_REFUSED)
        self.assertEqual(pet.friendship_history, before)
        self.assertFalse(pet.moodlets.active)
        acknowledge_interaction_text(pet, "pet_refused")
        self.assertEqual(pet.interact("pet").effect,
                         CareEffect.AFFECTION_BOUNDARY_IGNORED)
        self.assertEqual(pet.friendship, before_loss - .25)

    def test_cancelled_petting_boundary_cannot_turn_next_attempt_into_disregard(self):
        from aiko_pet.infrastructure.character_mind import make_aiko_mind
        from aiko_pet.pet.mind.reaction_sequence import Cue
        from aiko_pet.pet.routine import context_at

        pet = PetState(affection=100, friendship=50)
        for _ in range(3):
            pet.interact("pet")
        reaction = make_aiko_mind(started_at=0).select_reaction(
            "pet_refused", pet, context_at(pet.updated_at), 1,
        )
        assert reaction is not None
        reaction = replace(reaction, beats=(Cue("emote", "question", 500),
                                           Cue.text("Bitte gerade nicht.")))
        callbacks = []
        player = ReactionPlayer(schedule=lambda _ms, cb: callbacks.append(cb) or "t",
                                cancel_timer=Mock(), display_emote=Mock(),
                                display_text=Mock(), start_action=Mock(),
                                mark_spoken=Mock(), is_closed=lambda: False,
                                on_text=lambda event: acknowledge_interaction_text(
                                    pet, event))
        player.play(reaction)
        player.cancel()
        callbacks[0]()
        self.assertIsNone(pet.moodlets.interactions.petting_boundary_at)
        self.assertEqual(pet.interact("pet").effect, CareEffect.AFFECTION_REFUSED)
        player.play(reaction)
        callbacks[-1]()
        self.assertEqual(pet.interact("pet").effect,
                         CareEffect.AFFECTION_BOUNDARY_IGNORED)

    def test_refusal_and_loss_budget_remain_separate_from_offline_decay(self):
        from aiko_pet.pet.moodlet_catalog import MOODLET_CATALOG
        from aiko_pet.pet.moodlets import advance_moodlets
        from tools.pet_test_support import set_test_pet_values

        pet = PetState(affection=100, friendship=50)
        for _ in range(3):
            pet.interact("pet")
        acknowledge_interaction_text(pet, "pet_refused")
        before_loss = pet.friendship
        for _ in range(8):
            pet.interact("pet")
        self.assertEqual(pet.friendship, before_loss - 1)
        self.assertEqual(pet.moodlets.active[0].level, 3)
        self.assertEqual(pet.moodlets.interactions.petting_refused_until, 1200)
        set_test_pet_values(pet, lived_seconds=600)
        pet.interact("pet")
        self.assertEqual(pet.friendship, before_loss - 1.25)
        self.assertEqual(pet.moodlets.interactions.petting_refused_until, 1800)
        restored = decode_pet_state(encode_pet_state(pet), now=pet.updated_at)
        aged = advance_moodlets(
            restored.moodlets, 1200, elapsed=600, before=pet.needs, after=pet.needs,
            definitions=MOODLET_CATALOG.definitions, observed=False,
        )
        restored.restore_checkpoint(replace(restored.capture_checkpoint(),
                                            moodlets=aged, lived_seconds=1800,
                                            affection=10))
        self.assertEqual(restored.moodlets.active[0].level, 2)
        self.assertEqual(restored.interact("pet").effect, CareEffect.AFFECTION)
        self.assertEqual(restored.moodlets.active[0].level, 2)

    def test_trusted_full_affection_is_welcome_but_does_not_bypass_active_refusal(self):
        from tools.pet_test_support import set_test_pet_values

        pet = PetState(friendship=95, affection=100)
        for _ in range(8):
            self.assertEqual(pet.interact("pet").effect, CareEffect.AFFECTION)
        self.assertEqual(pet.moodlets.interactions.petting_excess_attempts, 0)
        self.assertFalse(pet.moodlets.active)
        pet = PetState(friendship=50, affection=100)
        for _ in range(3):
            pet.interact("pet")
        acknowledge_interaction_text(pet, "pet_refused")
        pet.interact("pet")
        set_test_pet_values(pet, friendship=95, affection=10, lived_seconds=299)
        self.assertEqual(pet.interact("pet").effect,
                         CareEffect.AFFECTION_BOUNDARY_IGNORED)
        self.assertEqual(pet.moodlets.interactions.petting_refused_until, 599)
        set_test_pet_values(pet, lived_seconds=599, affection=100)
        self.assertEqual(pet.interact("pet").effect, CareEffect.AFFECTION)
        self.assertTrue(pet.moodlets.active)  # Willingness does not erase the episode.
