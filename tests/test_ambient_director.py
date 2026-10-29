"""Headless tests for the independent resting and glance director."""

from __future__ import annotations

import unittest
from dataclasses import replace

from aiko_pet.pet.animation.ambient import AmbientDirector
from aiko_pet.pet.animation.animation import SpriteSelection
from aiko_pet.pet.animation.idle_behaviour import IdleBehaviourProfile


class AmbientDirectorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = AmbientDirector(
            100.0, between=lambda low, _high: low,
            direction=lambda options: options[0],
        )

    def test_idle_rest_never_restarts_blink_in_the_same_beat(self) -> None:
        self.assertEqual(self.policy.choose(100), SpriteSelection("idle", 0))
        self.assertEqual(self.policy.choose(105), SpriteSelection("idle"))
        self.assertTrue(self.policy.blinking)
        self.assertEqual(self.policy.choose(106), SpriteSelection("idle"))
        self.policy.finish_blink(108)
        self.assertFalse(self.policy.blinking)
        self.assertEqual(self.policy.choose(109), SpriteSelection("idle", 0))
        self.assertEqual(self.policy.choose(110), SpriteSelection("idle", 0))
        self.assertEqual(self.policy.choose(111), SpriteSelection("idle"))

    def test_blink_gaps_allow_three_to_eight_seconds(self) -> None:
        self.assertEqual(self.policy.next_blink_at, 103.0)
        self.assertEqual(self.policy.choose(102.99), SpriteSelection("idle", 0))
        self.assertEqual(self.policy.choose(103), SpriteSelection("idle"))
        self.policy.finish_blink(104.28)
        self.assertEqual(self.policy.next_blink_at, 107.28)

        longest = AmbientDirector(
            100.0, between=lambda _low, high: high,
            direction=lambda options: options[0],
        )
        self.assertEqual(longest.next_blink_at, 108.0)
        longest.suspend(200.0)
        self.assertEqual(longest.next_blink_at, 208.0)

    def test_independent_glance_uses_one_static_direction_then_rests(self) -> None:
        self.policy.next_blink_at = 1000.0
        self.assertEqual(
            self.policy.choose(122), SpriteSelection("look", fixed_frame=2),
        )
        self.assertEqual(
            self.policy.choose(122.5), SpriteSelection("look", fixed_frame=2),
        )
        self.assertEqual(self.policy.choose(124), SpriteSelection("idle", 0))
        self.assertGreater(self.policy.next_glance_at, 124)

    def test_suspension_clears_spontaneous_activity(self) -> None:
        self.policy.choose(105)
        self.assertTrue(self.policy.blinking)
        self.policy.suspend(105.2)
        self.assertFalse(self.policy.blinking)
        self.assertEqual(
            self.policy.choose(105.2), SpriteSelection("idle", 0),
        )
        self.assertGreater(self.policy.next_blink_at, 105.2)
        self.assertGreater(self.policy.next_glance_at, 105.2)

    def test_slow_motion_continues_during_neutral_rest(self) -> None:
        offsets = [
            self.policy.motion_offset(100 + index * .42 + .01)
            for index in range(9)
        ]
        self.assertEqual(offsets, [0, 0, 1, 1, 0, 0, -1, -1, 0])
        self.assertLessEqual(max(map(abs, offsets)), 1)

    def test_gaze_actions_and_blink_share_one_continuous_motion_clock(self) -> None:
        self.policy.suspend(101)
        self.assertEqual(self.policy.motion_offset(101), 1)
        self.policy.suspend(101)
        self.assertEqual(self.policy.motion_offset(101), 1)
        self.assertEqual(self.policy.motion_offset(101 + .85), 0)
        self.policy.next_blink_at = 103
        self.policy.choose(105)
        self.assertTrue(self.policy.blinking)
        offset_before_completion = self.policy.motion_offset(105.2)
        self.assertEqual(offset_before_completion, 0)
        self.policy.finish_blink(105.2)
        self.assertEqual(self.policy.motion_offset(105.2), offset_before_completion)

    def test_pointer_interruptions_do_not_starve_spontaneous_glances(self) -> None:
        self.policy.next_blink_at = 1000
        glances = []
        for tick in range(430):
            now = 100 + tick * .14
            tracking_pointer = (now - 100) % 10 < 4
            selected = self.policy.select_passive_animation(
                now, gaze_direction=4 if tracking_pointer else None,
                observing_computer=False, computer_busy=False,
                energy=80, mood=80, satiety=80,
            ).sprite
            if tracking_pointer:
                self.assertEqual(selected, SpriteSelection("look", 4))
            elif selected.animation == "look":
                glances.append(now)
        self.assertTrue(glances, "Brief mouse activity must not postpone every glance")
        self.assertLess(glances[0], 125)

    def test_due_glance_waits_for_directional_and_forward_attention(self) -> None:
        for gaze, forward, expected in (
            (4, False, SpriteSelection("look", 4)),
            (None, True, SpriteSelection("idle", 0)),
        ):
            with self.subTest(gaze=gaze, forward=forward):
                policy = AmbientDirector(
                    100, between=lambda low, _high: low,
                    direction=lambda options: options[0],
                )
                for now in (125, 130):
                    self.assertEqual(policy.select_passive_animation(
                        now, gaze_direction=gaze, forward_gaze=forward,
                        observing_computer=False, computer_busy=False,
                        energy=80, mood=80, satiety=80,
                    ).sprite, expected)
                    self.assertFalse(policy.blinking)
                self.assertEqual(policy.next_glance_at, 120)
                self.assertEqual(policy.select_passive_animation(
                    130.1, gaze_direction=None, observing_computer=False,
                    computer_busy=False, energy=80, mood=80, satiety=80,
                ).sprite, SpriteSelection("look", 2))

    def test_interrupted_glance_is_cancelled_and_schedules_one_fresh_gap(self) -> None:
        self.policy.next_blink_at = 1000
        self.assertEqual(self.policy.choose(122), SpriteSelection("look", 2))
        self.policy.suspend(122.2)
        self.assertEqual(self.policy.next_glance_at, 142.2)
        self.policy.suspend(130)
        self.assertEqual(self.policy.next_glance_at, 142.2)
        self.policy.next_blink_at = 1000
        self.assertEqual(self.policy.choose(130), SpriteSelection("idle", 0))
        self.assertEqual(self.policy.choose(142.2), SpriteSelection("look", 2))

    def test_external_gaze_keeps_sway_without_starting_ambient_blink(self) -> None:
        selected = self.policy.select_passive_animation(
            101.0, gaze_direction=3, observing_computer=True,
            computer_busy=True, energy=0, mood=0, satiety=0,
        ).sprite
        self.assertEqual(selected, SpriteSelection("look", fixed_frame=3))
        self.assertEqual(self.policy.motion_offset(101.0), 1)
        self.assertFalse(self.policy.blinking)

    def test_busy_computer_overrides_idle_without_resetting_motion(self) -> None:
        selected = self.policy.select_passive_animation(
            101.0, gaze_direction=None, observing_computer=True,
            computer_busy=True, energy=80, mood=80, satiety=80,
        ).sprite
        self.assertEqual(selected, SpriteSelection("review"))
        self.assertEqual(self.policy.motion_offset(101.0), 1)
        self.assertFalse(self.policy.blinking)

    def test_passive_idle_uses_original_blink_schedule(self) -> None:
        selected = self.policy.select_passive_animation(
            103.0, gaze_direction=None, observing_computer=False,
            computer_busy=False, energy=80, mood=80, satiety=80,
        ).sprite
        self.assertEqual(selected, SpriteSelection("idle"))
        self.assertTrue(self.policy.blinking)

    def test_invalid_autonomous_direction_is_rejected(self) -> None:
        bad = AmbientDirector(
            0.0, between=lambda low, _high: low,
            direction=lambda _options: 16,
        )
        with self.assertRaises(ValueError):
            bad.choose(22)

    def test_outing_finishes_with_short_stand_then_yields_front_and_new_attention(self):
        self.policy.finish_outing(100, -1)
        self.assertEqual(self.policy.choose(100.5), SpriteSelection("look", 12))
        self.assertEqual(self.policy.choose(101.1), SpriteSelection("idle", 0))
        self.policy.finish_outing(102, 1)
        self.policy.suspend(102.2)
        self.assertEqual(self.policy.choose(102.3).animation, "idle")


class AmbientBodyIntentTests(unittest.TestCase):
    def test_profile_hold_and_head_plan_survive_harmless_mid_episode_changes(self):
        policy = self.policy()
        policy.profile = IdleBehaviourProfile(mode="calm", body_glance_every=1,
                                              hold_minimum=6, hold_maximum=10)
        first = self.sample(policy, 10)
        self.assertEqual(first.body, "three_quarter")
        policy.note_body_settled(11, 1)
        policy.profile = replace(policy.profile, mode="active", hold_minimum=4,
                                 hold_maximum=8)
        self.assertEqual(policy.preferred_step_side, 1)
        self.assertEqual(self.sample(policy, 16.9).side, 1)
        self.assertEqual(self.sample(policy, 17.01).body, "front")
        self.assertEqual(policy.preferred_step_side, 0)

    def test_quiet_profile_uses_lower_axes_without_inventing_eye_frames(self):
        policy = self.policy()
        policy.profile = IdleBehaviourProfile(mode="tired", body_glance_every=1,
                                              prefer_lower_gaze=True,
                                              glance_gap_multiplier=1.5)
        first = self.sample(policy, 10)
        self.assertIn(first.sprite.fixed_frame, (4, 5, 6))
        policy.note_body_settled(11, 1)
        second = self.sample(policy, 12.6)
        self.assertIn(second.sprite.fixed_frame, (4, 5, 6))
        self.assertNotEqual(first.sprite, second.sprite)
        policy.suspend(13)
        self.assertEqual(policy.next_glance_at, 43)

    def policy(self, *, side=1, body_poses=True):
        policy = AmbientDirector(
            0, between=lambda low, _high: low,
            direction=lambda options: options[0] if side == 1 else options[-1],
            body_poses=body_poses,
        )
        policy.next_blink_at = 10000
        for now in (0, 5):
            policy.next_glance_at = now
            policy.choose(now)
            policy.choose(now + 3.1)
        policy.next_glance_at = 10
        return policy

    def sample(self, policy, now, gaze=None):
        return policy.select_passive_animation(
            now, gaze_direction=gaze, observing_computer=False,
            computer_busy=False, energy=80, mood=80, satiety=80,
        )

    def test_third_glance_turns_and_holds_only_after_actual_body_settles(self):
        for side in (-1, 1):
            with self.subTest(side=side):
                policy = self.policy(side=side)
                first = self.sample(policy, 10)
                self.assertEqual((first.body, first.side), ("three_quarter", side))
                self.assertEqual(self.sample(policy, 20), first)
                policy.note_body_settled(20, side)
                self.assertEqual(self.sample(policy, 21), first)
                changed = self.sample(policy, 21.6)
                self.assertNotEqual(changed.sprite, first.sprite)
                self.assertEqual((changed.body, changed.side),
                                 ("three_quarter", side))
                self.assertEqual(self.sample(policy, 22.9), changed)
                self.assertEqual(self.sample(policy, 23.01).body, "front")

    def test_attention_cancels_body_episode_without_resuming_an_old_pose(self):
        policy = self.policy()
        self.sample(policy, 10)
        policy.note_body_settled(10.5, 1)
        target = self.sample(policy, 10.6, gaze=12)
        self.assertEqual(target.sprite, SpriteSelection("look", 12))
        self.assertEqual(target.body, "front")
        policy.next_blink_at = 10000
        self.assertEqual(self.sample(policy, 11).sprite, SpriteSelection("idle", 0))

    def test_missing_body_pack_keeps_finite_head_only_glances(self):
        policy = self.policy(body_poses=False)
        self.assertEqual(self.sample(policy, 10).body, "front")
        self.assertEqual(self.sample(policy, 13).sprite, SpriteSelection("idle", 0))

    def test_alternate_outings_hold_quarter_then_yield_to_front_and_new_attention(self):
        policy = self.policy(side=-1)
        policy.finish_outing(10, -1)
        first = self.sample(policy, 10.1)
        self.assertEqual((first.body, first.side), ("three_quarter", -1))
        policy.note_body_settled(11, -1)
        self.assertEqual(self.sample(policy, 13.9).side, -1)
        self.assertEqual(self.sample(policy, 14.1).body, "front")
        policy.finish_outing(20, 1)
        self.assertEqual(self.sample(policy, 20.1).body, "front")
        self.assertEqual(self.sample(policy, 22.1).sprite, SpriteSelection("idle", 0))
        policy.finish_outing(30, -1)
        self.assertEqual(self.sample(policy, 30.1).side, -1)
        self.assertEqual(self.sample(policy, 30.2, gaze=4).body, "front")
        policy.next_blink_at = 10000
        self.assertEqual(self.sample(policy, 31).sprite, SpriteSelection("idle", 0))


if __name__ == "__main__":
    unittest.main()
