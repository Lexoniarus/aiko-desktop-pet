"""Shared social admission and physical horoscope-book lifecycle in the room."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import replace
from typing import TYPE_CHECKING

from ..pet.horoscope import HoroscopeCatalogue, HoroscopeEntry
from ..pet.mind.catalog import Reaction
from ..pet.needs import NeedCondition
from ..pet.routine import context_at
from ..presentation.book import HoroscopePlayback
from ..presentation.social import SocialConversationRuntime, SocialRuntimePorts
from ..world.contracts import ObjectState
from .commands import CareCommand
from .horoscope_coordinator import HoroscopeCoordinator
from .horoscope_models import HoroscopeDay, SkyCalculator
from .social_content import PreparedSocialContent, SocialCategory
from .social_coordinator import SocialContentCoordinator
from .social_fetch import SocialContentWorker

if TYPE_CHECKING:
    from .room_session import RoomSession


class RoomContent:
    def __init__(
        self, session: RoomSession, worker: SocialContentWorker,
        local: tuple[PreparedSocialContent, ...], catalogue: HoroscopeCatalogue,
        calculator: SkyCalculator,
    ) -> None:
        self.session = session
        self.social = SocialContentCoordinator(
            worker, history=session.social_history, local_content=local,
            persist_requests=self._persist_social,
        )
        self.runtime = SocialConversationRuntime(self.social, SocialRuntimePorts(
            can_start=lambda: not session.state.sleeping and session.games.sequence is None,
            defer=session.room.interaction.interrupt, start=self._start_social,
            show_wait=session.playback.speak, clear_wait=session.playback.player.cancel,
            persist_admission=lambda: self.persist(),
            show_status=lambda text: session.playback.comment(text, 6000),
        ))
        self.horoscope = HoroscopeCoordinator(
            catalogue, calculator, sign=lambda: session.settings.zodiac_sign,
            reactions=self._reactions, credit=self._credit,
            persist=self.persist, history=session.horoscope_history,
            expire_at=self._expire,
        )
        self.book = HoroscopePlayback(
            self.horoscope, session.playback.player,
            pose=lambda pose: setattr(session.room, "held_pose", pose),
            schedule=session.playback.schedule, cancel_timer=session.playback.cancel_timer,
            unavailable=lambda: session.playback.comment("Das Horoskop ist gerade nicht verfügbar.", 6000),
        )
        interaction = session.room.interaction
        interaction.can_read = lambda book, personal: (
            not session.state.sleeping and session.games.sequence is None
            and self.horoscope.availability(book) in (
                ("ready", "resume", "replay") if personal else ("ready", "resume")
            )
        )
        session.room.awareness.readable = lambda book: interaction.can_read(book, False)
        interaction.read_book = self.book.start
        interaction.cancel_reading = self.book.stop
        interaction.book_put_down = lambda book: self.horoscope.put_down(book)

    def _persist_social(self) -> None:
        self.persist()

    def persist(self) -> bool:
        self.session.social_history = self.social.history
        self.session.horoscope_history = self.horoscope.history
        self.session.save()
        return True

    def _start_social(self, content: PreparedSocialContent) -> bool:
        outcome = self.session.router.dispatch(
            CareCommand.from_action("talk", conversation=content), inputs=self.session.inputs(),
        )
        self.session.playback.speak(outcome.reaction)
        return outcome.reaction is not None

    def _reactions(self, entry: HoroscopeEntry) -> tuple[Reaction, Reaction | None, Reaction]:
        session = self.session
        context, now = context_at(time.time()), time.monotonic()
        dialogue = session.mind.dialogue_context(session.state, context, now)
        dialogue = replace(dialogue, horoscope_comment_key=next(
            (passage.comment_key for passage in entry.passages if passage.comment_key), None,
        ))
        opening = session.mind.select_reaction("horoscope_opening", session.state, context, now,
                                                dialogue=dialogue)
        closing = session.mind.select_reaction("horoscope_closing", session.state, context, now,
                                                dialogue=dialogue)
        if opening is None or closing is None:
            raise ValueError("Missing horoscope framing")
        comment = session.mind.select_reaction(
            "horoscope_comment", session.state, context, now, dialogue=dialogue,
        ) if NeedCondition.LOW_ENERGY not in dialogue.need_conditions else None
        return opening, comment, closing

    def _credit(self, day: HoroscopeDay) -> Callable[[], None]:
        checkpoint = self.session.state.capture_checkpoint()
        self.session.router.dispatch(CareCommand.from_action("talk", book_reading=day.reading),
                                      inputs=self.session.inputs())
        return lambda: self.session.state.restore_checkpoint(checkpoint)

    def _expire(self, book: str, deadline: float) -> Callable[[], None]:
        world = self.session.room.world
        previous = world.snapshot()
        world.set_book_expiry(book, deadline)
        return lambda: world.restore_snapshot(previous)

    def update(self) -> None:
        self.runtime.poll()
        world = self.session.room.world
        for book in self.horoscope.obsolete_books():
            item = world.get(book)
            if item.expires_at is None and item.state not in (ObjectState.CONSUMED, ObjectState.REMOVED):
                world.set_book_expiry(book, time.time())
        for book in world.expire_books(time.time()):
            self.book.expire(book)
        self.session.room.awareness.reconcile_books(world.snapshot())

    def select(self, category: str) -> None:
        if category == "horoscope":
            if self.horoscope.availability() not in ("ready", "resume", "replay"):
                raise ValueError("Bitte wähle dein Sternzeichen oder benutze das vorhandene Buch.")
            self.session.room.offer("horoscope_book")
        else:
            self.runtime.select(SocialCategory(category))

    def suspend(self) -> None:
        self.runtime.cancel()
        self.book.stop()
