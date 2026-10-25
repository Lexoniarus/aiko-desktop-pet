"""Cancellable quizmaster presentation, with explicit player advancement."""

from collections.abc import Callable
from uuid import uuid4

from ...games.contracts import GameId, GameRoundEvent
from ...games.quiz import QuizSession
from ...pet.mind.reaction_sequence import Cue, conversation_timing
from .rock_paper_scissors_dialogue import GameDialogue


class QuizSequence:
    def __init__(
        self, game: QuizSession, *,
        schedule: Callable[[int, Callable[[], None]], str],
        cancel: Callable[[str], None], present: Callable[[], None],
        say: Callable[[str, int], None], animate: Callable[[str], None],
        emote: Callable[[str, int], None],
        dialogue: Callable[[str], str] | None = None,
        round_event: Callable[[GameRoundEvent], None] = lambda _event: None,
    ) -> None:
        self.game = game
        self._schedule, self._cancel, self._present = schedule, cancel, present
        self._say, self._animate, self._emote = say, animate, emote
        self._dialogue = dialogue or GameDialogue().choose
        self._event = round_event
        self._session = uuid4().hex
        self._closed = self._started = False
        self._round_started = False
        self.busy = True
        self._timer: str | None = None
        self._generation = 0

    def _ready(self) -> None:
        self._timer = None
        if not self._closed:
            self.busy = False
            self._animate("idle")
            self._present()

    def _react(self, event: str) -> None:
        self.busy = True
        self._present()
        text = self._dialogue(event)
        duration = conversation_timing((Cue.text(text),))[0].duration_ms
        self._animate("idle")
        self._generation += 1
        generation = self._generation

        def ready() -> None:
            if not self._closed and generation == self._generation:
                self._ready()

        def speak() -> None:
            if not self._closed and generation == self._generation:
                self._say(text, duration)
                self._timer = self._schedule(duration, ready)

        if event == "game_quiz_correct":
            self._emote("star", 700)
            self._timer = self._schedule(700, speak)
        else:
            speak()

    def _begin(self) -> None:
        self._event(GameRoundEvent(
            GameId.QUIZ, self._session, self.game.rounds_completed + 1,
        ))
        self._round_started = True

    def greet(self) -> None:
        if not self._closed and not self._started:
            self._started = True
            self._begin()
            self._react("game_quiz_greeting")

    def answer(self, answer_id: str) -> bool:
        if self._closed or self.busy or not self._round_started:
            return False
        try:
            correct = self.game.answer(answer_id)
        except ValueError:
            return False
        self.busy = True
        # The visible resolution is the completion boundary, before final speech.
        self._present()
        if self._closed:
            return True
        if self.game.finished:
            self._event(GameRoundEvent(
                GameId.QUIZ, self._session, self.game.rounds_completed, "completed",
            ))
            self._react("game_quiz_finish")
        elif self.game.error_streak >= 2:
            self._react("game_quiz_encourage")
        elif self.game.index == 4 and correct:
            self._react("game_quiz_rolebreak")
        else:
            self._react("game_quiz_correct" if correct else "game_quiz_incorrect")
        return True

    def advance(self) -> None:
        if self._closed or self.busy or self.game.selected is None:
            return
        if self.game.finished:
            self.game.new_round()
            self._begin()
            self._react("game_quiz_greeting")
        else:
            self.game.advance()
            self._present()

    def close(self) -> None:
        self._closed = True
        self._generation += 1
        if self._timer is not None:
            self._cancel(self._timer)
            self._timer = None
