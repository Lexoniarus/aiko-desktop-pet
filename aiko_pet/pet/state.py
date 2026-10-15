"""Persisted pet state and stable API for separately tested domain rules."""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Any

from .care_actions import (
    apply_care_action as apply_care_action,
    plan_care_action,
    resolve_care_time,
)
from .friendship import (
    CARE_FRIENDSHIP_GAIN as CARE_FRIENDSHIP_GAIN,
    CARE_PRIMARY_NEED as CARE_PRIMARY_NEED,
    FRIENDSHIP_DAILY_CAP as FRIENDSHIP_DAILY_CAP,
    FRIENDSHIP_NEED_THRESHOLD as FRIENDSHIP_NEED_THRESHOLD,
    FRIENDSHIP_REWARD_INTERVAL as FRIENDSHIP_REWARD_INTERVAL,
    FRIENDSHIP_VARIETY_BONUS as FRIENDSHIP_VARIETY_BONUS,
    LEGACY_REWARD_ACTIONS as LEGACY_REWARD_ACTIONS,
    calculate_friendship_reward,
    award_friendship_for_care as award_friendship_for_care,
)
from .food import FoodActivity, FoodId, FoodState, advance_food
from .fun import GameExperience, advance_fun, calculate_game_session_fun
from .mood import MoodFactors, calculate_mood_target, reflect_care_in_mood
from .need_decay import (
    NeedLevels, apply_need_decay as apply_need_decay,
    calculate_need_decay,
)
from .lifecycle import (
    MAX_CATCHUP_SECONDS as MAX_CATCHUP_SECONDS,
    MAX_LIVE_EFFORT_SECONDS as MAX_LIVE_EFFORT_SECONDS,
    SIMULATION_STEP_SECONDS as SIMULATION_STEP_SECONDS,
    advance_pet_time as advance_pet_time,
    apply_daily_routine as apply_daily_routine,
    calculate_daily_routine,
    plan_pet_time,
)
from .routine import MEAL_NAMES, TimeContext, context_at
from .status_hints import MoodHint, choose_mood_hint
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
    food: FoodState = field(default_factory=FoodState)
    fun: float = 75.0  # Entertainment need; mood is its consequence.

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
            food=FoodState.from_dict(value.get("food")),
            fun=bounded(value.get("fun")),
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
            "food": self.food.to_dict(),
            "fun": round(self.fun, 4),
        }

    def _roll_meals(self, context: TimeContext) -> None:
        if self.meals_date != context.day_key:
            self.meals_date = context.day_key
            self.meals_today = []

    def _set_needs(self, values: NeedLevels) -> None:
        """Commit validated need values together inside the pet aggregate."""
        self.satiety = values.satiety
        self.mood = values.mood
        self.energy = values.energy
        self.social = values.social
        self.affection = values.affection

    def update_daily_routine(
        self,
        context: TimeContext,
        *,
        allow_bedtime: bool = True,
        allow_nap: bool = False,
        interrupt_nap: bool = False,
        effort: float | None = None,
    ) -> None:
        """Apply an evaluated sleep transition without exposing private hooks."""
        self._roll_meals(context)
        transition = calculate_daily_routine(
            self, context, allow_bedtime=allow_bedtime,
            allow_nap=allow_nap, interrupt_nap=interrupt_nap, effort=effort,
        )
        self.sleeping = transition.sleeping
        self.sleep_origin = transition.sleep_origin
        self.nap_until = transition.nap_until
        self.auto_sleep_night = transition.auto_sleep_night
        self.auto_nap_day = transition.auto_nap_day

    def _apply_clock(
        self,
        context: TimeContext,
        *,
        allow_bedtime: bool = True,
        allow_nap: bool = False,
        interrupt_nap: bool = False,
        effort: float | None = None,
    ) -> None:
        """Legacy private entrypoint; new rules use update_daily_routine."""
        self.update_daily_routine(
            context, allow_bedtime=allow_bedtime,
            allow_nap=allow_nap, interrupt_nap=interrupt_nap, effort=effort,
        )

    def _decay(
        self, hours: float, context: TimeContext | None,
        effort: float | None = None,
        food_activity: FoodActivity | None = None,
    ) -> None:
        """Update nutrition and the other needs in one aggregate transition."""
        food_progress = advance_food(
            self.food, self.satiety, hours,
            sleeping=self.sleeping,
            activity=(
                food_activity if food_activity is not None
                else FoodActivity(hardware_load=effort or 0.0)
            ),
        )
        self._set_needs(calculate_need_decay(
            self, hours, context, effort, food_progress=food_progress,
        ))
        self.food = food_progress.food
        self.fun = advance_fun(self.fun, hours, sleeping=self.sleeping)

    def _mood_target(self) -> float:
        """Read current needs; mood itself never feeds any of them back."""
        return calculate_mood_target(MoodFactors(
            satiety=self.satiety, energy=self.energy, fun=self.fun,
            social=self.social, affection=self.affection,
            friendship=self.friendship,
        ))

    def record_game_experience(
        self, experience: GameExperience, *, now: float,
    ) -> float:
        """Commit one finished minigame, retaining no session statistics."""
        reward = calculate_game_session_fun(experience, self.fun)
        if experience.completed_units == 0:
            return 0.0
        before = self.fun
        self.fun = bounded(self.fun + reward.fun_points, 0.0)
        self.energy = bounded(self.energy - reward.energy_cost, 0.0)
        self.social = bounded(self.social + reward.social_gain, 0.0)
        self._credit_friendship("play", now, before)
        self.mood = reflect_care_in_mood(self.mood, self._mood_target())
        return self.fun - before

    def advance(
        self,
        now: float,
        *,
        auto_routine: bool = False,
        allow_bedtime: bool | None = None,
        allow_nap: bool = False,
        interrupt_nap: bool = False,
        effort: float | None = None,
        elapsed_seconds: float | None = None,
        food_activity: FoodActivity | None = None,
    ) -> None:
        """Execute bounded time steps, keeping mutation inside PetState."""
        steps = plan_pet_time(
            self.updated_at, now, auto_routine=auto_routine, effort=effort,
            elapsed_seconds=elapsed_seconds,
        )
        if steps is None:
            return
        if not auto_routine:
            for step in steps:
                self._decay(step.hours, None, step.effort, food_activity)
            self._roll_meals(context_at(now))
        else:
            for step in steps:
                if step.context is None:
                    continue
                self.update_daily_routine(
                    step.context, allow_bedtime=allow_bedtime is not False,
                    allow_nap=allow_nap, interrupt_nap=interrupt_nap,
                )
                self._decay(step.hours, step.context, step.effort, food_activity)
            self.update_daily_routine(
                context_at(now), allow_bedtime=allow_bedtime is not False,
                allow_nap=allow_nap,
            )
        self.updated_at = now

    def _credit_friendship(
        self, action: str, stamp: float, need_before: float,
    ) -> None:
        """Apply an immutable friendship decision to owned reward fields."""
        transition = calculate_friendship_reward(
            self, action, stamp, need_before,
        )
        if transition is None:
            return
        self.friendship = transition.friendship
        self.friendship_day = transition.day
        self.friendship_gained_today = transition.gained_today
        self.care_types_today = list(transition.care_types)
        self.care_last_rewards = dict(transition.last_rewards)

    def interact(
        self, action: str, *, now: float | None = None,
        food_id: FoodId | None = None,
    ) -> str:
        """Commit one care transition and its friendship reward atomically."""
        stamp = resolve_care_time(now)
        transition = plan_care_action(
            self, action, now=stamp, food_id=food_id,
        )
        if not transition.changed:
            return transition.response
        self._set_needs(transition.needs)
        self.sleeping = transition.sleeping
        self.sleep_origin = transition.sleep_origin
        self.nap_until = transition.nap_until
        self.auto_sleep_night = transition.auto_sleep_night
        if transition.food is not None:
            self.food = transition.food
        if (
            self.meals_date != transition.meals_date
            or tuple(self.meals_today) != transition.meals_today
        ):
            self.meals_date = transition.meals_date
            self.meals_today = list(transition.meals_today)
        if transition.reward_action is not None:
            self._credit_friendship(
                transition.reward_action, stamp, transition.need_before,
            )
        if action in ("feed", "pet", "talk", "energy_drink"):
            self.mood = reflect_care_in_mood(
                self.mood, self._mood_target(),
                experience_points=transition.mood_experience,
            )
        return transition.response

    def feed_label(self, context: TimeContext) -> str:
        if context.meal and (
            context.day_key != self.meals_date or context.meal not in self.meals_today
        ):
            return MEAL_NAMES[context.meal]
        return "Snack"

    def mood_hint(self, context: TimeContext | None = None) -> MoodHint:
        """Return the semantic status hint, not a language-specific sentence."""
        return choose_mood_hint(self, context)
