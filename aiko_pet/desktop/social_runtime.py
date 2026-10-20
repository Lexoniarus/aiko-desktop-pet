"""Join prepared content to existing foreground admission and care playback."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Literal

from ..application.social_content import PreparedSocialContent, SocialCategory
from ..application.social_coordinator import SocialContentCoordinator, SocialSelection
from ..pet.content import GERMAN_TEXT
from ..pet.mind.catalog import Reaction


@dataclass(frozen=True, slots=True)
class SocialRuntimePorts:
    can_start: Callable[[], bool]
    defer: Callable[[Callable[[], None]], None]
    start: Callable[[PreparedSocialContent], bool]
    show_wait: Callable[[Reaction], None]
    clear_wait: Callable[[], None]
    can_wait: Callable[[], bool] = lambda: True


class SocialConversationRuntime:
    def __init__(
        self, content: SocialContentCoordinator, ports: SocialRuntimePorts,
    ) -> None:
        self.content = content
        self._ports = ports
        self._token: object | None = None
        self._phase: Literal["idle", "fetching", "admitting"] = "idle"
        self._closed = False
        self._status = "social.hint"
        self._last_content: PreparedSocialContent | None = None

    @property
    def waiting(self) -> bool:
        return self._phase != "idle"

    @property
    def prepared_categories(self) -> frozenset[str]:
        """Read existing warm stock without fetching, selecting or reserving it."""
        return frozenset(c.value for c in SocialCategory
                         if self.content.enabled and self.content.count(c))

    def snapshot(self) -> tuple[str, PreparedSocialContent | None]:
        key = self._status if self.content.enabled else "social.disabled"
        return GERMAN_TEXT.format(key), self._last_content

    def set_enabled(self, enabled: bool) -> None:
        self.cancel()
        self._last_content = None
        self.content.set_enabled(enabled)

    def cancel(self) -> None:
        self._token = None
        self._phase = "idle"
        self.content.cancel_selection()
        self._ports.clear_wait()
        self._status = "social.hint"

    def select(self, category: SocialCategory) -> None:
        if self._closed or not self._ports.can_start():
            return
        self.cancel()
        self._last_content = None
        token = object()
        self._token = token
        selection = self.content.select(category)
        if selection.status == "waiting":
            self._phase = "fetching"
            self._status = "social.waiting"

            def wait() -> None:
                if (self._token is token and self._phase == "fetching"
                        and not self._closed):
                    if not self._ports.can_start():
                        self.cancel()
                        return
                    self._ports.show_wait(Reaction.spoken(
                        "social-wait", GERMAN_TEXT.format("social.waiting"),
                        "idle", "social_wait",
                    ))

            self._ports.defer(wait)
        else:
            self._present(selection)

    def _present(self, selection: SocialSelection) -> None:
        if selection.status != "ready" or selection.content is None:
            self._phase = "idle"
            self._token = None
            self._ports.clear_wait()
            self._status = ("social.disabled" if selection.status == "disabled"
                            else "social.error")
            return
        item, token = selection.content, self._token
        self._phase = "admitting"

        def begin() -> None:
            if self._closed or self._token is not token or not self.content.enabled:
                return
            self._ports.clear_wait()
            if not self._ports.can_start():
                self.cancel()
                return
            self._phase = "idle"
            self._token = None
            if self._ports.start(item):
                self.content.accept(item)
                self._last_content = item
                self._status = "social.started"
            else:
                self.content.cancel_selection()
                self._status = "social.error"

        self._ports.defer(begin)

    def poll(self) -> None:
        if self._closed:
            return
        if self.waiting and not self._ports.can_wait():
            self.cancel()
        selection = self.content.poll()
        if selection is not None and self._token is not None:
            self._present(selection)

    def close(self) -> None:
        if self._closed:
            return
        self.cancel()
        self._closed = True
        self.content.close()
