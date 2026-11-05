"""Accepted contact and bounded direct consequences; PetState commits."""

from __future__ import annotations

import math
from dataclasses import replace
from typing import Protocol

from .balance import BALANCE
from .friendship_history import FriendshipHistory, FriendshipProgress, RelationshipEvent
from .moodlet_catalog import MOODLET_CATALOG
from .moodlets import (
    FoodMonotonyParameters,
    MoodletId,
    PettingParameters,
    RelocationParameters,
)
from .value_rules import clamp_need_value

# Retained only to validate/prune historical v1 reward metadata, never live budgets.
FRIENDSHIP_REWARD_INTERVAL = BALANCE.integer("friendship", "reward_interval_seconds")
FRIENDSHIP_DAILY_CAP = BALANCE.number("friendship", "daily_cap")
CONTACT_ACTIONS = ("feed", "play", "pet", "talk", "energy_drink")
REWARD_KINDS = frozenset((*CONTACT_ACTIONS, "wish"))
LEGACY_REWARD_ACTIONS = ("sleep",)


class FriendshipRecord(Protocol):
    @property
    def friendship(self) -> float: ...

    @property
    def friendship_history(self) -> FriendshipHistory: ...

    @property
    def lived_seconds(self) -> float: ...


def start_history(history: FriendshipHistory, now: float) -> FriendshipHistory:
    return history if history.baseline is not None else replace(history, baseline=now)


def prune_history(history: FriendshipHistory, now: float) -> FriendshipHistory:
    window = BALANCE.number("friendship", "history_window_seconds")
    return replace(
        history,
        rewards=tuple(e for e in history.rewards if e.at > now - window),
        eligible=tuple(
            (a, t) for a, t in history.eligible if t > now - FRIENDSHIP_REWARD_INTERVAL
        ),
        penalties=tuple(e for e in history.penalties
                        if e.at > now - penalty_budget(e.kind)[0]),
    )


def begin_continuous_friendship(
    history: FriendshipHistory, now: float,
) -> FriendshipHistory:
    """Activate once at an accounted-for endpoint, without fabricated contact."""
    history = start_history(history, now)
    return (replace(history, continuous_since=now)
            if history.continuous_since is None else history)


def record_accepted_contact(
    record: FriendshipRecord, action: str, stamp: float,
) -> FriendshipProgress | None:
    """Actual personal care renews contact; points change only through elapsed flow."""
    if action not in CONTACT_ACTIONS or not math.isfinite(stamp) or stamp <= 0:
        return None
    now = record.lived_seconds
    history = prune_history(begin_continuous_friendship(record.friendship_history, now),
                            now)
    return FriendshipProgress(record.friendship, replace(history, last_contact=now),
                              now)


def friendship_after_withholding(friendship: float, loss: float) -> float:
    if not math.isfinite(loss) or loss < 0:
        raise ValueError("Friendship loss must be finite and nonnegative")
    return clamp_need_value(friendship - loss)


def apply_negative_event(
    record: FriendshipRecord,
    kind: str,
    loss: float,
) -> FriendshipProgress:
    """Durable rolling caps survive new episodes, restart and wall-clock changes."""
    window, cap = penalty_budget(kind)
    friendship_after_withholding(record.friendship, loss)  # Validate before changes.
    now = record.lived_seconds
    history = prune_history(start_history(record.friendship_history, now), now)
    used = sum(
        e.amount for e in history.penalties if e.kind == kind and e.at > now - window
    )
    amount = max(
        0.0,
        min(
            loss, record.friendship, cap - used
        ),
    )
    events = history.penalties
    if amount > 1e-12:
        events += (RelationshipEvent(now, kind, amount),)
    return FriendshipProgress(
        record.friendship - amount,
        replace(history, penalties=events),
        now,
    )


PENALTY_KINDS = frozenset((
    "click", "withholding", "petting", "food_variety", "relocation",
))


def penalty_budget(kind: str) -> tuple[float, float]:
    """One lookup shared by live policy, pruning and save validation."""
    if kind in ("click", "withholding"):
        return (BALANCE.number("friendship", f"{kind}_window_seconds"),
                BALANCE.number("friendship", f"{kind}_cap"))
    if kind in ("petting", "food_variety", "relocation"):
        key = {"petting": MoodletId.CROWDED, "food_variety": MoodletId.FOOD_MONOTONY,
               "relocation": MoodletId.DISRUPTED}[kind]
        parameters = MOODLET_CATALOG.definitions[key].parameters
        assert isinstance(parameters, (
            PettingParameters, FoodMonotonyParameters, RelocationParameters,
        ))
        return (parameters.friendship_loss_window_seconds,
                parameters.friendship_loss_cap_points)
    raise ValueError("Unknown relationship penalty")
