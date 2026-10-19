"""Compose game graphics and native effects without owning game state."""

import tkinter as tk
from collections.abc import Callable, Iterable
from dataclasses import dataclass

from ..application.settings import PetSettings
from ..ui.common.playing_card_images import PlayingCardImages
from ..ui.pet_view.blackjack_hand_presenter import BlackjackHandPresenter
from ..ui.pet_view.desktop_window import DesktopWindow
from ..ui.pet_view.speech_presenter import SpeechPresenter
from ..ui.view_models.game_models import HandAnchor
from ..ui.windows.game_contracts import GameCardPorts
from ..ui.windows.hover_ui import HoverUi
from .object_windows import configure_object_window


def collect_overlay_windows(
    root: tk.Tk, world_windows: Iterable[tk.Toplevel], hover: HoverUi,
    speech: SpeechPresenter, hand: BlackjackHandPresenter,
) -> list[tk.Tk | tk.Toplevel]:
    """Compose the existing owners' stack order without retaining window state."""
    windows: list[tk.Tk | tk.Toplevel] = [root, *world_windows]
    windows.extend(hover.control_windows)
    windows.extend(hand.windows)
    if speech.bubble is not None:
        windows.append(speech.bubble)
    if hover.settings_window is not None:
        windows.append(hover.settings_window.window)
    return windows


@dataclass(frozen=True, slots=True)
class GameVisuals:
    images: PlayingCardImages
    hand: BlackjackHandPresenter

    @property
    def ports(self) -> GameCardPorts:
        return GameCardPorts(
            self.images, self.hand.show, self.clear, self.hand.set_topmost,
        )

    def clear(self) -> None:
        self.hand.hide()
        self.images.clear()


def assemble_game_visuals(
    window: DesktopWindow, settings: PetSettings,
    restore_stack: Callable[[], object],
) -> GameVisuals:
    images = PlayingCardImages(window.root)
    hand = BlackjackHandPresenter(
        window.root, images=images,
        anchor=lambda: HandAnchor(
            settings.x or 0, settings.y or 0, window.width, window.height,
            window.track.left, 0, window.track.right, window.track.ground_y,
            settings.scale,
        ),
        topmost=lambda: settings.always_on_top,
        configure_window=lambda overlay: configure_object_window(
            overlay, interactive=True,
        ),
        restore_stack=restore_stack,
    )
    return GameVisuals(images, hand)
