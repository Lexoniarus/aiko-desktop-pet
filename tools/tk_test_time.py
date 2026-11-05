"""Controlled clocks and chronological callbacks for real-widget Tk tests.

Only the isolated test interpreter is patched. Native widget events still run
through Tk; gameplay timers, frames and reading delays use virtual time.
"""

from __future__ import annotations

import heapq
import math
import time
import tkinter as tk
from collections.abc import Callable
from contextlib import ExitStack
from functools import partial
from types import TracebackType
from typing import Literal
from unittest.mock import patch

from aiko_pet import gui
from aiko_pet.application.session import PetSessionRestorer
from aiko_pet.desktop.persistence import DesktopPersistence
from aiko_pet.desktop.runtime import DesktopRuntime


class ControlledTkTime:
    """Run due callbacks in order, keeping all application clocks consistent."""

    def __init__(self) -> None:
        self._wall_start = time.time()
        self._elapsed_ms = 0
        self._serial = 0
        self._queue: list[tuple[int, int, int, str]] = []
        self._callbacks: dict[str, tuple[tk.Misc, Callable[[], object]]] = {}
        self._roots: set[tk.Tk] = set()
        self._advancing = False
        self._patches = ExitStack()

    def monotonic(self) -> float:
        return 1000 + self._elapsed_ms / 1000

    def wall_time(self) -> float:
        return self._wall_start + self._elapsed_ms / 1000

    def __enter__(self) -> ControlledTkTime:
        real_cancel = tk.Misc.after_cancel
        real_update = tk.Misc.update

        def after(
            widget: tk.Misc, ms: int | Literal["idle"],
            func: Callable[..., object] | None = None, *args: object,
        ) -> str:
            if func is None:
                raise AssertionError("Use advance(), not a blocking Tk delay")
            self._serial += 1
            token = f"controlled-after-{self._serial}"
            idle = ms == "idle"
            delay = 0 if idle else int(ms)
            heapq.heappush(self._queue, (
                self._elapsed_ms + max(0, delay), int(idle), self._serial, token,
            ))
            self._callbacks[token] = widget, partial(func, *args)
            if isinstance(widget, tk.Tk):
                self._roots.add(widget)
            return token

        def cancel(widget: tk.Misc, token: str) -> None:
            if token.startswith("controlled-after-"):
                self._callbacks.pop(token, None)
            else:
                real_cancel(widget, token)

        def update(widget: tk.Misc) -> None:
            real_update(widget)
            if not self._advancing:
                self.advance(0)

        self._patches.enter_context(patch.object(tk.Misc, "after", after))
        self._patches.enter_context(patch.object(tk.Misc, "after_cancel", cancel))
        self._patches.enter_context(patch.object(tk.Misc, "update", update))
        self._patches.enter_context(patch("time.monotonic", self.monotonic))
        self._patches.enter_context(patch("time.time", self.wall_time))
        # Constructor defaults captured the real functions at import time.
        self._patches.enter_context(patch.object(gui, "DesktopRuntime", partial(
            DesktopRuntime, monotonic=self.monotonic, wall_time=self.wall_time,
        )))
        self._patches.enter_context(patch.object(gui, "DesktopPersistence", partial(
            DesktopPersistence, monotonic=self.monotonic,
        )))
        self._patches.enter_context(patch.object(gui, "PetSessionRestorer", partial(
            PetSessionRestorer, wall_time=self.wall_time,
        )))
        for name in (
            "aiko_pet.gui.elapsed_uptime_seconds",
            "aiko_pet.desktop.world_runtime.active_uptime_seconds",
            "aiko_pet.desktop.session_runtime.elapsed_uptime_seconds",
            "aiko_pet.desktop.session_runtime.active_uptime_seconds",
        ):
            self._patches.enter_context(patch(name, self.monotonic))
        return self

    @staticmethod
    def _exists(widget: tk.Misc) -> bool:
        try:
            return bool(widget.winfo_exists())
        except tk.TclError:
            return False

    def pump(self) -> None:
        """Apply native mapping, geometry and widget events without sleeping."""
        for root in tuple(self._roots):
            if self._exists(root):
                root.update()
            else:
                self._roots.discard(root)

    def advance(self, seconds: float) -> None:
        if not math.isfinite(seconds) or seconds < 0:
            raise ValueError("Advance requires finite nonnegative seconds")
        target = self._elapsed_ms + round(seconds * 1000)
        calls = 0
        self._advancing = True
        try:
            self.pump()
            while self._queue and self._queue[0][0] <= target:
                due, _idle, _serial, token = heapq.heappop(self._queue)
                pending = self._callbacks.pop(token, None)
                if pending is None or not self._exists(pending[0]):
                    continue
                self._elapsed_ms = due
                pending[1]()
                self.pump()
                calls += 1
                if calls > 100_000:
                    raise AssertionError("Callbacks failed to yield virtual time")
            self._elapsed_ms = target
            self.pump()
        finally:
            self._advancing = False

    def __exit__(
        self, exc_type: type[BaseException] | None, exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self._callbacks.clear()
        self._queue.clear()
        self._roots.clear()
        self._patches.close()
