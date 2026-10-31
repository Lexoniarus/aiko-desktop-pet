"""Shared outcome-independent priority for original exact and flexible wishes."""

import unittest
from dataclasses import replace

from aiko_pet.pet.wish_catalog import WISH_CATALOG
from aiko_pet.pet.wish_matching import assign_activity_wish
from aiko_pet.pet.wishes import (
    ActiveWish,
    GameWishProgress,
    WishArea,
    WishId,
    WishState,
)

DEFINITIONS = WISH_CATALOG.definitions


def wish(key, reference=None, *, instance=1, at=0, pinned=False, progressed=False):
    definition = DEFINITIONS[key]
    target = definition.bind_target(reference)
    return ActiveWish(
        instance, key, reference or "", at, 600, goal=definition.goal,
        target=target, pinned=pinned,
        game=GameWishProgress(("earlier:1",), 1, 0) if progressed
        else GameWishProgress(),
    )


def assigned(*wishes, area=WishArea.GAMES, target="blackjack", elapsed=100):
    return assign_activity_wish(WishState(active=wishes), area, target,
                                elapsed=elapsed, definitions=DEFINITIONS)


class WishAssignmentTests(unittest.TestCase):
    def test_concrete_target_beats_older_flexible_target(self):
        free = wish(WishId.PLAY_ANY_GAME)
        exact = wish(WishId.PLAY_GAME, "blackjack", instance=2, at=10)
        self.assertEqual(assigned(free, exact), exact)

    def test_pinned_flexible_target_beats_specific_progress_and_age(self):
        exact = wish(WishId.PLAY_GAME, "blackjack", progressed=True)
        free = wish(WishId.PLAY_ANY_GAME, instance=2, at=20, pinned=True)
        self.assertEqual(assigned(exact, free), free)

    def test_exclusion_beats_free_choice_but_never_matches_excluded_game(self):
        free = wish(WishId.PLAY_ANY_GAME)
        other = wish(WishId.PLAY_OTHER_GAME, "mastermind", instance=2, at=10)
        self.assertEqual(assigned(free, other), other)
        self.assertEqual(assigned(free, other, target="mastermind"), free)

    def test_existing_progress_beats_age_only_at_equal_specificity(self):
        old = wish(WishId.PLAY_GAME, "blackjack")
        started = wish(WishId.WIN_OVERALL, "blackjack", instance=2, at=10,
                       progressed=True)
        self.assertEqual(assigned(old, started), started)
        free = wish(WishId.PLAY_ANY_GAME, instance=3, progressed=True)
        self.assertEqual(assigned(free, old), old)

    def test_equal_specificity_and_progress_use_age_then_stable_id(self):
        old = wish(WishId.WIN_ROUND, "blackjack", instance=3, at=10)
        newer = wish(WishId.AVOID_ROUND_LOSS, "blackjack", instance=1, at=20)
        self.assertEqual(assigned(newer, old), old)
        same_age = replace(newer, created_at=10)
        self.assertEqual(assigned(old, same_age), same_age)

    def test_future_expired_and_unsupported_targets_are_not_assigned(self):
        free = wish(WishId.PLAY_ANY_GAME)
        self.assertIsNone(assigned(free, elapsed=600))
        self.assertIsNone(assigned(replace(free, created_at=101)))
        self.assertIsNone(assigned(free, target="unsupported"))
        self.assertIsNone(assigned(free, area=WishArea.SOCIAL, target="chat"))
        self.assertEqual(assigned(replace(free, pinned=True), elapsed=1000),
                         replace(free, pinned=True))

    def test_social_free_choice_uses_same_priority_and_supported_categories(self):
        free = wish(WishId.SOCIAL_ANY)
        chat = wish(WishId.CHAT, "chat", instance=2, at=10)
        self.assertEqual(
            assigned(free, chat, area=WishArea.SOCIAL, target="chat"), chat,
        )
        self.assertEqual(
            assigned(free, chat, area=WishArea.SOCIAL, target="fact"), free,
        )
        self.assertIsNone(assigned(free, area=WishArea.SOCIAL, target="horoscope"))

    def test_legacy_exact_goal_keeps_its_original_progress_and_meaning(self):
        old = ActiveWish(1, WishId.PLAY_GAME, "blackjack", 0, 14400,
                         game=GameWishProgress(("old:1",), 0, 1, "old"))
        free = wish(WishId.PLAY_ANY_GAME, instance=2)
        self.assertIs(assigned(free, old), old)
