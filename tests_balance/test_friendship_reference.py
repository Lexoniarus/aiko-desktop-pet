"""Continuous contributions and progressive flow, using explicit elapsed amounts."""

import unittest
from dataclasses import replace

from aiko_pet.pet.friendship_decay import (
    advance_friendship,
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

