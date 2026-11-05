"""Transient player gesture; item custody remains exclusively in World."""

from dataclasses import dataclass

from ..pet.mind.object_perception import ItemPresentation
from ..world.contracts import WorldPosition


@dataclass(slots=True)
class RoomDrag:
    instance: str
    original: WorldPosition | None
    depth: float
    gesture: str
    presentation: ItemPresentation | None = None
    ready: bool = False
    inside: bool = False
    feedback: tuple[str, bool] | None = None
