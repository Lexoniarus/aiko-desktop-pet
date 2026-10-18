"""Deterministic callback scheduling shared by reaction integration tests."""

from collections.abc import Callable


class FakeScheduler:
    def __init__(self) -> None:
        self.callbacks: dict[str, tuple[int, Callable[[], None]]] = {}
        self.cancelled: set[str] = set()
        self.next_id = 0

    def schedule(self, delay_ms: int, callback: Callable[[], None]) -> str:
        self.next_id += 1
        token = str(self.next_id)
        self.callbacks[token] = (delay_ms, callback)
        return token

    def cancel(self, token: str) -> None:
        self.cancelled.add(token)
        self.callbacks.pop(token, None)

    def fire(self, token: str) -> None:
        _, callback = self.callbacks.pop(token)
        callback()
