"""Concrete, free and excluded wish meanings without lifecycle or UI state."""

import unittest
from dataclasses import FrozenInstanceError, replace
from typing import cast

from aiko_pet.infrastructure.wish_codec import decode_wish_goal
from aiko_pet.pet.wish_catalog import WISH_CATALOG
from aiko_pet.pet.wishes import (
    ActiveWish,
    WishId,
    WishTarget,
    WishTargetKind,
    WishTargetMode,
    legacy_wish_goal,
)


class WishTargetTests(unittest.TestCase):
    def test_free_play_accepts_different_games_without_becoming_concrete(self):
        target = WishTarget(WishTargetKind.GAME, WishTargetMode.ANY)
        self.assertTrue(target.matches(WishTargetKind.GAME, "blackjack"))
        self.assertTrue(target.matches(WishTargetKind.GAME, "mastermind"))
        self.assertFalse(target.matches(WishTargetKind.FOOD, "apple"))
        self.assertIsNone(target.target_id)

    def test_game_change_retains_its_exclusion_after_another_game_is_played(self):
        target = WishTarget(WishTargetKind.GAME, WishTargetMode.EXCLUDE, "blackjack")
        self.assertFalse(target.matches(WishTargetKind.GAME, "blackjack"))
        self.assertTrue(target.matches(WishTargetKind.GAME, "connect_four"))
        self.assertTrue(target.matches(WishTargetKind.GAME, "mastermind"))
        self.assertEqual(target.target_id, "blackjack")

    def test_free_social_accepts_each_supported_category_in_its_own_kind(self):
        target = WishTarget(WishTargetKind.SOCIAL, WishTargetMode.ANY)
        for category in ("chat", "single", "twopart", "fact"):
            with self.subTest(category=category):
                self.assertTrue(target.matches(WishTargetKind.SOCIAL, category))
        self.assertFalse(target.matches(WishTargetKind.GAME, "blackjack"))

    def test_exact_and_excluded_food_are_distinct_target_meanings(self):
        target = WishTarget(WishTargetKind.FOOD, WishTargetMode.EXACT, "apple")
        excluded = replace(target, mode=WishTargetMode.EXCLUDE)
        self.assertTrue(target.matches(WishTargetKind.FOOD, "apple"))
        self.assertFalse(excluded.matches(WishTargetKind.FOOD, "apple"))
        self.assertTrue(excluded.matches(WishTargetKind.FOOD, "donut"))

    def test_definition_binds_only_a_supported_reference(self):
        concrete = WISH_CATALOG.definitions[WishId.PLAY_GAME]
        self.assertEqual(concrete.bind_target("mastermind").target_id, "mastermind")
        free = replace(concrete, target_mode=WishTargetMode.ANY)
        self.assertIsNone(free.bind_target().target_id)
        for definition, target in ((concrete, "unknown"), (free, "blackjack")):
            with self.subTest(target=target), self.assertRaises(ValueError):
                definition.bind_target(target)

    def test_ambiguous_or_untyped_targets_are_rejected_and_values_are_immutable(self):
        for mode, target_id in (
            (WishTargetMode.ANY, "blackjack"),
            (WishTargetMode.EXACT, None),
            (WishTargetMode.EXCLUDE, ""),
        ):
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                WishTarget(WishTargetKind.GAME, mode, target_id)
        with self.assertRaises(ValueError):
            WishTarget(cast(WishTargetKind, "game"), WishTargetMode.ANY)
        target = WishTarget(WishTargetKind.GAME, WishTargetMode.ANY)
        with self.assertRaises(FrozenInstanceError):
            setattr(target, "target_id", "blackjack")

    def test_new_forms_require_explicit_original_goals_instead_of_legacy_guesses(self):
        for key in (WishId.PLAY_ANY_GAME, WishId.PLAY_OTHER_GAME,
                    WishId.REMATCH_GAME, WishId.COMEBACK_GAME, WishId.SOCIAL_ANY):
            goal = WISH_CATALOG.definitions[key].goal
            with self.subTest(wish=key):
                with self.assertRaises(ValueError):
                    legacy_wish_goal(key)
                with self.assertRaises(ValueError):
                    ActiveWish(1, key, "blackjack", 0, 100)
                self.assertEqual(decode_wish_goal({
                    "objective": goal.objective.value,
                    "required_count": goal.required_count,
                }, key), goal)
        with self.assertRaises(ValueError):
            decode_wish_goal({"objective": "retry_win", "required_count": 2},
                             WishId.COMEBACK_GAME)
