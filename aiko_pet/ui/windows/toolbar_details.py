"""Optional status details inside the single care toolbar, not another window."""

from __future__ import annotations

import tkinter as tk
from typing import Callable

from ..view_models.contracts import StatusSnapshot
from ..common.skin import AikoSkin


class ToolbarDetails:
    """Render the former status-only information without duplicating actions."""

    def __init__(
        self, parent: tk.Widget, skin: AikoSkin,
        snapshot: Callable[[], StatusSnapshot],
    ) -> None:
        self._snapshot = snapshot
        self.frame = tk.Frame(parent, bg=skin.panel)
        self._labels: dict[str, tk.Label] = {}
        for name in ("emotion", "hint", "fun_line", "next_event", "activity_line"):
            label = tk.Label(
                self.frame, text="", bg=skin.panel, fg=skin.text,
                font=(skin.font, 9), anchor="w", justify="left",
                wraplength=420,
            )
            label.pack(fill="x", padx=10, pady=3)
            self._labels[name] = label
        self.frame.bind("<Configure>", self._resize)

    def _resize(self, event: tk.Event) -> None:
        for label in self._labels.values():
            label.configure(wraplength=max(80, event.width - 24))

    def refresh(self) -> None:
        view = self._snapshot()
        for name, label in self._labels.items():
            text = getattr(view, name)
            if label.cget("text") != text:
                label.configure(text=text)

    def text(self, name: str) -> str:
        return str(self._labels[name].cget("text"))
