"""Coordinate deliberate care and social playback through existing owners."""

from __future__ import annotations

import time
import tkinter as tk
from collections.abc import Callable
from dataclasses import replace

from ..application.active_time import SessionInputs
from ..application.commands import CareCommand
from ..application.contact import ContactCoordinator, acknowledge_interaction_text
from ..application.game_experience import experience_from_session
from ..application.horoscope_coordinator import HoroscopeCoordinator
from ..application.horoscope_models import HoroscopeDay, HoroscopeHistory
from ..application.router import ApplicationRouter
from ..application.social_content import PreparedSocialContent, SocialCategory
from ..application.social_coordinator import SocialContentCoordinator
from ..application.social_fetch import SocialContentWorker
from ..application.social_history import SocialContentHistory
from ..application.storage_contracts import StorageError
from ..games.contracts import GameRoundEvent, SessionSummary
from ..infrastructure.astronomy import AstronomyEngineCalculator
from ..infrastructure.horoscope_catalogue import load_horoscope_catalogue
from ..infrastructure.social_api import HttpSocialContentWorker
from ..pet.content import GERMAN_TEXT
from ..pet.food import FoodId
from ..pet.horoscope import HoroscopeEntry
from ..pet.interaction_events import SocialCompletion
from ..pet.mind import PetMind
from ..pet.mind.catalog import Reaction
from ..pet.needs import NeedCondition
from ..pet.routine import TimeContext, context_at
from ..pet.state import PetState
from ..ui.pet_view.animated_pet import AnimatedPet
from ..ui.pet_view.care_presenter import CarePresenter, CareViewPorts
from ..ui.pet_view.reaction_player import ReactionPlayer
from ..ui.pet_view.speech_presenter import SpeechPresenter
from ..ui.windows.hover_ui import HoverUi
from ..world.contracts import ObjectState
from .horoscope_playback import HoroscopePlayback
from .social_runtime import SocialConversationRuntime, SocialRuntimePorts
from .world_runtime import DesktopWorldRuntime


class DesktopCareRuntime:
    def __init__(
        self,
        *,
        root: tk.Tk,
        state: PetState,
        router: ApplicationRouter,
        world: DesktopWorldRuntime,
        contact: ContactCoordinator,
        animated: AnimatedPet,
        player: ReactionPlayer,
        speech: SpeechPresenter,
        hover: HoverUi,
        cancel_action: Callable[[float], None],
        start_action: Callable[[str, float], None],
        react: Callable[[Reaction, int], None],
        inputs: Callable[[float, float], SessionInputs],
        set_context: Callable[[TimeContext], None],
        save: Callable[[], None],
        is_closed: Callable[[], bool],
        game_open: Callable[[], bool],
        social_worker: SocialContentWorker | None = None,
        social_history: SocialContentHistory = SocialContentHistory(),
        persist_requests: Callable[[], StorageError | None] = lambda: None,
        zodiac_sign: Callable[[], str | None] = lambda: None,
        horoscope_history: HoroscopeHistory = HoroscopeHistory(),
        mind: PetMind,
    ) -> None:
        self._root, self._state, self._router = root, state, router
        self._world, self._contact = world, contact
        self._hover = hover
        self._player = player
        self._cancel_action = cancel_action
        self._presenter = CarePresenter(
            CareViewPorts(
                set_item=animated.set_food_overlay,
                cancel_action=cancel_action,
                start_action=start_action,
                cancel_followup=player.cancel,
                react=react,
                show_text=speech.show_text,
                refresh_toolbar=hover.refresh_toolbar,
                refresh_status=hover.refresh_status,
                text_presented=lambda event: acknowledge_interaction_text(state, event),
            )
        )
        self._inputs, self._set_context, self._save = inputs, set_context, save
        self._is_closed = is_closed
        content = SocialContentCoordinator(
            social_worker if social_worker is not None else HttpSocialContentWorker(),
            history=social_history,
            persist_requests=persist_requests,
        )

        def reactions(
            entry: HoroscopeEntry,
        ) -> tuple[Reaction, Reaction | None, Reaction]:
            now, context = time.monotonic(), context_at(time.time())
            snapshot = mind.dialogue_context(state, context, now)
            key = next((p.comment_key for p in entry.passages if p.comment_key), None)
            snapshot = replace(snapshot, horoscope_comment_key=key)
            opening = mind.select_reaction(
                "horoscope_opening", state, context, now, dialogue=snapshot
            )
            closing = mind.select_reaction(
                "horoscope_closing", state, context, now, dialogue=snapshot
            )
            if opening is None or closing is None:
                raise ValueError("Missing local book framing")
            comment = (
                mind.select_reaction(
                    "horoscope_comment", state, context, now, dialogue=snapshot
                )
                if NeedCondition.LOW_ENERGY not in snapshot.need_conditions
                else None
            )
            return opening, comment, closing

        def expire_at(book: str, deadline: float) -> Callable[[], None]:
            previous = world.world.snapshot()
            world.world.set_book_expiry(book, deadline)
            return lambda: world.world.restore_snapshot(previous)

        self.horoscope = HoroscopeCoordinator(
            load_horoscope_catalogue(),
            AstronomyEngineCalculator(),
            sign=zodiac_sign,
            reactions=reactions,
            credit=self._credit_horoscope,
            persist=lambda: persist_requests() is None,
            history=horoscope_history,
            expire_at=expire_at,
        )

        def pose(name: str) -> None:
            animated.food_overlay.readable_state = name
            animated.show_frame("pick_up", time.monotonic(), fixed=7)

        self._horoscope = HoroscopePlayback(
            self.horoscope,
            player,
            pose,
            schedule=root.after,
            cancel_timer=root.after_cancel,
            unavailable=lambda: speech.show_text(
                GERMAN_TEXT.format("social.horoscope.unavailable"), 6500),
        )
        world.interaction.can_read = lambda book, personal: (
            not state.sleeping
            and not game_open()
            and self.horoscope.availability(book)
            in (("ready", "resume", "replay") if personal else ("ready", "resume"))
        )
        world.awareness.readable = lambda book: world.interaction.can_read(book, False)
        world.interaction.read_book = self._horoscope.start
        world.interaction.cancel_reading = self._horoscope.stop

        def put_down(book: str) -> None:
            self.horoscope.put_down(book)

        world.interaction.book_put_down = put_down
        world.expired_book = self._horoscope.expire
        world.obsolete_books = self.horoscope.obsolete_books
        # Recovery legally places unfinished held objects on the taskbar.
        # A completed book without a previous put-down starts its hour here.

        self._recovery_timer: str | None = None

        def recover_put_down() -> None:
            self._recovery_timer = None
            if is_closed():
                return
            for day in self.horoscope.history.days:
                if (
                    day.completed
                    and day.first_put_down_at is None
                    and day.book_instance_id
                ):
                    item = next(
                        (
                            item
                            for item in world.world.snapshot().objects
                            if item.instance_id == day.book_instance_id
                        ),
                        None,
                    )
                    if item is not None and item.state == ObjectState.RESTING:
                        self.horoscope.put_down(item.instance_id)

        self._recovery_timer = root.after(0, recover_put_down)
        self.social = SocialConversationRuntime(
            content,
            SocialRuntimePorts(
                can_start=self._can_start_social,
                defer=self._defer_social,
                start=self._start_social,
                show_wait=lambda reaction: player.play(reaction, animate=False),
                clear_wait=self._clear_wait,
                persist_admission=save,
                can_wait=lambda: (
                    not is_closed() and not state.sleeping and not game_open()
                ),
            ),
        )

    def interact(
        self,
        action: str,
        *,
        food_id: FoodId | None = None,
        conversation: PreparedSocialContent | None = None,
        wake_from_clicks: bool = False,
        persist: bool = True,
    ) -> None:
        if conversation is None:
            self.social.cancel()
        if self._world.cursor.carrying:
            self._world.cursor.cancel()
        if (
            self._world.interaction.active
            or self._world.awareness.intentions.goal is not None
        ):
            self._world.interrupt(
                lambda: self.interact(
                    action,
                    food_id=food_id,
                    conversation=conversation,
                    wake_from_clicks=wake_from_clicks,
                    persist=persist,
                )
            )
            return
        stamp, now = time.time(), time.monotonic()
        if self._player.interruptible:
            self._player.cancel()
            self._cancel_action(now)
        outcome = self._router.dispatch(
            CareCommand.from_action(
                action,
                food_id=food_id,
                conversation=conversation,
                wake_from_clicks=wake_from_clicks,
            ),
            inputs=self._inputs(stamp, now),
        )
        self._set_context(outcome.context)
        self._presenter.present(outcome, now=now, sleeping=self._state.sleeping)
        if persist:
            self._save()

    def advance_time(self) -> None:
        self._router.advance_time(self._inputs(time.time(), time.monotonic()))

    def set_wish_pinned(self, instance_id: int, pinned: bool) -> None:
        self._router.set_wish_pinned(
            instance_id, pinned, inputs=self._inputs(time.time(), time.monotonic()),
        )
        self._save()
        self._hover.refresh_toolbar()

    def dismiss_wish(self, instance_id: int) -> None:
        self._router.dismiss_wish(
            instance_id, inputs=self._inputs(time.time(), time.monotonic()),
        )
        self._save()
        self._hover.refresh_toolbar()

    def observe_game_round(self, event: GameRoundEvent) -> None:
        self._router.observe_game_round(
            event, inputs=self._inputs(time.time(), time.monotonic()),
        )
        if event.outcome is not None:
            self._save()
            self._hover.refresh_status()

    def complete_game(self, summary: SessionSummary) -> None:
        self._router.complete_game(
            experience_from_session(summary),
            inputs=self._inputs(time.time(), time.monotonic()),
        )
        self._save()

    def complete_social(self, completion: SocialCompletion) -> None:
        self._router.complete_social(
            completion, inputs=self._inputs(time.time(), time.monotonic()),
            arrangement_ready=self._world.arrangement_ready(),
        )
        self._save()

    def wake_from_clicks(self) -> None:
        """Present and persist deliberate waking through the normal care owner."""
        self.interact("sleep", wake_from_clicks=True)

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
        # The runtime saves care and the admitted receipt together after accept().
        self.interact("talk", conversation=content, persist=False)
        return True

    def _credit_horoscope(self, day: HoroscopeDay) -> Callable[[], None]:
        inputs = self._inputs(time.time(), time.monotonic())
        self._router.advance_time(inputs)
        checkpoint = self._state.capture_checkpoint()
        outcome = self._router.dispatch(
            CareCommand.from_action("talk", book_reading=day.reading),
            inputs=inputs,
        )
        self._set_context(outcome.context)
        self._hover.refresh_toolbar()
        self._hover.refresh_status()
        return lambda: self._state.restore_checkpoint(checkpoint)

    def close(self) -> None:
        if self._recovery_timer is not None:
            self._root.after_cancel(self._recovery_timer)
            self._recovery_timer = None
        self._horoscope.stop()
        self.social.close()

    def select_social(self, category: SocialCategory) -> None:
        if category == SocialCategory.HOROSCOPE:
            if self.horoscope_choice()[1]:
                self._world.begin_carry("horoscope_book")
        else:
            self.social.select(category)

    def horoscope_choice(self) -> tuple[str, bool]:
        status = self.horoscope.availability()
        if (status == "ready"
                and not self._world.world.can_place_definition("horoscope_book")):
            status = "bound"
        key = {"ready": "place", "sign": "choose_sign", "bound": "bound"}.get(
            status,
            "completed",
        )
        return GERMAN_TEXT.format(f"social.horoscope.{key}"), status == "ready"
