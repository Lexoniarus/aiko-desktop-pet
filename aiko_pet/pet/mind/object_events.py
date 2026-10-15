"""Semantic object reactions shared by phase execution and authored dialogue."""

from typing import Literal

ObjectEvent = Literal[
    "object_notice", "object_return", "object_approach", "object_pick_up",
    "object_inspect", "object_recognized", "object_unknown", "object_want",
    "object_later", "object_consuming", "object_put_down", "object_finished",
    "object_handover", "object_offer", "object_refuse",
]
