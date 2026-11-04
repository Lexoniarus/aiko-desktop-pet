"""Shared social fixtures without importing test cases."""

from __future__ import annotations

import random
from dataclasses import replace
from typing import Any

from aiko_pet.application.commands import CareCommand
from aiko_pet.application.social_candidates import JokeCatalog
from aiko_pet.application.social_content import (
    PreparedSocialContent,
    SocialCategory,
    SocialProvider,
    default_provider,
    prepare_social_content,
)
from aiko_pet.application.social_fetch import SocialFetchRequest, SocialFetchResult
from aiko_pet.games.contracts import GameId, GameRoundEvent
from aiko_pet.infrastructure.character_mind import make_aiko_mind
from aiko_pet.pet.moodlets import (
    MoodletCause,
    MoodletCauseKind,
    MoodletEpisode,
    MoodletOutcome,
)
from aiko_pet.pet.routine import context_at
from aiko_pet.pet.wishes import WishId
from support.payloads import fact_payload, joke_payload
from support.wishes import (
    INPUTS,
    WISH_GAME_ASSIGNMENT_WALL,
    SocialHarness,
    coordinator,
    wish,
    wish_game_assignment_pet_with,
)
from tools.pet_test_support import require_test_value

TEST_JOKE_CATALOG = JokeCatalog(0, 100000, 253402300799.0)


class SocialTestClock:
    def __init__(self) -> None:
        self.now = 1800000000.0

    def __call__(self) -> float:
        return self.now


class ManualSocialWorker:
    def __init__(self, *, clock: SocialTestClock | None = None) -> None:
        self.requests: list[tuple[SocialCategory, object]] = []
        self.providers: list[SocialProvider] = []
        self.clock = clock or SocialTestClock()
        self.result: SocialFetchResult | None = None
        self.closed = False
        self.plans: list[SocialFetchRequest | None] = []

    def start(
        self,
        category: SocialCategory,
        token: object,
        provider: SocialProvider | None = None,
        *,
        request: SocialFetchRequest | None = None,
    ) -> None:
        self.plans.append(request)
        self.requests.append((category, token))
        self.providers.append(provider or default_provider(category))

    def poll(self) -> SocialFetchResult | None:
        result, self.result = (self.result, None)
        return result

    def complete(self, identifier: int, *, fail: bool = False) -> None:
        category, token = self.requests[-1]
        provider = self.providers[-1]
        payload = (
            fact_payload(str(identifier))
            if category == SocialCategory.FACT
            else joke_payload(category, identifier)
        )
        field = (
            "text"
            if category == SocialCategory.FACT
            else "joke"
            if category == SocialCategory.SINGLE
            else "setup"
        )
        payload[field] = f"Test {identifier}."
        if provider == SocialProvider.QUOTATIONS:
            payload = dict(
                quote=f"Test {identifier}.",
                language="de",
                link=f"https://www.zitat-service.de/de/quotations/{identifier}",
                authorName="Testautor",
            )
        elif provider == SocialProvider.WITZAPI:
            payload = dict(
                language="de",
                text=f"Test {identifier}? Antwort {identifier}."
                if category == SocialCategory.TWO_PARTS
                else f"Test {identifier}.",
            )
        content = (
            None
            if fail
            else prepare_social_content(category, payload, provider=provider)
        )
        self.clock.now += 10
        self.result = SocialFetchResult(
            token,
            category,
            content,
            failure="temporary" if fail else None,
            retry_at=self.clock.now + 60 if fail else None,
        )

    def close(self) -> None:
        self.closed = True


def quote_payload(identifier: int = 1) -> dict[str, Any]:
    return dict(
        quote="Der Zweifel ist der Weisheit Anfang.",
        language="de",
        link=f"https://www.zitat-service.de/de/quotations/{identifier}",
        authorName="René Descartes",
        authorId=262,
        authorLink="https://de.wikipedia.org/wiki/Ren%C3%A9_Descartes",
        source="Test-Ausgabe",
        sourceLink="https://example.org/original",
    )


def quotation(payload: dict[str, Any]):
    return prepare_social_content(
        SocialCategory.SINGLE, payload, provider=SocialProvider.QUOTATIONS
    )


def originals() -> tuple[PreparedSocialContent, ...]:
    fact = fact_payload()
    fact["text"] = "Ein langer vollständiger Testsatz mit unveränderten Wörtern. " * 4
    return (
        prepare_social_content(
            SocialCategory.SINGLE, joke_payload(SocialCategory.SINGLE)
        ),
        quotation(quote_payload()),
        prepare_social_content(
            SocialCategory.TWO_PARTS, joke_payload(SocialCategory.TWO_PARTS)
        ),
        prepare_social_content(SocialCategory.FACT, fact),
    )


def play_content(harness: SocialHarness, content: PreparedSocialContent):
    outcome = harness.controller.execute(
        CareCommand("talk", conversation=content), harness.inputs
    )
    reaction = require_test_value(outcome.reaction)
    harness.player.play(reaction)
    return require_test_value(reaction.completed_social)


def mastermind_win():
    pet = wish_game_assignment_pet_with(wish(WishId.WIN_ROUND, "mastermind"))
    runtime = coordinator(pet)
    start = GameRoundEvent(GameId.MASTERMIND, "actual", 1)
    runtime.observe_round(start, INPUTS)
    runtime.observe_round(replace(start, outcome="loss"), INPUTS)
    return pet


def talk(pet, *, context=None):
    mind = make_aiko_mind(rng=random.Random(0), started_at=0)
    return require_test_value(
        mind.select_reaction(
            "talk", pet, context_at(WISH_GAME_ASSIGNMENT_WALL), 10, dialogue=context
        )
    )


def actual(number: int = 1, target: str = "chat") -> MoodletCause:
    return MoodletCause(
        MoodletCauseKind.INTERACTION,
        number,
        f"actual:{number}",
        target_id=target,
        outcome=MoodletOutcome.COMPLETED,
    )


def episode(number, family, level=1, *causes):
    return MoodletEpisode(number, family, level, 0, 50, 600, causes=causes)
