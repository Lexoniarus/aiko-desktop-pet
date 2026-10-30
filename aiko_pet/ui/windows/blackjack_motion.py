"""One visible deck, fixed-size cards and remote dealer gestures."""
from __future__ import annotations

import math
import tkinter as tk
from collections.abc import Callable

from ...games.blackjack import Table
from ...games.playing_cards import Card
from ..common.game_pacing import GAME_PACING
from ..pet_view.game_effects import GameEffects
from ..view_models.game_models import HandView
from .game_contracts import GameCardPorts
from .game_presentation import GamePresentation


class BlackjackMotion:
    def __init__(
        self, window: tk.Toplevel, cards: GameCardPorts,
        presentation: GamePresentation,
        player: Callable[[int, int], tuple[float, float]],
        visible: Callable[[], Table], clear: Callable[[], None],
        hit: Callable[[], None], *, topmost: bool,
    ) -> None:
        self.cards, self.presentation = cards, presentation
        self.player, self.visible, self.clear = player, visible, clear
        self.hit = hit
        self.effects = GameEffects(window, topmost=topmost,
                                   configure=presentation.configure)
        self._closed = False
        self._follow()

    def deck(self) -> tuple[float, float]:
        x, y, scale = self.presentation.origin()
        return x + 168 * scale, y + 38 * scale

    def _follow(self) -> None:
        if not self._closed:
            self.effects.show('deck', self.cards.images.draw_pile(2), *self.deck())
            self.effects.control('deck', self.presentation.configure_control, self.hit)
            self.effects.later(100, self._follow)

    def play(
        self, kind: str, card: Card | None, index: int, done: Callable[[], None],
    ) -> None:
        if kind == 'shuffle':
            self.presentation.look(self.deck())
            self.presentation.action(
                'attack', GAME_PACING.card_shuffle_ms, lambda _: None, lambda: None,
            )

            def draw(t: float) -> None:
                x, y = self.deck()
                for i in range(6):
                    spread = math.sin(math.pi * t) * math.sin(t * 6 * math.pi + i)
                    self.effects.show(f'shuffle{i}', self.cards.images.get(None, 2),
                                      x + spread * 38, y - abs(spread) * 16 - i)

            def end() -> None:
                for i in range(6):
                    self.effects.hide(f'shuffle{i}')
                self.presentation.look(None)
                done()
            self.effects.tween(GAME_PACING.card_shuffle_ms, draw, end)
        elif kind == 'gather':
            table = self.visible()
            points = [self.player(i, len(table.player))
                      for i in range(len(table.player))]
            points += [self.cards.point(i, len(table.dealer))
                       for i in range(len(table.dealer))]
            self.clear()
            self.cards.show(HandView(), False)

            def gather(t: float) -> None:
                dx, dy = self.deck()
                for i, (x, y) in enumerate(points):
                    self.effects.show(f'gather{i}', self.cards.images.get(None, 2),
                                      x + (dx - x) * t, y + (dy - y) * t)

            def end_gather() -> None:
                for i in range(len(points)):
                    self.effects.hide(f'gather{i}')
                done()
            self.effects.tween(GAME_PACING.card_gather_ms, gather, end_gather)
        else:
            start = self.deck()
            count = index + 1
            target = self.player if kind == 'player' else self.cards.point
            self.presentation.look(target(index, count))

            def fly(t: float) -> None:
                x, y = target(index, count)
                ease = t * t * (3 - 2 * t)
                # Hole cards remain backs throughout; no hidden face is requested.
                face = card if t >= .5 else None
                flip = min(7, max(0, int((t - .2) / .6 * 8)))
                compression = (1, 2, 4, 8, 8, 4, 2, 1)[flip] if card else 1
                image = self.cards.images.get(face, 2, compression)
                self.effects.show('flight', image,
                                  start[0] + (x - start[0]) * ease
                                  + (128 - image.width()) / 2,
                                  start[1] + (y - start[1]) * ease
                                  - 28 * math.sin(math.pi * t))

            def landed() -> None:
                self.effects.hide('flight')
                self.presentation.look(None)
                done()
            self.effects.tween(GAME_PACING.card_flight_ms, fly, landed)

    def close(self) -> None:
        self._closed = True
        self.presentation.cancel()
        self.presentation.look(None)
        self.effects.close()
