"""Game-owned stack, hand contact and ballistic chip presentation."""

from __future__ import annotations

import math
import tkinter as tk
from collections.abc import Callable

from ...asset_paths import GAME_ART_DIR
from ..pet_view.game_effects import GameEffects
from ..view_models.chip_flight import ChipTarget, flight_height, flight_point
from ..view_models.connect_four_geometry import CELL, CHIP, MARGIN, PREVIEW
from .game_presentation import GamePresentation


class ConnectFourThrow:
    def __init__(
        self, window: tk.Toplevel, canvas: tk.Canvas, presentation: GamePresentation,
        *, topmost: bool,
    ) -> None:
        self._window, self._canvas, self._presentation = window, canvas, presentation
        self.effects = GameEffects(window, topmost=topmost,
                                   configure=presentation.configure)
        self._generation = 0
        self._closed = False
        self._resting = True
        self._follow()

    def _follow(self) -> None:
        if self._closed:
            return
        x, y, scale = self._presentation.origin()
        chip = self.effects.image(GAME_ART_DIR / 'c4-pile.png', 32 * scale)
        for i in range(3):
            if i < 2 or self._resting:
                self.effects.show(f'stack{i}', chip, x + 80 * scale,
                                  y + (178 - i * 4) * scale)
        self.effects.later(100, self._follow)

    def target(self, cell: int) -> ChipTarget:
        x, y = self._canvas.winfo_rootx(), self._canvas.winfo_rooty()
        return ChipTarget(x + MARGIN + (cell % 7 + .5) * CELL, y + PREVIEW - 20,
                          x + MARGIN, x + MARGIN + 7 * CELL, y + PREVIEW, CHIP)

    def play(self, cell: int, done: Callable[[], None]) -> None:
        self._generation += 1
        generation = self._generation
        self._resting = False
        self.effects.hide('stack2')
        points = [None, (96, 164), (96, 184), (96, 181), (96, 171),
                  (96, 143), (96, 146), (96, 153)]

        def marker(index: int) -> None:
            if self._closed or generation != self._generation:
                return
            x, y, scale = self._presentation.origin()
            point = points[index]
            if point and index >= 3 and index <= 5:
                chip = self.effects.image(GAME_ART_DIR / 'c4-red.png', 32 * scale)
                self.effects.show('held', chip, x + (point[0] - 16) * scale,
                                  y + (point[1] - 18) * scale)
                mask = self.effects.image(GAME_ART_DIR / 'c4-hands' /
                                          f'{index:02d}.png', 192 * scale)
                self.effects.show('mask', mask, x, y - 2 * scale)
            if index == 5:
                self.effects.later(30, release)

        def release() -> None:
            if self._closed or generation != self._generation:
                return
            x, y, scale = self._presentation.origin()
            start = (x + 96 * scale, y + 141 * scale)
            self.effects.hide('held')
            self.effects.hide('mask')

            def draw(t: float) -> None:
                target = self.target(cell)
                px, py = flight_point(t, start, target)
                size = CHIP
                chip = self.effects.image(GAME_ART_DIR / 'c4-red.png', size)
                self.effects.show('flying', chip, px - size / 2, py - size / 2)

            def fall() -> None:
                self.effects.hide('flying')
                target = self.target(cell)
                height = flight_height(start, target)
                speed = (target.y - start[1] + 4 * height) / 1240
                gravity = 8 * height / 1240 ** 2
                distance = (cell // 7 + .5) * CELL + 20
                ms = (-speed + math.sqrt(speed ** 2 + 2 * gravity * distance)) / gravity
                chip = self.effects.image(GAME_ART_DIR / 'c4-red.png', CHIP)

                def drop(t: float) -> None:
                    self._canvas.delete('throwing')
                    elapsed = t * ms
                    py = PREVIEW - 20 + speed * elapsed + .5 * gravity * elapsed ** 2
                    self._canvas.create_image(MARGIN + (cell % 7 + .5) * CELL, py,
                                              image=chip, tags='throwing')
                    self._canvas.tag_lower('throwing', 'board_face')

                def landed() -> None:
                    self._canvas.delete('throwing')
                    self._resting = True
                    done()

                self.effects.tween(max(1, round(ms)), drop, landed)
            self.effects.tween(1240, draw, fall)

        self._presentation.action(
            'pick_up', (180, 120, 120, 130, 110, 140, 140, 220), marker,
            lambda: None,
        )

    def close(self) -> None:
        self._closed = True
        self._generation += 1
        self._presentation.cancel()
        self._presentation.look(None)
        self.effects.close()
