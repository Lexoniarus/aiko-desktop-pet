"""Kenney-styled player panel: input, private hand, and session scoreboard."""

from __future__ import annotations

import sys
import tkinter as tk
from collections.abc import Callable
from functools import partial

from ..asset_paths import GAME_HANDS_DIR
from ..games.rock_paper_scissors import Move, Score
from ..presentation.rock_paper_scissors_sequence import RockPaperScissorsSequence
from .skin import AikoSkin
from .window_drag import WindowDrag

_BG = "#D7DCE8"
_TEXT = "#414B5F"
_MUTED = "#617189"
_PANEL = "#E9ECF5"
_ACCENT = "#2998D4"
_MOVES: tuple[tuple[Move, str], ...] = (
    (Move.ROCK, "Stein"),
    (Move.PAPER, "Papier"),
    (Move.SCISSORS, "Schere"),
)
_MOVE_NAMES = dict(_MOVES)


class RockPaperScissorsWindow:
    """Permanent player-only panel sharing Aiko's existing hover styling."""

    def __init__(
        self, root: tk.Tk, *, on_closed: Callable[[], None],
        speak: Callable[[str, int], None],
        emote: Callable[[str, int], None],
        hand: Callable[[Move, int], None],
        animate: Callable[[str], None], always_on_top: bool,
        skin: AikoSkin | None = None,
    ) -> None:
        self._on_closed = on_closed
        self._closed = False
        self.skin = skin if skin is not None else AikoSkin(root)
        self.window = tk.Toplevel(root)
        self.window.withdraw()
        self.window.overrideredirect(True)
        self.window.configure(bg=self.skin.border)
        self.window.wm_attributes("-topmost", always_on_top)
        if sys.platform == "win32":
            self.window.wm_attributes("-toolwindow", True)
        self.window.bind("<Escape>", lambda _event: self.close())

        title_font = self.skin.font
        self.hand_images = {
            move: tk.PhotoImage(master=root, file=str(GAME_HANDS_DIR / f"{move.value}.png"))
            for move, _label in _MOVES
        }

        outer = self.skin.frame(self.window)
        # Keep the layout filling the fixed shell during widget updates.
        outer.pack(fill="both", expand=True, padx=3, pady=3)
        header = self.skin.header(outer, "AIKO · SPIELEN")
        header.pack(fill="x")
        self._drag = WindowDrag(self.window, header)

        tk.Label(
            outer, text="Wähle deine Hand", bg=_BG, fg=_TEXT,
            font=(title_font, 10, "bold"),
        ).pack(padx=12, pady=(12, 3))
        choices = tk.Frame(outer, bg=_BG)
        choices.pack(padx=12, pady=(2, 10))
        self.buttons: dict[Move, tk.Button] = {}
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

        self.result_panel = tk.Frame(
            outer, bg=_PANEL, highlightthickness=2,
            highlightbackground="#A6B9CD",
        )
        self.result_panel.pack(fill="x", padx=12, pady=(0, 10))
        self.result_title = tk.Label(
            self.result_panel, text="Deine Hand",
            bg=_PANEL, fg=_TEXT, font=(title_font, 10, "bold"),
        )
        self.result_title.pack(pady=(8, 2))
        # Fixed pixel canvas: changing '?' to an image cannot shrink it.
        self.player_hand = tk.Canvas(
            self.result_panel, width=120, height=96, bg=_PANEL,
            bd=0, highlightthickness=0, relief="flat",
        )
        self.player_hand.pack(padx=8)
        self._hand_image_item = self.player_hand.create_image(
            60, 48, anchor="center", state="hidden",
        )
        self._hand_question_item = self.player_hand.create_text(
            60, 48, text="?", fill=_MUTED, font=(title_font, 22, "bold"),
        )
        self._last_revealed: Move | None = None
        self.player_result_label = tk.Label(
            self.result_panel, text="Noch keine Runde gespielt",
            bg=_PANEL, fg=_MUTED, font=(title_font, 9),
        )
        self.player_result_label.pack(pady=(2, 9))

        score = tk.Frame(outer, bg=_BG)
        score.pack(fill="x", padx=12, pady=(0, 8))
        self.score_labels: dict[str, tk.Label] = {}
        for column, (key, title) in enumerate((
            ("games", "Runden"),
            ("wins", "Deine Siege"),
            ("losses", "Aikos Siege"),
            ("draws", "Remis"),
        )):
            cell = tk.Frame(score, bg=_PANEL, bd=0)
            cell.grid(row=0, column=column, padx=2, sticky="nsew")
            score.grid_columnconfigure(column, weight=1)
            tk.Label(
                cell, text=title, bg=_PANEL, fg=_MUTED,
                font=(title_font, 8),
            ).pack(padx=4, pady=(5, 1))
            count = tk.Label(
                cell, text="0", bg=_PANEL, fg=_TEXT,
                font=(title_font, 14, "bold"),
            )
            count.pack(padx=6, pady=(1, 5))
            self.score_labels[key] = count

        self.close_button = self.skin.button(outer, "Schließen", self.close)
        self.close_button.pack(anchor="e", padx=13, pady=(0, 9))
        self._sequence = RockPaperScissorsSequence(
            schedule=self.window.after, cancel=self.window.after_cancel,
            say=speak, show_emote=emote,
            show_aiko_hand=hand,
            reveal_player=self.reveal_player,
            animate=animate, set_busy=self._set_busy,
        )
        self.window.update_idletasks()
        width = self.window.winfo_reqwidth()
        height = self.window.winfo_reqheight()
        x = max(0, min(
            root.winfo_rootx() + root.winfo_width() + 12,
            root.winfo_screenwidth() - width,
        ))
        y = max(0, min(
            root.winfo_rooty() - height // 2,
            root.winfo_screenheight() - height - 45,
        ))
        # Fix both dimensions; borderless Tk must not reflow on reveal.
        self.window.geometry(f"{width}x{height}+{x}+{y}")
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

    def _clear_player_result(self) -> None:
        self.result_panel.configure(highlightbackground="#A6B9CD")
        if self._last_revealed is None:
            self.player_result_label.configure(text="Warten auf Aiko ...")
        else:
            # The previous full hand remains visible during a new countdown.
            self.player_result_label.configure(
                text=f"Letzte Hand: {_MOVE_NAMES[self._last_revealed]}",
            )

    def reveal_player(self, move: Move, score: Score) -> None:
        """Keep the complete hand PNG visible at its original pixel size."""
        self._last_revealed = move
        self.player_hand.itemconfigure(
            self._hand_image_item, image=self.hand_images[move],
            state="normal",
        )
        self.player_hand.itemconfigure(
            self._hand_question_item, state="hidden",
        )
        self.result_panel.configure(highlightbackground=_ACCENT)
        self.player_result_label.configure(text=f"Du: {_MOVE_NAMES[move]}")
        for key, label in self.score_labels.items():
            label.configure(text=str(getattr(score, key)))

    def choose(self, move: Move) -> None:
        if not self._closed and not self._sequence.busy:
            self._clear_player_result()
            self._sequence.choose(move)

    def focus(self) -> None:
        self.window.deiconify()
        self.window.lift()
        self.window.focus_set()

    def set_topmost(self, enabled: bool) -> None:
        self.window.wm_attributes("-topmost", enabled)

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._sequence.close()
        self._drag.close()
        self.window.destroy()
        self._on_closed()
