"""VN player surface: complete questions/answers, explicit next, no opponent."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from functools import partial

from ...games.contracts import GameId, GameRoundEvent, SessionSummary
from ...games.quiz import QuizSession
from ...games.quiz_catalogue import QuizCatalogue
from ...pet.content import GERMAN_TEXT
from ..common.image_button import ImageButton, update_button_state
from ..common.skin import AikoSkin
from ..common.window_geometry import BoundsAt
from .game_panel import GamePanel
from .quiz_sequence import QuizSequence


class QuizWindow:
    def __init__(
        self, root: tk.Tk, *, on_closed: Callable[[SessionSummary], None],
        speak: Callable[[str, int], None], animate: Callable[[str], None],
        emote: Callable[[str, int], None], always_on_top: bool, skin: AikoSkin,
        dialogue: Callable[[str], str] | None = None,
        round_event: Callable[[GameRoundEvent], None] = lambda _event: None,
        express_event: Callable[[str], None] = lambda _event: None,
        bounds_at: BoundsAt | None = None,
        catalogue: QuizCatalogue | None = None,
    ) -> None:
        self._closed = False
        self._on_closed, self.skin = on_closed, skin
        self._sequence: QuizSequence | None = None
        self._shown_id: str | None = None
        self._panel = GamePanel(
            root, GERMAN_TEXT.format("game.name.quiz"), close=self.close,
            next_round=self.next_question, skin=skin, always_on_top=always_on_top,
            game_id=GameId.QUIZ, bounds_at=bounds_at, body_height=500,
        )
        self.window = self._panel.window
        self._question_card = self._panel.passive(self._panel.body, padding=12)
        self._question_card.frame.pack(fill="x", pady=(0, 12))
        self._question = tk.Label(
            self._question_card.body, text="", bg=skin.panel, fg=skin.text,
            font=(skin.font, 11, "bold"), justify="left", anchor="w",
            wraplength=self._panel.content_width - 48,
        )
        self._question.pack(fill="x")
        self.answers: list[ImageButton] = []
        for index in range(4):
            button = skin.button(
                self._panel.body, "", partial(self._choose, index),
                size="regular", align_left=True,
                wraplength=self._panel.content_width - 36,
                preserve_selection=True,
            )
            button.pack(fill="x", pady=4)
            self.answers.append(button)
            self.window.bind(str(index + 1), partial(self._key, index))
        self._explanation_card = self._panel.passive(self._panel.body, padding=12)
        self._explanation = tk.Label(
            self._explanation_card.body, text="", bg=skin.panel, fg=skin.text,
            font=(skin.font, 10), justify="left", anchor="w",
            wraplength=self._panel.content_width - 48,
        )
        self._explanation.pack(fill="x")
        try:
            game = QuizSession(catalogue or QuizCatalogue.load())
        except (OSError, ValueError, TypeError, KeyError):
            self._question.configure(text=GERMAN_TEXT.format("quiz.unavailable"))
            for button in self.answers:
                button.pack_forget()
        else:
            self._sequence = QuizSequence(
                game, schedule=self.window.after, cancel=self.window.after_cancel,
                present=self._present, say=speak, animate=animate, emote=emote,
                dialogue=dialogue, round_event=round_event,
                express_event=express_event,
            )
            self._present()
        self._panel.show(root)

    def _present(self) -> None:
        sequence = self._sequence
        if self._closed or sequence is None:
            return
        game = sequence.game
        question = game.current
        self._question.configure(text=question.text)
        answered = game.selected is not None
        for index, (button, choice) in enumerate(zip(self.answers, question.answers)):
            marker = ""
            if answered and choice.id == question.correct_answer_id:
                marker = "✓ Richtig: "
            elif answered and choice.id == game.selected:
                marker = "Deine Antwort: "
            button.configure(
                text=f"{index + 1}. {marker}{choice.text}",
                state="normal" if not answered and not sequence.busy else "disabled",
            )
            button.set_selected(answered and choice.id == question.correct_answer_id)
        explanation = ""
        if answered:
            correct = next(a.text for a in question.answers
                           if a.id == question.correct_answer_id)
            explanation = GERMAN_TEXT.format(
                "quiz.correct" if game.selected == question.correct_answer_id
                else "quiz.incorrect", answer=correct, explanation=question.explanation,
            )
        self._explanation.configure(text=explanation)
        if answered:
            self._explanation_card.frame.pack(fill="x", pady=(12, 0))
        else:
            self._explanation_card.frame.pack_forget()
        self._panel.title.configure(text=GERMAN_TEXT.format(
            "quiz.progress", number=str(game.index + 1),
        ))
        self._panel.score_labels["correct"].configure(text=str(game.correct))
        self._panel.score_labels["answered"].configure(
            text=str(game.index + int(answered)),
        )
        self._panel.status.configure(text=GERMAN_TEXT.format(
            "quiz.finished" if game.finished else "quiz.think",
            correct=str(game.correct),
        ))
        if self._panel.next_button is not None:
            self._panel.next_button.configure(text=GERMAN_TEXT.format(
                "quiz.again" if game.finished else "quiz.next",
            ))
            update_button_state(self._panel.next_button,
                                enabled=answered and not sequence.busy)
        self._panel.scroll.adopt()
        if self._shown_id != question.id:
            self._panel.scroll.canvas.yview_moveto(0)
            self._shown_id = question.id
        # Paint the committed resolution before emitting its completion receipt.
        self.window.update_idletasks()

    def _key(self, index: int, _event: tk.Event[tk.Misc]) -> str:
        self._choose(index)
        return "break"

    def _choose(self, index: int) -> None:
        if not self._closed and self._sequence is not None:
            self._sequence.answer(self._sequence.game.current.answers[index].id)

    def greet(self) -> None:
        if self._sequence is not None:
            self._sequence.greet()

    def next_question(self) -> None:
        if self._sequence is not None:
            self._sequence.advance()

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        if self._sequence is not None:
            self._sequence.close()
        self._panel.destroy()
        # Completion was already credited at the final resolution, not at close.
        self._on_closed(SessionSummary(GameId.QUIZ))

    def set_topmost(self, enabled: bool) -> None:
        self.window.wm_attributes("-topmost", enabled)
