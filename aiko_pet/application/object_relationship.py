"""Commit identified withholding consequences through the existing pet owners."""

from collections import OrderedDict

from ..pet.mind.mind import PetMind
from ..pet.state import PetState


class ObjectRelationship:
    """Session receipts; durable loss budgets remain owned by PetState."""

    def __init__(self, state: PetState, mind: PetMind) -> None:
        self._state, self._mind = state, mind
        self._receipts: OrderedDict[str, None] = OrderedDict()

    def withheld(
        self, receipt: str, loss: float, *, active_time: float, monotonic_time: float,
    ) -> float:
        if receipt in self._receipts:
            return 0.0
        applied = 0.0
        if loss > 0:
            applied = self._state.apply_object_withholding(loss)
        self._mind.note_object_withholding(monotonic_time)
        self._receipts[receipt] = None
        if len(self._receipts) > 4096:
            self._receipts.popitem(last=False)
        return applied
