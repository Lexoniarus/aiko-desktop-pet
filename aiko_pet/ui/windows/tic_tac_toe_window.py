"""The shared board is player UI; Aiko's reactions stay with her figure."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from functools import partial

from ...games.contracts import GameRoundEvent, SessionSummary
from ...games.tic_tac_toe import Board
from ...pet.content import GERMAN_TEXT
from ..common.skin import AikoSkin
from .game_panel import GamePanel
from .tic_tac_toe_sequence import TicTacToeSequence


class TicTacToeWindow:
    def __init__(
        self, root: tk.Tk, *, on_closed: Callable[[SessionSummary], None],
        speak: Callable[[str, int], None], animate: Callable[[str], None],
        always_on_top: bool, skin: AikoSkin,
        dialogue: Callable[[str], str] | None = None,
        round_event: Callable[[GameRoundEvent], None] = lambda _event: None,
    ) -> None:
        self._closed = False
        self._on_closed = on_closed
        self.skin = skin
        self._panel = GamePanel(
            root, GERMAN_TEXT.format("game.name.tic_tac_toe"), close=self.close,
            next_round=self.next_round, skin=skin, always_on_top=always_on_top,
        )
        self.window = self._panel.window
        try:
            self.buttons: list[tk.Button] = []
            for i in range(9):
                button = tk.Button(
                    self._panel.body, text=" ", width=4, height=2,
                    font=(skin.font, 18, "bold"), bg=skin.panel, fg=skin.text,
                    disabledforeground=skin.text, command=partial(self.choose, i),
                )
                button.grid(row=i // 3, column=i % 3, padx=3, pady=3)
                self.buttons.append(button)
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
                state="normal" if board.turn == "X" and board.winner is None
                and not board.cells[i] else "disabled",
                bg=self.skin.accent if i in board.winning_line else self.skin.panel,
            )
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
