"""Wish objectives reference existing activities and positive Moodlet families."""

from __future__ import annotations

import copy
import random
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path
from types import MappingProxyType
from typing import Any, cast

from aiko_pet.application.social_content import SocialCategory
from aiko_pet.games.contracts import GameId
from aiko_pet.pet.balance import BALANCE, parse_balance
from aiko_pet.pet.catalog_validation import load_json
from aiko_pet.pet.content import GERMAN_TEXT
from aiko_pet.pet.food_catalog import DEFAULT_CATALOG
from aiko_pet.pet.moodlet_catalog import MOODLET_CATALOG, MoodletCatalog
from aiko_pet.pet.moodlets import MoodletId
from aiko_pet.pet.needs import NeedLevels
from aiko_pet.pet.wish_catalog import (
    WISH_CATALOG,
    load_packaged_wish_catalog,
    parse_wish_catalog,
)
from aiko_pet.pet.wishes import (
    WishArea,
    WishContext,
    WishId,
    WishObjective,
    WishState,
    replenish_wishes,
)

DATA = Path(__file__).resolve().parents[1] / "aiko_pet/data"


class WishCatalogTests(unittest.TestCase):
    def setUp(self) -> None:
        self.raw = load_json(DATA / "wishes.json")

    def test_twelve_forms_reference_the_actual_food_games_and_social_choices(self):
        catalog = load_packaged_wish_catalog()
        self.assertEqual(catalog, WISH_CATALOG)
        self.assertEqual(len(catalog.definitions), 12)
        self.assertEqual(set(catalog.definitions[WishId.FOOD].targets),
                         set(DEFAULT_CATALOG.foods))
        social = {t for d in catalog.definitions.values()
                  if d.area == WishArea.SOCIAL for t in d.targets}
        self.assertEqual(social, {"chat", *(c.value for c in SocialCategory)})
        for definition in catalog.definitions.values():
            if definition.area == WishArea.GAMES:
                self.assertEqual(set(definition.targets), {g.value for g in GameId})
        self.assertEqual(sum(d.area == WishArea.GAMES
                             for d in catalog.definitions.values()), 5)

    def test_game_goal_scope_and_initial_impression_follow_the_agreed_variants(self):
        definitions = WISH_CATALOG.definitions
        for key, rounds, moodlet, level in (
            (WishId.PLAY_GAME, 2, MoodletId.SHARED_PLAY, 1),
            (WishId.WIN_ROUND, 1, MoodletId.PRIDE, 1),
            (WishId.AVOID_ROUND_LOSS, 1, MoodletId.RELIEF, 1),
            (WishId.WIN_OVERALL, 3, MoodletId.PRIDE, 2),
            (WishId.AVOID_OVERALL_LOSS, 3, MoodletId.RELIEF, 2),
        ):
            with self.subTest(wish=key):
                definition = definitions[key]
                self.assertEqual((definition.round_count,
                                  definition.fulfillment_moodlet,
                                  definition.fulfillment_level),
                                 (rounds, moodlet, level))
        self.assertEqual(definitions[WishId.SINGLE].fulfillment_moodlet,
                         definitions[WishId.TWO_PARTS].fulfillment_moodlet)

    def test_new_goal_meanings_and_weights_are_explicit_without_activating_avoidance(
        self,
    ):
        definitions = WISH_CATALOG.definitions
        self.assertEqual({key: definitions[key].selection_weight for key in (
            WishId.PLAY_GAME, WishId.WIN_ROUND, WishId.AVOID_ROUND_LOSS,
            WishId.WIN_OVERALL, WishId.AVOID_OVERALL_LOSS,
        )}, {WishId.PLAY_GAME: 60, WishId.WIN_ROUND: 10,
             WishId.AVOID_ROUND_LOSS: 15, WishId.WIN_OVERALL: 10,
             WishId.AVOID_OVERALL_LOSS: 5})
        self.assertEqual(definitions[WishId.WIN_OVERALL].goal.objective,
                         WishObjective.TOTAL_WINS)
        self.assertEqual(definitions[WishId.PLAY_GAME].goal.objective,
                         WishObjective.TOTAL_ROUNDS)
        self.assertEqual(definitions[WishId.WIN_ROUND].goal.objective,
                         WishObjective.NEXT_WIN)
        avoid = definitions[WishId.AVOID_FOOD]
        self.assertEqual((avoid.area, avoid.goal.objective, avoid.selection_weight),
                         (WishArea.FOOD, WishObjective.FOOD_HANDOVER, 0))
        self.assertEqual(avoid.targets, definitions[WishId.FOOD].targets)
        state = WishState()
        self.assertEqual(replenish_wishes(
            state, elapsed=0, sleeping=False, context=WishContext(),
            needs=NeedLevels(50, 80, 100, 100, 50),
            definitions={avoid.id: avoid}, rng=random.Random(1),
        ), state)

    def test_definitions_targets_and_collections_are_read_only(self):
        with self.assertRaises(TypeError):
            cast(dict[Any, Any], WISH_CATALOG.definitions)[WishId.FOOD] = None
        with self.assertRaises(FrozenInstanceError):
            cast(Any, WISH_CATALOG.definitions[WishId.FOOD]).targets = ()
        self.assertIsInstance(WISH_CATALOG.definitions[WishId.FOOD].targets, tuple)

    def test_unknown_missing_duplicate_and_mistyped_objectives_are_rejected(self):
        for version in (True, 1.0, 2):
            with self.subTest(version=version), self.assertRaises(ValueError):
                parse_wish_catalog({**self.raw, "version": version})
        for rows in ([], self.raw["wishes"][:-1],
                     [*self.raw["wishes"], self.raw["wishes"][0]]):
            with self.subTest(count=len(rows)), self.assertRaises(ValueError):
                parse_wish_catalog({**self.raw, "wishes": rows})
        for key, field, bad in (
            ("food", "id", "sleep"), ("food", "area", "social"),
            ("food", "target_kind", "game"), ("food", "targets", ["energy_drink"]),
            ("food", "targets", ["apple", "apple"]),
            ("food", "targets", [{}]), ("food", "targets", []),
            ("play_game", "targets", ["unimplemented_game"]),
            ("single", "targets", ["fact"]), ("pet", "targets", ["sleep"]),
            ("food", "round_count", 1), ("play_game", "round_count", 0),
            ("win_round", "round_count", 3), ("win_round", "round_count", True),
            ("win_overall", "fulfillment_level", 4),
            ("food", "fulfillment_level", 2),
            ("food", "fulfillment_moodlet", "unknown"),
            ("food", "fulfillment_moodlet", "poking"),
            ("food", "fulfillment_moodlet", "pride"),
            ("food", "round_cuont", 0),
            ("food", "selection_weight", True),
            ("food", "selection_weight", -1),
            ("food", "selection_weight", 101),
            ("play_game", "objective", "session_rounds"),
            ("avoid_food", "objective", "food_intake"),
        ):
            raw = copy.deepcopy(self.raw)
            next(r for r in raw["wishes"] if r["id"] == key)[field] = bad
            with self.subTest(key=key, field=field, bad=bad):
                with self.assertRaises(ValueError):
                    parse_wish_catalog(raw)

    def test_missing_cross_catalogue_resources_cannot_silently_fall_back(self):
        definitions = dict(MOODLET_CATALOG.definitions)
        del definitions[MoodletId.FOOD_FULFILLED]
        with self.assertRaisesRegex(ValueError, "missing fulfillment Moodlet"):
            parse_wish_catalog(self.raw,
                               moodlets=MoodletCatalog(MappingProxyType(definitions)))
        with self.assertRaisesRegex(ValueError, "targets"):
            parse_wish_catalog(self.raw, food_ids={"apple"})
        with self.assertRaisesRegex(ValueError, "targets"):
            parse_wish_catalog(self.raw, game_ids={GameId.BLACKJACK.value})
        with self.assertRaisesRegex(ValueError, "localized"):
            parse_wish_catalog(self.raw,
                               text_keys=set(GERMAN_TEXT.messages)
                               - {"wish.pet.description"})

    def test_shared_pacing_and_bonus_have_one_balance_owner(self):
        self.assertEqual(BALANCE.integer("wishes", "maximum_active"), 3)
        self.assertEqual(BALANCE.integer("wishes", "maximum_per_area"), 1)
        self.assertEqual(BALANCE.integer("wishes", "lifetime_seconds"), 14400)
        self.assertEqual(BALANCE.integer("wishes", "refill_delay_seconds"), 720)
        self.assertEqual(BALANCE.integer("wishes", "disclosure_interval_seconds"), 1800)
        self.assertEqual(BALANCE.integer("wishes", "disclosure_friendship_level"), 3)
        self.assertEqual(BALANCE.number("wishes", "disclosure_mood_threshold"), 50)
        self.assertEqual(BALANCE.number("wishes", "friendship_bonus_points"), .25)
        self.assertEqual(BALANCE.number("wishes", "creation_need_threshold"), 70)
        self.assertEqual(BALANCE.number("wishes", "relevance_need_threshold"), 90)
        original = load_json(DATA / "balance.json")
        for key, bad in (
            ("maximum_active", 5), ("maximum_per_area", 2),
            ("disclosure_friendship_level", 11), ("disclosure_mood_threshold", 101),
            ("friendship_bonus_points", 1), ("friendship_bonus_points", True),
            ("refill_delay_seconds", 15000),
            ("lifetime_seconds", 0),
            ("creation_need_threshold", 90),
            ("relevance_need_threshold", 70),
            ("relevance_need_threshold", 101),
        ):
            raw = copy.deepcopy(original)
            raw["wishes"][key] = bad
            with self.subTest(key=key), self.assertRaises(ValueError):
                parse_balance(raw)
