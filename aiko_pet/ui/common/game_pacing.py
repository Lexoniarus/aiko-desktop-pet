"""Shared brisk game cues, independent of slower social conversation pacing."""
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GamePacing:
    emote_ms: int = 450
    card_flight_ms: int = 320
    card_shuffle_ms: int = 900
    card_gather_ms: int = 450
    card_flip_frame_ms: int = 25
    bank_reveal_ms: int = 260
    bank_pause_ms: int = 100
    next_hand_ms: int = 900

    def text_ms(self, text: str) -> int:
        return min(3200, max(750, 180 + len(text.strip()) * 25))


GAME_PACING = GamePacing()
