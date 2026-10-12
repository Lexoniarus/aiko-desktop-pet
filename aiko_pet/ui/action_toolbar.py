"""Movable Tkinter hover toolbar with the Kenney sci-fi skin."""

from __future__ import annotations

import sys
import time
import tkinter as tk
from tkinter import font as tkfont
from typing import TYPE_CHECKING, Callable

from ..asset_paths import KENNEY_UI_DIR
from ..system_activity import percent_label, workload_description

if TYPE_CHECKING:
    from ..gui import DesktopPet

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

    def __init__(self, pet: DesktopPet) -> None:
        self.pet = pet
        self.window = tk.Toplevel(pet.root)
        self.window.withdraw()
        self.window.overrideredirect(True)
        self.window.configure(bg="#8E9CB1")
        # Assets are pre-rendered with Kenney CC0 tiles. The optional user-
        # supplied Kenney Mini font is used only if installed on Windows;
        # font files are not packaged with Aiko.
        try:
            available_fonts = set(tkfont.families(root=pet.root))
        except tk.TclError:
            available_fonts = set()
        self.font_family = (
            "Kenney Mini" if "Kenney Mini" in available_fonts else "Segoe UI"
        )
        self._button_images = {
            key: tk.PhotoImage(file=str(KENNEY_UI_DIR / f"button_{key}.png"))
            for key in ("regular", "wide", "small")
        }
        self._header_image = tk.PhotoImage(file=str(KENNEY_UI_DIR / "toolbar_banner.png"))
        self.window.wm_attributes("-topmost", pet.settings.always_on_top)
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
                "<Configure>",
                lambda event, need=key: self._resize_need(need, event.width),
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
                parent, title, lambda selected=action: self.pet.interact(selected),
            )
        self._button(extra_row, "Status", pet.open_status)
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
        self.pet.toggle_settings_menu(
            button.winfo_rootx() + button.winfo_width(),
            button.winfo_rooty(),
        )

    def _resize_need(self, key: str, width: int | None = None) -> None:
        """Fill the *actual displayed* canvas, not its nominal requested width."""
        bar, rect, _label = self.needs[key]
        actual_width = width if width is not None else bar.winfo_width()
        if actual_width <= 1:
            actual_width = bar.winfo_reqwidth()
        amount = max(0.0, min(100.0, getattr(self.pet.state, key)))
        bar.coords(rect, 0, 0, round(actual_width * amount / 100), 10)

    def refresh(self) -> None:
        desired = "Wecken" if self.pet.state.sleeping else "Schlafen"
        feed_label = self.pet.state.feed_label(self.pet.context)
        changed = False
        for widget, value in (
            (self.buttons["sleep"], desired),
            (self.buttons["feed"], feed_label),
            (self.today, f"{self.pet.context.label}   ↔ Ziehen"),
        ):
            if widget.cget("text") != value:
                widget.configure(text=value)
                changed = True
        for key, title, _color in self.NEEDS:
            amount = max(0, min(100, getattr(self.pet.state, key)))
            _bar, _rect, label = self.needs[key]
            text = f"{title}  {amount:.0f}%"
            if key == "friendship":
                text = f"{title}  {amount:.0f}% · Lv {self.pet.state.friendship_level}"
            if label.cget("text") != text:
                label.configure(text=text)
            self._resize_need(key)
        reading = self.pet.activity_monitor.latest()
        if self.pet.settings.observe_computer:
            hardware_line = (
                f"MEIN RECHNER   CPU {percent_label(reading.cpu)}"
                f"   ·   GPU {percent_label(reading.gpu)}"
                f"   ·   RAM {percent_label(reading.ram)}"
            )
            work_line = workload_description(reading)
        else:
            hardware_line = "Rechnerbeobachtung deaktiviert"
            work_line = ""
        for widget, value in ((self.hardware, hardware_line),
                              (self.workload, work_line)):
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
        if not self.visible or self.pet.settings.toolbar_x is not None:
            return False
        x, y = self.window.winfo_rootx(), self.window.winfo_rooty()
        width, height = self.window.winfo_width(), self.window.winfo_height()
        pet_x, pet_y = self.pet.root.winfo_rootx(), self.pet.root.winfo_rooty()
        pet_right = pet_x + self.pet.width
        bar_right = x + width
        top = max(y, pet_y)
        bottom = min(y + height, pet_y + self.pet.height)
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
        screen_width = self.pet.root.winfo_screenwidth()
        screen_height = self.pet.root.winfo_screenheight()
        if self.pet.settings.toolbar_x is not None and self.pet.settings.toolbar_y is not None:
            x, y = self.pet.settings.toolbar_x, self.pet.settings.toolbar_y
        else:
            pet_x = self.pet.settings.x or 0
            pet_y = self.pet.settings.y or 0
            right_x = pet_x + self.pet.width + 10
            left_x = pet_x - width - 10
            x = right_x if right_x + width <= screen_width else left_x
            y = pet_y + max(0, (self.pet.height - height) // 2)
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
        screen_w = self.pet.root.winfo_screenwidth()
        screen_h = self.pet.root.winfo_screenheight()
        new_x = max(0, min(x + event.x_root - px, max(0, screen_w - width)))
        new_y = max(0, min(y + event.y_root - py, max(0, screen_h - height)))
        self.window.geometry(f"+{new_x}+{new_y}")
        self._last_placement = (new_x, new_y, width, height)
        self.pet._move_bubble()

    def _drag_end(self, _event: tk.Event) -> None:
        if self._drag_origin is None:
            return
        # The window manager may not have acknowledged our last geometry
        # request before ButtonRelease; save the requested, clamped position.
        position = self._last_placement
        self.pet.settings.toolbar_x = position[0] if position is not None else self.window.winfo_rootx()
        self.pet.settings.toolbar_y = position[1] if position is not None else self.window.winfo_rooty()
        self._drag_origin = None
        self._dragging = False
        self.pet._last_hover = time.monotonic()
        self.pet._save()

    def reset_position(self) -> None:
        self.pet.settings.toolbar_x = None
        self.pet.settings.toolbar_y = None
        self._last_placement = None
        if self.visible:
            self.place()
        self.pet._save()

    def show(self) -> None:
        if self.visible:
            return
        self.refresh()
        self.place()
        self.window.deiconify()
        self.visible = True
        self.pet._move_bubble()
        self.pet._overlay_stack.restore()

    def hide(self) -> None:
        if not self.visible:
            return
        self.visible = False
        self.window.withdraw()
        # Window managers may discard pending movements during withdrawal.
        self._last_placement = None
        self.pet._move_bubble()

    def close(self) -> None:
        self.window.destroy()
