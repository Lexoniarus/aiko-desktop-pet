"""Optional status details inside the single care toolbar, not another window."""

from __future__ import annotations

import tkinter as tk
from typing import Callable

from ...pet.content import GERMAN_TEXT
from ..common.scroll_region import ScrollRegion
from ..common.skin import AikoSkin
from ..view_models.contracts import StatusSnapshot


class ToolbarDetails:
    """Render the former status-only information without duplicating actions."""

    def __init__(
        self,
        parent: tk.Widget,
        skin: AikoSkin,
        snapshot: Callable[[], StatusSnapshot],
    ) -> None:
        self._snapshot = snapshot
        self._scroll = ScrollRegion(parent, skin, width=620, height=228)
        self.frame = self._scroll.frame
        self._labels: dict[str, tk.Label] = {}
        for group, icon, names in (
            (
                "wellbeing",
                "detail_wellbeing",
                (
                    "emotional_state_label",
                    "hint",
                    "wellbeing_line",
                    "relationship_line",
                    "sleep_context_line",
                    "contact_line",
                ),
            ),
            ("rhythm", "detail_rhythm", ("activity_line",)),
            ("next", "detail_next", ("next_event",)),
            ("objects", "detail_objects", ("objects_line",)),
        ):
            section = tk.Frame(
                self._scroll.body,
                bg=skin.panel,
                padx=8,
                pady=8,
                highlightthickness=1,
                highlightbackground=skin.border,
            )
            section.pack(fill="x", pady=3)
            tk.Label(section, image=skin.images.icon(icon), bg=skin.panel).pack(
                side="left", anchor="n", padx=(0, 8)
            )
            body = tk.Frame(section, bg=skin.panel)
            body.pack(fill="both", expand=True)
            tk.Label(
                body,
                text=GERMAN_TEXT.format(f"vn.details.{group}"),
                bg=skin.panel,
                fg=skin.text,
                font=(skin.font, 10, "bold"),
                anchor="w",
            ).pack(fill="x")
            for name in names:
                label = tk.Label(
                    body,
                    bg=skin.panel,
                    fg=skin.text,
                    font=(skin.font, 9),
                    anchor="w",
                    justify="left",
                    wraplength=550,
                )
                label.pack(fill="x", pady=2)
                self._labels[name] = label
        self.frame.bind("<Configure>", self._resize)
        self._scroll.adopt()

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
