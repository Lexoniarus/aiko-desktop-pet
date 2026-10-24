"""Inner/spoken wishes with concrete targets, original time and objective scope."""

import tkinter as tk
from functools import partial
from pathlib import Path
from typing import Callable, Mapping, cast

from ...pet.content import GERMAN_TEXT
from ..common.description_tip import DescriptionTip
from ..common.panel_surface import PanelSurface
from ..common.scroll_region import ScrollRegion
from ..common.skin import AikoSkin
from ..view_models.contracts import WishView
from ..view_models.emotional_text import (
    GAME_FILES,
    duration_text,
    wish_badge,
    wish_description,
    wish_icon,
    wish_progress,
)


class WishPanel:
    def __init__(
        self,
        parent: tk.Misc,
        skin: AikoSkin,
        tips: DescriptionTip,
        food_icons: Mapping[str, Path], *,
        pin_wish: Callable[[int, bool], None] = lambda _id, _pinned: None,
        dismiss_wish: Callable[[int], None] = lambda _id: None,
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
            height=1,
            horizontal=True,
            autohide=True,
            fit_content=True,
        )
        self._scroll.frame.pack(fill="x")
        self._skin, self._tips = skin, tips
        self._food_icons = food_icons
        self._pin_wish, self._dismiss_wish = pin_wish, dismiss_wish
        self._pin_icons: dict[int, tk.Canvas] = {}
        self._ids: tuple[int, ...] | None = None
        self._items: dict[int, WishView] = {}
        self._labels: dict[int, tk.Label] = {}
        self._objectives: dict[int, tk.Label] = {}
        self._meta: dict[int, tk.Label] = {}
        self._cards: list[PanelSurface] = []

    def refresh(self, items: tuple[WishView, ...]) -> None:
        self._items = {v.value.instance_id: v for v in items}
        ids = tuple(self._items)
        layout_changed = ids != self._ids
        if layout_changed:
            self._tips.hide()
            self._labels.clear()
            self._objectives.clear()
            self._meta.clear()
            self._pin_icons.clear()
            for child in self._scroll.body.winfo_children():
                child.destroy()
            self._cards.clear()
            if not items:
                tk.Label(
                    self._scroll.body,
                    text=GERMAN_TEXT.format("vn.no_wishes"),
                    bg=self._skin.background,
                    fg=self._skin.muted,
                    font=(self._skin.font, 9),
                    pady=14,
                ).pack()
            for item in items:
                self._card(item)
            self._scroll.adopt()
        for key, label in self._labels.items():
            item = self._items[key]
            objective = "\n".join(
                p
                for p in (
                    item.label if item.label != item.target_label else "",
                    wish_progress(item, compact=True),
                )
                if p
            )
            meta = " · ".join(
                p for p in (
                    GERMAN_TEXT.format(
                        "vn.wish_meta",
                        time=(GERMAN_TEXT.format("vn.wish_pinned") if item.value.pinned
                              else duration_text(item.value.remaining_seconds)),
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
            for widget, text in (
                (label, item.target_label),
                (self._objectives[key], objective),
                (self._meta[key], meta),
            ):
                if widget.cget("text") != text:
                    widget.configure(text=text)
                    layout_changed = True
            self._pin_icons[key].itemconfigure(
                "pin", state="normal" if item.value.pinned else "hidden",
            )
        if layout_changed:
            self._scroll.refresh_layout()
        # Publish the rendered identity only after every card is complete. If an
        # asset/widget fails, the next refresh must rebuild the partial layout.
        self._ids = ids

    def _card(self, item: WishView) -> None:
        skin = self._skin
        surface = skin.surface(self._scroll.body)
        self._cards.append(surface)
        surface.frame.configure(
            highlightthickness=1, highlightbackground=skin.background,
            highlightcolor=skin.accent,
        )
        surface.frame.pack(side="left", padx=3, fill="y")
        card = surface.body
        card.grid_columnconfigure(1, minsize=132)
        card.grid_rowconfigure(0, minsize=24)
        icon = tk.Canvas(
            card, width=42, height=42, bg=skin.background, highlightthickness=0,
        )
        icon.grid(row=0, column=0, rowspan=2, sticky="nw", padx=(0, 5))
        icon.create_image(21, 21, image=skin.images.icon("wish_thought_bubble", 40))
        key = wish_icon(item)
        image = (
            skin.images.file(self._food_icons[item.value.target_id], 24)
            if key == "food"
            else skin.images.file(GAME_FILES[key], 24)
            if key in GAME_FILES
            else skin.images.icon(key, 24)
        )
        icon.create_image(21, 18, image=image)
        badge = wish_badge(item)
        if badge is not None:
            icon.create_image(32, 32, image=skin.images.icon(badge, 24))
        label = tk.Label(
            card,
            bg=skin.background,
            fg=skin.text,
            font=(skin.font, 9, "bold"),
            wraplength=104,
            justify="left",
            anchor="nw",
        )
        label.grid(row=0, column=1, sticky="nw", padx=(0, 28))
        objective = tk.Label(
            card, bg=skin.background, fg=skin.muted, font=(skin.font, 8),
            wraplength=132, justify="left", anchor="nw",
        )
        objective.grid(row=1, column=1, sticky="nw")
        meta = tk.Label(
            card, bg=skin.background, fg=skin.muted, font=(skin.font, 8),
            wraplength=180, justify="left", anchor="w",
        )
        meta.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(4, 0))
        pin = tk.Canvas(
            card, width=24, height=24, bg=skin.background, highlightthickness=0,
        )
        pin.create_image(12, 12, image=skin.images.icon("ui_pin", 24),
                         tags="pin", state="hidden")
        # Reserve space inside the title row, not a third card column. Pinning
        # must not widen three ordinary cards beyond the shared viewport.
        pin.place(relx=1, y=0, anchor="ne")
        self._pin_icons[item.value.instance_id] = pin
        self._labels[item.value.instance_id] = label
        self._objectives[item.value.instance_id] = objective
        self._meta[item.value.instance_id] = meta
        self._bind_card_controls(surface.frame, item.value.instance_id, focusable=True)

    def _bind_card_controls(
        self, widget: tk.Misc, key: int, *, focusable: bool = False,
    ) -> None:
        """Every card surface, including its passive artwork, owns the same clicks."""
        self._tips.attach(cast(tk.Widget, widget), partial(self._description, key),
                          focusable=focusable)
        # Replace the tip's tap toggle; hover/focus/keyboard still read details.
        widget.bind("<Button-3>", partial(self._unpin_or_dismiss, key))
        widget.bind("<Button-1>", partial(self._pin, key))
        for child in widget.winfo_children():
            self._bind_card_controls(child, key)

    def _pin(self, key: int, _event: tk.Event) -> str:
        item = self._items.get(key)
        if item is not None and not item.value.pinned:
            self._tips.hide()
            self._pin_wish(key, True)
        return "break"

    def _unpin_or_dismiss(self, key: int, _event: tk.Event) -> str:
        item = self._items.get(key)
        if item is not None:
            self._tips.hide()
            if item.value.pinned:
                self._pin_wish(key, False)
            else:
                self._dismiss_wish(key)
        return "break"

    def _description(self, key: int) -> str:
        return wish_description(self._items[key])
