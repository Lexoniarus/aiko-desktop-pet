"""Passive illustrated readouts with continuously colored, clipped value fills."""

from __future__ import annotations

import tkinter as tk

from .skin import AikoSkin


def readout_color(value: float, *, friendship: bool = False) -> str:
    if friendship:
        return "#94B5CF"
    value = max(0, min(100, value))
    anchors = (
        (0, (217, 136, 151)),
        (25, (229, 176, 128)),
        (50, (224, 205, 134)),
        (100, (142, 189, 156)),
    )
    for (low, a), (high, b) in zip(anchors, anchors[1:]):
        if value <= high:
            weight = (value - low) / (high - low)
            return "#" + "".join(
                f"{round(x + (y - x) * weight):02X}" for x, y in zip(a, b)
            )
    raise AssertionError("Clamped value has no color interval")


def fill_geometry(value: float, width: int) -> tuple[float, ...]:
    right = 2 + (width - 4) * max(0, min(100, value)) / 100
    radius = min(4, (right - 2) / 2)
    return (
        2 + radius,
        2,
        right - radius,
        2,
        right,
        2,
        right,
        6,
        right,
        10,
        right - radius,
        10,
        2 + radius,
        10,
        2,
        10,
        2,
        6,
        2,
        2,
    )


class StatusReadout:
    def __init__(
        self,
        parent: tk.Misc,
        skin: AikoSkin,
        *,
        title: str,
        icon: str | None = None,
        width: int = 280,
        friendship: bool = False,
    ) -> None:
        self.frame = tk.Frame(
            parent,
            bg=skin.panel,
            padx=8,
            pady=5,
            highlightthickness=1,
            highlightbackground=skin.border,
        )
        self._width, self._friendship = width, friendship
        if icon is not None:
            tk.Label(self.frame, image=skin.images.icon(icon), bg=skin.panel).pack(
                side="left", padx=(0, 8)
            )
        content = tk.Frame(self.frame, bg=skin.panel)
        content.pack(fill="both", expand=True)
        self.label = tk.Label(
            content,
            text=title,
            bg=skin.panel,
            fg=skin.text,
            font=(skin.font, 9),
            anchor="w",
        )
        self.label.pack(fill="x")
        self.canvas = tk.Canvas(
            content, width=width, height=12, bg=skin.panel, bd=0, highlightthickness=0
        )
        self.canvas.pack(anchor="w", pady=(4, 0))
        self.canvas.create_image(
            0, 0, image=skin.images.surface(f"status_track.{width}"), anchor="nw"
        )
        self._fill = self.canvas.create_polygon(
            *fill_geometry(0, width), smooth=True, outline=""
        )
        self.canvas.create_image(
            0,
            0,
            image=skin.images.surface(f"status_frame_overlay.{width}"),
            anchor="nw",
        )
        self._title = title

    def refresh(self, value: float, *, suffix: str = "") -> None:
        amount = max(0, min(100, value))
        text = f"{self._title}   {amount:.0f} / 100{suffix}"
        if self.label.cget("text") != text:
            self.label.configure(text=text)
        self.canvas.coords(self._fill, *fill_geometry(amount, self._width))
        self.canvas.itemconfigure(
            self._fill,
            fill=readout_color(amount, friendship=self._friendship),
            state="hidden" if amount == 0 else "normal",
        )
