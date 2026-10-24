"""Embedded finite-stock placement choices; no feeding or character admission."""

from __future__ import annotations

import tkinter as tk
from functools import partial
from typing import Callable

from ...pet.content import GERMAN_TEXT
from ..common.image_button import ImageButton, update_button_state
from ..common.skin import AikoSkin
from ..view_models.food_models import FoodChoice, FoodChoiceId
from .embedded_selector import EmbeddedSelector


class FoodMenu(EmbeddedSelector):
    def __init__(
        self,
        parent: tk.Frame,
        *,
        choices: tuple[FoodChoice, ...],
        selected: Callable[[FoodChoiceId], None],
        closed: Callable[[], None],
        skin: AikoSkin,
        can_select: Callable[[], bool],
    ) -> None:
        super().__init__(
            parent, skin, title=GERMAN_TEXT.format("food.header"), closed=closed
        )
        self._selected, self._can_select = selected, can_select
        self.buttons: dict[str, ImageButton] = {}
        for choice in choices:
            button = skin.button(
                self.scroll.body,
                f"{choice.name}\n{choice.benefit_label}",
                partial(self.choose, choice.id),
                size="menu_choice",
                icon=skin.images.file(choice.image_path, 32),
                align_left=True,
            )
            button.pack(fill="x", pady=2)
            button.bind("<ButtonPress-1>", partial(self._press, choice.id))
            self.buttons[choice.id] = button
        self.scroll.adopt()
        self.refresh()

    def refresh(self) -> None:
        if not self._closed:
            allowed = self._can_select()
            for button in self.buttons.values():
                update_button_state(button, enabled=allowed)

    def choose(self, food_id: FoodChoiceId) -> None:
        if self._closed or food_id not in self.buttons or not self._can_select():
            return
        self.close()
        self._selected(food_id)

    def _press(self, food_id: FoodChoiceId, _event: tk.Event) -> str:
        self.choose(food_id)
        return "break"
