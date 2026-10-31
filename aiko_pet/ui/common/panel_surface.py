"""Prepared passive VN panel artwork behind ordinary, accessible Tk content."""

from __future__ import annotations

import tkinter as tk

from .icon_images import IconImages


class PanelSurface:
    def __init__(
        self, parent: tk.Misc, images: IconImages, *,
        background: str = "#FCF7F9", surface: str = "panel_surface.panel",
    ) -> None:
        self.frame = tk.Frame(parent, bg=background, bd=0)
        self._surface = surface
        self._images = images
        self._image: tk.PhotoImage | None = None
        self._size = (0, 0)
        self._background = tk.Label(self.frame, bd=0, bg=background)
        self._background.place(x=0, y=0, relwidth=1, relheight=1)
        self.body = tk.Frame(self.frame, bg="#FCF7F9", bd=0)
        self.body.pack(fill="both", expand=True, padx=10, pady=10)
        self.frame.bind("<Configure>", self._resize, add="+")
        self.frame.bind("<Destroy>", self._destroyed, add="+")

    def _resize(self, event: tk.Event) -> None:
        size = event.width, event.height
        if event.widget is not self.frame or size == self._size:
            return
        self._size = size
        self._image = self._images.panel_art(*size, surface=self._surface)
        self._background.configure(image=self._image)

    def _destroyed(self, event: tk.Event) -> None:
        if event.widget is self.frame:
            self._image = None
