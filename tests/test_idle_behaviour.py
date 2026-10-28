"""Idle profiles reuse current emotion and needs without owning their state."""

import unittest
from dataclasses import FrozenInstanceError, replace

import test_attention_policy as support

from aiko_pet.pet.animation.idle_behaviour import (
    IdleBehaviourContext,
    IdleBehaviourProfile,
    derive_idle_profile,
)
from aiko_pet.pet.emotions import EmotionalState
from aiko_pet.pet.needs import NeedCondition


class IdleBehaviourTests(unittest.TestCase):
    def test_canonical_feelings_and_physical_limits_select_the_profile(self):
        for feeling, mode in ((EmotionalState.CALM, "calm"),
                              (EmotionalState.CHEERFUL, "active"),
                              (EmotionalState.LONELY, "subdued"),
                              (EmotionalState.TENSE, "tense")):
            with self.subTest(feeling=feeling):
                context = IdleBehaviourContext(80, feeling)
                self.assertEqual(derive_idle_profile(context).mode, mode)
                tired = derive_idle_profile(replace(
                    context, conditions=frozenset((NeedCondition.LOW_ENERGY,)),
                ))
                self.assertEqual((tired.mode, tired.maximum_steps), ("tired", 1))
                self.assertFalse(derive_idle_profile(replace(context, energy=0))
                                 .allow_steps)

    def test_low_fun_does_not_override_exhaustion_or_negative_feelings(self):
        low_fun = frozenset((NeedCondition.LOW_FUN,))
        for energy, feeling, mode in (
            (80, EmotionalState.CALM, "active"),
            (0, EmotionalState.CALM, "tired"),
            (80, EmotionalState.DOWNCAST, "subdued"),
            (80, EmotionalState.IRRITATED, "tense"),
        ):
            self.assertEqual(derive_idle_profile(IdleBehaviourContext(
                energy, feeling, low_fun,
            )).mode, mode)

    def test_profiles_are_immutable_and_reject_invalid_ranges(self):
        profile = IdleBehaviourProfile()
        with self.assertRaises(FrozenInstanceError):
            setattr(profile, "mode", "active")
        for fields in ({"hold_minimum": 10, "hold_maximum": 1},
                       {"step_gap_multiplier": 0}, {"body_glance_every": 0},
                       {"two_step_probability": 2}):
            with self.assertRaises(ValueError):
                replace(profile, **fields)

    def test_application_read_does_not_tick_or_mutate_the_pet(self):
        fixture = support.AttentionPolicyTests()
        fixture.setUp()
        before = fixture.state.capture_checkpoint()
        for _ in range(10):
            self.assertIsInstance(fixture.attention.idle_profile(),
                                  IdleBehaviourProfile)
        self.assertEqual(fixture.state.capture_checkpoint(), before)
