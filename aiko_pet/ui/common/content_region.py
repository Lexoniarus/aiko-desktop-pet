"""Unclipped content; all sizing belongs to the shared 4K UI transform."""

import tkinter as tk

from . import scaled_widgets as scaled
from .skin import AikoSkin


class ContentRegion:
    def __init__(
        self, parent: tk.Misc, skin: AikoSkin, *, background: str | None = None,
    ) -> None:
        self.frame = scaled.Frame(parent, bg=background or skin.background)
        self.body = self.frame
