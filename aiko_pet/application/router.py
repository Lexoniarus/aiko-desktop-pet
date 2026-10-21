"""Single typed entry point for internal actions and future integrations."""

from __future__ import annotations

from threading import get_ident
from typing import overload

from ..games.contracts import GameRoundEvent
from ..pet.fun import GameExperience
from ..pet.interaction_events import SocialCompletion
from .active_time import SessionInputs
from .commands import (
    ApplicationCommand,
    CareCommand,
    NotificationCommand,
)
from .controller import CareController, CareOutcome
from .events import IncomingNotification
from .game_experience import GameExperienceCoordinator, GameExperienceOutcome
from .inbox import NotificationInbox, NotificationReceipt


class ApplicationRouter:
    """Route data without granting integrations access to GUI or pet internals.

    Notifications may arrive on worker threads. Care and inbox consumption run
    only on the owner thread, currently Tkinter's main event-loop thread.
    """

    def __init__(
        self, care: CareController, inbox: NotificationInbox | None = None,
        *, game_experience: GameExperienceCoordinator | None = None,
    ) -> None:
        self._care = care
        self._game_experience = game_experience
        self._inbox = inbox if inbox is not None else NotificationInbox()
        self._owner_thread = get_ident()

    def _require_owner_thread(self) -> None:
        if get_ident() != self._owner_thread:
            raise RuntimeError("Application state requires the owner thread")

    @overload
    def dispatch(
        self, command: CareCommand, *, inputs: SessionInputs,
    ) -> CareOutcome: ...

    @overload
    def dispatch(
        self, command: NotificationCommand, *,
        inputs: None = None,
    ) -> NotificationReceipt: ...

    def dispatch(
        self, command: ApplicationCommand, *,
        inputs: SessionInputs | None = None,
    ) -> CareOutcome | NotificationReceipt:
        """Only data notifications can cross the UI thread boundary."""
        if isinstance(command, NotificationCommand):
            if inputs is not None:
                raise ValueError("Notifications cannot supply care inputs")
            return self._inbox.submit(command.notification)
        if isinstance(command, CareCommand):
            self._require_owner_thread()
            if inputs is None:
                raise ValueError("Care actions require trusted care inputs")
            return self._care.execute(command, inputs)
        raise TypeError("Unknown application command")

    def advance_time(self, inputs: SessionInputs) -> None:
        """Advance admitted contact through the same session clock as care."""
        self._require_owner_thread()
        self._care.advance_time(inputs)

    def set_wish_pinned(
        self, instance_id: int, pinned: bool, *, inputs: SessionInputs,
    ) -> None:
        """UI preference, not personal contact or a care reward."""
        self._require_owner_thread()
        self._care.set_wish_pinned(instance_id, pinned, inputs)

    def dismiss_wish(self, instance_id: int, *, inputs: SessionInputs) -> None:
        self._require_owner_thread()
        self._care.dismiss_wish(instance_id, inputs)

    def complete_social(
        self, completion: SocialCompletion, *, inputs: SessionInputs,
        arrangement_ready: bool,
    ) -> None:
        """Receive a finished accepted sequence on the existing owner thread."""
        self._require_owner_thread()
        self._care.complete_social(
            completion, inputs, arrangement_ready=arrangement_ready,
        )

    def observe_game_round(
        self, event: GameRoundEvent, *, inputs: SessionInputs,
    ) -> None:
        self._require_owner_thread()
        if self._game_experience is None:
            raise RuntimeError("No game experience coordinator is installed")
        self._game_experience.observe_round(event, inputs)

    def complete_game(
        self, experience: GameExperience, *, inputs: SessionInputs,
    ) -> GameExperienceOutcome:
        """Owner-thread game-neutral completion boundary."""
        self._require_owner_thread()
        if self._game_experience is None:
            raise RuntimeError("No game experience coordinator is installed")
        return self._game_experience.complete(experience, inputs)

    def next_notification(self) -> IncomingNotification | None:
        """Consume accepted data on the owner thread for safe presentation."""
        self._require_owner_thread()
        return self._inbox.pop_next()

    def close(self) -> None:
        self._require_owner_thread()
        self._inbox.close()
