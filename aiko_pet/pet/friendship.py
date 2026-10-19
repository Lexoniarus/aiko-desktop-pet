"""Pure relationship rewards and bounded direct consequences; PetState commits."""

from __future__ import annotations

import math
from dataclasses import replace
from typing import Protocol

from .balance import BALANCE
from .friendship_history import FriendshipHistory, FriendshipProgress, RelationshipEvent
from .value_rules import clamp_need_value

FRIENDSHIP_REWARD_INTERVAL = BALANCE.integer("friendship", "reward_interval_seconds")
FRIENDSHIP_DAILY_CAP = BALANCE.number("friendship", "daily_cap")
CARE_FRIENDSHIP_GAIN = {
    action: BALANCE.number("friendship", f"{action}_gain")
    for action in ("feed", "play", "pet", "talk", "energy_drink")
}
CARE_PRIMARY_NEED = {
    "feed": "satiety",
    "play": "fun",
    "pet": "affection",
    "talk": "social",
    "energy_drink": "energy",
}
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
        penalties=tuple(
            e
            for e in history.penalties
            if e.at
            > now
            - max(
                BALANCE.number("friendship", "click_window_seconds"),
                BALANCE.number("friendship", "withholding_window_seconds"),
            )
        ),
    )


def calculate_friendship_reward(
    record: FriendshipRecord,
    action: str,
    stamp: float,
    need_before: float,
) -> FriendshipProgress | None:
    """Accepted contact survives exhausted credit; elapsed time owns eligibility."""
    if (
        action not in CARE_FRIENDSHIP_GAIN
        or not math.isfinite(stamp)
        or stamp <= 0
        or not math.isfinite(need_before)
    ):
        return None
    now = record.lived_seconds
    history = prune_history(start_history(record.friendship_history, now), now)
    history = replace(history, last_contact=now)
    anchors = dict(history.eligible)
    if action in anchors and now - anchors[action] < FRIENDSHIP_REWARD_INTERVAL:
        return FriendshipProgress(record.friendship, history, now)
    # A qualifying attempt consumes its interval even when the common pot is empty.
    anchors[action] = now
    gain = CARE_FRIENDSHIP_GAIN[action]
    if need_before > BALANCE.number("friendship", "need_threshold"):
        gain *= BALANCE.number("friendship", "satisfied_reward_fraction")
    short = BALANCE.number("friendship", "short_window_seconds")
    gain = max(
        0.0,
        min(
            gain,
            100 - record.friendship,
            FRIENDSHIP_DAILY_CAP - sum(e.amount for e in history.rewards),
            BALANCE.number("friendship", "short_cap")
            - sum(e.amount for e in history.rewards if e.at > now - short),
        ),
    )
    events = history.rewards
    if gain > 1e-12:
        events += (RelationshipEvent(now, action, gain),)
    return FriendshipProgress(
        clamp_need_value(record.friendship + gain),
        replace(history, rewards=events, eligible=tuple(anchors.items())),
        now,
    )


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
    if kind not in ("click", "withholding"):
        raise ValueError("Unknown relationship penalty")
    friendship_after_withholding(record.friendship, loss)  # Validate before changes.
    now = record.lived_seconds
    history = prune_history(start_history(record.friendship_history, now), now)
    window = BALANCE.number("friendship", f"{kind}_window_seconds")
    used = sum(
        e.amount for e in history.penalties if e.kind == kind and e.at > now - window
    )
    amount = max(
        0.0,
        min(
            loss, record.friendship, BALANCE.number("friendship", f"{kind}_cap") - used
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
