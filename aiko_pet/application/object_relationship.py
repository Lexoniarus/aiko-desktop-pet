"""Commit identified withholding consequences through the existing pet owners."""

from collections import OrderedDict

from ..pet.balance import BALANCE
from ..pet.mind.mind import PetMind
from ..pet.state import PetState


class ObjectRelationship:
    """Session receipts and cross-episode cooldown; no speech or World access."""

    def __init__(self, state: PetState, mind: PetMind) -> None:
        self._state, self._mind = state, mind
        self._receipts: OrderedDict[str, None] = OrderedDict()
        self._next_loss_at = 0.0

    def withheld(
        self, receipt: str, loss: float, *, active_time: float, monotonic_time: float,
    ) -> float:
        if receipt in self._receipts:
            return 0.0
        applied = 0.0
        if loss > 0 and active_time >= self._next_loss_at:
            applied = self._state.apply_object_withholding(loss)
            if applied > 0:
                self._next_loss_at = active_time + BALANCE.number(
                    "object_withholding", "friendship_cooldown_seconds",
                )
        self._mind.note_object_withholding(monotonic_time)
        self._receipts[receipt] = None
        if len(self._receipts) > 4096:
            self._receipts.popitem(last=False)
        return applied
