"""Desktop mouse and keyboard event binding, independent of game decisions."""

from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from typing import Callable, Protocol

from ..desktop_input import GlobalMouseClicks


class MouseClicks(Protocol):
    def clicked(self) -> bool: ...


@dataclass(frozen=True, slots=True)
class DesktopInputActions:
    """Only application callbacks granted to the desktop input adapter."""

    enter: Callable[[tk.Event | None], None]
    left_click: Callable[[tk.Event | None], None]
    right_click: Callable[[tk.Event | None], None]
    show_menu: Callable[[int, int], None]
    dismiss_outside: Callable[[int, int], None]
    open_status: Callable[[], None]
    quit: Callable[[], None]
    closed: Callable[[], bool]


class DesktopInput:
    """Own the Tk bindings and off-window click/focus fallback logic."""

    def __init__(
        self, root: tk.Tk, canvas: tk.Canvas,
        actions: DesktopInputActions,
        mouse: MouseClicks | None = None,
    ) -> None:
        self.root = root
        self.canvas = canvas
        self.actions = actions
        self.mouse = mouse if mouse is not None else GlobalMouseClicks()
        self._focus_timers: set[str] = set()
        self._stopped = False

    def initialize(self) -> None:
        """Baseline global button state before installing interactive handlers."""
        self.mouse.clicked()
        self.canvas.bind("<Enter>", self.actions.enter)
        self.canvas.bind("<Button-1>", self.actions.left_click)
        self.canvas.bind("<Button-3>", self.actions.right_click)
        self.canvas.bind("<Shift-Button-3>", self.on_menu)
        self.root.bind("<Control-q>", lambda _event: self.actions.quit())
        self.root.bind("<F2>", lambda _event: self.actions.open_status())
        self.root.bind_all("<ButtonPress>", self.on_tk_press, add="+")
        self.root.bind_all("<FocusOut>", self.on_focus_out, add="+")
        self.root.protocol("WM_DELETE_WINDOW", self.actions.quit)

    def on_menu(self, event: tk.Event) -> None:
        self.actions.show_menu(event.x_root, event.y_root)

    def on_tk_press(self, event: tk.Event) -> None:
        """Handle clicks inside Tk windows without losing focus to them."""
        self.actions.dismiss_outside(event.x_root, event.y_root)

    def on_focus_out(self, _event: tk.Event) -> None:
        """Keep delayed focus checks cancellable during window teardown."""
        if self._stopped or self.actions.closed():
            return
        scheduled: str | None = None

        def dismiss() -> None:
            if scheduled is not None:
                self._focus_timers.discard(scheduled)
            self.dismiss_after_focus_loss()

        scheduled = self.root.after(100, dismiss)
        self._focus_timers.add(scheduled)

    def dismiss_after_focus_loss(self) -> None:
        """Fall back to mouse location if a foreign window gained focus."""
        if self._stopped or self.actions.closed():
            return
        self.actions.dismiss_outside(
            self.root.winfo_pointerx(), self.root.winfo_pointery(),
        )

    def stop(self) -> None:
        """Cancel outstanding Tk focus callbacks before destroying the root."""
        if self._stopped:
            return
        self._stopped = True
        for scheduled in tuple(self._focus_timers):
            self.root.after_cancel(scheduled)
        self._focus_timers.clear()

    def poll_global_click(self) -> None:
        """Catch clicks on foreign windows missed by Tk's ButtonPress."""
        if not self._stopped and self.mouse.clicked():
            self.actions.dismiss_outside(
                self.root.winfo_pointerx(), self.root.winfo_pointery(),
            )
