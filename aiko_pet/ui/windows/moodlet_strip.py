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
            height=1,
            horizontal=True,
            autohide=True,
            fit_content=True,
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
                pady=10,
            ).pack()
        for item in items:
            card = tk.Frame(self._scroll.body, bg=self._skin.background)
            card.pack(side="left", padx=3)
            halo = tk.Canvas(
                card, width=42, height=42, bg=self._skin.background,
                bd=0, highlightthickness=0,
            )
            halo.pack()
            halo.create_oval(
                1, 1, 41, 41, outline="",
                fill="#F7E9EF" if item.value.polarity == "negative" else "#EAF2F8",
            )
            halo.create_image(
                21, 21, image=self._skin.images.icon(
                    MOODLET_ICONS[item.value.definition_id], 40
                ),
            )
            label = tk.Label(
                card,
                text=item.label,
                wraplength=90,
                width=13,
                font=(self._skin.font, 8),
                bg=self._skin.background,
                fg=self._skin.text,
                highlightthickness=1,
                highlightbackground=self._skin.background,
                highlightcolor=self._skin.accent,
            )
            label.pack(pady=(2, 0))
            self._tips.attach(
                halo, partial(self._description, item.value.instance_id),
                focusable=False,
            )
            self._tips.attach(
                label,
                partial(self._description, item.value.instance_id),
            )
        self._scroll.adopt()
        self._scroll.refresh_layout()

    def _description(self, key: int) -> str:
        return moodlet_description(self._items[key])
