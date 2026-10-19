"""Conversation choices and retrieval status in one transient utility window."""

from __future__ import annotations

import sys
import tkinter as tk
import webbrowser
from collections.abc import Callable
from functools import partial

from ...application.social_content import PreparedSocialContent, SocialCategory
from ...pet.content import GERMAN_TEXT
from ..common.skin import AikoSkin
from ..common.window_drag import bounded_position


class SocialMenu:
    def __init__(
        self, root: tk.Tk, x: int, y: int, *,
        selected: Callable[[SocialCategory | None], None],
        closed: Callable[[], None], enabled: Callable[[], bool],
        can_interact: Callable[[], bool],
        snapshot: Callable[[], tuple[str, PreparedSocialContent | None]],
        always_on_top: bool, skin: AikoSkin,
    ) -> None:
        self._selected = selected
        self._on_closed = closed
        self._enabled = enabled
        self._can_interact = can_interact
        self._snapshot = snapshot
        self._closed = False
        self._source: PreparedSocialContent | None = None
        self.window = tk.Toplevel(root)
        self.window.withdraw()
        self.window.overrideredirect(True)
        self.window.configure(bg=skin.border)
        self.window.wm_attributes("-topmost", always_on_top)
        if sys.platform == "win32":
            self.window.wm_attributes("-toolwindow", True)
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        self.window.bind("<Escape>", lambda _event: self.close())
        body = skin.frame(self.window)
        body.pack(fill="both", expand=True, padx=3, pady=3)
        header = skin.header(body, GERMAN_TEXT.format("ui.talk"))
        header.configure(width=310, cursor="arrow")
        header.pack(fill="x")
        self.buttons: dict[SocialCategory | None, tk.Button] = {}
        for category in (None, *SocialCategory):
            key = ("social.plain" if category is None
                   else f"social.name.{category.value}")
            button = skin.button(
                body, GERMAN_TEXT.format(key), partial(self.choose, category),
                size="wide",
            )
            button.pack(fill="x", padx=10, pady=4)
            self.buttons[category] = button
        self.status = tk.Label(
            body, text="", wraplength=290, justify="left", anchor="w", height=4,
            bg=skin.background, fg=skin.text, font=(skin.font, 10),
        )
        self.status.pack(fill="x", padx=10, pady=6)
        self.source_button = skin.button(body, "", self._open_source, size="wide")
        self.entry_button = skin.button(
            body, GERMAN_TEXT.format("social.api_entry"),
            self._open_entry, size="wide",
        )
        self.source_button.configure(width=290, height=44, wraplength=280)
        self.source_button.pack(fill="x", padx=10, pady=2)
        self.entry_button.pack(fill="x", padx=10, pady=2)
        skin.button(body, GERMAN_TEXT.format("ui.close"), self.close).pack(
            fill="x", padx=10, pady=(4, 8),
        )
        self.refresh()
        self.window.update_idletasks()
        x, y = bounded_position(
            x, y, self.window.winfo_reqwidth(), self.window.winfo_reqheight(),
            root.winfo_screenwidth(), root.winfo_screenheight() - 45,
        )
        self.window.geometry(f"+{x}+{y}")
        self.window.deiconify()
        self.window.focus_set()

    def choose(self, category: SocialCategory | None) -> None:
        if (self._closed or not self._can_interact()
                or category is not None and not self._enabled()):
            return
        self._selected(category)
        self.refresh()

    def refresh(self) -> None:
        if self._closed:
            return
        allowed, enabled = self._can_interact(), self._enabled()
        for category, button in self.buttons.items():
            button.configure(state=(
                "normal" if allowed and (category is None or enabled) else "disabled"
            ))
        status, source = self._snapshot()
        self.status.configure(text=status)
        self._source = source
        if source is not None:
            self.source_button.configure(text=GERMAN_TEXT.format(
                "social.source", source=source.source,
            ), state="normal")
            self.entry_button.configure(state="normal")
        else:
            self.source_button.configure(
                text=GERMAN_TEXT.format("social.source", source="—"), state="disabled",
            )
            self.entry_button.configure(state="disabled")

    def _open_source(self) -> None:
        if self._source is not None:
            webbrowser.open(self._source.source_url)

    def _open_entry(self) -> None:
        if self._source is not None:
            webbrowser.open(self._source.permalink)

    def contains_pointer(self, x: int, y: int) -> bool:
        return not self._closed and (
            self.window.winfo_rootx() <= x
            < self.window.winfo_rootx() + self.window.winfo_width()
            and self.window.winfo_rooty() <= y
            < self.window.winfo_rooty() + self.window.winfo_height()
        )

    def focus(self) -> None:
        self.window.lift()
        self.window.focus_set()

    def close(self) -> None:
        if not self._closed:
            self._closed = True
            self.window.destroy()
            self._on_closed()
