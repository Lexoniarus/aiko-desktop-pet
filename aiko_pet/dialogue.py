"""Legacy personality imports; canonical mind and catalogue are in personality."""

from __future__ import annotations

from .personality.mind import AikoMind as AikoMind
from .personality.catalog import (
    CATALOGUE as CATALOGUE,
    ANIMATIONS as ANIMATIONS,
    EMOTIONS as EMOTIONS,
    EMOTION_LABELS as EMOTION_LABELS,
    PERIODS as PERIODS,
    DialogueBook as DialogueBook,
    Line as Line,
    Reaction as Reaction,
)
from .personality.workload_events import (
    ComputerVoice as ComputerVoice,
    WorkloadEventDetector as WorkloadEventDetector,
)
from .personality.click_policy import ClickButton as ClickButton
from .personality.work_episode import WorkEpisodeMemory as WorkEpisodeMemory
