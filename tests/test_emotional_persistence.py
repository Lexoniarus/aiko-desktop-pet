"""Owned emotional values survive save/checkpoint boundaries without simulation."""

from __future__ import annotations

import copy
import json
import tempfile
import unittest
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
from typing import Any, cast
from unittest.mock import patch

from aiko_pet.application.read_snapshot import snapshot_pet
from aiko_pet.application.settings import PetSettings
from aiko_pet.infrastructure.moodlet_codec import decode_moodlets, encode_moodlets
from aiko_pet.infrastructure.persistence import StateStore
from aiko_pet.infrastructure.pet_codec import decode_pet_state, encode_pet_state
from aiko_pet.infrastructure.wish_codec import decode_wishes, encode_wishes
from aiko_pet.pet.moodlet_catalog import MOODLET_CATALOG
from aiko_pet.pet.moodlets import (
    MoodletAttribution,
    MoodletCause,
    MoodletCauseKind,
    MoodletEpisode,
    MoodletId,
    MoodletOutcome,
    MoodletState,
    MoodletWishCause,
    advance_moodlets,
)
from aiko_pet.pet.needs import NeedLevels
from aiko_pet.pet.state import PetState
from aiko_pet.pet.wish_catalog import WISH_CATALOG, WishCatalog
from aiko_pet.pet.wishes import (
    ActiveWish,
    GameWishProgress,
    WishArea,
    WishGoal,
    WishId,
    WishObjective,
    WishState,
)

WALL = 1_800_000_000.0
ELAPSED = 1000.0


def moodlet_state() -> MoodletState:
    return MoodletState(100, 8, (
        MoodletEpisode(1, MoodletId.POKING, 2, 100, 950, 570, (2, 3), 1),
        MoodletEpisode(3, MoodletId.HUNGER_WORN, 1, 200, 200, 2400, (1,),
                       decay_paused=True),
        MoodletEpisode(5, MoodletId.WITHHELD, 3, 300, 900, 1200,
                       decay_paused=True),
        MoodletEpisode(7, MoodletId.PRIDE, 2, 800, 850, 3600),
    ))


def wish_state() -> WishState:
    return WishState(6, (
        ActiveWish(1, WishId.FOOD, "apple", 100, 14500),
        ActiveWish(3, WishId.WIN_OVERALL, "blackjack", 200, 14600, 900,
                   GameWishProgress(("session-a:1", "session-b:1"), 1, 1)),
        ActiveWish(5, WishId.PET, "pet", 300, 14700),
    ), ((WishArea.FOOD, 100), (WishArea.GAMES, 200), (WishArea.AFFECTION, 300)), 900)


class MoodletPersistenceTests(unittest.TestCase):
    def test_old_episode_has_explicit_unknown_cause_without_inventing_a_wish(self):
        raw = encode_moodlets(moodlet_state())
        for episode in raw["active"]:
            del episode["causes"]
            episode.pop("attribution")
        restored = decode_moodlets(raw, ELAPSED)
        for episode in restored.active:
            self.assertEqual(episode.causes, (MoodletCause(
                MoodletCauseKind.LEGACY, episode.last_trigger_at,
            ),))
            self.assertIsNone(episode.causes[0].wish)
        self.assertEqual(decode_moodlets(encode_moodlets(restored), ELAPSED), restored)

    def test_one_cause_per_stage_survives_save_checkpoint_and_decay_only(self):
        episode = MoodletEpisode(1, MoodletId.PRIDE, 3, 100, 100, 7200)
        for number, game in enumerate(("blackjack", "tic_tac_toe",
                                        "blackjack", "rock_paper_scissors"), 1):
            cause = MoodletCause(
                MoodletCauseKind.WISH_FULFILLED, 100 * number, f"round:{number}",
                MoodletAttribution.USER,
                MoodletWishCause(number, "win_overall", game, "total_wins", 3),
                game, MoodletOutcome.WIN,
            )
            episode = replace(episode, level=min(number, 3),
                              last_trigger_at=100 * number).with_cause(cause)
            self.assertEqual(episode.with_cause(cause), episode)
        self.assertEqual([c.wish.instance_id for c in episode.causes if c.wish],
                         [1, 2, 4])
        pet = PetState(updated_at=WALL, lived_seconds=ELAPSED,
                       moodlets=MoodletState(100, 2, (episode,)))
        checkpoint = pet.capture_checkpoint()
        with tempfile.TemporaryDirectory() as folder:
            store = StateStore(Path(folder) / "state.json")
            store.save(pet, PetSettings())
            pet = store.load_session(now=WALL).state
        self.assertEqual(pet.capture_checkpoint(), checkpoint)
        self.assertFalse(pet.wishes.active)  # No ended-wish archive is necessary.
        read = snapshot_pet(pet)
        self.assertEqual(read.moodlets[0].causes, episode.causes)
        with self.assertRaises(FrozenInstanceError):
            cast(Any, read.moodlets[0].causes[0].wish).target_id = "apple"
        healthy = NeedLevels(80, 80, 80, 80, 80)
        for seconds, tier in ((7200, 2), (14400, 1)):
            aged = advance_moodlets(pet.moodlets, seconds, elapsed=ELAPSED,
                                    before=healthy, after=healthy,
                                    definitions=MOODLET_CATALOG.definitions)
            self.assertEqual(aged.active[0].level, tier)
            self.assertEqual(aged.active[0].causes, episode.causes)
        ended = advance_moodlets(pet.moodlets, 21600, elapsed=ELAPSED,
                                 before=healthy, after=healthy,
                                 definitions=MOODLET_CATALOG.definitions)
        self.assertEqual(encode_moodlets(ended)["active"], [])
        pet.restore_checkpoint(replace(checkpoint, moodlets=ended))
        pet.restore_checkpoint(checkpoint)
        self.assertEqual(pet.moodlets.active[0].causes, episode.causes)

    def test_old_rolling_causes_keep_one_real_cause_without_inventing_stages(self):
        episode = MoodletEpisode(1, MoodletId.PRIDE, 3, 100, 300, 100)
        for number in (1, 2, 3):
            cause = MoodletCause(
                MoodletCauseKind.WISH_FULFILLED, 100 * number, f"round:{number}",
                wish=MoodletWishCause(number, "win_overall", "blackjack",
                                      "total_wins", 3),
                target_id="blackjack", outcome=MoodletOutcome.WIN,
            )
            episode = replace(episode, level=number,
                              last_trigger_at=100 * number).with_cause(cause)
        original = MoodletState(0, 2, (episode,))
        raw = encode_moodlets(original)
        for row in raw["active"][0]["causes"]:
            del row["level"]
        restored = decode_moodlets(raw, ELAPSED)
        self.assertEqual(restored.active[0].level, 3)
        self.assertEqual(len(restored.active[0].causes), 1)
        cause = restored.active[0].causes[0]
        self.assertIsNone(cause.level)
        self.assertEqual(cause.event_id, "round:3")
        self.assertEqual(decode_moodlets(encode_moodlets(restored), ELAPSED), restored)

    def test_one_large_success_has_one_cause_and_refused_food_has_handover_evidence(
        self,
    ):
        for key, level, source, outcome, actual in (
            (MoodletId.PRIDE, 2,
             MoodletWishCause(1, "win_overall", "blackjack", "total_wins", 3),
             MoodletOutcome.WIN, "blackjack"),
            (MoodletId.FOOD_FULFILLED, 1,
             MoodletWishCause(2, "avoid_food", "apple", "food_handover", 0),
             MoodletOutcome.HANDOVER, "apple"),
            (MoodletId.DISAPPOINTED, 1,
             MoodletWishCause(3, "avoid_round_loss", "blackjack", "next_non_loss", 1),
             MoodletOutcome.LOSS, "blackjack"),
        ):
            with self.subTest(key=key):
                cause = MoodletCause(MoodletCauseKind.WISH_FAILED
                                     if key == MoodletId.DISAPPOINTED
                                     else MoodletCauseKind.WISH_FULFILLED,
                                     100, "receipt:1", wish=source,
                                     target_id=actual, outcome=outcome)
                episode = MoodletEpisode(1, key, level, 100, 100, 100,
                                         causes=(cause,))
                state = MoodletState(0, 2, (episode,))
                self.assertEqual(decode_moodlets(encode_moodlets(state), ELAPSED),
                                 state)
                self.assertEqual(len(episode.causes), 1)

    def test_corrupt_unbounded_or_incompatible_cause_evidence_is_rejected(self):
        cause = MoodletCause(
            MoodletCauseKind.WISH_FULFILLED, 850, "round:1",
            wish=MoodletWishCause(1, "win_overall", "blackjack", "total_wins", 3),
            outcome=MoodletOutcome.WIN,
        )
        episode = MoodletEpisode(1, MoodletId.PRIDE, 2, 800, 850, 100,
                                 causes=(cause,))
        original = encode_moodlets(MoodletState(100, 2, (episode,)))
        with self.assertRaises(ValueError):
            episode.with_cause(MoodletCause(MoodletCauseKind.LEGACY, 850))
        for field, bad in (
            ("kind", "made_up"), ("kind", "wish_failed"),
            ("level", 0), ("level", 4), ("level", True),
            ("occurred_at", 799), ("occurred_at", 851),
            ("occurred_at", float("nan")), ("event_id", "x" * 129),
            ("event_id", None), ("wish", None), ("target_id", "apple"),
            ("outcome", "unknown"), ("object_id", {}), ("extra", "field"),
        ):
            raw = copy.deepcopy(original)
            raw["active"][0]["causes"][0][field] = bad
            with self.subTest(field=field, bad=bad), self.assertRaises(ValueError):
                decode_moodlets(raw, ELAPSED)
        for field, bad in (("definition_id", "missing"), ("objective", "retry_win"),
                           ("required_count", True), ("instance_id", 0),
                           ("target_id", "apple")):
            raw = copy.deepcopy(original)
            raw["active"][0]["causes"][0]["wish"][field] = bad
            with self.subTest(field=field), self.assertRaises(ValueError):
                decode_moodlets(raw, ELAPSED)
        same_stage = copy.deepcopy(original)
        first = same_stage["active"][0]["causes"][0]
        first["level"] = 1
        second = copy.deepcopy(first)
        second["event_id"] = "round:2"
        second["wish"]["instance_id"] = 2
        same_stage["active"][0]["causes"].append(second)
        with self.assertRaises(ValueError):
            decode_moodlets(same_stage, ELAPSED)
        for causes in ([], original["active"][0]["causes"] * 2,
                       original["active"][0]["causes"] * 4):
            raw = copy.deepcopy(original)
            raw["active"][0]["causes"] = causes
            with self.subTest(causes=len(causes)), self.assertRaises(ValueError):
                decode_moodlets(raw, ELAPSED)

    def test_round_trip_retains_all_parallel_episodes_and_used_relief(self):
        state = PetState(lived_seconds=ELAPSED, updated_at=WALL,
                         moodlets=moodlet_state())
        encoded = json.loads(json.dumps(encode_pet_state(state), allow_nan=False))
        for later_wall in (WALL, WALL + 86400, WALL - 86400):
            loaded = decode_pet_state(encoded, now=later_wall)
            self.assertEqual(loaded.moodlets, state.moodlets)
            self.assertEqual(loaded.lived_seconds, ELAPSED)
            self.assertEqual(loaded.mood, state.mood)
            self.assertEqual(loaded.friendship, state.friendship)
        self.assertEqual(len(state.moodlets.active), 4)  # No three-Moodlet limit.
        self.assertEqual(decode_moodlets(encoded["moodlets"], ELAPSED),
                         moodlet_state())

    def test_legacy_save_gets_empty_state_at_its_existing_elapsed_baseline(self):
        state = decode_pet_state({
            "satiety": 42, "friendship": 67,
            "time": {"version": 1, "lived_seconds": ELAPSED},
        }, now=WALL)
        self.assertEqual(state.moodlets, MoodletState(baseline=ELAPSED))
        self.assertEqual((state.satiety, state.friendship), (42, 67))
        self.assertEqual(decode_pet_state({}, now=WALL).moodlets, MoodletState())

    def test_immutable_checkpoint_restore_covers_episodes_and_counters(self):
        state = PetState(lived_seconds=ELAPSED, updated_at=WALL,
                         moodlets=moodlet_state())
        checkpoint = state.capture_checkpoint()
        identity = id(state)
        with self.assertRaises(AttributeError):
            cast(Any, state).moodlets = MoodletState()
        with self.assertRaises(FrozenInstanceError):
            cast(Any, state.moodlets.active[0]).relieved_levels = ()
        state.restore_checkpoint(replace(checkpoint, moodlets=MoodletState()))
        self.assertEqual(state.moodlets.active, ())
        state.restore_checkpoint(checkpoint)
        self.assertEqual(id(state), identity)
        self.assertEqual(state.moodlets, moodlet_state())
        self.assertEqual(copy.deepcopy(state).capture_checkpoint(), checkpoint)

    def test_stage_progress_and_paused_recovery_are_not_reset_on_load(self):
        episode = MoodletEpisode(2, MoodletId.HUNGER_WORN, 2, 200, 200, 2400,
                                 (2,), recovery_since=900)
        raw = encode_moodlets(MoodletState(100, 3, (episode,)))
        restored = decode_moodlets(raw, ELAPSED)
        self.assertEqual(restored.active, (episode,))
        raw["active"][0]["relieved_levels"].clear()
        self.assertEqual(restored.active[0].relieved_levels, (2,))

    def test_bad_sections_reject_duplicates_bounds_types_and_invented_history(self):
        original = encode_moodlets(moodlet_state())
        for field, bad in (
            ("version", True), ("version", 999), ("baseline", ELAPSED + 1),
            ("next_instance_id", 7), ("next_instance_id", True),
            ("active", original["active"] * 5),
        ):
            raw = copy.deepcopy(original)
            raw[field] = bad
            with self.subTest(field=field, bad=bad), self.assertRaises(ValueError):
                decode_moodlets(raw, ELAPSED)
        for field, bad in (
            ("instance_id", 0), ("definition_id", "unknown"), ("level", 4),
            ("level", True), ("started_at", 99), ("last_trigger_at", ELAPSED + 1),
            ("remaining_seconds", float("nan")), ("remaining_seconds", 1201),
            ("remaining_seconds", 10**1000), ("relieved_levels", [2, 2]),
            ("relieved_levels", [True]), ("pending_repetitions", 3),
            ("decay_paused", 1), ("decay_paused", True), ("recovery_since", 900),
            ("stage_typo", 42),
        ):
            raw = copy.deepcopy(original)
            raw["active"][0][field] = bad
            with self.subTest(field=field), self.assertRaises(ValueError):
                decode_moodlets(raw, ELAPSED)
        for duplicate in ("instance", "family"):
            raw = copy.deepcopy(original)
            if duplicate == "instance":
                raw["active"][1]["instance_id"] = 1
            else:
                raw["active"].append({**raw["active"][0], "instance_id": 6})
            with self.subTest(duplicate=duplicate), self.assertRaises(ValueError):
                decode_moodlets(raw, ELAPSED)

    def test_store_uses_one_v1_save_and_preserves_corruption_before_replacement(self):
        with tempfile.TemporaryDirectory() as folder:
            store = StateStore(Path(folder) / "state.json")
            pet = PetState(satiety=42, updated_at=WALL, lived_seconds=ELAPSED,
                           moodlets=moodlet_state())
            store.save(pet, PetSettings())
            self.assertEqual(json.loads(store.path.read_text())["version"], 1)
            loaded = store.load_session(now=WALL + 3600)
            self.assertEqual(loaded.state.moodlets, pet.moodlets)
            self.assertEqual(loaded.state.lived_seconds, ELAPSED)
            for bad in (None, {"version": 999}):
                raw = encode_pet_state(pet)
                raw["moodlets"] = bad
                original = json.dumps(dict(version=1, pet=raw)).encode()
                store.path.write_bytes(original)
                loaded = store.load_session(now=WALL)
                self.assertEqual(loaded.state.satiety, 42)
                self.assertEqual(loaded.state.moodlets, MoodletState(ELAPSED))
                store.save(loaded.state, loaded.settings)
                self.assertIn(original, [p.read_bytes() for p in
                                         Path(folder).glob("*.aiko-save-backup")])

    def test_unloaded_invalid_section_is_backed_up_and_missing_section_is_legacy(self):
        with tempfile.TemporaryDirectory() as folder:
            store = StateStore(Path(folder) / "state.json")
            legacy = dict(version=1, pet={"satiety": 42})
            store.path.write_text(json.dumps(legacy), encoding="utf-8")
            loaded = store.load_session(now=WALL)
            store.save(loaded.state, loaded.settings)
            self.assertFalse(tuple(Path(folder).glob("*.aiko-save-backup")))
            corrupt = json.dumps(dict(version=1, pet={"moodlets": []})).encode()
            store.path.write_bytes(corrupt)
            store.save(PetState(updated_at=WALL), PetSettings())
            self.assertEqual([p.read_bytes() for p in
                              Path(folder).glob("*.aiko-save-backup")], [corrupt])


class WishPersistenceTests(unittest.TestCase):
    def test_legacy_game_goals_keep_their_original_meaning_and_progress(self):
        for key, objective, progress in (
            (WishId.PLAY_GAME, WishObjective.SESSION_ROUNDS,
             GameWishProgress(("a:1",), 1, 0, "a")),
            (WishId.WIN_ROUND, WishObjective.RETRY_WIN,
             GameWishProgress(("a:1",), 0, 1)),
            (WishId.WIN_OVERALL, WishObjective.BLOCK_MAJORITY,
             GameWishProgress(("a:1", "b:1"), 1, 1)),
        ):
            with self.subTest(key=key):
                wish = ActiveWish(1, key, "blackjack", 100, 14500, game=progress)
                original = WishState(2, (wish,), ((WishArea.GAMES, 100),))
                raw = encode_wishes(original)
                del raw["active"][0]["goal"]
                del raw["active"][0]["pinned"]
                del raw["active"][0]["game"]["completed_rounds"]
                restored = decode_wishes(raw, ELAPSED)
                self.assertEqual(restored, original)
                self.assertEqual(restored.active[0].goal_snapshot.objective, objective)
                self.assertEqual(decode_wishes(encode_wishes(restored), ELAPSED),
                                 original)

    def test_pinned_cumulative_goal_keeps_large_counts_with_bounded_receipts(self):
        wish = ActiveWish(
            1, WishId.WIN_OVERALL, "blackjack", 100, 14500,
            game=GameWishProgress(("a:9999", "a:10000"), 2, 9998, None, 10000),
            goal=WishGoal(WishObjective.TOTAL_WINS, 3), pinned=True,
        )
        state = WishState(2, (wish,), ((WishArea.GAMES, 100),))
        # Decoding is passive, including after the original unpinned deadline.
        self.assertEqual(decode_wishes(encode_wishes(state), 20000), state)
        pet = PetState(updated_at=WALL, lived_seconds=20000, wishes=state)
        before = pet.capture_checkpoint()
        loaded = decode_pet_state(encode_pet_state(pet), now=WALL)
        self.assertEqual(loaded.capture_checkpoint(), before)
        read = snapshot_pet(loaded).wishes[0]
        self.assertTrue(read.pinned)
        self.assertEqual(read.goal, wish.goal_snapshot)
        self.assertIsNotNone(read.game)
        assert read.game is not None
        self.assertEqual(read.game.completed_rounds, 10000)
        self.assertEqual(read.game.required_count, 3)
        self.assertEqual(len(wish.game.round_ids), 2)

    def test_original_count_survives_catalogue_tuning_and_legacy_majority_completes(
        self,
    ):
        state = wish_state()
        definitions = dict(WISH_CATALOG.definitions)
        definitions[WishId.WIN_OVERALL] = replace(
            definitions[WishId.WIN_OVERALL], round_count=5,
            goal=WishGoal(WishObjective.TOTAL_WINS, 5),
        )
        with patch("aiko_pet.infrastructure.wish_codec.WISH_CATALOG",
                   WishCatalog(definitions)):
            loaded = decode_wishes(encode_wishes(state), ELAPSED)
        self.assertEqual(loaded.active[1].goal_snapshot,
                         WishGoal(WishObjective.BLOCK_MAJORITY, 3))
        pet = PetState(updated_at=WALL, lived_seconds=ELAPSED, wishes=loaded)
        pet.complete_wish_round(instance_id=3, game_id="blackjack", session_id="c",
                                round_id="c:1", started_at=950, outcome="win")
        self.assertNotIn(3, [w.instance_id for w in pet.wishes.active])
        self.assertEqual(pet.moodlets.active[0].definition_id, MoodletId.PRIDE)
        self.assertEqual(pet.moodlets.active[0].level, 2)
        cumulative = replace(state.active[1],
                             goal=WishGoal(WishObjective.TOTAL_WINS, 3))
        state = replace(state, active=(state.active[0], cumulative, state.active[2]))
        with patch("aiko_pet.infrastructure.wish_codec.WISH_CATALOG",
                   WishCatalog(definitions)):
            loaded = decode_wishes(encode_wishes(state), ELAPSED)
        self.assertEqual(loaded.active[1].goal_snapshot.required_count, 3)

    def test_explicit_goal_pin_and_attempt_count_reject_corruption(self):
        original = encode_wishes(wish_state())
        for field, bad in (("pinned", 1), ("goal", None),
                           ("goal", dict(objective="total_wins", required_count=True)),
                           ("goal", dict(objective="next_win", required_count=1))):
            raw = copy.deepcopy(original)
            raw["active"][1][field] = bad
            with self.subTest(field=field, bad=bad), self.assertRaises(ValueError):
                decode_wishes(raw, ELAPSED)
        for field, bad in (("completed_rounds", True), ("completed_rounds", 10000),
                           ("completed_rounds", 1), ("round_ids", [str(i) for i
                                                                  in range(101)])):
            raw = copy.deepcopy(original)
            raw["active"][1]["game"][field] = bad
            with self.subTest(field=field), self.assertRaises(ValueError):
                decode_wishes(raw, ELAPSED)

    def test_round_trip_preserves_unspoken_spoken_and_cross_session_goals(self):
        pet = PetState(lived_seconds=ELAPSED, updated_at=WALL,
                       moodlets=moodlet_state(), wishes=wish_state())
        raw = json.loads(json.dumps(encode_pet_state(pet), allow_nan=False))
        for now in (WALL, WALL + 86400, WALL - 86400):
            loaded = decode_pet_state(raw, now=now)
            self.assertEqual(loaded.capture_checkpoint(), pet.capture_checkpoint())
            self.assertIsNone(loaded.wishes.active[0].expressed_at)
            self.assertEqual(loaded.wishes.active[1].game,
                             GameWishProgress(("session-a:1", "session-b:1"), 1, 1))
        # The codec stores even past deadlines unchanged; progression resolves them.
        self.assertEqual(decode_wishes(raw["wishes"], 20000), pet.wishes)

    def test_completed_identity_and_pacing_survive_an_empty_active_collection(self):
        retired = replace(wish_state(), active=())
        loaded = decode_wishes(encode_wishes(retired), ELAPSED)
        self.assertEqual(loaded, retired)
        self.assertEqual(loaded.next_instance_id, 6)
        self.assertEqual(loaded.last_created_at, 300)
        legacy = encode_wishes(wish_state())
        legacy.pop("refill_not_before")
        self.assertIsNone(decode_wishes(legacy, ELAPSED).refill_not_before)
        self.assertEqual(loaded.last_expressed_at, 900)
        self.assertEqual(loaded.active, ())
        raw = encode_wishes(retired)
        raw["next_instance_id"] = 1
        with self.assertRaises(ValueError):
            decode_wishes(raw, ELAPSED)
        self.assertEqual(decode_pet_state({"satiety": 42}, now=WALL).wishes,
                         WishState())

    def test_shared_play_keeps_its_session_and_bounded_round_receipts(self):
        wish = ActiveWish(1, WishId.PLAY_GAME, "tic_tac_toe", 200, 14600,
                          game=GameWishProgress(("session-a:1",), 0, 1, "session-a"))
        state = WishState(2, (wish,), ((WishArea.GAMES, 200),))
        raw = encode_wishes(state)
        decoded = decode_wishes(raw, ELAPSED)
        self.assertEqual(decoded, state)
        raw["active"][0]["game"]["round_ids"].clear()
        self.assertEqual(decoded.active[0].game.round_ids, ("session-a:1",))

    def test_bad_counts_targets_timestamps_and_progress_are_rejected(self):
        original = encode_wishes(wish_state())
        for field, bad in (
            ("version", True), ("version", 2), ("next_instance_id", 5),
            ("active", original["active"] * 2),
            ("last_created_by_area", {"sleep": 100}),
            ("last_created_by_area", {"food": 1001}),
            ("last_expressed_at", None), ("last_expressed_at", float("nan")),
            ("refill_not_before", -1), ("refill_not_before", True),
            ("refill_not_before", float("inf")), ("refill_not_before", 1721),
        ):
            raw = copy.deepcopy(original)
            raw[field] = bad
            with self.subTest(field=field), self.assertRaises(ValueError):
                decode_wishes(raw, ELAPSED)
        for field, bad in (
            ("instance_id", True), ("definition_id", "sleep"),
            ("target_id", "energy_drink"), ("target_id", {}),
            ("created_at", -1), ("created_at", 1001), ("created_at", 99),
            ("expires_at", 14501), ("expires_at", 100), ("expires_at", float("inf")),
            ("expressed_at", 99), ("expressed_at", 1001), ("unexpected", "field"),
        ):
            raw = copy.deepcopy(original)
            raw["active"][0][field] = bad
            with self.subTest(field=field), self.assertRaises(ValueError):
                decode_wishes(raw, ELAPSED)
        for field, bad in (
            ("wins", 3), ("wins", True), ("losses", 2),
            ("round_ids", ["one"] * 2), ("round_ids", ["1", "2", "3", "4"]),
            ("round_ids", [True]), ("session_id", "x" * 129),
        ):
            raw = copy.deepcopy(original)
            raw["active"][1]["game"][field] = bad
            with self.subTest(field=field), self.assertRaises(ValueError):
                decode_wishes(raw, ELAPSED)
        for duplicate in ("instance", "area"):
            raw = copy.deepcopy(original)
            if duplicate == "instance":
                raw["active"][1]["instance_id"] = 1
            else:
                raw["active"][1] = {**raw["active"][0], "instance_id": 3}
            with self.subTest(duplicate=duplicate), self.assertRaises(ValueError):
                decode_wishes(raw, ELAPSED)

    def test_nongame_and_sessionless_shared_play_cannot_claim_round_progress(self):
        raw = encode_wishes(wish_state())
        raw["active"][0]["game"]["session_id"] = "not-a-food-event"
        with self.assertRaises(ValueError):
            decode_wishes(raw, ELAPSED)
        raw = encode_wishes(wish_state())
        raw["active"][1]["definition_id"] = "play_game"
        with self.assertRaises(ValueError):
            decode_wishes(raw, ELAPSED)

    def test_complete_checkpoint_owns_and_restores_both_collections(self):
        pet = PetState(updated_at=WALL, lived_seconds=ELAPSED,
                       moodlets=moodlet_state(), wishes=wish_state())
        before = pet.capture_checkpoint()
        with self.assertRaises(AttributeError):
            cast(Any, pet).wishes = WishState()
        with self.assertRaises(FrozenInstanceError):
            cast(Any, pet.wishes.active[1].game).wins = 3
        pet.restore_checkpoint(replace(before, moodlets=MoodletState(),
                                       wishes=WishState()))
        pet.restore_checkpoint(before)
        self.assertEqual(copy.deepcopy(pet).capture_checkpoint(), before)
        self.assertEqual(pet.wishes, wish_state())

    def test_store_restores_both_and_only_discards_an_invalid_wish_section(self):
        with tempfile.TemporaryDirectory() as folder:
            store = StateStore(Path(folder) / "state.json")
            pet = PetState(updated_at=WALL, lived_seconds=ELAPSED,
                           moodlets=moodlet_state(), wishes=wish_state())
            store.save(pet, PetSettings())
            self.assertEqual(store.load_session(now=WALL).state, pet)
            for invalid in (None, {"version": 999}):
                raw: dict[str, Any] = dict(version=1, pet=encode_pet_state(pet))
                raw["pet"]["wishes"] = invalid
                original = json.dumps(raw).encode()
                store.path.write_bytes(original)
                restored = store.load_session(now=WALL)
                self.assertEqual(restored.state.wishes, WishState())
                self.assertEqual(restored.state.moodlets, pet.moodlets)
                store.save(restored.state, restored.settings)
                self.assertIn(original, [p.read_bytes() for p in
                                         Path(folder).glob("*.aiko-save-backup")])
            # Cold replacement must also preserve invalid optional wish data.
            store.path.write_bytes(original)
            previous_backups = len(tuple(Path(folder).glob("*.aiko-save-backup")))
            store.save(pet, PetSettings())
            self.assertEqual(len(tuple(Path(folder).glob("*.aiko-save-backup"))),
                             previous_backups + 1)
            self.assertEqual(store.load_session(now=WALL).state, pet)
