"""The five physical/care values, independent of mood and relationship."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class NeedLevels:
    """A detached value used by policies, not another mutable pet state."""

    satiety: float
    energy: float
    fun: float
    social: float
    affection: float
