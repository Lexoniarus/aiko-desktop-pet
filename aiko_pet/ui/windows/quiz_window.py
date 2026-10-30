"""VN player surface: complete questions/answers, explicit next, no opponent."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from functools import partial

from ...asset_paths import GAME_ART_DIR
from ...games.contracts import GameId, GameRoundEvent, SessionSummary
from ...games.quiz import QuizSession
from ...games.quiz_catalogue import QuizCatalogue
from ...pet.content import GERMAN_TEXT
from ..common.image_button import ImageButton, update_button_state
from ..common.rounded_panel import RoundedPanel
from ..common.skin import AikoSkin
from ..common.window_geometry import BoundsAt
from ..pet_view.game_effects import GameEffects
from .game_panel import GamePanel
from .game_presentation import GamePresentation
from .game_waiting import GameWaiting
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
        presentation: GamePresentation | None = None,
    ) -> None:
        self._closed = False
        self._on_closed, self.skin = on_closed, skin
        self._sequence: QuizSequence | None = None
        self._shown_id: str | None = None
        self._presentation = presentation
        self._history: dict[int, bool] = {}
        self._panel = GamePanel(
            root, GERMAN_TEXT.format("game.name.quiz"), close=self.close,
            next_round=self.next_question, skin=skin, always_on_top=always_on_top,
            game_id=GameId.QUIZ, bounds_at=bounds_at, body_height=570,
            reserve_right=100,
        )
        self.window = self._panel.window
        self._effects = (GameEffects(self.window, topmost=always_on_top,
                                     configure=presentation.configure)
                         if presentation is not None else None)
        self._waiting = GameWaiting(
            self.window.after, self.window.after_cancel, presentation,
            lambda: self._point(-1), self._wait_comment,
        )
        self._stage = tk.Frame(self._panel.body, bg="#7871a5", padx=12, pady=10)
        self._stage.pack(fill="x", pady=(0, 8))
        self._stage_art = tk.PhotoImage(master=self.window,
                                       file=str(GAME_ART_DIR / 'quiz-stage.png'))
        self._emblem = tk.PhotoImage(master=self.window,
                                    file=str(GAME_ART_DIR / 'quiz-emblem.png'))
        width = self._panel.content_width - 32
        self._marquee = tk.Canvas(self._stage, width=width, height=104,
                                  bg="#7871a5", bd=0, highlightthickness=0)
        self._marquee.pack(fill="x")
        self._marquee.create_image(width // 2, 52, image=self._stage_art)
        self._marquee.create_text(width // 2 - 22, 25, text="DIE KLEINE GROSSE",
                                  font=(skin.font, 8), fill="#efe1bd")
        self._marquee.create_text(width // 2 - 22, 53, text="Quizshow",
                                  font=(skin.font, 23, "bold"), fill="#fff8e4")
        self._marquee.create_text(width // 2 - 22, 82, text="mit Aiko",
                                  font=(skin.font, 10, "italic"), fill="#efd6df")
        self._marquee.create_image(width // 2 + 110, 53, image=self._emblem)
        self._question_card = RoundedPanel(
            self._stage, fill="#fffaee", border="#e0c48d",
            background="#7871a5", padding=12,
        )
        self._question_card.frame.pack(fill="x", pady=(0, 12))
        self._question = tk.Label(
            self._question_card.body, text="", bg="#fffaee", fg="#4c416b",
            font=(skin.font, 11, "bold"), justify="center", anchor="center",
            wraplength=width - 36, pady=12,
        )
        self._question.pack(fill="x")
        self._answers_grid = tk.Frame(self._stage, bg="#7871a5")
        self._answers_grid.pack(fill="x")
        columns = 2 if width >= 420 else 1
        button_width = (width - (columns - 1) * 12) // columns
        self.answers: list[ImageButton] = []
        self._answer_slots: list[tk.Frame] = []
        for index in range(4):
            slot = tk.Frame(self._answers_grid, width=button_width, height=106,
                            bg="#7871a5")
            slot.grid(row=index // columns, column=index % columns,
                      padx=(0, 12 if index % columns == 0 and columns == 2 else 0),
                      pady=5, sticky="nsew")
            slot.grid_propagate(False)
            button = skin.button(
                slot, "", partial(self._choose, index), size="quiz_answer",
                wraplength=button_width - 40, preserve_selection=True,
            )
            self._answer_slots.append(slot)
            self.answers.append(button)
            self.window.bind(str(index + 1), partial(self._key, index))
        self._lights = tk.Canvas(self._panel.body, width=300, height=26,
                                 bg=skin.background, bd=0, highlightthickness=0)
        self._lights.pack(pady=6)
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
                express_event=express_event, look=self._look,
            )
            self._present()
        self._panel.show(root)
        self._follow_cues()

    def _present(self) -> None:
        sequence = self._sequence
        if self._closed or sequence is None:
            return
        game = sequence.game
        question = game.current
        if self._shown_id != question.id:
            columns = (2 if self._panel.content_width >= 444
                       and max(len(a.text) for a in question.answers) < 65 else 1)
            width = (self._panel.content_width - 32 - (columns - 1) * 12) // columns
            slots = zip(self._answer_slots, self.answers)
            for index, (slot, button) in enumerate(slots):
                slot.grid_configure(
                    row=index // columns, column=index % columns,
                    padx=(0, 12 if columns == 2 and index % 2 == 0 else 0),
                )
                slot.configure(width=width)
                button.set_wraplength(width - 40)
        self._waiting.set_active(not sequence.busy and game.selected is None)
        self._question.configure(
            text=question.text if sequence.question_visible else "✦",
        )
        answered = sequence.revealed
        self._lights.delete("all")
        if answered:
            self._history[game.index] = game.selected == question.correct_answer_id
        elif game.index == 0:
            self._history.clear()
        for index in range(10):
            if index in self._history:
                fill = "#aba5d0" if self._history[index] else "#e7bbc9"
            else:
                fill = "#fff1c3" if index == game.index else "#e8e0ec"
            x = 12 + index * 28
            self._lights.create_oval(x, 7, x + 12, 19, fill=fill, outline="#bda5c3")
        for index, (button, choice) in enumerate(zip(self.answers, question.answers)):
            marker = ""
            if answered and choice.id == question.correct_answer_id:
                marker = "✓ Richtig: "
            elif answered and choice.id == game.selected:
                marker = "Deine Antwort: "
            visible = index < sequence.visible_answers
            if visible:
                button.place(x=0, y=0, relwidth=1, relheight=1)
            else:
                button.place_forget()
            button.configure(
                text=f"{chr(65 + index)} · {marker}{choice.text}" if visible else "",
                state="normal" if visible and not answered and not sequence.busy
                else "disabled",
                takefocus=visible and not sequence.busy,
            )
            button.set_selected(
                (answered and choice.id == question.correct_answer_id)
                or (not answered and choice.id == game.selected),
            )
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
        self._panel.score_labels["correct"].configure(text=str(sequence.visible_correct))
        self._panel.score_labels["answered"].configure(
            text=str(game.index + int(answered)),
        )
        self._panel.status.configure(text=GERMAN_TEXT.format(
            "quiz.finished" if game.finished and answered else
            "game.aiko_turn" if sequence.busy else "quiz.think",
            correct=str(sequence.visible_correct),
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

    def _follow_cues(self) -> None:
        if self._closed or self._effects is None or self._presentation is None:
            return
        x, y, scale = self._presentation.origin()
        image = self._effects.image(GAME_ART_DIR / 'quiz-cues.png', 95 * scale)
        self._effects.show('cues', image, x + 160 * scale, y + 126 * scale)
        number = self._sequence.game.index + 1 if self._sequence is not None else 1
        self._effects.caption('cues', f"{number} / 10")
        self._effects.later(100, self._follow_cues)

    def _point(self, index: int) -> tuple[float, float]:
        widget = self._question if index == -1 else self._answer_slots[index]
        return (widget.winfo_rootx() + widget.winfo_width() / 2,
                widget.winfo_rooty() + widget.winfo_height() / 2)

    def _look(self, index: int | None) -> None:
        if self._presentation is not None:
            self._presentation.look(None if index is None else self._point(index))

    def _wait_comment(self) -> None:
        if self._sequence is not None:
            self._sequence.wait_comment()

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
        self._waiting.set_active(False)
        if self._sequence is not None:
            self._sequence.close()
        if self._effects is not None:
            self._effects.close()
        self._panel.destroy()
        # Completion was already credited at the final resolution, not at close.
        self._on_closed(SessionSummary(GameId.QUIZ))

    def set_topmost(self, enabled: bool) -> None:
        self.window.wm_attributes("-topmost", enabled)
        if self._effects is not None:
            self._effects.set_topmost(enabled)
