"""Mutable pet aggregate; rules commit effects without text or save formats."""

from __future__ import annotations

import time
from copy import deepcopy
from dataclasses import dataclass, field, fields, replace

from .balance import BALANCE
from .care_actions import (
    CareTransition,
    plan_care_action,
    resolve_care_time,
)
from .care_result import CareResult
from .consumption import ConsumptionOrigin
from .food import (
    FOOD_CATALOG,
    FoodActivity,
    FoodId,
    FoodState,
    advance_food,
    eat_food,
)
from .friendship import (
    calculate_friendship_reward,
    friendship_after_withholding,
)
from .fun import GameExperience, advance_fun, calculate_game_session_fun
from .lifecycle import (
    calculate_daily_routine,
    plan_pet_time,
)
from .mood import MoodFactors, calculate_mood_target, reflect_care_in_mood
from .need_decay import (
    NeedLevels,
    calculate_need_decay,
)
from .routine import TimeContext, context_at, due_meal
from .status_hints import MoodHint, choose_mood_hint
from .value_rules import clamp_need_value


@dataclass
class PetState:
    satiety: float = BALANCE.number("initial", "satiety")
    mood: float = BALANCE.number("initial", "mood")
    energy: float = BALANCE.number("initial", "energy")
    social: float = BALANCE.number(
        "initial", "social"
    )  # Conversation and shared activity.
    affection: float = BALANCE.number(
        "initial", "affection"
    )  # Gentle attention and feeling cared for.
    friendship: float = BALANCE.number(
        "initial", "friendship"
    )  # Slow, durable bond; never an immediate need.
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
    fun: float = BALANCE.number(
        "initial", "fun"
    )  # Entertainment need; mood is its consequence.

    @property
    def friendship_level(self) -> int:
        """Display level (1..10), derived from the durable 0..100 bond."""
        return min(10, 1 + int(self.friendship // 10))

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
            self,
            context,
            allow_bedtime=allow_bedtime,
            allow_nap=allow_nap,
            interrupt_nap=interrupt_nap,
            effort=effort,
        )
        self.sleeping = transition.sleeping
        self.sleep_origin = transition.sleep_origin
        self.nap_until = transition.nap_until
        self.auto_sleep_night = transition.auto_sleep_night
        self.auto_nap_day = transition.auto_nap_day

    def _decay(
        self,
        hours: float,
        context: TimeContext | None,
        effort: float | None = None,
        food_activity: FoodActivity | None = None,
    ) -> None:
        """Update nutrition and the other needs in one aggregate transition."""
        food_progress = advance_food(
            self.food,
            self.satiety,
            hours,
            sleeping=self.sleeping,
            activity=(
                food_activity
                if food_activity is not None
                else FoodActivity(hardware_load=effort or 0.0)
            ),
        )
        self._set_needs(
            calculate_need_decay(
                self,
                hours,
                context,
                effort,
                food_progress=food_progress,
            )
        )
        self.food = food_progress.food
        self.fun = advance_fun(self.fun, hours, sleeping=self.sleeping)

    def _mood_target(self) -> float:
        """Read current needs; mood itself never feeds any of them back."""
        return calculate_mood_target(
            MoodFactors(
                satiety=self.satiety,
                energy=self.energy,
                fun=self.fun,
                social=self.social,
                affection=self.affection,
                friendship=self.friendship,
            )
        )

    def _provide_own_meal(self, context: TimeContext) -> None:
        """Eat a due main meal without crediting human attention or friendship."""
        meal = self.due_meal(context)
        if self.sleeping or meal is None:
            return
        meal_foods = tuple(
            key for key, profile in FOOD_CATALOG.items() if profile.category == "meal"
        )
        if not meal_foods:
            return
        # Prefer variety without inventing another nutrition/menu catalogue.
        food_id = next(
            (key for key in meal_foods if key != self.food.last_food_id),
            meal_foods[0],
        )
        intake = eat_food(self.food, self.satiety, food_id)
        if intake.accepted:
            self.satiety = intake.satiety
            self.food = intake.food
            self.meals_today.append(meal)

    def record_game_experience(
        self,
        experience: GameExperience,
        *,
        now: float,
    ) -> float:
        """Commit one finished minigame, retaining no session statistics."""
        reward = calculate_game_session_fun(experience, self.fun)
        if experience.completed_units == 0:
            return 0.0
        before = self.fun
        self.fun = clamp_need_value(self.fun + reward.fun_points, 0.0)
        self.energy = clamp_need_value(self.energy - reward.energy_cost, 0.0)
        self.social = clamp_need_value(self.social + reward.social_gain, 0.0)
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
        self_care: bool = False,
    ) -> None:
        """Execute bounded time steps, keeping mutation inside PetState."""
        steps = plan_pet_time(
            self.updated_at,
            now,
            auto_routine=auto_routine,
            effort=effort,
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
                    step.context,
                    allow_bedtime=allow_bedtime is not False,
                    allow_nap=allow_nap,
                    interrupt_nap=interrupt_nap,
                )
                self._decay(step.hours, step.context, step.effort, food_activity)
                if self_care:
                    self._provide_own_meal(step.context)
            self.update_daily_routine(
                context_at(now),
                allow_bedtime=allow_bedtime is not False,
                allow_nap=allow_nap,
            )
            if self_care:
                self._provide_own_meal(context_at(now))
        self.updated_at = now

    def apply_object_withholding(self, loss: float) -> float:
        """Commit a bounded application decision without manufacturing care."""
        previous = self.friendship
        self.friendship = friendship_after_withholding(previous, loss)
        return previous - self.friendship

    def _credit_friendship(
        self,
        action: str,
        stamp: float,
        need_before: float,
    ) -> None:
        """Apply an immutable friendship decision to owned reward fields."""
        transition = calculate_friendship_reward(
            self,
            action,
            stamp,
            need_before,
        )
        if transition is None:
            return
        self.friendship = transition.friendship
        self.friendship_day = transition.day
        self.friendship_gained_today = transition.gained_today
        self.care_types_today = list(transition.care_types)
        self.care_last_rewards = dict(transition.last_rewards)

    def interact(
        self,
        action: str,
        *,
        now: float | None = None,
        food_id: FoodId | None = None,
    ) -> CareResult:
        """Commit one care transition and its friendship reward atomically."""
        stamp = resolve_care_time(now)
        transition = plan_care_action(
            self,
            action,
            now=stamp,
            food_id=food_id,
        )
        return self._apply_care_transition(transition, stamp)

    def consume_item(
        self, item_id: str, origin: ConsumptionOrigin, *, now: float,
    ) -> CareResult | None:
        """Use canonical nutrition; autonomous intake is not human attention."""
        if self.sleeping:
            return None
        action = "energy_drink" if item_id == "energy_drink" else "feed"
        transition = plan_care_action(
            self, action, now=now,
            food_id=None if action == "energy_drink" else item_id,
        )
        if origin == ConsumptionOrigin.AUTONOMOUS:
            transition = replace(
                transition, reward_action=None,
                needs=replace(transition.needs, social=self.social),
            )
        return self._apply_care_transition(transition, now)

    def restore_values(self, snapshot: PetState) -> None:
        """Owner-controlled commit/recovery without replacing aggregate identity."""
        for item in fields(self):
            setattr(self, item.name, deepcopy(getattr(snapshot, item.name)))

    def _apply_care_transition(
        self, transition: CareTransition, stamp: float,
    ) -> CareResult:
        action = transition.result.action
        if not transition.changed:
            return transition.result
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
                transition.reward_action,
                stamp,
                transition.need_before,
            )
        if action in ("feed", "pet", "talk", "energy_drink"):
            self.mood = reflect_care_in_mood(
                self.mood,
                self._mood_target(),
                experience_points=transition.mood_experience,
            )
        return transition.result

    def due_meal(self, context: TimeContext) -> str | None:
        """Return the due meal ID, or None when only snacks remain."""
        return due_meal(
            context,
            meals_date=self.meals_date,
            meals_today=self.meals_today,
        )

    def mood_hint(self, context: TimeContext | None = None) -> MoodHint:
        """Return the semantic status hint, not a language-specific sentence."""
        return choose_mood_hint(self, context)
