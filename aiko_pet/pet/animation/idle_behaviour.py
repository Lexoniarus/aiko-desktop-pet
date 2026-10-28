"""Pure idle expression from existing needs and the canonical overall feeling."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

from ..balance import BALANCE
from ..emotions import EmotionalState
from ..needs import NeedCondition

IdleMode = Literal["neutral", "calm", "active", "tired", "subdued", "tense"]


@dataclass(frozen=True, slots=True)
class IdleBehaviourContext:
    energy: float
    feeling: EmotionalState
    conditions: frozenset[NeedCondition] = frozenset()
    sleeping: bool = False


@dataclass(frozen=True, slots=True)
class IdleBehaviourProfile:
    mode: IdleMode = "neutral"
    hold_minimum: float = 3
    hold_maximum: float = 6
    glance_gap_multiplier: float = 1
    step_gap_multiplier: float = 1
    body_glance_every: int = 3
    allow_steps: bool = True
    maximum_steps: int = 2
    two_step_probability: float = .2
    prefer_lower_gaze: bool = False

    def __post_init__(self) -> None:
        if (not all(math.isfinite(v) and v > 0 for v in (
                self.hold_minimum, self.hold_maximum,
                self.glance_gap_multiplier, self.step_gap_multiplier,
            )) or self.hold_minimum > self.hold_maximum
                or type(self.body_glance_every) is not int or self.body_glance_every < 1
                or self.maximum_steps not in (1, 2)
                or not math.isfinite(self.two_step_probability)
                or not 0 <= self.two_step_probability <= 1):
            raise ValueError("Invalid idle behaviour profile")


def derive_idle_profile(context: IdleBehaviourContext) -> IdleBehaviourProfile:
    """Select expression only; never qualify feelings, wishes or movement."""
    def number(key: str) -> float:
        return BALANCE.number("idle_behaviour", key)

    minimum_energy = BALANCE.number("walk", "minimum_energy")
    if (context.sleeping or NeedCondition.LOW_ENERGY in context.conditions
            or context.energy < minimum_energy):
        mode: IdleMode = "tired"
    elif context.feeling in (
        EmotionalState.SUBDUED, EmotionalState.DOWNCAST, EmotionalState.LONELY,
        EmotionalState.RESERVED,
    ):
        mode = "subdued"
    elif context.feeling in (
        EmotionalState.TENSE, EmotionalState.IRRITATED, EmotionalState.CROWDED,
        EmotionalState.FRUSTRATED, EmotionalState.AMBIVALENT,
    ):
        mode = "tense"
    elif context.energy >= number("active_energy") and (
        context.feeling in (EmotionalState.CHEERFUL, EmotionalState.CAREFREE,
                            EmotionalState.OPTIMISTIC, EmotionalState.PROUD)
        or NeedCondition.LOW_FUN in context.conditions
    ):
        mode = "active"
    else:
        mode = "calm"
    quiet = mode in ("tired", "subdued", "tense")
    return IdleBehaviourProfile(
        mode=mode,
        hold_minimum=number(f"{mode}_hold_minimum_seconds"),
        hold_maximum=number(f"{mode}_hold_maximum_seconds"),
        glance_gap_multiplier=number("quiet_glance_gap_multiplier") if quiet else (
            number("active_glance_gap_multiplier") if mode == "active" else 1
        ),
        step_gap_multiplier=number(f"{mode}_step_gap_multiplier"),
        body_glance_every=BALANCE.integer("idle_behaviour", "quiet_body_glance_every")
        if quiet else (BALANCE.integer("idle_behaviour", "active_body_glance_every")
                       if mode == "active" else
                       BALANCE.integer("ambient", "body_glance_every")),
        allow_steps=not context.sleeping and context.energy >= minimum_energy,
        maximum_steps=1 if quiet else 2,
        two_step_probability=number("active_two_step_probability")
        if mode == "active" else number("two_step_probability"),
        prefer_lower_gaze=mode in ("tired", "subdued"),
    )
