"""Compose game graphics and native effects without owning game state."""

import tkinter as tk
from collections.abc import Callable, Iterable
from dataclasses import dataclass

from ..application.settings import PetSettings
from ..ui.common.mastermind_images import MastermindImages
from ..ui.common.playing_card_images import PlayingCardImages
from ..ui.common.window_geometry import WindowBounds
from ..ui.pet_view.blackjack_hand_presenter import BlackjackHandPresenter
from ..ui.pet_view.desktop_window import DesktopWindow
from ..ui.pet_view.mastermind_safe_presenter import MastermindSafePresenter
from ..ui.pet_view.speech_presenter import SpeechPresenter
from ..ui.view_models.game_models import HandAnchor
from ..ui.windows.game_contracts import GameCardPorts, GameCodePorts
from ..ui.windows.hover_ui import HoverUi
from .object_windows import configure_object_window


def occupied_bounds(
    hover: HoverUi, speech: SpeechPresenter,
) -> tuple[WindowBounds, ...]:
    windows = [speech.bubble]
    if hover.game_window is not None:
        windows.append(hover.game_window.window)
    return tuple(WindowBounds(
        item.winfo_rootx(), item.winfo_rooty(),
        item.winfo_rootx() + item.winfo_width(),
        item.winfo_rooty() + item.winfo_height(),
    ) for item in windows if item is not None and item.winfo_exists())


def collect_overlay_windows(
    root: tk.Tk, world_windows: Iterable[tk.Toplevel], hover: HoverUi,
    speech: SpeechPresenter, hand: BlackjackHandPresenter,
    code: MastermindSafePresenter | None = None,
) -> list[tk.Tk | tk.Toplevel]:
    """Compose the existing owners' stack order without retaining window state."""
    windows: list[tk.Tk | tk.Toplevel] = [root, *world_windows]
    windows.extend(hover.control_windows)
    windows.extend(hand.windows)
    if code is not None:
        windows.extend(code.windows)
    if speech.bubble is not None:
        windows.append(speech.bubble)
    if hover.settings_window is not None:
        windows.append(hover.settings_window.window)
    return windows


@dataclass(frozen=True, slots=True)
class GameVisuals:
    images: PlayingCardImages
    hand: BlackjackHandPresenter
    code_images: MastermindImages
    code: MastermindSafePresenter

    @property
    def ports(self) -> GameCardPorts:
        return GameCardPorts(
            self.images, self.hand.show, self.clear_cards, self.hand.set_topmost,
            self.hand.point,
        )

    @property
    def code_ports(self) -> GameCodePorts:
        return GameCodePorts(self.code_images, self.code.show, self.clear_code,
                             self.code.set_topmost, self.code.move, self.code.open,
                             self.code.snack, self.code.point)

    def clear_cards(self) -> None:
        self.hand.hide()
        self.images.clear()

    def clear_code(self) -> None:
        self.code.hide()
        self.code_images.clear()

    def clear(self) -> None:
        self.clear_cards()
        self.clear_code()

    def move(self) -> None:
        self.hand.move()
        self.code.move()


def assemble_game_visuals(
    window: DesktopWindow, settings: PetSettings,
    restore_stack: Callable[[], object],
    *, occupied: Callable[[], tuple[WindowBounds, ...]] = lambda: (),
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
    code_images = MastermindImages(window.root)
    code = MastermindSafePresenter(
        window.root, images=code_images,
        anchor=lambda: HandAnchor(
            settings.x or 0, settings.y or 0, window.width, window.height,
            window.track.left, 0, window.track.right, window.track.ground_y,
            settings.scale,
        ), topmost=lambda: settings.always_on_top,
        configure_window=lambda overlay: configure_object_window(
            overlay,
        ),
        restore_stack=restore_stack, occupied=occupied,
    )
    return GameVisuals(images, hand, code_images, code)
