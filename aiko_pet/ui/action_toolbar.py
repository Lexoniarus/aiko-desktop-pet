"""Movable Tkinter hover toolbar with the Kenney sci-fi skin."""

from __future__ import annotations

import sys
import tkinter as tk
from functools import partial
from tkinter import font as tkfont
from typing import Callable

from ..asset_paths import KENNEY_UI_DIR
from .hover_contracts import HoverActions, HoverAnchor, HoverSnapshot

class ActionToolbar:
    """Kenney sci-fi hover status; all six controls remain clickable."""

    NEEDS = (
        ("satiety", "Sättigung", "#f5bd7a"),
        ("mood", "Laune", "#95ddc1"),
        ("energy", "Energie", "#98c9f5"),
        ("social", "Sozial", "#dda9ef"),
        ("affection", "Zuwendung", "#f0a5be"),
        ("friendship", "Freundschaft", "#ffb9c2"),
    )
    BAR_WIDTH = 92
    BACKGROUND = "#D7DCE8"
    TEXT = "#414B5F"
    SUBTEXT = "#617189"

    def __init__(
        self, root: tk.Tk, *, snapshot: Callable[[], HoverSnapshot],
        anchor: Callable[[], HoverAnchor], actions: HoverActions,
        always_on_top: bool,
    ) -> None:
        self.root = root
        self._snapshot = snapshot
        self._anchor = anchor
        self._actions = actions
        self._current = snapshot()
        self.window = tk.Toplevel(root)
        self.window.withdraw()
        self.window.overrideredirect(True)
        self.window.configure(bg="#8E9CB1")
        # Assets are pre-rendered with Kenney CC0 tiles. The optional user-
        # supplied Kenney Mini font is used only if installed on Windows;
        # font files are not packaged with Aiko.
        try:
            available_fonts = set(tkfont.families(root=root))
        except tk.TclError:
            available_fonts = set()
        self.font_family = (
            "Kenney Mini" if "Kenney Mini" in available_fonts else "Segoe UI"
        )
        self._button_images = {
            key: tk.PhotoImage(file=str(KENNEY_UI_DIR / f"button_{key}.png"))
            for key in ("regular", "wide", "small")
        }
        self._header_image = tk.PhotoImage(
            file=str(KENNEY_UI_DIR / "toolbar_banner.png"),
        )
        self.window.wm_attributes("-topmost", always_on_top)
        if sys.platform == "win32":
            self.window.wm_attributes("-toolwindow", True)

        outer = tk.Frame(
            self.window, bg=self.BACKGROUND, highlightthickness=2,
            highlightbackground="#E9ECF5", bd=0,
        )
        outer.pack(padx=3, pady=3)
        self.today = tk.Label(
            outer, text="", image=self._header_image, compound="center",
            font=(self.font_family, 10, "bold"),
            fg="#FFFFFF", bg="#2998D4", anchor="w", padx=14, pady=0,
        )
        self.today.pack(side="top", fill="x")
        # Drag by the title area, not by the care buttons.
        self._drag_origin: tuple[int, int, int, int] | None = None
        self._dragging = False
        self.today.configure(cursor="fleur")
        self.today.bind("<ButtonPress-1>", self._drag_start)
        self.today.bind("<B1-Motion>", self._drag_motion)
        self.today.bind("<ButtonRelease-1>", self._drag_end)

        # Two compact rows keep all six values visible on smaller desktops.
        needs_frame = tk.Frame(outer, bg=self.BACKGROUND)
        needs_frame.pack(fill="x", padx=7, pady=(1, 5))
        self.needs: dict[str, tuple[tk.Canvas, int, tk.Label]] = {}
        for column in range(3):
            needs_frame.columnconfigure(column, weight=1, uniform="needs")
        for i, (key, title, color) in enumerate(self.NEEDS):
            cell = tk.Frame(needs_frame, bg=self.BACKGROUND)
            cell.grid(row=i // 3, column=i % 3, sticky="ew", padx=3, pady=2)
            label = tk.Label(
                cell, text="", font=(self.font_family, 9), width=20,
                fg=self.TEXT, bg=self.BACKGROUND, anchor="w",
            )
            label.pack(anchor="w")
            bar = tk.Canvas(
                cell, width=self.BAR_WIDTH, height=10, bd=0,
                highlightthickness=0, bg="#969FB2",
            )
            rect = bar.create_rectangle(0, 0, 1, 10, outline="", fill=color)
            bar.pack(fill="x", pady=(3, 3))
            self.needs[key] = (bar, rect, label)
            bar.bind(
                "<Configure>", partial(self._on_need_resize, key),
            )

        actions_frame = tk.Frame(outer, bg=self.BACKGROUND)
        actions_frame.pack(fill="x", padx=5)
        actions_row = tk.Frame(actions_frame, bg=self.BACKGROUND)
        actions_row.pack(fill="x")
        extra_row = tk.Frame(actions_frame, bg=self.BACKGROUND)
        extra_row.pack(fill="x")
        self.buttons: dict[str, tk.Button] = {}
        for action, title, parent in (
            ("feed", "Snack", actions_row),
            ("play", "Spielen", actions_row),
            ("pet", "Streicheln", actions_row),
            ("talk", "Reden", actions_row),
            ("energy_drink", "Energy Drink +10", extra_row),
            ("sleep", "Schlafen", extra_row),
        ):
            self.buttons[action] = self._button(
                parent, title, partial(actions.interact, action),
            )
        self._button(extra_row, "Status", actions.open_status)
        self.settings_button = self._button(extra_row, "⋯", self._open_settings)

        self.hardware = tk.Label(
            outer, text="", font=(self.font_family, 8),
            fg=self.SUBTEXT, bg=self.BACKGROUND, anchor="w", padx=10, pady=3,
        )
        self.hardware.pack(fill="x")
        self.workload = tk.Label(
            outer, text="", font=(self.font_family, 8),
            fg=self.TEXT, bg=self.BACKGROUND, anchor="w", padx=10, pady=3,
        )
        self.workload.pack(fill="x")
        self.visible = False
        self._last_placement: tuple[int, int, int, int] | None = None

    def _button(
        self, parent: tk.Widget, text: str, command: Callable[[], None],
    ) -> tk.Button:
        if text == "⋯":
            image = self._button_images["small"]
        elif len(text) > 13:
            image = self._button_images["wide"]
        else:
            image = self._button_images["regular"]
        button = tk.Button(
            parent, text=text, command=command,
            image=image, compound="center", font=(self.font_family, 9),
            fg="#344256", bg=self.BACKGROUND,
            activeforeground="#0B6DAA", activebackground=self.BACKGROUND,
            bd=0, relief="flat", padx=0, pady=0,
            highlightthickness=0, cursor="hand2",
        )
        button.pack(side="left", padx=2, pady=4)
        return button

    def _open_settings(self) -> None:
        # A normal Toplevel popover is predictable on Windows: native Tk menus
        # can fail to emit Unmap, leaving a permanent hover/menu lock.
        button = self.settings_button
        self._actions.open_settings(
            button.winfo_rootx() + button.winfo_width(),
            button.winfo_rooty(),
        )

    def _on_need_resize(self, key: str, event: tk.Event) -> None:
        """Resize the actual Tk progress canvas for a named need."""
        self._resize_need(key, event.width)

    def _resize_need(self, key: str, width: int | None = None) -> None:
        """Fill the *actual displayed* canvas, not its nominal requested width."""
        bar, rect, _label = self.needs[key]
        actual_width = width if width is not None else bar.winfo_width()
        if actual_width <= 1:
            actual_width = bar.winfo_reqwidth()
        amount = max(0.0, min(100.0, self._current.need_value(key)))
        bar.coords(rect, 0, 0, round(actual_width * amount / 100), 10)

    def refresh(self) -> None:
        """Refresh only the immutable presentation values."""
        view = self._snapshot()
        self._current = view
        changed = False
        for widget, value in (
            (self.buttons["sleep"], view.sleep_label),
            (self.buttons["feed"], view.feed_label),
            (self.today, view.header),
        ):
            if widget.cget("text") != value:
                widget.configure(text=value)
                changed = True
        for key, title, _color in self.NEEDS:
            amount = max(0, min(100, view.need_value(key)))
            _bar, _rect, label = self.needs[key]
            text = f"{title}  {amount:.0f}%"
            if key == "friendship":
                text = f"{title}  {amount:.0f}% · Lv {view.friendship_level}"
            if label.cget("text") != text:
                label.configure(text=text)
            self._resize_need(key)
        for widget, value in (
            (self.hardware, view.hardware_line),
            (self.workload, view.workload_line),
        ):
            if widget.cget("text") != value:
                widget.configure(text=value)
                changed = True
        if changed and self.visible:
            self.place()

    def contains_pointer(self, px: int, py: int) -> bool:
        if not self.visible:
            return False
        x, y = self.window.winfo_rootx(), self.window.winfo_rooty()
        return (x <= px < x + self.window.winfo_width()
                and y <= py < y + self.window.winfo_height())

    def contains_bridge(self, px: int, py: int) -> bool:
        """Tolerate the small horizontal or vertical gap to the sprite."""
        anchor = self._anchor()
        if not self.visible or anchor.pinned_x is not None:
            return False
        x, y = self.window.winfo_rootx(), self.window.winfo_rooty()
        width, height = self.window.winfo_width(), self.window.winfo_height()
        pet_x, pet_y = self.root.winfo_rootx(), self.root.winfo_rooty()
        pet_right = pet_x + anchor.width
        bar_right = x + width
        top = max(y, pet_y)
        bottom = min(y + height, pet_y + anchor.height)
        if top <= bottom:
            if bar_right <= pet_x:
                return bar_right - 3 <= px <= pet_x + 5 and top <= py <= bottom
            if pet_right <= x:
                return pet_right - 5 <= px <= x + 3 and top <= py <= bottom
        left = max(x, pet_x)
        right = min(bar_right, pet_right)
        if left <= right:
            return left <= px <= right and y + height - 3 <= py <= pet_y + 10
        return False

    def place(self) -> None:
        """Dragged panel stays put; default stays beside Aiko's head."""
        if self._dragging:
            return
        self.window.update_idletasks()
        width = self.window.winfo_reqwidth()
        height = self.window.winfo_reqheight()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        anchor = self._anchor()
        if anchor.pinned_x is not None and anchor.pinned_y is not None:
            x, y = anchor.pinned_x, anchor.pinned_y
        else:
            right_x = anchor.x + anchor.width + 10
            left_x = anchor.x - width - 10
            x = right_x if right_x + width <= screen_width else left_x
            y = anchor.y + max(0, (anchor.height - height) // 2)
        x = max(0, min(round(x), max(0, screen_width - width)))
        y = max(0, min(round(y), max(0, screen_height - height)))
        placement = x, y, width, height
        if placement != self._last_placement:
            self.window.geometry(f"+{x}+{y}")
            self._last_placement = placement

    def _drag_start(self, event: tk.Event) -> None:
        self._dragging = True
        self._drag_origin = (
            event.x_root, event.y_root,
            self.window.winfo_rootx(), self.window.winfo_rooty(),
        )

    def _drag_motion(self, event: tk.Event) -> None:
        if self._drag_origin is None:
            return
        px, py, x, y = self._drag_origin
        width, height = self.window.winfo_width(), self.window.winfo_height()
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        new_x = max(0, min(x + event.x_root - px, max(0, screen_w - width)))
        new_y = max(0, min(y + event.y_root - py, max(0, screen_h - height)))
        self.window.geometry(f"+{new_x}+{new_y}")
        self._last_placement = (new_x, new_y, width, height)
        self._actions.move_speech()

    def _drag_end(self, _event: tk.Event) -> None:
        if self._drag_origin is None:
            return
        position = self._last_placement
        x = position[0] if position is not None else self.window.winfo_rootx()
        y = position[1] if position is not None else self.window.winfo_rooty()
        self._drag_origin = None
        self._dragging = False
        self._actions.save_position(x, y)

    def reset_position(self) -> None:
        self._actions.save_position(None, None)
        self._last_placement = None
        if self.visible:
            self.place()

    def show(self) -> None:
        if self.visible:
            return
        self.refresh()
        self.place()
        self.window.deiconify()
        self.visible = True
        self._actions.move_speech()
        self._actions.restore_stack()

    def hide(self) -> None:
        if not self.visible:
            return
        self.visible = False
        self.window.withdraw()
        # Window managers may discard pending movements during withdrawal.
        self._last_placement = None
        self._actions.move_speech()

    def close(self) -> None:
        self.window.destroy()
