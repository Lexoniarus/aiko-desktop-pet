"""Passive desktop code strip. It receives no unrevealed secret colors."""

import tkinter as tk
from collections.abc import Callable

from ...pet.content import GERMAN_TEXT
from ..common.mastermind_images import MastermindImages
from ..common.skin import AikoSkin
from ..common.window_geometry import WindowBounds
from ..view_models.game_models import HandAnchor
from ..view_models.mastermind_models import CodeView, place_code


class MastermindCodePresenter:
    def __init__(
        self,
        root: tk.Tk,
        *,
        images: MastermindImages,
        anchor: Callable[[], HandAnchor],
        topmost: Callable[[], bool],
        configure_window: Callable[[tk.Toplevel], None],
        restore_stack: Callable[[], object],
        occupied: Callable[[], tuple[WindowBounds, ...]],
    ) -> None:
        self._root, self._images, self._anchor = root, images, anchor
        self._topmost, self._configure = topmost, configure_window
        self._restore_stack, self._occupied = restore_stack, occupied
        self.window: tk.Toplevel | None = None
        self.canvas: tk.Canvas | None = None
        self._view = CodeView()

    @property
    def windows(self) -> tuple[tk.Toplevel, ...]:
        return (self.window,) if self.window is not None else ()

    def show(self, view: CodeView) -> None:
        self._view = view
        if self.window is None:
            self.window = tk.Toplevel(self._root)
            self.window.withdraw()
            self.window.overrideredirect(True)
            self.window.configure(bg=AikoSkin.border)
            self.canvas = tk.Canvas(
                self.window, bg=AikoSkin.panel, highlightthickness=0, bd=0
            )
            self.canvas.pack(padx=1, pady=1)
            self.canvas.bind("<Button-1>", lambda _event: "break")
            self.canvas.bind("<Button-3>", lambda _event: "break")
        self.move()
        self.set_topmost(self._topmost())
        self._configure(self.window)
        self.window.deiconify()
        self._restore_stack()

    def move(self) -> None:
        if self.window is None or self.canvas is None:
            return
        layout = place_code(self._anchor(), self._occupied())
        scale = layout.scale
        self.window.geometry(f"+{layout.x}+{layout.y}")
        canvas = self.canvas
        canvas.configure(width=208 * scale - 2, height=88 * scale - 2)
        canvas.delete("all")
        canvas.create_text(
            104 * scale,
            10 * scale,
            text=GERMAN_TEXT.format("mastermind.code"),
            fill=AikoSkin.text,
            font=("Segoe UI", 8 * scale),
        )
        for i, color in enumerate(self._view.slots):
            x, y = (32 + i * 48) * scale, 44 * scale
            if color == "white":
                canvas.create_oval(
                    x - 22 * scale,
                    y - 22 * scale,
                    x + 22 * scale,
                    y + 22 * scale,
                    fill="#B5C3D4",
                    outline=AikoSkin.accent,
                )
            canvas.create_image(
                x, y, image=self._images.get(color, scale), tags="piece"
            )
            if color is None:
                canvas.create_text(
                    x,
                    y,
                    text="?",
                    fill="white",
                    font=("Segoe UI", 14 * scale, "bold"),
                    tags="cover",
                )
            canvas.create_text(
                x,
                76 * scale,
                text=str(i + 1)
                if color is None
                else GERMAN_TEXT.format(f"mastermind.color.{color}"),
                fill=AikoSkin.text,
                font=("Segoe UI", 8 * scale),
            )

    def set_topmost(self, enabled: bool) -> None:
        if self.window is not None:
            self.window.wm_attributes("-topmost", enabled)

    def hide(self) -> None:
        if self.window is not None:
            self.window.destroy()
        self.window = self.canvas = None
        self._view = CodeView()
