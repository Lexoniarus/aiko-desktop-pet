"""The lifecycle surface required by the utility-window owner."""

import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from ..common.mastermind_images import MastermindImages
from ..common.playing_card_images import PlayingCardImages
from ..view_models.game_models import HandView
from ..view_models.mastermind_models import CodeView


@dataclass(frozen=True, slots=True)
class GameCardPorts:
    images: PlayingCardImages
    show: Callable[[HandView, bool], None]
    clear: Callable[[], None]
    set_topmost: Callable[[bool], None]


@dataclass(frozen=True, slots=True)
class GameCodePorts:
    images: MastermindImages
    show: Callable[[CodeView], None]
    clear: Callable[[], None]
    set_topmost: Callable[[bool], None]
    move: Callable[[], None] = lambda: None
    open: Callable[[Callable[[], None]], None] = lambda done: done()
    snack: Callable[[bool], None] = lambda _: None
    point: Callable[[], tuple[float, float]] = lambda: (0, 0)


class GameWindow(Protocol):
    @property
    def window(self) -> tk.Toplevel: ...

    def greet(self) -> None: ...

    def close(self) -> None: ...

    def set_topmost(self, enabled: bool) -> None: ...
