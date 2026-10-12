"""Pure care rules for Aiko, with an optional gentle daily rhythm."""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Any

from .care_actions import apply_care_action
from .friendship import (
    CARE_FRIENDSHIP_GAIN as CARE_FRIENDSHIP_GAIN,
    CARE_PRIMARY_NEED as CARE_PRIMARY_NEED,
    FRIENDSHIP_DAILY_CAP as FRIENDSHIP_DAILY_CAP,
    FRIENDSHIP_NEED_THRESHOLD as FRIENDSHIP_NEED_THRESHOLD,
    FRIENDSHIP_REWARD_INTERVAL as FRIENDSHIP_REWARD_INTERVAL,
    FRIENDSHIP_VARIETY_BONUS as FRIENDSHIP_VARIETY_BONUS,
    LEGACY_REWARD_ACTIONS as LEGACY_REWARD_ACTIONS,
    award_friendship_for_care,
)
from .need_decay import apply_need_decay
from .pet_lifecycle import (
    MAX_CATCHUP_SECONDS as MAX_CATCHUP_SECONDS,
    MAX_LIVE_EFFORT_SECONDS as MAX_LIVE_EFFORT_SECONDS,
    SIMULATION_STEP_SECONDS as SIMULATION_STEP_SECONDS,
    advance_pet_time,
    apply_daily_routine,
)
from .routine import MEAL_NAMES, TimeContext
from .value_rules import bounded as bounded, clamp_saved_time as clamp_saved_time


@dataclass
class PetState:
    satiety: float = 75.0
    mood: float = 75.0
    energy: float = 75.0
    social: float = 75.0  # Conversation and shared activity.
    affection: float = 75.0  # Gentle attention and feeling cared for.
    friendship: float = 15.0  # Slow, durable bond; never an immediate need.
    friendship_day: str = ""
    friendship_gained_today: float = 0.0
    care_types_today: list[str] = field(default_factory=list)
    care_last_rewards: dict[str, float] = field(default_factory=dict)
    sleeping: bool = False
    updated_at: float = field(default_factory=time.time)
    meals_date: str = ""
    meals_today: list[str] = field(default_factory=list)
    sleep_origin: str = ""  # "routine" or "manual", manual sleep isn't auto-cancelled
    auto_sleep_night: str = ""  # prevents repeated bedtime after manual waking
    nap_until: float = 0.0
    auto_nap_day: str = ""

    @classmethod
    def from_dict(cls, value: Any, *, now: float | None = None) -> PetState:
        """Load old saves defensively, preserving existing needs and trust."""
        current = time.time() if now is None else now
        if not isinstance(value, dict):
            return cls(updated_at=current)
        timestamp = value.get("updated_at", current)
        try:
            timestamp = float(timestamp)
        except (TypeError, ValueError, OverflowError):
            timestamp = current
        if not math.isfinite(timestamp):
            timestamp = current
        meals = value.get("meals_today")
        if not isinstance(meals, list):
            meals = []
        allowed_meals = tuple(MEAL_NAMES)
        valid_meals = [m for m in allowed_meals if m in meals]
        meals_date = value.get("meals_date", "")
        if not isinstance(meals_date, str) or len(meals_date) != 10:
            meals_date = ""
        sleeping = value.get("sleeping") is True
        origin = value.get("sleep_origin")
        if origin not in ("routine", "manual", "nap"):
            origin = "manual" if sleeping else ""
        night_key = value.get("auto_sleep_night")
        if not isinstance(night_key, str) or len(night_key) > 10:
            night_key = ""
        return cls(
            satiety=bounded(value.get("satiety")),
            mood=bounded(value.get("mood")),
            energy=bounded(value.get("energy")),
            social=bounded(value.get("social")),
            affection=bounded(value.get("affection")),
            friendship=bounded(value.get("friendship"), 15.0),
            friendship_day=value.get("friendship_day", "")
            if isinstance(value.get("friendship_day"), str)
            and len(value.get("friendship_day", "")) == 10 else "",
            friendship_gained_today=min(
                FRIENDSHIP_DAILY_CAP,
                bounded(value.get("friendship_gained_today", 0.0), 0.0),
            ),
            care_types_today=cls._load_care_types(value.get("care_types_today")),
            care_last_rewards=cls._load_reward_times(value.get("care_last_rewards")),
            sleeping=sleeping,
            updated_at=timestamp,
            meals_date=meals_date,
            meals_today=valid_meals,
            sleep_origin=origin,
            auto_sleep_night=night_key,
            nap_until=clamp_saved_time(value.get("nap_until")),
            auto_nap_day=value.get("auto_nap_day", "")
            if isinstance(value.get("auto_nap_day"), str)
            and len(value.get("auto_nap_day", "")) == 10 else "",
        )

    @staticmethod
    def _load_care_types(raw: Any) -> list[str]:
        if not isinstance(raw, list):
            return []
        return [action for action in CARE_PRIMARY_NEED if action in raw]

    @staticmethod
    def _load_reward_times(raw: Any) -> dict[str, float]:
        if not isinstance(raw, dict):
            return {}
        return {
            action: clamp_saved_time(raw[action])
            for action in (*CARE_FRIENDSHIP_GAIN, *LEGACY_REWARD_ACTIONS)
            if action in raw and clamp_saved_time(raw[action]) > 0
        }

    @property
    def friendship_level(self) -> int:
        """Display level (1..10), derived from the durable 0..100 bond."""
        return min(10, 1 + int(self.friendship // 10))

    def to_dict(self) -> dict[str, Any]:
        return {
            "satiety": round(self.satiety, 4),
            "mood": round(self.mood, 4),
            "energy": round(self.energy, 4),
            "social": round(self.social, 4),
            "affection": round(self.affection, 4),
            "friendship": round(self.friendship, 4),
            "friendship_day": self.friendship_day,
            "friendship_gained_today": round(self.friendship_gained_today, 4),
            "care_types_today": list(self.care_types_today),
            "care_last_rewards": dict(self.care_last_rewards),
            "sleeping": self.sleeping,
            "updated_at": self.updated_at,
            "meals_date": self.meals_date,
            "meals_today": list(self.meals_today),
            "sleep_origin": self.sleep_origin,
            "auto_sleep_night": self.auto_sleep_night,
            "nap_until": self.nap_until,
            "auto_nap_day": self.auto_nap_day,
        }

    def _roll_meals(self, context: TimeContext) -> None:
        if self.meals_date != context.day_key:
            self.meals_date = context.day_key
            self.meals_today = []

    def _apply_clock(
        self,
        context: TimeContext,
        *,
        allow_bedtime: bool = True,
        allow_nap: bool = False,
        interrupt_nap: bool = False,
        effort: float | None = None,
    ) -> None:
        """Apply the clock policy, preserving existing PetState callers."""
        apply_daily_routine(
            self, context, allow_bedtime=allow_bedtime,
            allow_nap=allow_nap, interrupt_nap=interrupt_nap,
            effort=effort,
        )

    def _decay(
        self, hours: float, context: TimeContext | None,
        effort: float | None = None,
    ) -> None:
        """Update needs at their established rates."""
        apply_need_decay(self, hours, context, effort=effort)

    def advance(
        self,
        now: float,
        *,
        auto_routine: bool = False,
        allow_bedtime: bool | None = None,
        allow_nap: bool = False,
        interrupt_nap: bool = False,
        effort: float | None = None,
    ) -> None:
        """Advance Aiko's needs, day rhythm and sleep state."""
        advance_pet_time(
            self, now,
            auto_routine=auto_routine, allow_bedtime=allow_bedtime,
            allow_nap=allow_nap, interrupt_nap=interrupt_nap, effort=effort,
        )

    def _credit_friendship(
        self, action: str, stamp: float, need_before: float,
    ) -> None:
        """Delegate relationship rewards without changing state semantics."""
        award_friendship_for_care(self, action, stamp, need_before)

    def interact(self, action: str, *, now: float | None = None) -> str:
        """Apply one care action and return the unchanged German fallback."""
        return apply_care_action(self, action, now=now)

    def feed_label(self, context: TimeContext) -> str:
        if context.meal and (
            context.day_key != self.meals_date or context.meal not in self.meals_today
        ):
            return MEAL_NAMES[context.meal]
        return "Snack"

    def mood_hint(self, context: TimeContext | None = None) -> str:
        if self.sleeping:
            return "Aiko schläft gerade ... gute Nacht." if context and context.night else "Aiko ruht sich aus."
        if self.satiety < 20:
            return "Ein kleiner Snack wäre schön ..."
        if self.energy < 20:
            return "Ich könnte etwas Schlaf gebrauchen."
        if self.social < 20:
            return "...Etwas Gesellschaft wäre gerade schön."
        if self.affection < 20:
            return "...Eine kleine Geste wäre gerade schön."
        if self.mood < 20:
            return "Mir ist irgendwie langweilig ..."
        if context is not None:
            if context.meal and context.meal not in self.meals_today:
                return f"Es wäre Zeit für {MEAL_NAMES[context.meal].lower()}."
            if context.weekend:
                return "Heute geht alles etwas langsamer. Gut so."
            if context.night:
                return "Es ist schon spät ..."
            if context.period == "evening":
                return "Endlich ein gemütlicher Abend."
        if min(
            self.satiety, self.mood, self.energy, self.social, self.affection,
        ) > 85:
            return "Heute ist ein guter Tag."
        return "... Ich bin gern hier."
