"""Semantic object reactions shared by phase execution and authored dialogue."""

from typing import Literal

ObjectEvent = Literal[
    "object_notice", "object_approach", "object_pick_up",
    "object_inspect", "object_recognized", "object_unknown", "object_want",
    "object_later", "object_put_down",
    "object_handover", "object_offer", "object_refuse",
    "object_recall_food", "object_recall_drink",
    "object_recall_saved_food", "object_recall_saved_drink",
    "object_consuming_food", "object_consuming_drink",
    "object_finished_food", "object_finished_drink", "object_missing",
    "object_search", "object_found",
    "object_busy",
]
