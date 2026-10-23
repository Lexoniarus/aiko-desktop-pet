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
from aiko_pet.pet.wish_selection import replenish_wishes
from aiko_pet.pet.wishes import (
    WishArea,
    WishContext,
    WishExperienceKind,
    WishId,
    WishObjective,
    WishState,
    WishTargetMode,
    wish_text_key,
)

DATA = Path(__file__).resolve().parents[1] / "aiko_pet/data"


class WishCatalogTests(unittest.TestCase):
    def setUp(self) -> None:
        self.raw = load_json(DATA / "wishes.json")

    def test_seventeen_forms_reference_actual_food_games_and_social_choices(self):
        catalog = load_packaged_wish_catalog()
        self.assertEqual(catalog, WISH_CATALOG)
        self.assertEqual(len(catalog.definitions), 17)
        self.assertEqual(set(catalog.definitions[WishId.FOOD].targets),
                         set(DEFAULT_CATALOG.foods))
        social = {t for d in catalog.definitions.values()
                  if d.area == WishArea.SOCIAL for t in d.targets}
        self.assertEqual(social, {"chat", *(c.value for c in SocialCategory)})
        for definition in catalog.definitions.values():
            if definition.area == WishArea.GAMES:
                with self.subTest(wish=definition.id):
                    self.assertEqual(set(definition.targets),
                                     {game.value for game in GameId})
        self.assertEqual(sum(d.area == WishArea.GAMES
                             for d in catalog.definitions.values()), 9)

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

    def test_goal_meanings_and_weights_include_evidence_gated_food_avoidance(self):
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
                         (WishArea.FOOD, WishObjective.FOOD_HANDOVER, 1))
        self.assertEqual(avoid.targets, definitions[WishId.FOOD].targets)
        state = WishState()
        self.assertFalse(replenish_wishes(
            state, elapsed=0, sleeping=False, context=WishContext(),
            needs=NeedLevels(50, 80, 100, 100, 50),
            definitions={avoid.id: avoid}, rng=random.Random(1),
        ).active)

    def test_definitions_targets_and_collections_are_read_only(self):
        with self.assertRaises(TypeError):
            cast(dict[Any, Any], WISH_CATALOG.definitions)[WishId.FOOD] = None
        with self.assertRaises(FrozenInstanceError):
            cast(Any, WISH_CATALOG.definitions[WishId.FOOD]).targets = ()
        self.assertIsInstance(WISH_CATALOG.definitions[WishId.FOOD].targets, tuple)

    def test_unknown_missing_duplicate_and_mistyped_objectives_are_rejected(self):
        for version in (True, 2.0, 1, 3):
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
                               moodlets=MoodletCatalog(
                                   MappingProxyType(definitions),
                                   MOODLET_CATALOG.long_term_policy,
                               ))
        with self.assertRaisesRegex(ValueError, "targets"):
            parse_wish_catalog(self.raw, food_ids={"apple"})
        with self.assertRaisesRegex(ValueError, "targets"):
            parse_wish_catalog(self.raw, game_ids={GameId.BLACKJACK.value})
        with self.assertRaisesRegex(ValueError, "localized"):
            parse_wish_catalog(self.raw,
                               text_keys=set(GERMAN_TEXT.messages)
                               - {"wish.pet.description"})

    def test_flexible_and_experience_forms_have_distinct_typed_goal_contracts(self):
        for key, mode, objective, count, moodlet, weight in (
            (WishId.PLAY_ANY_GAME, WishTargetMode.ANY, WishObjective.TOTAL_ROUNDS,
             2, MoodletId.SHARED_PLAY, 30),
            (WishId.PLAY_OTHER_GAME, WishTargetMode.EXCLUDE, WishObjective.TOTAL_ROUNDS,
             2, MoodletId.SHARED_PLAY, 10),
            (WishId.REMATCH_GAME, WishTargetMode.EXACT, WishObjective.TOTAL_ROUNDS,
             1, MoodletId.SHARED_PLAY, 10),
            (WishId.COMEBACK_GAME, WishTargetMode.EXACT, WishObjective.RETRY_WIN,
             1, MoodletId.PRIDE, 5),
            (WishId.SOCIAL_ANY, WishTargetMode.ANY, WishObjective.ACTIVITY,
             0, MoodletId.CONNECTION, 30),
        ):
            definition = WISH_CATALOG.definitions[key]
            with self.subTest(wish=key):
                self.assertEqual((definition.target_mode, definition.goal.objective,
                                  definition.round_count,
                                  definition.fulfillment_moodlet,
                                  definition.selection_weight),
                                 (mode, objective, count, moodlet, weight))
                self.assertEqual(wish_text_key(key, definition.goal, "utterance"),
                                 f"wish.{key}.utterance")
        social = WISH_CATALOG.definitions[WishId.SOCIAL_ANY]
        self.assertEqual(set(social.targets), {"chat", "single", "twopart", "fact"})
        self.assertIsNone(social.bind_target().target_id)
        other = WISH_CATALOG.definitions[WishId.PLAY_OTHER_GAME]
        self.assertFalse(other.bind_target("blackjack").matches(
            other.target_kind, "blackjack"))

    def test_experience_is_a_bounded_prerequisite_not_a_claim_of_actual_history(self):
        for key, kind in (
            (WishId.PLAY_OTHER_GAME, WishExperienceKind.RECENT_PLAY),
            (WishId.REMATCH_GAME, WishExperienceKind.LAST_ROUND_LOSS),
            (WishId.COMEBACK_GAME, WishExperienceKind.LAST_ROUND_LOSS),
        ):
            requirement = WISH_CATALOG.definitions[key].experience
            with self.subTest(wish=key):
                self.assertIsNotNone(requirement)
                assert requirement is not None
                self.assertEqual(requirement.kind, kind)
                self.assertEqual(requirement.window_seconds, 1800)
                self.assertEqual(requirement.weight_multiplier, 1.5)
                with self.assertRaises(FrozenInstanceError):
                    setattr(requirement, "window_seconds", 0)
        for key in (WishId.PLAY_ANY_GAME, WishId.SOCIAL_ANY, WishId.PLAY_GAME):
            self.assertIsNone(WISH_CATALOG.definitions[key].experience)

    def test_concrete_picker_does_not_misrepresent_flexible_or_experience_goals(self):
        pending = {
            key: WISH_CATALOG.definitions[key] for key in (
                WishId.PLAY_ANY_GAME, WishId.PLAY_OTHER_GAME, WishId.REMATCH_GAME,
                WishId.COMEBACK_GAME, WishId.SOCIAL_ANY,
            )
        }
        state = WishState()
        self.assertFalse(replenish_wishes(
            state, elapsed=100, sleeping=False, context=WishContext(online_social=True),
            needs=NeedLevels(0, 0, 0, 0, 0), definitions=pending, rng=random.Random(1),
        ).active)

    def test_invalid_target_modes_and_experience_requirements_are_rejected(self):
        for key, field, value in (
            ("play_any_game", "target_mode", "exact"),
            ("play_other_game", "target_mode", "any"),
            ("rematch_game", "experience", None),
            ("play_game", "experience", {"kind": "recent_play"}),
            ("social_any", "targets", ["horoscope"]),
            ("rematch_game", "round_count", 2),
            ("comeback_game", "objective", "next_win"),
        ):
            raw = copy.deepcopy(self.raw)
            next(r for r in raw["wishes"] if r["id"] == key)[field] = value
            with self.subTest(key=key, field=field), self.assertRaises(ValueError):
                parse_wish_catalog(raw)
        for field, value in (
            ("kind", "recent_play"), ("window_seconds", True),
            ("window_seconds", 0), ("weight_multiplier", float("nan")),
            ("weight_multiplier", True), ("weight_multiplier", 0.5),
        ):
            raw = copy.deepcopy(self.raw)
            row = next(r for r in raw["wishes"] if r["id"] == "rematch_game")
            row["experience"][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                parse_wish_catalog(raw)

    def test_shared_pacing_has_one_owner_and_rejects_the_retired_bonus(self):
        self.assertEqual(BALANCE.integer("wishes", "maximum_active"), 3)
        self.assertEqual(BALANCE.integer("wishes", "maximum_per_area"), 1)
        self.assertEqual(BALANCE.integer("wishes", "lifetime_seconds"), 14400)
        self.assertEqual(BALANCE.integer("wishes", "refill_delay_seconds"), 720)
        self.assertEqual(BALANCE.integer("wishes", "disclosure_interval_seconds"), 1800)
        self.assertEqual(BALANCE.integer("wishes", "disclosure_friendship_level"), 3)
        self.assertEqual(BALANCE.number("wishes", "disclosure_mood_threshold"), 50)
        self.assertNotIn("friendship_bonus_points", BALANCE.sections["wishes"])
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
