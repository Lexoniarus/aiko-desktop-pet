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
        self._surface = skin.surface(parent)
        self.frame = self._surface.frame
        self._scroll = ScrollRegion(
            self._surface.body, skin, width=600, height=228,
            autohide=True, fit_content=True, max_height=228,
        )
        self._scroll.frame.pack(fill="both", expand=True)
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
                bg=skin.background,
                padx=4,
                pady=8,
            )
            section.pack(fill="x", pady=3)
            tk.Label(section, image=skin.images.icon(icon), bg=skin.background).pack(
                side="left", anchor="n", padx=(0, 8)
            )
            body = tk.Frame(section, bg=skin.background)
            body.pack(fill="both", expand=True)
            tk.Label(
                body,
                text=GERMAN_TEXT.format(f"vn.details.{group}"),
                bg=skin.background,
                fg=skin.text,
                font=(skin.font, 10, "bold"),
                anchor="w",
            ).pack(fill="x")
            for name in names:
                label = tk.Label(
                    body,
                    bg=skin.background,
                    fg=skin.text,
                    font=(skin.font, 9),
                    anchor="w",
                    justify="left",
                    wraplength=550,
                )
                label.pack(fill="x", pady=2)
                self._labels[name] = label
            if group != "objects":
                tk.Frame(
                    self._scroll.body, bg=skin.border, height=1,
                ).pack(fill="x", padx=4)
        self.frame.bind("<Configure>", self._resize, add="+")
        self._scroll.adopt()

    def _resize(self, event: tk.Event) -> None:
        for label in self._labels.values():
            label.configure(wraplength=max(80, event.width - 84))

    def refresh(self) -> None:
        view = self._snapshot()
        for name, label in self._labels.items():
            text = getattr(view, name)
            if label.cget("text") != text:
                label.configure(text=text)

    def text(self, name: str) -> str:
        return str(self._labels[name].cget("text"))
