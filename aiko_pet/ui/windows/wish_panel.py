"""Inner/spoken wishes with concrete targets, original time and objective scope."""

import tkinter as tk
from functools import partial
from pathlib import Path
from typing import Mapping

from ...asset_paths import PLAYING_CARDS_DIR
from ...pet.content import GERMAN_TEXT
from ..common.description_tip import DescriptionTip
from ..common.scroll_region import ScrollRegion
from ..common.skin import AikoSkin
from ..view_models.contracts import WishView
from ..view_models.emotional_text import (
    duration_text,
    wish_badge,
    wish_description,
    wish_icon,
)


class WishPanel:
    def __init__(
        self,
        parent: tk.Misc,
        skin: AikoSkin,
        tips: DescriptionTip,
        food_icons: Mapping[str, Path],
    ) -> None:
        self.frame = tk.Frame(parent, bg=skin.background)
        tk.Label(
            self.frame,
            text=GERMAN_TEXT.format("vn.wishes"),
            bg=skin.background,
            fg=skin.muted,
            font=(skin.font, 9, "bold"),
        ).pack(anchor="w")
        self._scroll = ScrollRegion(
            self.frame,
            skin,
            width=620,
            height=max(116, skin.small_line_height * 8 + 16),
            horizontal=True,
        )
        self._scroll.frame.pack(fill="x")
        self._skin, self._tips = skin, tips
        self._food_icons = food_icons
        self._ids: tuple[int, ...] | None = None
        self._items: dict[int, WishView] = {}
        self._labels: dict[int, tk.Label] = {}

    def refresh(self, items: tuple[WishView, ...]) -> None:
        self._items = {v.value.instance_id: v for v in items}
        ids = tuple(self._items)
        if ids != self._ids:
            self._tips.hide()
            self._ids = ids
            self._labels.clear()
            for child in self._scroll.body.winfo_children():
                child.destroy()
            if not items:
                tk.Label(
                    self._scroll.body,
                    text=GERMAN_TEXT.format("vn.no_wishes"),
                    bg=self._skin.background,
                    fg=self._skin.muted,
                    font=(self._skin.font, 9),
                    pady=30,
                ).pack()
            for item in items:
                self._card(item)
            self._scroll.adopt()
        for key, label in self._labels.items():
            item = self._items[key]
            text = "\n".join(
                p
                for p in (
                    item.target_label,
                    item.label if item.label != item.target_label else "",
                    (
                        GERMAN_TEXT.format(
                            "vn.rounds_short",
                            completed=str(item.value.game.completed_rounds),
                            required=str(item.value.game.required_rounds),
                        )
                        if item.value.game is not None
                        else ""
                    ),
                    GERMAN_TEXT.format(
                        "vn.wish_meta",
                        time=duration_text(item.value.remaining_seconds),
                        state=GERMAN_TEXT.format(
                            "vn.wish_spoken_tag"
                            if item.value.expressed
                            else "vn.wish_inner_tag"
                        ),
                    ),
                    GERMAN_TEXT.format("vn.wish_unavailable_tag")
                    if item.restriction_label
                    else "",
                )
                if p
            )
            if label.cget("text") != text:
                label.configure(text=text)

    def _card(self, item: WishView) -> None:
        skin = self._skin
        card = tk.Frame(
            self._scroll.body,
            width=198,
            height=max(112, skin.small_line_height * 8 + 12),
            bg="#FFFCFD",
            highlightthickness=1,
            highlightbackground=skin.border,
        )
        card.pack(side="left", padx=3)
        card.pack_propagate(False)
        icon = tk.Canvas(card, width=48, height=48, bg="#FFFCFD", highlightthickness=0)
        icon.pack(side="left", anchor="n", padx=(3, 0), pady=5)
        icon.create_image(24, 24, image=skin.images.icon("wish_thought_bubble", 48))
        key = wish_icon(item)
        image = (
            skin.images.file(self._food_icons[item.value.target_id], 24)
            if key == "food"
            else skin.images.file(PLAYING_CARDS_DIR / "card_spades_A.png", 24)
            if key == "blackjack"
            else skin.images.icon(key, 24)
        )
        icon.create_image(24, 21, image=image)
        badge = wish_badge(item)
        if badge is not None:
            icon.create_image(36, 36, image=skin.images.icon(badge, 24))
        label = tk.Label(
            card,
            bg="#FFFCFD",
            fg=skin.text,
            font=(skin.font, 8),
            wraplength=136,
            justify="left",
            anchor="nw",
        )
        label.pack(fill="both", expand=True, padx=3, pady=5)
        self._labels[item.value.instance_id] = label
        for widget in (card, icon, label):
            self._tips.attach(
                widget,
                partial(self._description, item.value.instance_id),
            )

    def _description(self, key: int) -> str:
        return wish_description(self._items[key])
