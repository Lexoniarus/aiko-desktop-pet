"""Continuous contributions and progressive flow, using explicit elapsed amounts."""

import unittest
from dataclasses import replace

from aiko_pet.infrastructure.friendship_codec import (
    decode_friendship,
    encode_friendship,
)
from aiko_pet.pet.friendship_decay import (
    advance_friendship,
    balance_friendship,
    emotional_friendship_rates,
)
from aiko_pet.pet.friendship_history import FriendshipHistory, FriendshipProgress
from aiko_pet.pet.moodlets import MoodletEpisode, MoodletId, MoodletState


class ContinuousFriendshipTests(unittest.TestCase):
    def test_reference_days_keep_average_care_at_seven_eight_and_intensive_at_ten(self):
        # Approved scenario arithmetic, not a second needs or wish simulator.
        for mood, visits, per_visit, low, high in (
            (65, (7, 13, 19, 23), (1,), 60, 70),
            (65, (7, 13, 19, 23), (2,), 70, 80),
            (75, (7, 9.5, 12, 14.5, 17, 19, 21, 23), (1,), 80, 90),
            (75, (7, 9.5, 12, 14.5, 17, 19, 21, 23), (2, 1), 90, 100),
        ):
            with self.subTest(visits=len(visits), per_visit=per_visit):
                progress = FriendshipProgress(70, FriendshipHistory(
                    0, continuous_since=0,
                ), 7 * 3600)
                extremes = []

                def advance_to(end, impressions):
                    nonlocal progress
                    progress = advance_friendship(
                        progress, end - progress.elapsed, (100.,) * 5, (100.,) * 5,
                        sleeping=False, mood_before=mood, mood_after=mood,
                        moodlets=impressions,
                    )

                for day in range(160):
                    for index, hour in enumerate(visits):
                        target = (day * 24 + hour) * 3600
                        advance_to(target, MoodletState())
                        if day == 159:
                            extremes.append(progress.points)
                        progress = replace(progress, history=replace(
                            progress.history, last_contact=target,
                        ))
                        episodes = tuple(MoodletEpisode(i, key, 1, target, target, 7200)
                                         for i, key in enumerate((
                                             MoodletId.SECURE, MoodletId.CONNECTION,
                                         )[:per_visit[index % len(per_visit)]], 1))
                        advance_to(target + 7200, MoodletState(active=episodes))
                        if day == 159:
                            extremes.append(progress.points)
                advance_to((160 * 24 + 7) * 3600, MoodletState())
                extremes.append(progress.points)
                self.assertGreaterEqual(min(extremes), low)
                self.assertLessEqual(max(extremes), high)

    def test_numeric_mood_bands_and_recent_accepted_contact(self):
        for mood, positive, negative in ((0, 0, .004), (20, 0, .004),
                                         (30, 0, .002), (40, 0, 0), (60, 0, 0),
                                         (70, .001, 0), (80, .002, 0), (100, .002, 0)):
            with self.subTest(mood=mood):
                result = emotional_friendship_rates(mood, mood, MoodletState(),
                                                     recent_contact=True)
                self.assertEqual(result, (positive, negative))
                self.assertEqual(emotional_friendship_rates(
                    mood, mood, MoodletState(), recent_contact=False,
                ), (0, negative))
        average = emotional_friendship_rates(
            20, 80, MoodletState(), recent_contact=True,
        )
        self.assertAlmostEqual(average[0], .002 / 6)
        self.assertAlmostEqual(average[1], .004 / 6)

    def test_all_actual_moodlets_contribute_even_above_numeric_mood_caps(self):
        state = MoodletState(active=tuple(
            MoodletEpisode(i, key, tier, 0, 0, 1200)
            for i, (key, tier) in enumerate((
                (MoodletId.SECURE, 3), (MoodletId.RELIEF, 2),
                (MoodletId.POKING, 1), (MoodletId.CROWDED, 1),
            ), 1)
        ))
        positive, negative = emotional_friendship_rates(80, 80, state,
                                                        recent_contact=True)
        self.assertAlmostEqual(positive, .017)
        self.assertAlmostEqual(negative, .012)
        two_bad = replace(state, active=state.active[2:])
        positive, negative = emotional_friendship_rates(80, 80, two_bad,
                                                        recent_contact=True)
        result = balance_friendship(70, positive=positive, negative=negative)
        self.assertAlmostEqual(result - 70, -.0078, places=5)

    def test_simultaneous_progressive_flow_is_partition_independent(self):
        for points in (0, 34.9, 50, 70, 90, 100):
            for positive, negative in ((10, 0), (0, 10), (10, 7), (7, 10)):
                with self.subTest(points=points, positive=positive, negative=negative):
                    whole = balance_friendship(points, positive=positive,
                                                negative=negative)
                    split = points
                    for _ in range(10):
                        split = balance_friendship(split, positive=positive / 10,
                                                   negative=negative / 10)
                    self.assertAlmostEqual(whole, split, places=10)
                    self.assertTrue(0 <= whole <= 100)

    def test_continuous_boundary_is_optional_in_old_saves_and_strict_when_present(self):
        old = FriendshipHistory(baseline=10, last_contact=15)
        raw = encode_friendship(old)
        raw.pop("continuous_since")
        self.assertEqual(decode_friendship(raw, 100), old)
        current = replace(old, continuous_since=80)
        self.assertEqual(decode_friendship(encode_friendship(current), 100), current)
        for invalid in (True, -1, 9, 101):
            raw["continuous_since"] = invalid
            with self.assertRaises(ValueError):
                decode_friendship(raw, 100)
