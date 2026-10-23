"""Root-local Kenney images; existing Connect Four pieces are shared by path."""

import tkinter as tk

from ...asset_paths import CONNECT_FOUR_DIR, MASTERMIND_DIR


class MastermindImages:
    def __init__(self, root: tk.Tk) -> None:
        self._root = root
        self._images: dict[tuple[str | None, int], tk.PhotoImage] = {}

    def get(self, color: str | None, scale: int = 1) -> tk.PhotoImage:
        if color not in (None, "red", "yellow", "blue", "green", "purple", "white"):
            raise ValueError("Unknown piece")
        if scale not in (1, 2):
            raise ValueError("Unsupported scale")
        key = color, scale
        if key not in self._images:
            directory = (
                CONNECT_FOUR_DIR if color in ("red", "yellow") else MASTERMIND_DIR
            )
            source = tk.PhotoImage(
                master=self._root, file=str(directory / f"{color or 'black'}.png")
            )
            self._images[key] = source if scale == 1 else source.zoom(scale)
        return self._images[key]

    def clear(self) -> None:
        self._images.clear()
