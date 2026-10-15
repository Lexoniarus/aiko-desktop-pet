"""Choose foreground animation priority independently of Tk and host input."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

AnimationMode = Literal["game", "sleep", "action", "timed", "passive"]


@dataclass(frozen=True, slots=True)
class AnimationPriority:
    """The chosen animation source and required owner-state transitions."""

    mode: AnimationMode
    animation: str | None = None
    clear_action: bool = False
    interrupt_walk: bool = False


def choose_animation_priority(
    *,
    game_mode: bool,
    sleeping: bool,
    active_action: str | None,
    action_loops: bool,
    timed_action_active: bool,
) -> AnimationPriority:
    """Preserve game, sleep and one-shot priorities before ambient decisions.

    A timed action's actual clip is read only when that priority wins;
    this policy never calls UI ports, reads files or mutates runtime state.
    """
    if game_mode:
        if active_action is not None and not action_loops:
            return AnimationPriority("game", animation=active_action)
        return AnimationPriority("game", animation="waiting", clear_action=True)
    if sleeping:
        return AnimationPriority(
            "sleep", animation="sleep", clear_action=True, interrupt_walk=True,
        )
    if active_action is not None and not action_loops:
        return AnimationPriority("action", animation=active_action)
    if timed_action_active:
        return AnimationPriority("timed")
    return AnimationPriority("passive", clear_action=True)
