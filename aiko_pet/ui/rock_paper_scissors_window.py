"""Kenney-styled minigame input panel; all dialogue stays with Aiko."""

from __future__ import annotations

import sys
import tkinter as tk
from collections.abc import Callable
from functools import partial
from tkinter import font as tkfont

from ..asset_paths import GAME_HANDS_DIR, KENNEY_UI_DIR
from ..games.rock_paper_scissors import Move, Score
from ..presentation.rock_paper_scissors_sequence import RockPaperScissorsSequence

_BG = "#D7DCE8"
_TEXT = "#414B5F"
_MOVES: tuple[tuple[Move, str], ...] = (
    (Move.ROCK, "Stein"),
    (Move.PAPER, "Papier"),
    (Move.SCISSORS, "Schere"),
)


class RockPaperScissorsWindow:
    """A permanent input-only panel matching the existing hover toolbar."""

    def __init__(
        self, root: tk.Tk, *, on_closed: Callable[[], None],
        speak: Callable[[str, int], None],
        emote: Callable[[str, int], None],
        hands: Callable[[Move, Move, int], None],
        animate: Callable[[str], None], always_on_top: bool,
    ) -> None:
        self._on_closed = on_closed
        self._closed = False
        self._drag_origin: tuple[int, int, int, int] | None = None
        self.window = tk.Toplevel(root)
        self.window.withdraw()
        self.window.overrideredirect(True)
        self.window.configure(bg="#8E9CB1")
        self.window.wm_attributes("-topmost", always_on_top)
        if sys.platform == "win32":
            self.window.wm_attributes("-toolwindow", True)
        self.window.bind("<Escape>", lambda _event: self.close())

        fonts = set(tkfont.families(root=root))
        title_font = "Kenney Mini" if "Kenney Mini" in fonts else "Segoe UI"
        self._banner = tk.PhotoImage(
            file=str(KENNEY_UI_DIR / "toolbar_banner.png"),
        )
        self._close_image = tk.PhotoImage(
            file=str(KENNEY_UI_DIR / "button_regular.png"),
        )
        outer = tk.Frame(
            self.window, bg=_BG, highlightthickness=2,
            highlightbackground="#E9ECF5", bd=0,
        )
        outer.pack(padx=3, pady=3)
        header = tk.Label(
            outer, text="AIKO · SPIELEN", image=self._banner,
            compound="center", font=(title_font, 10, "bold"),
            fg="#FFFFFF", bg="#2998D4", padx=14, cursor="fleur",
        )
        header.pack(fill="x")
        header.bind("<ButtonPress-1>", self._drag_start)
        header.bind("<B1-Motion>", self._drag_motion)
        header.bind("<ButtonRelease-1>", self._drag_end)

        tk.Label(
            outer, text="Deine Wahl", bg=_BG, fg=_TEXT,
            font=(title_font, 10, "bold"),
        ).pack(padx=12, pady=(13, 3))

        choices = tk.Frame(outer, bg=_BG)
        choices.pack(padx=12, pady=(2, 10))
        self.buttons: dict[Move, tk.Button] = {}
        self.hand_images = {
            move: tk.PhotoImage(file=str(GAME_HANDS_DIR / f"{move.value}.png"))
            for move, _label in _MOVES
        }
        for move, label in _MOVES:
            button = tk.Button(
                choices, text=label, image=self.hand_images[move],
                compound="top", font=(title_font, 9),
                bg=_BG, fg=_TEXT, activeforeground="#0B6DAA",
                activebackground="#BED5E5", bd=1, relief="flat",
                highlightthickness=1, highlightbackground="#B3C2D8",
                padx=8, pady=5, cursor="hand2",
                command=partial(self.choose, move),
            )
            button.pack(side="left", padx=3)
            self.buttons[move] = button

        self.close_button = tk.Button(
            outer, text="Schließen", image=self._close_image,
            compound="center", font=(title_font, 9),
            bg=_BG, fg=_TEXT, activeforeground="#0B6DAA",
            activebackground=_BG, bd=0, relief="flat",
            highlightthickness=0, cursor="hand2", command=self.close,
        )
        self.close_button.pack(anchor="e", padx=13, pady=(0, 9))

        self._sequence = RockPaperScissorsSequence(
            schedule=self.window.after,
            cancel=self.window.after_cancel,
            say=speak, show_emote=emote,
            show_hands=hands, animate=animate,
            set_busy=self._set_busy,
        )
        self.window.update_idletasks()
        width, height = (
            self.window.winfo_reqwidth(), self.window.winfo_reqheight()
        )
        x = max(0, min(
            root.winfo_rootx() + root.winfo_width() + 12,
            root.winfo_screenwidth() - width,
        ))
        y = max(0, min(
            root.winfo_rooty() - height // 2,
            root.winfo_screenheight() - height - 45,
        ))
        self.window.geometry(f"+{x}+{y}")
        self.window.deiconify()

    @property
    def score(self) -> Score:
        return self._sequence.score

    def greet(self) -> None:
        self._sequence.greet()

    def _set_busy(self, busy: bool) -> None:
        for button in self.buttons.values():
            if busy:
                button.configure(state="disabled")
            else:
                button.configure(state="normal")

    def choose(self, move: Move) -> None:
        if not self._closed:
            self._sequence.choose(move)

    def focus(self) -> None:
        self.window.deiconify()
        self.window.lift()
        self.window.focus_set()

    def set_topmost(self, enabled: bool) -> None:
        self.window.wm_attributes("-topmost", enabled)

    def _drag_start(self, event: tk.Event) -> None:
        self._drag_origin = (
            event.x_root, event.y_root,
            self.window.winfo_rootx(), self.window.winfo_rooty(),
        )

    def _drag_motion(self, event: tk.Event) -> None:
        origin = self._drag_origin
        if origin is None:
            return
        x = origin[2] + event.x_root - origin[0]
        y = origin[3] + event.y_root - origin[1]
        x = max(0, min(
            x, self.window.winfo_screenwidth() - self.window.winfo_width(),
        ))
        y = max(0, min(
            y, self.window.winfo_screenheight() - self.window.winfo_height(),
        ))
        self.window.geometry(f"+{x}+{y}")

    def _drag_end(self, _event: tk.Event) -> None:
        self._drag_origin = None

    def close(self) -> None:
        """Restore normal Aiko behavior even if a countdown is in progress."""
        if self._closed:
            return
        self._closed = True
        self._sequence.close()
        self.window.destroy()
        self._on_closed()
