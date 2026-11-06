"""Optional environment facts; no identity, custody or care decisions."""

from typing import Protocol

from ..pet.mind.object_attention import ObjectAttention
from ..pet.mind.object_knowledge import ObjectKnowledge


class ObjectSpatialGeometry(Protocol):
    def sees_instance(self, instance: str, attention: ObjectAttention) -> bool: ...

    def sees_place(self, known: ObjectKnowledge, attention: ObjectAttention) -> bool: ...

    def same_place(self, instance: str, known: ObjectKnowledge) -> bool: ...

    def distance_to_place(self, known: ObjectKnowledge) -> float: ...
