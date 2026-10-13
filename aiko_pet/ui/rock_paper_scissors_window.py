"""Independent Tkinter minigame window; the hover bar may hide normally."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from functools import partial

from ..games.rock_paper_scissors import (
    Move, Outcome, RockPaperScissors, Round, Score,
)

_BG = "#202733"
_PANEL = "#303B4A"
_TEXT = "#E9EEF6"
_ACCENT = "#B0E7FB"
_MOVES: tuple[tuple[Move, str, str], ...] = (
    (Move.ROCK, "✊", "Stein"),
    (Move.PAPER, "✋", "Papier"),
    (Move.SCISSORS, "✌", "Schere"),
)
_LABELS = {move: (emoji, name) for move, emoji, name in _MOVES}
_REMARKS = {
    Outcome.WIN: "Aiko: Hmpf ... diesmal hast du gewonnen!",
    Outcome.LOSS: "Aiko: Hehe! Der Punkt geht an mich!",
    Outcome.DRAW: "Aiko: Unentschieden! Noch eine Runde?",
}


class RockPaperScissorsWindow:
    """Window and countdown lifecycle, separate from the game's pure rules."""

    COUNT_INTERVAL_MS = 750

    def __init__(
        self, root: tk.Tk, *, on_closed: Callable[[], None],
        always_on_top: bool,
    ) -> None:
        self._on_closed = on_closed
        self._game = RockPaperScissors()
        self._closed = False
        self._timer: str | None = None
        self._count = 0
        self.window = tk.Toplevel(root)
        self.window.title("Aiko · Schere, Stein, Papier")
        self.window.resizable(False, False)
        self.window.configure(bg=_BG)
        self.window.attributes("-topmost", always_on_top)
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        self.window.bind("<Escape>", lambda _event: self.close())

        outer = tk.Frame(self.window, bg=_BG)
        outer.pack(fill="both", expand=True, padx=18, pady=16)
        tk.Label(
            outer, text="SPIELEN MIT AIKO", bg=_BG, fg=_ACCENT,
            font=("Segoe UI", 16, "bold"),
        ).pack(anchor="w")
        tk.Label(
            outer, text="Schere · Stein · Papier", bg=_BG, fg=_TEXT,
            font=("Segoe UI", 12),
        ).pack(anchor="w", pady=(3, 14))

        self.score_label = tk.Label(
            outer, text="", bg=_PANEL, fg=_TEXT,
            font=("Segoe UI", 10), pady=8,
        )
        self.score_label.pack(fill="x")
        self.count_label = tk.Label(
            outer, text="Bereit?", bg=_BG, fg=_ACCENT,
            font=("Segoe UI", 24, "bold"), pady=7,
        )
        self.count_label.pack()
        self.reveal_label = tk.Label(
            outer, text="Du wählst zuerst. Aiko deckt bei Drei auf.",
            bg=_BG, fg=_TEXT, font=("Segoe UI", 10), wraplength=350,
            justify="center",
        )
        self.reveal_label.pack(pady=(0, 10))

        choices = tk.Frame(outer, bg=_BG)
        choices.pack(fill="x", pady=(5, 8))
        self.buttons: dict[Move, tk.Button] = {}
        for move, emoji, name in _MOVES:
            button = tk.Button(
                choices, text=f"{emoji}  {name}",
                command=partial(self.choose, move),
                bg=_PANEL, fg=_TEXT, activeforeground=_ACCENT,
                activebackground="#40526A", font=("Segoe UI Emoji", 12),
                relief="flat", padx=8, pady=11, cursor="hand2",
                width=9,
            )
            button.pack(side="left", expand=True, padx=3)
            self.buttons[move] = button

        self.remark_label = tk.Label(
            outer, text="Aiko: Na los, trau dich!",
            bg=_BG, fg=_ACCENT, font=("Segoe UI", 10),
            wraplength=350, justify="center", pady=8,
        )
        self.remark_label.pack(fill="x")
        tk.Button(
            outer, text="Spiel verlassen", command=self.close,
            bg=_PANEL, fg=_TEXT, activebackground="#40526A",
            activeforeground=_TEXT, relief="flat", padx=12, pady=7,
        ).pack(anchor="e", pady=(6, 0))

        self._refresh_score()
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

    @property
    def score(self) -> Score:
        return self._game.score

    def focus(self) -> None:
        """Clicking Spielen again reuses the same session and counters."""
        self.window.deiconify()
        self.window.lift()
        self.window.focus_set()

    def set_topmost(self, enabled: bool) -> None:
        self.window.wm_attributes("-topmost", enabled)

    def _refresh_score(self) -> None:
        score = self._game.score
        self.score_label.configure(
            text=(
                f"Spiele: {score.games}    Siege: {score.wins}    "
                f"Niederlagen: {score.losses}    Remis: {score.draws}"
            ),
        )

    def choose(self, move: Move) -> None:
        """Seal both moves now; do not reveal Aiko's until 1, 2, 3."""
        if self._closed or self._game.pending:
            return
        self._game.begin(move)
        for button in self.buttons.values():
            button.configure(state="disabled")
        self._count = 1
        self.count_label.configure(text="1")
        self.reveal_label.configure(text="Aiko überlegt noch ...")
        self.remark_label.configure(text="Aiko: Eins ...")
        self._timer = self.window.after(
            self.COUNT_INTERVAL_MS, self._advance_countdown,
        )

    def _advance_countdown(self) -> None:
        self._timer = None
        if self._closed:
            return
        self._count += 1
        if self._count <= 3:
            self.count_label.configure(text=str(self._count))
            words = {2: "Zwei ...", 3: "Drei!"}
            self.remark_label.configure(
                text="Aiko: " + words[self._count],
            )
            self._timer = self.window.after(
                self.COUNT_INTERVAL_MS, self._advance_countdown,
            )
            return
        result = self._game.reveal()
        self._show_result(result)

    def _show_result(self, result: Round) -> None:
        person_emoji, person_label = _LABELS[result.player]
        aiko_emoji, aiko_label = _LABELS[result.aiko]
        self.count_label.configure(text="Aufgedeckt!")
        self.reveal_label.configure(
            text=(
                f"Du: {person_emoji} {person_label}   —   "
                f"Aiko: {aiko_emoji} {aiko_label}"
            ),
        )
        self.remark_label.configure(text=_REMARKS[result.outcome])
        self._refresh_score()
        for button in self.buttons.values():
            button.configure(state="normal")

    def close(self) -> None:
        """Cancel every pending Tk callback before destroying this window."""
        if self._closed:
            return
        self._closed = True
        if self._timer is not None:
            self.window.after_cancel(self._timer)
            self._timer = None
        self._game.cancel()
        self.window.destroy()
        self._on_closed()
