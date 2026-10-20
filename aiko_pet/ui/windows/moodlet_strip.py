"""Passive horizontal impressions, retaining focus/scroll while time changes."""

import tkinter as tk
from functools import partial

from ...pet.content import GERMAN_TEXT
from ..common.description_tip import DescriptionTip
from ..common.scroll_region import ScrollRegion
from ..common.skin import AikoSkin
from ..view_models.contracts import MoodletView
from ..view_models.emotional_text import MOODLET_ICONS, moodlet_description


class MoodletStrip:
    def __init__(self, parent: tk.Misc, skin: AikoSkin, tips: DescriptionTip) -> None:
        self.frame = tk.Frame(parent, bg=skin.background)
        tk.Label(
            self.frame,
            text=GERMAN_TEXT.format("vn.moodlets"),
            fg=skin.muted,
            bg=skin.background,
            font=(skin.font, 9, "bold"),
        ).pack(anchor="w")
        self._scroll = ScrollRegion(
            self.frame,
            skin,
            width=620,
            height=max(82, 44 + skin.small_line_height * 3),
            horizontal=True,
        )
        self._scroll.frame.pack(fill="x")
        self._skin, self._tips = skin, tips
        self._items: dict[int, MoodletView] = {}
        self._ids: tuple[int, ...] | None = None

    def refresh(self, items: tuple[MoodletView, ...]) -> None:
        ids = tuple(v.value.instance_id for v in items)
        self._items = {v.value.instance_id: v for v in items}
        if ids == self._ids:
            return
        self._tips.hide()
        self._ids = ids
        for child in self._scroll.body.winfo_children():
            child.destroy()
        if not items:
            tk.Label(
                self._scroll.body,
                text=GERMAN_TEXT.format("vn.no_moodlets"),
                bg=self._skin.background,
                fg=self._skin.muted,
                font=(self._skin.font, 9),
                pady=20,
            ).pack()
        for item in items:
            label = tk.Label(
                self._scroll.body,
                text=item.label,
                image=self._skin.images.icon(
                    MOODLET_ICONS[item.value.definition_id], 40
                ),
                compound="top",
                wraplength=90,
                width=96,
                height=max(78, 44 + self._skin.small_line_height * 3),
                font=(self._skin.font, 8),
                bg="#F7E9EF" if item.value.polarity == "negative" else "#EAF2F8",
                fg=self._skin.text,
                highlightthickness=1,
                highlightbackground=self._skin.background,
                highlightcolor=self._skin.accent,
            )
            label.pack(side="left", padx=2)
            self._tips.attach(
                label,
                partial(self._description, item.value.instance_id),
            )
        self._scroll.adopt()

    def _description(self, key: int) -> str:
        return moodlet_description(self._items[key])
