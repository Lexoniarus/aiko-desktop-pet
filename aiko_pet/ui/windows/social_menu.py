"""Embedded social choices and current preparation status; credits live in settings."""

from __future__ import annotations

import tkinter as tk
from functools import partial
from typing import Callable

from ...application.social_content import PreparedSocialContent, SocialCategory
from ...pet.content import GERMAN_TEXT
from ..common.image_button import ImageButton, update_button_state
from ..common.skin import AikoSkin
from .embedded_selector import EmbeddedSelector


class SocialMenu(EmbeddedSelector):
    def __init__(
        self,
        parent: tk.Frame,
        *,
        selected: Callable[[SocialCategory | None], None],
        closed: Callable[[], None],
        enabled: Callable[[], bool],
        can_interact: Callable[[], bool],
        snapshot: Callable[[], tuple[str, PreparedSocialContent | None]],
        skin: AikoSkin,
        horoscope_choice: Callable[[], tuple[str, bool]] = lambda: ("", True),
        can_place_item: Callable[[], bool] = lambda: True,
    ) -> None:
        super().__init__(
            parent, skin, title=GERMAN_TEXT.format("ui.talk"), closed=closed
        )
        self._selected, self._enabled, self._can_interact = (
            selected,
            enabled,
            can_interact,
        )
        self._snapshot = snapshot
        self._horoscope_choice = horoscope_choice
        self._can_place_item = can_place_item
        self.buttons: dict[SocialCategory | None, ImageButton] = {}
        for category in (None, *SocialCategory):
            key = (
                "social.plain" if category is None else f"social.name.{category.value}"
            )
            icon = (
                "status_social"
                if category in (None, SocialCategory.HOROSCOPE)
                else f"wish_{category.value}"
            )
            button = skin.button(
                self.scroll.body,
                GERMAN_TEXT.format(key),
                partial(self.choose, category),
                size="menu_social",
                icon=skin.images.icon(icon, 24),
                align_left=True,
            )
            button.pack(fill="x", pady=2)
            if category == SocialCategory.HOROSCOPE:
                button.bind("<ButtonPress-1>", self._book_press)
            self.buttons[category] = button
        self.status = tk.Label(
            self.scroll.body,
            bg=skin.background,
            fg=skin.muted,
            font=(skin.font, 8),
            wraplength=215,
            justify="left",
        )
        self.status.pack(fill="x", pady=4)
        self.scroll.adopt()
        self.refresh()

    def _book_press(self, _event: tk.Event) -> str:
        self.choose(SocialCategory.HOROSCOPE)
        return "break"

    def choose(self, category: SocialCategory | None) -> None:
        if self._closed:
            return
        if category == SocialCategory.HOROSCOPE:
            if not self._can_place_item() or not self._horoscope_choice()[1]:
                return
            # Like food: destroy the selector before capturing the press gesture.
            self.close()
            self._selected(category)
            return
        if not self._can_interact() or category is not None and not self._enabled():
            return
        self._selected(category)
        self.refresh()

    def refresh(self) -> None:
        if self._closed:
            return
        allowed, enabled = self._can_interact(), self._enabled()
        for category, button in self.buttons.items():
            category_allowed = True
            if category == SocialCategory.HOROSCOPE:
                label, category_allowed = self._horoscope_choice()
                if label and button.cget("text") != label:
                    button.configure(text=label)
            update_button_state(
                button,
                enabled=(self._can_place_item() and category_allowed
                         if category == SocialCategory.HOROSCOPE else
                         allowed and (category is None or enabled)),
            )
        status, _source = self._snapshot()
        text = status if enabled else GERMAN_TEXT.format("social.disabled")
        if self.status.cget("text") != text:
            self.status.configure(text=text)
