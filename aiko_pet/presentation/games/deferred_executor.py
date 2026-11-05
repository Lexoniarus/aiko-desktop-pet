"""Bounded pure searches on the Python Worker, with cancellable queued work."""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import Executor, Future
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
T = TypeVar("T")


class DeferredSearchExecutor(Executor):
    """No thread or second mutable pet; existing search limits bound each task."""

    def __init__(self, schedule: Callable[[int, Callable[[], None]], str]) -> None:
        self._schedule = schedule
        self._closed = False
        self._pending: list[Future[object]] = []

    def submit(
        self, fn: Callable[P, T], /, *args: P.args, **kwargs: P.kwargs
    ) -> Future[T]:
        if self._closed:
            raise RuntimeError("Search executor is closed")
        future: Future[T] = Future()

        def run() -> None:
            if self._closed or not future.set_running_or_notify_cancel():
                return
            try:
                future.set_result(fn(*args, **kwargs))
            except Exception as error:
                future.set_exception(error)

        self._schedule(1, run)
        return future

    def shutdown(self, wait: bool = True, *, cancel_futures: bool = False) -> None:
        self._closed = True
