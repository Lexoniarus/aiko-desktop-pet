"""Short-lived cursor attention history, without any desktop dependencies."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CursorAttentionSnapshot:
    """Immutable clock values used when rendering one frame."""

    last_pointer_move: float
    attention_until: float


@dataclass(slots=True)
class CursorAttention:
    """Track pointer changes and the original brief walk-attention window."""

    previous_pointer: tuple[int, int] | None = None
    last_pointer_move: float = -100.0
    last_attention: float = -100.0
    attention_until: float = -100.0

    def reset(self) -> None:
        """Forget cursor history on game-mode transitions."""
        self.previous_pointer = None
        self.last_pointer_move = -100.0
        self.last_attention = -100.0
        self.attention_until = -100.0

    def snapshot(self) -> CursorAttentionSnapshot:
        """Read the current attention window without exposing mutable state."""
        return CursorAttentionSnapshot(
            last_pointer_move=self.last_pointer_move,
            attention_until=self.attention_until,
        )

    def observe(
        self, pointer: tuple[int, int], now: float, *, game_mode: bool = False,
    ) -> bool:
        """Observe pointer motion; keep game-mode readings as baselines."""
        previous = self.previous_pointer
        self.previous_pointer = pointer
        if game_mode or previous is None or pointer == previous:
            return False
        self.last_pointer_move = now
        if now - self.last_attention >= 6.0:
            self.last_attention = now
            self.attention_until = now + 1.0
        return True
