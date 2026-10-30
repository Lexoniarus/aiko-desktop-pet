"""Present minigame dialogue through Aiko's existing character overlays.

The minigame never owns a second speech bubble or presentation stack.
"""

from __future__ import annotations

from collections.abc import Callable

from ...games.rock_paper_scissors import Move
from ...pet.animation.expression import EXPRESSION_CLIPS, Expression, event_expression
from ..pet_view.reaction_player import ReactionPlayer
from ..pet_view.speech_presenter import SpeechPresenter
from .game_presentation import GamePresentation


class GameSpeech:
    """Exclusive character presentation channel while playing."""

    def __init__(
        self, reactions: ReactionPlayer, speech: SpeechPresenter,
        mark_spoken: Callable[[], None],
        set_game_mode: Callable[[bool], None],
        animate_character: Callable[[str], None],
        express: Callable[[Expression | None], object] = lambda _value: None,
        presentation: GamePresentation | None = None,
    ) -> None:
        self._reactions = reactions
        self._speech = speech
        self._mark_spoken = mark_spoken
        self._set_game_mode = set_game_mode
        self._animate_character = animate_character
        self._express = express
        self.presentation = presentation

    def start(self) -> None:
        self._reactions.cancel()
        self._speech.hide()
        self._speech.begin_game()
        self._set_game_mode(True)

    def say(self, phrase: str, duration_ms: int) -> None:
        self._mark_spoken()
        self._speech.show_text(phrase, duration_ms)

    def emote(self, name: str, duration_ms: int) -> None:
        self._mark_spoken()
        self._speech.show_emote(name, duration_ms)

    def react(self, event: str) -> None:
        """The sequence calls this at actual speech admission, never selection."""
        self._express(event_expression(event))

    def hand(self, aiko: Move, duration_ms: int) -> None:
        """Aiko reveals only her own hand; the player view owns its hand."""
        self._mark_spoken()
        self._speech.show_game_hand(aiko, duration_ms)

    def animate(self, name: str) -> None:
        expression = next((value for value, clip in EXPRESSION_CLIPS.items()
                           if clip == name), None)
        if expression is not None:
            self._express(expression)
            return
        if name != "idle":
            self._express(None)
        self._animate_character(name)

    def stop(self) -> None:
        if self.presentation is not None:
            self.presentation.cancel()
            self.presentation.look(None)
        self._express(None)
        self._speech.hide()
        self._set_game_mode(False)
