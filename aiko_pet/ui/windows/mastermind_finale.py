"""Cosmetic snack ending: safe opening and existing eating, with no care effects."""

import tkinter as tk
from collections.abc import Callable

from ...asset_paths import GAME_ART_DIR
from ..pet_view.game_effects import GameEffects
from .game_contracts import GameCodePorts
from .game_presentation import GamePresentation


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
            anchors = [156, 138, 132, 138, 138, 138, 156, 156]

            def marker(index: int) -> None:
                x, y, scale = self._presentation.origin()
                if index <= 5:
                    snack = self.effects.image(
                        GAME_ART_DIR / 'mm-donut.png', 18 * scale,
                    )
                    self.effects.show('snack', snack, x + 87 * scale,
                                      y + (anchors[index] - 14) * scale)
                else:
                    self.effects.hide('snack')

            self._presentation.action(
                'eat', (500, 350, 300, 240, 550, 600, 450, 600), marker, done,
            )

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
