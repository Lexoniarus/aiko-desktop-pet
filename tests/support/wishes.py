"""Shared wishes fixtures without importing test cases."""

from __future__ import annotations

from dataclasses import replace

from aiko_pet.application.active_time import ActiveSessionClock, SessionInputs
from aiko_pet.application.commands import CareCommand
from aiko_pet.application.controller import CareController
from aiko_pet.application.game_experience import GameExperienceCoordinator
from aiko_pet.application.social_content import SocialCategory, prepare_social_content
from aiko_pet.infrastructure.character_mind import make_aiko_mind
from aiko_pet.pet.mind.adaptive import AdaptiveRoutine
from aiko_pet.pet.state import PetState
from aiko_pet.pet.wish_catalog import WISH_CATALOG
from aiko_pet.pet.wish_matching import assign_activity_wish
from aiko_pet.pet.wishes import (
    ActiveWish,
    GameWishProgress,
    WishArea,
    WishId,
    WishState,
)
from aiko_pet.presentation.playback import ReactionPlayer
from support.payloads import fact_payload, joke_payload
from tools.reaction_test_support import FakeScheduler


def food_handover_wishes_pet_with(*wishes):
    return PetState(
        lived_seconds=100,
        satiety=100,
        friendship=50,
        wishes=WishState(
            max((w.instance_id for w in wishes)) + 1,
            wishes,
            ((WishArea.FOOD, 0),),
            refresh_at=600,
        ),
    )


def wishes(instance=1, created=0):
    return WishState(
        instance + 1,
        (ActiveWish(instance, WishId.PET, "pet", created, created + 14400),),
        ((WishArea.AFFECTION, created),),
    )


DEFINITIONS = WISH_CATALOG.definitions


def wish(key, reference=None, *, instance=1, at=0, pinned=False, progressed=False):
    definition = DEFINITIONS[key]
    target = definition.bind_target(reference)
    return ActiveWish(
        instance,
        key,
        reference or "",
        at,
        600,
        goal=definition.goal,
        target=target,
        pinned=pinned,
        game=GameWishProgress(("earlier:1",), 1, 0)
        if progressed
        else GameWishProgress(),
    )


def assigned(*wishes, area=WishArea.GAMES, target="blackjack", elapsed=100):
    return assign_activity_wish(
        WishState(active=wishes), area, target, elapsed=elapsed, definitions=DEFINITIONS
    )


WISH_FOOD_WALL = 1800000000.0


def food_pet(wish_id=WishId.FOOD, **values):
    return PetState(
        updated_at=WISH_FOOD_WALL,
        lived_seconds=100,
        satiety=30,
        friendship=50,
        wishes=WishState(
            2,
            (
                ActiveWish(
                    1,
                    wish_id,
                    "apple",
                    0,
                    14400,
                    goal=WISH_CATALOG.definitions[wish_id].goal,
                ),
            ),
            ((WishArea.FOOD, 0),),
        ),
        **values,
    )


WISH_GAME_ASSIGNMENT_WALL = 1800000000
INPUTS = SessionInputs(WISH_GAME_ASSIGNMENT_WALL, 0, False, None, False, False, None)


def coordinator(pet):
    return GameExperienceCoordinator(
        pet,
        make_aiko_mind(started_at=0),
        AdaptiveRoutine(),
        clock=ActiveSessionClock(lambda: 0),
    )


def wish_game_assignment_pet_with(*wishes):
    return PetState(
        updated_at=WISH_GAME_ASSIGNMENT_WALL,
        lived_seconds=100,
        friendship=50,
        wishes=WishState(
            max((w.instance_id for w in wishes)) + 1,
            wishes,
            ((WishArea.GAMES, 0),),
            refresh_at=600,
        ),
    )


def finish(runtime, event, outcome):
    runtime.observe_round(replace(event, outcome=outcome), INPUTS)


WISH_SOCIAL_ASSIGNMENT_WALL = 1800000000


class SocialHarness:
    def __init__(self, *wishes):
        self.pet = PetState(
            updated_at=WISH_SOCIAL_ASSIGNMENT_WALL,
            lived_seconds=100,
            friendship=50,
            social=50,
            wishes=WishState(
                max((w.instance_id for w in wishes), default=0) + 1,
                wishes,
                ((WishArea.SOCIAL, 0),) if wishes else (),
                refresh_at=600,
            ),
        )
        self.inputs = SessionInputs(
            WISH_SOCIAL_ASSIGNMENT_WALL, 0, False, None, False, False, None
        )
        self.controller = CareController(
            self.pet,
            make_aiko_mind(started_at=0),
            AdaptiveRoutine(),
            clock=ActiveSessionClock(lambda: 0),
        )
        self.scheduler = FakeScheduler()
        self.player = ReactionPlayer(
            schedule=self.scheduler.schedule,
            cancel_timer=self.scheduler.cancel,
            display_emote=lambda *_: None,
            display_text=lambda *_: None,
            start_action=lambda *_: None,
            mark_spoken=lambda: None,
            is_closed=lambda: False,
            social_completed=lambda completion: self.controller.complete_social(
                completion, self.inputs, arrangement_ready=False
            ),
        )

    def admit(self, category="chat"):
        content = None
        if category != "chat":
            kind = SocialCategory(category)
            content = prepare_social_content(
                kind, fact_payload() if category == "fact" else joke_payload(kind)
            )
        reaction = self.controller.execute(
            CareCommand("talk", conversation=content), self.inputs
        ).reaction
        assert reaction is not None
        self.player.play(reaction)
        return reaction.completed_social

    def finish(self):
        self.scheduler.drain()
