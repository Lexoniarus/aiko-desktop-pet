"""Cosmetic snack ending: safe opening and existing eating, with no care effects."""

import tkinter as tk
from collections.abc import Callable

from ...asset_paths import GAME_ART_DIR
from ...presentation.games.ports import GamePresentation
from ..pet_view.game_effects import GameEffects
from .game_contracts import GameCodePorts


class MastermindFinale:
    def __init__(
        self, window: tk.Toplevel, code: GameCodePorts,
        presentation: GamePresentation, *, topmost: bool,
    ) -> None:
        self._code, self._presentation = code, presentation
        self.effects = GameEffects(window, topmost=topmost,
                                   configure=presentation.configure)
        self._closed = False

    def play(self, _won: bool, done: Callable[[], None]) -> None:
        self._presentation.look(self._code.point())

        def eat() -> None:
            if self._closed:
                return
            self._presentation.look(None)
            self._code.snack(False)

            def marker(index: int) -> None:
                x, y, scale = self._presentation.origin()
                anchor = self._presentation.food_anchor('eat', index)
                if anchor is not None:
                    snack = self.effects.image(
                        GAME_ART_DIR / 'mm-donut.png', 18 * scale,
                    )
                    self.effects.show('snack', snack, x + (anchor[0] - 9) * scale,
                                      y + (anchor[1] - 14) * scale)
                else:
                    self.effects.hide('snack')

            def finished() -> None:
                self.effects.hide('snack')
                if not self._closed:
                    done()

            self._presentation.action('eat', None, marker, finished)

        def opened() -> None:
            if not self._closed:
                self._presentation.look(None)
                self.effects.later(500, eat)
        self._code.open(opened)

    def close(self) -> None:
        self._closed = True
        self._presentation.cancel()
        self._presentation.look(None)
        self.effects.close()
