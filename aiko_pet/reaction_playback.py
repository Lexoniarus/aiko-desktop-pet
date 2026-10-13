"""Legacy visual playback imports; the presenter owns reaction timers."""

from __future__ import annotations

from .presentation.reaction_playback import (
    TimerCallback as TimerCallback,
    ScheduleTimer as ScheduleTimer,
    CancelTimer as CancelTimer,
    DisplayCue as DisplayCue,
    StartAction as StartAction,
    choose_idle_emote as choose_idle_emote,
    ReactionPlayer as ReactionPlayer,
)
