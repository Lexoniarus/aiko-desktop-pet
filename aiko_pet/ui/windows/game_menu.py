"""Embedded game choice; deferred application admission remains authoritative."""

from __future__ import annotations

import tkinter as tk
from functools import partial
from typing import Callable

from ...asset_paths import CONNECT_FOUR_DIR, MASTERMIND_DIR, PLAYING_CARDS_DIR
from ...games.contracts import GameId
from ...pet.content import GERMAN_TEXT
from ..common.image_button import ImageButton, update_button_state
from ..common.skin import AikoSkin
from ..view_models.emotional_text import GAME_ICONS
from .embedded_selector import EmbeddedSelector


class GameMenu(EmbeddedSelector):
    def __init__(
        self,
        parent: tk.Frame,
        *,
        choices: tuple[GameId, ...],
        selected: Callable[[GameId], None],
        closed: Callable[[], None],
        skin: AikoSkin,
        can_select: Callable[[], bool],
    ) -> None:
        super().__init__(
            parent, skin, title=GERMAN_TEXT.format("game.select"), closed=closed
        )
        self._selected, self._can_select = selected, can_select
        self.buttons: dict[GameId, ImageButton] = {}
        for game in choices:
            image = (
                skin.images.file(PLAYING_CARDS_DIR / "card_spades_A.png", 40)
                if game is GameId.BLACKJACK
                else skin.images.file(CONNECT_FOUR_DIR / "red.png", 40)
                if game is GameId.CONNECT_FOUR
                else skin.images.file(MASTERMIND_DIR / "blue.png", 40)
                if game is GameId.MASTERMIND
                else skin.images.icon(GAME_ICONS[game.value], 40)
            )
            button = skin.button(
                self.scroll.body,
                GERMAN_TEXT.format(f"game.name.{game.value}"),
                partial(self.choose, game),
                size="menu_game",
                icon=image,
                align_left=True,
            )
            button.pack(fill="x", pady=4)
            self.buttons[game] = button
        self.scroll.adopt()
        self.refresh()

    def refresh(self) -> None:
        if not self._closed:
            allowed = self._can_select()
            for button in self.buttons.values():
                update_button_state(button, enabled=allowed)

    def choose(self, game: GameId) -> None:
        if self._closed or game not in self.buttons or not self._can_select():
            return
        self.close()
        self._selected(game)
