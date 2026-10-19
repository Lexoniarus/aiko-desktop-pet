"""Coordinate deliberate care and social playback through existing owners."""

from __future__ import annotations

import time
import tkinter as tk
from collections.abc import Callable

from ..application.active_time import SessionInputs
from ..application.commands import CareCommand
from ..application.contact import ContactCoordinator
from ..application.router import ApplicationRouter
from ..application.social_content import PreparedSocialContent
from ..application.social_coordinator import (
    SocialContentCoordinator,
    SocialContentWorker,
)
from ..infrastructure.social_api import HttpSocialContentWorker
from ..pet.food import FoodId
from ..pet.mind.catalog import Reaction
from ..pet.routine import TimeContext
from ..pet.state import PetState
from ..ui.pet_view.animated_pet import AnimatedPet
from ..ui.pet_view.care_presenter import CarePresenter, CareViewPorts
from ..ui.pet_view.reaction_player import ReactionPlayer
from ..ui.pet_view.speech_presenter import SpeechPresenter
from ..ui.windows.hover_ui import HoverUi
from .social_runtime import SocialConversationRuntime, SocialRuntimePorts
from .world_runtime import DesktopWorldRuntime


class DesktopCareRuntime:
    def __init__(
        self, *, root: tk.Tk, state: PetState, router: ApplicationRouter,
        world: DesktopWorldRuntime, contact: ContactCoordinator,
        animated: AnimatedPet, player: ReactionPlayer,
        speech: SpeechPresenter, hover: HoverUi,
        cancel_action: Callable[[float], None],
        start_action: Callable[[str, float], None],
        react: Callable[[Reaction, int], None],
        inputs: Callable[[float, float], SessionInputs],
        set_context: Callable[[TimeContext], None], save: Callable[[], None],
        is_closed: Callable[[], bool], game_open: Callable[[], bool],
        social_worker: SocialContentWorker | None = None,
    ) -> None:
        self._root, self._state, self._router = root, state, router
        self._world, self._contact = world, contact
        self._player = player
        self._presenter = CarePresenter(CareViewPorts(
            set_item=animated.set_food_overlay, cancel_action=cancel_action,
            start_action=start_action, cancel_followup=player.cancel,
            react=react, show_text=speech.show_text,
            refresh_toolbar=hover.refresh_toolbar, refresh_status=hover.refresh_status,
        ))
        self._inputs, self._set_context, self._save = inputs, set_context, save
        self._is_closed = is_closed
        content = SocialContentCoordinator(
            social_worker if social_worker is not None else HttpSocialContentWorker(),
        )
        self.social = SocialConversationRuntime(content, SocialRuntimePorts(
            can_start=self._can_start_social,
            defer=self._defer_social, start=self._start_social,
            show_wait=lambda reaction: player.play(reaction, animate=False),
            clear_wait=self._clear_wait,
            can_wait=lambda: (not is_closed() and not state.sleeping
                              and not game_open()),
        ))

    def interact(
        self, action: str, *, food_id: FoodId | None = None,
        conversation: PreparedSocialContent | None = None,
    ) -> None:
        if conversation is None:
            self.social.cancel()
        if self._world.cursor.carrying:
            self._world.cursor.cancel()
        if (self._world.interaction.active
                or self._world.awareness.intentions.goal is not None):
            self._world.interrupt(lambda: self.interact(
                action, food_id=food_id, conversation=conversation,
            ))
            return
        stamp, now = time.time(), time.monotonic()
        outcome = self._router.dispatch(
            CareCommand.from_action(action, food_id=food_id, conversation=conversation),
            inputs=self._inputs(stamp, now),
        )
        self._set_context(outcome.context)
        self._presenter.present(outcome, now=now, sleeping=self._state.sleeping)
        self._save()

    def _clear_wait(self) -> None:
        if self._player.event == "social_wait":
            self._player.cancel()

    def _defer_social(self, action: Callable[[], None]) -> None:
        # Admission is rechecked after World releases its pending-action marker.
        def schedule() -> None:
            self._root.after(0, action)

        self._world.interrupt(schedule)

    def _can_start_social(self) -> bool:
        return not self._is_closed() and self._contact.can_interact("talk")

    def _start_social(self, content: PreparedSocialContent) -> bool:
        if not self._can_start_social():
            return False
        self.interact("talk", conversation=content)
        return True
