"""The five physical/care values, independent of mood and relationship."""

from dataclasses import dataclass
from enum import StrEnum

from .balance import BALANCE


@dataclass(frozen=True, slots=True)
class NeedLevels:
    """A detached value used by policies, not another mutable pet state."""

    satiety: float
    energy: float
    fun: float
    social: float
    affection: float


class NeedCondition(StrEnum):
    LOW_SATIETY = "low_satiety"
    LOW_ENERGY = "low_energy"
    LOW_FUN = "low_fun"
    LOW_SOCIAL = "low_social"
    LOW_AFFECTION = "low_affection"


def assess_need_conditions(needs: NeedLevels) -> frozenset[NeedCondition]:
    """Concurrent care facts, independent of sleep, mood and lasting feelings."""
    return frozenset(
        condition
        for condition, value, threshold in (
            (
                NeedCondition.LOW_SATIETY,
                needs.satiety,
                BALANCE.number("mind", "hungry_satiety"),
            ),
            (
                NeedCondition.LOW_ENERGY,
                needs.energy,
                BALANCE.number("mind", "tired_energy"),
            ),
            (
                NeedCondition.LOW_FUN,
                needs.fun,
                BALANCE.number("mood", "low_need_threshold"),
            ),
            (
                NeedCondition.LOW_SOCIAL,
                needs.social,
                BALANCE.number("mind", "care_lonely_social"),
            ),
            (
                NeedCondition.LOW_AFFECTION,
                needs.affection,
                BALANCE.number("mind", "care_low_affection"),
            ),
        )
        if value <= threshold
    )
