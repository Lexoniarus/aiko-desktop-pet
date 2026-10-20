"""The shared board is player UI; Aiko's reactions stay with her figure."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from functools import partial

from ...games.contracts import GameId, GameRoundEvent, SessionSummary
from ...games.tic_tac_toe import Board
from ...pet.content import GERMAN_TEXT
from ..common.scroll_region import ScrollRegion
from ..common.skin import AikoSkin
from ..common.window_geometry import BoundsAt
from .game_panel import GamePanel
from .tic_tac_toe_sequence import TicTacToeSequence


class TicTacToeWindow:
    def __init__(
        self, root: tk.Tk, *, on_closed: Callable[[SessionSummary], None],
        speak: Callable[[str, int], None], animate: Callable[[str], None],
        always_on_top: bool, skin: AikoSkin,
        dialogue: Callable[[str], str] | None = None,
        round_event: Callable[[GameRoundEvent], None] = lambda _event: None,
        bounds_at: BoundsAt | None = None,
    ) -> None:
        self._closed = False
        self._on_closed = on_closed
        self.skin = skin
        self._panel = GamePanel(
            root, GERMAN_TEXT.format("game.name.tic_tac_toe"), close=self.close,
            next_round=self.next_round, skin=skin, always_on_top=always_on_top,
            game_id=GameId.TIC_TAC_TOE, bounds_at=bounds_at,
        )
        self.window = self._panel.window
        try:
            self._tokens = {
                mark: skin.images.icon(f"play_ttt_{mark.lower()}", 64)
                for mark in ("X", "O")
            }
            self._blank = tk.PhotoImage(master=root, width=64, height=64)
            legend = tk.Frame(self._panel.body, bg=skin.background)
            legend.pack(anchor="w", pady=(0, 10))
            for mark, key in (("X", "player"), ("O", "aiko")):
                tk.Label(
                    legend, image=skin.images.icon(f"play_ttt_{mark.lower()}", 24),
                    text=GERMAN_TEXT.format(f"game.score.{key}"), compound="left",
                    bg=skin.background, fg=skin.muted, font=(skin.font, 9),
                ).pack(side="left", padx=(0, 14))
            self._board_scroll = ScrollRegion(
                self._panel.body, skin, width=min(294, self._panel.content_width),
                height=294, horizontal=True, autohide=True,
            )
            self._board_scroll.frame.pack()
            self._board = self._panel.passive(self._board_scroll.body, padding=9)
            self._board.frame.pack()
            self.buttons: list[tk.Button] = []
            self._token_labels: list[tk.Label] = []
            for i in range(9):
                button = tk.Button(
                    self._board.body, text=" ", image=self._blank, compound="none",
                    width=84, height=84, padx=0, pady=0, bd=0,
                    highlightthickness=1, highlightbackground=skin.border,
                    highlightcolor=skin.accent, relief="flat", cursor="hand2",
                    font=(skin.font, 18, "bold"), bg="#FFFCFD", fg=skin.text,
                    activebackground="#F9E9F1", activeforeground=skin.text,
                    disabledforeground=skin.text, command=partial(self.choose, i),
                )
                button.grid(row=i // 3, column=i % 3, padx=3, pady=3)
                self.buttons.append(button)
                # Native disabled buttons stipple images on Windows. An inert
                # label keeps occupied marks crisp; the button still owns input.
                token = tk.Label(button, bd=0, padx=0, pady=0, cursor="arrow")
                self._token_labels.append(token)
            self._board_scroll.adopt()
            self._sequence = TicTacToeSequence(
                schedule=self.window.after, cancel=self.window.after_cancel,
                present=self._present, say=speak, animate=animate, dialogue=dialogue,
                round_event=round_event,
            )
            self._present(self._sequence.game.board, self._sequence.game.score)
            self._panel.show(root)
        except Exception:
            # Admission failed; the host still owns mode/completion cleanup.
            self._closed = True
            self._panel.destroy()
            raise

    def greet(self) -> None:
        self._sequence.greet()

    def _present(self, board: Board, score: SessionSummary) -> None:
        for i, button in enumerate(self.buttons):
            button.configure(
                text=board.cells[i] or " ",
                image=self._tokens[board.cells[i]] if board.cells[i] else self._blank,
                state="normal" if board.turn == "X" and board.winner is None
                and not board.cells[i] else "disabled",
                bg=(
                    "#E1EDF7" if board.winner == "X" else "#F4DFE9"
                ) if i in board.winning_line else "#FFFCFD",
                highlightbackground=(
                    self.skin.accent if board.winner == "X" else "#BC8DA6"
                ) if i in board.winning_line else self.skin.border,
            )
            token = self._token_labels[i]
            if board.cells[i]:
                token.configure(
                    image=self._tokens[board.cells[i]], bg=button.cget("bg"),
                )
                token.place(relx=0.5, rely=0.5, anchor="center")
            else:
                token.place_forget()
        if board.winner is None:
            key = "game.player_turn" if board.turn == "X" else "game.aiko_turn"
        else:
            key = {"X": "game.player_win", "O": "game.aiko_win", "": "game.draw"}[
                board.winner
            ]
        self._panel.update(
            score, status=GERMAN_TEXT.format(key), finished=board.winner is not None,
        )

    def choose(self, cell: int) -> None:
        if not self._closed:
            self._sequence.choose(cell)

    def next_round(self) -> None:
        self._sequence.next_round()

    def set_topmost(self, enabled: bool) -> None:
        self.window.wm_attributes("-topmost", enabled)

    def close(self) -> None:
        if not self._closed:
            self._closed = True
            score = self._sequence.close()
            try:
                self._panel.destroy()
            finally:
                self._on_closed(score)
