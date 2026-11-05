"""One Tk-owned cache shared by player cards and Aiko's desktop hand."""

import tkinter as tk
from pathlib import Path
from typing import Any, cast

from ...asset_paths import PLAYING_CARDS_DIR
from ...games.playing_cards import Card


class PlayingCardImages:
    def __init__(self, root: tk.Tk, *, directory: Path = PLAYING_CARDS_DIR) -> None:
        self._root = root
        self._directory = directory
        self._images: dict[tuple[Card | None, int, int], tk.PhotoImage] = {}
        self._piles: dict[int, tk.PhotoImage] = {}

    def get(
        self, card: Card | None, scale: int = 1, compression: int = 1,
    ) -> tk.PhotoImage:
        if scale not in (1, 2) or compression not in (1, 2, 4, 8):
            raise ValueError("Unsupported card scale/flip frame")
        key = card, scale, compression
        if key not in self._images:
            if compression != 1:
                # Python 3.13's Tk stubs reject a numeric vertical factor.
                # Preserve the existing horizontal-only image compression.
                result = self.get(card, scale).subsample(
                    compression, cast(Any, 1),
                )
            else:
                filename = card.asset_name if card else "card_back.png"
                source = tk.PhotoImage(
                    master=self._root, file=str(self._directory / filename),
                )
                result = source.zoom(scale) if scale != 1 else source
            self._images[key] = result
        return self._images[key]

    def draw_pile(self, scale: int = 2) -> tk.PhotoImage:
        """Layer the existing back into a visual draw control, without deck state."""
        back = self.get(None, scale)
        if scale not in self._piles:
            step = 4 * scale
            pile = tk.PhotoImage(
                master=self._root, width=back.width() + 2 * step,
                height=back.height() + 2 * step,
            )
            for offset in (2 * step, step, 0):
                pile.tk.call(
                    str(pile), "copy", str(back), "-to", offset, offset,
                    "-compositingrule", "overlay",
                )
            self._piles[scale] = pile
        return self._piles[scale]

    def clear(self) -> None:
        """Release references on the Tk thread after card widgets are destroyed."""
        self._images.clear()
        self._piles.clear()
