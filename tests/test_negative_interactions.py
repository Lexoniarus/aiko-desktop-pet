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
        pet = PetState(affection=95, friendship=50)
        history = pet.friendship_history
        self.assertEqual(pet.interact("pet").effect, CareEffect.AFFECTION_REFUSED)
        self.assertFalse(pet.moodlets.active)
        self.assertEqual(pet.friendship_history, history)
        acknowledge_interaction_text(pet, "pet_refused")
        for count in range(7):
            self.assertEqual(pet.interact("pet").effect, CareEffect.AFFECTION_REFUSED)
            self.assertEqual(pet.moodlets.active[0].level, 1 + count // 3)
        self.assertEqual(pet.affection, 95)
        self.assertEqual(pet.friendship, 49)
        self.assertIsNone(pet.friendship_history.last_contact)
        self.assertEqual(pet.moodlets.interactions.petting_refused_until, 1200)

    def test_refusal_and_budget_survive_restart_without_creating_care(self):
        pet = PetState(affection=95, friendship=50)
        acknowledge_interaction_text(pet, "pet_refused")
        pet.interact("pet")
        pet = decode_pet_state(encode_pet_state(pet), now=pet.updated_at)
        pet.interact("pet")
        self.assertEqual(pet.friendship, 49.5)
        self.assertEqual(pet.moodlets.active[0].definition_id, MoodletId.CROWDED)

    def test_pre_action_threshold_and_refusal_expiry(self):
        pet = PetState(affection=59, friendship=0)
        self.assertEqual(pet.interact("pet").effect, CareEffect.AFFECTION)
        self.assertGreater(pet.affection, 60)
        self.assertEqual(pet.interact("pet").effect, CareEffect.AFFECTION_REFUSED)
        acknowledge_interaction_text(pet, "pet_refused")
        pet.interact("pet")
        from tools.pet_test_support import set_test_pet_values

        set_test_pet_values(pet, affection=10, lived_seconds=299)
        self.assertEqual(pet.interact("pet").effect, CareEffect.AFFECTION_REFUSED)
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

    def test_pure_care_plan_and_commit_share_petting_acceptance(self):
        from aiko_pet.pet.care_actions import plan_care_action

        for friendship, affection, refused in ((0, 59, False), (0, 60, True),
                                               (50, 89, False), (50, 90, True)):
            with self.subTest(friendship=friendship, affection=affection):
                pet = PetState(friendship=friendship, affection=affection)
                checkpoint = pet.capture_checkpoint()
                plan = plan_care_action(pet, "pet", now=pet.updated_at)
                self.assertEqual(pet.capture_checkpoint(), checkpoint)
                result = pet.interact("pet", now=pet.updated_at)
                self.assertEqual(result, plan.result)
                self.assertEqual(result.effect == CareEffect.AFFECTION_REFUSED, refused)
