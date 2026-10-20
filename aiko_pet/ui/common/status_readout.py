"""Passive illustrated readouts with continuously colored, clipped value fills."""

from __future__ import annotations

import tkinter as tk

from ...pet.content import GERMAN_TEXT
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
            bg=skin.background if icon is not None else skin.panel,
        )
        self._backdrop = tk.Canvas(
            self.frame, bg=self.frame.cget("bg"), bd=0, highlightthickness=0,
        )
        self._backdrop.place(x=0, y=0, relwidth=1, relheight=1)
        self._outline = self._backdrop.create_polygon(
            0, 0, 0, 0, fill=skin.panel,
            outline=skin.border if icon is not None else skin.panel, smooth=True,
        )
        self.frame.bind("<Configure>", self._resize, add="+")
        body = tk.Frame(self.frame, bg=skin.panel)
        body.pack(fill="both", expand=True, padx=9, pady=6)
        self._width, self._friendship = width, friendship
        if icon is not None:
            tk.Label(body, image=skin.images.icon(icon), bg=skin.panel).pack(
                side="left", padx=(0, 8)
            )
        content = tk.Frame(body, bg=skin.panel)
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

    def _resize(self, event: tk.Event) -> None:
        width, height, radius = event.width - 1, event.height - 1, 9
        self._backdrop.coords(
            self._outline,
            radius, 1, width - radius, 1, width, 1, width, radius,
            width, height - radius, width, height, width - radius, height,
            radius, height, 1, height, 1, height - radius, 1, radius, 1, 1,
        )

    def refresh(self, value: float, *, suffix: str = "") -> None:
        amount = max(0, min(100, value))
        text = GERMAN_TEXT.format(
            "vn.status_value", title=self._title, percent=f"{amount:.0f}", suffix=suffix
        )
        if self.label.cget("text") != text:
            self.label.configure(text=text)
        self.canvas.coords(self._fill, *fill_geometry(amount, self._width))
        self.canvas.itemconfigure(
            self._fill,
            fill=readout_color(amount, friendship=self._friendship),
            state="hidden" if amount == 0 else "normal",
        )
