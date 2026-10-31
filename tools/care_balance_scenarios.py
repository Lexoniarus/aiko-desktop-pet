"""Seeded acceptance scenarios using the actual care/wish/progression policies.

Round outcomes are a declared balanced fixture, not a forecast of player skill.
No needs, Moodlets or relationship values are replaced after initialization.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from aiko_pet.games.contracts import GameId, GameResult, RoundOutcome  # noqa: E402
from aiko_pet.pet.consumption import ConsumptionOrigin  # noqa: E402
from aiko_pet.pet.food import FoodActivity  # noqa: E402
from aiko_pet.pet.fun import GameExperience  # noqa: E402
from aiko_pet.pet.interaction_events import SocialCompletion  # noqa: E402
from aiko_pet.pet.moodlets import MoodletCauseKind  # noqa: E402
from aiko_pet.pet.state import PetState  # noqa: E402
from aiko_pet.pet.wish_catalog import WISH_CATALOG  # noqa: E402
from aiko_pet.pet.wish_matching import assign_activity_wish  # noqa: E402
from aiko_pet.pet.wishes import WishArea, WishContext, WishTargetMode  # noqa: E402

START = datetime(2026, 10, 12, 7).timestamp()
PHASES = (0, 6 * 3600, 12 * 3600, 15 * 3600 + 1800)


class CareScenario:
    def __init__(self, *, friendship: float, intensive: bool, seed: int) -> None:
        self.pet = PetState(
            updated_at=START,
            friendship=friendship,
            satiety=100,
            energy=100,
            fun=100,
            social=100,
            affection=100,
            mood=80,
        )
        self.intensive = intensive
        self.selection = random.Random(seed)
        self.results = random.Random(seed + 1000)
        self.serial = 0
        self.completed = 0
        self.rounds = 0
        self.social = 0

    def context(self) -> WishContext:
        evidence = self.pet.moodlets.care_evidence
        recent = (
            next(
                (e for e in reversed(evidence.experiences) if e.activity == "play"),
                None,
            )
            if evidence
            else None
        )
        return WishContext(
            online_social=True,
            prepared_social=frozenset(("single", "twopart", "fact")),
            recent_play=recent,
        )

    def feed(self, food: str) -> None:
        self.serial += 1
        receipt = f"scenario:gift:{self.serial}"
        obj = f"scenario:food:{self.serial}"
        self.pet.begin_food_handover(receipt, object_id=obj)
        self.pet.recognize_food_handover(receipt, food)
        self.pet.consume_item(
            food, ConsumptionOrigin.HANDOVER, now=self.pet.updated_at, object_id=obj
        )
        self.pet.release_food_handovers(frozenset((obj,)))

    def visit(
        self, *, social_budget: int, base_foods: tuple[str, ...], ordinary_petting: bool
    ) -> None:
        pet = self.pet
        before = {w.instance_id for w in pet.wishes.active}
        desired = tuple(pet.wishes.active)
        petted = False
        for wish in desired:
            area = WISH_CATALOG.definitions[wish.definition_id].area
            if area == WishArea.FOOD:
                food = wish.target_id
                if (
                    wish.target is not None
                    and wish.target.mode == WishTargetMode.EXCLUDE
                ):
                    food = "onigiri" if food != "onigiri" else "sandwich"
                self.feed(food)
            elif area == WishArea.AFFECTION:
                pet.interact("pet", now=pet.updated_at)
                petted = True
        for food in base_foods:
            pet.consume_item(food, ConsumptionOrigin.HANDOVER, now=pet.updated_at)
        for _ in range(social_budget):
            selected = next(
                (
                    w
                    for w in pet.wishes.active
                    if WISH_CATALOG.definitions[w.definition_id].area == WishArea.SOCIAL
                ),
                None,
            )
            category = selected.target_id if selected and selected.target_id else "chat"
            assigned = assign_activity_wish(
                pet.wishes,
                WishArea.SOCIAL,
                category,
                elapsed=pet.lived_seconds,
                definitions=WISH_CATALOG.definitions,
            )
            pet.interact("talk", now=pet.updated_at)
            self.serial += 1
            pet.complete_social_experience(
                SocialCompletion(
                    category,
                    assigned.instance_id if assigned else None,
                    f"scenario:{self.serial}",
                    pet.lived_seconds,
                )
            )
            self.social += 1
        if ordinary_petting and not petted:
            pet.interact("pet", now=pet.updated_at)
        session = f"scenario:session:{self.serial}"
        game = GameId.ROCK_PAPER_SCISSORS.value
        wins = losses = 0
        selected = next(
            (
                w
                for w in pet.wishes.active
                if WISH_CATALOG.definitions[w.definition_id].area == WishArea.GAMES
            ),
            None,
        )
        if selected and selected.target_id:
            game = selected.target_id
            if selected.target and selected.target.mode == WishTargetMode.EXCLUDE:
                game = "mastermind" if game != "mastermind" else "blackjack"
        for number in (1, 2):
            assigned = assign_activity_wish(
                pet.wishes,
                WishArea.GAMES,
                game,
                elapsed=pet.lived_seconds,
                definitions=WISH_CATALOG.definitions,
            )
            outcomes: tuple[RoundOutcome, ...] = ("win", "loss", "draw")
            outcome: GameResult = self.results.choice(outcomes)
            if game == GameId.QUIZ.value:
                outcome = "completed"
            round_id = f"{session}:{number}"
            pet.record_completed_game_round(
                game_id=game, round_id=round_id, outcome=outcome
            )
            if assigned:
                pet.complete_wish_round(
                    assigned.instance_id,
                    game_id=game,
                    session_id=session,
                    round_id=round_id,
                    started_at=pet.lived_seconds,
                    outcome=outcome,
                )
            pet.finish_game_round_experience(game_id=game, round_id=round_id)
            wins += outcome == "win"
            losses += outcome == "loss"
            self.rounds += 1
        experience = (
            GameExperience(game, 2) if game == GameId.QUIZ.value
            else GameExperience(game, 2, wins, 2 - wins - losses, losses)
        )
        pet.record_game_experience(experience, now=pet.updated_at)
        pet.complete_play_session(
            game_id=game, session_id=session, round_id=f"{session}:2"
        )
        self.serial += 1
        successes = {
            c.wish.instance_id
            for e in pet.moodlets.active
            for c in e.causes
            if c.kind == MoodletCauseKind.WISH_FULFILLED and c.wish
        }
        self.completed += len(before & successes)

    def run(self, days: int) -> list[dict[str, float | int]]:
        rows = []
        foods = (("onigiri",), ("sandwich", "apple"), ("sandwich",), ("dorayaki",))
        for day in range(days):
            origin = START + day * 86400
            if self.pet.sleeping:
                self.pet.interact("sleep", now=origin)
            initial, completed = self.pet.friendship, self.completed
            visits = {
                phase + offset: (i, offset)
                for i, phase in enumerate(PHASES)
                for offset in ((0, 600, 1200, 1800) if self.intensive else (0,))
            }
            for second in sorted(set(range(0, 16 * 3600 + 1, 600)) | set(visits)):
                self.pet.advance(origin + second, food_activity=FoodActivity(0.2, 0.5))
                self.pet.evaluate_wishes(self.context(), rng=self.selection)
                if second in visits:
                    i, offset = visits[second]
                    self.visit(
                        social_budget=2 if offset == 0 else 1,
                        base_foods=foods[i] if offset == 0 else (),
                        ordinary_petting=offset == 0,
                    )
                    if self.intensive and i > 0 and offset == 0:
                        self.pet.interact("energy_drink", now=origin + second)
            self.pet.interact("sleep", now=origin + 16 * 3600)
            self.pet.advance(origin + 86400, food_activity=FoodActivity(0.2, 0.5))
            rows.append(
                dict(
                    day=day + 1,
                    start=round(initial, 4),
                    end=round(self.pet.friendship, 4),
                    successes=self.completed - completed,
                    mood=round(self.pet.mood, 2),
                )
            )
        return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=int, default=5)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    reports = []
    for intensive, friendship in ((False, 70), (True, 90), (False, 90)):
        scenario = CareScenario(
            friendship=friendship, intensive=intensive, seed=args.seed
        )
        rows = scenario.run(args.days)
        reports.append(
            dict(
                intensive=intensive,
                initial=friendship,
                seed=args.seed,
                rows=rows,
                rounds=scenario.rounds,
                social=scenario.social,
            )
        )
        print(
            json.dumps(
                dict(
                    intensive=intensive,
                    initial=friendship,
                    final=rows[-1]["end"],
                    morning_range=[
                        min(r["end"] for r in rows),
                        max(r["end"] for r in rows),
                    ],
                    successes=[r["successes"] for r in rows],
                )
            ),
            flush=True,
        )
    if args.report is not None:
        args.report.write_text(json.dumps(reports, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
