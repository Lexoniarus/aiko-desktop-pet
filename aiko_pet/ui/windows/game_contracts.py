"""The lifecycle surface required by the utility-window owner."""

import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from ..common.playing_card_images import PlayingCardImages
from ..view_models.game_models import HandView


@dataclass(frozen=True, slots=True)
class GameCardPorts:
    images: PlayingCardImages
    show: Callable[[HandView, bool], None]
    clear: Callable[[], None]
    set_topmost: Callable[[bool], None]


class GameWindow(Protocol):
    @property
    def window(self) -> tk.Toplevel: ...

    def greet(self) -> None: ...

    def close(self) -> None: ...

    def set_topmost(self, enabled: bool) -> None: ...
