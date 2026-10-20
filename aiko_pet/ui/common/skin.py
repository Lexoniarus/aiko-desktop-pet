"""Shared VN tokens and root-local artwork; views retain layout ownership."""

from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont
from typing import Callable

from .icon_images import IconImages
from .image_button import ImageButton
from .panel_surface import PanelSurface


class AikoSkin:
    background = "#FCF7F9"
    text = "#3E4C61"
    muted = "#65758A"
    panel = "#EDF4FA"
    accent = "#657F9D"
    border = "#B8CDDF"
    title = "#FFFFFF"

    def __init__(self, root: tk.Tk) -> None:
        fonts = set(tkfont.families(root=root))
        self.font = "Segoe UI" if "Segoe UI" in fonts else "Arial"
        self.small_line_height = tkfont.Font(
            root=root, family=self.font, size=8
        ).metrics("linespace")
        self.images = IconImages(root)

    def release_images(self) -> None:
        self.images.release()

    def frame(self, parent: tk.Misc) -> tk.Frame:
        return tk.Frame(
            parent,
            bg=self.background,
            highlightthickness=1,
            highlightbackground=self.border,
            bd=0,
        )

    def surface(self, parent: tk.Misc) -> PanelSurface:
        return PanelSurface(parent, self.images)

    def header(self, parent: tk.Misc, text: str) -> tk.Label:
        return tk.Label(
            parent,
            text=text,
            font=(self.font, 12, "bold"),
            fg=self.text,
            bg=self.title,
            padx=14,
            pady=10,
            cursor="fleur",
        )

    def button(
        self,
        parent: tk.Misc,
        text: str,
        command: Callable[[], None],
        *,
        size: str = "regular",
        icon: tk.PhotoImage | None = None,
        align_left: bool = False,
    ) -> ImageButton:
        return ImageButton(
            parent,
            text,
            command,
            images=self.images,
            size=size,
            font=self.font,
            icon=icon,
            align_left=align_left,
        )
