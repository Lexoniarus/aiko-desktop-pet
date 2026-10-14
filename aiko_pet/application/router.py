"""Single typed entry point for internal actions and future integrations."""

from __future__ import annotations

from threading import get_ident
from typing import overload

from .commands import (
    ApplicationCommand,
    CareCommand,
    NotificationCommand,
)
from .controller import CareController, CareOutcome, CareRuntime
from .events import IncomingNotification
from .inbox import NotificationInbox, NotificationReceipt
from ..pet.fun import GameExperience
from .game_experience import GameExperienceCoordinator, GameExperienceOutcome


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
        self, command: CareCommand, *, runtime: CareRuntime,
    ) -> CareOutcome: ...

    @overload
    def dispatch(
        self, command: NotificationCommand, *,
        runtime: None = None,
    ) -> NotificationReceipt: ...

    def dispatch(
        self, command: ApplicationCommand, *,
        runtime: CareRuntime | None = None,
    ) -> CareOutcome | NotificationReceipt:
        """Only data notifications can cross the UI thread boundary."""
        if isinstance(command, NotificationCommand):
            if runtime is not None:
                raise ValueError("Notifications cannot supply runtime context")
            return self._inbox.submit(command.notification)
        if isinstance(command, CareCommand):
            self._require_owner_thread()
            if runtime is None:
                raise ValueError("Care actions require trusted runtime context")
            return self._care.execute(command, runtime)
        raise TypeError("Unknown application command")

    def complete_game(
        self, experience: GameExperience, *, runtime: CareRuntime,
    ) -> GameExperienceOutcome:
        """Owner-thread game-neutral completion boundary."""
        self._require_owner_thread()
        if self._game_experience is None:
            raise RuntimeError("No game experience coordinator is installed")
        return self._game_experience.complete(experience, runtime)

    def next_notification(self) -> IncomingNotification | None:
        """Consume accepted data on the owner thread for safe presentation."""
        self._require_owner_thread()
        return self._inbox.pop_next()

    def close(self) -> None:
        self._require_owner_thread()
        self._inbox.close()
