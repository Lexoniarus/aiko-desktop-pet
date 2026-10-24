"""UI-drawn rounded passive surfaces; labels and controls remain native widgets."""

import tkinter as tk


class RoundedPanel:
    def __init__(
        self, parent: tk.Misc, *, fill: str, border: str, background: str,
        padding: int = 10,
    ) -> None:
        self.frame = tk.Frame(parent, bg=background, bd=0)
        self._canvas = tk.Canvas(
            self.frame, bg=background, bd=0, highlightthickness=0,
        )
        self._canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self._shape = self._canvas.create_polygon(
            0, 0, 0, 0, fill=fill, outline=border, smooth=True,
        )
        self.body = tk.Frame(self.frame, bg=fill, bd=0)
        self.body.pack(fill="both", expand=True, padx=padding, pady=padding)
        self.frame.bind("<Configure>", self._resize, add="+")

    def _resize(self, event: tk.Event) -> None:
        width, height, radius = event.width - 1, event.height - 1, 9
        self._canvas.coords(
            self._shape,
            radius, 1, width - radius, 1, width, 1, width, radius,
            width, height - radius, width, height, width - radius, height,
            radius, height, 1, height, 1, height - radius, 1, radius, 1, 1,
        )

    def set_fill(self, color: str) -> None:
        self._canvas.itemconfigure(self._shape, fill=color)
        self.body.configure(bg=color)
