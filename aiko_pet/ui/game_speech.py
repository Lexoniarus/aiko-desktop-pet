"""Present minigame dialogue through Aiko's existing character overlays.

The minigame never owns a second speech bubble or presentation stack.
"""

from __future__ import annotations

from collections.abc import Callable

from ..games.rock_paper_scissors import Move
from ..presentation.reaction_playback import ReactionPlayer
from .speech_presenter import SpeechPresenter


class GameSpeech:
    """Exclusive character presentation channel while playing."""

    def __init__(
        self, reactions: ReactionPlayer, speech: SpeechPresenter,
        mark_spoken: Callable[[], None],
        set_game_mode: Callable[[bool], None],
        animate_character: Callable[[str], None],
    ) -> None:
        self._reactions = reactions
        self._speech = speech
        self._mark_spoken = mark_spoken
        self._set_game_mode = set_game_mode
        self._animate_character = animate_character

    def start(self) -> None:
        self._reactions.cancel()
        self._speech.hide()
        self._set_game_mode(True)

    def say(self, phrase: str, duration_ms: int) -> None:
        self._mark_spoken()
        self._speech.show_text(phrase, duration_ms)

    def emote(self, name: str, duration_ms: int) -> None:
        self._mark_spoken()
        self._speech.show_emote(name, duration_ms)

    def hands(self, player: Move, aiko: Move, duration_ms: int) -> None:
        self._mark_spoken()
        self._speech.show_game_hands(player, aiko, duration_ms)

    def animate(self, name: str) -> None:
        self._animate_character(name)

    def stop(self) -> None:
        self._speech.hide()
        self._set_game_mode(False)
