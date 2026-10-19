"""Compose game graphics and native effects without owning game state."""

from collections.abc import Callable
from dataclasses import dataclass

from ..application.settings import PetSettings
from ..ui.common.playing_card_images import PlayingCardImages
from ..ui.pet_view.blackjack_hand_presenter import BlackjackHandPresenter
from ..ui.pet_view.desktop_window import DesktopWindow
from ..ui.view_models.game_models import HandAnchor
from .object_windows import configure_object_window


@dataclass(frozen=True, slots=True)
class GameVisuals:
    images: PlayingCardImages
    hand: BlackjackHandPresenter

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
